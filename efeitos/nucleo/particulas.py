"""Partículas DETERMINÍSTICAS por semente, em metros no mundo: gravidade, vento, arrasto, turbulência e quique no chão.

Simulação em passo fixo (1/fps, com subpassos): o estado no quadro N é sempre o mesmo para a mesma semente, em
qualquer máquina. Desenho: cada partícula vira uma mancha na tela com tamanho pela profundidade (perspectiva real) e
profundidade própria (o cenário mais perto a cobre). Estilos: "faisca" (brilho somado, com rastro de movimento),
"poeira" e "fumaca" (cobrem, crescem e somem), "brilho" (pontos de luz).
"""
import math
import numpy as np

G = np.array([0.0, 0.0, -9.81])


class Sistema:
    def __init__(self, semente, gravidade=1.0, vento=(0.0, 0.0, 0.0), arrasto=0.0, turbulencia=0.0, chao_z=None,
                 restituicao=0.35, atrito=0.6, fps=30, subpassos=4):
        self.rng = np.random.default_rng(semente); self.g = G * gravidade; self.vento = np.asarray(vento, float)
        self.k = arrasto; self.turb = turbulencia; self.chao = chao_z; self.rest = restituicao; self.atr = atrito
        self.dt = 1.0 / fps / subpassos; self.sub = subpassos; self.t = 0.0; self.n_quadro = 0
        self.pos = np.zeros((0, 3)); self.vel = np.zeros((0, 3)); self.idade = np.zeros(0); self.vida = np.zeros(0)
        self.tam = np.zeros(0); self.cor = np.zeros((0, 3)); self.ant = np.zeros((0, 3)); self.fase = np.zeros(0)

    def emitir(self, n, origem, vel, dispersao=0.5, vida=(0.6, 1.2), tam=(0.01, 0.03), cor=(1.0, 0.8, 0.4), raio_origem=0.0):
        if n <= 0:
            return
        r = self.rng
        o = np.asarray(origem, float) + r.normal(0, raio_origem, (n, 3)) * (raio_origem > 0)
        v = np.asarray(vel, float) + r.normal(0, dispersao, (n, 3))
        c = np.clip(np.asarray(cor, float) * r.uniform(0.85, 1.1, (n, 1)), 0, 1.5)
        self.pos = np.vstack([self.pos, o]); self.vel = np.vstack([self.vel, v]); self.ant = np.vstack([self.ant, o])
        self.idade = np.concatenate([self.idade, np.zeros(n)]); self.vida = np.concatenate([self.vida, r.uniform(*vida, n)])
        self.tam = np.concatenate([self.tam, r.uniform(*tam, n)]); self.cor = np.vstack([self.cor, c])
        self.fase = np.concatenate([self.fase, r.uniform(0, 6.28, n)])

    def _turbulencia(self, p, t):
        """Campo suave e determinístico (soma de senos defasados) — vento irregular sem ruído aleatório por quadro."""
        a = self.turb
        return a * np.stack([np.sin(1.7 * p[:, 1] + 1.3 * t) + 0.5 * np.sin(3.1 * p[:, 2] - 0.7 * t),
                             np.sin(1.9 * p[:, 2] + 1.1 * t) + 0.5 * np.sin(2.7 * p[:, 0] + 0.9 * t),
                             0.6 * np.sin(1.5 * p[:, 0] - 1.7 * t) + 0.3 * np.sin(2.3 * p[:, 1] + 0.5 * t)], axis=1)

    def passo(self):
        """Avança um quadro (com subpassos)."""
        if len(self.pos):
            self.ant = self.pos.copy()
        for _ in range(self.sub):
            if not len(self.pos):
                break
            acc = self.g + self.k * (self.vento - self.vel)
            if self.turb:
                acc = acc + self._turbulencia(self.pos, self.t)
            self.vel = self.vel + acc * self.dt; self.pos = self.pos + self.vel * self.dt
            if self.chao is not None:
                baixo = self.pos[:, 2] < self.chao
                if baixo.any():
                    self.pos[baixo, 2] = self.chao + (self.chao - self.pos[baixo, 2]) * self.rest
                    self.vel[baixo, 2] = -self.vel[baixo, 2] * self.rest; self.vel[baixo, :2] *= self.atr
            self.idade = self.idade + self.dt; self.t += self.dt
        vivo = self.idade < self.vida
        if not vivo.all():
            for k in ("pos", "vel", "idade", "vida", "tam", "cor", "ant", "fase"):
                setattr(self, k, getattr(self, k)[vivo])
        self.n_quadro += 1

    def desenhar(self, ctx, tela, estilo="faisca", ganho=1.0, z_entre=(0.0, 1e9)):
        """z_entre: só as partículas nessa faixa de profundidade (a Mesa desenha 'atras' e 'frente' do personagem)."""
        if not len(self.pos) or ganho <= 0:
            return 0
        n = 0; f = ctx.P.f
        for i in range(len(self.pos)):
            x, y, s, z = ctx.tela(self.pos[i])
            if z <= 0.1 or not (z_entre[0] <= z < z_entre[1]):
                continue
            vida = self.idade[i] / self.vida[i]; r = max(0.6, self.tam[i] * f / z * s)
            if estilo == "faisca":
                a = ganho * (1 - vida) ** 0.7; x0, y0, _, _ = ctx.tela(self.ant[i]); m = max(1, int(math.hypot(x - x0, y - y0) / max(r, 1)))
                for k in range(m + 1):     # rastro de movimento: manchas ao longo do deslocamento do quadro
                    u = k / max(m, 1); tela.mancha(x0 + (x - x0) * u, y0 + (y - y0) * u, r, self.cor[i] * a, 0.35 + 0.65 * u, z, "add")
                tela.mancha(x, y, r * 2.6, self.cor[i] * a * 0.25, 1.0, z, "add")       # halo
            elif estilo in ("poeira", "fumaca"):
                cresce = 1 + (2.5 if estilo == "fumaca" else 1.2) * vida
                a = ganho * (0.5 if estilo == "fumaca" else 0.3) * math.sin(math.pi * min(1.0, vida * 1.1)) ** 0.8
                for k in range(3):        # 3 sub-manchas defasadas: borda irregular (não é bola)
                    ang = self.fase[i] + k * 2.1; dd = r * cresce * 0.35
                    tela.mancha(x + dd * math.cos(ang), y + dd * math.sin(ang) * 0.6, r * cresce * (0.8 + 0.15 * k), self.cor[i], a * 0.5, z, "alpha")
            elif estilo == "pedra":       # lasca de pedra/terra: disco sólido que cobre, com face clara
                tela.mancha(x, y, max(1.2, r), self.cor[i], 1.0, z, "alpha", perfil="disco")
                tela.mancha(x - r * 0.25, y - r * 0.3, max(0.8, r * 0.45), np.clip(self.cor[i] * 1.5, 0, 1), 0.8, z, "alpha", perfil="disco")
            else:   # brilho
                a = ganho * math.sin(math.pi * vida); tela.mancha(x, y, r, self.cor[i] * a, 1.0, z, "add")
                tela.mancha(x, y, r * 3, self.cor[i] * a * 0.2, 1.0, z, "add")
            n += 1
        return n
