"""Cenografia — geometria base (E0, bpy).

Primitivas com CHANFRO real (bordas que pegam luz: tira a cara de "caixa de videogame"), coleções por camada,
instâncias para peças repetidas e espalhamento determinístico por semente.
Convenção de mundo: metros; z para cima; a câmera olha aproximadamente para +y.
"""
import math
import bpy, bmesh
from mathutils import Vector


def colecao(nome):
    c = bpy.data.collections.get(nome)
    if c is None:
        c = bpy.data.collections.new(nome); bpy.context.scene.collection.children.link(c)
    return c


def _obj(nome, bm, mat, col, liso=False):
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    if liso:
        for f in me.polygons:
            f.use_smooth = True
    o = bpy.data.objects.new(nome, me)
    if mat is not None:
        o.data.materials.append(mat)
    col.objects.link(o)
    return o


def _chanfro(o, largura, segmentos=2):
    if largura > 0:
        b = o.modifiers.new("chanfro", "BEVEL"); b.width = largura; b.segments = segmentos; b.limit_method = "ANGLE"
        b.harden_normals = False
    return o


def caixa(nome, c0, c1, mat, col, chanfro=0.0):
    """Caixa pelos cantos opostos (x0,y0,z0)–(x1,y1,z1)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    d = [b - a for a, b in zip(c0, c1)]; c = [(a + b) / 2 for a, b in zip(c0, c1)]
    for v in bm.verts:
        v.co = Vector((c[0] + v.co.x * d[0], c[1] + v.co.y * d[1], c[2] + v.co.z * d[2]))
    return _chanfro(_obj(nome, bm, mat, col), chanfro)


def cilindro(nome, base, raio, altura, mat, col, lados=20, raio_topo=None, chanfro=0.0):
    """Cilindro (ou tronco de cone) de pé, com a base em 'base' (x, y, z)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=raio, radius2=raio if raio_topo is None else raio_topo, depth=altura)
    for v in bm.verts:
        v.co = Vector((base[0] + v.co.x, base[1] + v.co.y, base[2] + altura / 2 + v.co.z))
    return _chanfro(_obj(nome, bm, mat, col, liso=True), chanfro)


def cilindro_eixo(nome, p0, p1, raio, mat, col, lados=16):
    """Cilindro entre dois pontos (braços de poste, tubos)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o = cilindro(nome, (0, 0, 0), raio, d.length, mat, col, lados)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); o.location = p0
    return o


def esfera(nome, centro, raio, mat, col, sub=3):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=raio)
    for v in bm.verts:
        v.co += Vector(centro)
    return _obj(nome, bm, mat, col, liso=True)


def deformar_ruido(o, forca=0.15, escala=0.6, semente=0):
    """Deslocamento por ruído (volumes orgânicos: copas, arbustos) — sem facetas de low-poly."""
    tex = bpy.data.textures.new(f"ruido_{o.name}", "CLOUDS"); tex.noise_scale = escala; tex.noise_depth = 2
    m = o.modifiers.new("ruido", "DISPLACE"); m.texture = tex; m.strength = forca; m.texture_coords = "GLOBAL"
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 1
    o.modifiers.move(len(o.modifiers) - 1, 0)
    return o


def espalhar(rng, area, n, dist_min=0.5, tentativas=40):
    """Pontos (x, y) espalhados por semente dentro de area=(x0, y0, x1, y1), com distância mínima (Poisson simples)."""
    x0, y0, x1, y1 = area; pts = []
    for _ in range(n * tentativas):
        if len(pts) >= n:
            break
        p = (rng.uniform(x0, x1), rng.uniform(y0, y1))
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= dist_min for q in pts):
            pts.append(p)
    return pts


def prisma(nome, pontos_xy, z0, z1, mat, col, chanfro=0.0):
    """Polígono (lista de (x, y), anti-horário) extrudado de z0 a z1 — esquinas arredondadas, rampas, recortes."""
    bm = bmesh.new()
    base = [bm.verts.new((x, y, z0)) for x, y in pontos_xy]
    f = bm.faces.new(base)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _chanfro(_obj(nome, bm, mat, col), chanfro)


def rampa(nome, x0, x1, y0, y1, z_baixo, z_alto, eixo, mat, col):
    """Cunha: sobe de z_baixo a z_alto ao longo de 'eixo' ("+x", "-x", "+y", "-y")."""
    bm = bmesh.new()
    def z_em(x, y):
        k = {"+x": (x - x0) / (x1 - x0), "-x": (x1 - x) / (x1 - x0), "+y": (y - y0) / (y1 - y0), "-y": (y1 - y) / (y1 - y0)}[eixo]
        return z_baixo + (z_alto - z_baixo) * k
    cantos = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    baixo = [bm.verts.new((x, y, -0.05)) for x, y in cantos]; cima = [bm.verts.new((x, y, z_em(x, y))) for x, y in cantos]
    bm.faces.new(list(reversed(baixo))); bm.faces.new(cima)
    for i in range(4):
        j = (i + 1) % 4; bm.faces.new([baixo[i], baixo[j], cima[j], cima[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(nome, bm, mat, col)


def catenaria(nome, p0, p1, flecha, raio, mat, col, pontos=24):
    """Cabo pendurado entre dois pontos (parábola com 'flecha' m de queda no meio), como curva com espessura."""
    cu = bpy.data.curves.new(nome, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = raio; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); sp.points.add(pontos - 1)
    p0, p1 = Vector(p0), Vector(p1)
    for i in range(pontos):
        t = i / (pontos - 1); p = p0.lerp(p1, t); p.z -= 4 * flecha * t * (1 - t)
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
    o = bpy.data.objects.new(nome, cu); o.data.materials.append(mat); col.objects.link(o)
    o["suspenso"] = True
    return o


_FONTES = {}


def texto(nome, corpo, pos, tamanho, mat, col, rot=(0.0, 0.0, 0.0), fonte=None, extrusao=0.002, alinhar="CENTER"):
    """Texto 3D (placas): fonte oficial do repositório; o QA lê por OCR e só aceita textos da lista permitida."""
    from pathlib import Path
    caminho = str(Path(__file__).resolve().parents[2] / "assets" / "fontes" / (fonte or "RobotoCondensed-ExtraBold.ttf"))
    if caminho not in _FONTES:
        _FONTES[caminho] = bpy.data.fonts.load(caminho)
    cu = bpy.data.curves.new(nome, "FONT"); cu.body = corpo; cu.font = _FONTES[caminho]; cu.size = tamanho
    cu.align_x = alinhar; cu.align_y = "CENTER"; cu.extrude = extrusao
    o = bpy.data.objects.new(nome, cu); o.data.materials.append(mat); col.objects.link(o)
    o.location = pos; o.rotation_euler = rot; o["suspenso"] = True; o["texto"] = corpo
    return o
