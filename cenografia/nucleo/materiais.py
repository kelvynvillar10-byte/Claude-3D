"""Cenografia — biblioteca de MATERIAIS procedurais (E0, roda dentro do bpy).

Estilo aprovado: estilizado com acabamento cinematográfico — textura e desgaste visíveis, sem fotorrealismo.
Tudo é procedural (nós de textura do Blender: ruído, Voronoi, tijolo), sem imagens externas (rede não liberada).
Cada material aceita: cor (hex), escala, desgaste (0–1), sujeira (0–1). Mesmo nome + mesmos parâmetros = mesmo material.

Materiais da E0: asfalto, concreto (placas de calçada), reboco, tijolo, pintura (metal/madeira pintados), vidro,
emissor (luz de janela, luminária), borracha, folhagem, terra. A E1 amplia e refina esta biblioteca.
"""
import bpy

_CACHE = {}


def lin(h, a=1.0):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (a,)


def _escurece(h, f):
    c = lin(h); return tuple(x * f for x in c[:3]) + (1.0,)


class _NT:
    """Atalhos para montar árvores de nós."""

    def __init__(self, nome):
        self.m = bpy.data.materials.new(nome); self.m.use_nodes = True
        self.nt = self.m.node_tree; self.b = self.nt.nodes["Principled BSDF"]

    def n(self, tipo, **kw):
        no = self.nt.nodes.new(tipo)
        for k, v in kw.items():
            if k in no.inputs:
                no.inputs[k].default_value = v
            else:
                setattr(no, k, v)
        return no

    def l(self, a, b):
        self.nt.links.new(a, b)

    def coord(self, tipo="Object", escala=(1, 1, 1)):
        tc = self.n("ShaderNodeTexCoord")
        if escala == (1, 1, 1):
            return tc.outputs[tipo]
        mp = self.n("ShaderNodeMapping"); mp.inputs["Scale"].default_value = escala
        self.l(tc.outputs[tipo], mp.inputs["Vector"]); return mp.outputs["Vector"]

    def ruido(self, vec, escala, detalhe=4.0, rug=0.55, distorcao=0.0):
        r = self.n("ShaderNodeTexNoise", Scale=escala, Detail=detalhe, Roughness=rug, Distortion=distorcao)
        self.l(vec, r.inputs["Vector"]); return r.outputs["Factor"]

    def rampa(self, fac, pontos):
        cr = self.n("ShaderNodeValToRGB"); el = cr.color_ramp.elements
        el[0].position, el[0].color = pontos[0][0], pontos[0][1]
        el[1].position, el[1].color = pontos[-1][0], pontos[-1][1]
        for pos, cor in pontos[1:-1]:
            e = el.new(pos); e.color = cor
        self.l(fac, cr.inputs["Fac"]); return cr.outputs["Color"]

    def mistura(self, a, b, fac, modo="MIX"):
        mx = self.n("ShaderNodeMix", data_type="RGBA", blend_type=modo)
        if isinstance(fac, (int, float)):
            mx.inputs["Factor"].default_value = fac
        else:
            self.l(fac, mx.inputs["Factor"])
        for sock, v in ((mx.inputs[6], a), (mx.inputs[7], b)):
            if isinstance(v, tuple):
                sock.default_value = v
            else:
                self.l(v, sock)
        return mx.outputs[2]

    def mat_valor(self, fac, a, b):
        """Mapeia fac (0–1) para o intervalo [a, b]."""
        mr = self.n("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = a; mr.inputs["To Max"].default_value = b
        self.l(fac, mr.inputs["Value"]); return mr.outputs["Result"]

    def relevo(self, altura, forca=0.3, dist=0.02, normal=None):
        bp = self.n("ShaderNodeBump", Strength=forca, Distance=dist)
        self.l(altura, bp.inputs["Height"])
        if normal is not None:
            self.l(normal, bp.inputs["Normal"])
        return bp.outputs["Normal"]

    def sujeira_base(self, cor_base, sujeira, altura_m=0.9):
        """Escurece perto do chão (respingo, poeira) — altura em metros, coordenadas de mundo."""
        if sujeira <= 0:
            return cor_base
        pos = self.n("ShaderNodeNewGeometry").outputs["Position"]
        sep = self.n("ShaderNodeSeparateXYZ"); self.l(pos, sep.inputs["Vector"])
        mr = self.n("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = altura_m
        mr.inputs["To Min"].default_value = sujeira; mr.inputs["To Max"].default_value = 0.0
        self.l(sep.outputs["Z"], mr.inputs["Value"])
        rd = self.ruido(self.coord("Object"), 6.0)
        fator = self.n("ShaderNodeMath", operation="MULTIPLY"); self.l(mr.outputs["Result"], fator.inputs[0]); self.l(rd, fator.inputs[1])
        return self.mistura(cor_base, lin("#3a3128"), fator.outputs[0], "MULTIPLY")

    def escorrido(self, cor_base, desgaste):
        """Manchas verticais de chuva (escorridos) em fachadas."""
        if desgaste <= 0:
            return cor_base
        r = self.ruido(self.coord("Object", (3.0, 3.0, 0.12)), 4.0, 3.0, 0.6)
        f = self.mat_valor(r, 0.0, 0.55 * desgaste)
        return self.mistura(cor_base, lin("#6b6258"), f, "MULTIPLY")


def _guardar(chave, m):
    _CACHE[chave] = m; return m


def asfalto(cor="#3a3a3d", escala=1.0, desgaste=0.5, sujeira=0.4):
    chave = ("asfalto", cor, escala, desgaste, sujeira)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("asfalto"); v = t.coord("Object")
    grao = t.ruido(v, 180 * escala, 2.0, 0.7)                                   # agregado fino
    manchas = t.ruido(v, 1.2 * escala, 3.0, 0.5)                                # remendos e manchas grandes
    base = t.rampa(grao, [(0.3, _escurece(cor, 0.75)), (0.55, lin(cor)), (0.78, _escurece(cor, 1.35))])
    base = t.mistura(base, _escurece(cor, 0.72), t.mat_valor(manchas, -0.2 * desgaste, 0.5 * desgaste))
    # rachaduras: borda de Voronoi em escala grande, afinada
    vor = t.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", Scale=0.35 * escala); t.l(v, vor.inputs["Vector"])
    rach = t.n("ShaderNodeMapRange"); rach.inputs["From Min"].default_value = 0.0; rach.inputs["From Max"].default_value = 0.012 + 0.01 * desgaste
    rach.inputs["To Min"].default_value = desgaste; rach.inputs["To Max"].default_value = 0.0
    t.l(vor.outputs["Distance"], rach.inputs["Value"])
    base = t.mistura(base, lin("#141415"), rach.outputs["Result"])
    t.l(base, t.b.inputs["Base Color"])
    t.l(t.mat_valor(grao, 0.78, 0.95), t.b.inputs["Roughness"])
    alt = t.n("ShaderNodeMath", operation="SUBTRACT"); t.l(grao, alt.inputs[0]); t.l(rach.outputs["Result"], alt.inputs[1])
    t.l(t.relevo(alt.outputs[0], 0.25, 0.01), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def concreto(cor="#a9a397", escala=1.0, desgaste=0.4, sujeira=0.3, placa_m=(1.0, 1.0)):
    """Placas de calçada: juntas pelo nó de tijolo (sem deslocamento entre fileiras)."""
    chave = ("concreto", cor, escala, desgaste, sujeira, placa_m)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("concreto"); v = t.coord("Object")
    br = t.n("ShaderNodeTexBrick", offset=0.0, squash=1.0, Scale=1.0 / placa_m[0], **{"Mortar Size": 0.012, "Brick Width": 1.0,
                                                                                        "Row Height": placa_m[1] / placa_m[0], "Bias": 0.0})
    br.inputs["Color1"].default_value = lin(cor); br.inputs["Color2"].default_value = _escurece(cor, 0.9)
    br.inputs["Mortar"].default_value = _escurece(cor, 0.45); t.l(v, br.inputs["Vector"])
    mancha = t.ruido(v, 2.5 * escala, 4.0, 0.6)
    base = t.mistura(br.outputs["Color"], _escurece(cor, 0.7), t.mat_valor(mancha, -0.3, 0.5 * desgaste + 0.1))
    base = t.sujeira_base(base, sujeira, 0.25)
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.88
    junta = t.n("ShaderNodeMath", operation="SUBTRACT"); junta.inputs[0].default_value = 1.0; t.l(br.outputs["Factor"], junta.inputs[1])
    t.l(t.relevo(junta.outputs[0], 0.35, 0.01), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def reboco(cor="#e2c9a4", escala=1.0, desgaste=0.35, sujeira=0.35):
    chave = ("reboco", cor, escala, desgaste, sujeira)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("reboco"); v = t.coord("Object")
    textura = t.ruido(v, 22 * escala, 5.0, 0.6)
    nuvem = t.ruido(v, 0.8 * escala, 3.0, 0.5)
    base = t.rampa(nuvem, [(0.25, _escurece(cor, 0.86)), (0.6, lin(cor)), (0.85, _escurece(cor, 1.06))])
    base = t.escorrido(base, desgaste)
    base = t.sujeira_base(base, sujeira, 1.0)
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.92
    t.l(t.relevo(textura, 0.18, 0.004), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def tijolo(cor="#9c4f35", escala=1.0, desgaste=0.3, sujeira=0.3):
    chave = ("tijolo", cor, escala, desgaste, sujeira)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("tijolo"); v = t.coord("Object")
    br = t.n("ShaderNodeTexBrick", offset=0.5, Scale=4.2 * escala, **{"Mortar Size": 0.018, "Brick Width": 0.5, "Row Height": 0.18,
                                                                       "Mortar Smooth": 0.2})
    br.inputs["Color1"].default_value = lin(cor); br.inputs["Color2"].default_value = _escurece(cor, 0.78)
    br.inputs["Mortar"].default_value = lin("#cdbfa8"); t.l(v, br.inputs["Vector"])
    var = t.ruido(v, 9 * escala, 3.0, 0.6)
    base = t.mistura(br.outputs["Color"], _escurece(cor, 1.18), t.mat_valor(var, -0.25, 0.35))
    base = t.escorrido(base, desgaste); base = t.sujeira_base(base, sujeira, 0.8)
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.9
    junta = t.n("ShaderNodeMath", operation="SUBTRACT"); junta.inputs[0].default_value = 1.0; t.l(br.outputs["Factor"], junta.inputs[1])
    t.l(t.relevo(junta.outputs[0], 0.5, 0.008), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def pintura(cor="#2f5d62", rug=0.45, metal=0.0, desgaste=0.2):
    chave = ("pintura", cor, rug, metal, desgaste)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("pintura"); v = t.coord("Object")
    var = t.ruido(v, 5.0, 3.0, 0.5)
    base = t.mistura(lin(cor), _escurece(cor, 0.8), t.mat_valor(var, 0.0, 0.5 * desgaste + 0.05))
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Metallic"].default_value = metal
    t.l(t.mat_valor(var, rug - 0.08, rug + 0.12), t.b.inputs["Roughness"])
    return _guardar(chave, t.m)


def vidro(cor="#24323f", reflexo=0.08):
    """Vidro de janela visto de fora: escuro, com reflexo especular (sem transmissão — barato e legível)."""
    chave = ("vidro", cor, reflexo)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("vidro"); t.b.inputs["Base Color"].default_value = lin(cor)
    t.b.inputs["Roughness"].default_value = reflexo; t.b.inputs["Specular IOR Level"].default_value = 0.7
    return _guardar(chave, t.m)


def emissor(cor="#ffd59a", forca=4.0):
    chave = ("emissor", cor, forca)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("emissor"); t.b.inputs["Base Color"].default_value = lin(cor)
    t.b.inputs["Emission Color"].default_value = lin(cor); t.b.inputs["Emission Strength"].default_value = forca
    return _guardar(chave, t.m)


def borracha(cor="#1b1b1d"):
    return pintura(cor, rug=0.85)


def folhagem(cor="#4f7a3a", escala=1.0):
    chave = ("folhagem", cor, escala)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("folhagem"); v = t.coord("Object")
    folhas = t.n("ShaderNodeTexVoronoi", Scale=38 * escala); t.l(v, folhas.inputs["Vector"])
    luz = t.ruido(v, 3.0, 3.0, 0.5)
    base = t.rampa(folhas.outputs["Distance"], [(0.0, _escurece(cor, 1.25)), (0.5, lin(cor)), (1.0, _escurece(cor, 0.55))])
    base = t.mistura(base, _escurece(cor, 0.6), t.mat_valor(luz, 0.0, 0.45))
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.75
    t.l(t.relevo(folhas.outputs["Distance"], 0.6, 0.02), t.b.inputs["Normal"])
    t.b.inputs["Subsurface Weight"].default_value = 0.08
    return _guardar(chave, t.m)


def terra(cor="#5a4632"):
    chave = ("terra", cor)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("terra"); v = t.coord("Object"); r = t.ruido(v, 14.0, 5.0, 0.65)
    t.l(t.rampa(r, [(0.3, _escurece(cor, 0.7)), (0.7, _escurece(cor, 1.2))]), t.b.inputs["Base Color"])
    t.b.inputs["Roughness"].default_value = 0.95; t.l(t.relevo(r, 0.5, 0.02), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


CATALOGO = {"asfalto": asfalto, "concreto": concreto, "reboco": reboco, "tijolo": tijolo, "pintura": pintura, "vidro": vidro,
            "emissor": emissor, "borracha": borracha, "folhagem": folhagem, "terra": terra}


def por_nome(nome, **params):
    return CATALOGO[nome](**params)
