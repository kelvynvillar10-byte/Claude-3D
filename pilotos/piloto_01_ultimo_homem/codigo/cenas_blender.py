#!/usr/bin/env python3
"""Piloto 01 — cenários 3D low-poly no Blender (bpy, Cycles CPU).

Um único "mundo" coerente: rua de bairro vazia ao amanhecer e, num 4º andar, o quarto do
Heitor com a janela voltada para a rua. Cada plano renderiza um FUNDO estático 25 % maior
que a tela (1350×2400), um mapa de NÉVOA/profundidade (para atmosfera e desfoque no
compositor), camadas de PRIMEIRO PLANO quando o personagem fica atrás de algo, e as
ÂNCORAS (projeção 3D→2D) que posicionam e dimensionam o personagem 2D na cena.

Uso: .venv/bin/python codigo/cenas_blender.py [plano ...] [--amostras 48] [--rapido]
"""
import json, math, random, sys, time
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

P = Path(__file__).resolve().parents[1]
OUT = P / "_cache" / "render"
OUT.mkdir(parents=True, exist_ok=True)
REC = P / "recursos"
W, H = 1350, 2400
AMOSTRAS = int(sys.argv[sys.argv.index("--amostras") + 1]) if "--amostras" in sys.argv else 48
if "--rapido" in sys.argv:
    W, H, AMOSTRAS = 338, 600, 8
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
cena = bpy.context.scene
col = cena.collection

# ------------------------------------------------------------------ materiais
_mats = {}


def hexrgb(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (a,)


def mat(nome, cor, rug=0.7, metal=0.0, emit=None, forca=1.0, img=None, ruido=0.0):
    if nome in _mats:
        return _mats[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rug
    bsdf.inputs["Metallic"].default_value = metal
    if img:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(img))
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if emit:
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = forca
    else:
        bsdf.inputs["Base Color"].default_value = hexrgb(cor)
        if ruido:  # variação sutil de cor (desgaste) para não parecer plástico
            noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3.0
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            c0 = hexrgb(cor); c1 = tuple(min(1, x * (1 - ruido)) for x in c0[:3]) + (1,)
            ramp.color_ramp.elements[0].color = c1; ramp.color_ramp.elements[1].color = c0
            nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        if emit:
            bsdf.inputs["Emission Color"].default_value = hexrgb(emit)
            bsdf.inputs["Emission Strength"].default_value = forca
    _mats[nome] = m
    return m


def obj_de_bm(nome, bm, m):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nome, me)
    o.data.materials.append(m)
    col.objects.link(o)
    return o


def caixa(nome, centro, dim, m, chanfro=0.0, rot_z=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], v.co.z * dim[2]))
    o = obj_de_bm(nome, bm, m)
    o.location = centro; o.rotation_euler[2] = rot_z
    if chanfro:
        b = o.modifiers.new("chanfro", "BEVEL"); b.width = chanfro; b.segments = 3
    return o


def cilindro(nome, centro, raio, altura, m, rot=(0, 0, 0), lados=24):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=raio, radius2=raio, depth=altura)
    o = obj_de_bm(nome, bm, m); o.location = centro; o.rotation_euler = rot
    return o


def esfera(nome, centro, raio, m, sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=raio)
    o = obj_de_bm(nome, bm, m); o.location = centro
    return o


def plano(nome, centro, dim, m, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], 0))
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x / dim[0] + 0.5, l.vert.co.y / dim[1] + 0.5)
    o = obj_de_bm(nome, bm, m); o.location = centro; o.rotation_euler = rot
    return o


