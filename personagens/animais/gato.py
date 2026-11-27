"""Gato do EP01 — personagem ORIGINAL do Modo Curioso, desenhado por código (skia), no estilo 2D do canal.

Desenho próprio (não copia gato de desenho, quadrinho ou marca): gato cinza-azulado rajado, peito creme, olhos verde-
limão com pupila em fenda, orelhas com miolo rosado, cauda grossa com ponta escura. Cores lisas com 1 tom de sombra e
contorno fino escuro, como o Heitor.

desenhar(cv, x_pe, y_pe, altura_px, pose="sentado", direcao=1, olhar=0.0, pupila=0.25, piscar=0.0)
  x_pe, y_pe   ponto no chão sob o peito (px) · altura_px = altura do topo da cabeça (sentado) em px
  pose         "sentado" | "agachado" (caçando: corpo baixo, ombros altos, cauda reta, orelhas de lado)
  direcao      1 olhando para a direita, -1 para a esquerda
  olhar        -1..1 desloca as pupilas na horizontal · pupila 0..1 (0 = fenda fina; 1 = redonda dilatada: caça)
pata(cv, cx, cy, tamanho_px, garras=1.0, angulo=0.0)   pata vista de perto (almofadas, pelo, garras de 0 a 1)
olho(cv, cx, cy, largura_px, pupila=0.2, olhar=0.0)    olho em close (para o crash-zoom)
"""
import math
import skia

COR = {"pelo": "#8e9aa8", "pelo_sombra": "#6f7b8a", "listra": "#566270", "peito": "#ece4d4", "peito_sombra": "#d4c9b5",
       "orelha_miolo": "#e9a7a0", "olho": "#a8d43c", "olho_borda": "#5d7a1e", "pupila": "#141414", "nariz": "#d9827a",
       "contorno": "#2a2328", "almofada": "#d98b86", "garra": "#f4efe4", "bigode": "#f6f3ee"}


