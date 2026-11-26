"""PODER: ELETRICIDADE (E8). Usa só o núcleo; não mexe no rig.

Família de cores: ciano-claro com núcleo quase branco (contrasta com o azul #3d80d8 da camiseta: ΔE medido no teste).
Fases:
  início      estalos: faíscas pequenas na mão, arcos curtos começando a correr pelo corpo
  ativação    arcos pelo contorno do corpo aumentam; a mão acende; luz ciano no cenário
  uso         (moderado/extremo) raio fractal da mão ao alvo, redesenhado a cada 2 quadros (3 no discreto), ramos
  impacto     raio mais forte; faíscas no alvo; marca queimada (alvo no chão); tremida; quadro de impacto (extremo)
  dissipação  arcos residuais, fumaça no alvo, luz caindo
  encerramento estalos finais
Intensidades: discreto (só corpo + mão), moderado (raio ao alvo), extremo (raios múltiplos e grossos, chão, impacto).
Luz no personagem: calculada (luz_personagem) e registrada; NÃO aplicada (extensão do rig pendente de aprovação).
"""
import math
import numpy as np
import cv2
import skia
from efeitos.nucleo.base import Efeito, efeito
from efeitos.nucleo import particulas as PT, curvas as CV, marcas as MK, tremida as TR, impacto as IM, contatos as CT

HALO = "#6ff4ff"; NUCLEO = "#f5feff"; HALO2 = "#b8f9ff"


def _rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