# ------------------------------------------------------------------ mundo / céu
mundo = bpy.data.worlds.new("ceu"); cena.world = mundo
mundo.use_nodes = True
bg = mundo.node_tree.nodes["Background"]
sky = mundo.node_tree.nodes.new("ShaderNodeTexGradient")
mp = mundo.node_tree.nodes.new("ShaderNodeMapping"); tc = mundo.node_tree.nodes.new("ShaderNodeTexCoord")
mp.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
ramp = mundo.node_tree.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = hexrgb("#f6c99a")   # horizonte quente
ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = hexrgb("#7f93bf")   # céu frio
L = mundo.node_tree.links
L.new(tc.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], sky.inputs["Vector"])
L.new(sky.outputs["Fac"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.9

sol_d = bpy.data.lights.new("sol", "SUN"); sol_d.energy = 3.2; sol_d.color = (1.0, 0.78, 0.55); sol_d.angle = math.radians(2.5)
sol = bpy.data.objects.new("sol", sol_d); col.objects.link(sol)
sol.rotation_euler = Vector((-0.78, -0.42, -0.46)).to_track_quat('-Z', 'Y').to_euler()   # sol baixo e rasante: entra pela janela do quarto

# ------------------------------------------------------------------ rua
ASF = mat("asfalto", "#3b3d44", rug=0.85, ruido=0.35)
CALC = mat("calcada", "#9b968c", rug=0.9, ruido=0.25)
FAIXA = mat("faixa", "#e8e2d0", rug=0.6)
plano("asfalto", (0, 30, 0), (12, 220, 1), ASF)
for s in (-1, 1):
    caixa(f"calcada{s}", (s * 8.5, 30, 0.08), (5, 220, 0.16), CALC)
    caixa(f"meiofio{s}", (s * 6.05, 30, 0.08), (0.12, 220, 0.18), mat("meiofio", "#b9b2a4", rug=0.8))
for i in range(-20, 60):
    caixa(f"faixa{i}", (0, i * 3.0, 0.005), (0.14, 1.5, 0.01), FAIXA)
# faixa de pedestres
for k in range(8):
    caixa(f"zebra{k}", (-4.5 + k * 1.3, 9.0, 0.006), (0.7, 3.0, 0.012), FAIXA)

# prédios (sem gente: cidade vazia)
FACH = ["#c9a98a", "#b5735a", "#8f9aa6", "#d8cbb2", "#a7876b", "#7f8c7a", "#c4b59a", "#9d6f5d"]
VIDRO = mat("vidro", "#1d2633", rug=0.15, metal=0.3)
VIDRO_LUZ = mat("vidro_luz", "#3a2c1c", rug=0.3, emit="#ffb46b", forca=1.6)
MOLD = mat("moldura", "#e9e3d6", rug=0.7)


def predio(nome, x0, x1, y0, y1, alt, cor, lado):
    m = mat(f"fach_{cor}", cor, rug=0.85, ruido=0.18)
    caixa(nome, ((x0 + x1) / 2, (y0 + y1) / 2, alt / 2), (x1 - x0, y1 - y0, alt), m)
    # janelas na fachada voltada para a rua (geometria, não textura)
    bm = bmesh.new(); bm2 = bmesh.new()
    face_x = x1 if lado < 0 else x0
    nx = int((y1 - y0) / 2.2); nz = int((alt - 3.5) / 3.0)
    for j in range(nx):
        for k in range(nz):
            y = y0 + 1.1 + j * (y1 - y0 - 2.2) / max(1, nx - 1) if nx > 1 else (y0 + y1) / 2
            z = 3.6 + k * 3.0
            alvo = bm2 if random.random() < 0.04 else bm
            r = bmesh.ops.create_cube(alvo, size=1.0)
            for v in r["verts"]:
                v.co = Vector((face_x + v.co.x * 0.12, y + v.co.y * 1.1, z + v.co.z * 1.5))
    if bm.verts:
        obj_de_bm(nome + "_jan", bm, VIDRO)
    else:
        bm.free()
    if bm2.verts:
        obj_de_bm(nome + "_janluz", bm2, VIDRO_LUZ)
    else:
        bm2.free()
    # térreo com toldo e porta
    caixa(nome + "_toldo", (face_x - lado * 0.6, (y0 + y1) / 2, 3.0), (1.2, (y1 - y0) * 0.7, 0.12),
          mat(f"toldo{cor}", random.choice(["#2f5d62", "#8c2f2f", "#d9a441", "#3d4f7a"]), rug=0.8))


y = -40
while y < 140:
    larg = random.uniform(9, 14)
    for lado in (-1, 1):
        x_rua = 11.0
        alt = random.uniform(9, 26)
        if lado < 0 and -4 < y + larg / 2 < 10:
            y_pred = y  # o prédio do Heitor é montado à parte
        else:
            predio(f"p{lado}_{int(y)}", -x_rua - 12 if lado < 0 else x_rua, -x_rua if lado < 0 else x_rua + 12,
                   y, y + larg - 0.4, alt, random.choice(FACH), lado)
    y += larg

# outdoor com a marca (ID-004: "MODO CURIOSO" em maiúsculas, a partir do arquivo-mestre)
OUTD = mat("outdoor", None, rug=0.6, img=REC / "marca" / "outdoor_MODO_CURIOSO.png", emit=True, forca=0.25)
caixa("outdoor_estrutura", (11.2, 36, 13.5), (0.4, 9.4, 4.4), mat("metal_escuro", "#2b2d33", rug=0.5, metal=0.6))
plano("outdoor", (10.98, 36, 13.5), (9.0, 4.0, 1), OUTD, rot=(math.radians(90), 0, math.radians(-90)))

# carros abandonados
CORES_CARRO = ["#b23a3a", "#d7d2c8", "#2f4f6f", "#3c3c40", "#c79a3a"]
PNEU = mat("pneu", "#151515", rug=0.9); CROMO = mat("cromo", "#cfd3d8", rug=0.25, metal=1.0)


def carro(nome, x, y, ang, cor, porta_aberta=False):
    m = mat(f"carro{cor}", cor, rug=0.35, metal=0.2)
    base = caixa(nome, (0, 0, 0.62), (1.8, 4.2, 0.7), m, chanfro=0.12)
    cab = caixa(nome + "_cab", (0, -0.2, 1.22), (1.6, 2.2, 0.62), VIDRO, chanfro=0.15)
    teto = caixa(nome + "_teto", (0, -0.2, 1.55), (1.62, 2.0, 0.08), m, chanfro=0.03)
    pecas = [base, cab, teto]
    for sx in (-0.85, 0.85):
        for sy in (-1.35, 1.35):
            pecas.append(cilindro(nome + f"_r{sx}{sy}", (sx, sy, 0.36), 0.36, 0.28, PNEU, rot=(0, math.radians(90), 0)))
    if porta_aberta:
        porta = caixa(nome + "_porta", (1.35, 0.15, 0.95), (0.08, 1.2, 0.95), m, rot_z=math.radians(-55))
        pecas.append(porta)
    vazio = bpy.data.objects.new(nome + "_pai", None); col.objects.link(vazio)
    for p_ in pecas:
        p_.parent = vazio
    vazio.location = (x, y, 0); vazio.rotation_euler[2] = math.radians(ang)
    return vazio


carro("carro1", -2.6, 14, 8, CORES_CARRO[0], porta_aberta=True)
carro("carro2", 3.1, 24, -12, CORES_CARRO[1])
carro("carro3", -3.4, 33, 3, CORES_CARRO[2])
carro("carro4", 1.4, 46, 28, CORES_CARRO[3])
carro("carro5", 3.6, 5.5, -4, CORES_CARRO[4])

# postes, semáforo, árvores, papéis no chão
POSTE = mat("poste", "#4a4d55", rug=0.5, metal=0.5)
for yy in range(-10, 120, 18):
    for s in (-1, 1):
        cilindro(f"poste{s}{yy}", (s * 6.6, yy, 3.5), 0.09, 7.0, POSTE)
        caixa(f"braco{s}{yy}", (s * 5.9, yy, 6.95), (1.4, 0.15, 0.12), POSTE)
cilindro("sem_poste", (6.4, 8.0, 2.4), 0.1, 4.8, POSTE)
caixa("sem_caixa", (6.0, 8.0, 4.9), (0.45, 0.4, 1.2), mat("sem_caixa", "#22252b", rug=0.5))
esfera("sem_amarela", (6.0, 7.78, 4.9), 0.13, mat("sem_amarelo", "#ffb000", emit="#ffb000", forca=6.0))
TRONCO = mat("tronco", "#5b4636", rug=0.9); FOLHA = mat("folha", "#5f7d47", rug=0.8, ruido=0.3)
for yy in range(-6, 110, 14):
    for s in (-1, 1):
        cilindro(f"tronco{s}{yy}", (s * 9.4, yy + 5, 1.6), 0.16, 3.2, TRONCO)
        for k in range(3):
            esfera(f"copa{s}{yy}{k}", (s * 9.4 + random.uniform(-0.6, 0.6), yy + 5 + random.uniform(-0.6, 0.6),
                                       3.6 + k * 0.7), random.uniform(1.0, 1.5), FOLHA)
PAPEL = mat("papel", "#ece6d6", rug=0.9)
for i in range(70):
    plano(f"papel{i}", (random.uniform(-5.5, 5.5), random.uniform(-4, 50), 0.012), (0.21, 0.28, 1), PAPEL,
          rot=(0, 0, random.uniform(0, 6.28)))

# ------------------------------------------------------------------ prédio e quarto do Heitor (4º andar)
# Interior: x ∈ [-16, -12], y ∈ [-2, 2], piso em z = 12, pé-direito 2,7 m. Janela em x = -12 (vista para a rua).
FZ = 12.0
PAREDE = mat("parede_quarto", "#b9c3c9", rug=0.9, ruido=0.08)
FACH_H = mat("fach_heitor", "#cdb49a", rug=0.85, ruido=0.18)
PISO = mat("piso_madeira", "#8a5a3b", rug=0.55, ruido=0.35)
# fachada do prédio (com o buraco da janela do quarto)
xf = -11.85
caixa("hp_baixo", (-18, 0, FZ / 2), (12.3, 14, FZ), FACH_H)
caixa("hp_cima", (-18, 0, FZ + 2.7 + 6), (12.3, 14, 12), FACH_H)
caixa("hp_esq", (-18, -4.5, FZ + 1.35), (12.3, 5, 2.7), FACH_H)
caixa("hp_dir", (-18, 4.5, FZ + 1.35), (12.3, 5, 2.7), FACH_H)
# interior escavado: paredes internas do quarto
caixa("q_piso", (-14, 0, FZ - 0.05), (4, 4, 0.1), PISO)
caixa("q_teto", (-14, 0, FZ + 2.75), (4, 4, 0.1), mat("teto", "#d9d5cc"))
caixa("q_fundo", (-16.05, 0, FZ + 1.35), (0.1, 4, 2.7), PAREDE)
caixa("q_lado_e", (-14, -2.05, FZ + 1.35), (4, 0.1, 2.7), PAREDE)
caixa("q_lado_d", (-14, 2.05, FZ + 1.35), (4, 0.1, 2.7), PAREDE)
# parede da janela (frente) com abertura y ∈ [-0.85, 0.85], z ∈ [0.85, 2.25]
caixa("q_jan_e", (-11.95, -1.43, FZ + 1.35), (0.2, 1.15, 2.7), PAREDE)
caixa("q_jan_d", (-11.95, 1.43, FZ + 1.35), (0.2, 1.15, 2.7), PAREDE)
caixa("q_jan_b", (-11.95, 0, FZ + 0.42), (0.2, 1.7, 0.85), PAREDE)
caixa("q_jan_c", (-11.95, 0, FZ + 2.48), (0.2, 1.7, 0.45), PAREDE)
for z_, h_ in ((0.85, 0.06), (2.25, 0.06)):
    caixa(f"q_moldura{z_}", (-11.9, 0, FZ + z_), (0.26, 1.78, h_), MOLD)
for yy in (-0.85, 0.0, 0.85):
    caixa(f"q_mont{yy}", (-11.9, yy, FZ + 1.55), (0.26, 0.05, 1.4), MOLD)
# cortinas
CORT = mat("cortina", "#d8c9a6", rug=0.95)
for s in (-1, 1):
    caixa(f"cortina{s}", (-12.15, s * 1.1, FZ + 1.5), (0.06, 0.5, 2.3), CORT)
# cama (cabeceira na parede do fundo), cobertor, travesseiro
MAD = mat("madeira_cama", "#6b4630", rug=0.6, ruido=0.2)
caixa("cama_base", (-14.95, -0.9, FZ + 0.22), (2.0, 1.1, 0.44), MAD, chanfro=0.02)
caixa("cabeceira", (-15.93, -0.9, FZ + 0.6), (0.08, 1.15, 1.2), MAD, chanfro=0.02)
caixa("colchao", (-14.95, -0.9, FZ + 0.55), (1.95, 1.05, 0.22), mat("lencol", "#e9e6df", rug=0.9), chanfro=0.05)
TRAV = mat("travesseiro", "#f2efe8", rug=0.95)
caixa("travesseiro", (-15.6, -0.9, FZ + 0.74), (0.45, 0.75, 0.16), TRAV, chanfro=0.07)
COB = mat("cobertor", "#3e6e7c", rug=0.95, ruido=0.25)
cobertor = caixa("cobertor", (-14.55, -0.9, FZ + 0.72), (1.25, 1.12, 0.12), COB, chanfro=0.05)
# criado-mudo, luminária, prateleira, livros, planta
caixa("criado", (-15.6, 0.45, FZ + 0.3), (0.45, 0.45, 0.6), MAD, chanfro=0.02)
cilindro("lum_base", (-15.6, 0.45, FZ + 0.63), 0.08, 0.06, mat("lum_base", "#2b2b2b"))
cilindro("lum_haste", (-15.6, 0.45, FZ + 0.8), 0.015, 0.34, mat("lum_base", "#2b2b2b"))
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.16, radius2=0.09, depth=0.2)
cup = obj_de_bm("lum_cupula", bm, mat("cupula", "#f1dfb8", emit="#ffcf8a", forca=2.0)); cup.location = (-15.6, 0.45, FZ + 1.02)
caixa("prateleira", (-15.85, 1.2, FZ + 1.75), (0.28, 1.2, 0.04), MAD)
for i in range(9):
    h_ = random.uniform(0.18, 0.28)
    caixa(f"livro{i}", (-15.85, 0.7 + i * 0.11, FZ + 1.77 + h_ / 2), (0.2, 0.08, h_),
          mat(f"livro{i%5}", ["#8c2f2f", "#2f5d62", "#d9a441", "#3d4f7a", "#5f7d47"][i % 5], rug=0.7))
cilindro("vaso", (-12.6, 1.6, FZ + 0.18), 0.14, 0.36, mat("vaso", "#b5735a"))
for k in range(4):
    esfera(f"planta{k}", (-12.6 + random.uniform(-0.12, 0.12), 1.6 + random.uniform(-0.12, 0.12), FZ + 0.48 + k * 0.08),
           0.14, FOLHA, sub=1)
# pôster na parede lateral (ID-004: "MODO CURIOSO")
POSTER = mat("poster", None, rug=0.7, img=REC / "marca" / "poster_MODO_CURIOSO.png")
plano("poster", (-14.4, 1.99, FZ + 1.55), (0.62, 0.88, 1), POSTER, rot=(math.radians(90), 0, math.radians(180)))
# tapete
plano("tapete", (-13.6, 0.1, FZ + 0.012), (1.6, 1.1, 1), mat("tapete", "#8f5d4a", rug=1.0, ruido=0.3))
# luz de preenchimento fria dentro do quarto (sombra azulada) + luz da janela
area_d = bpy.data.lights.new("janela_luz", "AREA"); area_d.energy = 300; area_d.color = (1.0, 0.70, 0.45)
area_d.shape = "RECTANGLE"; area_d.size = 1.7; area_d.size_y = 1.4
area = bpy.data.objects.new("janela_luz", area_d); col.objects.link(area); area.visible_camera = False
area.location = (-11.7, 0, FZ + 1.55); area.rotation_euler = (0, math.radians(90), 0)   # aponta para dentro do quarto (-X)
fill_d = bpy.data.lights.new("preench", "AREA"); fill_d.energy = 22; fill_d.color = (0.62, 0.68, 1.0); fill_d.size = 2.5
fill = bpy.data.objects.new("preench", fill_d); col.objects.link(fill)
fill.location = (-14, 0, FZ + 2.6); fill.rotation_euler = (0, 0, 0)

# celular (no asfalto, para o plano 7)
CEL_CORPO = mat("cel_corpo", "#1a1b1f", rug=0.35, metal=0.4)
cel = caixa("celular", (0.35, -0.25, 0.02), (0.075, 0.155, 0.009), CEL_CORPO, chanfro=0.006, rot_z=math.radians(22))
tela_off = mat("tela_off", "#0b0d12", rug=0.12)
tela_on = mat("tela_on", None, rug=0.2, img=REC / "tela_celular.png", emit=True, forca=2.2)
tela = plano("tela", (0.35, -0.25, 0.0252), (0.068, 0.146, 1), tela_off, rot=(0, 0, math.radians(22)))

# planeta (inserto científico, plano 5) — longe de tudo
TERRA = bpy.data.materials.new("terra"); TERRA.use_nodes = True
nt = TERRA.node_tree; b_ = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 8
rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].position = 0.52; rp.color_ramp.elements[0].color = hexrgb("#1f4e8c")
rp.color_ramp.elements[1].position = 0.55; rp.color_ramp.elements[1].color = hexrgb("#5f8a4a")
nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], b_.inputs["Base Color"])
b_.inputs["Roughness"].default_value = 0.6
nt.links.new(rp.outputs["Color"], b_.inputs["Emission Color"]); b_.inputs["Emission Strength"].default_value = 0.9
terra = esfera("terra", (0, 0, -500), 6.0, TERRA, sub=5)
for f in terra.data.polygons:
    f.use_smooth = True
