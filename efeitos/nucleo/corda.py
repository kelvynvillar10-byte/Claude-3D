"""CORDA com física (Verlet + restrições de comprimento), para teias e cabos: ponta A presa (prédio, poste), ponta B
presa a um ponto que se move (mão do personagem) ou solta (pêndulo). Determinística (passo fixo)."""
import numpy as np
import skia

G = np.array([0.0, 0.0, -9.81])


class Corda:
    def __init__(self, a, b, n=24, comprimento=None, amortecimento=0.995, iteracoes=30, fps=30, subpassos=4):
        a, b = np.asarray(a, float), np.asarray(b, float)
        self.L = comprimento or np.linalg.norm(b - a); self.n = n; self.seg = self.L / (n - 1)
        self.p = np.linspace(a, b, n); self.ant = self.p.copy(); self.amort = amortecimento; self.it = iteracoes
        self.dt = 1.0 / fps / subpassos; self.sub = subpassos; self.fixo_a = a.copy(); self.fixo_b = b.copy(); self.solta_b = False

    def passo(self, a=None, b=None):
        if a is not None:
            self.fixo_a = np.asarray(a, float)
        if b is not None:
            self.fixo_b = np.asarray(b, float)
        for _ in range(self.sub):
            v = (self.p - self.ant) * self.amort; self.ant = self.p.copy(); self.p = self.p + v + G * self.dt * self.dt
            for _ in range(self.it):
                self.p[0] = self.fixo_a
                if not self.solta_b:
                    self.p[-1] = self.fixo_b
                d = self.p[1:] - self.p[:-1]; L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
                corr = (L - self.seg) / L * d * 0.5
                self.p[:-1] += corr; self.p[1:] -= corr
            self.p[0] = self.fixo_a
            if not self.solta_b:
                self.p[-1] = self.fixo_b

    def esticamento_max(self):
        L = np.linalg.norm(self.p[1:] - self.p[:-1], axis=1)
        return float(np.max(np.abs(L - self.seg)) / self.seg)

    def desenhar(self, ctx, tela, cor="#f2efe8", espessura_m=0.012, alfa=1.0):
        pts = [ctx.tela(q) for q in self.p]; pts = [q for q in pts if q[3] > 0.1]
        if len(pts) < 2 or alfa <= 0:
            return
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0)
        z = float(np.mean([q[3] for q in pts])); w = max(1.0, espessura_m * ctx.px_por_m(z) * pts[0][2])
        path = skia.Path(); path.moveTo(pts[0][0], pts[0][1])
        for q in pts[1:]:
            path.lineTo(q[0], q[1])
        c = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        sombra = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w * 1.8, Color4f=skia.Color4f(0.1, 0.08, 0.12, 0.35 * alfa),
                            StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
        cv.drawPath(path, sombra)
        cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, Color4f=skia.Color4f(*c, alfa),
                                     StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join))
        img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
        tela.imagem(img, None, z)
