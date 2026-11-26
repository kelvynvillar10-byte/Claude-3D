"""Proteção do ROSTO e da ESTAMPA do Heitor: na camada da frente, o efeito pode cobrir no máximo 'LIMITE' (35 %) dessas
áreas. As áreas vêm da posição do personagem (pés e topo na tela) e das proporções do rig (4 cabeças):
rosto = elipse no quarto de cima; estampa = elipse no peito (só nas vistas frente e 3/4)."""
import numpy as np

LIMITE = 0.35


def mascaras(ctx):
    pc = ctx.personagem
    x, y, _, _ = pc["pe_tela"]; _, yt, _, _ = pc["topo_tela"]; alt = y - yt
    H, W = ctx.P.H, ctx.P.W; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rosto = (((xx - x) / (0.15 * alt)) ** 2 + ((yy - (yt + 0.13 * alt)) / (0.14 * alt)) ** 2) <= 1
    estampa = np.zeros_like(rosto)
    if pc.get("vista", "frente") in ("frente", "tres_quartos"):
        estampa = (((xx - x) / (0.15 * alt)) ** 2 + ((yy - (yt + 0.37 * alt)) / (0.07 * alt)) ** 2) <= 1
    # personagem em voo (corpo inclinado, fora do chão): o próprio poder informa onde estão o rosto e a estampa
    if pc.get("rosto_elipse"):
        ex, ey, rx, ry = pc["rosto_elipse"]; rosto = (((xx - ex) / rx) ** 2 + ((yy - ey) / ry) ** 2) <= 1
    if "estampa_elipse" in pc:
        estampa = np.zeros_like(rosto)
        if pc["estampa_elipse"]:
            ex, ey, rx, ry = pc["estampa_elipse"]; estampa = (((xx - ex) / rx) ** 2 + ((yy - ey) / ry) ** 2) <= 1
    return rosto, estampa


def proteger(camada, ctx):
    rosto, estampa = mascaras(ctx); m = (rosto | estampa)
    if not m.any():
        return camada
    total = camada["rgba"][..., 3] + camada["add"].max(axis=2)          # cobertura somada (cobrir + brilhar)
    fator = np.where(m & (total > LIMITE), LIMITE / np.maximum(total, 1e-6), 1.0).astype(np.float32)
    camada["rgba"] *= fator[..., None]; camada["add"] *= fator[..., None]
    return camada


def cobertura(camada, ctx):
    """Quanto o efeito cobre rosto e estampa (média de alfa + brilho somado, 0..1)."""
    if camada is None:
        return {"rosto": 0.0, "estampa": 0.0}
    rosto, estampa = mascaras(ctx)
    cob = np.clip(camada["rgba"][..., 3] + camada["add"].max(axis=2), 0, 1)
    return {"rosto": round(float(cob[rosto].max()) if rosto.any() else 0.0, 3), "estampa": round(float(cob[estampa].max()) if estampa.any() else 0.0, 3)}
