#!/usr/bin/env python3
"""Folha ANTES × DEPOIS dos ombros (4 vistas + braços erguidos, abertos e caminhando)."""
import sys
from pathlib import Path
import numpy as np, skia, cv2
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "rig_v2" / "codigo")); sys.path.insert(0, str(AQUI))
import heitor_v2 as HV, animacao as AN, ombros as OB

CASOS = [("frente", {}, "neutro"), ("tres_quartos", {}, "alegria"), ("perfil", {}, "neutro"), ("costas", {}, None),
         ("frente", {"braco_d": 160, "braco_e": -160}, "surpresa"), ("frente", {"braco_d": 80, "braco_e": -80}, "alegria"),
         ("perfil", "caminhada", "neutro")]


def linha(cv, y0, rotulo):
    for i, (vista, extra, rosto) in enumerate(CASOS):
        if extra == "caminhada":
            pose, _ = AN.pose_locomocao(0.2, vista=vista, tipo="caminhada")
        else:
            pose = HV.pose_base(vista); pose.update(extra)
        HV.desenhar(cv, 150 + i * 270, y0 + 560, 520, vista=vista, direcao=1, pose=pose, rosto=rosto)
    f = skia.Font(skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "Nunito-ExtraBold.ttf")), 40)
    cv.drawString(rotulo, 20, y0 + 40, f, skia.Paint(AntiAlias=True, Color=0xFF1F2A44))


s = skia.Surface(1900, 1260); cv = s.getCanvas(); cv.clear(0xFFEEEAE2)
linha(cv, 0, "ANTES (rig v2 aprovado)")
with OB.ativar():
    linha(cv, 620, "DEPOIS (proposta: ombros arredondados)")
a = np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))
cv2.imwrite(str(AQUI / "ombros_antes_depois.png"), cv2.cvtColor(a, cv2.COLOR_RGBA2BGR)); print("ok")
