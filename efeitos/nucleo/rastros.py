"""RASTROS e BORRÃO DE VELOCIDADE: fita que segue o histórico de posições (mais fina e transparente no fim) e borrão
direcional de uma camada (linha de movimento)."""
import numpy as np
import cv2
import skia


def fita(ctx, tela, historico, cor, largura_m=0.08, modo="add", alfa=1.0):
    pts = [ctx.tela(p) for p in historico]; pts = [q for q in pts if q[3] > 0.1]
    if len(pts) < 2 or alfa <= 0:
        return
    s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); c = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    n = len(pts)
    for i in range(n - 1):
        u = (i + 1) / n; w = max(1.0, largura_m * ctx.px_por_m(pts[i][3]) * pts[i][2] * u)
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                       Color4f=skia.Color4f(*c, alfa * u ** 1.5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.4))
        if modo == "add":
            p.setBlendMode(skia.BlendMode.kPlus)
        cv.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], p)
    img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    z = float(np.mean([q[3] for q in pts]))
    if modo == "add":
        tela.imagem(None, img[..., :3], z)
    else:
        tela.imagem(img, None, z)


def borrao_direcional(rgb, direcao_px):
    """Borrão de movimento ao longo de (dx, dy) px."""
    dx, dy = direcao_px; L = max(1, int(np.hypot(dx, dy)))
    k = np.zeros((2 * L + 1, 2 * L + 1), np.float32)
    for i in range(L + 1):
        u = i / max(L, 1); k[int(round(L + dy * u)), int(round(L + dx * u))] = 1
    k /= k.sum()
    return cv2.filter2D(rgb, -1, k, borderType=cv2.BORDER_CONSTANT)