def _cor(h, a=255):
    h = h.lstrip("#"); return skia.ColorSetARGB(a, int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _p(cor, a=255, contorno=0.0, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=_cor(cor, a))
    if contorno:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(contorno); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def _preencher(cv, path, cor, sombra=None, contorno=None, s=1.0):
    cv.drawPath(path, _p(cor))
    if sombra is not None:
        cv.save(); cv.clipPath(path, doAntiAlias=True); cv.drawPath(sombra, _p(COR["pelo_sombra"] if cor == COR["pelo"] else COR["peito_sombra"])); cv.restore()
    if contorno:
        cv.drawPath(path, _p(COR["contorno"], 255, contorno * s))


def _elipse(cx, cy, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def _bolha(pts):
    """Contorno suave (Catmull-Rom fechado) por uma lista de pontos."""
    p = skia.Path(); n = len(pts)
    p.moveTo(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    p.close(); return p


def _olho_amendoa(cv, cx, cy, w, h, pupila, olhar, piscar, contorno):
    """Olho em amêndoa: íris verde, pupila em fenda (0) a redonda (1), brilho; pálpebra fecha com 'piscar'."""
    olho = skia.Path(); olho.moveTo(cx - w / 2, cy)
    olho.quadTo(cx, cy - h * (1 - piscar), cx + w / 2, cy); olho.quadTo(cx, cy + h * (1 - piscar), cx - w / 2, cy); olho.close()
    cv.drawPath(olho, _p(COR["olho"]))
    cv.save(); cv.clipPath(olho, doAntiAlias=True)
    cv.drawPath(_elipse(cx, cy + h * 0.55, w * 0.6, h * 0.5), _p(COR["olho_borda"], 120))
    px = cx + olhar * w * 0.18; pw = w * (0.07 + 0.25 * pupila); ph = h * (0.8 - 0.15 * pupila)
    cv.drawPath(_elipse(px, cy, pw, ph), _p(COR["pupila"]))
    cv.drawPath(_elipse(px + w * 0.1, cy - h * 0.35, w * 0.07, w * 0.07), _p("#ffffff", 230))
    cv.restore()
    cv.drawPath(olho, _p(COR["contorno"], 255, contorno))


def desenhar(cv, x_pe, y_pe, altura_px, pose="sentado", direcao=1, olhar=0.0, pupila=0.25, piscar=0.0, fase=0.0, cauda=0.0,
             inclinar=0.0):
    """pose "andando": ciclo de passo de 4 patas (sequência lateral: traseira, dianteira do mesmo lado, depois o outro),
    fase 0–1 por passada; cauda −1..1 balança a ponta; inclinar (graus) inclina a cabeça (curiosidade)."""
    A = altura_px; c = max(1.0, A * 0.006)                              # espessura do contorno
    cv.save(); cv.translate(x_pe, y_pe); cv.scale(direcao * A, A)
    k = 1.0 / A                                                          # contorno em px, escala unitária
    if pose == "agachado":
        _agachado(cv, olhar, pupila, piscar, c * k, cauda)
    elif pose == "andando":
        _andando(cv, olhar, pupila, piscar, c * k, fase, cauda, inclinar)
    else:
        _sentado(cv, olhar, pupila, piscar, c * k, cauda, inclinar)
    cv.restore()


def _cauda(cv, pts, larg, s):
    p = skia.Path(); p.moveTo(*pts[0]); p.cubicTo(*pts[1], *pts[2], *pts[3])
    cv.drawPath(p, _p(COR["contorno"], 255, larg + 2 * s)); cv.drawPath(p, _p(COR["pelo"], 255, larg))
    pe = skia.DashPathEffect.Make([0.04, 0.05], 0.0)
    lt = _p(COR["listra"], 255, larg * 0.92); lt.setPathEffect(pe); lt.setStrokeCap(skia.Paint.kButt_Cap); cv.drawPath(p, lt)
    cv.drawCircle(pts[3][0], pts[3][1], larg * 0.55, _p(COR["listra"]))


def _cabeca(cv, cx, cy, r, olhar, pupila, piscar, s, orelhas="em_pe", inclinar=0.0):
    if inclinar:
        cv.save(); cv.rotate(inclinar, cx, cy + r * 0.6)
        _cabeca(cv, cx, cy, r, olhar, pupila, piscar, s, orelhas, 0.0); cv.restore(); return
    # orelhas
    for lado in (-1, 1):
        if orelhas == "em_pe":
            base = [(cx + lado * r * 0.25, cy - r * 0.75), (cx + lado * r * 0.95, cy - r * 0.35), (cx + lado * r * 0.78, cy - r * 1.25)]
        else:                                                            # achatadas para o lado (caçando)
            base = [(cx + lado * r * 0.35, cy - r * 0.7), (cx + lado * r * 1.05, cy - r * 0.2), (cx + lado * r * 1.3, cy - r * 0.85)]
        o = skia.Path(); o.moveTo(*base[0]); o.lineTo(*base[1]); o.lineTo(*base[2]); o.close()
        cv.drawPath(o, _p(COR["pelo"])); cv.drawPath(o, _p(COR["contorno"], 255, s))
        m = skia.Path(); mx = sum(p[0] for p in base) / 3; my = sum(p[1] for p in base) / 3
        m.moveTo(*[(a + mx) / 2 for a in base[0]][:1], (base[0][1] + my) / 2)
        m.lineTo((base[1][0] + mx) / 2, (base[1][1] + my) / 2); m.lineTo((base[2][0] * 0.7 + mx * 0.3), (base[2][1] * 0.7 + my * 0.3)); m.close()
        cv.drawPath(m, _p(COR["orelha_miolo"]))
    # crânio largo e bochechas
    cab = _bolha([(cx - r * 1.0, cy + r * 0.1), (cx - r * 0.85, cy - r * 0.6), (cx, cy - r * 0.92), (cx + r * 0.85, cy - r * 0.6),
                  (cx + r * 1.0, cy + r * 0.1), (cx + r * 0.75, cy + r * 0.62), (cx, cy + r * 0.78), (cx - r * 0.75, cy + r * 0.62)])
    sombra = _elipse(cx + r * 0.2, cy + r * 0.55, r * 1.1, r * 0.4)
    _preencher(cv, cab, COR["pelo"], sombra, s / 1.0 if s else None)
    cv.save(); cv.clipPath(cab, doAntiAlias=True)
    for i, dx in enumerate((-0.28, 0.0, 0.28)):                         # listras da testa (o "M" rajado, desenho próprio)
        lp = skia.Path(); lp.moveTo(cx + dx * r, cy - r * 0.92); lp.quadTo(cx + dx * r * 1.25, cy - r * 0.6, cx + dx * r * 0.9, cy - r * 0.38)
        cv.drawPath(lp, _p(COR["listra"], 255, r * 0.09))
    for lado in (-1, 1):
        for j in range(2):
            lp = skia.Path(); y0 = cy + r * (0.05 + 0.17 * j)
            lp.moveTo(cx + lado * r * 1.02, y0); lp.quadTo(cx + lado * r * 0.8, y0 - r * 0.05, cx + lado * r * 0.66, y0 + r * 0.04)
            cv.drawPath(lp, _p(COR["listra"], 255, r * 0.07))
    cv.drawPath(_elipse(cx, cy + r * 0.45, r * 0.55, r * 0.36), _p(COR["peito"]))      # focinho claro
    cv.restore()
    # olhos, nariz, boca e bigodes
    for lado in (-1, 1):
        _olho_amendoa(cv, cx + lado * r * 0.42, cy - r * 0.05, r * 0.5, r * 0.3, pupila, olhar, piscar, s)
    nz = skia.Path(); nz.moveTo(cx - r * 0.1, cy + r * 0.25); nz.lineTo(cx + r * 0.1, cy + r * 0.25); nz.lineTo(cx, cy + r * 0.36); nz.close()
    cv.drawPath(nz, _p(COR["nariz"])); cv.drawPath(nz, _p(COR["contorno"], 255, s * 0.7))
    bc = skia.Path(); bc.moveTo(cx, cy + r * 0.36); bc.quadTo(cx - r * 0.05, cy + r * 0.5, cx - r * 0.16, cy + r * 0.46)
    bc.moveTo(cx, cy + r * 0.36); bc.quadTo(cx + r * 0.05, cy + r * 0.5, cx + r * 0.16, cy + r * 0.46)
    cv.drawPath(bc, _p(COR["contorno"], 255, s * 0.8))
    for lado in (-1, 1):
        for j, ang in enumerate((-0.12, 0.02, 0.16)):
            b = skia.Path(); x0 = cx + lado * r * 0.3; y0 = cy + r * 0.42
            b.moveTo(x0, y0); b.quadTo(x0 + lado * r * 0.6, y0 + ang * r - r * 0.04, x0 + lado * r * 1.25, y0 + ang * r * 2.2)
            cv.drawPath(b, _p(COR["bigode"], 235, s * 0.55))


def _sentado(cv, olhar, pupila, piscar, s, cauda=0.0, inclinar=0.0):
    # cauda enrolada pela frente das patas (a ponta balança com 'cauda')
    _cauda(cv, [(-0.30, -0.12), (-0.55, 0.0), (-0.1, 0.03), (0.33, -0.03 - 0.07 * cauda)], 0.075, s)
    # quadril/coxa traseira e corpo
    corpo = _bolha([(-0.42, -0.05), (-0.48, -0.3), (-0.33, -0.52), (-0.05, -0.62), (0.18, -0.6), (0.24, -0.38), (0.2, -0.05), (-0.1, 0.0)])
    _preencher(cv, corpo, COR["pelo"], _elipse(-0.3, -0.05, 0.32, 0.2), s)
    cv.save(); cv.clipPath(corpo, doAntiAlias=True)
    for i in range(4):                                                   # listras do flanco
        lp = skia.Path(); x = -0.38 + i * 0.1
        lp.moveTo(x, -0.5 + i * 0.02); lp.quadTo(x - 0.06, -0.32, x + 0.01, -0.15)
        cv.drawPath(lp, _p(COR["listra"], 255, 0.035))
    cv.restore()
    peito = _bolha([(0.02, -0.6), (0.2, -0.58), (0.25, -0.38), (0.19, -0.12), (0.06, -0.16), (0.0, -0.4)])
    _preencher(cv, peito, COR["peito"], None, None)
    # patas da frente
    for dx in (0.02, 0.15):
        pt = skia.Path(); pt.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(dx - 0.045, -0.36, dx + 0.045, 0.0), 0.045, 0.045))
        _preencher(cv, pt, COR["peito"], None, s)
        for j in (-1, 0, 1):
            cv.drawLine(dx + j * 0.017, -0.004, dx + j * 0.017, -0.03, _p(COR["contorno"], 200, s * 0.6))
    # cabeça
    _cabeca(cv, 0.14, -0.78, 0.2, olhar, pupila, piscar, s, inclinar=inclinar)


def _agachado(cv, olhar, pupila, piscar, s, cauda=0.0):
    # cauda reta para trás, ponta levantada (a ponta tremula com 'cauda': caçando)
    _cauda(cv, [(-0.4, -0.3), (-0.6, -0.33), (-0.78, -0.32), (-0.92, -0.42 - 0.06 * cauda)], 0.065, s)
    corpo = _bolha([(-0.5, -0.06), (-0.55, -0.32), (-0.4, -0.45), (-0.05, -0.42), (0.18, -0.5), (0.32, -0.35), (0.3, -0.05), (-0.1, -0.02)])
    _preencher(cv, corpo, COR["pelo"], _elipse(-0.15, 0.0, 0.5, 0.17), s)
    cv.save(); cv.clipPath(corpo, doAntiAlias=True)
    for i in range(5):
        lp = skia.Path(); x = -0.45 + i * 0.12
        lp.moveTo(x, -0.46); lp.quadTo(x - 0.05, -0.3, x + 0.02, -0.16)
        cv.drawPath(lp, _p(COR["listra"], 255, 0.035))
    cv.restore()
    for dx in (0.12, 0.26, -0.42, -0.3):                                 # patas dobradas, rente ao chão
        pt = skia.Path(); pt.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(dx - 0.05, -0.1, dx + 0.07, 0.0), 0.05, 0.05))
        _preencher(cv, pt, COR["peito"] if dx > 0 else COR["pelo"], None, s)
    _cabeca(cv, 0.4, -0.3, 0.19, olhar, pupila, piscar, s, orelhas="de_lado")


