"""Segurança para fotossensíveis: limite de FLASHES por segundo.

- Governador: a Mesa informa, a cada quadro, o brilho previsto dos efeitos. Se uma nova inversão forte de brilho
  (sobe→desce ou desce→sobe) faria passar de 'limite' flashes no último segundo, o ganho segura o brilho no valor
  anterior (o efeito continua, sem piscar).
- analisar_flashes(): conferência no vídeo pronto, quadro a quadro, com a regra simplificada de "flash geral" (WCAG
  2.3.1): par de variações opostas de luminância relativa ≥ 10 % do máximo, com o lado escuro abaixo de 0,8, em mais de
  25 % da tela. Conta quantos ocorrem em qualquer janela de 1 s.
"""
import numpy as np


class Governador:
    def __init__(self, fps=30, limite=3, delta=0.1):
        self.fps, self.limite, self.delta = fps, limite, delta
        self.ultimo = None; self.direcao = 0; self.eventos = []; self.saida_anterior = 0.0

    def ganho(self, brilho, t):
        if self.ultimo is None:
            self.ultimo = brilho; self.saida_anterior = brilho; return 1.0
        d = brilho - self.saida_anterior
        if abs(d) >= self.delta:
            dirn = 1 if d > 0 else -1
            if self.direcao and dirn != self.direcao:          # inversão = meio flash
                recentes = [e for e in self.eventos if t - e < 1.0]
                if len(recentes) >= 2 * self.limite:
                    return (self.saida_anterior / brilho) if brilho > 1e-6 else 1.0   # segura
                self.eventos = recentes + [t]
            self.direcao = dirn
        self.saida_anterior = brilho
        return 1.0


def luminancia_relativa(img_u8):
    x = img_u8.astype(np.float32) / 255.0
    x = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]


def analisar_flashes(quadros_lum, fps=30, delta=0.1, area=0.25):
    """quadros_lum: lista de mapas de luminância relativa (reduzidos). Retorna o máximo de flashes em 1 s."""
    trans = []          # (quadro, direção) de variações grandes em área suficiente
    for i in range(1, len(quadros_lum)):
        a, b = quadros_lum[i - 1], quadros_lum[i]
        sobe = ((b - a) >= delta) & (np.minimum(a, b) < 0.8); desce = ((a - b) >= delta) & (np.minimum(a, b) < 0.8)
        if sobe.mean() > area:
            trans.append((i, 1))
        elif desce.mean() > area:
            trans.append((i, -1))
    flashes = []; i = 0                 # flash = PAR de variações opostas (sobe+desce): pares sem sobreposição
    while i < len(trans) - 1:
        if trans[i][1] != trans[i + 1][1]:
            flashes.append(trans[i + 1][0]); i += 2
        else:
            i += 1
    pior = 0
    for k in flashes:
        pior = max(pior, sum(1 for m in flashes if k <= m < k + fps))
    return {"flashes_total": len(flashes), "max_flashes_em_1s": pior}
