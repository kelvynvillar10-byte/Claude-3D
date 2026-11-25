#!/usr/bin/env python3
"""Heitor rig v2 — cenário do TESTE T8 (bpy, Cycles CPU).

Um canto de quarto/estudo simples, low-poly, em cores que conversam com a paleta do Heitor: parede creme, piso de
madeira, rodapé, mesa de madeira, estante com livros e planta, janela com luz quente e o pôster "MODO CURIOSO"
(textura do piloto 01, já aprovada no QA — ID-004).
Câmera fixa, horizontal, na altura de 0,90 m (35 mm, sensor vertical 24 mm). O personagem fica no plano y = D.
Saída (recursos/cena_t8/): fundo.png (1080×1920) e ancoras.json (projeção 3D → 2D para posicionar o Heitor 2D).

Uso: .venv/bin/python codigo/cena_t8_blender.py [--amostras 64] [--rapido]
"""
import json, math, sys, time
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
OUT = AQUI.parent / "recursos" / "cena_t8"; OUT.mkdir(parents=True, exist_ok=True)
POSTER_IMG = RAIZ / "pilotos" / "piloto_01_ultimo_homem" / "recursos" / "marca" / "poster_MODO_CURIOSO.png"
W, Hpx = 1080, 1920
AMOSTRAS = int(sys.argv[sys.argv.index("--amostras") + 1]) if "--amostras" in sys.argv else 64
if "--rapido" in sys.argv:
    W, Hpx, AMOSTRAS = 270, 480, 8
CAM_Z = 0.90            # altura da câmera (m)
D = 3.9                 # profundidade do plano do personagem (m)
ALT_HEITOR = 1.40       # altura do Heitor (m) → H = 0,35 m
MESA = dict(x0=0.22, x1=0.82, y0=3.62, y1=4.22, z=0.68)

bpy.ops.wm.read_factory_settings(use_empty=True)
cena = bpy.context.scene; col = cena.collection
_mats = {}


def lin(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def mat(nome, cor=None, rug=0.7, img=None, emit=None, forca=1.0, ruido=0.0):
    if nome in _mats:
        return _mats[nome]
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rug
    if img:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(img))
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    elif ruido:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0
        rp = nt.nodes.new("ShaderNodeValToRGB"); c0 = lin(cor)
        rp.color_ramp.elements[0].color = tuple(x * (1 - ruido) for x in c0[:3]) + (1,); rp.color_ramp.elements[1].color = c0
        nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = lin(cor)
    if emit:
        b.inputs["Emission Color"].default_value = lin(emit); b.inputs["Emission Strength"].default_value = forca
    _mats[nome] = m
    return m


def obj(nome, bm, m):
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nome, me); o.data.materials.append(m); col.objects.link(o); return o


def caixa(nome, c0, c1, m, chanfro=0.0):
    """Caixa pelos cantos (x0,y0,z0)–(x1,y1,z1)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    dim = [b - a for a, b in zip(c0, c1)]
    for v in bm.verts:
        v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], v.co.z * dim[2]))
    o = obj(nome, bm, m); o.location = [(a + b) / 2 for a, b in zip(c0, c1)]
    if chanfro:
        bv = o.modifiers.new("chanfro", "BEVEL"); bv.width = chanfro; bv.segments = 2
    return o


def quadro_parede(nome, cx, cz, w, h, y, m):
    """Plano vertical (de frente para a câmera) com UV 0–1, na parede y."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((cx - w / 2, y, cz - h / 2)), bm.verts.new((cx + w / 2, y, cz - h / 2)),
          bm.verts.new((cx + w / 2, y, cz + h / 2)), bm.verts.new((cx - w / 2, y, cz + h / 2))]
    f = bm.faces.new(vs)
    for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = (u, v)
    return obj(nome, bm, m)


def cilindro(nome, c, raio, alt, m, lados=20):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=raio, radius2=raio, depth=alt)
    o = obj(nome, bm, m); o.location = c; return o


# ------------------------------------------------------------------ cenário
PAREDE_Y = 5.6
caixa("piso", (-4, 0, -0.1), (4, 9, 0), mat("piso", "#A06E45", 0.55, ruido=0.12))
for i in range(14):   # juntas das tábuas (linhas horizontais que dão profundidade)
    y = 2.2 + i * 0.26
    caixa(f"junta{i}", (-4, y, 0.0), (4, y + 0.008, 0.0015), mat("junta", "#7E5534", 0.6))
