#!/usr/bin/env python3
"""EP02 — grafismo 2D: legendas, marca d'água, rótulos de números, cartelas de tempo, termômetro, HUD do jogo,
tela de instalação, inserts (videogame, coração, tesouro) e cartela final. Tudo desenho próprio, sem marca de terceiros:
o jogo é uma cidade genérica ao pôr do sol, sem logotipo; o console e o controle são genéricos."""
import math, sys
from pathlib import Path
import numpy as np, cv2, skia

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "personagens" / "adultos"))
import poses as PO                                                            # noqa: E402

OW, OH = 1080, 1920
ROBOTO = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "RobotoCondensed-ExtraBold.ttf"))
NUNITO = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "Nunito-ExtraBold.ttf"))
AMARELO = 0xFFFFC21F; ESCURO = 0xFF1A110C; BRANCO = 0xFFFFFFFF


def pt(cor, a=1.0, **k):
    p = skia.Paint(AntiAlias=True, Color=cor, **k); p.setAlphaf(a); return p


def borda(cor, w, a=1.0):
    p = skia.Paint(AntiAlias=True, Color=cor, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join,
                   StrokeCap=skia.Paint.kRound_Cap); p.setAlphaf(a); return p


def skimg(a):
    a = np.ascontiguousarray(a)
    if a.shape[2] == 3:
        a = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    return skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.kRGBA_8888_ColorType)


def snap(s, rgba=False):
    a = np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))
    return a if rgba else a[..., :3]


