"""QUADRO DE IMPACTO (padrão do skill): silhueta clara do personagem sobre linhas radiais + estilhaços brancos sobre
azul-marinho, por 1–2 quadros. Gera a imagem inteira (espaço de exibição, 0..1) na resolução da placa."""
import math
import numpy as np
import skia


def quadro_impacto(P, centro_xy, alfa_personagem, semente=1, fundo="#14204a", linhas="#2f4ea0"):
    W, H = P.W, P.H; rng = np.random.default_rng(semente)
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color(*[int(fundo[i:i + 2], 16) for i in (1, 3, 5)]))
    cx, cy = centro_xy; R = math.hypot(W, H)
    cl = skia.Paint(AntiAlias=True, Color=skia.Color(*[int(linhas[i:i + 2], 16) for i in (1, 3, 5)]))
    for k in range(48):     # linhas radiais (cunhas finas)
        a = 2 * math.pi * k / 48 + rng.uniform(-0.03, 0.03); w = rng.uniform(0.006, 0.02)
        path = skia.Path(); path.moveTo(cx, cy)
        path.lineTo(cx + R * math.cos(a - w), cy + R * math.sin(a - w)); path.lineTo(cx + R * math.cos(a + w), cy + R * math.sin(a + w)); path.close()
        cv.drawPath(path, cl)
    branco = skia.Paint(AntiAlias=True, Color=skia.Color(246, 244, 236))
    for k in range(26):     # estilhaços
        a = rng.uniform(0, 2 * math.pi); d = rng.uniform(0.05, 0.42) * min(W, H); tam = rng.uniform(0.008, 0.03) * min(W, H)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a); path = skia.Path()
        for j in range(3):
            b = a + j * 2.1 + rng.uniform(-0.4, 0.4); path.lineTo(x + tam * math.cos(b), y + tam * math.sin(b)) if j else path.moveTo(x + tam * math.cos(b), y + tam * math.sin(b))
        path.close(); cv.drawPath(path, branco)
    img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.float32) / 255.0
    if alfa_personagem is not None:
        a = np.clip(alfa_personagem * 1.2, 0, 1)[..., None]
        img = img * (1 - a) + np.array([0.965, 0.957, 0.925], np.float32) * a       # silhueta clara
    return img
