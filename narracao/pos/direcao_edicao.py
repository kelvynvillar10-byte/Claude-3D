"""Direção da EDIÇÃO (pós-produção) e ficha de GERAÇÃO para o MiniMax Audio.

Fluxo por narração:
1. `rascunho(texto, palavras)`: divide o texto em frases, sugere a intenção de cada uma por regras (reaproveitando o
   diretor de narração `narracao/direcao.py`, sem alterá-lo) e calcula as pausas-alvo pela TABELA aprovada.
2. O Claude REVISA frase a frase (intenção, pausas, palavras de destaque, justificativa) e marca `"revisado": true`.
3. `editar.py` aplica. O conteúdo falado nunca muda: só pausas, nível e destaque.

Pausas aprovadas pelo diretor em 26/11/2026: suspense e revelação até 0,7 s; surpresa até 0,5 s; ação até 0,15 s;
nenhuma pausa ≥ 0,8 s. Vírgulas mantêm a pausa natural dentro de uma faixa.
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import direcao as DR          # noqa: E402  (diretor de narração existente; só leitura)

INTENCOES = ["curiosidade", "suspense", "surpresa", "descoberta", "acao", "emocao", "conclusao", "explicacao",
             "misterio", "tensao", "entusiasmo"]
NOMES = {"curiosidade": "Curiosidade", "suspense": "Suspense", "surpresa": "Surpresa", "descoberta": "Descoberta/revelação",
         "acao": "Ação", "emocao": "Emoção", "conclusao": "Conclusão", "explicacao": "Explicação", "misterio": "Mistério",
         "tensao": "Tensão", "entusiasmo": "Entusiasmo"}

# pausas-alvo (s) ENTRE frases: a pausa efetiva = max(depois da frase anterior, antes da próxima), limitada pelo teto.
# vírgula: faixa [mín, máx] em que a pausa natural é mantida (fora dela, é trazida para a borda).
TABELA = {
    "explicacao":  {"antes": 0.00, "depois": 0.30, "virgula": (0.10, 0.22)},
    "curiosidade": {"antes": 0.00, "depois": 0.38, "virgula": (0.10, 0.22)},
    "entusiasmo":  {"antes": 0.00, "depois": 0.25, "virgula": (0.08, 0.18)},
    "misterio":    {"antes": 0.40, "depois": 0.40, "virgula": (0.14, 0.28)},
    "suspense":    {"antes": 0.45, "depois": 0.60, "virgula": (0.16, 0.32)},
    "tensao":      {"antes": 0.15, "depois": 0.20, "virgula": (0.06, 0.15)},
    "acao":        {"antes": 0.12, "depois": 0.15, "virgula": (0.05, 0.12)},
    "surpresa":    {"antes": 0.50, "depois": 0.35, "virgula": (0.10, 0.20)},
    "descoberta":  {"antes": 0.60, "depois": 0.45, "virgula": (0.12, 0.25)},
    "emocao":      {"antes": 0.40, "depois": 0.45, "virgula": (0.14, 0.28)},
    "conclusao":   {"antes": 0.50, "depois": 0.00, "virgula": (0.12, 0.25)},
}
TETO = {"suspense": 0.70, "descoberta": 0.70, "surpresa": 0.50, "acao": 0.15}   # tetos aprovados por intenção
TETO_GERAL = 0.70                     # nenhuma pausa dirigida passa disto (e nunca ≥ 0,8 s)
PAUSA_INICIO = 0.15                   # silêncio antes da primeira palavra
PAUSA_FINAL = 0.50                    # silêncio depois da última palavra
PAUSA_INADEQUADA = 0.25               # pausa SEM pontuação acima disto é tratada como inadequada…
PAUSA_SEM_PONTUACAO = 0.10            # …e reduzida para isto
DESTAQUE_DB = 1.5                     # destaque padrão de uma palavra (máx. 2 dB)

PISTAS_EXTRA = [
    ("descoberta", [r"\bpercebe[ur]", r"\bdescobri", r"\brevel", r"\bna verdade\b", r"\bera\b.*\bnão\b", r"\bnão era\b",
                    r"\bdescobert", r"\bacontece que\b"]),
    ("acao", [r"\bcorr[eiu]", r"\bpul[aoe]", r"\bexplod", r"\bbat[eiu]", r"\bderrub", r"\bdispar", r"\bvo[ao]u\b", r"\bcai[ru]?\b"]),
]
DESTAQUE_PISTAS = [r"^\d", r"milh[õo]es", r"bilh[õo]es", r"^nunca$", r"^ningu[eé]m$", r"imposs[ií]vel", r"segredo", r"^jamais$",
                   r"^único$|^única$", r"^maior$", r"^menor$", r"incr[ií]vel", r"^tudo$", r"^nada$", r"^sempre$"]


def frases(texto):
    """Frases com posição de caracteres (fim inclui a pontuação final)."""
    out = []
    for m in re.finditer(r"[^.!?…]+(?:[.!?…]+|$)", texto):
        s = m.group(0)
        if s.strip():
            a = m.start() + (len(s) - len(s.lstrip())); b = m.end()
            out.append({"texto": texto[a:b].strip(), "c0": a, "c1": b})
    return out


def classificar(texto_frase, ultima=False):
    t = texto_frase.lower()
    for nome, pats in PISTAS_EXTRA:
        for p in pats:
            if re.search(p, t):
                return nome, p
    nome, pista = DR.classificar(texto_frase)
    if ultima and nome == "explicacao":
        return "conclusao", "última frase"
    return nome, pista


def rascunho(texto, palavras):
    """Rascunho por regras: intenção, pausas-alvo e destaques. O Claude revisa antes da edição."""
    fs = frases(texto)
    out = []
    for n, f in enumerate(fs):
        idx = [p["i"] for p in palavras if p["c0"] >= f["c0"] and p["c1"] <= f["c1"]]
        if not idx:
            continue
        nome, pista = classificar(f["texto"], ultima=(n == len(fs) - 1))
        dest = [{"i": i, "w": palavras[i]["w"], "db": DESTAQUE_DB} for i in idx
                if any(re.search(p, palavras[i]["w"].lower()) for p in DESTAQUE_PISTAS)][:2]
        out.append({"n": len(out) + 1, "texto": f["texto"], "c0": f["c0"], "c1": f["c1"], "palavras": [idx[0], idx[-1]],
                    "intencao": nome, "justificativa": f"rascunho por regra ({pista})" if pista else "rascunho: sem pista → explicação",
                    "pausa_antes_s": TABELA[nome]["antes"], "pausa_depois_s": TABELA[nome]["depois"],
                    "virgula_s": list(TABELA[nome]["virgula"]), "destaques": dest, "ganho_db": 0.0, "nota": ""})
    return {"versao": 1, "revisado": False, "frases": out,
            "ajustes_pausa": {},          # {"<índice da palavra ANTES da pausa>": {"alvo_s": 0.3 | null (= manter a natural), "motivo": "…"}}
            "regras": {"teto_geral_s": TETO_GERAL, "tetos_por_intencao_s": TETO, "pausa_inicio_s": PAUSA_INICIO,
                       "pausa_final_s": PAUSA_FINAL, "pausa_sem_pontuacao_inadequada_s": PAUSA_INADEQUADA,
                       "pausa_sem_pontuacao_alvo_s": PAUSA_SEM_PONTUACAO}}


def validar(d, n_palavras):
    erros = []
    vistos = []
    for f in d["frases"]:
        if f["intencao"] not in INTENCOES:
            erros.append(f"frase {f['n']}: intenção desconhecida {f['intencao']}")
        for k in ("pausa_antes_s", "pausa_depois_s"):
            teto = TETO.get(f["intencao"], TETO_GERAL)
            if not 0 <= f[k] <= min(teto, TETO_GERAL) + 1e-9:
                erros.append(f"frase {f['n']}: {k}={f[k]} fora de [0, {min(teto, TETO_GERAL)}]")
        for dd in f["destaques"]:
            if not 0 < dd["db"] <= 2.0:
                erros.append(f"frase {f['n']}: destaque de {dd['db']} dB (permitido: até 2 dB)")
        if abs(f.get("ganho_db", 0)) > 2.0:
            erros.append(f"frase {f['n']}: ganho de frase {f['ganho_db']} dB (permitido: ±2 dB)")
        vistos += list(range(f["palavras"][0], f["palavras"][1] + 1))
    for k, aj in d.get("ajustes_pausa", {}).items():
        if not str(k).isdigit() or not 0 <= int(k) < n_palavras - 1:
            erros.append(f"ajuste de pausa em palavra inexistente: {k}")
        a = aj.get("alvo_s")
        if a is not None and not 0 <= a <= TETO_GERAL:
            erros.append(f"ajuste de pausa {k}: {a} s fora de [0, {TETO_GERAL}]")
        if not aj.get("motivo"):
            erros.append(f"ajuste de pausa {k}: falta o motivo")
    if vistos != list(range(n_palavras)):
        erros.append("palavras faltando, repetidas ou fora de ordem nas frases")
    return erros


def ficha_geracao(texto, cfg_voz, velocidade_base=1.0):
    """Ficha para o diretor gerar no MiniMax Audio: trechos com intenção, velocidade, volume, tom, emoção e pausas.
    Reaproveita o diretor de narração (velocidade/volume/tom/emoção por intenção). Não chama nenhuma API."""
    fs = frases(texto)
    linhas = [f"# Ficha de geração — MiniMax Audio", "",
              f"- **Voz:** `{cfg_voz['voz']['voice_id']}` ({cfg_voz['voz'].get('nome_na_api', '')})",
              f"- **Modelo:** {cfg_voz['modelo']} · **Idioma:** Portuguese",
              "- Gere **um trecho por linha** (cada um com seus parâmetros) ou o texto inteiro com os parâmetros da linha 1, "
              "se o site não permitir por trecho. As pausas entre trechos são feitas na edição.",
              "- Marcas `<#0.3#>` = pausa em segundos (sintaxe da API MiniMax; use só se o site aceitar — senão, ignore).",
              "", "| # | Intenção | Texto | Velocidade | Volume | Tom | Emoção | Pausa sugerida depois |",
              "|---|---|---|---|---|---|---|---|"]
    for n, f in enumerate(fs, 1):
        nome, _ = classificar(f["texto"], ultima=(n == len(fs)))
        base = {"descoberta": "surpresa", "acao": "tensao", "conclusao": "explicacao"}.get(nome, nome)
        p = DR.parametros(base, velocidade_base)
        emo = p["emocao_proposta"] or "automática"
        linhas.append(f"| {n} | {NOMES[nome]} | {f['texto']} | {p['speed']} | {p['vol']} | {p['pitch']:+d} | {emo} | "
                      f"{TABELA[nome]['depois']:.2f} s |")
    linhas += ["", f"**Total:** {len(texto)} caracteres (inclui espaços e pontuação)."]
    return "\n".join(linhas)