atm = esfera("atmosfera", (0, 0, -500), 6.25, mat("atm", "#6fa8ff", rug=1.0, emit="#6fa8ff", forca=0.0), sub=5)
atm_m = atm.data.materials[0]; atm_m.blend_method = "BLEND" if hasattr(atm_m, "blend_method") else None
ant = atm_m.node_tree
fres = ant.nodes.new("ShaderNodeLayerWeight"); emi = ant.nodes.new("ShaderNodeEmission"); tr = ant.nodes.new("ShaderNodeBsdfTransparent")
mix = ant.nodes.new("ShaderNodeMixShader"); emi.inputs["Color"].default_value = hexrgb("#7fb6ff"); emi.inputs["Strength"].default_value = 3.0
pw = ant.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.5
ant.links.new(fres.outputs["Facing"], pw.inputs[0]); ant.links.new(pw.outputs["Value"], mix.inputs["Fac"]); ant.links.new(tr.outputs["BSDF"], mix.inputs[1]); ant.links.new(emi.outputs["Emission"], mix.inputs[2])
ant.links.new(mix.outputs["Shader"], ant.nodes["Material Output"].inputs["Surface"])
for f in atm.data.polygons:
    f.use_smooth = True

# ------------------------------------------------------------------ câmeras e planos
def camera(nome, loc, alvo, lente=35, dof=None, fstop=2.8):
    c = bpy.data.cameras.new(nome); c.lens = lente; c.sensor_fit = "VERTICAL"; c.sensor_height = 24
    if dof:
        c.dof.use_dof = True; c.dof.focus_distance = dof; c.dof.aperture_fstop = fstop
    o = bpy.data.objects.new(nome, c); col.objects.link(o)
    o.location = loc
    d = Vector(alvo) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


