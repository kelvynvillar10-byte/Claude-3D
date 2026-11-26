"""PODER: TERRA (E8). Usa só o núcleo; não mexe no rig.

Família de cores: terra/ocre e poeira bege (contrasta com o azul da camiseta). O chão vem do Blender: tudo é posto no
plano da calçada em perspectiva real, e os pedaços de chão são RECORTADOS DO PRÓPRIO FUNDO (a imagem do cenário),
deixando um buraco escuro no lugar.
Fases:
  início      tremor leve; poeira fina nos pés
  ativação    rachadura corre dos pés até o alvo (crescendo); onda de terra levanta a calçada (moderado/extremo)
  uso         pedaços do chão se soltam, sobem e flutuam (com espessura, sombra de lado e buraco); pedrinhas
  impacto     pedaços disparam; pilar de rocha sobe com assentamento (extremo); cratera; detritos; tremida; quadro de impacto
  dissipação  pedaços caem e somem na poeira; a rachadura, os buracos, a cratera e o pilar ficam
  encerramento poeira assentando
Intensidades: discreto (rachadura + pedrinhas + tremor leve), moderado (+ pedaços recortados + onda), extremo (+ pilar,
cratera, detritos, tremida forte, quadro de impacto).
Parâmetros extras (kw): origem (pés, mundo), alvo (chão, mundo), fundo (imagem do cenário sem efeitos, na resolução da
placa, 0..1 — fonte da textura dos pedaços), sol (direção para o sol/lua, do manifesto da placa).
"""
import math
import numpy as np
import cv2
import skia
from efeitos.nucleo.base import Efeito, efeito
from efeitos.nucleo import particulas as PT, marcas as MK, tremida as TR, impacto as IM

TERRA = np.array([0.45, 0.34, 0.23], np.float32); ROCHA = np.array([0.50, 0.42, 0.33], np.float32); POEIRA = (0.80, 0.71, 0.56)


def _girar(v, ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return v @ (Rz @ Ry @ Rx).T


def _tracos(tela, linhas, z, W, H):
    """Linhas (skia) numa janela do tamanho delas: linhas = [(pts [(x, y)], largura px, (r, g, b), alfa)]."""
    xs = [p[0] for pts, *_ in linhas for p in pts]; ys = [p[1] for pts, *_ in linhas for p in pts]
    if not xs:
        return
    m = max(w for _, w, _, _ in linhas) + 3
    x0, y0 = max(0, int(min(xs) - m)), max(0, int(min(ys) - m)); x1, y1 = min(W, int(max(xs) + m)), min(H, int(max(ys) + m))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    s = skia.Surface(x1 - x0, y1 - y0); cv = s.getCanvas(); cv.clear(0)
    for pts, w, cor, a in linhas:
        if len(pts) < 2:
            continue
        path = skia.Path(); path.moveTo(pts[0][0] - x0, pts[0][1] - y0)
        for q in pts[1:]:
            path.lineTo(q[0] - x0, q[1] - y0)
        cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(0.8, w), StrokeCap=skia.Paint.kRound_Cap,
                                     StrokeJoin=skia.Paint.kRound_Join, Color4f=skia.Color4f(*[float(c) for c in cor], float(a))))
    img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    tela.recorte(img, x0, y0, z)


