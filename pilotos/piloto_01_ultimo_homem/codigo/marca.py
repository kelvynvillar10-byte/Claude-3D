#!/usr/bin/env python3
"""Piloto 01 — arquivos-mestre da marca (PROPOSTA) e texturas de cena.

- camiseta_modo_curioso.svg : "Modo Curioso" (ID-002/ID-003), Nunito ExtraBold em curvas, "Modo" #f2efe8 + "Curioso" #ffc21f
- cenario_MODO_CURIOSO.svg  : "MODO CURIOSO" (ID-004), Roboto Condensed ExtraBold em curvas, "MODO" branco + "CURIOSO" #ffc21f
- poster_MODO_CURIOSO.png, outdoor_MODO_CURIOSO.png : texturas do pôster do quarto e do outdoor da rua (ID-004)
- tela_celular.png : tela acesa do celular (notificação)
Uso: .venv/bin/python codigo/marca.py
"""
from pathlib import Path
import skia

P = Path(__file__).resolve().parents[1]
RAIZ = P.parents[1]
FON = RAIZ / "assets" / "fontes"
OUT = P / "recursos" / "marca"; OUT.mkdir(parents=True, exist_ok=True)
NUNITO = skia.Typeface.MakeFromFile(str(FON / "Nunito-ExtraBold.ttf"))
ROBOTO = skia.Typeface.MakeFromFile(str(FON / "RobotoCondensed-ExtraBold.ttf"))
COR = {"tecido_branco": 0xFFF2EFE8, "amarelo": 0xFFFFC21F, "marinho": 0xFF1F2A44, "branco": 0xFFFFFFFF}


def texto_curvas(tf, tam, txt, x=0.0, y=0.0):
    """Converte texto em skia.Path (curvas), glifo a glifo."""
    f = skia.Font(tf, tam); f.setSubpixel(True)
    glifos = f.textToGlyphs(txt); larg = f.getWidths(glifos)
    caminho = skia.Path(); cx = x
    for g, w in zip(glifos, larg):
        gp = f.getPath(g)
        if gp is not None:
            caminho.addPath(gp, cx, y)
        cx += w
    return caminho, cx - x


def svg(arquivo, w, h, desenho):
    stream = skia.FILEWStream(str(arquivo))
    c = skia.SVGCanvas.Make(skia.Rect.MakeWH(w, h), stream)
    desenho(c); del c; stream.flush()


def marca_duas_cores(c, tf, tam, p1, p2, cor1, cor2, x, y, esp=0.28):
    a, w1 = texto_curvas(tf, tam, p1, x, y)
    b, w2 = texto_curvas(tf, tam, p2, x + w1 + tam * esp, y)
    c.drawPath(a, skia.Paint(AntiAlias=True, Color=cor1))
    c.drawPath(b, skia.Paint(AntiAlias=True, Color=cor2))
    return w1 + tam * esp + w2


# --- arquivos-mestre vetoriais (texto em curvas)
_, wm = texto_curvas(NUNITO, 100, "Modo"); _, wc = texto_curvas(NUNITO, 100, "Curioso")
LW = wm + 28 + wc + 20
svg(OUT / "camiseta_modo_curioso.svg", LW, 130,
    lambda c: marca_duas_cores(c, NUNITO, 100, "Modo", "Curioso", COR["tecido_branco"], COR["amarelo"], 10, 100))
_, wm2 = texto_curvas(ROBOTO, 100, "MODO"); _, wc2 = texto_curvas(ROBOTO, 100, "CURIOSO")
svg(OUT / "cenario_MODO_CURIOSO.svg", wm2 + 28 + wc2 + 20, 125,
    lambda c: marca_duas_cores(c, ROBOTO, 100, "MODO", "CURIOSO", COR["branco"], COR["amarelo"], 10, 100))


def png(arquivo, w, h, desenho):
    s = skia.Surface(w, h); c = s.getCanvas(); desenho(c, w, h)
    s.makeImageSnapshot().save(str(arquivo), skia.kPNG)