PASSADA = 0.16                      # meio passo (unidades da altura do gato)
APOIO = 0.6                         # fração do ciclo com a pata no chão
AVANCO_POR_CICLO = 2 * PASSADA / APOIO   # quanto o gato anda por ciclo, para os pés não deslizarem (× altura_px)


def _perna(cv, quadril, pe, a, b, frente, larg, cor, s):
    """Perna de 2 segmentos por IK: do quadril/ombro até o pé. A junta dobra para a frente (pata da frente) ou para trás."""
    dx = pe[0] - quadril[0]; dy = pe[1] - quadril[1]; d = max(1e-6, min(a + b - 1e-4, math.hypot(dx, dy)))
    ca = (a * a + d * d - b * b) / (2 * a * d); ang = math.atan2(dy, dx); off = math.acos(max(-1.0, min(1.0, ca)))
    ang1 = ang - off if frente else ang + off                   # y para baixo: −off põe a junta à frente (+x) numa perna que desce
    j = (quadril[0] + a * math.cos(ang1), quadril[1] + a * math.sin(ang1))
    for p0, p1, w in ((quadril, j, larg), (j, pe, larg * 0.82)):
        cv.drawLine(*p0, *p1, _p(COR["contorno"], 255, w + 2 * s)); cv.drawLine(*p0, *p1, _p(cor, 255, w))
    pt = _elipse(pe[0] + 0.02, pe[1] - 0.015, 0.045, 0.025); cv.drawPath(pt, _p(cor)); cv.drawPath(pt, _p(COR["contorno"], 255, s))


