#!/usr/bin/env python3
"""Heitor rig v2 — testes da fase F4, renderizados e MEDIDOS.

T7 expressões animadas (frente, 3/4 e perfil ao mesmo tempo) + piscadas + olhar + fala de teste com sincronia labial.
T8 teste em cena: fundo 3D estático (Blender, Cycles CPU) + Heitor 2D — entra andando, para, pega a bola na mesa,
   vira para a câmera, mostra a bola e acena.
Saída: testes/T7_*.mp4, testes/T8_*.mp4 (+ folhas) e testes/f4_metricas.json
"""
import copy, json, math, subprocess, sys
from pathlib import Path
import numpy as np, skia

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import heitor_v2 as H   # noqa: E402
import animacao as A    # noqa: E402
import gestos as G      # noqa: E402
import fala as F        # noqa: E402
from testes_f3 import gravar, legenda, OUT, W, HH, FPS, F_P   # noqa: E402

CONT = ["palp_sup", "palp_inf", "pupila", "sorriso", "largura"]   # parâmetros contínuos medidos


def mux(nome, wav):
    v = OUT / f"{nome}.mp4"; tmp = OUT / f"{nome}_tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-i", str(wav), "-c:v", "copy", "-af",
                    "loudnorm=I=-16:TP=-1.6:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest", str(tmp)], check=True)
    tmp.replace(v)


