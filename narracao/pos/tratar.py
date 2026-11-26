"""Tratamento de áudio (preset da assinatura sonora). Etapas condicionais só entram se a medição pedir.
Ordem: graves → cliques → ruído → equalização → de-esser → compressão → loudness (2 passagens, modo linear).
Nunca muda tom nem velocidade. O atraso de cada filtro é medido e compensado (os tempos das palavras não podem andar).
"""
import json, re
from pathlib import Path
import numpy as np

import audio as AU

PRESET = Path(__file__).resolve().parent / "preset_v1.json"


def carregar_preset(caminho=PRESET):
    return json.loads(Path(caminho).read_text())


def cadeia(pr, medidas):
    """Monta a cadeia de filtros e a lista do que entrou e por quê."""
    etapas, decisoes = [], []
    fg = pr["filtro_graves"]
    etapas.append(f"highpass=f={fg['hz']}:poles={fg['polos']}"); decisoes.append(f"filtro de graves em {fg['hz']} Hz (sempre: tira ronco e subgrave sem efeito na voz)")
    if pr["cliques"]["usar_se_detectados"] and medidas["cliques"]:
        etapas.append(f"adeclick=w={pr['cliques']['janela_ms']}:t={pr['cliques']['limiar']}")
        decisoes.append(f"remoção de cliques: {len(medidas['cliques'])} candidato(s) detectado(s)")
    else:
        decisoes.append("remoção de cliques: não aplicada (nenhum clique detectado)")
    piso = medidas["piso_ruido_db"]
    if piso is not None and piso > pr["ruido"]["usar_se_piso_acima_dbfs"]:
        etapas.append(f"afftdn=nr={pr['ruido']['reducao_db']}:nf={pr['ruido']['piso_db']}:tn=1")
        decisoes.append(f"redução de ruído leve: piso nas pausas em {piso} dBFS")
    else:
        decisoes.append(f"redução de ruído: não aplicada (piso {piso} dBFS, abaixo de {pr['ruido']['usar_se_piso_acima_dbfs']})")
    sib = medidas["bandas"]["sibilancia_5k_10k"]
    deesser = sib > pr["de_esser"]["usar_se_sibilancia_acima_db"]
    eqs = [e for e in pr["equalizacao"] if not (deesser and e.get("tipo") == "prateleira_aguda")]
    for e in eqs:
        if e.get("tipo") == "prateleira_aguda":
            etapas.append(f"highshelf=f={e['hz']}:g={e['db']}")
        else:
            etapas.append(f"equalizer=f={e['hz']}:t=q:w={e['q']}:g={e['db']}")
    decisoes.append("equalização: " + ", ".join(f"{e['nome']} {e['db']:+.1f} dB em {e['hz']} Hz" for e in eqs)
                    + (" (sem o reforço de 'ar': a sibilância já está alta)" if len(eqs) < len(pr["equalizacao"]) else ""))
    if deesser:
        etapas.append(f"deesser=i={pr['de_esser']['intensidade']}:f={pr['de_esser']['frequencia']}")
        decisoes.append(f"de-esser: sibilância em {sib} dB do total (acima de {pr['de_esser']['usar_se_sibilancia_acima_db']})")
    else:
        decisoes.append(f"de-esser: não aplicado (sibilância em {sib} dB do total)")
    c = pr["compressao"]
    etapas.append(f"acompressor=threshold={c['limiar_db']}dB:ratio={c['razao']}:attack={c['ataque_ms']}:release={c['liberacao_ms']}:knee={c['joelho']}:makeup=1")
    decisoes.append(f"compressão moderada {c['razao']}:1 a partir de {c['limiar_db']} dB")
    return ",".join(etapas), decisoes


def _atraso(a, b, sr, max_ms=30):
    """Atraso (amostras) de b em relação a a, por correlação cruzada (FFT), procurado em ±max_ms."""
    from scipy.signal import correlate
    n = min(len(a), len(b), sr * 20)
    m = int(max_ms * sr / 1000)
    c = correlate(b[:n].astype(np.float64), a[:n].astype(np.float64), mode="full", method="fft")
    meio = n - 1
    janela = c[meio - m:meio + m + 1]
    return int(np.argmax(janela)) - m