def ease(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def pop(x, ini=0.82):
    """Entrada com overshoot (para cartelas e rótulos): 0 → 1,06 → 1."""
    x = min(1.0, max(0.0, x))
    if x < 0.6:
        return ini + (1.06 - ini) * ease(x / 0.6)
    return 1.06 - 0.06 * ease((x - 0.6) / 0.4)


def texto_contorno(cv, txt, x, y, f, cor=BRANCO, w=None, sombra=True):
    w = w if w is not None else f.getSize() * 0.17
    if sombra:
        cv.drawString(txt, x + 4, y + 7, f, pt(0xFF000000, 0.55, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    cv.drawString(txt, x, y, f, borda(ESCURO, w)); cv.drawString(txt, x, y, f, pt(cor))


def centro(cv, txt, cx, y, tam, cor=BRANCO, fonte=None):
    f = skia.Font(fonte or ROBOTO, tam); w = f.measureText(txt); texto_contorno(cv, txt, cx - w / 2, y, f, cor); return w


# ---------------------------------------------------------------- marca d'água (exatamente "MODO CURIOSO")
def marca_dagua(cv):
    alt = 30; tam = alt / 0.711; f = skia.Font(ROBOTO, tam)
    w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
    x = OW - 46 - (w1 + esp + w2); base = 64 + alt
    cv.drawString("MODO", x, base, f, pt(BRANCO, 0.6)); cv.drawString("CURIOSO", x + w1 + esp, base, f, pt(AMARELO))


# ---------------------------------------------------------------- legendas (2–3 palavras, troca na fala)
class Legendas:
    def __init__(self, blocos):
        self.b = blocos; self.pos = {}

    def desenhar(self, cv, t, rosto_y=None, fixo=None):
        for i, lg in enumerate(self.b):
            if lg["ini"] <= t < lg["fim"]:
                if i not in self.pos:
                    self.pos[i] = "topo" if (rosto_y is not None and 0.6 * OH < rosto_y < 0.86 * OH) else "baixo"
                tl = t - lg["ini"]; esc = 0.97 + 0.03 * min(1, tl / (2 / 30))
                tam = 96 * esc; f = skia.Font(ROBOTO, tam); palavras = lg["txt"].split(); dest = set(lg["dest"])
                esp = f.measureText(" "); larg = sum(f.measureText(w) for w in palavras) + esp * (len(palavras) - 1)
                if larg > OW * 0.86:
                    tam *= OW * 0.86 / larg; f = skia.Font(ROBOTO, tam); esp = f.measureText(" ")
                    larg = sum(f.measureText(w) for w in palavras) + esp * (len(palavras) - 1)
                pos = fixo or (0.215 if self.pos[i] == "topo" else 0.745)
                cy = OH * pos; base = cy + tam * 0.711 / 2; x = OW / 2 - larg / 2
                for w in palavras:
                    cor = AMARELO if w.strip("?!.,…") in dest else BRANCO
                    cv.drawString(w, x + 3, base + 6, f, pt(0xFF000000, 0.55, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
                    cv.drawString(w, x, base, f, borda(ESCURO, tam * 0.711 * 0.24)); cv.drawString(w, x, base, f, pt(cor))
                    x += f.measureText(w) + esp
                return lg
        return None


# ---------------------------------------------------------------- rótulo com linha-guia e número grande
def rotulo(cv, txt, sub, ax, ay, lado=1, k=1.0, cor=AMARELO):
    if k <= 0:
        return
    s = pop(k)
    f = skia.Font(NUNITO, 96 * s); w = f.measureText(txt); f2 = skia.Font(NUNITO, 40 * s); w2 = f2.measureText(sub or "")
    larg = max(w, w2) + 60
    if lado > 0 and ax + 160 + larg > OW - 30:
        lado = -1
    if lado < 0 and ax - 160 - larg < 30:
        lado = 1
    bx = ax + lado * 160; by = max(230, ay - 150)
    pth = skia.Path(); pth.moveTo(ax, ay); pth.lineTo(bx, by); pth.lineTo(bx + lado * 40, by)
    m = skia.PathMeasure(pth, False); seg = skia.Path(); m.getSegment(0, m.getLength() * min(1, k * 2.5), seg, True)
    cv.drawPath(seg, borda(0xFF000000, 9, 0.55)); cv.drawPath(seg, borda(BRANCO, 5)); cv.drawCircle(ax, ay, 9, pt(BRANCO))
    x0 = bx + lado * 52 if lado > 0 else bx - 52 - w
    x0 = min(max(30, x0), OW - 30 - w)
    texto_contorno(cv, txt, x0, by + 34, f, cor, w=14 * s)
    if sub:
        x2 = x0 if lado > 0 else x0 + w - w2; x2 = min(max(30, x2), OW - 30 - w2)
        texto_contorno(cv, sub, x2, by + 84 * s, f2, BRANCO, w=8 * s)


def cartela_tempo(cv, numero, linha, k, y=0.30, sub=None):
    """'2 HORAS DEPOIS': número enorme em amarelo com relógio girando, entrada com pop."""
    if k <= 0:
        return
    s = pop(k); cx = OW / 2; cy = OH * y
    r = 120 * s; rx = cx - 250 * s
    cv.drawCircle(rx, cy, r, pt(0xFFF6F1E7)); cv.drawCircle(rx, cy, r, borda(ESCURO, 12 * s))
    for i in range(12):
        a = i * math.pi / 6; cv.drawLine(rx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78, rx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9, borda(ESCURO, 6 * s))
    am = -math.pi / 2 + k * 14; ah = -math.pi / 2 + k * 14 / 12
    cv.drawLine(rx, cy, rx + math.cos(am) * r * 0.75, cy + math.sin(am) * r * 0.75, borda(0xFFD9452B, 9 * s))
    cv.drawLine(rx, cy, rx + math.cos(ah) * r * 0.5, cy + math.sin(ah) * r * 0.5, borda(ESCURO, 12 * s))
    cv.drawCircle(rx, cy, 12 * s, pt(ESCURO))
    f = skia.Font(ROBOTO, 330 * s); texto_contorno(cv, numero, cx - 90 * s, cy + 118 * s, f, AMARELO, w=26 * s)
    f2 = skia.Font(ROBOTO, 110 * s); wn = f.measureText(numero)
    texto_contorno(cv, linha, cx - 90 * s + wn + 24 * s, cy + 20 * s, f2, BRANCO, w=14 * s)
    if sub:
        texto_contorno(cv, sub, cx - 90 * s + wn + 24 * s, cy + 118 * s, skia.Font(ROBOTO, 84 * s), BRANCO, w=11 * s)


def relogio_digital(cv, hora, x, y, k=1.0, tam=88):
    if k <= 0:
        return
    s = pop(k); f = skia.Font(ROBOTO, tam * s); w = f.measureText(hora)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2 - 28 * s, y - tam * 0.86 * s, w + 56 * s, tam * 1.15 * s), 22 * s, 22 * s)
    cv.drawRRect(rr, pt(0xFF101626, 0.86)); cv.drawRRect(rr, borda(AMARELO, 5 * s))
    cv.drawString(hora, x - w / 2, y + 4, f, pt(AMARELO))


def termometro(cv, x, y, temp, k=1.0, tmin=20, tmax=70):
    if k <= 0:
        return
    s = pop(k); h = 420 * s; w = 46 * s
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h, w, h), w / 2, w / 2), pt(0xFFF6F1E7))
    cv.drawCircle(x, y + 10 * s, 52 * s, pt(0xFFF6F1E7))
    fr = (temp - tmin) / (tmax - tmin); cor = 0xFFE53B2B if temp > 45 else (0xFFF08A24 if temp > 32 else 0xFF3D80D8)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w * 0.28, y - h * (0.1 + 0.85 * fr), w * 0.56, h * (0.1 + 0.85 * fr) + 10 * s), w * 0.28, w * 0.28), pt(cor))
    cv.drawCircle(x, y + 10 * s, 38 * s, pt(cor))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h, w, h), w / 2, w / 2), borda(ESCURO, 8 * s))
    cv.drawCircle(x, y + 10 * s, 52 * s, borda(ESCURO, 8 * s))
    f = skia.Font(NUNITO, 110 * s); txt = f"{temp:.0f} °C"
    texto_contorno(cv, txt, x + 80 * s, y - h * 0.45, f, AMARELO if temp > 32 else 0xFF9FD3FF, w=14 * s)


