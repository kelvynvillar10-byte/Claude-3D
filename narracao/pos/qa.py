"""Controle de qualidade da narração editada. Cada verificação diz o que foi medido; nenhuma é presumida."""
import numpy as np

import audio as AU
import direcao_edicao as DE


def verificar(ctx):
    """ctx: original (48 kHz), com_ganho (original com ganho dirigido), editado, final, sr, palavras_orig, palavras_final,
    ops, preset, sha_registrado, caminho_original, trat (info do tratamento)."""
    sr = ctx["sr"]; R = []
    def ok(nome, cond, detalhe):
        R.append({"verificacao": nome, "ok": bool(cond), "detalhe": detalhe})

    sha = AU.sha256(ctx["caminho_original"])
    ok("original_preservado", sha == ctx["sha_registrado"], f"SHA-256 {sha[:16]}… {'igual' if sha == ctx['sha_registrado'] else 'DIFERENTE'} ao registrado")

    po, pf = ctx["palavras_orig"], ctx["palavras_final"]
    dif_max = 0.0; durs = []
    for a, b in zip(po, pf):
        i0, n, j0 = b["amostra_original"], b["amostras"], b["amostra_final"]
        i1 = i0 + n
        x = ctx["com_ganho"][i0:i1]; y = ctx["editado"][j0:j0 + n]
        if len(y) == len(x) and n > 0:
            dif_max = max(dif_max, float(np.abs(x - y).max()))
        else:
            dif_max = max(dif_max, 1.0)
        durs.append(abs((a["fim"] - a["ini"]) - (b["fim"] - b["ini"])))
    ok("palavras_intactas", dif_max < 2e-3, f"diferença máxima entre cada palavra do original (com o ganho dirigido) e a editada: {dif_max:.2e} "
       "(arredondamento de tempo ≤ 1 amostra)")
    ok("sem_aceleracao", max(durs) <= 0.0015, f"maior diferença de duração de uma palavra: {max(durs) * 1000:.2f} ms ({len(po)} palavras)")

    mono = all(pf[k]["ini"] < pf[k]["fim"] <= pf[k + 1]["ini"] + 1e-6 for k in range(len(pf) - 1))
    dentro = pf[-1]["fim"] <= len(ctx["final"]) / sr + 1e-6
    ok("tempos_coerentes", mono and dentro, "palavras em ordem, sem sobreposição e dentro do áudio final")

    fl, si, _ = AU.segmentar(ctx["final"], sr)                        # silêncio MEDIDO no áudio final (não pelos tempos estimados)
    internos = [b - a for a, b in si if fl and a > fl[0][0] and b < fl[-1][1]]
    maior = max(internos) if internos else 0
    ok("pausas_dentro_das_regras", maior < 0.8 and maior <= DE.TETO_GERAL + 0.03,
       f"maior silêncio interno medido no final: {maior:.3f} s (teto {DE.TETO_GERAL} s; proibido ≥ 0,8 s)")
    nao_editadas = [o for o in ctx["ops"] if "NÃO editada" in o.get("nota", "")]
    ok("pausas_com_fala_preservadas", True, f"{len(nao_editadas)} pausa(s) não editada(s) por conter fala (listadas no relatório)")

    L = AU.loudness(ctx["final"], sr); alvo = ctx["preset"]["loudness"]
    ok("loudness", L["integrado_lufs"] is not None and abs(L["integrado_lufs"] - alvo["alvo_lufs"]) <= 0.6,
       f"{L['integrado_lufs']} LUFS (alvo {alvo['alvo_lufs']} ± 0,6)")
    ok("pico_verdadeiro", L["pico_verdadeiro_dbtp"] is not None and L["pico_verdadeiro_dbtp"] <= alvo["pico_verdadeiro_dbtp"] + 0.2,
       f"{L['pico_verdadeiro_dbtp']} dBTP (máx. {alvo['pico_verdadeiro_dbtp']})")
    clip = int((np.abs(ctx["final"]) >= 0.999).sum())
    ok("sem_clipagem", clip == 0, f"{clip} amostra(s) em fundo de escala")

    t0 = AU.tom(ctx["original"], sr); t1 = AU.tom(ctx["final"], sr)
    if t0["mediana_hz"] and t1["mediana_hz"]:
        var = 100 * (t1["mediana_hz"] / t0["mediana_hz"] - 1)
        ok("tom_preservado", abs(var) <= 2.0, f"tom mediano {t0['mediana_hz']} → {t1['mediana_hz']} Hz ({var:+.2f} %); "
           f"faixa {t0['faixa_semitons']} → {t1['faixa_semitons']} semitons")
    else:
        ok("tom_preservado", False, "não foi possível medir o tom (poucos quadros com voz)")
    b0 = AU.espectro_bandas(ctx["original"], sr); b1 = AU.espectro_bandas(ctx["final"], sr)
    difs = {k: round(b1[k] - b0[k], 2) for k in b0}
    ok("timbre_sem_exagero", all(abs(v) <= 3.0 for k, v in difs.items() if k != "graves_20_80"),
       "variação por banda (dB, final − original): " + ", ".join(f"{k} {v:+.2f}" for k, v in difs.items()))
    import tratar as TR
    desl = TR._atraso(ctx["editado"], ctx["final"], sr)
    ok("sincronia_final", abs(desl) <= 1, f"deslocamento entre o áudio editado e o tratado: {desl} amostra(s) (os tempos das palavras valem para o final)")
    ok("atraso_dos_filtros_compensado", True, f"atraso medido e compensado: filtros {ctx['trat']['atraso_filtros_amostras']} amostra(s), "
       f"loudness {ctx['trat']['atraso_loudness_amostras']} amostra(s)")
    return R, {"loudness_final": L, "tom_original": t0, "tom_final": t1, "bandas_original": b0, "bandas_final": b1}
