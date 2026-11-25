#!/usr/bin/env python3
"""Heitor rig v2 (PROPOSTA) — testes da fase F2 (T2 caminhada frente/perfil/costas, T3 corrida).

Renderiza cada teste em MP4 1080×1920 30 qps (câmera acompanha a pelve; marcas no chão andam com o mundo),
gera folha de contato de 1 ciclo e sobreposição (onion skin), e MEDE pela cinemática real do rig (FK):
erro de IK, deslize do pé de apoio, continuidade dos ângulos, oposição braço/perna, fase de voo (corrida).
Saída: testes/*.mp4, testes/*_folha.jpg, testes/*_sobreposicao.png, testes/f2_metricas.json, testes/f2_metricas.md
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np, skia

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import heitor_v2 as H   # noqa: E402
import animacao as A    # noqa: E402

OUT = AQUI.parent / "testes"; OUT.mkdir(exist_ok=True)
W, HH, FPS = 1080, 1920, 30
ALT = 1150; U = ALT / 4; CHAO = 1640; CX = W / 2
F_L = skia.Font(H.NUNITO, 34)


def cenario(c, X, vista):
    c.clear(0xFFE9E6DF)
    grad = skia.GradientShader.MakeLinear([skia.Point(0, CHAO - 40), skia.Point(0, HH)], [0xFFCFC9BE, 0xFFB9B2A6])
    c.drawRect(skia.Rect.MakeLTRB(0, CHAO - 40 if vista != "perfil" else CHAO, W, HH), skia.Paint(Shader=grad))
    if vista == "perfil":   # marcas no chão a cada 0,5 H, presas ao mundo (o pé de apoio deve andar junto com elas)
        c.drawLine(0, CHAO, W, CHAO, skia.Paint(AntiAlias=True, Color=0xFF8C8577, StrokeWidth=3))
        k0 = math.floor((X - CX / U) / 0.5) - 1
        for k in range(k0, k0 + int(W / U / 0.5) + 4):
            x = CX + (k * 0.5 - X) * U
            c.drawLine(x, CHAO, x, CHAO + 26, skia.Paint(AntiAlias=True, Color=0xFF8C8577, StrokeWidth=3))
    else:   # frente/costas: linhas do piso vindo em direção à câmera
        for k in range(12):
            y = CHAO - 30 + ((k * 0.5 + (X if vista == "frente" else -X) * 0.6) % 6.0) / 6.0 * (HH - CHAO + 30)
            c.drawLine(0, y, W, y, skia.Paint(AntiAlias=True, Color=0x338C8577, StrokeWidth=2))


def sombra_pes(c, M, vista):
    for s in ("d", "e"):
        p = M[f"pe_{s}"].mapXY(0.05, 0.22)
        y_pe = -p.y()   # altura do pé acima do chão (H)
        a = max(0.0, 1 - y_pe / 0.6)
        if a <= 0:
            continue
        c.drawOval(skia.Rect.MakeXYWH(CX + p.x() * U - 0.22 * U, CHAO - 0.03 * U, 0.44 * U, 0.06 * U),
                   skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(90 * a), 30, 26, 40),
                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))


def renderizar(nome, vista, tipo, dur, rotulo):
    P = A.CAMINHADA if tipo == "caminhada" else A.CORRIDA
    n = int(round(dur * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{HH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / f"{nome}.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    reg = []
    ciclo_q = int(round(P["T"] * FPS))
    sobre = skia.Surface(W, HH); cs = sobre.getCanvas(); cenario(cs, 0.0, vista)
    for q in range(n):
        t = q / FPS
        pose, dg = A.pose_locomocao(t, vista, tipo)
        pose["respira"] = math.sin(2 * math.pi * t / 2.6)
        s = skia.Surface(W, HH); c = s.getCanvas()
        cenario(c, dg["pelve_x"], vista)
        M = H.esqueleto(pose, vista)
        sombra_pes(c, M, vista)
        H.desenhar(c, CX, CHAO, ALT, vista=vista, pose=pose, rosto=A.rosto_com_piscada("neutro", t))
        c.drawString(rotulo, 40, 70, F_L, skia.Paint(AntiAlias=True, Color=0xFF1F2A44))
        c.drawString(f"quadro {q:03d} · t={t:4.2f} s · fase {dg['pernas']['d']['fase']:.2f}", 40, 115, F_L, skia.Paint(AntiAlias=True, Color=0xFF55607A))
        pr.stdin.write(s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
        if q < ciclo_q:   # sobreposição de 1 ciclo (onion skin)
            cs.saveLayerAlpha(None, 50); H.desenhar(cs, CX, CHAO, ALT, vista=vista, pose=pose, rosto="neutro"); cs.restore()
        # medições pela FK real (mundo, H)
        reg.append({"t": t, "pose": {k: v for k, v in pose.items() if isinstance(v, (int, float))},
                    "pe": {s_: [dg["pelve_x"] + M[f"pe_{s_}"].mapXY(0, 0).x(), -M[f"pe_{s_}"].mapXY(0, 0).y()] for s_ in ("d", "e")},
                    "apoio": {s_: dg["pernas"][s_]["apoio"] for s_ in ("d", "e")},
                    "erro_ik": max(dg["pernas"][s_]["erro_ik"] for s_ in ("d", "e"))})
    pr.stdin.close(); pr.wait()
    sobre.makeImageSnapshot().save(str(OUT / f"{nome}_sobreposicao.png"), skia.kPNG)
    # folha de contato de 1 ciclo
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"{nome}.mp4"), "-vf",
                    f"select='lt(n\\,{ciclo_q})',scale=270:480,tile={min(ciclo_q, 9)}x{math.ceil(ciclo_q / 9)}", "-frames:v", "1",
                    str(OUT / f"{nome}_folha.jpg")])
    return reg, P


def medir(reg, P, vista, tipo):
    m = {"quadros": len(reg), "ciclo_quadros": round(P["T"] * FPS, 1), "ciclo_s": P["T"]}
    m["erro_ik_max_H"] = round(max(r["erro_ik"] for r in reg), 5)
    # deslize do pé de apoio (perfil: x no mundo deve ficar parado enquanto apoiado)
    desl = []
    for s in ("d", "e"):
        trecho = []
        for r in reg + [None]:
            if r is not None and r["apoio"][s]:
                trecho.append(r["pe"][s][0])
            elif len(trecho) >= 4:
                desl.append(max(trecho) - min(trecho)); trecho = []
            else:
                trecho = []
    if vista == "perfil":
        m["deslize_pe_apoio_max_H"] = round(max(desl), 4) if desl else None
        m["deslize_pe_apoio_pct_altura"] = round(100 * max(desl) / 4.0, 2) if desl else None
    # continuidade: maior variação de ângulo entre quadros (graus/quadro)
    chaves = [k for k in reg[0]["pose"] if not k.startswith(("_", "respira", "esc_"))]
    salto = {k: max(abs(reg[i + 1]["pose"][k] - reg[i]["pose"][k]) for i in range(len(reg) - 1)) for k in chaves}
    pior = max(salto, key=salto.get)
    m["maior_variacao_angulo"] = {"junta": pior, "graus_por_quadro": round(salto[pior], 2)}
    if vista == "perfil":
        b = np.array([r["pose"]["braco_d"] for r in reg]); cx_ = np.array([r["pose"]["coxa_d"] for r in reg])
        m["correlacao_braco_d_coxa_d"] = round(float(np.corrcoef(b, cx_)[0, 1]), 3)
        voo = sum(1 for r in reg if not r["apoio"]["d"] and not r["apoio"]["e"])
        m["quadros_em_voo"] = voo; m["quadros_apoio_duplo"] = sum(1 for r in reg if r["apoio"]["d"] and r["apoio"]["e"])
    alt_pe = [min(r["pe"]["d"][1], r["pe"]["e"][1]) for r in reg]
    m["pe_mais_baixo_H"] = [round(min(alt_pe), 3), round(max(alt_pe), 3)]
    return m


TESTES = [
    ("T2_caminhada_perfil", "perfil", "caminhada", 3.44, "T2 · caminhada · perfil — Heitor rig v2 (PROPOSTA)"),
    ("T2_caminhada_frente", "frente", "caminhada", 2.58, "T2 · caminhada · frente — Heitor rig v2 (PROPOSTA)"),
    ("T2_caminhada_costas", "costas", "caminhada", 2.58, "T2 · caminhada · costas — Heitor rig v2 (PROPOSTA)"),
    ("T3_corrida_perfil", "perfil", "corrida", 2.12, "T3 · corrida · perfil — Heitor rig v2 (PROPOSTA)"),
]
if __name__ == "__main__":
    so = sys.argv[1:]
    res = {}
    for nome, vista, tipo, dur, rot in TESTES:
        if so and nome not in so:
            continue
        reg, P = renderizar(nome, vista, tipo, dur, rot)
        res[nome] = medir(reg, P, vista, tipo)
        print(nome, json.dumps(res[nome], ensure_ascii=False))
    (OUT / "f2_metricas.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
