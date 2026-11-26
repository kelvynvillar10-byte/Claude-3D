"""PODER: VOO (E8 parte 2). Usa o núcleo de efeitos e a EXTENSÃO X2 aprovada (poses de voo, corpo inclinado, roupa e
cabelo ao vento); não mexe no rig v2.

O poder controla o MOVIMENTO do Heitor a partir das fases (assim decolagem, arrancada e pouso ficam sempre sincronizados
com os efeitos). A cena pede `estado(t)` (posição da pelve, pose, vista, inclinação, vento) e desenha o Heitor com
`personagens/heitor/extensoes/x2_voo/voo.py`.

Modos (kw modo):
  pairar       sobe devagar, paira e pousa de volta (padrão do discreto)
  sair_voando  agacha, decola, paira, ARRANCA (vira o corpo e acelera) e sai do quadro (perfil)
  subir        decolagem vertical: sai do chão como um foguete, estoura a barreira no alto e some (frente/costas)
Fases:
  início       poeira começa a girar sob os pés; anéis de ar fracos
  ativação     decolagem: anel de poeira, onda de choque no chão, pedrinhas e tremida (moderado/extremo); rachadura (extremo)
  uso          voo: anéis de ar em volta do corpo, poeira soprada no chão (cai com a altura), rastros dos pés, linhas de velocidade
  impacto      arrancada: anel de vapor perpendicular ao movimento, onda de choque no ar, tremida; quadro de impacto (extremo)
  dissipação   rastros e poeira somem
  encerramento poeira assentando; a rachadura fica
Família de cores: branco-ar levemente azulado (#e9f0ff) e a poeira do chão; nada de luz forte (voo não brilha).
Sombra no chão: diminui e some com a altura (desenhada na camada do chão).
"""
import math, sys
from pathlib import Path
import numpy as np
import skia
from efeitos.nucleo.base import Efeito, efeito
from efeitos.nucleo import particulas as PT, marcas as MK, tremida as TR, impacto as IM, distorcao as DS

_X2 = Path(__file__).resolve().parents[2] / "personagens" / "heitor" / "extensoes" / "x2_voo"
if str(_X2) not in sys.path:
    sys.path.insert(0, str(_X2))
import voo as X2                    # noqa: E402  (extensão aprovada; ela importa o rig v2 só para leitura)
HV = X2.HV

AR = "#e9f0ff"; AR_RGB = np.array([0.914, 0.941, 1.0], np.float32); POEIRA = (0.80, 0.74, 0.64)
H_M = 0.35                          # H (altura da cabeça) em metros: o Heitor tem 1,4 m
PROPORCOES = {"pairar": {"inicio": 0.12, "ativacao": 0.18, "uso": 0.34, "impacto": 0.08, "dissipacao": 0.18, "encerramento": 0.10},
              "sair_voando": {"inicio": 0.12, "ativacao": 0.14, "uso": 0.30, "impacto": 0.10, "dissipacao": 0.24, "encerramento": 0.10},
              "subir": {"inicio": 0.16, "ativacao": 0.12, "uso": 0.30, "impacto": 0.10, "dissipacao": 0.22, "encerramento": 0.10}}
CONTATOS = {"pe_d": ("pe_d", 0.10, 0.10), "pe_e": ("pe_e", 0.10, 0.10), "mao_d": ("mao_d", 0.0, 0.17), "mao_e": ("mao_e", 0.0, 0.17),
            "cabeca": ("cabeca", 0.0, -0.58), "peito": ("tronco", 0.0, -0.64)}


def _ler(surface):
    """Lê a superfície do skia PRÉ-MULTIPLICADA (o formato que a tela de efeitos espera). O padrão do skia-python é
    não pré-multiplicado: nas bordas suaves isso viraria uma franja clara (ver relatório, achado)."""
    return surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                                alphaType=skia.AlphaType.kPremul_AlphaType).astype(np.float32) / 255.0


