"""PODER: ARANHA (E8 parte 3). Usa o núcleo de efeitos e as extensões aprovadas X3 (escalada, balanço no fio, gesto de
lançar) e X2 (corpo inclinado, roupa e cabelo ao vento); não mexe no rig v2.

Como o voo, o poder controla o MOVIMENTO do Heitor a partir das fases; a cena chama `desenhar_heitor(ctx, canvas)`.
Modos (kw modo):
  lancar    (de frente) gesto de lançar → o fio voa até o alvo e GRUDA → ele puxa → puxão → solta (o fio afrouxa e some)
  balancar  (de perfil) lança o fio para o alto → gruda → o fio encurta e ele sai do chão balançando → no ponto mais
            baixo, o puxão (tensão máxima, o fio vibra) → solta no alto e sai do quadro; o fio volta e some
  escalar   (de costas) escala a parede deixando PEGADAS de grude → para, lança um leque de fios → uma REDE se forma →
            ele se puxa até a rede, que estica e vibra → fica preso nela; a rede e as pegadas ficam
Fases: início · ativação (o fio voa e gruda) · uso (tensão / puxão / rede se formando) · impacto (puxão máximo: vibração,
tremida; quadro de impacto no extremo) · dissipação (solta / balança) · encerramento (o que fica: grude, pegadas, rede).
Família de cores: seda marfim (#ece3c6) com brilho branco fino; o fio não emite luz.
"""
import copy, math, sys
from pathlib import Path
import numpy as np
import skia
from efeitos.nucleo.base import Efeito, efeito
from efeitos.nucleo import particulas as PT, tremida as TR, impacto as IM

_EXT = Path(__file__).resolve().parents[2] / "personagens" / "heitor" / "extensoes"
for _p in (_EXT / "x2_voo", _EXT / "x3_aranha"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import aranha as X3                  # noqa: E402  (extensão aprovada)
HV, GE, X2 = X3.HV, X3.GE, X3.X2

SEDA = "#ece3c6"; SEDA_RGB = np.array([0.925, 0.890, 0.776], np.float32); BRILHO = np.array([1.0, 0.99, 0.96], np.float32)
H_M = 0.35
DURACOES = {"lancar": {"inicio": 0.5, "ativacao": 0.3, "uso": 1.0, "impacto": 0.25, "dissipacao": 0.8, "encerramento": 0.5},
            "balancar": {"inicio": 0.6, "ativacao": 0.35, "uso": 0.62, "impacto": 0.3, "dissipacao": 1.3, "encerramento": 0.5},
            "escalar": {"inicio": 1.4, "ativacao": 0.55, "uso": 0.8, "impacto": 0.3, "dissipacao": 0.9, "encerramento": 0.5}}


def _ler(s):
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                         alphaType=skia.AlphaType.kPremul_AlphaType).astype(np.float32) / 255.0


