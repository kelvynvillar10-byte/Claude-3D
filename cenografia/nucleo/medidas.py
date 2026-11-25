"""Cenografia — medidas de imagem para QA (E0).

As mesmas fórmulas de tools/analise/analyze.py (auditoria das referências), aplicadas a um quadro:
brilho (Y), saturação (S), contraste (C), vinheta (cantos/centro) e cor Lab das sombras (20 % mais escuros)
e das altas luzes (15 % mais claros). Alvos do skill, seção 5: Y 46–56 %, S 35–46 %, contraste ~17 %,
vinheta 57–66 %, sombras a≈+7 b≈−10, altas luzes b≈+19.
"""
import numpy as np, cv2


def quadro(rgb):
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    sm = cv2.resize(bgr, (270, 480), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    H_, W_ = g.shape; c = g[H_ // 3:2 * H_ // 3, W_ // 3:2 * W_ // 3].mean(); k = 40
    cantos = np.mean([g[:k, :k].mean(), g[:k, -k:].mean(), g[-k:, :k].mean(), g[-k:, -k:].mean()])
    lab = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float)
    L = lab[:, 0] * 100 / 255; a = lab[:, 1] - 128; b = lab[:, 2] - 128
    sh = L < np.percentile(L, 20); hi = L > np.percentile(L, 85)
    return {"brilho_pct": round(100 * g.mean() / 255, 1), "saturacao_pct": round(100 * hsv[..., 1].mean() / 255, 1),
            "contraste_pct": round(100 * g.std() / 255, 1), "vinheta_pct": round(100 * cantos / max(c, 1), 1),
            "sombras_a": round(float(a[sh].mean()), 1), "sombras_b": round(float(b[sh].mean()), 1),
            "altas_luzes_b": round(float(b[hi].mean()), 1)}


ALVOS = {"brilho_pct": (46, 56), "saturacao_pct": (35, 46), "vinheta_pct": (57, 66)}


def comparar(a, b):
    """Diferença entre dois quadros RGB uint8 do mesmo tamanho."""
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return {"erro_medio_8bit": round(float(d.mean()), 2), "pixels_dif_maior_12_pct": round(100 * float((d > 12).mean()), 2),
            "psnr_db": round(float(10 * np.log10(255 ** 2 / max(mse, 1e-9))), 1)}, d
