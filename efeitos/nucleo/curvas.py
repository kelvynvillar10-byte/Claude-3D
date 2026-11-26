"""Curvas FRACTAIS (para raios e arcos): deslocamento do ponto médio em 3D entre dois contatos, com ramificações.

- As pontas ficam EXATAMENTE nos contatos (mão, objeto, chão): o raio "toca" o que precisa tocar.
- Redesenho a cada N quadros (2–3, como no plano dos poderes): semente = semente base + quadro // N.
- Desenho com o skia: halo largo e borrado na cor do efeito + núcleo fino quase branco, somados ao quadro (brilho),
  com a profundidade média da curva (o cenário mais perto a cobre).
"""
import math
import numpy as np
import skia


def fractal(p0, p1, rng, niveis=6, desvio=0.18, ramos=3, frac_ramo=0.45):
    """Retorna lista de (polilinha Nx3, espessura relativa). A principal tem espessura 1."""
    def subdividir(a, b, nivel, dv):
        pts = [np.asarray(a, float), np.asarray(b, float)]
        for _ in range(nivel):
            novo = [pts[0]]
            for i in range(len(pts) - 1):
                u, v = pts[i], pts[i + 1]; m = (u + v) / 2; d = v - u; L = np.linalg.norm(d)
                if L < 1e-6:
                    novo += [m, v]; continue
                perp = np.cross(d, rng.normal(size=3)); perp /= np.linalg.norm(perp) + 1e-9
                novo += [m + perp * rng.normal(0, dv) * L, v]
            pts = novo; dv *= 0.62
        return np.array(pts)
    principal = subdividir(p0, p1, niveis, desvio); out = [(principal, 1.0)]
    for _ in range(ramos):
        i = int(rng.integers(len(principal) // 6, max(len(principal) * 5 // 6, len(principal) // 6 + 1)))
        a = principal[i]; d = principal[min(i + 4, len(principal) - 1)] - a
        L = np.linalg.norm(np.asarray(p1) - np.asarray(p0)) * frac_ramo * rng.uniform(0.4, 1.0)
        dirn = d / (np.linalg.norm(d) + 1e-9) + rng.normal(0, 0.7, 3); dirn /= np.linalg.norm(dirn) + 1e-9
        out.append((subdividir(a, a + dirn * L, max(3, niveis - 2), desvio * 1.2), 0.45))
    return out


def desenhar(ctx, tela, curvas, cor_halo, largura_m=0.006, forca=1.0, nucleo="#f4f8ff"):
    """Desenha as curvas na tela do efeito (modo brilho). largura_m: espessura do núcleo no mundo."""
    if forca <= 0:
        return
    W, H = ctx.P.W, ctx.P.H; s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(0); zs = []
    ch = skia.Color4f(*[int(cor_halo[i:i + 2], 16) / 255 for i in (1, 3, 5)], 1.0)
    cn = skia.Color4f(*[int(nucleo[i:i + 2], 16) / 255 for i in (1, 3, 5)], 1.0)
    for pts, esp in curvas:
        tela_pts = [ctx.tela(p) for p in pts]; tela_pts = [q for q in tela_pts if q[3] > 0.1]
        if len(tela_pts) < 2:
            continue
        z = float(np.mean([q[3] for q in tela_pts])); zs.append(z); px = ctx.px_por_m(z) * tela_pts[0][2]
        path = skia.Path(); path.moveTo(tela_pts[0][0], tela_pts[0][1])
        for q in tela_pts[1:]:
            path.lineTo(q[0], q[1])
        w = max(1.0, largura_m * px * esp)
        for larg, cor, alfa, borra in ((w * 5, ch, 0.22, w * 2.2), (w * 2.2, ch, 0.6, w * 0.8), (w, cn, 1.0, 0)):
            p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=larg, StrokeCap=skia.Paint.kRound_Cap,
                           StrokeJoin=skia.Paint.kRound_Join, Color4f=skia.Color4f(cor.fR, cor.fG, cor.fB, alfa * min(1.0, forca)))
            if borra:
                p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, borra))
            p.setBlendMode(skia.BlendMode.kPlus)
            cv.drawPath(path, p)
    if not zs:
        return
    img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    tela.imagem(None, img[..., :3] * (forca if forca > 1 else 1.0), float(np.mean(zs)))   # forca ≤ 1 já está no alfa do traço
