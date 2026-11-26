"""PODER: ELASTICIDADE (E8 parte 4). Usa o núcleo de efeitos e a extensão aprovada X4 (estica só antebraço e coxa
pelo escorço do rig; a mão, a manga, a barra e o tênis ficam os do rig); não mexe no rig v2.

Como o voo e a aranha, o poder controla o MOVIMENTO do Heitor; a cena chama `desenhar_heitor(ctx, canvas)`.
Modos (kw modo):
  tocar         (de frente) o braço estica até um ponto longe, toca, vibra e volta com a mola
  pegar         (de perfil) o braço estica até a prateleira, PEGA uma fruta e volta num estalo, trazendo a fruta
  pernas_de_pau (de costas) as pernas crescem, ele espia por cima, e voltam num estalo: PISÃO no chão
Fases: início (pequena preparação: o braço recua / ele se abaixa) · ativação (estica: linhas de tensão e de
velocidade) · uso (segura esticado: vibra) · impacto (toque / estalo de volta / pisão: ondas de mola; tremida;
quadro de impacto no extremo) · dissipação (a mola assenta) · encerramento (de volta ao corpo original).
Família de cor: rosa-mola (#ff6fb5) com brilho claro (#ffd1e6); o poder não emite luz. Nada de soco esticado.
"""
import copy, math, sys
from pathlib import Path
import numpy as np
import skia
from efeitos.nucleo.base import Efeito, efeito
from efeitos.nucleo import particulas as PT, tremida as TR, impacto as IM, distorcao as DS

_EXT = Path(__file__).resolve().parents[2] / "personagens" / "heitor" / "extensoes"
for _p in (_EXT / "x2_voo", _EXT / "x3_aranha", _EXT / "x4_elasticidade"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import elasticidade as X4            # noqa: E402  (extensão aprovada)
HV, GE, X3 = X4.HV, X4.GE, X4.X3

MOLA = "#ff6fb5"; MOLA_RGB = np.array([1.0, 0.435, 0.710], np.float32); CLARO = np.array([1.0, 0.82, 0.90], np.float32)
FRUTA = np.array([0.98, 0.55, 0.12], np.float32)
DURACOES = {"tocar": {"inicio": 0.35, "ativacao": 0.3, "uso": 0.8, "impacto": 0.25, "dissipacao": 0.6, "encerramento": 0.4},
            "pegar": {"inicio": 0.4, "ativacao": 0.3, "uso": 0.55, "impacto": 0.3, "dissipacao": 0.8, "encerramento": 0.45},
            "pernas_de_pau": {"inicio": 0.4, "ativacao": 0.45, "uso": 1.0, "impacto": 0.3, "dissipacao": 0.8, "encerramento": 0.45}}


def _ler(s):
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                         alphaType=skia.AlphaType.kPremul_AlphaType).astype(np.float32) / 255.0


def _c4(rgb, a):
    return skia.Color4f(float(rgb[0]), float(rgb[1]), float(rgb[2]), float(max(0.0, min(1.0, a))))


def _suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


