#!/usr/bin/env python3
"""Poses-chave e objetos do EP02 para o Juca e a Jandira (PROPOSTA). Só calculam poses com as funções públicas
do rig (FK/IK e regra do cotovelo do v2.1); os objetos são desenho próprio, sem marca de terceiros."""
import copy, math
import skia


def _ik_par(P, pose, vista, alvos, mao="segurar", mao_vista=None):
    G, H = P.G, P.H
    for lado, alvo in alvos.items():
        if mao_vista:
            pose[f"mao_vista_{lado}"] = mao_vista
        pose[f"dedos_{lado}"] = copy.deepcopy(H.MAOS[mao])
        G.ik_braco(pose, vista, lado, alvo, cotovelo=None)
    return pose


def altura_sentado(P, assento=None):
    """Deslocamento da pelve (H, para baixo) para sentar com a coxa na horizontal (assento na altura do joelho)."""
    pr = P.H.PROP
    return pr["barra_camisa"] - (pr["joelho"] + 0.02) if assento is None else pr["barra_camisa"] - assento


def sentado(P, vista, dy=None):
    H = P.H; p = H.pose_base(vista); dy = altura_sentado(P) if dy is None else dy
    p["raiz"] = [0.0, dy]
    if vista == "perfil":
        for s in ("d", "e"):
            p[f"coxa_{s}"] = -88; p[f"canela_{s}"] = 88; p[f"pe_{s}"] = 0
    else:
        for s in ("d", "e"):
            p[f"esc_coxa_{s}"] = 0.04; p[f"_prof_{s}"] = 0.0   # coxa apontando para a câmera: quase some (escorço)
    return p


def controle_pos(P, pose, vista):
    """Centro do controle (mundo, H): no colo (frente) / à frente da barriga (perfil)."""
    pelve_y = -(P.H.PROP["barra_camisa"] - pose["raiz"][1])
    if vista == "perfil":
        return (0.78, pelve_y - 0.5)
    return (0.0, pelve_y - 0.12)


def jogando(P, vista, t=0.0, dy=None, intensidade=1.0):
    """Sentado com o controle nas duas mãos; os polegares e o controle mexem com o jogo."""
    p = sentado(P, vista, dy)
    cx, cy = controle_pos(P, p, vista)
    balanco = 0.04 * intensidade * math.sin(t * 7.0) + 0.02 * intensidade * math.sin(t * 17.0)
    cy += 0.03 * intensidade * math.sin(t * 5.3)
    if vista == "perfil":
        alvos = {"d": (cx + balanco, cy), "e": (cx + 0.06 + balanco, cy - 0.02)}
    else:
        sep = 0.21
        alvos = {"d": (cx - sep + balanco, cy), "e": (cx + sep + balanco, cy)}
    _ik_par(P, p, vista, alvos, "segurar")
    for s in ("d", "e"):   # polegares apertando botões
        p[f"dedos_{s}"]["polegar"] = [30 + 25 * max(0, math.sin(t * 11 + (0 if s == "d" else 1.7))), 25]
    p["cabeca"] = 2.0 * math.sin(t * 3.1) * intensidade
    p["tronco"] = -4.0 if vista == "perfil" else 1.5 * math.sin(t * 2.3) * intensidade
    return p, (cx + balanco, cy), balanco * 60


def segurando_caixa(P, vista, larg=1.1, alt=0.85, y_centro=None):
    H = P.H; p = H.pose_base(vista)
    yc = -(H.PROP["barra_camisa"] + 0.25) if y_centro is None else y_centro
    if vista == "perfil":
        alvos = {"d": (0.42, yc + alt / 2 - 0.05), "e": (0.62, yc + alt / 2 - 0.02)}
    else:
        alvos = {"d": (-larg / 2 - 0.02, yc + 0.12), "e": (larg / 2 + 0.02, yc + 0.12)}
    _ik_par(P, p, vista, alvos, "aberta" if vista != "perfil" else "segurar")
    return p, (0.0 if vista != "perfil" else 0.62, yc)


def objeto_mundo(desenho):
    """Callback de objeto segurado que desenha SEM a rotação da mão: na posição do encaixe, em pixels de tela.
    desenho(c, x_px, y_px) é chamado com a matriz zerada (o objeto fica atrás dos dedos na vista de dorso)."""
    def f(cc, v):
        ex, ey = {"dorso": (0.0, 0.215), "palma": (0.0, 0.2), "lado": (-0.10, 0.17)}[v]
        pt = cc.getTotalMatrix().mapXY(ex, ey)
        cc.save(); cc.resetMatrix(); desenho(cc, pt.x(), pt.y()); cc.restore()
    return f


def bracos_cruzados(P, vista="frente"):
    H = P.H; p = H.pose_base(vista)
    y = -(H.PROP["ombro"] - 0.55)
    _ik_par(P, p, vista, {"d": (0.30, y + 0.02), "e": (-0.30, y - 0.05)}, "relaxada")
    return p


# ---------------------------------------------------------------- objetos (desenho próprio, sem marca)
def _pt(cor, a=1.0):
    p = skia.Paint(AntiAlias=True, Color=cor); p.setAlphaf(a); return p


def _ln(cor, w):
    return skia.Paint(AntiAlias=True, Color=cor, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap)


CONTORNO = 0xFF2A1D17


