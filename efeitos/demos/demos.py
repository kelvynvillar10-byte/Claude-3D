"""Plugins de DEMONSTRAÇÃO do núcleo (E7). Cada um exercita peças do núcleo; NENHUM é poder (os poderes são da E8).

demo_faiscas  partículas (gravidade, quique no chão, rastro de movimento) saindo da mão + luz 2D laranja
demo_arco     curva fractal da mão até um ponto do cenário, redesenhada a cada 2 quadros + luz que tremula
demo_poeira   poeira e fumaça (partículas que cobrem), atrás e na frente do personagem conforme a profundidade
demo_orbe     ponto de luz que passa pela rua à noite: luz 2D com albedo da placa + rastro (fita)
demo_onda     onda de choque (distorção) + tremida + rachadura que fica no chão + quadro de impacto + poeira
demo_calor    tremulação de calor acima de uma fonte + fumaça fina
demo_corda    corda com física presa na fachada e na mão; no impacto, a mão solta e ela balança (pêndulo)
demo_estrobo  só para o teste de segurança: luz que pisca forte (o governador limita os flashes)
"""
import math
import numpy as np
from efeitos.nucleo.base import Efeito, efeito
from efeitos.nucleo import particulas as PT, curvas as CV, corda as CD, distorcao as DS, impacto as IM, tremida as TR, \
    marcas as MK, rastros as RS, contatos as CT


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


class _ComSimulacao(Efeito):
    """Base para efeitos com simulação por quadro (partículas, corda): avança até o quadro pedido; se o quadro voltar
    (testes fora de ordem), refaz do começo — o resultado é sempre o mesmo para a mesma semente."""
    def _novo(self, ctx): raise NotImplementedError
    def _passo(self, ctx, k): raise NotImplementedError

    def preparar(self, ctx):
        k = int(round(self.tl(ctx) * ctx.fps))
        if getattr(self, "_k", None) is None or k < self._k:
            self._novo(ctx); self._k = 0
        while self._k < k:
            self._k += 1; self._passo(ctx, self._k)

    def _z_personagem(self, ctx):
        return ctx.personagem["pe_tela"][3] if ctx.personagem else 1e9


@efeito("demo_faiscas")
class Faiscas(_ComSimulacao):
    familia = "#ffb347"

    def _novo(self, ctx):
        self.s = PT.Sistema(self.p.semente, gravidade=1.0, arrasto=0.4, chao_z=0.154, restituicao=0.4, fps=ctx.fps)

    def _passo(self, ctx, k):
        t = k / ctx.fps; f = self.fases.envelope(t) * self.p.fator * self.ganho; fase, _ = self.fases.em(t)
        if fase in ("ativacao", "uso", "impacto") and ctx.personagem:
            n = int((18 if fase == "impacto" else 6) * f)
            o = CT.rig_mundo(ctx, "mao_d"); d = np.asarray(self.p.direcao, float)
            self.s.emitir(n, o, d * 2.2 * self.p.velocidade + np.array([0, 0, 1.2]), dispersao=1.1, vida=(0.5, 1.1),
                          tam=(0.006, 0.014), cor=_rgb(self.p.cor))
        self.s.passo()

    def luzes(self, ctx):
        if not ctx.personagem or not self.ativo(ctx):
            return []
        f = self.forca(ctx); fl = 0.8 + 0.2 * math.sin(ctx.quadro * 1.7)
        return [{"pos": tuple(CT.rig_mundo(ctx, "mao_d")), "cor": _rgb(self.p.cor), "forca": 0.9 * f * fl, "raio": 0.25}]

    def desenhar(self, ctx, onde, tela):
        zp = self._z_personagem(ctx)
        if onde == "atras":
            self.s.desenhar(ctx, tela, "faisca", self.ganho, z_entre=(zp, 1e9))
        elif onde == "frente":
            self.s.desenhar(ctx, tela, "faisca", self.ganho, z_entre=(0, zp))