PLANOS = {
    # 1: close de cima no travesseiro (Heitor acordando); cobertor na frente do corpo
    "p1_travesseiro": dict(cam=((-14.45, 0.55, FZ + 1.55), (-15.45, -0.9, FZ + 0.82)), lente=38, dof=1.95, f=2.4,
                           frente=["cobertor"], ancoras={"cabeca": (-15.55, -0.9, FZ + 0.88), "cabeca_topo": (-15.725, -0.9, FZ + 0.88),
                                                       "pes": (-14.15, -0.9, FZ + 0.88)}),
    # 2: de costas, Heitor diante da janela, rua lá fora
    "p2_janela": dict(cam=((-15.4, 0.75, FZ + 1.25), (-12.0, -0.05, FZ + 1.3)), lente=30, dof=2.6, f=4.0,
                      ancoras={"pe": (-12.75, 0.0, FZ), "cabeca": (-12.75, 0.0, FZ + 1.40)}),
    # 3: revelação — da janela para a rua vazia (pull-out forte no compositor)
    "p3_cidade": dict(cam=((-11.4, -1.0, FZ + 1.7), (2.0, 34.0, 0.0)), lente=24),
    # 4: nível da rua; Heitor pequeno no meio da rua vazia
    "p4_rua": dict(cam=((1.6, -7.5, 1.15), (-0.2, 6.0, 1.6)), lente=28, dof=7.6, f=8.0,
                   ancoras={"pe": (-0.4, 0.0, 0.0), "cabeca": (-0.4, 0.0, 1.40)}),
    # 6: close assustado (fundo desfocado)
    "p6_close": dict(cam=((0.15, -1.55, 1.18), (-0.4, 0.0, 1.22)), lente=50, dof=1.66, f=1.8,
                     ancoras={"pe": (-0.4, 0.0, 0.0), "cabeca": (-0.4, 0.0, 1.40), "ombro": (-0.4, 0.0, 1.0)}),
    # 7: celular no asfalto (tela apagada e acesa)
    "p7_celular": dict(cam=((0.62, -0.62, 0.42), (0.35, -0.25, 0.02)), lente=55, dof=0.608, f=5.6, variante_tela=True),
    # 5: planeta (inserto científico)
    "p5_terra": dict(cam=((0, -45.0, -500), (0, 0, -500)), lente=35, terra=True),
}