# ------------------------------------------------------------------ T7: expressões animadas + fala
def t7():
    FRASE = "Calma... acho que vai dar tudo certo!"
    T_FALA = 7.7; DUR = 12.0; n = int(DUR * FPS)
    y, palavras = F.gerar(FRASE)
    bocas, rms = F.boca_por_quadro(y, palavras, FPS, n, inicio=T_FALA)
    wav = OUT / "T7_fala.wav"; F.escrever_wav(wav, y, T_FALA, DUR)
    clip = G.Clipe({
        "rosto": [(0.0, G.expr("neutro"), "suave"), (2.4, G.expr("neutro"), "suave"), (2.62, G.expr("surpresa"), "saida"),
                  (3.6, G.expr("surpresa"), "suave"), (3.95, G.expr("medo"), "saida"), (5.0, G.expr("medo"), "suave"),
                  (5.6, G.expr("preocupacao"), "suave"), (6.6, G.expr("preocupacao"), "suave"), (7.15, G.expr("alegria"), "volta"),
                  (11.0, G.expr("alegria"), "suave"), (11.6, G.expr("neutro"), "suave")],
        "olhar": [(0.0, [0.0, 0.0], "suave"), (0.6, [0.0, 0.0], "suave"), (0.85, [-0.9, 0.0], "saida"), (1.4, [-0.9, 0.0], "suave"),
                  (1.65, [0.9, -0.2], "saida"), (2.1, [0.9, -0.2], "suave"), (2.35, [0.0, 0.0], "saida"), (5.6, [0.0, 0.0], "suave"),
                  (5.9, [0.5, 0.4], "suave"), (6.5, [0.5, 0.4], "suave"), (6.8, [0.0, 0.0], "suave")],
        "cabeca": [(0.0, 0.0, "suave"), (0.85, 2.0, "suave"), (1.65, -2.0, "suave"), (2.35, 0.0, "suave"), (2.62, -5.0, "volta"),
                   (3.6, -4.0, "suave"), (3.95, 3.0, "saida"), (5.0, 3.0, "suave"), (5.6, 5.0, "suave"), (6.6, 5.0, "suave"),
                   (7.15, -3.0, "volta"), (11.0, -2.0, "suave"), (11.6, 0.0, "suave")]})
    reg = []

    def rosto_em(q, tt):
        e = clip.valor("rosto", tt)
        e["olhar"] = clip.valor("olhar", tt)
        pf = A.piscada(tt, periodo=3.1, deslocamento=0.5)
        pisc = pf > 0
        if pf > 0:
            e["palp_sup"] = max(e["palp_sup"], 1.0 if pf > 0.9 else pf)
        b = bocas[q]
        if b is not None:   # fala: o desenho da boca vem da fala; o sorriso vem da expressão
            e.update(b)
        return e, pisc

    def quadro(c, q, tt):
        c.clear(0xFFE9E6DF)
        e, pisc = rosto_em(q, tt)
        tremor = 1.2 * math.sin(2 * math.pi * 9 * tt) if 4.0 <= tt <= 5.0 else 0.0
        paineis = (("frente", skia.Rect.MakeLTRB(0, 0, W, 1180), 540, 2700, 150),
                   ("tres_quartos", skia.Rect.MakeLTRB(0, 1190, 540, HH), 270, 1500, 1250),
                   ("perfil", skia.Rect.MakeLTRB(540, 1190, W, HH), 800, 1500, 1250))
        for v, r, x, alt, topo in paineis:
            c.save(); c.clipRect(r)
            c.drawRect(r, skia.Paint(Color=0xFFF3F0EA if v == "frente" else 0xFFE2DED5))
            pose = H.pose_base(v); pose["cabeca"] = clip.valor("cabeca", tt) + tremor
            pose["respira"] = math.sin(2 * math.pi * tt / 2.8)
            H.desenhar(c, x, topo + alt, alt, vista=v, pose=pose, rosto=e)
            c.restore()
            c.drawString({"frente": "FRENTE", "tres_quartos": "3/4", "perfil": "PERFIL"}[v], r.left() + 24, r.bottom() - 24, F_P,
                         skia.Paint(AntiAlias=True, Color=0xFF55607A))
        c.drawLine(540, 1190, 540, HH, skia.Paint(Color=0xFFBFB8AA, StrokeWidth=4))
        legenda(c, "T7 · expressões animadas e fala — Heitor rig v2", q, tt,
                "· falando" if bocas[q] is not None else "")
        reg.append({"t": tt, "e": copy.deepcopy(e), "pisc": pisc, "fala": bocas[q] is not None})
        return reg[-1]

    gravar("T7_expressoes_fala", DUR, quadro)
    mux("T7_expressoes_fala", wav)
    # ---------------- métricas
    trocas_boca, trocas_olho, saltos = [], [], {k: 0.0 for k in CONT}
    for a, b in zip(reg, reg[1:]):
        if not (a["fala"] or b["fala"]) and a["e"]["boca"] != b["e"]["boca"]:
            trocas_boca.append({"t": round(b["t"], 2), "de": a["e"]["boca"], "para": b["e"]["boca"],
                                "abertura_na_troca": round(max(a["e"]["abertura"], b["e"]["abertura"]), 3)})
        if a["e"]["branco"] != b["e"]["branco"]:
            trocas_olho.append({"t": round(b["t"], 2), "escondida_por_piscada": a["e"]["palp_sup"] >= 0.99 or b["e"]["palp_sup"] >= 0.99})
        if not (a["pisc"] or b["pisc"] or a["e"].get("_piscada_troca") or b["e"].get("_piscada_troca")):
            for k in CONT:
                if k == "palp_sup" and (a["e"]["branco"] != b["e"]["branco"] or max(a["e"]["palp_sup"], b["e"]["palp_sup"]) >= 0.99):
                    continue
                if k in ("largura", "sorriso") and (a["fala"] or b["fala"]):
                    continue
                saltos[k] = max(saltos[k], abs(a["e"][k] - b["e"][k]))
    # piscadas: blocos de quadros com pálpebra animada pela piscada automática
    blocos, i = [], 0
    while i < len(reg):
        if reg[i]["pisc"]:
            j = i
            while j < len(reg) and reg[j]["pisc"]:
                j += 1
            blocos.append(j - i); i = j
        else:
            i += 1
    # sincronia labial: abertura × energia do áudio (correlação por atraso, em quadros)
    ab = np.array([r["e"]["abertura"] if r["fala"] else 0.0 for r in reg]); en = rms
    q0, q1 = int(T_FALA * FPS), int(T_FALA * FPS + len(y) / F.SR * FPS)
    corr = {}
    for lag in range(-4, 5):
        a_ = ab[q0:q1]; b_ = np.roll(en, lag)[q0:q1]
        corr[lag] = float(np.corrcoef(a_, b_)[0, 1])
    lag_max = max(corr, key=corr.get)
    sil = [i for i in range(q0, q1) if en[i] < 0.05]
    fech = sum(1 for i in sil if ab[i] < 0.08)
    # pausas de verdade (>= 0,2 s, ex.: depois de "Calma..."): a boca precisa fechar
    pausas, i = [], q0
    while i < q1:
        if en[i] < 0.05:
            j = i
            while j < q1 and en[j] < 0.05:
                j += 1
            if j - i >= 6:
                pausas.append((i, j))
            i = j
        else:
            i += 1
    fech_p = [sum(1 for k in range(a_, b_) if ab[k] < 0.08) / (b_ - a_) for a_, b_ in pausas]
    return {"duracao_s": DUR, "frase": FRASE, "fala_inicio_s": T_FALA, "fala_duracao_s": round(len(y) / F.SR, 2),
            "palavras": [(p[0], round(p[1] + T_FALA, 2), round(p[2] + T_FALA, 2)) for p in palavras],
            "trocas_de_boca_fora_da_fala": trocas_boca, "trocas_de_estilo_de_olho": trocas_olho,
            "maior_salto_por_quadro_parametros_continuos": {k: round(v, 3) for k, v in saltos.items()},
            "piscadas": len(blocos), "piscada_duracao_quadros": sorted(set(blocos)),
            "sincronia_atraso_quadros_melhor": lag_max, "sincronia_correlacao_no_melhor": round(corr[lag_max], 3),
            "sincronia_correlacao_atraso_0": round(corr[0], 3),
            "silencio_na_fala_quadros": len(sil), "silencio_com_boca_fechada_pct": round(100 * fech / max(1, len(sil)), 1),
            "pausas_longas": len(pausas), "pausas_longas_boca_fechada_pct": [round(100 * x, 1) for x in fech_p]}