def vapor(cv, x, y, t, forca=1.0, esc=1.0):
    for i in range(5):
        fase = (t * 0.7 + i / 5) % 1.0; a = forca * (1 - fase) * math.sin(math.pi * min(1, fase * 3))
        if a <= 0.01:
            continue
        xx = x + (i - 2) * 26 * esc + 18 * esc * math.sin(t * 3 + i * 1.7 + fase * 6); yy = y - fase * 260 * esc
        cv.drawCircle(xx, yy, (22 + 40 * fase) * esc, pt(0xFFFFFFFF, 0.35 * a, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14 * esc)))


def brilhos(cv, cx, cy, raio, t, n=14, cor=0xFFFFF1C2, semente=1, forca=1.0):
    rng = np.random.default_rng(semente)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi); d = raio * rng.uniform(0.3, 1.0); f = rng.uniform(0, 6)
        k = max(0.0, math.sin(t * rng.uniform(4, 8) + f)) * forca
        if k <= 0.02:
            continue
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d; L = 26 * k * rng.uniform(0.6, 1.4)
        p = borda(cor, 5 * k)
        cv.drawLine(x - L, y, x + L, y, p); cv.drawLine(x, y - L, x, y + L, p)
        cv.drawCircle(x, y, 6 * k, pt(BRANCO, k))


def raios(cv, cx, cy, t, cor=0xFFFFE6A0, n=14, r0=60, r1=1400, a=0.25):
    for i in range(n):
        ang = t * 0.4 + i * 2 * math.pi / n; d = 0.07
        pth = skia.Path(); pth.moveTo(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
        pth.lineTo(cx + math.cos(ang - d) * r1, cy + math.sin(ang - d) * r1); pth.lineTo(cx + math.cos(ang + d) * r1, cy + math.sin(ang + d) * r1); pth.close()
        cv.drawPath(pth, pt(cor, a))


def fundo_insert(cv, t, cor_a=0xFF0E1838, cor_b=0xFF22124A):
    g = skia.GradientShader.MakeRadial((OW / 2, OH * 0.45), OH * 0.75, [cor_b, cor_a])
    cv.drawRect(skia.Rect.MakeWH(OW, OH), skia.Paint(Shader=g))
    rng = np.random.default_rng(5)
    for i in range(26):
        x = rng.uniform(0, OW) + 30 * math.sin(t * 0.4 + i); y = rng.uniform(0, OH) - (t * 25 * rng.uniform(0.5, 1.5)) % OH
        y = y % OH; r = rng.uniform(20, 90)
        cv.drawCircle(x, y, r, pt([0xFF5FB8FF, 0xFFFFC21F, 0xFFB57BFF][i % 3], 0.10, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.4)))