def _sai(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def _suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def _norm(pose):
    """Ângulos de braço em (−180°, 180°]: a transição entre poses vai pelo caminho curto (o braço não cruza o rosto)."""
    for k in ("braco_d", "braco_e", "antebraco_d", "antebraco_e", "mao_d", "mao_e"):
        pose[k] = GE._ang(pose[k])
    return pose


PONTA_PUNHO = (0.0, 0.21)      # no balanço o fio sai do alto do punho fechado (a palma fica atrás da cabeça, de perfil)


def _ponta(pose, lado="e"):
    q = HV.esqueleto(pose, "perfil")[f"mao_{lado}"].mapXY(*PONTA_PUNHO); return q.x(), q.y()


def _c4(rgb, a):
    return skia.Color4f(float(rgb[0]), float(rgb[1]), float(rgb[2]), float(max(0.0, min(1.0, a))))


@efeito("aranha")
class Aranha(Efeito):
    familia = SEDA; prioridade = 2; deixa_marca = True

    def __init__(self, params=None, inicio=0.0, **kw):
        self.modo = kw.get("modo", "lancar"); d = DURACOES[self.modo]
        params.duracao = sum(d.values()); kw.setdefault("proporcoes", d)
        super().__init__(params, inicio, **kw)
        self.pe = np.asarray(kw["origem"], float)               # pés do Heitor no começo (mundo)
        self.alvos = [np.asarray(a, float) for a in kw.get("alvos", [])]   # âncoras (mundo)
        self.esc = X3.Escalada("costas") if self.modo == "escalar" else None
        self.bal = X3.Balanco(amplitude=1.0, periodo=2.4, atraso=0.10, direcao=1) if self.modo == "balancar" else None
        self._cache = {}

    def _f(self, n):
        return self.fases.inicio_de(n)

    # ------------------------------------------------------------------ geometria básica
    def _base(self, ctx):
        """(x, y) dos pés, altura em px e profundidade do Heitor parado no começo."""
        x, y, s, z = ctx.tela(self.pe); _, yt, _, _ = ctx.tela(self.pe + [0, 0, 1.4])
        return x, y, y - yt, z

    def _palma_tela(self, ctx, pose, vista, x, y, alt, lado, inc=0.0, direcao=1, ref=None):
        """Centro da palma na tela (desenho do rig com a pose; com inclinação em torno de 'ref', como a X2)."""
        u = alt / 4.0; px, py = X3.palma(pose, vista, lado)
        if ref is None:
            return x + px * u * direcao, y + py * u
        ox, oy = px * u * direcao, X2.ALT_PELVE * u + py * u; th = math.radians(inc * direcao); c, s = math.cos(th), math.sin(th)
        return ref[0] + ox * c - oy * s, ref[1] + ox * s + oy * c

    def _alvo_H(self, ctx, alvo):
        x, y, alt, _ = self._base(ctx); ax, ay, _, _ = ctx.tela(alvo); u = alt / 4.0
        return ((ax - x) / u, (ay - y) / u)

    # ------------------------------------------------------------------ estado do Heitor + fios, por modo
    def estado(self, ctx):
        t = self.tl(ctx); chave = (round(t, 5), tuple(round(v, 4) for v in ctx.cam.values()), ctx.quadro)
        if chave in self._cache:
            return self._cache[chave]
        e = getattr(self, "_estado_" + self.modo)(ctx, t); self._cache = {chave: e}
        return e

    def _tiro(self, t, t0, dur=0.22):
        """Fração do caminho que a ponta do fio já percorreu (0 → 1)."""
        return _sai((t - t0) / dur) if t >= t0 else 0.0

    def _estado_lancar(self, ctx, t):
        x, y, alt, z = self._base(ctx); alvo = self.alvos[0]; a, u_, im, di, en = (self._f(n) for n in ("ativacao", "uso", "impacto", "dissipacao", "encerramento"))
        base = HV.pose_base("frente"); mira = HV.pose_base("frente"); lado = "e" if ctx.tela(alvo)[0] > x else "d"
        X3.pose_lancar(mira, "frente", lado, self._alvo_H(ctx, alvo)); _norm(mira)
        if t < a:
            k = GE.curva(t / a, "volta")
        elif t < di + 0.15:
            k = 1.0
        else:
            k = 1 - _suave((t - di - 0.15) / (self.fases.duracao - di - 0.15))
        pose = X2.transicao(base, mira, max(0.0, min(1.0, k)))
        if u_ <= t < di:                                          # puxa: o cotovelo dobra um pouco
            pux = 0.35 * math.sin(math.pi * min(1.0, (t - u_) / (di - u_)))
            pose[f"antebraco_{lado}"] += (1 if lado == "e" else -1) * -14 * pux
        palma = self._palma_tela(ctx, pose, "frente", x, y, alt, lado)
        fios = []
        if t >= a:
            ax, ay, _, az = ctx.tela(alvo); frac = self._tiro(t, a)
            estado = "voando" if frac < 1 else ("tenso" if t < di else "solto")
            fios.append({"de": palma, "ate": (ax, ay), "z": (z + az) / 2, "frac": frac, "estado": estado, "t_solto": t - di})
        return {"desenho": ("rig", x, y, alt, "frente", pose, "convencido"), "z": z, "fios": fios, "grudes": [(alvo, a + 0.22)],
                "rosto_elipse": None}

    def _estado_balancar(self, ctx, t):
        x, y, alt, z = self._base(ctx); A = self.alvos[0]; ax, ay, _, az = ctx.tela(A)
        a, u_, im, di = (self._f(n) for n in ("ativacao", "uso", "impacto", "dissipacao"))
        base = HV.pose_base("perfil"); mira = HV.pose_base("perfil"); X3.pose_lancar(mira, "perfil", "e", self._alvo_H(ctx, A)); _norm(mira)
        pxm = alt / 1.4                                              # px por metro no plano do Heitor
        palma0 = self._palma_tela(ctx, mira, "perfil", x, y, alt, "e")
        L0 = math.hypot(palma0[0] - ax, palma0[1] - ay); fi0 = math.degrees(math.atan2(palma0[0] - ax, palma0[1] - ay))
        L1 = max(0.6 * L0, (y - ay) - 1.30 * alt)                     # comprimento final: os pés passam acima do chão
        w = (math.pi / 2) / max(im - u_, 1e-3)                        # o fundo do arco (velocidade máxima) cai no começo do impacto
        out = {"z": z, "grudes": [(A, a + 0.22)], "fios": [], "rosto_elipse": None}
        if t < u_:
            k = GE.curva(min(1.0, t / max(a, 1e-3)), "volta")
            pose = X2.transicao(base, mira, max(0.0, min(1.0, k)))
            out["desenho"] = ("rig", x, y, alt, "perfil", pose, "convencido")
            if t >= a:
                pal = self._palma_tela(ctx, pose, "perfil", x, y, alt, "e")
                out["fios"].append({"de": pal, "ate": (ax, ay), "z": (z + az) / 2, "frac": self._tiro(t, a), "estado": "tenso"})
            return out
        tau = t - u_; L = L0 + (L1 - L0) * _sai(tau / 0.45)
        t_solta = (di - u_) + 0.06; fi = fi0 * math.cos(w * min(tau, t_solta)); dfi = -fi0 * w * math.sin(w * min(tau, t_solta))
        if tau <= t_solta:
            k = _suave(tau / 0.3); pb = self.bal.pose(0.0); kk = max(-1.0, min(1.0, dfi / (abs(fi0) * w + 1e-9)))
            pb = self._pose_balanco(kk); pose = X2.transicao(mira, pb, k)
            inc = -fi * k; mao = (ax + L * math.sin(math.radians(fi)), ay + L * math.cos(math.radians(fi)))
            qx, qy = _ponta(pose); u = alt / 4.0; ox, oy = qx * u, X2.ALT_PELVE * u + qy * u
            th = math.radians(inc); c, s = math.cos(th), math.sin(th); ref = (mao[0] - (ox * c - oy * s), mao[1] - (ox * s + oy * c))
            vel = (L * math.cos(math.radians(fi)) * math.radians(dfi), -L * math.sin(math.radians(fi)) * math.radians(dfi))
            out["desenho"] = ("x2", ref[0], ref[1], alt, "perfil", pose, "alegria", inc, vel)
            out["fios"].append({"de": mao, "ate": (ax, ay), "z": (z + az) / 2, "frac": 1.0, "estado": "tenso", "tensao": abs(math.cos(math.radians(fi)))})
            out["mao"] = mao
        else:                                                          # solta no alto e sai voando (balística)
            ts = tau - t_solta; fi_s = fi0 * math.cos(w * t_solta); dfi_s = -fi0 * w * math.sin(w * t_solta)
            mao_s = (ax + L1 * math.sin(math.radians(fi_s)), ay + L1 * math.cos(math.radians(fi_s)))
            impulso = 2.6 + 0.8 * self.p.fator                            # o fio "estilinga" o Heitor na soltura
            vx = impulso * L1 * math.cos(math.radians(fi_s)) * math.radians(dfi_s); vy = impulso * -L1 * math.sin(math.radians(fi_s)) * math.radians(dfi_s) - 0.8 * pxm
            g = 9.81 * pxm; mao = (mao_s[0] + vx * ts, mao_s[1] + vy * ts + 0.5 * g * ts * ts)
            k = _suave(ts / 0.35); pose = X2.transicao(self._pose_balanco(-1.0), X2.pose_voo("impulso", "perfil", t), k)
            inc = -fi_s * (1 - k) + 35.0 * k
            qx, qy = _ponta(pose); u = alt / 4.0; ox, oy = qx * u, X2.ALT_PELVE * u + qy * u
            th = math.radians(inc); c, s = math.cos(th), math.sin(th); ref = (mao[0] - (ox * c - oy * s), mao[1] - (ox * s + oy * c))
            out["desenho"] = ("x2", ref[0], ref[1], alt, "perfil", pose, "alegria", inc, (vx, vy + g * ts))
            volta = _sai(ts / 0.3)                                     # o fio solto volta para a âncora e some
            out["fios"].append({"de": (mao_s[0] + (ax - mao_s[0]) * volta, mao_s[1] + (ay - mao_s[1]) * volta), "ate": (ax, ay),
                                "z": (z + az) / 2, "frac": 1.0, "estado": "solto", "t_solto": ts})
        return out

    def _pose_balanco(self, kk):
        """A pose do balanço da X3 com o sentido do movimento kk (−1..1)."""
        T = self.bal.T; t = math.acos(max(-1.0, min(1.0, kk))) / (2 * math.pi / T) if kk != 0 else T / 4
        return self.bal.pose(t)

    def _estado_escalar(self, ctx, t):
        x0, y0, alt, z = self._base(ctx); u = alt / 4.0; E = self.esc
        a, u_, im, di = (self._f(n) for n in ("ativacao", "uso", "impacto", "dissipacao"))
        t_fz = a; o_fz = E.origem(t_fz)
        out = {"z": z, "fios": [], "grudes": [], "pegadas": [], "rosto_elipse": None}
        # pegadas: cada apoio plantado durante a escalada deixa um grude na parede (fica)
        for nome in ("mao_d", "mao_e", "pe_d", "pe_e"):
            k = 0
            while True:
                t_pl = (k + 0.5 - E.defasagem[nome]) * E.T
                if t_pl > min(t, t_fz):
                    break
                if t_pl >= 0:
                    p, _ = E.apoio(nome, t_pl + 1e-4); out["pegadas"].append((nome, p.copy(), t_pl))
                k += 1
        centro = np.array([0.0, o_fz[1] - 5.3])                         # centro da rede (H, plano da parede), acima das mãos
        ancs = self._ancoras_H(ctx)
        if t < a:
            pose, _ = E.pose(t); o = E.origem(t)
        else:
            pose, _ = E.pose(t_fz); o = o_fz.copy()
            if t < u_:                                                 # lança o leque de fios com a mão direita
                k = GE.curva((t - a) / (u_ - a) * 2.5, "volta"); mira = copy.deepcopy(pose)
                X3.pose_lancar(mira, "costas", "d", (centro[0] - o[0], centro[1] - o[1]))
                pose = X2.transicao(pose, mira, max(0.0, min(1.0, k)))
            else:                                                      # puxa-se até a rede
                sub = _sai((t - u_) / (im - u_)); o = o_fz + (centro - [0, -3.75] - o_fz) * np.array([0, 1]) * sub
                if t >= im:                                            # na rede: estica e vibra
                    tt = t - im; o = o + np.array([0, 0.35 * math.exp(-tt * 3.0) * math.cos(tt * 14.0) * self.p.fator])
        xs, ys = x0 + o[0] * u, y0 + o[1] * u
        out["desenho"] = ("rig", xs, ys, alt, "costas", pose, None)
        if t >= a:
            pal = self._palma_tela(ctx, pose, "costas", xs, ys, alt, "d")
            c_tela = (x0 + centro[0] * u, y0 + centro[1] * u)
            if t >= im:                                                # o centro da rede é puxado para baixo pelo corpo
                c_tela = (c_tela[0], c_tela[1] + (o[1] - (centro[1] + 3.75)) * u * 0.6)
            for i, aH in enumerate(ancs):
                at = (x0 + aH[0] * u, y0 + aH[1] * u); t0 = a + 0.06 * i
                if t < u_:
                    out["fios"].append({"de": pal, "ate": at, "z": z + 0.3, "frac": self._tiro(t, t0), "estado": "tenso"})
                out["grudes"].append((("tela", at), t0 + 0.22))
            if t >= u_:
                out["rede"] = {"centro": c_tela, "ancoras": [(x0 + aH[0] * u, y0 + aH[1] * u) for aH in ancs],
                               "forma": _suave((t - u_) / (im - u_) * 1.3), "z": z + 0.3,
                               "vib": (0.0 if t < im else math.exp(-(t - im) * 3.0) * math.sin((t - im) * 22.0))}
        out["origem_tela"] = (x0, y0, u)
        return out

    def _ancoras_H(self, ctx):
        """Âncoras da rede (H, no plano da parede, relativas aos pés no começo)."""
        x0, y0, alt, _ = self._base(ctx); u = alt / 4.0; out = []
        for A in self.alvos:
            ax, ay, _, _ = ctx.tela(A); out.append(((ax - x0) / u, (ay - y0) / u))
        return out

    # ------------------------------------------------------------------ desenho do Heitor (a cena chama isto)
    def desenhar_heitor(self, ctx, cv):
        e = self.estado(ctx); d = e["desenho"]; tl = self.tl(ctx)
        if d[0] == "rig":
            _, x, y, alt, vista, pose, rosto = d
            r = __import__("animacao").rosto_com_piscada(rosto, tl) if rosto else None
            if vista != "costas":
                cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                            skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
            HV.desenhar(cv, x, y, alt, vista=vista, direcao=1, pose=pose, rosto=r)
        else:
            _, x, y, alt, vista, pose, rosto, inc, vel = d
            v = np.asarray(vel, float); n = np.linalg.norm(v); mps = n / (alt / 1.4)
            vento = tuple(-v / n * min(1.0, mps / 5.0)) if n > 1e-6 else (0.0, 0.0)
            X2.desenhar(cv, x, y, alt, vista=vista, direcao=1, pose=pose, rosto=__import__("animacao").rosto_com_piscada(rosto, tl),
                        inclinacao=inc, vento=vento, t=tl)

    def personagem(self, ctx):
        """Para Mesa.preparar e a X1 (antes da mesa ter o contexto, usa o do quadro informado)."""
        e = self.estado(ctx); d = e["desenho"]; P = ctx.P
        x, y, alt = d[1], d[2], d[3]
        if d[0] == "x2":    # pés de referência da X2 (pelve − 1,72 H)
            y = y + X2.ALT_PELVE * alt / 4.0
        pe = self._tela_para_mundo(ctx, x, y, e["z"])
        return {"pe_mundo": tuple(pe), "altura_m": 1.4, "pose": d[5], "vista": d[4], "direcao": 1, "_aranha": self}

    def _tela_para_mundo(self, ctx, x, y, z):
        I = ctx.P.m["intrinsecos"]; pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))
        cam = ctx.cam; zz = z + cam.get("tz", 0.0); zoom = cam.get("zoom", 1.0)
        u = ((x - ctx.P.cx) / zoom * (zz - cam.get("tz", 0.0)) + ctx.P.f * cam.get("tx", 0.0)) / zz
        v = ((y - ctx.P.cy) / zoom * (zz - cam.get("tz", 0.0)) - ctx.P.f * cam.get("ty", 0.0)) / zz
        return pos + (dr + (u / ctx.P.f) * dx - (v / ctx.P.f) * cima) * zz

    # ------------------------------------------------------------------ partículas (fiapos que somem)
    def preparar(self, ctx):
        pc = ctx.personagem
        if pc is not None and pc.get("_aranha") is self:
            e = self.estado(ctx); d = e["desenho"]
            if d[0] == "x2":                                           # corpo inclinado: rosto onde ele está
                _, x, y, alt, vista, pose, _, inc, _ = d; M = HV.esqueleto(pose, vista); q = M["cabeca"].mapXY(0, -0.58); u = alt / 4.0
                ox, oy = q.x() * u, X2.ALT_PELVE * u + q.y() * u; th = math.radians(inc); c, s = math.cos(th), math.sin(th)
                pc["rosto_elipse"] = (x + ox * c - oy * s, y + ox * s + oy * c, 0.15 * alt, 0.14 * alt); pc["estampa_elipse"] = None
        k = int(round(self.tl(ctx) * ctx.fps))
        if not hasattr(self, "fiapos") or getattr(self, "_k", None) is None or k < self._k:
            self.fiapos = PT.Sistema(self.p.semente, gravidade=0.08, arrasto=1.6, turbulencia=0.3, fps=ctx.fps); self._k = 0
        while self._k < k:
            self._k += 1; self.fiapos.passo()

    # ------------------------------------------------------------------ desenho do poder
    def _fio_pts(self, fio, t_ctx):
        """Pontos do fio na tela: voando (ponta avançando, ondulação que some), tenso (reto, vibrando) ou solto (afrouxa)."""
        a = np.array(fio["de"], float); b = np.array(fio["ate"], float); frac = fio.get("frac", 1.0)
        ponta = a + (b - a) * frac; d = ponta - a; L = np.linalg.norm(d) + 1e-9; n = np.array([-d[1], d[0]]) / L
        s = np.linspace(0, 1, 40); pts = a[None] + d[None] * s[:, None]
        if fio["estado"] == "tenso" and frac < 1:
            pts += n[None] * (L * 0.05 * (1 - frac) * np.sin(math.pi * s * 3 + t_ctx * 30) * np.sin(math.pi * s))[:, None]
        elif fio["estado"] == "tenso":
            amp = getattr(self, "_vib", 0.0) * L * 0.035
            pts += n[None] * (amp * np.sin(math.pi * s * 2) * np.sin(t_ctx * 40))[:, None]
        elif fio["estado"] == "solto":
            sag = min(1.0, fio.get("t_solto", 0) / 0.4) * L * 0.18
            pts += np.array([0.0, 1.0])[None] * (sag * np.sin(math.pi * s))[:, None]
        return pts

    def _desenhar_fio(self, ctx, tela, pts, z, alfa, larg_px):
        if alfa <= 0.01 or len(pts) < 2:
            return
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); path = skia.Path(); path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
        for w, cor, a, borra in ((larg_px * 3.2, SEDA_RGB, 0.22, larg_px * 1.2), (larg_px, SEDA_RGB, 0.95, 0), (max(0.8, larg_px * 0.35), BRILHO, 0.9, 0)):
            p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                           StrokeJoin=skia.Paint.kRound_Join, Color4f=_c4(cor, a * alfa))
            if borra:
                p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, borra))
            cv.drawPath(path, p)
        tela.imagem(_ler(s), None, z)

    def _grude(self, ctx, tela, x, y, z, raio, alfa, semente):
        """Mancha de grude: miolo, fios radiais curtos e dois anéis ligando os fios (pequena teia)."""
        if alfa <= 0.01 or raio < 1:
            return
        rng = np.random.default_rng(semente); n = int(rng.integers(6, 9)); angs = np.sort(rng.uniform(0, 2 * math.pi, n) + np.arange(n) * 0.0)
        angs = 2 * math.pi * np.arange(n) / n + rng.uniform(-0.25, 0.25, n); comp = raio * rng.uniform(0.7, 1.1, n)
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); w = max(0.8, raio * 0.07)
        pf = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, Color4f=_c4(SEDA_RGB, 0.9 * alfa))
        for ang, L in zip(angs, comp):
            cv.drawLine(x, y, x + L * math.cos(ang), y + L * math.sin(ang), pf)
        for f in (0.45, 0.8):
            path = skia.Path()
            for j, (ang, L) in enumerate(zip(list(angs) + [angs[0]], list(comp) + [comp[0]])):
                q = (x + f * L * math.cos(ang), y + f * L * math.sin(ang)); path.moveTo(*q) if j == 0 else path.lineTo(*q)
            cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w * 0.7, Color4f=_c4(SEDA_RGB, 0.75 * alfa)))
        cv.drawCircle(x, y, raio * 0.22, skia.Paint(AntiAlias=True, Color4f=_c4(SEDA_RGB, 0.95 * alfa)))
        cv.drawCircle(x - raio * 0.06, y - raio * 0.06, raio * 0.08, skia.Paint(AntiAlias=True, Color4f=_c4(BRILHO, 0.9 * alfa)))
        tela.imagem(_ler(s), None, z)

    def _rede(self, ctx, tela, rede, larg_px, alfa):
        c = np.array(rede["centro"]); ancs = [np.array(a) for a in rede["ancoras"]]; f = rede["forma"]; vib = rede["vib"]
        if f <= 0:
            return
        ordem = sorted(ancs, key=lambda a: math.atan2(a[1] - c[1], a[0] - c[0]))
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0)
        def traco(p0, p1, w, a):
            mid = (p0 + p1) / 2 + np.array([0.0, vib * np.linalg.norm(p1 - p0) * 0.05])
            path = skia.Path(); path.moveTo(*p0); path.quadTo(*mid, *p1)
            cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, Color4f=_c4(SEDA_RGB, a)))
            cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(0.7, w * 0.35), Color4f=_c4(BRILHO, a * 0.8)))
        for a in ordem:                                                  # raios (sempre)
            traco(c, a, larg_px, 0.95 * alfa)
        for k, fr in enumerate((0.3, 0.55, 0.8)):                       # anéis aparecem um por um
            ak = max(0.0, min(1.0, f * 3 - k))
            if ak <= 0:
                continue
            pts = [c + (a - c) * fr for a in ordem]
            for i in range(len(pts)):
                traco(pts[i], pts[(i + 1) % len(pts)], larg_px * 0.75, 0.85 * alfa * ak)
        tela.imagem(_ler(s), None, rede["z"])

    def desenhar(self, ctx, onde, tela):
        tl = self.tl(ctx)
        if tl < 0:
            return
        fim = tl > self.fases.duracao
        e = self.estado(ctx) if not fim else self._estado_final(ctx)
        _, _, alt, zp = self._base(ctx); larg = max(1.2, alt * 0.008 * (0.8 + 0.25 * self.p.fator) * self.p.escala)
        if onde == "atras":                                            # o que fica na parede: grude, pegadas e rede
            for i, (ref, t0) in enumerate(e.get("grudes", [])):
                if tl < t0:
                    continue
                if isinstance(ref, tuple) and ref and ref[0] == "tela":
                    gx, gy = ref[1]; gz = zp + 0.3
                else:
                    gx, gy, _, gz = ctx.tela(ref)
                self._grude(ctx, tela, gx, gy, gz, alt * (0.07 + 0.03 * self.p.fator), min(1.0, (tl - t0) * 8), self.p.semente * 31 + i)
            for j, (nome, p, t_pl) in enumerate(e.get("pegadas", [])):
                x0, y0, u = e["origem_tela"]
                self._grude(ctx, tela, x0 + p[0] * u, y0 + p[1] * u, zp + 0.25, alt * 0.035, 0.75, self.p.semente * 7 + j)
            if e.get("rede"):
                self._rede(ctx, tela, e["rede"], larg, 1.0)
            return
        if onde != "frente" or fim:
            return
        f = self.forca(ctx); self._vib = 0.0
        ti = tl - self._f("impacto")
        if 0 <= ti <= 0.5:
            self._vib = math.exp(-ti * 6) * self.p.fator
        for fio in e.get("fios", []):
            a = 1.0
            if fio["estado"] == "solto":
                a = max(0.0, 1 - fio.get("t_solto", 0) / 0.45)
            pts = self._fio_pts(fio, tl)
            # o fio sai DA PALMA: o trecho perto da mão fica na frente; o resto atrás do Heitor só se a âncora estiver atrás
            self._desenhar_fio(ctx, tela, pts, fio["z"] if fio["z"] < zp else zp - 0.05, a, larg * (1.25 if fio.get("tensao", 0) > 0.95 else 1.0))
            if self.p.intensidade == "extremo" and self.modo == "balancar":
                self._desenhar_fio(ctx, tela, pts + np.array([larg * 2.2, 0]), zp - 0.05, a * 0.8, larg * 0.7)

    def _estado_final(self, ctx):
        """Depois do fim: só o que fica (grude, pegadas, rede parada)."""
        e = dict(self.estado(ctx)); e["fios"] = []
        return e

    # ------------------------------------------------------------------ tremida, impacto
    def tremida(self, ctx):
        if self.p.intensidade == "discreto":
            return (0.0, 0.0)
        ti = self.tl(ctx) - self._f("impacto"); amp = 0.014 * 1080 * (1.0 if self.p.intensidade == "extremo" else 0.4)
        return TR.tremida(ti, duracao=0.35, amplitude_px=amp, semente=self.p.semente)

    def impacto(self, ctx, alfa):
        if self.p.intensidade != "extremo":
            return None
        ti = self.tl(ctx) - self._f("impacto")
        if 0 <= ti < 2 / ctx.fps:
            d = self.estado(ctx)["desenho"]
            return IM.quadro_impacto(ctx.P, (d[1], d[2] - d[3] * 0.5), alfa, semente=self.p.semente, fundo="#2a2238", linhas="#5a4a6e")
        return None

    def luzes(self, ctx):
        return []

    def brilho_previsto(self, ctx):
        return 0.0
