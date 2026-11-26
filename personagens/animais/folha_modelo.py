#!/usr/bin/env python3
"""Folha de modelo do gato e da aranha do EP01 (personagens originais, 2D por código)."""
import sys
from pathlib import Path
import numpy as np, skia, cv2
AQUI = Path(__file__).resolve().parent; sys.path.insert(0, str(AQUI))
import gato as G, aranha as A


def folha(caminho):
    W, H = 2000, 1200
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.ColorSetARGB(255, 238, 234, 226))
    cv.drawLine(0, 560, W, 560, skia.Paint(Color=skia.ColorSetARGB(255, 200, 192, 180), StrokeWidth=2))
    G.desenhar(cv, 260, 540, 440, pose="sentado", pupila=0.15)
    G.desenhar(cv, 760, 540, 440, pose="sentado", direcao=-1, pupila=0.9, olhar=-0.6)
    G.desenhar(cv, 1300, 540, 440, pose="agachado", pupila=1.0, olhar=0.4)
    G.pata(cv, 1780, 300, 200, garras=1.0)
    G.olho(cv, 300, 900, 220, pupila=0.1); G.olho(cv, 800, 900, 220, pupila=0.95)
    A.desenhar(cv, 1250, 1050, 420, fase=0.0); A.desenhar(cv, 1750, 1050, 420, fase=0.25, levantar_frente=1.0)
    img = np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))
    cv2.imwrite(str(caminho), cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))


if __name__ == "__main__":
    folha(AQUI / "folhas" / "folha_gato_aranha.png"); print("ok")