# ------------------------------------------------------------------ T8: teste em cena (fundo 3D + Heitor 2D)
ROB = skia.Typeface.MakeFromFile(str(AQUI.parents[3] / "assets" / "fontes" / "RobotoCondensed-ExtraBold.ttf"))


def marca_dagua(c):
    """Marca d'água oficial "MODO CURIOSO" (mesma especificação do piloto 01: Roboto Condensed ExtraBold, 30 px)."""
    alt = 30; f = skia.Font(ROB, alt / 0.711)
    w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
    x = W - 40 - (w1 + esp + w2); base = 60 + alt
    c.drawString("MODO", x, base, f, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(153, 255, 255, 255)))
    c.drawString("CURIOSO", x + w1 + esp, base, f, skia.Paint(AntiAlias=True, Color=0xFFFFC21F))


def t8():
    REC = AQUI.parent / "recursos" / "cena_t8"
    an = json.loads((REC / "ancoras.json").read_text())
    fundo = skia.Image.open(str(REC / "fundo.png"))
    ALT = an["altura_heitor_px"]; U = ALT / 4; Y_PE = an["pe_x0"][1]; X0 = an["pe_x0"][0]; PPM = an["px_por_m"]
    HM = an["alt_heitor_m"] / 4                                  # metros por H
    MESA_Y = (an["mesa_tampo_no_plano_x0"][1] - Y_PE) / U         # tampo da mesa no plano do personagem (H, y para baixo)
    P = A.CAMINHADA; T = P["T"]; L = H.LAYOUT["perfil"]; TORN = H.PROP["tornozelo"]
    TS, DS = 2 * T, 0.45                                         # para no contato do calcanhar direito; 0,45 s para assentar
    _, dS = A.pose_locomocao(TS, "perfil")
    Ad, Ae = dS["pernas"]["d"]["alvo"], dS["pernas"]["e"]["alvo"]
    XS, PEL_S = dS["pelve_x"], dS["pelve_y"]
    ang_e0 = A._pe_ciclo(TS, 0.5, P, L["coxa_e"][0])[2]; ang_d0 = A._pe_ciclo(TS, 0.0, P, L["coxa_d"][0])[2]
    XF = Ad[0] - L["coxa_d"][0]                                  # pelve final: quadril direito sobre o pé direito
    x_ini = -0.02 / HM - XF                                      # início (H, mundo da cena; 0 = centro da tela)
    sx = lambda xh: X0 + (x_ini + xh) * U                        # noqa: E731  mundo do personagem (H) → tela
    bola = G.Objeto((0.30 / HM) - x_ini, MESA_Y - 0.095)         # bola em x = 0,30 m, sobre o tampo
    apoio = ((0.22 / HM) - x_ini, (0.82 / HM) - x_ini, MESA_Y)
    peito_perfil = (XF + 0.42, -2.32); peito_frente = (XF - 0.58, -2.12); alto = (XF - 0.95, -3.55); lado = (XF - 0.66, -1.68)

    def pernas_parada(s):
        X = XS + (XF - XS) * s; pel = PEL_S + (H.PROP["barra_camisa"] - PEL_S) * s
        exf = XF + L["coxa_e"][0]
        pes = {"d": (Ad[0], TORN, ang_d0 * (1 - s)),
               "e": (Ae[0] + (exf - Ae[0]) * s, TORN + (Ae[1] - TORN) * (1 - s) + 0.10 * math.sin(math.pi * s), ang_e0 * (1 - s))}
        p = {}
        for lado_, (ax, ay, pang) in pes.items():
            a1, a2, _, _ = A.ik2(X + L[f"coxa_{lado_}"][0], -(pel - 0.02), ax, -ay, A.L_COXA, A.L_CANELA, joelho=1)
            p[f"coxa_{lado_}"] = a1; p[f"canela_{lado_}"] = a2 - a1; p[f"pe_{lado_}"] = pang - a2
        p["raiz"] = [0.0, -(pel - H.PROP["barra_camisa"])]
        return X, p, pes

    pw_ts, _ = A.pose_locomocao(TS, "perfil")
    C = G.Clipe({
        "rosto": [(0.0, G.expr("neutro"), "suave"), (2.0, G.expr("neutro"), "suave"), (2.3, G.expr("pensativo"), "suave"),
                  (3.1, G.expr("pensativo"), "suave"), (3.4, G.expr("alegria"), "suave"), (4.3, G.expr("alegria"), "suave"),
                  (4.5, G.expr("surpresa"), "saida"), (4.95, G.expr("surpresa"), "suave"), (5.25, G.expr("alegria"), "volta")],
        "cabeca": [(0.0, 0.0, "suave"), (2.2, 0.0, "suave"), (2.5, 10.0, "suave"), (3.3, 8.0, "suave"), (3.8, 0.0, "suave"),
                   (4.6, -6.0, "suave"), (5.4, -6.0, "suave"), (5.9, 0.0, "suave"), (6.4, 3.0, "suave"), (7.9, 3.0, "suave"), (8.3, 0.0, "suave")],
        "tronco": [(0.0, 0.0, "suave"), (2.2, 0.0, "suave"), (2.9, 7.0, "suave"), (3.25, 7.0, "suave"), (3.8, 0.0, "suave")],
        "olhar": [(0.0, [0.0, 0.0], "suave"), (2.2, [0.0, 0.0], "suave"), (2.5, [0.3, 0.7], "suave"), (3.6, [0.3, 0.7], "suave"),
                  (3.9, [0.0, 0.0], "suave"), (4.5, [0.0, 0.0], "suave"), (4.8, [-0.8, -0.6], "suave"), (5.5, [-0.8, -0.6], "suave"),
                  (5.8, [0.0, 0.0], "suave")],
        "alvo": [(2.2, None, "suave"), (2.3, "rep", "suave"), (2.95, [bola.x, bola.y], "suave"), (3.25, [bola.x, bola.y], "suave"),
                 (3.85, list(peito_perfil), "suave"), (3.95, list(peito_perfil), "suave"), (4.35, list(peito_frente), "suave"),
                 (4.5, list(peito_frente), "suave"), (5.1, list(alto), "volta"), (5.6, list(alto), "suave"), (6.1, list(lado), "suave")],
        "dedos_d": [(0.0, G.mao("relaxada"), "suave"), (2.4, G.mao("relaxada"), "suave"), (2.85, G.mao("aberta"), "suave"),
                    (2.95, G.mao("aberta"), "suave"), (3.2, G.mao("segurar"), "suave")],
        "braco_e": [(0.0, 0.0, "suave"), (6.1, 0.0, "suave"), (6.45, -108.0, "volta"), (7.8, -108.0, "suave"), (8.3, 0.0, "suave")],
        "antebraco_e": [(0.0, 0.0, "suave"), (6.1, 0.0, "suave"), (6.45, -62.0, "suave"), (7.8, -62.0, "suave"), (8.3, 0.0, "suave")],
        "dedos_e": [(0.0, G.mao("relaxada"), "suave"), (6.1, G.mao("relaxada"), "suave"), (6.4, G.mao("acenar"), "suave"),
                    (7.8, G.mao("acenar"), "suave"), (8.3, G.mao("relaxada"), "suave")]})
    est = {"preso": False, "rep": None}
    _, p_fim, _ = pernas_parada(1.0)

    def vista_em(tt):
        return "perfil" if tt < 4.08 else ("tres_quartos" if tt < 4.22 else "frente")

    def alvo_em(tt):
        ks = C.canais["alvo"]
        if tt < ks[1][0]:
            return None
        if est["rep"] is None:
            return None
        pts = [(t, est["rep"] if v == "rep" else v, cv) for t, v, cv in ks[1:]]
        return G.Clipe({"a": pts}).valor("a", tt)

    def quadro(c, q, tt):
        c.drawImage(fundo, 0, 0)
        v = vista_em(tt)
        pose = H.pose_base(v); pose["respira"] = math.sin(2 * math.pi * tt / 2.7)
        apoio_pes = {}
        if tt < TS:
            pw, dw = A.pose_locomocao(tt, "perfil"); pose.update(pw); X = dw["pelve_x"]
            apoio_pes = {s: dw["pernas"][s]["apoio"] for s in ("d", "e")}
        elif tt < TS + DS:
            s = A.suave((tt - TS) / DS); X, pl, _ = pernas_parada(s); pose.update(pl)
            for k in ("braco_d", "braco_e", "antebraco_d", "antebraco_e", "tronco", "cabeca"):
                pose[k] = pw_ts[k] * (1 - s)
            apoio_pes = {"d": True, "e": s >= 1.0}
        else:
            X = XF; apoio_pes = {"d": True, "e": True}
            if v == "perfil":
                pose.update(p_fim)
        # parte de cima: rosto, cabeça, tronco, mãos
        e = C.valor("rosto", tt); e["olhar"] = C.valor("olhar", tt)
        pf = A.piscada(tt, periodo=3.3, deslocamento=1.1)
        if pf > 0:
            e["palp_sup"] = max(e["palp_sup"], 1.0 if pf > 0.9 else pf)
        if tt >= TS + DS:
            pose["cabeca"] = C.valor("cabeca", tt); pose["tronco"] = C.valor("tronco", tt) if v == "perfil" else 0.0
        pose["dedos_d"] = C.valor("dedos_d", tt)
        pose["mao_vista_d"] = "lado" if v == "perfil" else "palma"   # de frente: a bola aparece na palma
        for k in ("braco_e", "antebraco_e", "dedos_e"):
            if tt >= 6.0:
                pose[k] = C.valor(k, tt)
        if 6.45 <= tt <= 7.8:
            o = math.sin(2 * math.pi * 2.2 * (tt - 6.45)); pose["antebraco_e"] += 24 * o; pose["mao_e"] = -8 * o
        if tt >= 6.0:
            pose["mao_vista_e"] = "palma"
        erro = 0.0
        if tt >= 2.3 and est["rep"] is None:
            est["rep"] = [X + a for a in G.encaixe_mundo(pose, v, "d")][:1] + [G.encaixe_mundo(pose, v, "d")[1]]
        alvo = alvo_em(tt)
        if alvo is not None:
            erro = G.ik_braco(pose, v, "d", (alvo[0] - X, alvo[1]), cotovelo=None)
        ex_, ey_ = G.encaixe_mundo(pose, v, "d"); sx_, sy_ = X + ex_, ey_
        fecho = pose["dedos_d"]["indicador"][0] / 55.0
        if not est["preso"] and fecho > 0.6 and math.hypot(sx_ - bola.x, sy_ - bola.y) < 0.06:
            est["preso"] = True; bola.segurado = True
        if est["preso"]:
            bola.x, bola.y = sx_, sy_
        else:
            bola.passo(1 / FPS, 0.0, apoio)
        # sombras de contato (chão no plano do personagem)
        M = H.esqueleto(pose, v)
        for s in ("d", "e"):
            pp = M[f"pe_{s}"].mapXY(0.05, 0.22); a = max(0.0, 1 - (-pp.y()) / 0.6)
            if a > 0:
                c.drawOval(skia.Rect.MakeXYWH(sx(X + pp.x()) - 0.24 * U, Y_PE - 0.035 * U, 0.48 * U, 0.07 * U),
                           skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(85 * a), 60, 35, 20),
                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
        if not est["preso"]:
            if abs(bola.y - (MESA_Y - bola.r)) < 1e-3:
                c.drawOval(skia.Rect.MakeXYWH(sx(bola.x) - 0.11 * U, Y_PE + MESA_Y * U - 0.02 * U, 0.22 * U, 0.04 * U),
                           skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(70, 60, 35, 20),
                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
            bola.desenhar(c, sx(bola.x), Y_PE + bola.y * U, U)
        else:
            pose["objeto_d"] = lambda cc, vv: bola.desenhar(cc, *H.ENCAIXE[vv], 1.0)
        H.desenhar(c, sx(X), Y_PE, ALT, vista=v, pose=pose, rosto=e)
        marca_dagua(c)
        c.drawString(f"T8 · em cena · rig v2 · {q:03d} · {tt:4.2f} s", 40, 1880, F_P, skia.Paint(AntiAlias=True, Color=0xFF1F2A44))
        pes_mundo = {s: (X + M[f"pe_{s}"].mapXY(0, 0).x(), -M[f"pe_{s}"].mapXY(0, 0).y()) for s in ("d", "e")}
        return {"t": tt, "vista": v, "X": X, "pes": pes_mundo, "apoio": apoio_pes, "bola": (bola.x, bola.y), "encaixe": (sx_, sy_),
                "preso": est["preso"], "erro_ik": erro}

    reg = gravar("T8_em_cena", 8.6, quadro)
    # ---------------- métricas
    desl = 0.0
    for a, b in zip(reg, reg[1:]):
        for s in ("d", "e"):
            if a["apoio"].get(s) and b["apoio"].get(s) and a["vista"] == b["vista"]:   # troca de vista não é deslize
                # pé de apoio: só conta enquanto o calcanhar está no chão (tornozelo na altura de repouso)
                if abs(a["pes"][s][1] - TORN) < 0.005 and abs(b["pes"][s][1] - TORN) < 0.005:
                    desl = max(desl, abs(b["pes"][s][0] - a["pes"][s][0]))
    presos = [r for r in reg if r["preso"]]
    giro = [r for r in reg if 3.95 <= r["t"] <= 4.4]
    passo_giro = max(math.hypot(b["bola"][0] - a["bola"][0], b["bola"][1] - a["bola"][1]) for a, b in zip(giro, giro[1:]))
    # OCR das marcas num quadro de frente (estampa, pôster e marca d'água)
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); quadros_ocr = {}
    for tq in (5.3, 7.0):
        img = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(tq), "-i", str(OUT / "T8_em_cena.mp4"), "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
        arr = np.frombuffer(img, np.uint8).reshape(HH, W, 3).copy()
        quadros_ocr[tq] = [t for _, t, cf in (ocr(arr)[0] or [])]
    todos = " | ".join(quadros_ocr[7.0])
    # marca no cenário (pôster, ID-004): em TODOS os quadros, a região do pôster tem de ser igual ao fundo (nada na frente)
    (x0, y1), (x1, y0) = an["poster_cantos"]; x0, y0 = int(x0) + 4, int(y0) + 4; x1, y1 = x0 + (int(x1) - 4 - x0) // 2 * 2, y0 + (int(y1) - 4 - y0) // 2 * 2
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUT / "T8_em_cena.mp4"), "-vf", f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(bruto, np.uint8).reshape(-1, y1 - y0, x1 - x0, 3).astype(np.int16)
    # referência: o quadro 0 (o Heitor ainda fora da tela), decodificado do mesmo vídeo — descarta a diferença de
    # compressão (H.264 4:2:0 nas bordas do texto), que não é oclusão
    ref = fr[0]
    cobertura = [float(np.mean(np.abs(f - ref).max(axis=2) > 48)) for f in fr]
    return {"duracao_s": 8.6, "fundo_blender": {"render_s": an["render_s"], "amostras": an["amostras"], "resolucao": [an["W"], an["H"]]},
            "escala_heitor_px": round(ALT, 1), "caminhada_deslize_pe_apoio_max_H": round(desl, 4),
            "pega_em_s": next((round(r["t"], 2) for r in reg if r["preso"]), None), "quadros_segurando": len(presos),
            "distancia_bola_encaixe_enquanto_segura_max_H": round(max(math.hypot(r["encaixe"][0] - r["bola"][0], r["encaixe"][1] - r["bola"][1]) for r in presos), 5) if presos else None,
            "erro_ik_max_H": round(max(r["erro_ik"] for r in reg), 4), "giro_maior_passo_da_bola_por_quadro_H": round(passo_giro, 3),
            "poster_marca_coberta_max_pct_dos_pixels": round(100 * max(cobertura), 3),
            "ocr_quadro_7s": todos, "ocr_quadro_5_3s": " | ".join(quadros_ocr[5.3])}


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "f4_metricas.json"
    res = json.loads(caminho.read_text()) if caminho.exists() else {}
    testes = [("T7_expressoes_fala", t7)]
    if "t8" in globals():
        testes.append(("T8_em_cena", globals()["t8"]))
    for nome, f in testes:
        if so and nome not in so:
            continue
        H.AUDITORIA = []
        res[nome] = f()
        res[nome]["quadros_com_cotovelo_invertido"] = sum(1 for v, p in H.AUDITORIA for l in ("d", "e") if G.cotovelo_invertido(p, v, l)[0])
        H.AUDITORIA = None
        print(nome, json.dumps(res[nome], ensure_ascii=False))
    caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1))
