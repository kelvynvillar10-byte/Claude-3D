#!/usr/bin/env python3
"""Heitor rig v2 (PROPOSTA) — testes da fase F3 (mãos e gestos), renderizados e MEDIDOS.

T4 dedos individuais · T5 segurar e soltar · T6 acenar e apontar · T6b reações (susto e comemoração).
Saída: testes/T4_*.mp4, T5_*.mp4, T6_*.mp4 (+ folhas) e testes/f3_metricas.json
"""
import copy, json, math, subprocess, sys
from pathlib import Path
import numpy as np, skia

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import heitor_v2 as H   # noqa: E402
import animacao as A    # noqa: E402
import gestos as G      # noqa: E402

OUT = AQUI.parent / "testes"; OUT.mkdir(exist_ok=True)
W, HH, FPS = 1080, 1920, 30
ALT = 1150; U = ALT / 4; CHAO = 1640; CX = W / 2
F_L = skia.Font(H.NUNITO, 34); F_P = skia.Font(H.NUNITO, 28)
DEDOS = ["polegar", "indicador", "medio", "anelar", "minimo"]


def estudio(c, chao=True):
    c.clear(0xFFE9E6DF)
    if chao:
        grad = skia.GradientShader.MakeLinear([skia.Point(0, CHAO), skia.Point(0, HH)], [0xFFCFC9BE, 0xFFB9B2A6])
        c.drawRect(skia.Rect.MakeLTRB(0, CHAO, W, HH), skia.Paint(Shader=grad))
        c.drawLine(0, CHAO, W, CHAO, skia.Paint(AntiAlias=True, Color=0xFF8C8577, StrokeWidth=3))


def legenda(c, rotulo, q, t, extra=""):
    c.drawString(rotulo, 40, 70, F_L, skia.Paint(AntiAlias=True, Color=0xFF1F2A44))
    c.drawString(f"quadro {q:03d} · t={t:4.2f} s {extra}", 40, 115, F_L, skia.Paint(AntiAlias=True, Color=0xFF55607A))


