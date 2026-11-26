"""TREMIDA de câmera (padrão do skill): amplitude ~1,4 % do quadro, 0,25–0,6 s, decaindo. Determinística por semente.
Retorna o deslocamento do recorte (px), que usa a margem da placa (não aparece borda)."""
import math


def tremida(t, duracao=0.4, amplitude_px=15.0, semente=1):
    if t < 0 or t > duracao:
        return 0.0, 0.0
    dec = (1 - t / duracao) ** 1.5; f1, f2 = 23.0 + semente % 5, 31.0 + semente % 7
    return (amplitude_px * dec * math.sin(2 * math.pi * f1 * t + semente), amplitude_px * dec * 0.7 * math.sin(2 * math.pi * f2 * t + 2 * semente))