def _andando(cv, olhar, pupila, piscar, s, fase, cauda, inclinar):
    """Gato andando de lado (cabeça à direita). Patas do lado de lá desenhadas antes, num tom mais escuro."""
    bob = 0.012 * math.sin(4 * math.pi * fase)
    cv.save(); cv.translate(0, bob)
    offs = {"tras_longe": 0.5, "frente_longe": 0.75, "tras_perto": 0.0, "frente_perto": 0.25}
    pos = {"tras_longe": (-0.30, -0.40), "frente_longe": (0.18, -0.40), "tras_perto": (-0.38, -0.38), "frente_perto": (0.26, -0.38)}

    def pe(nome):
        f = (fase + offs[nome]) % 1.0; q = pos[nome]
        if f < APOIO:                                                   # apoio: o pé fica parado no chão e o corpo passa por cima
            x = PASSADA - 2 * PASSADA * f / APOIO; y = 0.0
        else:                                                           # balanço: levanta em arco e volta para a frente
            u = (f - APOIO) / (1 - APOIO); e = 0.5 - 0.5 * math.cos(math.pi * u)
            x = -PASSADA + 2 * PASSADA * e; y = -0.08 * math.sin(math.pi * u)
        return (q[0] + x, y - bob)

    for nome in ("tras_longe", "frente_longe"):
        _perna(cv, pos[nome], pe(nome), 0.205, 0.205, "frente" in nome, 0.095, COR["pelo_sombra"], s)
    _cauda(cv, [(-0.42, -0.55), (-0.6, -0.68), (-0.62, -0.95), (-0.5 + 0.12 * cauda, -1.05)], 0.065, s)
    corpo = _bolha([(-0.52, -0.40), (-0.56, -0.60), (-0.36, -0.72), (0.05, -0.70), (0.28, -0.74), (0.40, -0.58), (0.32, -0.38), (-0.1, -0.33)])
    _preencher(cv, corpo, COR["pelo"], _elipse(-0.1, -0.36, 0.5, 0.12), s)
    cv.save(); cv.clipPath(corpo, doAntiAlias=True)
    for i in range(5):
        lp = skia.Path(); x = -0.45 + i * 0.13
        lp.moveTo(x, -0.76); lp.quadTo(x - 0.05, -0.6, x + 0.02, -0.46); cv.drawPath(lp, _p(COR["listra"], 255, 0.035))
    cv.drawPath(_elipse(0.28, -0.52, 0.12, 0.12), _p(COR["peito"]))
    cv.restore()
    for nome in ("tras_perto", "frente_perto"):
        _perna(cv, pos[nome], pe(nome), 0.205, 0.205, "frente" in nome, 0.10, COR["pelo"] if "tras" in nome else COR["peito"], s)
    cv.restore()
    _cabeca(cv, 0.46, -0.86 + bob, 0.19, olhar, pupila, piscar, s, inclinar=inclinar)


