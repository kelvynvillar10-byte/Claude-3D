"""PROPOSTA (não aprovada) — ombros arredondados para o Heitor rig v2. NÃO altera o rig: troca, só dentro do bloco
`with ativar():`, duas formas do desenho:
1. tronco: o topo deixa de ser uma reta com cantos vivos; desce do pescoço para os ombros numa curva suave (caimento de
   ombro) e arredonda a quina;
2. manga: o topo vira uma cúpula (o deltoide arredondado) em vez de um retângulo de cantos levemente arredondados.
Pescoço, gola, estampa, braços, cotovelos, proporções e cores ficam iguais. Ao sair do bloco, tudo volta ao rig aprovado.
"""
import contextlib
import skia
import heitor_v2 as HV


def _forma_tronco(vista):
    """Do pescoço ao ombro a linha DESCE em curva (trapézio), sem patamar reto; a quina do ombro é redonda."""
    p = skia.Path(); top, hem = HV.OMBRO_Y - 0.1, 0.0
    if vista in ("frente", "costas"):
        p.moveTo(-0.13, top - 0.025); p.lineTo(0.13, top - 0.025)
        p.cubicTo(0.22, top - 0.02, 0.31, top + 0.035, 0.40, top + 0.075)          # trapézio descendo
        p.cubicTo(0.455, top + 0.10, 0.485, top + 0.14, 0.485, top + 0.20)         # quina redonda do ombro
        p.quadTo(0.49, -0.55, 0.42, hem); p.lineTo(-0.42, hem); p.quadTo(-0.49, -0.55, -0.485, top + 0.20)
        p.cubicTo(-0.485, top + 0.14, -0.455, top + 0.10, -0.40, top + 0.075)
        p.cubicTo(-0.31, top + 0.035, -0.22, top - 0.02, -0.13, top - 0.025)
    elif vista == "tres_quartos":
        p.moveTo(-0.11, top - 0.025); p.lineTo(0.10, top - 0.025)
        p.cubicTo(0.18, top - 0.02, 0.26, top + 0.03, 0.32, top + 0.07)
        p.cubicTo(0.37, top + 0.095, 0.39, top + 0.14, 0.39, top + 0.19)
        p.quadTo(0.43, -0.55, 0.35, hem); p.lineTo(-0.36, hem); p.quadTo(-0.44, -0.55, -0.42, top + 0.19)
        p.cubicTo(-0.42, top + 0.13, -0.39, top + 0.095, -0.34, top + 0.07)
        p.cubicTo(-0.27, top + 0.03, -0.19, top - 0.02, -0.11, top - 0.025)
    else:
        p.moveTo(-0.10, top - 0.025); p.lineTo(0.08, top - 0.025)
        p.cubicTo(0.15, top - 0.015, 0.21, top + 0.03, 0.235, top + 0.10)
        p.quadTo(0.30, -0.6, 0.24, hem); p.lineTo(-0.22, hem); p.quadTo(-0.27, -0.55, -0.225, top + 0.10)
        p.cubicTo(-0.20, top + 0.03, -0.16, top - 0.015, -0.10, top - 0.025)
    p.close(); return p


def desenhar_manga(c, lado_luz, distante=False):
    """Manga com topo em cúpula: o ombro fica redondo em qualquer ângulo do braço."""
    mr = skia.Path(); r = 0.15                                          # cúpula mais baixa: continua a curva do trapézio
    mr.moveTo(-0.14, 0.26); mr.lineTo(-r, 0.04)
    mr.cubicTo(-r, -0.03, -0.08, -0.07, 0.0, -0.07); mr.cubicTo(0.08, -0.07, r, -0.03, r, 0.04)
    mr.lineTo(0.14, 0.26); mr.quadTo(0.0, 0.275, -0.14, 0.26); mr.close()
    cam, cam_s = (HV.C["camisa_s"], HV.C["camisa_s"]) if distante else (HV.C["camisa"], HV.C["camisa_s"])
    HV.preenche(c, mr, cam, cam_s, lado_luz, 0.3)
    c.drawLine(-0.12, 0.225, 0.12, 0.225, HV.traco(HV.C["gola"], 0.012))


@contextlib.contextmanager
def ativar():
    orig = (HV._forma_tronco, HV.desenhar_manga)
    HV._forma_tronco, HV.desenhar_manga = _forma_tronco, desenhar_manga
    try:
        yield
    finally:
        HV._forma_tronco, HV.desenhar_manga = orig