# ---------------------------------------------------------------- inserts
def insert_console(t, k):
    """O videogame novinho saindo da caixa: luz de dentro, giro leve, brilhos. Rótulo: 0 HORAS DE USO."""
    s = skia.Surface(OW, OH); cv = s.getCanvas(); fundo_insert(cv, t)
    raios(cv, OW / 2, OH * 0.6, t, a=0.18 + 0.1 * math.sin(t * 3))
    u = 900 * (0.9 + 0.1 * ease(k * 2)); y = OH * (0.62 - 0.12 * ease(k * 1.6))
    PO.caixa_presente(cv, OW / 2, OH * 0.80, 760, larg=1.15, alt=0.62, tampa=1.0, brilho=0.6)
    cv.save(); cv.translate(OW / 2, y); cv.rotate(-8 + 6 * math.sin(t * 1.3)); PO.console(cv, 0, 0, u, deitado=False, luz=0.6 + 0.4 * math.sin(t * 4)); cv.restore()
    brilhos(cv, OW / 2, y, 420, t, n=18)
    rotulo(cv, "0 h", "DE USO", OW / 2 + 130, y - 260, 1, k=(k - 0.35) * 2.2)
    return snap(s)


def insert_coracao(t, k, bpm0=72, bpm1=140):
    s = skia.Surface(OW, OH); cv = s.getCanvas(); fundo_insert(cv, t, 0xFF1A0E22, 0xFF3A1230)
    bpm = bpm0 + (bpm1 - bpm0) * ease(k * 1.3); f = bpm / 60.0
    fase = (t * f) % 1.0; bat = 1 + 0.16 * math.exp(-fase * 9) + 0.08 * math.exp(-((fase - 0.25) % 1) * 12)
    cx, cy, R = OW / 2, OH * 0.43, 300 * bat
    p = skia.Path(); p.moveTo(cx, cy + R * 0.9)
    p.cubicTo(cx - R * 1.4, cy + R * 0.05, cx - R * 0.95, cy - R * 1.05, cx, cy - R * 0.35)
    p.cubicTo(cx + R * 0.95, cy - R * 1.05, cx + R * 1.4, cy + R * 0.05, cx, cy + R * 0.9); p.close()
    cv.drawPath(p, pt(0xFFE2384D, 0.35, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
    cv.drawPath(p, pt(0xFFE2384D)); cv.save(); cv.clipPath(p, doAntiAlias=True)
    cv.drawCircle(cx + R * 0.5, cy + R * 0.5, R * 0.9, pt(0xFFB3223A)); cv.drawCircle(cx - R * 0.45, cy - R * 0.45, R * 0.22, pt(BRANCO, 0.5)); cv.restore()
    cv.drawPath(p, borda(ESCURO, 14))
    # eletrocardiograma
    y0 = OH * 0.72; ecg = skia.Path(); ecg.moveTo(40, y0)
    for x in range(40, OW - 40, 6):
        u = ((x / OW) * 3 - t * f) % 1.0
        dy = (-170 if 0.10 < u < 0.13 else (120 if 0.13 < u < 0.16 else 0)) + 25 * math.exp(-((u - 0.35) * 18) ** 2)
        ecg.lineTo(x, y0 + dy)
    cv.drawPath(ecg, borda(0xFF5CFFB0, 7)); cv.drawPath(ecg, borda(0xFF5CFFB0, 18, 0.25))
    rotulo(cv, f"{bpm:.0f} BPM", "BATIMENTOS POR MINUTO", OW * 0.66, OH * 0.30, 1, k=k * 2.5)
    return snap(s)


def insert_tesouro(t, k):
    s = skia.Surface(OW, OH); cv = s.getCanvas(); fundo_insert(cv, t, 0xFF20140A, 0xFF5A3A0E)
    raios(cv, OW / 2, OH * 0.5, t * 1.5, cor=0xFFFFD36A, n=18, a=0.22)
    for i in range(22):   # moedas douradas genéricas caindo
        rng = np.random.default_rng(i); x = rng.uniform(80, OW - 80); y = (rng.uniform(-OH, 0) + t * 900 * rng.uniform(0.6, 1.1)) % (OH + 200) - 100
        r = rng.uniform(26, 44); sq = abs(math.cos(t * 5 + i))
        cv.drawOval(skia.Rect.MakeXYWH(x - r * sq, y - r, 2 * r * sq + 2, 2 * r), pt(0xFFFFC21F)); cv.drawOval(skia.Rect.MakeXYWH(x - r * sq, y - r, 2 * r * sq + 2, 2 * r), borda(0xFF8A5A10, 5))
    z = 0.85 + 0.15 * ease(k)
    cv.drawCircle(OW / 2, OH * 0.5, 420 * z, pt(0xFFFFD36A, 0.45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 90)))
    cv.save(); cv.translate(OW / 2, OH * 0.5); cv.rotate(6 * math.sin(t * 2)); PO.console(cv, 0, 0, 980 * z, luz=1.0); cv.restore()
    brilhos(cv, OW / 2, OH * 0.5, 480, t, n=22, cor=0xFFFFE08A, semente=4)
    return snap(s)


def cartela_final(t, k):
    s = skia.Surface(OW, OH); cv = s.getCanvas(); fundo_insert(cv, t)
    e = pop(min(1, k * 2.0))
    linhas = [("COMENTA AÍ:", AMARELO), ("VOCÊ DESLIGARIA", BRANCO), ("O VIDEOGAME?", BRANCO)]
    for i, (ln, cor) in enumerate(linhas):
        centro(cv, ln, OW / 2, OH * 0.30 + i * 150, 118 * e, cor)
    PO.controle(cv, OW / 2, OH * 0.585, 900 * e, 6 * math.sin(t * 3))
    if k > 0.25:
        e2 = pop((k - 0.25) * 2.5); centro(cv, "SEGUE AÍ!", OW / 2, OH * 0.80, 140 * e2, BRANCO)
        f = skia.Font(ROBOTO, 64 * e2); w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
        x = OW / 2 - (w1 + esp + w2) / 2; y = OH * 0.86
        texto_contorno(cv, "MODO", x, y, f, BRANCO, w=8); texto_contorno(cv, "CURIOSO", x + w1 + esp, y, f, AMARELO, w=8)
    return snap(s)


# ---------------------------------------------------------------- o "jogo" (cidade genérica + HUD próprio)
def carro_jogador(cv, cx, cy, L, t, cor=0xFFE0457B):
    """Carro esportivo genérico visto de trás (sem marca, sem placa com caracteres)."""
    sw = 6 * math.sin(t * 2.3); cv.save(); cv.translate(cx + sw, cy); cv.scale(L, L)
    cv.drawOval(skia.Rect.MakeXYWH(-0.62, 0.20, 1.24, 0.14), pt(0xFF000000, 0.5, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.03)))
    for sx in (-0.42, 0.42):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx - 0.11, 0.06, 0.22, 0.22), 0.04, 0.04), pt(0xFF15151A))
    corpo = skia.Path(); corpo.moveTo(-0.6, 0.18); corpo.lineTo(-0.58, -0.02); corpo.quadTo(-0.5, -0.12, -0.3, -0.14)
    corpo.lineTo(-0.22, -0.32); corpo.quadTo(0, -0.37, 0.22, -0.32); corpo.lineTo(0.3, -0.14); corpo.quadTo(0.5, -0.12, 0.58, -0.02)
    corpo.lineTo(0.6, 0.18); corpo.close()
    cv.drawPath(corpo, pt(cor)); vid = skia.Path(); vid.moveTo(-0.2, -0.15); vid.lineTo(-0.16, -0.3); vid.quadTo(0, -0.34, 0.16, -0.3); vid.lineTo(0.2, -0.15); vid.close()
    cv.drawPath(vid, pt(0xFF1F2A44)); cv.drawPath(vid, pt(0xFF9FD3FF, 0.25))
    for sx in (-1, 1):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx * 0.36 - 0.13, -0.06, 0.26, 0.06), 0.02, 0.02), pt(0xFFFF3B3B))
        cv.drawCircle(sx * 0.36, -0.03, 0.12, pt(0xFFFF3B3B, 0.35, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.05)))
    cv.drawRect(skia.Rect.MakeXYWH(-0.14, 0.02, 0.28, 0.07), pt(0xFFF6F1E7))
    cv.drawPath(corpo, borda(ESCURO, 0.018)); cv.restore()


