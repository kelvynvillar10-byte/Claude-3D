"""Cenografia — render em CAMADAS com grupos de luz (E0, bpy, Cycles CPU).

Para cada camada (céu, longe, meio, perto, frente):
- só os objetos da camada ficam visíveis para a CÂMERA; os outros continuam projetando sombra, refletindo e
  iluminando (visible_camera=False). Resultado: cada camada sai inteira, sem buracos atrás do que está na frente
  — é o que permite paralaxe 2.5D sem "rasgos".
- o compositor do Blender grava em EXR (half float, linear): uma passada por grupo de luz (já sem ruído: OIDN com
  albedo e normal), a imagem completa, o alfa, a profundidade e (E7) o albedo, usado pela luz 2D dos efeitos.
"""
import time
from pathlib import Path
import numpy as np
import bpy

ARQ = {"alfa": "alfa", "profundidade": "profundidade", "imagem": "imagem"}
TIPOS_VISIVEIS = ("MESH", "CURVE", "EMPTY", "FONT", "SURFACE", "META")   # tudo o que a câmera pode ver (texto incluso)


def configurar(cena, amostras, semente, grupos, persistente=True):
    cena.render.engine = "CYCLES"; cena.cycles.device = "CPU"
    cena.cycles.samples = amostras; cena.cycles.use_adaptive_sampling = True; cena.cycles.adaptive_threshold = 0.02
    cena.cycles.seed = semente; cena.cycles.use_animated_seed = False
    cena.cycles.use_denoising = False                  # a limpeza é feita por passada, no compositor (OIDN)
    cena.cycles.max_bounces = 6; cena.cycles.diffuse_bounces = 3; cena.cycles.glossy_bounces = 3
    cena.render.use_persistent_data = persistente     # reaproveita a cena entre as camadas (menos tempo de preparo)
    vl = cena.view_layers[0]; vl.use_pass_z = True; vl.cycles.denoising_store_passes = True
    from .luz import preparar_grupos
    preparar_grupos(vl, grupos)
    return vl


def _grafo(cena, pasta, grupos):
    ng = bpy.data.node_groups.get("saida_camadas") or bpy.data.node_groups.new("saida_camadas", "CompositorNodeTree")
    ng.nodes.clear(); cena.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    fo = ng.nodes.new("CompositorNodeOutputFile"); fo.directory = str(pasta) + "/"; fo.file_name = ""
    fo.format.media_type = "IMAGE"; fo.format.file_format = "OPEN_EXR"; fo.format.color_depth = "16"; fo.format.exr_codec = "ZIP"

    def limpo(saida):
        dn = ng.nodes.new("CompositorNodeDenoise"); dn.inputs["HDR"].default_value = True
        ng.links.new(saida, dn.inputs["Image"])
        ng.links.new(rl.outputs["Denoising Albedo"], dn.inputs["Albedo"]); ng.links.new(rl.outputs["Denoising Normal"], dn.inputs["Normal"])
        return dn.outputs["Image"]
    for g in grupos:
        fo.file_output_items.new("RGBA", f"luz_{g}"); ng.links.new(limpo(rl.outputs[f"Combined_{g}"]), fo.inputs[f"luz_{g}"])
    fo.file_output_items.new("RGBA", "imagem"); ng.links.new(limpo(rl.outputs["Image"]), fo.inputs["imagem"])
    # E7: albedo (cor própria das superfícies) — a luz 2D dos efeitos ilumina o cenário com a cor certa
    fo.file_output_items.new("RGBA", "albedo"); ng.links.new(rl.outputs["Denoising Albedo"], fo.inputs["albedo"])
    fo.file_output_items.new("FLOAT", "alfa"); ng.links.new(rl.outputs["Alpha"], fo.inputs["alfa"])
    fo.file_output_items.new("FLOAT", "profundidade"); ng.links.new(rl.outputs["Depth"], fo.inputs["profundidade"])


def render_camada(cena, colecoes, camada, pasta, grupos):
    """colecoes: {nome_camada: bpy.Collection}. camada 'ceu' = só o mundo (céu)."""
    pasta = Path(pasta); pasta.mkdir(parents=True, exist_ok=True)
    alvo = set(colecoes[camada].all_objects) if camada != "ceu" else set()
    for o in cena.objects:
        if o.type in TIPOS_VISIVEIS:
            o.visible_camera = o in alvo
    cena.render.film_transparent = camada != "ceu"
    _grafo(cena, pasta, grupos)
    t = time.time(); bpy.ops.render.render(write_still=False); dt = time.time() - t
    return round(dt, 2)


def ler_exr(caminho):
    """EXR → numpy float32 (altura, largura, 4), origem no canto superior esquerdo."""
    img = bpy.data.images.load(str(caminho), check_existing=False)
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return np.flipud(a.reshape(h, w, 4)).copy()
