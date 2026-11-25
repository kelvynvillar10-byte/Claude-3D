"""Cenografia — iluminação e GRUPOS DE LUZ (E0, bpy).

Toda luz pertence a um grupo de luz do Cycles; cada grupo sai numa passada separada (linear). No compositor:
imagem = Σ peso_g × cor_g × passada_g. Isso permite reacender, escurecer ou tingir cada grupo SEM renderizar de
novo (ex.: o sol cai e os postes acendem; um raio azul ilumina a rua). Grupos:
- "ceu":        céu físico do Blender (mundo): luz ambiente do céu e o próprio céu visto pela câmera
- "sol":        o sol (luz direcional com sombra dura e quente)
- "artificial": postes, janelas acesas, vitrines (objetos emissivos e luzes)
- "efeito":     luzes reservadas para efeitos (posição vem da receita); renderizadas com intensidade unitária
Presets de horário definem o céu e o sol físicos (a posição do sol NÃO muda no compositor: muda só intensidade/cor).
"""
import math
import bpy
from mathutils import Vector
from .materiais import lin

PRESETS = {
    # elevação/azimute do sol (graus), intensidade, cor; céu: turbidez/ar/aerosol, força; pesos padrão no compositor
    "tarde_dourada": dict(sol_elev=12.0, sol_azim=52.0, sol_forca=4.2, sol_cor="#ffcf96", sol_raio=1.2,
                          ceu_forca=0.45, ar=1.0, aerosol=2.2, ozonio=1.0, pesos={"ceu": 1.0, "sol": 1.0, "artificial": 0.25, "efeito": 0.0}),
    "meio_dia": dict(sol_elev=62.0, sol_azim=-30.0, sol_forca=5.0, sol_cor="#fff4e6", sol_raio=0.6,
                     ceu_forca=0.6, ar=1.0, aerosol=1.0, ozonio=1.0, pesos={"ceu": 1.0, "sol": 1.0, "artificial": 0.0, "efeito": 0.0}),
    # E1 — horários do dia (o sol muda de lugar → cada horário é uma placa)
    "manha": dict(sol_elev=20.0, sol_azim=-135.0, sol_forca=4.4, sol_cor="#ffe2bf", sol_raio=0.9,
                  ceu_forca=0.5, ar=1.0, aerosol=1.4, ozonio=1.0, pesos={"ceu": 1.0, "sol": 1.0, "artificial": 0.0, "efeito": 0.0}),
    "crepusculo": dict(sol_elev=1.5, sol_azim=60.0, sol_forca=1.6, sol_cor="#ff7a45", sol_raio=1.5, ceu_elev=-1.2,
                       ceu_forca=1.6, ar=1.0, aerosol=3.0, ozonio=1.2, pesos={"ceu": 1.0, "sol": 1.0, "artificial": 1.0, "efeito": 0.0}),
    # noite: céu em degradê azul-escuro (o céu físico fica preto abaixo do horizonte) + LUA como luz direcional fria
    "noite": dict(sol_elev=38.0, sol_azim=-40.0, sol_forca=0.22, sol_cor="#9fb4ff", sol_raio=0.6, noite=True,
                  ceu_cor_alto="#06102a", ceu_cor_horizonte="#1d2d55", ceu_forca=0.9, pesos={"ceu": 1.0, "sol": 1.0, "artificial": 1.4, "efeito": 0.0}),
}


def _ceu_noite(nt, bg, P):
    """Degradê vertical do céu noturno (horizonte mais claro, alto escuro)."""
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 0.75
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
    el[0].color = lin(P["ceu_cor_horizonte"]); el[1].color = lin(P["ceu_cor_alto"])
    nt.links.new(mr.outputs["Result"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], bg.inputs["Color"])


def ceu_e_sol(preset):
    P = PRESETS[preset]; cena = bpy.context.scene
    mundo = bpy.data.worlds.new("mundo"); cena.world = mundo; mundo.use_nodes = True
    nt = mundo.node_tree; bg = nt.nodes["Background"]
    if P.get("noite"):
        _ceu_noite(nt, bg, P)
    else:
        ceu = nt.nodes.new("ShaderNodeTexSky"); ceu.sky_type = "MULTIPLE_SCATTERING"
        ceu.sun_disc = False; ceu.sun_elevation = math.radians(P.get("ceu_elev", P["sol_elev"])); ceu.sun_rotation = math.radians(P["sol_azim"])
        ceu.air_density = P["ar"]; ceu.aerosol_density = P["aerosol"]; ceu.ozone_density = P["ozonio"]
        nt.links.new(ceu.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = P["ceu_forca"]
    mundo.lightgroup = "ceu"
    sol = bpy.data.lights.new("sol", "SUN"); sol.energy = P["sol_forca"]; sol.color = lin(P["sol_cor"])[:3]
    sol.angle = math.radians(P["sol_raio"])
    o = bpy.data.objects.new("sol", sol); cena.collection.objects.link(o); o.lightgroup = "sol"
    el, az = math.radians(P["sol_elev"]), math.radians(P["sol_azim"])
    d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))   # direção PARA o sol
    o.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    P = dict(P, sol_dir=list(d))
    return P


def luz_ponto(nome, pos, forca_w, cor, grupo, raio=0.08, tipo="POINT", alvo=None, angulo=None):
    L = bpy.data.lights.new(nome, tipo); L.energy = forca_w; L.color = lin(cor)[:3]; L.shadow_soft_size = raio
    if tipo == "SPOT":
        L.spot_size = math.radians(angulo or 110); L.spot_blend = 0.6
    o = bpy.data.objects.new(nome, L); bpy.context.scene.collection.objects.link(o); o.location = pos; o.lightgroup = grupo
    if alvo is not None:
        o.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


def preparar_grupos(view_layer, grupos):
    for g in grupos:
        if g not in [lg.name for lg in view_layer.lightgroups]:
            view_layer.lightgroups.add(name=g)