def gravar(nome, dur, quadro, folha=(12, 0)):
    n = int(round(dur * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{HH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / f"{nome}.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); reg = []
    for q in range(n):
        s = skia.Surface(W, HH); c = s.getCanvas()
        reg.append(quadro(c, q, q / FPS))
        pr.stdin.write(s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
    pr.stdin.close(); pr.wait()
    passo = max(1, n // (folha[0] * 2))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"{nome}.mp4"), "-vf",
                    f"select='not(mod(n\\,{passo}))',scale=216:384,tile={folha[0]}x{math.ceil(n / passo / folha[0])}", "-frames:v", "1",
                    str(OUT / f"{nome}_folha.jpg")])
    return reg


# ------------------------------------------------------------------ T4: dedos individuais
def t4():
    k = []  # quadros-chave da mão
    t = 0.0; k.append((t, G.mao("aberta"), "suave")); t = 0.4; k.append((t, G.mao("aberta"), "suave"))
    janelas = {}
    for d in DEDOS:   # cada dedo dobra e volta sozinho
        m = G.mao("aberta"); m[d] = [65, 70] if d == "polegar" else [90, 95, 60]
        janelas[d] = (t, t + 0.6)
        k.append((t + 0.3, m, "suave")); k.append((t + 0.6, G.mao("aberta"), "suave")); t += 0.6
    for n in range(1, 6):   # contagem
        k.append((t + 0.4, G.mao(f"conta_{n}"), "volta")); t += 0.4
    k.append((t + 0.4, G.mao("punho"), "volta")); t += 0.4
    k.append((t + 0.45, G.mao("aberta"), "volta")); t += 0.45
    t_onda = t + 0.1; dur = t + 1.6
    clip = G.Clipe({"mao": k})

    def mao_em(tt):
        m = clip.valor("mao", tt)
        if tt > t_onda:   # "onda" dos dedos (do mínimo ao indicador), defasada
            for i, d in enumerate(["minimo", "anelar", "medio", "indicador"]):
                a = max(0.0, math.sin(2 * math.pi * 1.6 * (tt - t_onda) - i * 0.7)) * 55
                m[d] = [a, a * 0.8, a * 0.5]
        return m

    def quadro(c, q, tt):
        estudio(c, chao=False)
        m = mao_em(tt)
        for x, v, rot in ((260, "dorso", "DORSO"), (820, "palma", "PALMA")):
            c.save(); c.translate(x, 560); c.scale(1700, 1700); H.desenhar_mao(c, m, v, False, 1); c.restore()
            c.drawString(rot, x - 50, 1420, F_P, skia.Paint(AntiAlias=True, Color=0xFF1F2A44))
        ativo = next((d for d, (a, b) in janelas.items() if a <= tt < b), "")
        legenda(c, "T4 · dedos individuais — Heitor rig v2 (PROPOSTA)", q, tt, f"· {ativo}")
        return {"t": tt, "mao": copy.deepcopy(m)}

    reg = gravar("T4_dedos_individuais", dur, quadro)
    # métricas: isolamento de cada dedo na sua janela, limites, continuidade
    iso = {}
    for d, (a, b) in janelas.items():
        outros = [o for o in DEDOS if o != d]
        sel = [r for r in reg if a <= r["t"] < b]
        mov_proprio = max(max(r["mao"][d]) for r in sel) - min(max(r["mao"][d]) for r in sel)
        mov_outros = max(abs(r["mao"][o][j] - sel[0]["mao"][o][j]) for r in sel for o in outros for j in range(len(r["mao"][o])))
        iso[d] = {"movimento_proprio_graus": round(mov_proprio, 1), "movimento_dos_outros_graus": round(mov_outros, 2)}
    todos = [v for r in reg for d in DEDOS for v in r["mao"][d]]
    salto = max(abs(reg[i + 1]["mao"][d][j] - reg[i]["mao"][d][j]) for i in range(len(reg) - 1) for d in DEDOS for j in range(len(reg[i]["mao"][d])))
    return {"duracao_s": round(dur, 2), "isolamento": iso, "angulo_min_max": [round(min(todos), 1), round(max(todos), 1)],
            "maior_variacao_graus_por_quadro": round(salto, 1)}


# ------------------------------------------------------------------ T5: segurar e soltar
def t5():
    vista = "perfil"
    base = H.pose_base(vista); base["mao_vista_d"] = "lado"
    rest = G.encaixe_mundo(base, vista, "d")
    bola = G.Objeto(0.74, -1.725 - 0.095)
    mesa = (0.5, 0.98, -1.725)   # x0, x1, y do tampo (y para baixo)
    peito = (0.40, -2.2); solta = (0.47, -1.98)
    alvos = G.Clipe({"alvo": [(0.0, list(rest), "suave"), (0.45, list(rest), "suave"), (1.15, [bola.x, bola.y], "suave"),
                              (1.45, [bola.x, bola.y], "suave"), (2.15, list(peito), "suave"), (2.8, list(peito), "suave"),
                              (3.3, list(solta), "suave"), (3.6, list(solta), "suave"), (4.4, list(rest), "suave")],
                     "dedos_d": [(0.0, G.mao("relaxada"), "suave"), (0.6, G.mao("relaxada"), "suave"), (1.0, G.mao("aberta"), "suave"),
                                 (1.15, G.mao("aberta"), "suave"), (1.45, G.mao("segurar"), "suave"), (3.32, G.mao("segurar"), "suave"),
                                 (3.44, G.mao("aberta"), "saida"), (3.9, G.mao("aberta"), "suave"), (4.4, G.mao("relaxada"), "suave")],
                     "tronco": [(0.0, 0.0, "suave"), (0.5, 0.0, "suave"), (1.15, 9.0, "suave"), (1.5, 9.0, "suave"), (2.1, 2.0, "suave"),
                                (3.3, 4.0, "suave"), (4.4, 0.0, "suave")],
                     "cabeca": [(0.0, 0.0, "suave"), (0.6, 8.0, "suave"), (1.6, 0.0, "suave"), (2.2, -4.0, "suave"), (3.4, 6.0, "suave"),
                                (3.8, 14.0, "suave"), (4.6, 10.0, "suave")],
                     "rosto": [(0.0, G.expr("neutro"), "suave"), (0.5, G.expr("pensativo"), "suave"), (1.6, G.expr("alegria"), "suave"),
                               (3.2, G.expr("alegria"), "suave"), (3.55, G.expr("surpresa"), "saida"), (4.3, G.expr("preocupacao"), "suave")]})
    estado = {"preso": False, "solto_em": None}

    def quadro(c, q, tt):
        estudio(c)
        pose = H.pose_base(vista); pose["mao_vista_d"] = "lado"
        pose["dedos_d"] = alvos.valor("dedos_d", tt); pose["tronco"] = alvos.valor("tronco", tt); pose["cabeca"] = alvos.valor("cabeca", tt)
        pose["respira"] = math.sin(2 * math.pi * tt / 2.6)
        alvo = alvos.valor("alvo", tt)
        erro = G.ik_braco(pose, vista, "d", alvo, cotovelo=-1)
        sx, sy = G.encaixe_mundo(pose, vista, "d")
        fecho = pose["dedos_d"]["indicador"][0] / 55.0
        if not estado["preso"] and estado["solto_em"] is None and fecho > 0.6 and math.hypot(sx - bola.x, sy - bola.y) < 0.06:
            estado["preso"] = True; bola.segurado = True
        if estado["preso"] and tt >= 3.36:
            estado["preso"] = False; bola.segurado = False; estado["solto_em"] = tt
            bola.vx = (sx - bola.hist[-1][0]) * FPS if bola.hist else 0; bola.vy = (sy - bola.hist[-1][1]) * FPS if bola.hist else 0
        if estado["preso"]:
            bola.x, bola.y = sx, sy
        else:
            bola.passo(1 / FPS, 0.0, mesa)
        bola.hist.append((bola.x, bola.y))
        # mesa (desenho próprio, madeira)
        mx0, mx1, my = mesa
        c.drawRect(skia.Rect.MakeLTRB(CX + mx0 * U, CHAO + my * U, CX + mx1 * U, CHAO + (my + 0.06) * U), H.tinta(0xFF8A5A3B))
        for xx in (mx0 + 0.05, mx1 - 0.1):
            c.drawRect(skia.Rect.MakeLTRB(CX + xx * U, CHAO + (my + 0.06) * U, CX + (xx + 0.05) * U, CHAO), H.tinta(0xFF6B4630))
        e = alvos.valor("rosto", tt); e = A.rosto_com_piscada("neutro", tt) if False else e
        if estado["preso"]:
            pose["objeto_d"] = lambda cc, v: bola.desenhar(cc, *H.ENCAIXE[v], 1.0 / U * U)
            H.desenhar(c, CX, CHAO, ALT, vista=vista, pose=pose, rosto=e)
        else:
            H.desenhar(c, CX, CHAO, ALT, vista=vista, pose=pose, rosto=e)
            bola.desenhar(c, CX + bola.x * U, CHAO + bola.y * U, U)
        legenda(c, "T5 · segurar e soltar — Heitor rig v2 (PROPOSTA)", q, tt, "· " + ("segurando" if estado["preso"] else ("solta" if estado["solto_em"] else "livre")))
        return {"t": tt, "encaixe": (sx, sy), "bola": (bola.x, bola.y), "preso": estado["preso"], "erro_ik": erro}

    reg = gravar("T5_segurar_soltar", 5.2, quadro)
    presos = [r for r in reg if r["preso"]]
    dist = [math.hypot(r["encaixe"][0] - r["bola"][0], r["encaixe"][1] - r["bola"][1]) for r in presos]
    contato = next((r for r in reg if r["preso"]), None)
    return {"quadros_segurando": len(presos), "pega_em_s": round(contato["t"], 2) if contato else None,
            "solta_em_s": estado["solto_em"] and round(estado["solto_em"], 2),
            "distancia_bola_encaixe_enquanto_segura_max_H": round(max(dist), 5) if dist else None,
            "erro_ik_max_H": round(max(r["erro_ik"] for r in reg), 4),
            "bola_atravessa_chao": any(r["bola"][1] > -bola.r + 1e-6 for r in reg),
            "bola_final_no_chao": abs(reg[-1]["bola"][1] + bola.r) < 0.01}


# ------------------------------------------------------------------ T6: acenar e apontar
def t6():
    vista = "frente"; XP = CX - 100; ESTRELA = (975, 720)   # pés do Heitor e alvo na tela
    alvo_ponto = ((ESTRELA[0] - XP) / U, (ESTRELA[1] - CHAO) / U)   # alvo no mundo do personagem (H)
    clip = G.Clipe({
        "braco_d": [(0.0, 0.0, "suave"), (0.3, 0.0, "suave"), (0.8, 152.0, "volta"), (2.7, 152.0, "suave"), (3.2, 0.0, "suave")],
        "antebraco_d": [(0.0, 0.0, "suave"), (0.3, 0.0, "suave"), (0.8, -28.0, "suave"), (2.7, -28.0, "suave"), (3.2, 0.0, "suave")],
        "dedos_d": [(0.0, G.mao("relaxada"), "suave"), (0.5, G.mao("relaxada"), "suave"), (0.8, G.mao("acenar"), "suave"),
                    (2.7, G.mao("acenar"), "suave"), (3.2, G.mao("relaxada"), "suave")],
        "dedos_e": [(0.0, G.mao("relaxada"), "suave"), (3.3, G.mao("relaxada"), "suave"), (3.75, G.mao("apontar"), "suave"),
                    (5.3, G.mao("apontar"), "suave"), (5.8, G.mao("relaxada"), "suave")],
        "peso_aponta": [(0.0, 0.0, "suave"), (3.3, 0.0, "suave"), (3.8, 1.0, "volta"), (5.3, 1.0, "suave"), (5.9, 0.0, "suave")],
        "cabeca": [(0.0, 0.0, "suave"), (0.8, -4.0, "suave"), (2.7, -4.0, "suave"), (3.4, 0.0, "suave"), (3.8, -7.0, "suave"),
                   (5.3, -7.0, "suave"), (5.9, 0.0, "suave")],
        "rosto": [(0.0, G.expr("neutro"), "suave"), (0.6, G.expr("alegria"), "suave"), (2.8, G.expr("alegria"), "suave"),
                  (3.5, G.expr("surpresa"), "suave"), (5.4, G.expr("surpresa"), "suave"), (6.0, G.expr("neutro"), "suave")]})

    def quadro(c, q, tt):
        estudio(c)
        pose = H.pose_base(vista)
        for k in ("braco_d", "antebraco_d", "dedos_d", "dedos_e", "cabeca"):
            pose[k] = clip.valor(k, tt)
        pose["mao_vista_d"] = "palma"; pose["mao_vista_e"] = "dorso"; pose["respira"] = math.sin(2 * math.pi * tt / 2.6)
        if 0.8 <= tt <= 2.7:   # aceno: antebraço e punho oscilam (2,2 Hz)
            o = math.sin(2 * math.pi * 2.2 * (tt - 0.8))
            pose["antebraco_d"] += 24 * o; pose["mao_d"] = 8 * o
        w = clip.valor("peso_aponta", tt); err_ang = None
        if w > 0:
            alvo_pose = copy.deepcopy(pose); G.mira_braco(alvo_pose, vista, "e", alvo_ponto)
            for k in ("braco_e", "antebraco_e", "mao_e"):
                pose[k] = pose[k] * (1 - w) + alvo_pose[k] * w
        if 4.0 <= tt <= 5.3:   # segurando a mira: erro medido no esqueleto desenhado
            err_ang = abs(G.erro_mira(pose, vista, "e", alvo_ponto))
        # alvo (estrela de desenho próprio)
        ax, ay = ESTRELA
        est = skia.Path()
        for i in range(10):
            r = 34 if i % 2 == 0 else 14; a = math.pi / 2 + i * math.pi / 5
            (est.moveTo if i == 0 else est.lineTo)(ax + r * math.cos(a), ay - r * math.sin(a))
        est.close(); c.drawPath(est, H.tinta(0xFFFFC21F)); c.drawPath(est, H.contorno(3))
        H.desenhar(c, XP, CHAO, ALT, vista=vista, pose=pose, rosto=clip.valor("rosto", tt))
        legenda(c, "T6 · acenar e apontar — Heitor rig v2 (PROPOSTA)", q, tt)
        return {"t": tt, "antebraco_d": pose["antebraco_d"], "erro_mira_graus": err_ang}

    reg = gravar("T6_acenar_apontar", 6.2, quadro)
    ac = [r for r in reg if 0.9 <= r["t"] <= 2.6]
    sinal = np.array([r["antebraco_d"] for r in ac]); sinal = sinal - sinal.mean()
    esp = np.abs(np.fft.rfft(sinal * np.hanning(len(sinal)), n=4096)); fr = np.fft.rfftfreq(4096, 1 / FPS)
    mira = [r["erro_mira_graus"] for r in reg if r["erro_mira_graus"] is not None]
    return {"aceno_frequencia_hz_medida": round(float(fr[np.argmax(esp[1:]) + 1]), 2), "aceno_frequencia_hz_pedida": 2.2,
            "aceno_amplitude_antebraco_graus": round(float(sinal.max() - sinal.min()) / 2, 1),
            "apontar_erro_mira_max_graus": round(max(mira), 3), "apontar_quadros_medidos": len(mira)}


# ------------------------------------------------------------------ T6b: reações
def t6b():
    vista = "frente"
    clip = G.Clipe({
        "raiz_y": [(0.0, 0.0, "suave"), (0.8, 0.0, "suave"), (0.93, 0.11, "saida"), (1.12, -0.22, "saida"), (1.32, 0.09, "suave"),
                   (1.5, 0.0, "suave"), (2.9, 0.0, "suave"), (3.05, 0.11, "saida"), (3.3, -0.28, "saida"), (3.55, 0.08, "suave"), (3.75, 0.0, "suave")],
        "braco_d": [(0.0, 0.0, "suave"), (0.9, 0.0, "suave"), (1.1, 128.0, "volta"), (2.3, 120.0, "suave"), (2.8, 0.0, "suave"),
                    (3.05, 0.0, "suave"), (3.3, 150.0, "volta"), (4.2, 150.0, "suave"), (4.7, 0.0, "suave")],
        "antebraco_d": [(0.0, 0.0, "suave"), (0.9, 0.0, "suave"), (1.1, -72.0, "volta"), (2.3, -66.0, "suave"), (2.8, 0.0, "suave"),
                        (3.05, 0.0, "suave"), (3.3, -55.0, "volta"), (4.2, -55.0, "suave"), (4.7, 0.0, "suave")],
        "braco_e": [(0.0, 0.0, "suave"), (0.9, 0.0, "suave"), (1.1, -128.0, "volta"), (2.3, -120.0, "suave"), (2.8, 0.0, "suave")],
        "antebraco_e": [(0.0, 0.0, "suave"), (0.9, 0.0, "suave"), (1.1, 72.0, "volta"), (2.3, 66.0, "suave"), (2.8, 0.0, "suave")],
        "dedos_d": [(0.0, G.mao("relaxada"), "suave"), (0.9, G.mao("relaxada"), "suave"), (1.05, G.mao("aberta"), "saida"),
                    (2.4, G.mao("aberta"), "suave"), (2.8, G.mao("relaxada"), "suave"), (3.1, G.mao("punho"), "saida"), (4.3, G.mao("punho"), "suave"),
                    (4.7, G.mao("relaxada"), "suave")],
        "dedos_e": [(0.0, G.mao("relaxada"), "suave"), (0.9, G.mao("relaxada"), "suave"), (1.05, G.mao("aberta"), "saida"),
                    (2.4, G.mao("aberta"), "suave"), (2.8, G.mao("relaxada"), "suave")],
        "cabeca": [(0.0, 0.0, "suave"), (0.9, 0.0, "suave"), (1.1, 6.0, "volta"), (2.3, 3.0, "suave"), (2.8, 0.0, "suave")],
        "rosto": [(0.0, G.expr("neutro"), "suave"), (0.88, G.expr("neutro"), "suave"), (0.98, G.expr("medo"), "saida"), (2.2, G.expr("medo"), "suave"),
                  (2.7, G.expr("preocupacao"), "suave"), (2.95, G.expr("preocupacao"), "suave"), (3.15, G.expr("alegria"), "saida"), (4.8, G.expr("alegria"), "suave")]})

    def quadro(c, q, tt):
        estudio(c)
        pose = H.pose_base(vista)
        for k in ("braco_d", "antebraco_d", "braco_e", "antebraco_e", "dedos_d", "dedos_e", "cabeca"):
            pose[k] = clip.valor(k, tt)
        pose["mao_vista_d"] = "palma"; pose["mao_vista_e"] = "palma"
        y = clip.valor("raiz_y", tt)
        if 1.35 <= tt <= 2.2:   # tremor de medo
            y += 0.008 * math.sin(2 * math.pi * 11 * tt); pose["cabeca"] += 1.2 * math.sin(2 * math.pi * 9 * tt)
        # agachar (y>0): a pelve desce y e as pernas encurtam exatamente y (escorço do joelho que vem para a câmera),
        # então os pés ficam no chão. Pular (y<0): o corpo inteiro sobe (os pés saem do chão).
        pose["raiz"] = [0.0, max(0.0, y)]
        if y > 0:   # só a canela encurta: no rig, a escala da coxa é herdada pela canela e pelo pé (ver relatório)
            k = 1 - y / H.OSS["canela"]
            for s in ("d", "e"):
                pose[f"esc_canela_{s}"] = k
        M = H.esqueleto(pose, vista); tz = M["pe_d"].mapXY(0, 0).y()   # tornozelo (mundo, H, y para baixo)
        if 0.86 <= tt <= 1.05:   # evento: "estouro" (desenho próprio)
            for i in range(12):
                a = i * math.pi / 6; r0, r1 = 40, 120 + 30 * math.sin(i)
                c.drawLine(880 + r0 * math.cos(a), 520 + r0 * math.sin(a), 880 + r1 * math.cos(a), 520 + r1 * math.sin(a),
                           skia.Paint(AntiAlias=True, Color=0xFFFFC21F, StrokeWidth=10, StrokeCap=skia.Paint.kRound_Cap))
        H.desenhar(c, CX - 60, CHAO + min(0.0, y) * U, ALT, vista=vista, pose=pose, rosto=clip.valor("rosto", tt))
        legenda(c, "T6b · reações: susto e comemoração — Heitor rig v2 (PROPOSTA)", q, tt)
        return {"t": tt, "raiz_y": y, "braco_d": pose["braco_d"], "tornozelo_y": -tz}

    reg = gravar("T6b_reacoes", 5.0, quadro)
    ys = [r["raiz_y"] for r in reg]
    pre = [r["raiz_y"] for r in reg if 0.85 <= r["t"] <= 0.95]
    bd = [r["braco_d"] for r in reg if 3.05 <= r["t"] <= 3.6]
    return {"antecipacao_agacha_antes_do_pulo_H": round(max(pre), 3), "altura_maxima_pulo_H": round(-min(ys), 3),
            "overshoot_braco_comemoracao_graus": round(max(bd) - 150.0, 1),
            # pés no chão enquanto não está no ar: altura do tornozelo comparada à da pose de repouso (quadro 0)
            "tornozelo_no_chao_variacao_max_H": round(max(abs(r["tornozelo_y"] - reg[0]["tornozelo_y"]) for r in reg if r["raiz_y"] >= 0), 5)}


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "f3_metricas.json"
    res = json.loads(caminho.read_text()) if caminho.exists() else {}
    for nome, f in (("T4_dedos_individuais", t4), ("T5_segurar_soltar", t5), ("T6_acenar_apontar", t6), ("T6b_reacoes", t6b)):
        if so and nome not in so:
            continue
        res[nome] = f(); print(nome, json.dumps(res[nome], ensure_ascii=False))
    caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1))