cena.render.engine = "CYCLES"
cena.cycles.device = "CPU"
cena.cycles.samples = AMOSTRAS
cena.cycles.use_denoising = True
cena.cycles.max_bounces = 6
cena.render.resolution_x, cena.render.resolution_y = W, H
cena.render.resolution_percentage = 100
cena.render.image_settings.file_format = "PNG"
cena.render.image_settings.color_mode = "RGBA"
cena.view_settings.view_transform = "AgX"
try:
    cena.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
cena.view_settings.exposure = 0.15


def esconder_terra(sim):
    for o in (terra, atm):
        o.hide_render = sim


def render_para(arquivo):
    cena.render.filepath = str(arquivo)
    bpy.ops.render.render(write_still=True)


def mapa_nevoa(arquivo, cam_obj, d0, d1):
    """Render rápido com override de material: branco = longe (névoa), preto = perto."""
    m = bpy.data.materials.get("_nevoa") or bpy.data.materials.new("_nevoa")
    m.use_nodes = True; nt_ = m.node_tree; nt_.nodes.clear()
    cd = nt_.nodes.new("ShaderNodeCameraData"); mr = nt_.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = d0; mr.inputs["From Max"].default_value = d1
    em = nt_.nodes.new("ShaderNodeEmission"); out = nt_.nodes.new("ShaderNodeOutputMaterial")
    nt_.links.new(cd.outputs["View Distance"], mr.inputs["Value"]); nt_.links.new(mr.outputs["Result"], em.inputs["Strength"])
    nt_.links.new(em.outputs["Emission"], out.inputs["Surface"])
    vl = cena.view_layers[0]; vl.material_override = m
    s0, vt, w_ = cena.cycles.samples, cena.view_settings.view_transform, mundo.node_tree.nodes["Background"].inputs["Strength"].default_value
    cena.cycles.samples = 4; cena.view_settings.view_transform = "Standard"; cena.cycles.use_denoising = False
    mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    cena.world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    render_para(arquivo)
    vl.material_override = None; cena.cycles.samples = s0; cena.view_settings.view_transform = vt; cena.cycles.use_denoising = True
    mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = w_


