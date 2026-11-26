"""Edição expressiva: pausas por intenção, destaque de palavras e nível por frase.

Garantias (conferidas no QA):
- o áudio de cada palavra é copiado sem nenhum corte (idêntico ao original, exceto o ganho dirigido);
- cortes e inserções só acontecem DENTRO das pausas, com transições suaves (crossfade de potência constante);
- nada é acelerado, desacelerado ou mudado de tom;
- os tempos das palavras são recalculados para o áudio final.
"""
import re
import numpy as np

import direcao_edicao as DE

XF = 0.010          # crossfade dentro das pausas (s)
RAMPA = 0.025       # rampa do ganho de destaque/frase (s)


def _ganho(y, sr, palavras, direcao):
    """Envelope de ganho (dB): ganho da frase + destaque das palavras. Trapézio: rampa de 25 ms FORA do trecho, para o
    trecho inteiro receber o ganho pleno."""
    t = np.arange(len(y)) / sr
    g = np.zeros(len(y))
    def aplica(a, b, db):
        if db == 0 or b <= a:
            return
        lo, hi = max(0, int((a - RAMPA) * sr)), min(len(y), int((b + RAMPA) * sr) + 1)
        g[lo:hi] += np.interp(t[lo:hi], [a - RAMPA, a, b, b + RAMPA], [0, db, db, 0])
    for f in direcao["frases"]:
        aplica(palavras[f["palavras"][0]]["ini"], palavras[f["palavras"][1]]["fim"], float(f.get("ganho_db", 0)))
        for d in f["destaques"]:
            p = palavras[d["i"]]; aplica(p["ini"], p["fim"], float(d["db"]))
    return (y * (10 ** (g / 20))).astype(np.float32), g


def _juntar(pecas, xf):
    """Concatena pedaços com crossfade de potência constante de `xf` amostras em cada junção."""
    out = pecas[0].astype(np.float32)
    for p in pecas[1:]:
        p = p.astype(np.float32)
        n = min(xf, len(out), len(p))
        if n <= 0:
            out = np.concatenate([out, p]); continue
        t = np.linspace(0, np.pi / 2, n)
        mix = out[-n:] * np.cos(t) + p[:n] * np.sin(t)
        out = np.concatenate([out[:-n], mix, p[n:]])
    return out