@efeito("eletricidade")
class Eletricidade(Efeito):
    familia = HALO; prioridade = 3; deixa_marca = True

    def __init__(self, params=None, inicio=0.0, **kw):
        super().__init__(params, inicio, **kw)
        self.redesenho = 3 if self.p.intensidade == "discreto" else 2
        self.mao = kw.get("mao", "mao_d")                   # contato: a mão que aponta (mao_d ou mao_e)
        self._k = None; self.ultimas_curvas = []

    # ---------------- simulação (faíscas e fumaça), determinística
    def preparar(self, ctx):
        k = int(round(self.tl(ctx) * ctx.fps))
        if self._k is None or k < self._k:
            self.faisca = PT.Sistema(self.p.semente, gravidade=1.0, arrasto=0.6, chao_z=0.154, restituicao=0.35, fps=ctx.fps)
            self.fumaca = PT.Sistema(self.p.semente + 7, gravidade=-0.06, vento=(0.25, 0, 0.5), arrasto=1.0, turbulencia=0.4, fps=ctx.fps)
            self.tex = MK.textura("queimado", self.p.semente); self._k = 0
        while self._k < k:
            self._k += 1; self._passo(ctx, self._k / ctx.fps)

    def _passo(self, ctx, t):
        fase, _ = self.fases.em(t); f = self.fases.envelope(t) * self.p.fator * self.ganho
        if ctx.personagem and fase in ("inicio", "ativacao", "uso", "impacto", "dissipacao"):
            mao = CT.rig_mundo(ctx, self.mao)
            n = int(round({"inicio": 1.5, "ativacao": 3, "uso": 2, "impacto": 6, "dissipacao": 1}[fase] * f))
            self.faisca.emitir(n, mao, (0, 0, 0.6), dispersao=1.4, vida=(0.15, 0.45), tam=(0.004, 0.009), cor=tuple(_rgb(HALO2)))
        alvo = self.kw.get("alvo")
        if alvo is not None and self.p.intensidade != "discreto":
            if fase == "impacto":
                self.faisca.emitir(int(14 * f), alvo, (0, 0, 1.2), dispersao=2.0, vida=(0.3, 0.8), tam=(0.005, 0.012), cor=tuple(_rgb(HALO2)))
            if fase in ("impacto", "dissipacao", "encerramento"):
                self.fumaca.emitir(1, alvo, (0, 0, 0.4), dispersao=0.15, vida=(1.2, 2.2), tam=(0.07, 0.12), cor=(0.62, 0.64, 0.68), raio_origem=0.05)
        self.faisca.passo(); self.fumaca.passo()

    # ---------------- raio principal
    def _raios(self, ctx):
        alvo = self.kw.get("alvo")
        if alvo is None or self.p.intensidade == "discreto" or not ctx.personagem:
            return []
        fase, _ = self.fases.em(self.tl(ctx))
        if fase not in ("uso", "impacto"):
            return []
        semente = self.p.semente * 1000 + ctx.quadro // self.redesenho
        rng = np.random.default_rng(semente); mao = CT.rig_mundo(ctx, self.mao); out = []
        n = 3 if self.p.intensidade == "extremo" else 1
        for i in range(n):
            fim = np.asarray(alvo, float) + (rng.normal(0, 0.25, 3) * [1, 1, 0] if i else 0)
            out += CV.fractal(mao, fim, rng, niveis=6, desvio=0.17 * self.p.escala, ramos=3 if i == 0 else 1, frac_ramo=0.35)
        self.ultimas_curvas = out; self.ultimo_redesenho = semente
        return out

    # ---------------- arcos curtos pelo contorno do corpo (tela, 2D)
    def _arcos_corpo(self, ctx, tela, forca):
        alfa = getattr(ctx.P, "ultimo_alfa_personagem", None)
        if alfa is None or forca <= 0.02:
            return
        pq = cv2.resize((alfa > 0.5).astype(np.uint8), (alfa.shape[1] // 2, alfa.shape[0] // 2), interpolation=cv2.INTER_NEAREST)
        cont, _ = cv2.findContours(pq, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cont:
            return
        c = max(cont, key=len)[:, 0, :].astype(np.float32) * 2.0
        if len(c) < 40:
            return
        rng = np.random.default_rng(self.p.semente * 77 + ctx.quadro // self.redesenho)
        n_arcos = int(round({"discreto": 3, "moderado": 4, "extremo": 6}[self.p.intensidade] * min(1.0, forca)))
        centro = c.mean(axis=0); s = skia.Surface(ctx.P.W, ctx.P.H); cv = s.getCanvas(); cv.clear(0)
        alt = c[:, 1].max() - c[:, 1].min(); w = max(1.0, alt * 0.004)
        h, nu = _rgb(HALO), _rgb(NUCLEO)
        for _ in range(n_arcos):
            i0 = int(rng.integers(0, len(c))); L = int(rng.uniform(0.05, 0.12) * len(c))
            seg = c[[(i0 + j) % len(c) for j in range(0, L, max(1, L // 10))]]
            fora = seg - centro; fora /= (np.linalg.norm(fora, axis=1, keepdims=True) + 1e-6)
            pts = seg + fora * rng.uniform(2, 10, (len(seg), 1)) + rng.normal(0, w * 2.5, seg.shape)
            path = skia.Path(); path.moveTo(*pts[0])
            for q in pts[1:]:
                path.lineTo(*q)
            for larg, cor, a, borra in ((w * 5, h, 0.35, w * 2), (w, nu, 0.95, 0)):
                p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=larg, StrokeJoin=skia.Paint.kRound_Join,
                               Color4f=skia.Color4f(*[float(v) for v in cor], float(a * min(1.0, forca))))
                if borra:
                    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, borra))
                p.setBlendMode(skia.BlendMode.kPlus); cv.drawPath(path, p)
        img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
        tela.imagem(None, img[..., :3], ctx.personagem["pe_tela"][3] - 0.05)

    # ---------------- ganchos do núcleo
    def _brilho_mao(self, ctx):
        fase, x = self.fases.em(self.tl(ctx))
        return 0.0 if fase is None else self.forca(ctx) * (0.85 + 0.15 * ((ctx.quadro // self.redesenho) % 2))   # cintila pouco (segurança)

    def luzes(self, ctx):
        if not self.ativo(ctx) or not ctx.personagem:
            return []
        f = self._brilho_mao(ctx); fase, _ = self.fases.em(self.tl(ctx))
        out = [{"pos": tuple(CT.rig_mundo(ctx, self.mao)), "cor": tuple(_rgb(HALO)), "forca": 0.7 * f * (1.6 if self.p.intensidade == "extremo" else 1.0), "raio": 0.3}]
        alvo = self.kw.get("alvo")
        if alvo is not None and self.p.intensidade != "discreto" and fase in ("uso", "impacto"):
            out.append({"pos": tuple(np.asarray(alvo) + [0, 0, 0.3]), "cor": tuple(_rgb(HALO)), "forca": (1.2 if fase == "uso" else 2.4) * f, "raio": 0.4})
        return out

    def brilho_previsto(self, ctx):
        return sum(L["forca"] for L in self.luzes(ctx)) / 10.0

    def luz_personagem(self, ctx):
        return (HALO, round(0.5 * self.forca(ctx), 3)) if self.ativo(ctx) else None

    def desenhar(self, ctx, onde, tela):
        if self.tl(ctx) < 0 or (not self.ativo(ctx) and onde != "chao"):      # depois do fim, só a marca queimada fica
            return
        zp = ctx.personagem["pe_tela"][3] if ctx.personagem else 1e9; f = self.forca(ctx); tl = self.tl(ctx)
        if onde == "chao":
            alvo = self.kw.get("alvo"); t_imp = self.fases.inicio_de("impacto")
            if alvo is not None and self.kw.get("alvo_no_chao") and self.p.intensidade != "discreto" and tl >= t_imp:
                MK.desenhar(ctx, tela, alvo, (0.55 if self.p.intensidade == "moderado" else 0.9) * self.p.escala, self.tex, alfa=min(1.0, (tl - t_imp) * 6))
            return
        if onde == "atras":
            self.fumaca.desenhar(ctx, tela, "fumaca", 0.8, z_entre=(zp, 1e9)); self.faisca.desenhar(ctx, tela, "faisca", 1.0, z_entre=(zp, 1e9))
            return
        # frente: raios, arcos pelo corpo, faíscas e fumaça mais perto que o personagem
        r = self._raios(ctx)
        if r:
            fase, _ = self.fases.em(tl)
            CV.desenhar(ctx, tela, r, HALO, largura_m=(0.0045 if self.p.intensidade == "extremo" else 0.003) * self.p.escala,
                        forca=min(1.0, f) * (1.0 if fase == "uso" else 1.0), nucleo=NUCLEO)
        self._arcos_corpo(ctx, tela, f)
        x, y, z = CT.rig(ctx, self.mao); u = abs(ctx.personagem["pe_tela"][1] - ctx.personagem["topo_tela"][1]) / 4.0
        tela.mancha(x, y, u * 0.35, _rgb(HALO) * 0.5 * min(1.0, f), 1.0, z - 0.06, "add")      # mão acesa
        tela.mancha(x, y, u * 0.1, _rgb(NUCLEO) * 0.9 * min(1.0, f), 1.0, z - 0.06, "add")
        self.fumaca.desenhar(ctx, tela, "fumaca", 0.8, z_entre=(0, zp)); self.faisca.desenhar(ctx, tela, "faisca", 1.0, z_entre=(0, zp))

    def tremida(self, ctx):
        if self.p.intensidade == "discreto":
            return (0.0, 0.0)
        ti = self.tl(ctx) - self.fases.inicio_de("impacto")
        amp = 0.014 * 1080 * (1.0 if self.p.intensidade == "extremo" else 0.5)
        return TR.tremida(ti, duracao=0.35, amplitude_px=amp, semente=self.p.semente)

    def impacto(self, ctx, alfa):
        if self.p.intensidade != "extremo" or self.kw.get("alvo") is None:
            return None
        ti = self.tl(ctx) - self.fases.inicio_de("impacto")
        if 0 <= ti < 2 / ctx.fps:
            x, y, _, _ = ctx.tela(self.kw["alvo"])
            return IM.quadro_impacto(ctx.P, (x, y), alfa, semente=self.p.semente, fundo="#0e1838", linhas="#2a6f8a")
        return None