def hud(cv, t, W, H, velocidade=None, missao_pct=3, escala=1.0, k_missao=1.0):
    """HUD genérico do canal (não imita o de nenhum jogo): faixa de missão no topo, minimapa quadrado, velocímetro."""
    e = escala
    if k_missao > 0:
        f = skia.Font(ROBOTO, 46 * e); x, y = 40 * e, 70 * e
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 16 * e, y - 50 * e, 420 * e, 110 * e), 14 * e, 14 * e), pt(0xFF0B0F1C, 0.72))
        cv.drawString("MISSÃO 1", x, y, f, pt(AMARELO))
        cv.drawRect(skia.Rect.MakeXYWH(x, y + 18 * e, 380 * e, 20 * e), pt(0xFF3A4157))
        cv.drawRect(skia.Rect.MakeXYWH(x, y + 18 * e, 380 * e * missao_pct / 100, 20 * e), pt(0xFF5CFFB0))
        cv.drawString(f"{missao_pct} %", x + 250 * e, y, f, pt(BRANCO))
    m = 190 * e; mx, my = 40 * e, H - m - 50 * e
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(mx, my, m, m), 18 * e, 18 * e), pt(0xFF0B0F1C, 0.75))
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(mx, my, m, m), 18 * e, 18 * e), True)
    off = (t * 40 * e) % (60 * e)
    for i in range(-1, 5):
        yy = my + i * 60 * e + off; cv.drawLine(mx, yy, mx + m, yy, borda(0xFF4A5470, 8 * e))
    cv.drawLine(mx + m / 2, my, mx + m / 2, my + m, borda(0xFF8A93B0, 14 * e)); cv.restore()
    seta = skia.Path(); seta.moveTo(mx + m / 2, my + m / 2 - 18 * e); seta.lineTo(mx + m / 2 + 12 * e, my + m / 2 + 14 * e); seta.lineTo(mx + m / 2 - 12 * e, my + m / 2 + 14 * e); seta.close()
    cv.drawPath(seta, pt(AMARELO))
    if velocidade is not None:
        f = skia.Font(ROBOTO, 96 * e); txt = f"{velocidade:.0f}"; w = f.measureText(txt)
        texto_contorno(cv, txt, W - 70 * e - w - 120 * e, H - 80 * e, f, BRANCO, w=10 * e, sombra=False)
        texto_contorno(cv, "km/h", W - 70 * e - 110 * e, H - 80 * e, skia.Font(ROBOTO, 50 * e), AMARELO, w=6 * e, sombra=False)


