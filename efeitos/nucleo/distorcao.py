"""DISTORÇÃO de tela (aplicada ao quadro composto, personagem incluído): onda de choque (anel que se expande e
empurra a imagem) e calor (tremulação vertical acima de uma fonte quente). Retornam (dx, dy) em px da placa."""
import numpy as np


def onda_de_choque(P, centro_xy, raio_px, largura_px, amplitude_px, achatamento=0.45):
    """Anel elíptico (achatado: o chão em perspectiva) que desloca a imagem para fora."""
    cx, cy = centro_xy; u, v = P.u + P.cx - cx, (P.v + P.cy - cy) / achatamento
    d = np.sqrt(u * u + v * v) + 1e-6
    k = amplitude_px * np.exp(-((d - raio_px) / max(largura_px, 1.0)) ** 2)
    return (-k * u / d).astype(np.float32), (-k * v / d * achatamento).astype(np.float32)


def calor(P, base_xy, largura_px, altura_px, amplitude_px, t):
    """Tremulação acima de uma fonte (sobe e some com a altura)."""
    bx, by = base_xy; x = P.u + P.cx; y = P.v + P.cy
    sobe = np.clip((by - y) / max(altura_px, 1.0), 0, 1); lado = np.exp(-((x - bx) / max(largura_px / 2, 1.0)) ** 2)
    m = (sobe > 0) * (1 - sobe) * lado
    dx = amplitude_px * m * np.sin(y * 0.09 + t * 11.0 + np.sin(x * 0.05) * 2.0)
    dy = amplitude_px * 0.5 * m * np.sin(x * 0.07 - t * 7.0)
    return dx.astype(np.float32), dy.astype(np.float32)