def projeta(cam_obj, pts):
    res = {}
    for k, p in pts.items():
        v = world_to_camera_view(cena, cam_obj, Vector(p))
        res[k] = [round(v.x * W, 1), round((1 - v.y) * H, 1), round(v.z, 3)]
    return res


pedidos = [a for a in sys.argv[1:] if not a.startswith("--") and not a.replace(".", "").isdigit()]
alvos = pedidos or list(PLANOS)
ancoras_todas = json.loads((OUT / "ancoras.json").read_text()) if (OUT / "ancoras.json").exists() else {}
for nome in alvos:
    cfg = PLANOS[nome]; t0 = time.time()
    (loc, alvo) = cfg["cam"]
    cam = camera("cam_" + nome, loc, alvo, cfg.get("lente", 35), cfg.get("dof"), cfg.get("f", 2.8))
    cena.camera = cam
    esconder_terra(not cfg.get("terra"))
    if cfg.get("terra"):
        cena.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
        cena.render.film_transparent = True
    else:
        cena.render.film_transparent = False
        bg.inputs["Strength"].default_value = 0.9
    render_para(OUT / f"{nome}_fundo.png")
    if cfg.get("variante_tela"):
        tela.data.materials[0] = tela_on
        render_para(OUT / f"{nome}_fundo_acesa.png")
        tela.data.materials[0] = tela_off
    if not cfg.get("terra"):
        mapa_nevoa(OUT / f"{nome}_nevoa.png", cam, 2.0 if "rua" in nome or "cidade" in nome else 0.5,
                   90.0 if "cidade" in nome else 40.0)
    if cfg.get("frente"):  # camada de primeiro plano (só os objetos que ficam na frente do personagem)
        visiveis = {o.name: o.hide_render for o in bpy.data.objects}
        for o in bpy.data.objects:
            if o.type == "MESH" and o.name not in cfg["frente"]:
                o.is_holdout = True
        cena.render.film_transparent = True
        render_para(OUT / f"{nome}_frente.png")
        for o in bpy.data.objects:
            o.is_holdout = False
        cena.render.film_transparent = False
    if cfg.get("ancoras"):
        ancoras_todas[nome] = projeta(cam, cfg["ancoras"])
    print(f"PLANO {nome}: {time.time()-t0:.1f} s", flush=True)
ancoras_todas["_resolucao"] = [W, H]
(OUT / "ancoras.json").write_text(json.dumps(ancoras_todas, indent=1))
print("OK", OUT)
