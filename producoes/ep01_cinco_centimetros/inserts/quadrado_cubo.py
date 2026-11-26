#!/usr/bin/env python3
"""Insert científico do EP01 — lei do quadrado-cubo (encolher 28×: peso ÷21.952, força ÷784, força/peso ×28).

Padrão do canal para inserts: fundo azul-marinho com bokeh e partículas; rótulos grandes (Nunito ExtraBold), número em
amarelo #ffc21f; personagem "fantasma" translúcido azul para comparar (Heitor de 1,40 m) ao lado do Heitor de 5 cm.
quadro(t) → imagem RGB 1080×1920, t de 0 a 1:
  0,00–0,30  o fantasma (1,40 m) encolhe até o Heitor de 5 cm (÷28)
  0,30–0,65  barra do PESO cai ÷21.952; barra da FORÇA cai ÷784 (barras em ESCALA LOGARÍTMICA, avisada na tela: em escala
            linear as duas sumiriam e não daria para ver que o peso cai muito mais que a força)
  0,65–1,00  destaque: "×28 MAIS FORTE em relação ao próprio peso"
Contas (lei do quadrado-cubo): 1,40/0,05 = 28; 28³ = 21.952; 28² = 784; 21.952/784 = 28.
"""
import math, sys
from pathlib import Path
import numpy as np, skia

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "rig_v2" / "codigo"))
import heitor_v2 as HV                                                     # noqa: E402

W, H = 1080, 1920
FONTE = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "Nunito-ExtraBold.ttf"))
AMARELO, BRANCO, MARINHO = (255, 194, 31), (255, 255, 255), (16, 24, 52)


def _c(rgb, a=255):
    return skia.ColorSetARGB(a, *rgb)


def _ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def _texto(cv, txt, x, y, tam, cor=BRANCO, alinhar="centro", a=255):
    f = skia.Font(FONTE, tam); w = f.measureText(txt)
    x0 = x - w / 2 if alinhar == "centro" else x
    contorno = skia.Paint(AntiAlias=True, Color=_c((26, 17, 12), a), Style=skia.Paint.kStroke_Style, StrokeWidth=tam * 0.12, StrokeJoin=skia.Paint.kRound_Join)
    cv.drawString(txt, x0, y, f, contorno); cv.drawString(txt, x0, y, f, skia.Paint(AntiAlias=True, Color=_c(cor, a)))


def _fundo(cv, t):
    cv.clear(_c(MARINHO))
    g = skia.GradientShader.MakeRadial((W / 2, H * 0.42), H * 0.7, [_c((40, 58, 120)), _c(MARINHO)])
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g))
    rng = np.random.default_rng(3)
    for _ in range(26):                                                  # bokeh
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 90)
        cv.drawCircle(x + 30 * math.sin(t * 2 + x), y - 40 * t, r, skia.Paint(AntiAlias=True, Color=_c((120, 160, 255), int(rng.uniform(10, 28))),
                                                                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.4)))
    for _ in range(80):                                                  # partículas
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        cv.drawCircle(x, (y - 120 * t) % H, rng.uniform(1.5, 3.5), skia.Paint(AntiAlias=True, Color=_c((210, 225, 255), int(rng.uniform(60, 160)))))


def _heitor_fantasma(alt):
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.ColorTRANSPARENT)
    HV.desenhar(c, W * 0.5, H * 0.6, alt, vista="frente", direcao=1, pose=None, rosto="surpresa")
    a = np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).astype(np.float32) / 255.0
    lum = (a[..., :3] @ [0.3, 0.59, 0.11])[..., None]
    azul = np.clip(0.25 + lum * np.array([0.45, 0.75, 1.0]), 0, 1)
    out = np.dstack([azul, a[..., 3:] * 0.45])
    return skia.Image.fromarray((out * 255).astype(np.uint8), colorType=skia.kRGBA_8888_ColorType)


def _barra(cv, x, y, w, h, frac, cor, rot, num, a=255):
    cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), h / 2, h / 2, skia.Paint(AntiAlias=True, Color=_c((255, 255, 255), 40)))
    if frac > 0:
        cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, max(h, w * frac), h), h / 2, h / 2, skia.Paint(AntiAlias=True, Color=_c(cor, a)))
    _texto(cv, rot, x, y - 22, 50, BRANCO, "esq", a)
    if num:
        f = skia.Font(FONTE, 64); _texto(cv, num, x + w - f.measureText(num), y - 18, 64, AMARELO, "esq", a)


