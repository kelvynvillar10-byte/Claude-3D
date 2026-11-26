"""Aranha do EP01 — personagem ORIGINAL do Modo Curioso (aranha doméstica genérica), desenhada por código (skia).

Estilo 2D do canal: cores lisas, 1 tom de sombra, contorno fino. Anatomia simplificada mas correta: cefalotórax +
abdômen, 8 patas com 3 segmentos (coxa, fêmur, tíbia/metatarso), 2 pedipalpos, quelíceras, 8 olhos (2 grandes à frente,
6 menores), pelos curtos. Marrom com chevrons claros no abdômen. "Assustadora" pela escala, não por gore.

desenhar(cv, x, y, largura_px, fase=0.0, olhos_brilho=1.0, levantar_frente=0.0)
  x, y            centro do corpo no chão (px) · largura_px = envergadura das patas (px)
  fase            0..1 ciclo de passo (patas alternadas, tetrapod) · levantar_frente 0..1 ergue as 2 patas da frente (ameaça)
Vista de frente-3/4 (a aranha encara a câmera ou o Heitor).
"""
import math
import skia

COR = {"corpo": "#6b4a32", "corpo_sombra": "#4e3523", "abdomen": "#5d402b", "chevron": "#b08a5e", "pata": "#5a3e2a",
       "pata_claro": "#8a6748", "olho": "#141012", "brilho": "#ffffff", "contorno": "#1e1612", "pelo": "#3a281b"}


def _cor(h, a=255):
    h = h.lstrip("#"); return skia.ColorSetARGB(a, int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _p(cor, a=255, traco=0.0):
    p = skia.Paint(AntiAlias=True, Color=_cor(cor, a))
    if traco:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(traco); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def _elipse(cx, cy, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def _pata(cv, base, lado, i, fase, levantar, s):
    """Uma pata (unidade = envergadura). i = 0 (frente) … 3 (trás). Joelho alto, ponta no chão."""
    ang = math.radians([-35, -10, 15, 40][i]) * lado                    # direção da pata no plano
    alcance = [0.46, 0.5, 0.48, 0.44][i]
    passo = math.sin(2 * math.pi * (fase + (0.5 if (i + (lado > 0)) % 2 else 0.0)))
    erguer = max(0.0, passo) * 0.04 + (levantar * 0.22 if i == 0 else 0.0)
    pe = (base[0] + lado * alcance * math.cos(ang), base[1] + 0.02 + 0.1 * math.sin(abs(ang)) * (1 if i > 1 else -0.2) - erguer)
    joelho = (base[0] + lado * alcance * 0.55 * math.cos(ang), base[1] - 0.2 - 0.04 * (3 - i) - (levantar * 0.15 if i == 0 else 0.0))
    meio = ((joelho[0] + pe[0]) / 2 + lado * 0.03, (joelho[1] + pe[1]) / 2 - 0.03)
    for a, b, w in ((base, joelho, 0.034), (joelho, meio, 0.026), (meio, pe, 0.018)):
        cv.drawLine(*a, *b, _p(COR["contorno"], 255, w + 2 * s)); cv.drawLine(*a, *b, _p(COR["pata"], 255, w))
        cv.drawLine(a[0], a[1] - w * 0.2, b[0], b[1] - w * 0.2, _p(COR["pata_claro"], 160, w * 0.35))
        n = 4                                                           # pelos curtos
        for k in range(1, n):
            t = k / n; px = a[0] + (b[0] - a[0]) * t; py = a[1] + (b[1] - a[1]) * t
            cv.drawLine(px, py, px + lado * 0.012, py - 0.018, _p(COR["pelo"], 230, s * 0.9))
    cv.drawCircle(*joelho, 0.02, _p(COR["pata"])); cv.drawCircle(*joelho, 0.02, _p(COR["contorno"], 255, s))


def desenhar(cv, x, y, largura_px, fase=0.0, olhos_brilho=1.0, levantar_frente=0.0):
    L = largura_px; s = max(1.0, L * 0.004) / L
    cv.save(); cv.translate(x, y); cv.scale(L, L)
    base = (0.0, -0.1)
    # abdômen atrás e acima (vista frente-3/4)
    abd = _elipse(0.0, -0.27, 0.17, 0.15)
    cv.drawPath(abd, _p(COR["abdomen"]))
    cv.save(); cv.clipPath(abd, doAntiAlias=True)
    cv.drawPath(_elipse(0.06, -0.2, 0.2, 0.1), _p(COR["corpo_sombra"]))
    for k in range(3):                                                  # chevrons claros
        c = skia.Path(); yk = -0.36 + k * 0.05; w = 0.09 - k * 0.018
        c.moveTo(-w, yk); c.lineTo(0, yk + 0.03); c.lineTo(w, yk)
        cv.drawPath(c, _p(COR["chevron"], 255, 0.016))
    cv.restore(); cv.drawPath(abd, _p(COR["contorno"], 255, s))
    # patas (trás primeiro)
    for i in (3, 2, 1, 0):
        for lado in (-1, 1):
            _pata(cv, (base[0] + lado * 0.05, base[1] - 0.02), lado, i, fase, levantar_frente, s)
    # cefalotórax
    cef = _elipse(0.0, -0.12, 0.11, 0.085)
    cv.drawPath(cef, _p(COR["corpo"]))
    cv.save(); cv.clipPath(cef, doAntiAlias=True); cv.drawPath(_elipse(0.04, -0.06, 0.12, 0.05), _p(COR["corpo_sombra"])); cv.restore()
    cv.drawPath(cef, _p(COR["contorno"], 255, s))
    # pedipalpos e quelíceras
    for lado in (-1, 1):
        cv.drawLine(lado * 0.04, -0.07, lado * 0.075, -0.02, _p(COR["contorno"], 255, 0.026 + 2 * s)); cv.drawLine(lado * 0.04, -0.07, lado * 0.075, -0.02, _p(COR["pata"], 255, 0.026))
        q = skia.Path(); q.moveTo(lado * 0.035, -0.07); q.quadTo(lado * 0.04, -0.03, lado * 0.012, -0.02); q.lineTo(lado * 0.008, -0.06); q.close()
        cv.drawPath(q, _p(COR["corpo_sombra"])); cv.drawPath(q, _p(COR["contorno"], 255, s))
    # 8 olhos: 2 grandes na frente, 6 menores em arco
    for lado in (-1, 1):
        for (dx, dy, r) in ((0.028, -0.115, 0.022), (0.06, -0.14, 0.012), (0.035, -0.155, 0.011), (0.075, -0.115, 0.01)):
            cv.drawCircle(lado * dx, dy, r, _p(COR["olho"]))
            cv.drawCircle(lado * dx - r * 0.3, dy - r * 0.35, r * 0.35, _p(COR["brilho"], int(230 * olhos_brilho)))
    cv.restore()