def pata(cv, cx, cy, tamanho_px, garras=1.0, angulo=0.0):
    """Pata em close (vem do alto do quadro): pelo, almofadas rosadas e garras que saem com 'garras' (0–1)."""
    T = tamanho_px; s = max(1.0, T * 0.008) / T
    cv.save(); cv.translate(cx, cy); cv.rotate(angulo); cv.scale(T, T)
    braco = _bolha([(-0.28, -1.4), (0.28, -1.4), (0.36, -0.2), (0.0, 0.1), (-0.36, -0.2)])
    _preencher(cv, braco, COR["pelo"], _elipse(0.25, -0.6, 0.2, 0.9), s * T and s)
    for i in range(3):
        cv.drawLine(-0.2 + i * 0.2, -1.2, -0.15 + i * 0.2, -0.75, _p(COR["listra"], 255, 0.06))
    for j, (dx, dy) in enumerate([(-0.24, 0.0), (-0.08, 0.1), (0.08, 0.1), (0.24, 0.0)]):
        dedo = _elipse(dx, dy, 0.1, 0.11); _preencher(cv, dedo, COR["peito"], None, s)
        cv.drawPath(_elipse(dx, dy + 0.02, 0.055, 0.05), _p(COR["almofada"]))
        if garras > 0:
            g = skia.Path(); g.moveTo(dx - 0.025, dy + 0.08); g.quadTo(dx + 0.01, dy + 0.08 + 0.2 * garras, dx + 0.05 * garras, dy + 0.1 + 0.24 * garras)
            g.quadTo(dx + 0.015, dy + 0.12, dx + 0.025, dy + 0.08); g.close()
            cv.drawPath(g, _p(COR["garra"])); cv.drawPath(g, _p(COR["contorno"], 255, s * 0.8))
    cv.drawPath(_elipse(0.0, -0.17, 0.17, 0.12), _p(COR["almofada"]))
    cv.restore()


def olho(cv, cx, cy, largura_px, pupila=0.2, olhar=0.0):
    """Olho em close com o pelo em volta (para o crash-zoom de 'acabou de te ver')."""
    L = largura_px
    cv.drawRect(skia.Rect.MakeLTRB(cx - L, cy - L * 0.7, cx + L, cy + L * 0.7), _p(COR["pelo"]))
    for i in range(9):
        y = cy - L * 0.65 + i * L * 0.16
        lp = skia.Path(); lp.moveTo(cx - L, y); lp.quadTo(cx, y - L * 0.08, cx + L, y + L * 0.03)
        cv.drawPath(lp, _p(COR["listra"], 140, L * 0.04))
    _olho_amendoa(cv, cx, cy, L, L * 0.55, pupila, olhar, 0.0, max(1.5, L * 0.012))