@efeito("terra")
class Terra(Efeito):
    familia = "#8a5a3a"; prioridade = 3; deixa_marca = True

    def __init__(self, params=None, inicio=0.0, **kw):
        super().__init__(params, inicio, **kw)
        rng = np.random.default_rng(self.p.semente); o = np.asarray(kw["origem"], float); a = np.asarray(kw["alvo"], float)
        self.o, self.a, self.zc = o, a, float(a[2]); self.rng = rng
        self.rach = self._rachaduras(rng)
        n, R, rr = {"discreto": (0, 0, (0, 0)), "moderado": (6, 1.1, (0.22, 0.4)), "extremo": (8, 1.5, (0.24, 0.45))}[self.p.intensidade]
        self.pedacos = []; self.n_alvo = n
        for i in range(3 * n):      # candidatos (o triplo): depois só ficam os de chão visível; polígono irregular, sem sobrepor
            for _ in range(30):
                ang = rng.uniform(0, 2 * math.pi); d = rng.uniform(0.35, R); c = a + np.array([d * math.cos(ang), d * math.sin(ang), 0.0])
                r = rng.uniform(*rr)
                fx = kw.get("faixa_x", (-1e9, 1e9))                  # só dentro da calçada (nem rua, nem fachada)
                if (all(np.linalg.norm(c[:2] - q["c"][:2]) > r + q["r"] + 0.08 for q in self.pedacos) and np.linalg.norm(c[:2] - o[:2]) > 0.6
                        and fx[0] + r * 1.1 <= c[0] <= fx[1] - r * 1.1):
                    break
            k = int(rng.integers(6, 9)); angs = 2 * math.pi * np.arange(k) / k + rng.uniform(-0.3, 0.3, k) * (2 * math.pi / k)   # espaçados: polígono sem lascas
            loc = np.stack([np.cos(angs) * r * rng.uniform(0.75, 1.1, k), np.sin(angs) * r * rng.uniform(0.75, 1.1, k), np.zeros(k)], 1)
            # inclinação: a face de cima vira um pouco para a câmera (mostra o chão recortado, não só o lado)
            cam = np.asarray(kw.get("camera_pos", (-5.0, 0.0, 1.15)), float); d_cam = cam[:2] - c[:2]; d_cam /= np.linalg.norm(d_cam) + 1e-9
            incl = rng.uniform(0.45, 0.75)
            giro = np.array([-d_cam[1] * incl, d_cam[0] * incl, 0.0]) + rng.uniform(-0.25, 0.25, 3) * [1, 1, 2]
            self.pedacos.append({"c": c, "r": r, "loc": loc, "esp": rng.uniform(0.12, 0.2), "h": rng.uniform(0.5, 1.3),
                                 "giro": giro, "fase": rng.uniform(0, 6.28),
                                 "v": np.array([math.cos(ang) * rng.uniform(1.0, 2.5), math.sin(ang) * rng.uniform(1.0, 2.5), rng.uniform(3.0, 5.0)])})
        self._k = None; self.tex_cratera = MK.textura("cratera", self.p.semente)

    # ---------------- rachaduras no plano do chão (crescem com o tempo)
    def _rachaduras(self, rng):
        o, a = self.o, self.a; d = a[:2] - o[:2]; L = float(np.linalg.norm(d)); u = d / max(L, 1e-6); perp = np.array([-u[1], u[0]])
        n = 40; pts = []; lat = 0.0
        for i in range(n + 1):
            t = i / n; lat += rng.normal(0, 0.045); lat *= 0.92
            pts.append(np.concatenate([o[:2] + u * (0.25 + t * (L + 0.6)) + perp * lat, [self.zc]]))
        linhas = [(np.array(pts), 0.0, 1.0)]       # (pontos, início no crescimento 0..1, espessura relativa)
        for _ in range({"discreto": 5, "moderado": 8, "extremo": 12}[self.p.intensidade]):
            i = int(rng.integers(6, n - 4)); b = pts[i]; ang = math.atan2(u[1], u[0]) + rng.choice([-1, 1]) * rng.uniform(0.5, 1.2)
            q = [b]; Lb = rng.uniform(0.3, 0.9)
            for j in range(1, 9):
                ang += rng.normal(0, 0.25); q.append(q[-1] + np.array([math.cos(ang), math.sin(ang), 0]) * Lb / 8)
            linhas.append((np.array(q), i / n, 0.55))
        return linhas

    def _crescimento(self, t):
        fase, x = self.fases.em(t)
        ordem = ["inicio", "ativacao", "uso", "impacto", "dissipacao", "encerramento"]
        if fase is None:
            return 1.0 if t > 0 else 0.0
        i = ordem.index(fase)
        return 0.0 if i == 0 else (x ** 0.8 if i == 1 else 1.0)

    # ---------------- simulação de poeira, pedrinhas e detritos
    def _validar_pedacos(self, ctx):
        """Só fica o pedaço cujo chão está VISÍVEL na imagem (nada na frente): a textura recortada tem de ser chão."""
        prof = self.kw.get("prof")
        if getattr(self, "_validado", False):
            return
        if prof is None:
            self.pedacos = self.pedacos[:self.n_alvo]; self.descartados = 0; self._validado = True; return
        bons = []
        for q in self.pedacos:
            ok = True
            for p in list(q["loc"]) + [np.zeros(3)]:
                u, v, z = ctx.placa(q["c"] + p); iu, iv = int(round(u)), int(round(v))
                if not (0 <= iv < prof.shape[0] and 0 <= iu < prof.shape[1]) or abs(float(prof[iv, iu]) - z) > 0.3:
                    ok = False; break
            if ok:
                bons.append(q)
            if len(bons) >= self.n_alvo:
                break
        self.descartados = len(self.pedacos) - len(bons); self.pedacos = bons; self._validado = True

    def preparar(self, ctx):
        self._validar_pedacos(ctx)
        k = int(round(self.tl(ctx) * ctx.fps))
        if self._k is None or k < self._k:
            self.poeira = PT.Sistema(self.p.semente + 1, gravidade=0.04, vento=(0.25, 0, 0.12), arrasto=1.3, turbulencia=0.35, chao_z=self.zc, fps=ctx.fps)
            self.pedras = PT.Sistema(self.p.semente + 2, gravidade=1.0, arrasto=0.2, chao_z=self.zc, restituicao=0.25, atrito=0.5, fps=ctx.fps)
            self._k = 0
        while self._k < k:
            self._k += 1; self._passo(ctx, self._k / ctx.fps)
        self._tom(ctx)

    def _passo(self, ctx, t):
        fase, x = self.fases.em(t); f = self.fases.envelope(t) * self.p.fator * self.ganho
        if fase in ("inicio", "ativacao"):
            self.poeira.emitir(int(1 + 2 * f), self.o + [0, 0.3, 0], (0, 0, 0.3), dispersao=0.4, vida=(1.0, 1.8), tam=(0.05, 0.1), cor=POEIRA, raio_origem=0.2)
        if fase == "ativacao" and self.p.intensidade != "discreto":          # poeira atrás da onda de terra
            p = self._onda_pos(t)
            if p is not None:
                self.poeira.emitir(int(3 * f), p, (0, 0, 0.5), dispersao=0.5, vida=(1.0, 2.0), tam=(0.07, 0.13), cor=POEIRA, raio_origem=0.15)
        if fase == "uso":
            if self.p.intensidade == "discreto" or self.rng is None:
                self.pedras.emitir(1 if (int(t * 30) % 3 == 0) else 0, self.a + np.r_[np.random.default_rng(int(t * 1000)).normal(0, 0.4, 2), 0], (0, 0, 2.4),
                                   dispersao=0.3, vida=(0.9, 1.3), tam=(0.02, 0.05), cor=(0.42, 0.33, 0.24))
        if fase == "impacto" and x < 0.12 and self.p.intensidade != "discreto":
            self.poeira.emitir(int(40 * f), self.a, (0, 0, 0.8), dispersao=1.8, vida=(1.4, 2.6), tam=(0.1, 0.22), cor=POEIRA, raio_origem=0.4)
            self.pedras.emitir(int((40 if self.p.intensidade == "extremo" else 16) * f), self.a + [0, 0, 0.1], (0, 0, 3.0), dispersao=2.2,
                               vida=(1.0, 2.0), tam=(0.025, 0.06), cor=(0.40, 0.31, 0.22))
        self.poeira.passo(); self.pedras.passo()

    def _tom(self, ctx):
        """Brilho do chão neste horário (amostrado no fundo, perto do alvo): pedra, terra e pilar acompanham a luz da cena."""
        if getattr(self, "_tom_v", None) is not None:
            return
        fundo = self.kw.get("fundo"); self._tom_v = 1.0
        if fundo is not None:
            u, v, z = ctx.placa(self.a); r = 40
            jan = fundo[max(0, int(v) - r):int(v) + r, max(0, int(u) - r):int(u) + r]
            if jan.size:
                self._tom_v = float(np.clip(jan.mean() / 0.55, 0.45, 1.3))

    def _onda_pos(self, t):
        fase, x = self.fases.em(t)
        if fase != "ativacao":
            return None
        return self.o + (self.a - self.o) * (0.15 + 0.85 * x)

    # ---------------- pedaços
    def _estado_pedaco(self, q, t):
        """Posição (centro), rotação, alfa do pedaço no tempo t; None se ainda não se soltou."""
        t_uso = self.fases.inicio_de("uso"); t_imp = self.fases.inicio_de("impacto"); t_dis = self.fases.inicio_de("dissipacao"); T = self.fases.duracao
        if t < t_uso:
            return None
        if t < t_imp:
            x = (t - t_uso) / max(t_imp - t_uso, 1e-6); s = 1 - (1 - min(1.0, x * 1.4)) ** 3
            h = q["h"] * s + 0.05 * math.sin(2 * math.pi * t / 1.6 + q["fase"]) * s
            return q["c"] + [0, 0, h], q["giro"] * s, 1.0
        dt = t - t_imp; c0 = q["c"] + [0, 0, q["h"]]
        c = c0 + q["v"] * dt + np.array([0, 0, -0.5 * 9.81 * dt * dt])
        c[2] = max(c[2], self.zc + 0.05)
        alfa = 1.0 if t < t_dis else max(0.0, 1 - (t - t_dis) / max(T - t_dis, 1e-6) * 1.6)
        return c, q["giro"] + np.array([2.0, 1.5, 0.8]) * dt, alfa

    def _desenhar_pedaco(self, ctx, tela, q, c, giro, alfa, cam_pos):
        topo = c + _girar(q["loc"], *giro); nrm = _girar(np.array([[0, 0, 1.0]]), *giro)[0]
        base = topo - nrm * q["esp"]; sol = np.asarray(ctx.P.m.get("sol_dir", (0.3, -0.5, 0.8)), float); sol /= np.linalg.norm(sol)
        tt = [ctx.tela(p) for p in topo]; tb = [ctx.tela(p) for p in base]
        if any(p[3] <= 0.1 for p in tt + tb):
            return None
        z = float(np.mean([p[3] for p in tt])); tom = self._tom_v; polys = []
        k = len(topo)
        for i in range(k):            # lados visíveis, sombreados pelo sol do horário
            j = (i + 1) % k; mid = (topo[i] + topo[j] + base[i] + base[j]) / 4
            fn = np.cross(topo[j] - topo[i], base[i] - topo[i]); fn /= np.linalg.norm(fn) + 1e-9
            if fn @ (mid - c) < 0:
                fn = -fn
            if fn @ (cam_pos - mid) <= 0:
                continue
            luz = 0.4 + 0.6 * max(0.0, float(fn @ sol))
            polys.append(([tt[i][:2], tt[j][:2], tb[j][:2], tb[i][:2]], np.clip(TERRA * luz * tom, 0, 1), alfa))
        if polys:
            tela.poligonos(polys, z)
        fundo = self.kw.get("fundo")        # face de cima: textura RECORTADA do próprio fundo
        if fundo is not None:
            src = np.float32([ctx.placa(self.a * 0 + q["c"] + p)[:2] for p in q["loc"]]); dst = np.float32([p[:2] for p in tt])
            Hm, _ = cv2.findHomography(src, dst, 0)
            if Hm is not None:
                x0, y0 = max(0, int(dst[:, 0].min()) - 2), max(0, int(dst[:, 1].min()) - 2)
                x1, y1 = min(ctx.P.W, int(dst[:, 0].max()) + 3), min(ctx.P.H, int(dst[:, 1].max()) + 3)
                if x1 - x0 > 1 and y1 - y0 > 1:
                    T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], float) @ Hm
                    img = cv2.warpPerspective(fundo, T, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
                    m = np.zeros((y1 - y0, x1 - x0), np.float32); cv2.fillPoly(m, [np.int32(np.round(dst - [x0, y0]))], 1.0)
                    m = cv2.GaussianBlur(m, (3, 3), 0) * alfa
                    luz = 0.75 + 0.25 * max(0.0, float(nrm @ sol)) / max(1e-3, sol[2])          # face inclinada muda de luz
                    tela.recorte(np.dstack([img * min(luz, 1.15) * m[..., None], m]).astype(np.float32), x0, y0, z - 0.01)
        return z

    def _buraco(self, ctx, tela, q):
        tt = [ctx.tela(q["c"] + p) for p in q["loc"]]
        if any(p[3] <= 0.1 for p in tt):
            return
        fundo_buraco = [ctx.tela(q["c"] + p * 0.8 + [0, 0, -0.12]) for p in q["loc"]]
        tom = self._tom_v; z = float(np.mean([p[3] for p in tt]))
        tela.poligonos([([p[:2] for p in tt], np.clip(TERRA * 0.55 * tom, 0, 1), 0.97),
                        ([p[:2] for p in fundo_buraco], np.clip(np.array([0.07, 0.055, 0.04]) * tom, 0, 1), 0.97)], z)

    # ---------------- pilar (extremo)
    def _pilar(self, ctx, tela, t, cam_pos):
        t_imp = self.fases.inicio_de("impacto")
        if self.p.intensidade != "extremo" or t < t_imp:
            return
        x = min(1.0, (t - t_imp) / 0.45)
        c1, c3 = 1.70158, 2.70158; s = 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2         # sobe com assentamento
        Hp = 2.4 * self.p.escala * s; rng = np.random.default_rng(self.p.semente + 9); n = 7
        angs = 2 * math.pi * np.arange(n) / n + rng.uniform(-0.3, 0.3, n) * (2 * math.pi / n); rb = 0.48 * rng.uniform(0.85, 1.1, n) * self.p.escala; rt = rb * 0.8
        ht = Hp * rng.uniform(0.9, 1.05, n)
        base = [self.a + [rb[i] * math.cos(angs[i]), rb[i] * math.sin(angs[i]), 0] for i in range(n)]
        topo = [self.a + [rt[i] * math.cos(angs[i]), rt[i] * math.sin(angs[i]), ht[i]] for i in range(n)]
        sol = np.asarray(ctx.P.m.get("sol_dir", (0.3, -0.5, 0.8)), float); sol /= np.linalg.norm(sol); tom = self._tom_v
        faces = []
        for i in range(n):
            j = (i + 1) % n; quad = [base[i], base[j], topo[j], topo[i]]; mid = sum(quad) / 4
            fn = np.cross(base[j] - base[i], topo[i] - base[i]); fn /= np.linalg.norm(fn) + 1e-9
            if fn @ (mid - self.a - [0, 0, Hp / 2]) < 0:
                fn = -fn
            if fn @ (cam_pos - mid) <= 0:
                continue
            luz = 0.35 + 0.65 * max(0.0, float(fn @ sol)); cor = np.clip(ROCHA * luz * tom * rng.uniform(0.92, 1.06), 0, 1)
            faces.append((float(np.linalg.norm(cam_pos - mid)), quad, cor))
        tc = sum(topo) / n
        if cam_pos[2] > tc[2]:                 # o topo só aparece se a câmera estiver acima dele
            faces.append((float(np.linalg.norm(cam_pos - tc)) - 0.01, topo, np.clip(ROCHA * (0.35 + 0.65 * max(0.0, sol[2])) * tom * 1.05, 0, 1)))
        faces.sort(key=lambda f: -f[0])
        proj = lambda pts: [ctx.tela(p)[:2] for p in pts]
        z = ctx.tela(self.a + [0, 0, Hp * 0.4])[3]
        tela.poligonos([(proj(q), cor, 1.0) for _, q, cor in faces], z)
        linhas = []                         # fendas nas faces visíveis
        for _, q, cor in [f for f in faces if len(f[1]) == 4]:
            a0 = q[0] + (q[3] - q[0]) * rng.uniform(0.2, 0.5); a1 = q[1] + (q[2] - q[1]) * rng.uniform(0.4, 0.9)
            linhas.append((proj([a0, (a0 + a1) / 2 + rng.normal(0, 0.05, 3), a1]), 2.0, tuple(cor * 0.45), 0.9))
        _tracos(tela, linhas, z - 0.02, ctx.P.W, ctx.P.H)

    # ---------------- ganchos do núcleo
    def desenhar(self, ctx, onde, tela):
        if self.tl(ctx) < 0:
            return
        t = self.tl(ctx); zp = ctx.personagem["pe_tela"][3] if ctx.personagem else 1e9
        cam_pos = np.asarray(ctx.P.m["intrinsecos"]["pos"], float)
        if onde == "chao":
            g = self._crescimento(t); tom = self._tom_v; linhas = []; zs = []
            for pts, ini, esp in self.rach:
                if g <= ini:
                    continue
                frac = min(1.0, (g - ini) / max(1 - ini, 1e-6)) if ini > 0 else g
                m = max(2, int(len(pts) * frac)); tp = [ctx.tela(p) for p in pts[:m]]; tp = [p for p in tp if p[3] > 0.1]
                if len(tp) < 2:
                    continue
                zs.append(np.mean([p[3] for p in tp])); w = 0.075 * esp * ctx.px_por_m(tp[0][3]) * (1.5 if self.p.intensidade == "extremo" else 1.0)
                linhas.append(([(p[0], p[1] + 1.2) for p in tp], w * 0.7, tuple(np.clip(np.array(POEIRA) * tom * 1.1, 0, 1)), 0.7))   # borda clara
                linhas.append(([p[:2] for p in tp], w, (0.06, 0.045, 0.035), 0.95))
            if linhas:
                _tracos(tela, linhas, float(np.mean(zs)), ctx.P.W, ctx.P.H)
            for q in self.pedacos:
                if self._estado_pedaco(q, t) is not None:
                    self._buraco(ctx, tela, q)
            t_imp = self.fases.inicio_de("impacto")
            if self.p.intensidade == "extremo" and t >= t_imp:
                MK.desenhar(ctx, tela, self.a + [0, 0, 0.004], 1.3 * self.p.escala, self.tex_cratera, alfa=min(1.0, (t - t_imp) * 5))
            return
        faixa = (zp, 1e9) if onde == "atras" else (0, zp)
        lista = []
        for q in self.pedacos:
            e = self._estado_pedaco(q, t)
            if e is None or e[2] <= 0:
                continue
            zq = ctx.tela(e[0])[3]
            if faixa[0] <= zq < faixa[1]:
                lista.append((zq, q, e))
        for zq, q, e in sorted(lista, key=lambda x: -x[0]):            # do mais longe para o mais perto (pintor)
            self._desenhar_pedaco(ctx, tela, q, e[0], e[1], e[2], cam_pos)
        if faixa[0] <= ctx.tela(self.a)[3] < faixa[1]:
            self._pilar(ctx, tela, t, cam_pos)
        self.pedras.desenhar(ctx, tela, "pedra", 1.0, z_entre=faixa); self.poeira.desenhar(ctx, tela, "poeira", 1.0, z_entre=faixa)

    def distorcao(self, ctx):
        p = self._onda_pos(self.tl(ctx))
        if p is None:
            return None
        x, y, s, z = ctx.tela(p); px = ctx.px_por_m(z) * s
        X = ctx.P.u + ctx.P.cx; Y = ctx.P.v + ctx.P.cy
        k = np.exp(-(((X - x) / (0.6 * px)) ** 2 + ((Y - y) / (0.22 * px)) ** 2))
        return np.zeros_like(k, np.float32), (0.10 * px * self.p.fator * self.ganho * k).astype(np.float32)      # a calçada sobe

    def tremida(self, ctx):
        t = self.tl(ctx); fase, x = self.fases.em(t)
        if fase is None:
            return (0.0, 0.0)
        leve = 0.004 * 1080 * min(1.0, self.forca(ctx)) if fase in ("inicio", "ativacao", "uso") else 0.0
        dx, dy = leve * math.sin(t * 61.0 + self.p.semente), leve * 0.7 * math.sin(t * 47.0 + 2 * self.p.semente)
        if self.p.intensidade != "discreto":
            a, b = TR.tremida(t - self.fases.inicio_de("impacto"), duracao=0.5, amplitude_px=0.014 * 1080 * (1.0 if self.p.intensidade == "extremo" else 0.6),
                              semente=self.p.semente)
            dx += a; dy += b
        return dx, dy

    def impacto(self, ctx, alfa):
        if self.p.intensidade != "extremo":
            return None
        ti = self.tl(ctx) - self.fases.inicio_de("impacto")
        if 0 <= ti < 2 / ctx.fps:
            x, y, _, _ = ctx.tela(self.a)
            return IM.quadro_impacto(ctx.P, (x, y), alfa, semente=self.p.semente)
        return None

    def brilho_previsto(self, ctx):
        return 0.0