def controle(c, x, y, u, ang=0.0, perfil=False, luz=0xFF4FC3F7):
    """Controle genérico (sem marca): corpo grafite com duas alças, dois direcionais, 4 botões claros e luz."""
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(u, u)
    if perfil:   # visto de lado: desenho frontal comprimido (trapaça de animação 2D para o controle ler)
        c.scale(0.6, 1.0)
    corpo = skia.Path()
    corpo.moveTo(-0.16, -0.08); corpo.lineTo(0.16, -0.08)
    corpo.cubicTo(0.26, -0.09, 0.30, 0.02, 0.31, 0.12); corpo.cubicTo(0.32, 0.2, 0.24, 0.22, 0.2, 0.14)
    corpo.quadTo(0.12, 0.05, 0.0, 0.05); corpo.quadTo(-0.12, 0.05, -0.2, 0.14)
    corpo.cubicTo(-0.24, 0.22, -0.32, 0.2, -0.31, 0.12); corpo.cubicTo(-0.30, 0.02, -0.26, -0.09, -0.16, -0.08); corpo.close()
    c.drawPath(corpo, _pt(0xFF3A3F4A))
    s = skia.Path(corpo); s.offset(0.0, -0.03)
    sb = skia.Op(corpo, s, skia.PathOp.kDifference_PathOp)
    if sb:
        c.drawPath(sb, _pt(0xFF262A33))
    c.drawPath(corpo, _ln(CONTORNO, 0.016))
    for sx in (-0.07, 0.07):   # direcionais analógicos
        c.drawCircle(sx, 0.02, 0.035, _pt(0xFF1B1E25)); c.drawCircle(sx, 0.015, 0.024, _pt(0xFF555B68))
    c.drawRect(skia.Rect.MakeLTRB(-0.2, -0.035, -0.18, 0.025), _pt(0xFF8A90A0)); c.drawRect(skia.Rect.MakeLTRB(-0.22, -0.015, -0.16, 0.005), _pt(0xFF8A90A0))
    for bx, by in ((0.19, -0.04), (0.19, 0.01), (0.165, -0.015), (0.215, -0.015)):
        c.drawCircle(bx, by, 0.012, _pt(0xFFD9DCE3))
    c.drawRect(skia.Rect.MakeLTRB(-0.05, -0.075, 0.05, -0.06), _pt(luz))
    c.restore()


def caixa_presente(c, x, y, u, larg=0.9, alt=0.75, tampa=0.0, brilho=0.0):
    """Caixa de presente (papel roxo-escuro, fita dourada). tampa 0–1 abre a tampa; brilho 0–1 sai luz de dentro."""
    c.save(); c.translate(x, y); c.scale(u, u)
    w, h = larg / 2, alt / 2
    if brilho > 0:
        g = skia.GradientShader.MakeRadial((0, -h), 1.2, [0xCCFFE9A8, 0x00FFE9A8])
        p = skia.Paint(AntiAlias=True, Shader=g); p.setAlphaf(brilho)
        c.drawCircle(0, -h, 1.2, p)
        for k in range(7):
            a = math.radians(-150 + k * 20)
            raio = skia.Path(); raio.moveTo(0, -h); raio.lineTo(math.cos(a) * 1.4 - 0.05, -h + math.sin(a) * 1.4)
            raio.lineTo(math.cos(a) * 1.4 + 0.05, -h + math.sin(a) * 1.4); raio.close()
            c.drawPath(raio, _pt(0xFFFFF1C2, 0.35 * brilho))
    corpo = skia.Path(); corpo.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w, -h + 0.08, w, h), 0.03, 0.03))
    c.drawPath(corpo, _pt(0xFF33407A))
    c.drawRect(skia.Rect.MakeLTRB(w * 0.35, -h + 0.08, w, h), _pt(0xFF27325F))
    c.drawRect(skia.Rect.MakeLTRB(-0.06, -h + 0.08, 0.06, h), _pt(0xFFFFC21F))
    c.drawPath(corpo, _ln(CONTORNO, 0.02))
    c.save(); c.translate(-w - 0.03, -h + 0.1); c.rotate(-80 * tampa); c.translate(w + 0.03, h - 0.1)
    tp = skia.Path(); tp.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w - 0.04, -h - 0.04, w + 0.04, -h + 0.1), 0.03, 0.03))
    c.drawPath(tp, _pt(0xFF3D4C8F)); c.drawRect(skia.Rect.MakeLTRB(-0.065, -h - 0.04, 0.065, -h + 0.1), _pt(0xFFFFC21F))
    c.drawPath(tp, _ln(CONTORNO, 0.02))
    if tampa < 0.3:   # laço
        for s in (-1, 1):
            l = skia.Path(); l.moveTo(0, -h - 0.04); l.cubicTo(s * 0.12, -h - 0.25, s * 0.26, -h - 0.12, 0, -h - 0.04)
            c.drawPath(l, _pt(0xFFFFC21F)); c.drawPath(l, _ln(CONTORNO, 0.016))
    c.restore()
    c.restore()


def console(c, x, y, u, deitado=False, luz=1.0):
    """Videogame genérico (sem marca): torre grafite com frisos e faixa de luz azul."""
    c.save(); c.translate(x, y); c.scale(u, u)
    if deitado:
        c.rotate(-90)
    w, h = 0.16, 0.5
    b = skia.Path(); b.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w, -h, w, h), 0.04, 0.04))
    c.drawPath(b, _pt(0xFF2E333D)); c.drawRect(skia.Rect.MakeLTRB(w * 0.3, -h, w, h), _pt(0xFF22262E))
    for k in range(6):
        c.drawLine(-w + 0.03, -h + 0.12 + k * 0.03, w * 0.2, -h + 0.12 + k * 0.03, _ln(0xFF414754, 0.008))
    c.drawRect(skia.Rect.MakeLTRB(-0.012, -h + 0.04, 0.012, h - 0.04), _pt(0xFF4FC3F7, 0.35 + 0.65 * luz))
    c.drawPath(b, _ln(CONTORNO, 0.02))
    c.restore()