@efeito("elasticidade")
class Elasticidade(Efeito):
    familia = MOLA; prioridade = 2; deixa_marca = False

    def __init__(self, params=None, inicio=0.0, **kw):
        self.modo = kw.get("modo", "tocar"); d = DURACOES[self.modo]
        params.duracao = sum(d.values()); kw.setdefault("proporcoes", d)
        super().__init__(params, inicio, **kw)
        self.pe = np.asarray(kw["origem"], float); self.alvo = np.asarray(kw["alvo"], float) if kw.get("alvo") is not None else None
        self.vista = kw.get("vista", {"tocar": "frente", "pegar": "perfil", "pernas_de_pau": "costas"}[self.modo])
        self._cache = {}; self._k = None

    def _f(self, n):
        return self.fases.inicio_de(n)

    def _base(self, ctx):
        x, y, s, z = ctx.tela(self.pe); _, yt, _, _ = ctx.tela(self.pe + [0, 0, 1.4]); return x, y, y - yt, z

    def _k_esticar(self, t):
        """Quanto do esticão já foi (0..~1,12): estica na ativação, segura (vibra) no uso, volta no impacto (estalo)."""
        a, u, im, di = (self._f(n) for n in ("ativacao", "uso", "impacto", "dissipacao")); f = self.p.fator
        if t < a:
            return -0.06 * math.sin(math.pi * t / a)                          # preparação: recua um pouquinho
        if t < u:
            return GE.curva((t - a) / (u - a), "volta")
        if t < im:
            x = t - u; return 1.0 + 0.035 * min(f, 1.5) * math.exp(-x * 4) * math.sin(x * 26)   # vibra esticado
        if t < di:
            x = (t - im) / (di - im); return max(0.0, 1.0 - GE.curva(x, "saida"))             # estalo de volta
        x = t - di; return max(0.0, 0.07 * math.exp(-x * 6) * math.sin(x * 22)) if x < 0.6 else 0.0   # quique final

    # ------------------------------------------------------------------ estado do Heitor
    def estado(self, ctx):
        t = self.tl(ctx); chave = (round(t, 5), tuple(round(v, 4) for v in ctx.cam.values()))
        if self._cache.get("chave") == chave:
            return self._cache["e"]
        x, y, alt, z = self._base(ctx); u = alt / 4.0; vista = self.vista; k = self._k_esticar(t)
        base = HV.pose_base(vista); base["respira"] = math.sin(2 * math.pi * t / 2.8); e = {"z": z, "k": k, "x": x, "y": y, "alt": alt}
        if self.modo in ("tocar", "pegar"):
            ax, ay, _, az = ctx.tela(self.alvo); lado = "e" if (vista == "frente" and ax > x) else "d"
            alvo_H = ((ax - x) / u, (ay - y) / u)
            pose, erro, esc = X4.alcance(base, vista, lado, alvo_H, k=max(0.0, k))
            if self.modo == "pegar" and t >= self._f("uso") + 0.15:
                pose[f"dedos_{lado}"] = copy.deepcopy(HV.MAOS["segurar"])       # fechou a mão na fruta
            pal = X3.palma(pose, vista, lado); e.update(pose=pose, lado=lado, palma=(x + pal[0] * u, y + pal[1] * u), alvo_tela=(ax, ay, az),
                                                        rosto="surpresa" if 0.2 < k else "convencido")
        else:
            esc = 1.0 + 1.6 * max(0.0, k) * min(1.0, 0.6 + 0.4 * self.p.fator)
            pose = base; X4.pernas_de_pau(pose, esc); e.update(pose=pose, esc=esc, rosto=None)
        self._cache = {"chave": chave, "e": e}
        return e

    def desenhar_heitor(self, ctx, cv):
        e = self.estado(ctx); x, y, alt = e["x"], e["y"], e["alt"]
        if self.vista != "costas":
            cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                        skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
        r = __import__("animacao").rosto_com_piscada(e["rosto"], self.tl(ctx)) if e.get("rosto") else None
        X4.desenhar(cv, x, y, alt, vista=self.vista, pose=e["pose"], rosto=r)

    def personagem(self, ctx):
        e = self.estado(ctx)
        return {"pe_mundo": tuple(self.pe), "altura_m": 1.4 * (1 + (e.get("esc", 1.0) - 1) * X4.L_COXA / 4), "pose": e["pose"],
                "vista": self.vista, "direcao": 1, "_elast": self}

    def preparar(self, ctx):
        pc = ctx.personagem
        if pc is not None and pc.get("_elast") is self and self.modo == "pernas_de_pau":    # rosto/estampa sobem junto
            e = self.estado(ctx); sobe = (e["esc"] - 1) * X4.L_COXA * e["alt"] / 4
            pc["rosto_elipse"] = (e["x"], e["y"] - e["alt"] + 0.13 * e["alt"] - sobe, 0.15 * e["alt"], 0.14 * e["alt"]); pc["estampa_elipse"] = None
        k = int(round(self.tl(ctx) * ctx.fps))
        if self._k is None or k < self._k:
            self.poeira = PT.Sistema(self.p.semente, gravidade=0.12, arrasto=1.4, turbulencia=0.25, chao_z=self.pe[2], restituicao=0.1, fps=ctx.fps); self._k = 0
        while self._k < k:
            self._k += 1; t = self._k / ctx.fps
            if self.modo == "pernas_de_pau" and self.p.intensidade != "discreto" and abs(t - self._f("dissipacao") - 0.05) < 0.5 / ctx.fps:
                rng = self.poeira.rng; n = int(24 * self.p.fator)
                for i in range(n):                                         # pisão: anel de poeira
                    ang = 2 * math.pi * i / n; d = np.array([math.cos(ang), math.sin(ang), 0.0])
                    self.poeira.emitir(1, self.pe + d * 0.25 + [0, 0, 0.03], d * rng.uniform(1.5, 3.2) + [0, 0, 0.3], dispersao=0.2,
                                       vida=(0.7, 1.4), tam=(0.05, 0.12), cor=(0.78, 0.72, 0.62))
            self.poeira.passo()

    # ------------------------------------------------------------------ desenho do poder
    def _tracos(self, ctx, tela, linhas, z):
        """linhas: [(pontos N×2, largura, cor, alfa)] desenhadas com ponta arredondada (cobrem, leves)."""
        if not linhas:
            return
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0)
        for pts, w, cor, a in linhas:
            if a <= 0.01 or len(pts) < 2:
                continue
            path = skia.Path(); path.moveTo(*pts[0])
            for q in pts[1:]:
                path.lineTo(*q)
            cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                                         StrokeJoin=skia.Paint.kRound_Join, Color4f=_c4(cor, a)))
        tela.imagem(_ler(s), None, z)

    def _linhas_tensao(self, ctx, e, f):
        """Linhas finas paralelas ao membro esticado, onduladas, dos dois lados (aparecem ao esticar e na vibração)."""
        t = self.tl(ctx); k = e["k"]; out = []
        if k < 0.15:
            return out
        alt = e["alt"]; w = max(1.0, alt * 0.006)
        if self.modo in ("tocar", "pegar"):
            M = HV.esqueleto(e["pose"], self.vista); lado = e["lado"]; u = alt / 4.0
            a0 = M[f"antebraco_{lado}"].mapXY(0, 0); a1 = M[f"mao_{lado}"].mapXY(0, 0)
            p0 = np.array([e["x"] + a0.x() * u, e["y"] + a0.y() * u]); p1 = np.array([e["x"] + a1.x() * u, e["y"] + a1.y() * u]); segs = [(p0, p1)]
        else:
            M = HV.esqueleto(e["pose"], self.vista); u = alt / 4.0; segs = []
            for s in ("d", "e"):
                c0 = M[f"coxa_{s}"].mapXY(0, 0); c1 = M[f"canela_{s}"].mapXY(0, 0)
                segs.append((np.array([e["x"] + c0.x() * u, e["y"] + c0.y() * u]), np.array([e["x"] + c1.x() * u, e["y"] + c1.y() * u])))
        n_l = {"discreto": 1, "moderado": 2, "extremo": 3}[self.p.intensidade]
        for p0, p1 in segs:
            d = p1 - p0; L = np.linalg.norm(d)
            if L < 1:
                continue
            dn = d / L; nrm = np.array([-dn[1], dn[0]]); ss = np.linspace(0.15, 0.85, 24)
            pernas = self.modo == "pernas_de_pau"
            fora = 1 if float(np.dot((p0 + p1) / 2 - [e["x"], e["y"]], nrm)) > 0 else -1     # pernas: só o lado de fora de cada perna
            for lado_ in ((fora,) if pernas else (-1, 1)):
                for j in range(n_l):
                    off = (alt * ((0.07 if pernas else 0.055) + 0.022 * j)) * lado_
                    onda = alt * (0.004 if pernas else 0.01) * np.sin(ss * 18 + t * 30 + j) * min(1.0, k)
                    pts = p0[None] + d[None] * ss[:, None] + nrm[None] * (off + onda)[:, None]
                    out.append((pts, w * (1 - 0.25 * j), MOLA_RGB if j == 0 else CLARO, 0.75 * min(1.0, f) * min(1.0, (k - 0.15) * 2) * (1 - 0.25 * j)))
        return out

    def _ondas(self, ctx, centro, alt, x_, n, forca, dir_=None):
        """Ondas de mola ')))' em volta de um ponto: arcos que se abrem e somem (x_ = 0..1 do tempo do efeito)."""
        out = []
        for i in range(n):
            r = alt * (0.10 + 0.32 * x_ + 0.09 * i); a = (1 - x_) ** 1.3 * forca * (1 - 0.25 * i)
            if dir_ is None:
                angs = [(0.3 + q * math.pi / 2, 1.0 + q * math.pi / 2) for q in range(4)]
            else:
                b = math.atan2(dir_[1], dir_[0]); angs = [(b - 0.7, b + 0.7)]
            for a0, a1 in angs:
                th = np.linspace(a0, a1, 14); pts = np.stack([centro[0] + r * np.cos(th), centro[1] + r * np.sin(th) * (0.45 if dir_ is None and self.modo == "pernas_de_pau" else 1.0)], 1)
                out.append((pts, max(1.2, alt * 0.009), MOLA_RGB, a))
        return out

    def desenhar(self, ctx, onde, tela):
        if not self.ativo(ctx) or onde == "chao":
            return
        e = self.estado(ctx); t = self.tl(ctx); f = self.forca(ctx); zp = e["z"]; alt = e["alt"]
        if onde == "atras":
            self.poeira.desenhar(ctx, tela, "poeira", 1.0, z_entre=(zp, 1e9))
            if self.modo == "pegar" and self.alvo is not None and t < self._f("uso") + 0.15:     # a fruta na prateleira
                ax, ay, az = e["alvo_tela"]; self._fruta(ctx, tela, ax, ay, az, alt)
            return
        linhas = self._linhas_tensao(ctx, e, f)
        a, u_, im, di = (self._f(n) for n in ("ativacao", "uso", "impacto", "dissipacao"))
        n_o = {"discreto": 1, "moderado": 2, "extremo": 3}[self.p.intensidade]
        if self.modo in ("tocar", "pegar"):
            if a <= t < u_ + 0.25:                                              # chegada / toque na ponta
                x_ = (t - (u_ - 0.05)) / 0.45
                if 0 <= x_ <= 1:
                    linhas += self._ondas(ctx, e["palma"], alt, x_, n_o, min(1.0, f))
            if im <= t < im + 0.45:                                             # estalo de volta: ondas no ombro
                M = HV.esqueleto(e["pose"], self.vista); o = M[f"braco_{e['lado']}"].mapXY(0, 0); uu = alt / 4.0
                linhas += self._ondas(ctx, (e["x"] + o.x() * uu, e["y"] + o.y() * uu), alt, (t - im) / 0.45, n_o, min(1.0, f))
            if a <= t < u_ or im <= t < di:                                     # linhas de velocidade atrás da mão
                d = np.array(e["palma"]) - np.array([e["x"], e["y"] - alt * 0.7]); d /= np.linalg.norm(d) + 1e-9
                if im <= t < di:
                    d = -d
                rng = np.random.default_rng(self.p.semente + int(t * 15)); n_v = {"discreto": 3, "moderado": 5, "extremo": 8}[self.p.intensidade]
                for _ in range(n_v):
                    off = np.array([-d[1], d[0]]) * rng.uniform(-0.12, 0.12) * alt; p0 = np.array(e["palma"]) - d * alt * rng.uniform(0.08, 0.2) + off
                    linhas.append((np.array([p0, p0 - d * alt * rng.uniform(0.2, 0.5)]), max(1.0, alt * 0.006), CLARO, 0.7 * min(1.0, f)))
            if self.modo == "pegar" and t >= u_ + 0.15:                        # a fruta vem na mão
                px, py = e["palma"]; self._fruta(ctx, tela, px, py, zp - 0.1, alt)
        else:
            if im - 0.05 <= t < im + 0.5 and self.p.intensidade != "discreto":   # pisão: ondas achatadas no chão
                linhas += self._ondas(ctx, (e["x"], e["y"]), alt * 1.6, (t - im + 0.05) / 0.55, n_o, min(1.0, f))
        self._tracos(ctx, tela, linhas, zp - 0.2)
        self.poeira.desenhar(ctx, tela, "poeira", 1.0, z_entre=(0, zp))

    def _fruta(self, ctx, tela, x, y, z, alt):
        """Uma laranja (objeto de cena simples, desenho próprio) com folhinha."""
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); r = alt * 0.06
        cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=_c4(FRUTA, 1.0)))
        cv.drawCircle(x - r * 0.3, y - r * 0.3, r * 0.3, skia.Paint(AntiAlias=True, Color4f=_c4((1.0, 0.78, 0.45), 0.9)))
        cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.0, r * 0.12), Color4f=_c4((0.165, 0.114, 0.09), 1.0)))
        folha = skia.Path(); folha.moveTo(x, y - r); folha.quadTo(x + r * 0.7, y - r * 1.6, x + r * 0.9, y - r * 1.05); folha.quadTo(x + r * 0.4, y - r * 0.9, x, y - r)
        cv.drawPath(folha, skia.Paint(AntiAlias=True, Color4f=_c4((0.30, 0.62, 0.25), 1.0)))
        tela.imagem(_ler(s), None, z)

    # ------------------------------------------------------------------ distorção, tremida, impacto
    def distorcao(self, ctx):
        if self.modo != "pernas_de_pau" or self.p.intensidade == "discreto":
            return None
        ti = self.tl(ctx) - self._f("impacto")
        if not 0 <= ti <= 0.45:
            return None
        e = self.estado(ctx)
        return DS.onda_de_choque(ctx.P, (e["x"], e["y"]), e["alt"] * (0.2 + 1.2 * ti / 0.45), e["alt"] * 0.08,
                                 e["alt"] * 0.03 * self.p.fator * (1 - ti / 0.45), achatamento=0.3)

    def tremida(self, ctx):
        if self.p.intensidade == "discreto":
            return (0.0, 0.0)
        ti = self.tl(ctx) - self._f("impacto"); amp = 0.014 * 1080 * (1.0 if self.p.intensidade == "extremo" else 0.35)
        return TR.tremida(ti, duracao=0.35, amplitude_px=amp, semente=self.p.semente)

    def impacto(self, ctx, alfa):
        if self.p.intensidade != "extremo":
            return None
        ti = self.tl(ctx) - self._f("impacto")
        if 0 <= ti < 2 / ctx.fps:
            e = self.estado(ctx)
            return IM.quadro_impacto(ctx.P, (e["x"], e["y"] - e["alt"] * 0.4), alfa, semente=self.p.semente, fundo="#3a1830", linhas="#7a3a62")
        return None

    def luzes(self, ctx):
        return []

    def brilho_previsto(self, ctx):
        return 0.0