def _alinhar_tamanho(y, n, atraso):
    if atraso > 0:
        y = y[atraso:]
    elif atraso < 0:
        y = np.concatenate([np.zeros(-atraso, np.float32), y])
    return y[:n] if len(y) >= n else np.concatenate([y, np.zeros(n - len(y), np.float32)])


def tratar(y, sr, medidas, pr=None):
    pr = pr or carregar_preset()
    cad, decisoes = cadeia(pr, medidas)
    # ganho de entrada: leva a voz a um nível de referência ANTES da compressão, para o limiar do compressor valer igual
    # para qualquer arquivo (uma voz baixa não passaria pelo compressor e sobraria tudo para o limitador)
    ref = pr["compressao"].get("nivel_entrada_lufs", -20.0)
    l0 = AU.loudness(y, sr)["integrado_lufs"]
    g0 = 0.0 if l0 is None else ref - l0
    y = (y * (10 ** (g0 / 20))).astype(np.float32)
    decisoes.insert(0, f"ganho de entrada {g0:+.1f} dB (de {l0} para {ref} LUFS) antes da compressão")
    z, _ = AU.filtrar(y, cad, sr)
    atraso1 = _atraso(y, z, sr); z = _alinhar_tamanho(z, len(y), atraso1)
    L = pr["loudness"]
    w = z; reducao = []
    for _ in range(3):                                    # ganho fixo + limitador de pico verdadeiro; 3 passadas no máximo
        med = AU.loudness(w, sr)
        if med["integrado_lufs"] is None:
            break
        ganho = L["alvo_lufs"] - med["integrado_lufs"]
        if abs(ganho) < 0.05 and med["pico_verdadeiro_dbtp"] <= L["pico_verdadeiro_dbtp"] + 0.05:
            break
        g = (w * (10 ** (ganho / 20))).astype(np.float32)
        teto = 10 ** ((L["pico_verdadeiro_dbtp"] - 0.3) / 20)
        lim, _ = AU.filtrar(g, f"aresample=192000:resampler=soxr,alimiter=limit={teto:.5f}:attack=3:release=60:level=disabled:latency=1,"
                                f"aresample={sr}:resampler=soxr", sr)
        lim = _alinhar_tamanho(lim, len(y), _atraso(g, lim, sr))
        w5 = int(0.005 * sr); n5 = len(g) // w5
        env = np.abs(g[:n5 * w5]).reshape(n5, w5).max(1)
        exc = 20 * np.log10(np.maximum(env / teto, 1.0))
        reducao.append({"tempo_com_reducao_pct": round(float(100 * (exc > 0).mean()), 2),
                        "tempo_acima_1db_pct": round(float(100 * (exc > 1).mean()), 2),
                        "tempo_acima_3db_pct": round(float(100 * (exc > 3).mean()), 2), "reducao_max_db": round(float(exc.max()), 1)})
        w = lim
    medf = AU.loudness(w, sr)
    atraso2 = _atraso(z, w, sr)
    if reducao:
        r0 = reducao[0]
        lim_txt = (f"limitador agindo em {r0['tempo_com_reducao_pct']} % do tempo (mais de 1 dB em {r0['tempo_acima_1db_pct']} %, "
                   f"mais de 3 dB em {r0['tempo_acima_3db_pct']} %; máximo {r0['reducao_max_db']} dB, em picos isolados)")
    else:
        lim_txt = "limitador não precisou agir"
    decisoes.append(f"loudness: ganho fixo até {L['alvo_lufs']} LUFS e limitador de pico verdadeiro (sobreamostragem 4×) em "
                    f"{L['pico_verdadeiro_dbtp']} dBTP; resultado {medf['integrado_lufs']} LUFS, {medf['pico_verdadeiro_dbtp']} dBTP; {lim_txt}")
    m = {"passadas_do_limitador": len(reducao), "reducao_de_pico_db": reducao, "resultado": medf}
    m2 = {}
    return w, {"cadeia": cad, "decisoes": decisoes, "atraso_filtros_amostras": int(atraso1), "atraso_loudness_amostras": int(atraso2),
               "loudness": m}