def poster(c, w, h):
    c.clear(COR["marinho"])
    # moldura e ícone de lupa (desenho próprio, sem semelhança com logotipos de terceiros)
    p = skia.Paint(AntiAlias=True, Color=0x33FFFFFF, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
    c.drawRect(skia.Rect.MakeXYWH(24, 24, w - 48, h - 48), p)
    cx, cy = w / 2 - 30, h * 0.31
    c.drawCircle(cx, cy, 120, skia.Paint(AntiAlias=True, Color=COR["amarelo"], Style=skia.Paint.kStroke_Style, StrokeWidth=34))
    c.drawCircle(cx, cy, 103, skia.Paint(AntiAlias=True, Color=0x22FFFFFF))
    cabo = skia.Paint(AntiAlias=True, Color=COR["amarelo"], StrokeWidth=50, StrokeCap=skia.Paint.kRound_Cap)
    c.drawLine(cx + 92, cy + 92, cx + 190, cy + 190, cabo)
    q, wq = texto_curvas(ROBOTO, 150, "?")
    c.save(); c.translate(cx - wq / 2, cy + 52); c.drawPath(q, skia.Paint(AntiAlias=True, Color=COR["branco"])); c.restore()
    a, wa = texto_curvas(ROBOTO, 170, "MODO"); b, wb = texto_curvas(ROBOTO, 170, "CURIOSO")
    c.save(); c.translate((w - wa) / 2, h * 0.70); c.drawPath(a, skia.Paint(AntiAlias=True, Color=COR["branco"])); c.restore()
    c.save(); c.translate((w - wb) / 2, h * 0.87); c.drawPath(b, skia.Paint(AntiAlias=True, Color=COR["amarelo"])); c.restore()


def outdoor(c, w, h):
    c.clear(COR["marinho"])
    tam = 300
    larg = marca_duas_cores(skia.Canvas(skia.Bitmap()), ROBOTO, tam, "MODO", "CURIOSO", 0, 0, 0, 0)
    marca_duas_cores(c, ROBOTO, tam, "MODO", "CURIOSO", COR["branco"], COR["amarelo"], (w - larg) / 2, h * 0.62)
    e, we = texto_curvas(ROBOTO, 120, "E SE…?")
    c.save(); c.translate((w - we) / 2, h * 0.88); c.drawPath(e, skia.Paint(AntiAlias=True, Color=0xCCFFFFFF)); c.restore()


def tela(c, w, h):
    # tela de bloqueio acesa com uma notificação (desenho próprio, sem marcas de terceiros)
    grad = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, h)], [0xFF2B3A67, 0xFF7A4E7E])
    c.drawPaint(skia.Paint(Shader=grad))
    hora, wh = texto_curvas(NUNITO, 230, "07:42")
    c.save(); c.translate((w - wh) / 2, 420); c.drawPath(hora, skia.Paint(AntiAlias=True, Color=0xF2FFFFFF)); c.restore()
    d, wd = texto_curvas(NUNITO, 64, "quarta-feira")
    c.save(); c.translate((w - wd) / 2, 520); c.drawPath(d, skia.Paint(AntiAlias=True, Color=0xCCFFFFFF)); c.restore()
    card = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(60, 760, w - 120, 300), 46, 46)
    c.drawRRect(card, skia.Paint(AntiAlias=True, Color=0xE6F4F2EE))
    c.drawCircle(150, 860, 46, skia.Paint(AntiAlias=True, Color=0xFF3FB36B))
    t1, _ = texto_curvas(NUNITO, 60, "1 nova mensagem"); t2, _ = texto_curvas(NUNITO, 50, "Número desconhecido")
    t3, _ = texto_curvas(NUNITO, 50, "agora")
    for pth, x, y, cor in ((t1, 230, 860, 0xFF1F2A44), (t2, 230, 940, 0xFF5A6070), (t3, w - 230, 860, 0xFF8A90A0)):
        c.save(); c.translate(x, y); c.drawPath(pth, skia.Paint(AntiAlias=True, Color=cor)); c.restore()


png(OUT / "poster_MODO_CURIOSO.png", 700, 1000, poster)
png(OUT / "outdoor_MODO_CURIOSO.png", 2250, 1000, outdoor)
png(P / "recursos" / "tela_celular.png", 1080, 2340, tela)
print("ok:", sorted(x.name for x in OUT.iterdir()), "+ tela_celular.png")
