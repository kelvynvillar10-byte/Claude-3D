#!/usr/bin/env python3
"""Cenografia E1 — FOLHA DE MATERIAIS (mostruário renderizado no Blender, Cycles CPU) + medidas por material.

16 amostras em painéis de 0,9 m (escala real: placas, pedras e ladrilhos no tamanho certo), inclinados para pegar
luz rasante do sol da tarde, com chanfro na borda. Medidas por amostra: saturação média, brilho, variação de
luminância (detalhe/"não chapado") e se a cor média está dentro do esperado.
Saída: cenografia/testes/e1/E1_folha_materiais.png e e1_materiais.json
"""
import json, math, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
OUT = RAIZ / "cenografia" / "testes" / "e1"; OUT.mkdir(parents=True, exist_ok=True)
TMP = RAIZ / "_tmp" / "e1"; TMP.mkdir(parents=True, exist_ok=True)

AMOSTRAS = [   # (rótulo, nome no catálogo, parâmetros)
    ("asfalto", "asfalto", {}), ("asfalto molhado", "asfalto", {"umidade": 0.8}),
    ("concreto (placas)", "concreto", {}), ("calçada portuguesa", "calcada_portuguesa", {}),
    ("ladrilho hidráulico", "ladrilho_hidraulico", {}), ("reboco amarelo-ocre", "reboco", {"cor": "#e3a12f"}),
    ("reboco verde-água", "reboco", {"cor": "#4fae9c"}), ("tijolo à vista", "tijolo", {}),
    ("pastilha", "pastilha", {"cor": "#3fa7d6"}), ("azulejo", "azulejo", {}),
    ("telha cerâmica", "telha_ceramica", {}), ("concreto aparente", "concreto_aparente", {}),
    ("metal + ferrugem", "metal_ferrugem", {}), ("madeira pintada", "madeira", {"pintada": "#c25a36"}),
    ("grama", "grama", {}), ("folhagem", "folhagem", {}),
]
COLS, LIN, PAINEL, PASSO = 4, 4, 0.9, 1.05


def render(amostras=64, lado_px=1600):
    import bpy
    from cenografia.nucleo import materiais as M, geometria as G, luz as L
    bpy.ops.wm.read_factory_settings(use_empty=True); M._CACHE.clear()
    cena = bpy.context.scene; col = G.colecao("mostruario")
    for i, (_, nome, params) in enumerate(AMOSTRAS):
        c, l = i % COLS, i // COLS
        x = (c - (COLS - 1) / 2) * PASSO; z = ((LIN - 1) / 2 - l) * PASSO + 2.0
        o = G.caixa(f"amostra_{i}", (x - PAINEL / 2, -0.04, z - PAINEL / 2), (x + PAINEL / 2, 0.04, z + PAINEL / 2), M.por_nome(nome, **params), col, chanfro=0.025)
        o.rotation_euler = (math.radians(-18), 0, 0)
    G.caixa("fundo", (-4, 0.6, -1), (4, 0.7, 5), M.pintura("#2b2f38", rug=0.9), col)
    L.ceu_e_sol("tarde_dourada")
    camd = bpy.data.cameras.new("cam"); camd.lens = 85; camd.sensor_fit = "VERTICAL"; camd.sensor_height = 24
    cam = bpy.data.objects.new("cam", camd); cena.collection.objects.link(cam); cam.location = (0, -15.5, 2.0); cam.rotation_euler = (math.radians(90), 0, 0)
    cena.camera = cam
    cena.render.engine = "CYCLES"; cena.cycles.device = "CPU"; cena.cycles.samples = amostras; cena.cycles.use_denoising = True
    cena.render.resolution_x = cena.render.resolution_y = lado_px; cena.render.resolution_percentage = 100
    cena.view_settings.view_transform = "AgX"; cena.view_settings.exposure = -0.6
    cena.render.image_settings.file_format = "PNG"; cena.render.filepath = str(TMP / "folha_materiais.png")
    t = time.time(); bpy.ops.render.render(write_still=True)
    # centro de cada amostra na imagem (para medir)
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    bpy.context.view_layer.update(); centros = []
    for i in range(len(AMOSTRAS)):
        o = bpy.data.objects[f"amostra_{i}"]; v = world_to_camera_view(cena, cam, o.matrix_world @ Vector((0, 0, 0)))
        centros.append((v.x * lado_px, (1 - v.y) * lado_px))
    return time.time() - t, centros


def medir_e_rotular(centros, lado_px):
    img = cv2.cvtColor(cv2.imread(str(TMP / "folha_materiais.png")), cv2.COLOR_BGR2RGB)
    meio = int(0.30 * lado_px / COLS * 1.0); res = {}
    for (rot, _, _), (cx, cy) in zip(AMOSTRAS, centros):
        rec = img[int(cy) - meio:int(cy) + meio, int(cx) - meio:int(cx) + meio]
        hsv = cv2.cvtColor(rec, cv2.COLOR_RGB2HSV); g = cv2.cvtColor(rec, cv2.COLOR_RGB2GRAY).astype(np.float32)
        detalhe = float(cv2.Laplacian(g, cv2.CV_32F).std())
        res[rot] = {"saturacao_pct": round(100 * hsv[..., 1].mean() / 255, 1), "brilho_pct": round(100 * g.mean() / 255, 1),
                    "variacao_luminancia_pct": round(100 * g.std() / 255, 1), "detalhe_laplaciano": round(detalhe, 1)}
    a = np.dstack([img, np.full(img.shape[:2], 255, np.uint8)]).copy(); s = skia.Surface(a); c = s.getCanvas()
    f = skia.Font(skia.Typeface.MakeFromFile(str(RAIZ / "assets/fontes/Nunito-ExtraBold.ttf")), 26)
    for (rot, _, _), (cx, cy) in zip(AMOSTRAS, centros):
        w = f.measureText(rot); y = cy + 0.25 * lado_px / COLS
        c.drawRoundRect(skia.Rect.MakeXYWH(cx - w / 2 - 10, y - 26, w + 20, 36), 8, 8, skia.Paint(AntiAlias=True, Color=0xCC1F2A44))
        c.drawString(rot, cx - w / 2, y, f, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF))
    out = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3]
    cv2.imwrite(str(OUT / "E1_folha_materiais.png"), cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    return res


if __name__ == "__main__":
    t, centros = render()
    res = {"render_s": round(t, 1), "amostras": medir_e_rotular(centros, 1600)}
    (OUT / "e1_materiais.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))