@efeito("demo_arco")
class Arco(Efeito):
    familia = "#b9a7ff"

    def _curvas(self, ctx):
        k = ctx.quadro // 2                                         # redesenho a cada 2 quadros
        rng = np.random.default_rng(self.p.semente * 1000 + k)
        a = CT.rig_mundo(ctx, "mao_d"); b = np.asarray(self.kw["alvo"], float)
        return CV.fractal(a, b, rng, niveis=6, desvio=0.16 * self.p.escala, ramos=3)

    def luzes(self, ctx):
        if not ctx.personagem or not self.ativo(ctx):
            return []
        a = CT.rig_mundo(ctx, "mao_d"); b = np.asarray(self.kw["alvo"], float); fl = 0.7 + 0.3 * ((ctx.quadro // 2) % 3) / 2
        return [{"pos": tuple((a + b) / 2), "cor": _rgb(self.p.cor), "forca": 1.4 * self.forca(ctx) * fl, "raio": 0.4}]

    def desenhar(self, ctx, onde, tela):
        if onde == "frente" and ctx.personagem and self.ativo(ctx):
            CV.desenhar(ctx, tela, self._curvas(ctx), self.p.cor, largura_m=0.0028 * self.p.escala, forca=min(1.0, self.forca(ctx)) * 0.85)


@efeito("demo_poeira")
class Poeira(_ComSimulacao):
    familia = "#c9b08a"

    def _novo(self, ctx):
        self.s = PT.Sistema(self.p.semente, gravidade=0.04, vento=self.kw.get("vento", (0.3, 0.0, 0.15)), arrasto=1.2, turbulencia=0.35,
                            chao_z=0.154, fps=ctx.fps)

    def _passo(self, ctx, k):
        t = k / ctx.fps; fase, _ = self.fases.em(t); f = self.fases.envelope(t) * self.p.fator * self.ganho
        if fase in ("ativacao", "uso", "impacto"):
            n = int((9 if fase == "impacto" else 2) * f)
            self.s.emitir(2 * n, self.kw["origem"], (0, 0, 0.6), dispersao=0.9, vida=(1.4, 2.6), tam=(0.07, 0.14) if self.kw.get("estilo") != "fumaca" else (0.08, 0.16),
                          cor=_rgb(self.p.cor), raio_origem=0.25 * self.p.escala)
        self.s.passo()

    def desenhar(self, ctx, onde, tela):
        zp = self._z_personagem(ctx); est = self.kw.get("estilo", "poeira")
        if onde == "atras":
            self.s.desenhar(ctx, tela, est, self.ganho, z_entre=(zp, 1e9))
        elif onde == "frente":
            self.s.desenhar(ctx, tela, est, self.ganho, z_entre=(0, zp))


@efeito("demo_orbe")
class Orbe(Efeito):
    familia = "#7fd4ff"

    def _pos(self, t):
        c = np.asarray(self.kw["centro"], float); r = self.kw.get("raio", 1.6); w = 0.9 * self.p.velocidade
        return c + np.array([r * 0.55 * math.sin(w * t), r * math.cos(w * t) - r, 0.25 * math.sin(2 * w * t)])

    def luzes(self, ctx):
        if not self.ativo(ctx):
            return []
        return [{"pos": tuple(self._pos(self.tl(ctx))), "cor": _rgb(self.p.cor), "forca": 2.6 * self.forca(ctx), "raio": 0.35}]

    def desenhar(self, ctx, onde, tela):
        if not self.ativo(ctx):
            return
        t = self.tl(ctx); p = self._pos(t); x, y, s, z = ctx.tela(p)
        zp = self._z_personagem(ctx) if ctx.personagem else 1e9
        if (onde == "frente") != (z < zp):
            return
        f = self.forca(ctx); r = 0.05 * ctx.px_por_m(z) * s
        hist = [self._pos(max(0.0, t - k / ctx.fps)) for k in range(14, -1, -1)]
        RS.fita(ctx, tela, hist, self.p.cor, largura_m=0.06, alfa=0.5 * min(f, 1.0))
        tela.mancha(x, y, r * 5.0, np.array(_rgb(self.p.cor)) * 0.22 * min(f, 1.0), 1.0, z, "add")
        tela.mancha(x, y, r, np.array([0.85, 0.95, 1.0]) * 0.8 * min(1.0, f), 1.0, z, "add")

    def _z_personagem(self, ctx):
        return ctx.personagem["pe_tela"][3]


@efeito("demo_onda")
class Onda(_ComSimulacao):
    familia = "#e8f0ff"; prioridade = 2

    def _novo(self, ctx):
        self.s = PT.Sistema(self.p.semente, gravidade=0.05, arrasto=1.5, turbulencia=0.3, chao_z=0.154, fps=ctx.fps)
        self.tex = MK.textura("rachadura", self.p.semente)

    def _passo(self, ctx, k):
        t = k / ctx.fps; t_imp = self.fases.inicio_de("impacto")
        if abs(t - t_imp) < 0.5 / ctx.fps:
            self.s.emitir(int(70 * self.p.fator), self.kw["origem"], (0, 0, 0.6), dispersao=2.0, vida=(1.0, 2.2), tam=(0.1, 0.2),
                          cor=(0.78, 0.72, 0.62), raio_origem=0.2)
        self.s.passo()

    def _t_imp(self, ctx):
        return self.tl(ctx) - self.fases.inicio_de("impacto")

    def distorcao(self, ctx):
        ti = self._t_imp(ctx)
        if not (0 <= ti <= 0.6):
            return None
        x, y, s, z = ctx.tela(self.kw["origem"]); px = ctx.px_por_m(z) * s
        return DS.onda_de_choque(ctx.P, (x, y), raio_px=ti * 7.0 * px * self.p.velocidade, largura_px=0.35 * px,
                                 amplitude_px=32 * self.p.fator * self.ganho * (1 - ti / 0.6))

    def tremida(self, ctx):
        return TR.tremida(self._t_imp(ctx), duracao=0.4, amplitude_px=0.014 * 1080 * min(1.0, self.p.fator), semente=self.p.semente)

    def impacto(self, ctx, alfa):
        ti = self._t_imp(ctx)
        if 0 <= ti < 2 / ctx.fps and self.kw.get("quadro_impacto", True):   # 2 quadros
            x, y, _, _ = ctx.tela(self.kw["origem"])
            return IM.quadro_impacto(ctx.P, (x, y), alfa, semente=self.p.semente)
        return None

    def desenhar(self, ctx, onde, tela):
        ti = self._t_imp(ctx)
        if onde == "chao" and ti >= 0:                          # a rachadura fica até o fim
            MK.desenhar(ctx, tela, self.kw["origem"], 1.3 * self.p.escala, self.tex, alfa=min(1.0, ti * 8))
            if ti <= 0.6:                                        # anel de poeira clara acompanhando a onda, no chão
                ox, oy, oz = self.kw["origem"]; r = ti * 7.0 * self.p.velocidade
                for k in range(36):
                    a = 2 * math.pi * k / 36; x, y, s, z = ctx.tela((ox + r * math.cos(a), oy + r * math.sin(a), oz + 0.05))
                    tela.mancha(x, y, 0.18 * ctx.px_por_m(z) * s, (0.93, 0.9, 0.84), 0.35 * (1 - ti / 0.6), z, "alpha")
        zp = ctx.personagem["pe_tela"][3] if ctx.personagem else 1e9
        if onde == "atras":
            self.s.desenhar(ctx, tela, "poeira", 1.0, z_entre=(zp, 1e9))
        elif onde == "frente":
            self.s.desenhar(ctx, tela, "poeira", 1.0, z_entre=(0, zp))


@efeito("demo_calor")
class Calor(_ComSimulacao):
    familia = "#ffd9a0"

    def _novo(self, ctx):
        self.s = PT.Sistema(self.p.semente, gravidade=-0.08, vento=(0.2, 0, 0.6), arrasto=1.0, turbulencia=0.4, fps=ctx.fps)

    def _passo(self, ctx, k):
        t = k / ctx.fps
        if self.fases.em(t)[0] in ("ativacao", "uso", "impacto"):
            self.s.emitir(1, self.kw["origem"], (0, 0, 0.5), dispersao=0.15, vida=(1.5, 2.5), tam=(0.06, 0.1), cor=(0.7, 0.68, 0.66), raio_origem=0.1)
        self.s.passo()

    def distorcao(self, ctx):
        if not self.ativo(ctx):
            return None
        x, y, s, z = ctx.tela(self.kw["origem"]); px = ctx.px_por_m(z) * s
        return DS.calor(ctx.P, (x, y), largura_px=1.2 * px, altura_px=2.2 * px, amplitude_px=3.5 * self.forca(ctx), t=ctx.t)

    def desenhar(self, ctx, onde, tela):
        if onde == "atras":
            self.s.desenhar(ctx, tela, "fumaca", 0.6)


@efeito("demo_corda")
class Corda(_ComSimulacao):
    familia = "#f2efe8"

    def _novo(self, ctx):
        mao = CT.rig_mundo(ctx, "mao_d"); a = np.asarray(self.kw["ancora"], float)
        self.c = CD.Corda(a, mao, n=26, comprimento=np.linalg.norm(mao - a) * 1.08, fps=ctx.fps)

    def _passo(self, ctx, k):
        t = k / ctx.fps
        if self.fases.em(t)[0] in ("impacto", "dissipacao", "encerramento"):
            self.c.solta_b = True                                # a mão solta: vira pêndulo
        self.c.passo(b=None if self.c.solta_b else CT.rig_mundo(ctx, "mao_d"))

    def desenhar(self, ctx, onde, tela):
        if onde == "frente" and self.ativo(ctx):
            self.c.desenhar(ctx, tela, self.p.cor, espessura_m=0.015 * self.p.escala, alfa=min(1.0, self.forca(ctx) * 1.5))


@efeito("demo_estrobo")
class Estrobo(Efeito):
    """Só para o teste de segurança: pisca a cada 2 quadros (7,5 flashes/s, acima do limite de 3/s)."""
    familia = "#ffffff"

    def luzes(self, ctx):
        if not self.ativo(ctx):
            return []
        acesa = (ctx.quadro // 2) % 2 == 0
        return [{"pos": tuple(self.kw["pos"]), "cor": (1, 1, 1), "forca": (40.0 if acesa else 0.0) * self.ganho, "raio": 0.5, "difusa": 0.6}]

    def brilho_previsto(self, ctx):
        acesa = (ctx.quadro // 2) % 2 == 0
        return 4.0 if acesa else 0.0