def _preenchimento(gap, n, sr):
    """`n` amostras de 'silêncio' com o mesmo fundo da pausa (digital zero se a pausa já for silêncio digital)."""
    if n <= 0:
        return np.zeros(0, np.float32)
    if not len(gap) or 20 * np.log10(np.sqrt(np.mean(gap.astype(np.float64) ** 2)) + 1e-12) < -80:
        return np.zeros(n, np.float32)
    w = int(0.06 * sr)
    if len(gap) <= w:
        base = gap
    else:
        rms = [np.mean(gap[i:i + w] ** 2) for i in range(0, len(gap) - w, w // 2)]
        i = int(np.argmin(rms)) * (w // 2); base = gap[i:i + w]
    xf = min(int(XF * sr), len(base) // 3)
    pecas = []; total = 0
    while total < n + xf * (len(pecas) + 1):
        pecas.append(base); total += len(base)
    return _juntar(pecas, xf)[:n]


def _refazer_pausa(gap, alvo_s, sr, resp=None):
    """Pausa com a duração-alvo, preservando o começo (cauda da palavra anterior) e o fim (ataque da próxima).
    `resp` = (ini, fim) da respiração relativa à pausa, mantida inteira quando couber."""
    n = int(round(alvo_s * sr)); d = len(gap); xf = int(XF * sr)
    if n == d:
        return gap.copy(), None
    if resp is not None:
        ra, rb = max(0, int((resp[0] - 0.02) * sr)), min(d, int((resp[1] + 0.02) * sr))
        lb = rb - ra
        if n >= lb + int(0.08 * sr):
            resto = n - lb
            L = int(resto * 0.6); R = resto - L
            L = min(L, ra); R = min(R, d - rb)
            falta = n - (L + lb + R)
            pecas = [gap[:L + xf]] if L else []
            meio = gap[ra:rb]
            if falta > 0:
                meio = _juntar([meio, _preenchimento(gap, falta + xf, sr)], xf)
            pecas.append(meio)
            if R:
                pecas.append(gap[d - R - xf:] if d - R - xf >= rb else gap[d - R:])
            y = _juntar(pecas, xf) if len(pecas) > 1 else pecas[0]
            return _ajusta(y, n), "respiração mantida"
        resp_nota = "respiração removida (não cabia na pausa-alvo)"
    else:
        resp_nota = None
    if n < d:                                                         # encurtar: mantém as duas pontas
        h1 = n // 2; h2 = n - h1
        y = _juntar([gap[:h1 + xf // 2], gap[d - h2 - (xf - xf // 2):]], xf) if n > 2 * xf else np.concatenate([gap[:h1], gap[d - h2:]])
        return _ajusta(y, n), resp_nota
    meio = d // 2                                                     # alongar: insere fundo no meio
    y = _juntar([gap[:meio], _preenchimento(gap, n - d + 2 * xf, sr), gap[meio:]], xf)
    return _ajusta(y, n), resp_nota


def _ajusta(y, n):
    if len(y) > n:
        return y[:n]
    if len(y) < n:
        return np.concatenate([y, np.zeros(n - len(y), np.float32)])
    return y


def _tipo_fronteira(texto, p0, p1):
    sep = texto[p0["c1"]:p1["c0"]]
    if re.search(r"[.!?…]", sep):
        return "frase"
    if re.search(r"[,;:—–]", sep) or re.search(r"\s-\s", sep):
        return "virgula"
    return "nenhuma"


def alvo_da_pausa(tipo, d, fa, fb):
    """Pausa-alvo (s) e o motivo, pela direção revisada."""
    if tipo == "frase":
        cands = [(fa["pausa_depois_s"], fa["intencao"], "depois"), (fb["pausa_antes_s"], fb["intencao"], "antes")]
        t, inten, lado = max(cands)
        teto = min(DE.TETO.get(inten, DE.TETO_GERAL), DE.TETO_GERAL)
        minimo = 0.10 if "acao" in (fa["intencao"], fb["intencao"]) else 0.18
        t = min(max(t, minimo), teto)
        return t, f"entre frases: {DE.NOMES[inten]} ({lado}) → {t:.2f} s"
    if tipo == "virgula":
        lo, hi = fa["virgula_s"]
        t = min(max(d, lo), hi)
        return t, f"vírgula/pausa interna ({DE.NOMES[fa['intencao']]}): faixa {lo:.2f}–{hi:.2f} s"
    if d > DE.PAUSA_INADEQUADA:
        return DE.PAUSA_SEM_PONTUACAO, f"pausa sem pontuação de {d:.2f} s (inadequada) → {DE.PAUSA_SEM_PONTUACAO:.2f} s"
    return d, "pausa natural mantida"


def _tem_fala(gap, sr, limiar_db):
    """Há fala dentro da pausa (sem as pontas de 20 ms)? Se houver, a pausa NÃO é editada (provável erro de alinhamento)."""
    import audio as AU
    m = int(0.02 * sr)
    miolo = gap[m:len(gap) - m]
    if len(miolo) < int(0.03 * sr):
        return False
    acima = AU.energia_db(miolo, sr) > limiar_db + 3.0            # fala = 40 ms seguidos acima do limiar de fala (+3 dB de folga)
    corrida = 0
    for v in acima:
        corrida = corrida + 1 if v else 0
        if corrida >= 4:
            return True
    return False


def editar(y, sr, texto, palavras, direcao, respiracoes, limiar_db=-60.0):
    """Devolve (áudio editado, palavras no áudio final, operações, envelope de ganho)."""
    y2, g = _ganho(y, sr, palavras, direcao)
    frase_de = {}
    for f in direcao["frases"]:
        for i in range(f["palavras"][0], f["palavras"][1] + 1):
            frase_de[i] = f
    ops = []; pedacos = []; desloc = []
    # pausa inicial
    a0 = int(palavras[0]["ini"] * sr)
    ini_gap = y2[:a0]; n = int(DE.PAUSA_INICIO * sr)
    if len(ini_gap) >= n:
        novo = ini_gap[len(ini_gap) - n:].copy()
    else:
        novo = np.concatenate([np.zeros(n - len(ini_gap), np.float32), ini_gap])
    f_in = min(int(0.01 * sr), len(novo))
    if f_in:
        novo[:f_in] *= np.linspace(0, 1, f_in)
    ops.append({"tipo": "pausa inicial", "original_s": round(a0 / sr, 3), "final_s": round(n / sr, 3), "motivo": "início padronizado"})
    pedacos.append(novo); pos = n
    for k, p in enumerate(palavras):
        a = int(p["ini"] * sr); b = int(p["fim"] * sr)
        desloc.append((pos / sr - a / sr, a, pos, b - a))
        pedacos.append(y2[a:b]); pos += b - a
        if k + 1 < len(palavras):
            c = int(palavras[k + 1]["ini"] * sr)
            gap = y2[b:c]; d = (c - b) / sr
            tipo = _tipo_fronteira(texto, p, palavras[k + 1])
            alvo, motivo = alvo_da_pausa(tipo, d, frase_de[k], frase_de[k + 1])
            resp = next(([r[0] - b / sr, r[1] - b / sr] for r in respiracoes if r[0] >= b / sr - 0.01 and r[1] <= c / sr + 0.01), None)
            if abs(alvo - d) <= 0.010 and not (d < 0.02 < alvo):
                novo, nota = gap.copy(), None
                alvo = d
            elif d >= 0.02 and _tem_fala(gap, sr, limiar_db):
                novo, nota = gap.copy(), "NÃO editada: há fala dentro da pausa (provável erro de alinhamento); conferir"
            elif d < 0.02:                                             # sem pausa natural: insere fundo no ponto de menor energia
                novo = np.zeros(int(round(alvo * sr)), np.float32)
                nota = "inserção sem pausa natural (fronteira sem silêncio no original)"
                if len(gap):
                    novo = _juntar([gap, novo], 0)[:len(novo)] if len(gap) < len(novo) else gap[:len(novo)]
            else:
                novo, nota = _refazer_pausa(gap, alvo, sr, resp)
            if abs(len(novo) / sr - d) > 0.0105 or nota:
                ops.append({"tipo": tipo, "depois_da_palavra": k, "entre": f"{p['w']} → {palavras[k + 1]['w']}",
                            "inicio_original_s": round(b / sr, 3), "original_s": round(d, 3), "final_s": round(len(novo) / sr, 3),
                            "motivo": motivo, **({"nota": nota} if nota else {})})
            pedacos.append(novo); pos += len(novo)
    # pausa final
    b = int(palavras[-1]["fim"] * sr)
    fim_gap = y2[b:]; n = int(DE.PAUSA_FINAL * sr)
    novo = fim_gap[:n].copy() if len(fim_gap) >= n else np.concatenate([fim_gap, np.zeros(n - len(fim_gap), np.float32)])
    f_out = min(int(0.06 * sr), len(novo))
    if f_out:
        novo[-f_out:] *= np.linspace(1, 0, f_out)
    ops.append({"tipo": "pausa final", "original_s": round(len(fim_gap) / sr, 3), "final_s": round(n / sr, 3), "motivo": "final padronizado"})
    pedacos.append(novo)
    saida = np.concatenate(pedacos).astype(np.float32)
    finais = [{**{k: v for k, v in p.items() if k not in ("ini", "fim")},
               "ini": round(p["ini"] + desloc[k][0], 3), "fim": round(p["fim"] + desloc[k][0], 3),
               "ini_original": p["ini"], "fim_original": p["fim"],
               "amostra_original": desloc[k][1], "amostra_final": desloc[k][2], "amostras": desloc[k][3]} for k, p in enumerate(palavras)]
    return saida, finais, ops, g
