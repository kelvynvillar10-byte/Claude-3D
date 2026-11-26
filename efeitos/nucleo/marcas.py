"""MARCAS QUE FICAM no chão (queimado, rachadura): textura procedural projetada no plano do chão em PERSPECTIVA real
(os 4 cantos no mundo → tela; homografia). Depois de criada, a marca fica até o fim da cena."""
import math
import numpy as np
import cv2
import skia

TEX = 256


def textura(tipo, semente=1):
    """RGBA pré-multiplicado (0..1), TEX×TEX: 'queimado' (mancha escura irregular) ou 'rachadura' (fendas ramificadas)."""
    rng = np.random.default_rng(semente); yy, xx = np.mgrid[0:TEX, 0:TEX].astype(np.float32) / TEX - 0.5
    r = np.sqrt(xx ** 2 + yy ** 2) * 2; ang = np.arctan2(yy, xx)
    if tipo == "queimado":
        borda = 0.75 + 0.18 * np.sin(ang * 5 + rng.uniform(0, 6)) + 0.08 * np.sin(ang * 13 + rng.uniform(0, 6))
        a = np.clip((borda - r) / 0.35, 0, 1) ** 1.3 * 0.85
        cor = np.array([0.05, 0.04, 0.035], np.float32)
        return np.dstack([cor[None, None, :] * a[..., None], a]).astype(np.float32)
    s = skia.Surface(TEX, TEX); cv = s.getCanvas(); cv.clear(0)
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, Color=skia.Color(18, 14, 12), StrokeCap=skia.Paint.kRound_Cap)
    def fenda(x, y, a, L, w, nivel):
        path = skia.Path(); path.moveTo(x, y)
        for _ in range(6):
            a += rng.uniform(-0.5, 0.5); x += L / 6 * math.cos(a); y += L / 6 * math.sin(a); path.lineTo(x, y)
        p.setStrokeWidth(w); cv.drawPath(path, p)
        if nivel > 0:
            for _ in range(2):
                fenda(x, y, a + rng.uniform(-1, 1), L * 0.55, w * 0.6, nivel - 1)
    for k in range(rng.integers(5, 8)):
        fenda(TEX / 2, TEX / 2, 2 * math.pi * k / 6 + rng.uniform(-0.3, 0.3), TEX * 0.36, 9.0, 2)
    cv.drawCircle(TEX / 2, TEX / 2, TEX * 0.07, skia.Paint(AntiAlias=True, Color=skia.Color(18, 14, 12)))   # afundamento no centro
    img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    return img


def desenhar(ctx, tela, centro_mundo, raio_m, tex, alfa=1.0):
    """Projeta a textura no chão (plano horizontal na altura do centro) e junta na tela do efeito."""
    cx, cy, cz = centro_mundo
    cantos = [(cx - raio_m, cy - raio_m, cz), (cx + raio_m, cy - raio_m, cz), (cx + raio_m, cy + raio_m, cz), (cx - raio_m, cy + raio_m, cz)]
    t = [ctx.tela(c) for c in cantos]
    if any(q[3] <= 0.1 for q in t):
        return
    src = np.float32([[0, 0], [TEX, 0], [TEX, TEX], [0, TEX]]); dst = np.float32([[q[0], q[1]] for q in t])
    Hm = cv2.getPerspectiveTransform(src, dst)
    img = cv2.warpPerspective(tex * alfa, Hm, (ctx.P.W, ctx.P.H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    tela.imagem(img, None, ctx.tela(centro_mundo)[3])