caixa("parede", (-4, PAREDE_Y, 0), (4, PAREDE_Y + 0.1, 3.2), mat("parede", "#E4CFAA", 0.9, ruido=0.04))
caixa("rodape", (-4, PAREDE_Y - 0.02, 0), (4, PAREDE_Y, 0.11), mat("rodape", "#F7F3EA", 0.5))
# janela (esquerda): moldura + vidro emissivo quente
caixa("jan_vidro", (-1.25, PAREDE_Y - 0.005, 1.0), (-0.45, PAREDE_Y + 0.0, 2.1), mat("vidro", "#FFE7B8", 0.2, emit="#FFE2AE", forca=1.3))
MOLD = mat("moldura", "#F7F3EA", 0.5)
# peças da moldura sem sobreposição de volumes (sobreposição gerava quadrados escuros nos cantos)
for i, (a, b, prof) in enumerate((((-1.31, 0.94), (-0.39, 1.0), 0.06), ((-1.31, 2.1), (-0.39, 2.16), 0.06),
                                  ((-1.31, 1.0), (-1.25, 2.1), 0.058), ((-0.45, 1.0), (-0.39, 2.1), 0.058),
                                  ((-0.88, 1.0), (-0.86, 1.54), 0.05), ((-0.88, 1.56), (-0.86, 2.1), 0.05),
                                  ((-1.25, 1.54), (-0.45, 1.56), 0.052))):
    caixa(f"mold{i}", (a[0], PAREDE_Y - prof, a[1]), (b[0], PAREDE_Y, b[1]), MOLD)
caixa("peitoril", (-1.36, PAREDE_Y - 0.14, 0.9), (-0.34, PAREDE_Y, 0.95), MOLD)
# pôster MODO CURIOSO (ID-004) — textura do piloto 01
# alto na parede: a cabeça, a bola erguida e a mão que acena nunca passam na frente da marca (ID-004)
quadro_parede("poster", 0.05, 2.12, 0.50, 0.714, PAREDE_Y - 0.012, mat("poster", rug=0.7, img=POSTER_IMG))
# estante (direita) com livros e planta
MAD = mat("madeira", "#8A5A3B", 0.6, ruido=0.1)
for z in (0.9, 1.35):
    caixa("prat", (0.55, PAREDE_Y - 0.28, z), (1.35, PAREDE_Y, z + 0.035), MAD)
cores = ["#3E7BD6", "#FFC21F", "#E8722C", "#2F9E6E", "#1F2A44", "#C9473B", "#6B5BD6"]
x = 0.6
for i in range(9):
    w = 0.045 + 0.02 * ((i * 7) % 3); h = 0.22 + 0.05 * ((i * 5) % 3)
    caixa(f"livro{i}", (x, PAREDE_Y - 0.24, 0.935), (x + w, PAREDE_Y - 0.06, 0.935 + h), mat(f"livro{i}", cores[i % len(cores)], 0.6))
    x += w + 0.008
cilindro("vaso", (1.1, PAREDE_Y - 0.15, 1.385 + 0.08), 0.07, 0.16, mat("vaso", "#E8722C", 0.5))
FOLHA = mat("folha", "#2F9E6E", 0.6)
for i, (dx, dz, r) in enumerate(((0, 0.2, 0.09), (-0.07, 0.16, 0.07), (0.07, 0.17, 0.07), (0.02, 0.27, 0.06))):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    o = obj(f"folha{i}", bm, FOLHA); o.location = (1.1 + dx, PAREDE_Y - 0.15, 1.385 + dz)
# mesa (lado direito do plano do personagem)
caixa("tampo", (MESA["x0"], MESA["y0"], MESA["z"] - 0.04), (MESA["x1"], MESA["y1"], MESA["z"]), MAD, chanfro=0.008)
for (px, py) in ((MESA["x0"] + 0.04, MESA["y0"] + 0.04), (MESA["x1"] - 0.08, MESA["y0"] + 0.04),
                 (MESA["x0"] + 0.04, MESA["y1"] - 0.08), (MESA["x1"] - 0.08, MESA["y1"] - 0.08)):
    caixa("perna", (px, py, 0), (px + 0.04, py + 0.04, MESA["z"] - 0.04), mat("perna", "#6B4630", 0.6))