def linhas_velocidade(cv, t, W, H, forca=1.0, cx=None, cy=None):
    cx = W / 2 if cx is None else cx; cy = H * 0.52 if cy is None else cy
    rng = np.random.default_rng(int(t * 30) // 2)
    for i in range(int(28 * forca)):
        a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0.35, 0.6) * W; L = rng.uniform(120, 380)
        cv.drawLine(cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * (r0 + L), cy + math.sin(a) * (r0 + L), borda(BRANCO, rng.uniform(2, 5), rng.uniform(0.2, 0.5)))


def tela_instalacao(t, k, W=960, H=540):
    """Tela de instalação do jogo (genérica): pôr do sol retrô, palmeiras em silhueta e barra até 100 %."""
    s = skia.Surface(W, H); cv = s.getCanvas()
    g = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [0xFF2A0E4A, 0xFFB0306A, 0xFFFF8A3D])
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g))
    cv.drawCircle(W / 2, H * 0.62, H * 0.32, pt(0xFFFFD36A))
    for i in range(6):
        y = H * 0.5 + i * 18 + (t * 20) % 18; cv.drawRect(skia.Rect.MakeXYWH(0, y, W, 4 + i * 1.5), pt(0xFFB0306A))
    cv.drawRect(skia.Rect.MakeXYWH(0, H * 0.74, W, H * 0.26), pt(0xFF1A0A2E))
    for px, ph, inc in ((W * 0.14, 0.55, -8), (W * 0.24, 0.42, 6), (W * 0.83, 0.5, 7)):
        tr = skia.Path(); tr.moveTo(px - 6, H * 0.75); tr.quadTo(px + inc * 3, H * (0.75 - ph / 2), px + inc * 4, H * (0.75 - ph)); tr.lineTo(px + inc * 4 + 8, H * (0.75 - ph)); tr.quadTo(px + inc * 3 + 10, H * (0.75 - ph / 2), px + 8, H * 0.75); tr.close()
        cv.drawPath(tr, pt(0xFF1A0A2E)); tx, ty = px + inc * 4, H * (0.75 - ph)
        for a in range(7):
            ang = math.radians(-170 + a * 28 + 3 * math.sin(t * 2 + a)); fl = skia.Path(); fl.moveTo(tx, ty)
            fl.quadTo(tx + math.cos(ang) * 50, ty + math.sin(ang) * 50 - 20, tx + math.cos(ang) * 95, ty + math.sin(ang) * 95 + 25)
            cv.drawPath(fl, borda(0xFF1A0A2E, 10))
    pct = min(100, 100 * ease(k * 1.25))
    bx, by, bw = W * 0.18, H * 0.86, W * 0.64
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, bw, 22), 11, 11), pt(0xFF0B0F1C, 0.7))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, bw * pct / 100, 22), 11, 11), pt(0xFF5CFFB0))
    f = skia.Font(ROBOTO, 40); txt = "INSTALADO" if pct >= 99.5 else "INSTALANDO…"
    cv.drawString(txt, bx, by - 14, f, pt(BRANCO)); tt = f"{pct:.0f} %"; cv.drawString(tt, bx + bw - f.measureText(tt), by - 14, f, pt(AMARELO))
    return snap(s)