def _log(fator, divisor):
    """Comprimento da barra em escala log: 1 → 100 %; 1/divisor → 1 − log(divisor)/log(21.952)."""
    return 1 - math.log(1 + (divisor - 1) * fator) / math.log(21952)


def quadro(t):
    s = skia.Surface(W, H); cv = s.getCanvas(); _fundo(cv, t)
    chao = H * 0.6
    cv.drawLine(80, chao, W - 80, chao, skia.Paint(AntiAlias=True, Color=_c((150, 180, 255), 90), StrokeWidth=3))
    # 1) encolher 28×
    e = _ease(t / 0.3); alt_cheia = 820; alt = alt_cheia * (1 - e) + (alt_cheia / 28) * e
    cv.drawImage(_heitor_fantasma(alt_cheia), 0, 0, skia.SamplingOptions(), skia.Paint(Color=_c((255, 255, 255), int(255 * (0.35 + 0.65 * (1 - e))))))
    HV.desenhar(cv, W * 0.5 + (W * 0.18) * e, chao, max(alt, alt_cheia / 28), vista="frente", direcao=1, pose=None, rosto="surpresa")
    _texto(cv, "1,40 m", W * 0.5, chao - alt_cheia - 40, 64, BRANCO, a=int(255 * max(0.0, 1 - 2.5 * e)))
    if e > 0.5:
        a = int(255 * min(1, (e - 0.5) * 2))
        _texto(cv, "÷ 28", W * 0.5, H * 0.17, 150, AMARELO, a=a)
        # lupa: o Heitor de 5 cm ampliado num círculo, ligado por uma linha ao lugar dele
        px, lx, ly, lr = W * 0.68, W * 0.76, chao - 330, 170
        cv.drawLine(px + 8, chao - 30, lx - lr * 0.6, ly + lr * 0.75, skia.Paint(AntiAlias=True, Color=_c(BRANCO, a), StrokeWidth=4))
        cv.save(); cl = skia.Path(); cl.addCircle(lx, ly, lr); cv.clipPath(cl, doAntiAlias=True)
        cv.drawCircle(lx, ly, lr, skia.Paint(AntiAlias=True, Color=_c((28, 40, 86), a)))
        HV.desenhar(cv, lx, ly + lr * 0.85, lr * 1.5, vista="frente", direcao=1, pose=None, rosto="surpresa")
        cv.restore()
        cv.drawCircle(lx, ly, lr, skia.Paint(AntiAlias=True, Color=_c(BRANCO, a), Style=skia.Paint.kStroke_Style, StrokeWidth=10))
        _texto(cv, "5 cm", lx, ly + lr + 70, 64, AMARELO, a=a)
    # 2) barras peso × força
    b = _ease((t - 0.3) / 0.35)
    if t > 0.28:
        a = int(255 * min(1, (t - 0.28) / 0.05))
        _barra(cv, 120, H * 0.70, 840, 54, _log(b, 21952), (230, 90, 70), "PESO", "÷ 21.952" if b > 0.6 else "", a)
        _barra(cv, 120, H * 0.80, 840, 54, _log(b, 784), (90, 200, 120), "FORÇA", "÷ 784" if b > 0.6 else "", a)
        _texto(cv, "barras em escala logarítmica", W / 2, H * 0.865, 30, (190, 205, 240), a=a)
    # 3) resultado
    r = _ease((t - 0.65) / 0.2)
    if r > 0:
        a = int(255 * r)
        _texto(cv, "× 28", W / 2, H * 0.93, 130, AMARELO, a=a)
        _texto(cv, "MAIS FORTE EM RELAÇÃO AO PRÓPRIO PESO", W / 2, H * 0.97, 40, BRANCO, a=a)
    return np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))[..., :3]


if __name__ == "__main__":
    import cv2
    out = Path(__file__).resolve().parent
    fr = [quadro(t) for t in (0.0, 0.2, 0.45, 0.9)]
    folha = np.concatenate([cv2.resize(f, (540, 960)) for f in fr], axis=1)
    cv2.imwrite(str(out / "folha_quadrado_cubo.png"), cv2.cvtColor(folha, cv2.COLOR_RGB2BGR)); print("ok")
