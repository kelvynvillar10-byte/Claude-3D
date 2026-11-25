"""Cenografia — câmera, OVERSCAN e âncoras 3D → 2D (E0, bpy).

- A placa é renderizada maior que a tela (overscan, ex.: 25 %) com o MESMO enquadramento central: o sensor cresce
  na mesma proporção da resolução. O recorte central 1080×1920 é exatamente o plano pedido; a margem serve à câmera
  2.5D (pan, push-in, tremida) no compositor.
- Intrínsecos (f em px, centro óptico) e a pose da câmera vão para o manifesto: o compositor calcula a paralaxe
  com a mesma geometria da câmera real.
- Âncoras: pontos 3D da receita projetados na placa (pé do personagem, contato na parede, chão para efeitos).
"""
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

SENSOR_BASE_MM = 24.0


def criar(cfg, saida):
    cena = bpy.context.scene; f = 1.0 + saida["overscan"]
    W = int(round(saida["largura"] * f / 2) * 2); H = int(round(saida["altura"] * f / 2) * 2)
    d = bpy.data.cameras.new("cam"); d.lens = cfg.get("lente_mm", 35.0); d.sensor_fit = "VERTICAL"
    d.sensor_height = SENSOR_BASE_MM * H / saida["altura"]
    d.clip_start = 0.05; d.clip_end = 500
    cam = bpy.data.objects.new("cam", d); cena.collection.objects.link(cam)
    cam.location = cfg["pos"]
    cam.rotation_euler = (Vector(cfg["alvo"]) - Vector(cfg["pos"])).to_track_quat("-Z", "Y").to_euler()
    cena.camera = cam
    cena.render.resolution_x, cena.render.resolution_y, cena.render.resolution_percentage = W, H, 100
    bpy.context.view_layer.update()
    return cam, W, H


def intrinsecos(cam, W, H):
    f_px = cam.data.lens / cam.data.sensor_height * H
    mw = cam.matrix_world
    return {"f_px": f_px, "cx": W / 2, "cy": H / 2, "W": W, "H": H,
            "pos": list(mw.translation), "dir": list((mw.to_3x3() @ Vector((0, 0, -1))).normalized()),
            "cima": list((mw.to_3x3() @ Vector((0, 1, 0))).normalized()), "dir_x": list((mw.to_3x3() @ Vector((1, 0, 0))).normalized())}


def projetar(cam, p, W, H):
    bpy.context.view_layer.update()
    v = world_to_camera_view(bpy.context.scene, cam, Vector(p))
    return [v.x * W, (1 - v.y) * H, v.z]   # x, y em px; z = profundidade ao longo do eixo da câmera (m)