def _fita(ctx, tela, historico, largura_m, alfa):
    """Rastro de ar (como rastros.fita do núcleo, modo cobrir), lido pré-multiplicado."""
    pts = [ctx.tela(p) for p in historico]; pts = [q for q in pts if q[3] > 0.1]
    if len(pts) < 2 or alfa <= 0:
        return
    s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); n = len(pts)
    for i in range(n - 1):
        u = (i + 1) / n; w = max(1.0, largura_m * ctx.px_por_m(pts[i][3]) * pts[i][2] * u)
        cv.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                    skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                               Color4f=skia.Color4f(*[float(v) for v in AR_RGB], float(alfa * u ** 1.5)),
                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.4)))
    tela.imagem(_ler(s), None, float(np.mean([q[3] for q in pts])))


def _suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def _sai(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


@efeito("voo")
class Voo(Efeito):
    familia = AR; prioridade = 2; deixa_marca = True

    def __init__(self, params=None, inicio=0.0, **kw):
        self.modo = kw.get("modo", "pairar")
        kw.setdefault("proporcoes", PROPORCOES[self.modo])
        super().__init__(params, inicio, **kw)
        self.o = np.asarray(kw["origem"], float)                      # pés no chão no começo (mundo)
        d = np.asarray(kw.get("direcao", (0.0, 1.0, 0.0)), float); self.d = d / (np.linalg.norm(d) + 1e-9)
        self.vista = kw.get("vista", "perfil" if self.modo == "sair_voando" else "frente")
        self.lado = kw.get("lado_tela", 1)                            # direção na tela (+1 = olha para a direita)
        self._k = None; self.hist = {"pe_d": [], "pe_e": []}

    # ------------------------------------------------------------------ movimento (o poder decide)
    def _f(self, nome):
        return self.fases.inicio_de(nome)

    def estado(self, t):
        """Estado do Heitor no tempo local t: pelve (mundo), pose, vista, inclinação, expressão e velocidade."""
        p = self._estado_pos(t); p2 = self._estado_pos(t + 1 / 60)
        p["vel"] = (np.asarray(p2["pelve"]) - np.asarray(p["pelve"])) * 60
        return p

    def _estado_pos(self, t):
        z0 = self.o[2]; vista = self.vista; d = self.d; a = self._f("ativacao"); u = self._f("uso"); im = self._f("impacto")
        di = self._f("dissipacao"); en = self._f("encerramento"); T = self.fases.duracao; fator = self.p.fator
        pe = HV.pose_base(vista); pair = X2.pose_voo("pairar", vista, t)
        pel_pe = X2.altura_pelve(pe) * H_M
        if self.modo == "pairar":
            alt = 0.55 + 0.25 * min(fator, 1.0)
            if t < a:
                pose, h, rosto = pe, 0.0, "neutro"
            elif t < u:
                k = _suave((t - a) / (u - a)); pose = X2.transicao(pe, pair, k); h = alt * k; rosto = "alegria"
            elif t < di:
                pose, h, rosto = pair, alt, "alegria"
            elif t < en + 0.6 * (T - en):
                k = _suave((t - di) / (en + 0.6 * (T - en) - di)); pose = X2.transicao(pair, pe, k); h = alt * (1 - k); rosto = "alegria"
            else:
                pose, h, rosto = pe, 0.0, "alegria"
            pel = self.o + [0, 0, pel_pe + h]; inc = 0.0
        elif self.modo == "sair_voando":
            ag = X2.pose_voo("agachar", vista, t); imp = X2.pose_voo("impulso", vista, t); cru = X2.pose_voo("cruzeiro", vista, t)
            alt = 1.1; inc = 0.0; rosto = "alegria"; avanco = 0.0
            if t < a:
                k = _suave(t / a); pose = X2.transicao(pe, ag, k); h = 0.0; rosto = "convencido"     # o agachar (raiz da pose) já abaixa a pelve com os pés no chão
            elif t < u:
                x = (t - a) / (u - a); k = _suave(min(1.0, x * 3)); pose = X2.transicao(ag, imp, k); h = alt * _sai(x)
            elif t < im:
                k = _suave((t - u) / (im - u) * 1.6); pose = X2.transicao(imp, pair, k); h = alt
            else:
                k = _suave((t - im) / (di - im)); pose = X2.transicao(pair, cru, k); inc = 72.0 * k; h = alt + 0.25 * k
                tt = t - im; avanco = 0.9 * tt * tt * (1 + 2.0 * (fator - 0.45)) + (max(0.0, t - di) ** 2) * 3.0 * fator
            pel = self.o + [0, 0, pel_pe + h] + d * avanco
        else:   # subir
            imp = X2.pose_voo("impulso", vista, t); inc = 0.0; rosto = "convencido" if t < a else "alegria"
            if t < a:
                pose, h = pe, 0.0
            else:
                k = _suave((t - a) / ((u - a) * 0.5)); pose = X2.transicao(pe, imp, k)
                x_ = min(1.0, (t - a) / (im - a)); h = 1.3 * (1 - (1 - x_) ** 2) + max(0.0, t - im) * 2.0 + max(0.0, t - im) ** 2 * 7.0
            pel = self.o + [0, 0, pel_pe + h] + d * (0.25 * max(0.0, h - 1.0))
        return {"pelve": tuple(pel), "pose": pose, "vista": vista, "direcao": self.lado, "inclinacao": inc, "rosto": rosto,
                "altura_chao": float(pel[2] - pel_pe - z0)}

    # ------------------------------------------------------------------ geometria do personagem na tela (mesma da X2)
    def tela_personagem(self, ctx, t=None):
        """(x_pelve, y_pelve, altura_px, profundidade) na tela da placa — o desenhista usa exatamente isto."""
        e = self.estado(self.tl(ctx) if t is None else t); pm = np.asarray(e["pelve"])
        x, y, s, z = ctx.tela(pm); _, ya, _, _ = ctx.tela(pm - [0, 0, 0.6]); _, yb, _, _ = ctx.tela(pm + [0, 0, 0.8])
        return x, y, (ya - yb), z

    def ponto(self, ctx, nome, t=None):
        """Ponto do rig (mão, pé, cabeça, peito) na tela, com a pose, a inclinação e a direção da X2."""
        tl = self.tl(ctx) if t is None else t; e = self.estado(tl); x, y, alt, z = self.tela_personagem(ctx, tl)
        osso, lx, ly = CONTATOS[nome]; M = HV.esqueleto(e["pose"], e["vista"]); u = alt / 4.0
        if osso.startswith("pe_") and e["vista"] in ("frente", "costas"):
            lx = 0.0                                     # de frente/costas o tênis fica centrado no tornozelo (desenhar_pe do rig)
        q = M[osso].mapXY(lx, ly)
        px, py = q.x() * u * e["direcao"], X2.ALT_PELVE * u + q.y() * u
        th = math.radians(e["inclinacao"] * e["direcao"]); c, s = math.cos(th), math.sin(th)
        return x + px * c - py * s, y + px * s + py * c, z

    def _para_mundo(self, ctx, x, y, z):
        """Tela → mundo no plano de profundidade z (desfaz o movimento de câmera como os contatos do núcleo)."""
        I = ctx.P.m["intrinsecos"]; pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))
        cam = ctx.cam; zz = z + cam.get("tz", 0.0); zoom = cam.get("zoom", 1.0)
        u = ((x - ctx.P.cx) / zoom * (zz - cam.get("tz", 0.0)) + ctx.P.f * cam.get("tx", 0.0)) / zz
        v = ((y - ctx.P.cy) / zoom * (zz - cam.get("tz", 0.0)) - ctx.P.f * cam.get("ty", 0.0)) / zz
        return pos + (dr + (u / ctx.P.f) * dx - (v / ctx.P.f) * cima) * zz

    def personagem(self, ctx_ou_none=None, t=None):
        """Dicionário para Mesa.preparar (contatos, proteção do rosto/estampa e a X1). Precisa do ctx para as elipses."""
        e = self.estado(t)
        pe = np.asarray(e["pelve"]) - [0, 0, X2.ALT_PELVE * H_M]
        return {"pe_mundo": tuple(pe), "altura_m": 1.4, "pose": e["pose"], "vista": e["vista"], "direcao": e["direcao"], "_voo": self}

    def vento_tela(self, ctx):
        """Vento para a X2 (direção do ar em relação ao Heitor, na tela): contra a velocidade + corrente do poder."""
        tl = self.tl(ctx); e = self.estado(tl); pm = np.asarray(e["pelve"]); v = np.asarray(e["vel"])
        x0, y0, _, _ = ctx.tela(pm); x1, y1, _, _ = ctx.tela(pm + v * 0.05); d = np.array([x1 - x0, y1 - y0]); n = np.linalg.norm(d)
        vel = float(np.linalg.norm(v)); out = np.zeros(2)
        if n > 1e-6:
            out = -d / n * min(1.0, vel / 5.0)
        fase, _ = self.fases.em(tl)
        if fase in ("ativacao", "uso") and vel < 2.0 and e["altura_chao"] > 0.05:
            out = out + np.array([0.06, -0.30]) * min(1.0, self.forca(ctx) + 0.3)        # corrente de ar subindo enquanto paira
        return tuple(out)

    # ------------------------------------------------------------------ simulação (poeira, pedrinhas), determinística
    def preparar(self, ctx):
        pc = ctx.personagem
        if pc is not None and pc.get("_voo") is self:      # proteção do rosto e da estampa onde eles ESTÃO (corpo inclinado)
            x, y, alt, _ = self.tela_personagem(ctx); hx, hy, _ = self.ponto(ctx, "cabeca"); px_, py_, _ = self.ponto(ctx, "peito")
            pc["rosto_elipse"] = (hx, hy, 0.15 * alt, 0.14 * alt)
            pc["estampa_elipse"] = (px_, py_ - 0.03 * alt, 0.15 * alt, 0.07 * alt) if pc.get("vista") in ("frente", "tres_quartos") else None
        k = int(round(self.tl(ctx) * ctx.fps))
        if self._k is None or k < self._k:
            self.poeira = PT.Sistema(self.p.semente, gravidade=0.12, arrasto=1.4, turbulencia=0.25, chao_z=self.o[2], restituicao=0.1, fps=ctx.fps)
            self.pedras = PT.Sistema(self.p.semente + 3, gravidade=1.0, arrasto=0.3, chao_z=self.o[2], restituicao=0.3, fps=ctx.fps)
            self.tex = MK.textura("rachadura", self.p.semente); self._k = 0; self.hist = {"pe_d": [], "pe_e": []}
            self._cor_poeira(ctx)
        while self._k < k:
            self._k += 1; self._passo(ctx, self._k / ctx.fps)

    def _cor_poeira(self, ctx):
        """Poeira com a cor do chão daquele horário (amostrada no fundo, como a terra), misturada ao bege."""
        fundo = self.kw.get("fundo"); self.cor_p = np.array(POEIRA)
        if fundo is not None:
            u, v, z = ctx.placa(self.o); r = 40
            jan = fundo[max(0, int(v) - r):int(v) + r, max(0, int(u) - r):int(u) + r]
            if jan.size:
                self.cor_p = np.clip(0.5 * np.array(POEIRA) * float(np.clip(jan.mean() / 0.55, 0.45, 1.2)) + 0.5 * np.median(jan.reshape(-1, 3), 0), 0, 1)

    def _passo(self, ctx, t):
        fase, x = self.fases.em(t); f = self.fases.envelope(t) * self.p.fator * max(self.ganho, 0.0)
        e = self.estado(t); h = e["altura_chao"]; chao = np.array([e["pelve"][0], e["pelve"][1], self.o[2]])
        rng = self.poeira.rng
        # sopro no chão: poeira saindo para fora sob o Heitor (cai com a altura; some acima de 2,5 m)
        sopro = max(0.0, 1 - h / 2.5) * f * (0.5 if fase == "inicio" else 1.0)
        if fase in ("inicio", "ativacao", "uso", "impacto", "dissipacao") and sopro > 0.02:
            for _ in range(int(round(3 * sopro + rng.uniform(0, 1)))):
                ang = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 0.45); dirc = np.array([math.cos(ang), math.sin(ang), 0])
                self.poeira.emitir(1, chao + dirc * r + [0, 0, 0.03], dirc * rng.uniform(1.2, 2.6) * (0.6 + 0.6 * sopro) + [0, 0, 0.25],
                                   dispersao=0.15, vida=(0.7, 1.4), tam=(0.05, 0.11), cor=tuple(self.cor_p))
        # decolagem: anel de poeira e pedrinhas (moderado/extremo); no discreto, um sopro leve
        t_dec = self._f("ativacao")
        if fase == "ativacao" and abs(t - t_dec - 1 / ctx.fps) < 0.5 / ctx.fps:
            n = {"discreto": 10, "moderado": 36, "extremo": 70}[self.p.intensidade]
            for i in range(n):
                ang = 2 * math.pi * i / n + rng.uniform(-0.1, 0.1); dirc = np.array([math.cos(ang), math.sin(ang), 0])
                self.poeira.emitir(1, self.o + dirc * 0.3 + [0, 0, 0.04], dirc * rng.uniform(2.5, 5.0) * self.p.fator ** 0.5 + [0, 0, 0.4],
                                   dispersao=0.3, vida=(0.9, 1.8), tam=(0.07, 0.16), cor=tuple(self.cor_p))
            if self.p.intensidade != "discreto":
                self.pedras.emitir(int(14 * self.p.fator), self.o + [0, 0, 0.05], (0, 0, 2.6 * self.p.fator ** 0.5), dispersao=1.6,
                                   vida=(0.8, 1.5), tam=(0.015, 0.035), cor=tuple(np.clip(self.cor_p * 0.7, 0, 1)), raio_origem=0.15)
        self.poeira.passo(); self.pedras.passo()
        # rastros: histórico dos pés no mundo (só quando rápido)
        vel = float(np.linalg.norm(e["vel"])); self.hist_novo = {}
        for nome in ("pe_d", "pe_e"):
            hh = self.hist[nome]; self.hist_novo[nome] = False
            if vel > 1.5 and fase in ("ativacao", "uso", "impacto", "dissipacao"):
                x_, y_, z_ = self.ponto(ctx, nome, t); hh.append(self._para_mundo(ctx, x_, y_, z_)); self.hist_novo[nome] = True
            elif hh:
                hh.pop(0)
            del hh[:-10]

    # ------------------------------------------------------------------ desenho
    def _aneis(self, ctx, tela, onde, forca):
        """Anéis de ar em volta do corpo (2D): elipses perpendiculares ao eixo do corpo, girando; a metade de trás fica
        atrás do Heitor e a da frente na frente (com proteção do rosto e da estampa)."""
        if forca <= 0.03:
            return
        tl = self.tl(ctx); e = self.estado(tl); x, y, alt, zp = self.tela_personagem(ctx)
        hx, hy, _ = self.ponto(ctx, "cabeca"); ax = np.array([hx - x, hy - y]); ax /= np.linalg.norm(ax) + 1e-9; nx = np.array([-ax[1], ax[0]])
        vel = float(np.linalg.norm(e["vel"])); n = {"discreto": 2, "moderado": 3, "extremo": 4}[self.p.intensidade]
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); desenhou = False
        for i in range(n):
            ciclo = (tl * (0.55 + 0.25 * vel) + i / n) % 1.0
            pos_ = -0.55 + 1.35 * ciclo if vel < 2.0 else 0.75 - 1.5 * ciclo          # sobe pairando; corre para trás voando
            c = np.array([x, y]) + ax * pos_ * alt * 0.5; rx = alt * (0.30 + 0.08 * math.sin(i * 1.7)); ry = alt * 0.07
            vida = math.sin(math.pi * ciclo); gira = tl * 5.0 + i * 2.0
            th = np.linspace(gira, gira + 2.6, 30)
            frente = np.sin(th) > 0
            pts = c[None] + nx[None] * (rx * np.cos(th))[:, None] + ax[None] * (ry * np.sin(th))[:, None]
            sel = frente if onde == "frente" else ~frente
            idx = np.nonzero(sel)[0]
            if len(idx) < 2:
                continue
            grupos = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
            for g in grupos:
                if len(g) < 2:
                    continue
                for j in range(len(g) - 1):
                    a0, a1 = pts[g[j]], pts[g[j + 1]]; u = (g[j] - 0) / len(th); w = max(1.2, alt * 0.009 * math.sin(math.pi * u))
                    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                                   Color4f=skia.Color4f(*[float(v) for v in AR_RGB], float(min(0.75, 0.3 + 0.45 * forca) * vida * math.sin(math.pi * u) ** 0.6)),
                                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.5))
                    cv.drawLine(float(a0[0]), float(a0[1]), float(a1[0]), float(a1[1]), p); desenhou = True
        if desenhou:
            img = _ler(s)
            tela.imagem(img, None, zp + (0.25 if onde == "atras" else -0.25))

    def _linhas_velocidade(self, ctx, tela, forca):
        """Linhas de velocidade atrás do Heitor, paralelas ao movimento na tela (só quando rápido)."""
        e = self.estado(self.tl(ctx)); vel = float(np.linalg.norm(e["vel"]))
        if vel < 2.0 or forca <= 0.03:
            return
        x, y, alt, zp = self.tela_personagem(ctx); pm = np.asarray(e["pelve"]); x1, y1, _, _ = ctx.tela(pm + np.asarray(e["vel"]) * 0.05)
        d = np.array([x1 - x, y1 - y]); d /= np.linalg.norm(d) + 1e-9; nrm = np.array([-d[1], d[0]])
        rng = np.random.default_rng(self.p.semente * 31 + ctx.quadro // 2)               # redesenha a cada 2 quadros
        n = {"discreto": 4, "moderado": 7, "extremo": 11}[self.p.intensidade]; k = min(1.0, (vel - 2.0) / 4.0)
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0)
        for _ in range(n):
            off = rng.uniform(-0.35, 0.35) * alt; atras = rng.uniform(0.15, 0.5) * alt; L = rng.uniform(0.3, 0.8) * alt * (0.5 + 0.5 * k)
            p0 = np.array([x, y]) + nrm * off - d * atras; p1 = p0 - d * L; w = max(1.0, alt * rng.uniform(0.003, 0.006))
            p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                           Color4f=skia.Color4f(*[float(v) for v in AR_RGB], float(0.85 * min(1.0, forca) * k)))
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)],
                                                       [skia.Color4f(*[float(v) for v in AR_RGB], float(0.85 * min(1.0, forca) * k)), skia.Color4f(*[float(v) for v in AR_RGB], 0.0)]))
            cv.drawLine(float(p0[0]), float(p0[1]), float(p1[0]), float(p1[1]), p)
        img = _ler(s)
        tela.imagem(img, None, zp + 0.3)

    def _anel_arrancada(self, ctx, tela, onde):
        """Impacto: anel de vapor em volta do Heitor, perpendicular ao movimento NA TELA (legível em qualquer câmera), que
        se abre e some; metade de trás atrás dele. Extremo: 3 anéis e um cone de vapor. Discreto (pairar): sem anel."""
        ti = self.tl(ctx) - self._f("impacto"); dur = 0.55
        if not (0 <= ti <= dur) or self.p.intensidade == "discreto":
            return
        t_im = self._f("impacto"); x, y, alt, zp = self.tela_personagem(ctx)
        e = self.estado(t_im + 0.05); pm = np.asarray(e["pelve"]); x1, y1, _, _ = ctx.tela(pm + np.asarray(e["vel"]) * 0.05)
        x0, y0, _, _ = ctx.tela(pm); d = np.array([x1 - x0, y1 - y0]); d = d / (np.linalg.norm(d) + 1e-9) if np.linalg.norm(d) > 1e-6 else np.array([0.0, -1.0])
        nrm = np.array([-d[1], d[0]]); xx = ti / dur; n = 3 if self.p.intensidade == "extremo" else 1
        s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0); hx, hy, _ = self.ponto(ctx, "peito")
        for i in range(n):
            R = alt * (0.22 + 0.75 * _sai(xx)) * (1 - 0.2 * i) * self.p.escala; r = R * 0.32
            c = np.array([hx, hy]) - d * alt * (0.15 + 0.35 * xx + 0.22 * i)
            th = np.linspace(0, math.pi, 36) if onde == "frente" else np.linspace(math.pi, 2 * math.pi, 36)
            pts = c[None] + nrm[None] * (R * np.cos(th))[:, None] + d[None] * (r * np.sin(th))[:, None]
            a_ = float((1 - xx) ** 1.2 * (0.95 if i == 0 else 0.65) * max(self.ganho, 0.0))
            w = max(1.5, alt * 0.016 * (1 - 0.3 * i))
            path = skia.Path(); path.moveTo(*pts[0])
            for q in pts[1:]:
                path.lineTo(*q)
            cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                                         Color4f=skia.Color4f(*[float(v) for v in AR_RGB], a_), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.45)))
        if self.p.intensidade == "extremo" and onde == "atras":         # cone de vapor atrás do Heitor
            R = alt * (0.22 + 0.75 * _sai(xx)); c = np.array([hx, hy]) - d * alt * (0.15 + 0.35 * xx)
            cone = [np.array([hx, hy]) + d * alt * 0.25, c + nrm * R, c - nrm * R]
            path = skia.Path(); path.moveTo(*cone[0]); path.lineTo(*cone[1]); path.lineTo(*cone[2]); path.close()
            cv.drawPath(path, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*[float(v) for v in AR_RGB], float(0.3 * (1 - xx) * max(self.ganho, 0.0))),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, alt * 0.03)))
        img = _ler(s)
        tela.imagem(img, None, zp + (0.2 if onde == "atras" else -0.2))

    def desenhar(self, ctx, onde, tela):
        tl = self.tl(ctx)
        if tl < 0:
            return
        ativo = self.ativo(ctx); f = self.forca(ctx) if ativo else 0.0
        if onde == "chao":
            t_dec = self._f("ativacao")
            if self.p.intensidade == "extremo" and tl >= t_dec:                       # rachadura da decolagem (fica)
                MK.desenhar(ctx, tela, tuple(self.o), 0.75 * self.p.escala, self.tex, alfa=min(1.0, (tl - t_dec) * 8))
            if ativo:
                self._sombra(ctx, tela)
            return
        if not ativo:
            return
        x, y, alt, zp = self.tela_personagem(ctx)
        if onde == "atras":
            self._linhas_velocidade(ctx, tela, f)
            for nome, hh in self.hist.items():
                if len(hh) > 2:
                    _fita(ctx, tela, hh, 0.04 * self.p.escala, 0.7 * min(1.0, f))
            self._aneis(ctx, tela, "atras", f); self._anel_arrancada(ctx, tela, "atras")
            self.poeira.desenhar(ctx, tela, "poeira", 1.0, z_entre=(zp, 1e9)); self.pedras.desenhar(ctx, tela, "pedra", 1.0, z_entre=(zp, 1e9))
            return
        self._aneis(ctx, tela, "frente", f); self._anel_arrancada(ctx, tela, "frente")
        self.poeira.desenhar(ctx, tela, "poeira", 1.0, z_entre=(0, zp)); self.pedras.desenhar(ctx, tela, "pedra", 1.0, z_entre=(0, zp))

    def _sombra(self, ctx, tela):
        """Sombra no chão sob a pelve: diminui, clareia e borra com a altura; some acima de 3 m."""
        e = self.estado(self.tl(ctx)); h = e["altura_chao"]; pm = np.asarray(e["pelve"]); g = np.array([pm[0], pm[1], self.o[2]])
        k = max(0.0, 1 - h / 3.0)
        if k <= 0.02:
            return
        xs, ys, s, z = ctx.tela(g); px = ctx.px_por_m(z) * s; w = px * 0.45 * (0.55 + 0.45 * k); hh = px * 0.04 * (0.7 + 0.3 * k)
        sf = skia.Surface(ctx.P.W, ctx.P.H); cv = sf.getCanvas(); cv.clear(0)
        cv.drawOval(skia.Rect.MakeXYWH(xs - w / 2, ys - hh / 2, w, hh),
                    skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.16, 0.11, 0.09, float(0.43 * k ** 1.2)),
                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(1.0, px * (0.012 + 0.05 * (1 - k))))))
        img = _ler(sf)
        tela.imagem(img, None, z)
        self.ultima_sombra = {"centro": (xs, ys), "alfa": 0.43 * k ** 1.2}

    # ------------------------------------------------------------------ distorção, tremida, impacto, luz
    def distorcao(self, ctx):
        tl = self.tl(ctx); campos = []
        td = tl - self._f("ativacao")
        if self.p.intensidade != "discreto" and 0 <= td <= 0.45:                       # onda de choque no chão, na decolagem
            x, y, s, z = ctx.tela(self.o); px = ctx.px_por_m(z) * s
            campos.append(DS.onda_de_choque(ctx.P, (x, y), px * (0.3 + 2.6 * _sai(td / 0.45)), px * 0.18,
                                            px * 0.05 * self.p.fator * (1 - td / 0.45) * self.ganho, achatamento=0.35))
        ti = tl - self._f("impacto")
        if self.p.intensidade != "discreto" and 0 <= ti <= 0.4:                        # onda no ar, na arrancada
            x, y, alt, z = self.tela_personagem(ctx, self._f("impacto"))
            campos.append(DS.onda_de_choque(ctx.P, (x, y), alt * (0.3 + 1.4 * _sai(ti / 0.4)), alt * 0.1,
                                            alt * 0.025 * self.p.fator * (1 - ti / 0.4) * self.ganho, achatamento=0.8))
        if not campos:
            return None
        return sum(c[0] for c in campos), sum(c[1] for c in campos)

    def tremida(self, ctx):
        if self.p.intensidade == "discreto":
            return (0.0, 0.0)
        tl = self.tl(ctx); amp = 0.014 * 1080 * (1.0 if self.p.intensidade == "extremo" else 0.45)
        a = TR.tremida(tl - self._f("ativacao"), duracao=0.4, amplitude_px=amp, semente=self.p.semente)
        b = TR.tremida(tl - self._f("impacto"), duracao=0.3, amplitude_px=amp * 0.6, semente=self.p.semente + 1)
        return a[0] + b[0], a[1] + b[1]

    def impacto(self, ctx, alfa):
        if self.p.intensidade != "extremo":
            return None
        ti = self.tl(ctx) - self._f("impacto")
        if 0 <= ti < 2 / ctx.fps:
            x, y, _, _ = self.tela_personagem(ctx)
            return IM.quadro_impacto(ctx.P, (x, y), alfa, semente=self.p.semente, fundo="#1b2d4a", linhas="#3d5f86")
        return None

    def luzes(self, ctx):
        """Voo quase não emite luz: só um clarão branco suave na arrancada (moderado/extremo)."""
        ti = self.tl(ctx) - self._f("impacto")
        if self.p.intensidade == "discreto" or not (0 <= ti <= 0.35) or not self.ativo(ctx):
            return []
        e = self.estado(self.tl(ctx)); k = (1 - ti / 0.35) * (1.0 if self.p.intensidade == "extremo" else 0.5) * self.ganho
        return [{"pos": tuple(e["pelve"]), "cor": tuple(float(v) for v in AR_RGB), "forca": 1.2 * k, "raio": 0.5}]

    def brilho_previsto(self, ctx):
        return sum(L["forca"] for L in self.luzes(ctx)) / 10.0

    def luz_personagem(self, ctx):
        return None