cilindro("caneca", (0.68, 4.05, MESA["z"] + 0.05), 0.04, 0.1, mat("caneca", "#3E7BD6", 0.4))
caixa("livro_mesa", (0.5, 3.95, MESA["z"]), (0.66, 4.17, MESA["z"] + 0.03), mat("livro_mesa", "#FFC21F", 0.6))

# ------------------------------------------------------------------ luz e câmera
mundo = bpy.data.worlds.new("mundo"); cena.world = mundo; mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs["Color"].default_value = lin("#DCE6F2")
mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38
sol = bpy.data.lights.new("janela", "AREA"); sol.energy = 320; sol.size = 1.0; sol.color = lin("#FFE2B8")[:3]
so = bpy.data.objects.new("janela", sol); col.objects.link(so); so.visible_camera = False; so.location = (-0.85, PAREDE_Y - 0.4, 1.6)
so.rotation_euler = (Vector((0.2, 3.9, 0.3)) - Vector(so.location)).to_track_quat("-Z", "Y").to_euler()
pre = bpy.data.lights.new("preenchimento", "AREA"); pre.energy = 170; pre.size = 3.0; pre.color = lin("#E9F0FF")[:3]
po = bpy.data.objects.new("preenchimento", pre); col.objects.link(po); po.visible_camera = False; po.location = (0.8, 0.8, 2.6)
po.rotation_euler = (Vector((0.0, 4.2, 0.6)) - Vector(po.location)).to_track_quat("-Z", "Y").to_euler()
camd = bpy.data.cameras.new("cam"); camd.lens = 35; camd.sensor_fit = "VERTICAL"; camd.sensor_height = 24
cam = bpy.data.objects.new("cam", camd); col.objects.link(cam); cam.location = (0.0, 0.0, CAM_Z)
cam.rotation_euler = (math.radians(90), 0, 0); cena.camera = cam

cena.render.engine = "CYCLES"; cena.cycles.device = "CPU"; cena.cycles.samples = AMOSTRAS; cena.cycles.use_denoising = True
cena.cycles.max_bounces = 6
cena.render.resolution_x, cena.render.resolution_y, cena.render.resolution_percentage = W, Hpx, 100
cena.render.image_settings.file_format = "PNG"; cena.render.image_settings.color_mode = "RGB"
cena.view_settings.view_transform = "AgX"
try:
    cena.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
cena.view_settings.exposure = -0.55


def projeta(p):
    bpy.context.view_layer.update()
    v = world_to_camera_view(cena, cam, Vector(p))
    return [v.x * W, (1 - v.y) * Hpx]


ancoras = {"W": W, "H": Hpx, "D_m": D, "alt_heitor_m": ALT_HEITOR, "cam_z_m": CAM_Z,
           "pe_x0": projeta((0.0, D, 0.0)), "cabeca_x0": projeta((0.0, D, ALT_HEITOR)), "pe_x1": projeta((1.0, D, 0.0)),
           "mesa": {k: v for k, v in MESA.items()},
           "mesa_tampo_no_plano_x0": projeta((MESA["x0"], D, MESA["z"])), "mesa_tampo_no_plano_x1": projeta((MESA["x1"], D, MESA["z"])),
           "parede_rodape": projeta((0.0, PAREDE_Y, 0.0)),
           "poster_cantos": [projeta((0.05 - 0.25, PAREDE_Y, 2.12 - 0.357)), projeta((0.05 + 0.25, PAREDE_Y, 2.12 + 0.357))]}
ancoras["px_por_m"] = ancoras["pe_x1"][0] - ancoras["pe_x0"][0]
ancoras["altura_heitor_px"] = ancoras["pe_x0"][1] - ancoras["cabeca_x0"][1]
t0 = time.time()
cena.render.filepath = str(OUT / ("fundo_rapido.png" if "--rapido" in sys.argv else "fundo.png"))
bpy.ops.render.render(write_still=True)
ancoras["render_s"] = round(time.time() - t0, 1); ancoras["amostras"] = AMOSTRAS
(OUT / ("ancoras_rapido.json" if "--rapido" in sys.argv else "ancoras.json")).write_text(json.dumps(ancoras, indent=1))
print(json.dumps(ancoras))