def tela_ligando(t, W=960, H=540):
    """Tela do console ligando: fundo azul com ondas de luz (sem logotipo)."""
    s = skia.Surface(W, H); cv = s.getCanvas()
    g = skia.GradientShader.MakeRadial((W / 2, H / 2), W * 0.7, [0xFF2B5BD7, 0xFF070B1E]); cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g))
    for i in range(5):
        r = ((t * 220 + i * 90) % 450); cv.drawCircle(W / 2, H / 2, r, borda(0xFF9FD3FF, 3, max(0, 1 - r / 450)))
    cv.drawCircle(W / 2, H / 2, 30 + 6 * math.sin(t * 6), pt(BRANCO, 0.9, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
    return snap(s)


def tela_missao(t, pct=3, W=960, H=540, fundo=None):
    s = skia.Surface(W, H); cv = s.getCanvas()
    if fundo is not None:
        cv.drawImage(skimg(fundo), 0, 0)
    cv.drawRect(skia.Rect.MakeWH(W, H), pt(0xFF000000, 0.35))
    f = skia.Font(ROBOTO, 110); txt = "MISSÃO 1"; w = f.measureText(txt); texto_contorno(cv, txt, W / 2 - w / 2, H * 0.42, f, AMARELO, w=10)
    bw = W * 0.7; bx = (W - bw) / 2; by = H * 0.55
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, bw, 40), 20, 20), pt(0xFF0B0F1C, 0.85))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, max(40, bw * pct / 100), 40), 20, 20), pt(0xFF5CFFB0))
    f2 = skia.Font(ROBOTO, 90); tt = f"{pct} % CONCLUÍDA"; w2 = f2.measureText(tt); texto_contorno(cv, tt, W / 2 - w2 / 2, H * 0.82, f2, BRANCO, w=9)
    return snap(s)


def warp_tela(cv, img, cantos, alfa=1.0, brilho=1.0):
    """Desenha 'img' na tela da TV (cantos em px na ordem SE, SD, ID, IE) com perspectiva, brilho e reflexo leve."""
    h, w = img.shape[:2]
    m = skia.Matrix(); ok = m.setPolyToPoly([skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)],
                                           [skia.Point(*c) for c in cantos])
    if not ok:
        return
    a = img if brilho == 1.0 else np.clip(img.astype(np.float32) * brilho, 0, 255).astype(np.uint8)
    cv.save(); cv.concat(m)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alfa)
    cv.drawImageRect(skimg(a), skia.Rect.MakeWH(w, h), skia.SamplingOptions(skia.FilterMode.kLinear), p)
    g = skia.GradientShader.MakeLinear([(0, 0), (w, h)], [0x22FFFFFF, 0x00FFFFFF, 0x10FFFFFF], [0.0, 0.5, 1.0])
    cv.drawRect(skia.Rect.MakeWH(w, h), skia.Paint(Shader=g))
    cv.restore()
