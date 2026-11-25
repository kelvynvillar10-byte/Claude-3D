"""Cenografia — biblioteca de MATERIAIS procedurais (E0, roda dentro do bpy).

Estilo aprovado: estilizado com acabamento cinematográfico — textura e desgaste visíveis, sem fotorrealismo.
Tudo é procedural (nós de textura do Blender: ruído, Voronoi, tijolo), sem imagens externas (rede não liberada).
Cada material aceita: cor (hex), escala, desgaste (0–1), sujeira (0–1). Mesmo nome + mesmos parâmetros = mesmo material.

Materiais da E0: asfalto, concreto (placas de calçada), reboco, tijolo, pintura (metal/madeira pintados), vidro,
emissor (luz de janela, luminária), borracha, folhagem, terra.
E1 (bairro urbano brasileiro): calçada portuguesa, ladrilho hidráulico, pastilha, azulejo, telha cerâmica, concreto
aparente, metal com ferrugem, madeira, grama; PALETA_BAIRRO (cores de fachada mais saturadas); UMIDADE (piso molhado:
mais escuro, brilhante e com poças) em asfalto, concreto e calçada portuguesa.
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

    def planar(self):
        """Coordenadas de PAREDE/PISO: os nós de padrão (tijolo, ladrilho, ondas) só usam o plano XY do vetor.
        Paredes (normal horizontal) recebem (u = ao longo da parede, v = altura, w = profundidade); pisos e
        telhados (normal para cima) recebem (x, y, z). Sem isso, numa parede o padrão vira listras."""
        tc = self.n("ShaderNodeTexCoord"); pos = self.n("ShaderNodeSeparateXYZ"); self.l(tc.outputs["Object"], pos.inputs["Vector"])
        nrm = self.n("ShaderNodeSeparateXYZ"); self.l(self.n("ShaderNodeNewGeometry").outputs["Normal"], nrm.inputs["Vector"])
        ab = {k: self.n("ShaderNodeMath", operation="ABSOLUTE") for k in "XYZ"}
        for k in "XYZ":
            self.l(nrm.outputs[k], ab[k].inputs[0])

        def mul_soma(a1, b1, a2, b2):
            m1 = self.n("ShaderNodeMath", operation="MULTIPLY"); self.l(a1, m1.inputs[0]); self.l(b1, m1.inputs[1])
            m2 = self.n("ShaderNodeMath", operation="MULTIPLY"); self.l(a2, m2.inputs[0]); self.l(b2, m2.inputs[1])
            sm = self.n("ShaderNodeMath", operation="ADD"); self.l(m1.outputs[0], sm.inputs[0]); self.l(m2.outputs[0], sm.inputs[1])
            return sm.outputs[0]
        u = mul_soma(pos.outputs["X"], ab["Y"].outputs[0], pos.outputs["Y"], ab["X"].outputs[0])
        w = mul_soma(pos.outputs["X"], ab["X"].outputs[0], pos.outputs["Y"], ab["Y"].outputs[0])
        parede = self.n("ShaderNodeCombineXYZ"); self.l(u, parede.inputs["X"]); self.l(pos.outputs["Z"], parede.inputs["Y"]); self.l(w, parede.inputs["Z"])
        piso = self.n("ShaderNodeCombineXYZ")
        for k in "XYZ":
            self.l(pos.outputs[k], piso.inputs[k])
        eh_piso = self.n("ShaderNodeMath", operation="GREATER_THAN"); self.l(ab["Z"].outputs[0], eh_piso.inputs[0]); eh_piso.inputs[1].default_value = 0.5
        mx = self.n("ShaderNodeMix", data_type="VECTOR"); self.l(eh_piso.outputs[0], mx.inputs["Factor"])
        self.l(parede.outputs[0], mx.inputs[4]); self.l(piso.outputs[0], mx.inputs[5])
        return mx.outputs[1]

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
        r = self.ruido(self.coord("Object", (0.6, 0.6, 0.08)), 4.0, 3.0, 0.6)
        f = self.mat_valor(r, 0.0, 0.55 * desgaste)
        return self.mistura(cor_base, lin("#6b6258"), f, "MULTIPLY")


def _guardar(chave, m):
    _CACHE[chave] = m; return m


def asfalto(cor="#46464a", escala=1.0, desgaste=0.5, sujeira=0.4, umidade=0.0, detalhe=0.0, faixas_x=()):
    """detalhe (E2, 0 = igual à E1): pedrisco graúdo visível, desgaste em manchas médias (óleo, borracha), malha de
    fissuras finas — para o asfalto não ficar liso em plano próximo.
    faixas_x: centros (x, m) das faixas de rolamento: mancha escura de óleo no meio de cada faixa (só pista reta ao longo de y)."""
    chave = ("asfalto", cor, escala, desgaste, sujeira, umidade, detalhe, tuple(faixas_x))
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("asfalto"); v = t.coord("Object")
    grao = t.ruido(v, 180 * escala, 2.0, 0.7)                                   # agregado fino
    manchas = t.ruido(v, 1.2 * escala, 3.0, 0.5)                                # remendos e manchas grandes
    medio = t.ruido(v, 24 * escala, 3.0, 0.6)                                     # agregado médio (pedrisco)
    base = t.rampa(grao, [(0.3, _escurece(cor, 0.6)), (0.55, lin(cor)), (0.78, _escurece(cor, 1.7))])
    base = t.mistura(base, _escurece(cor, 1.35), t.mat_valor(medio, -0.6, 0.45))
    base = t.mistura(base, _escurece(cor, 0.72), t.mat_valor(manchas, -0.2 * desgaste, 0.5 * desgaste))
    # rachaduras: borda de Voronoi em escala grande, afinada
    vor = t.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", Scale=0.35 * escala); t.l(v, vor.inputs["Vector"])
    rach = t.n("ShaderNodeMapRange"); rach.inputs["From Min"].default_value = 0.0; rach.inputs["From Max"].default_value = 0.012 + 0.01 * desgaste
    rach.inputs["To Min"].default_value = desgaste; rach.inputs["To Max"].default_value = 0.0
    t.l(vor.outputs["Distance"], rach.inputs["Value"])
    base = t.mistura(base, lin("#141415"), rach.outputs["Result"])
    if detalhe > 0:
        # o ruído do Blender fica quase sempre entre 0,3 e 0,7: as rampas abaixo são centradas nessa faixa
        pedra = t.ruido(v, 55 * escala, 1.0, 0.4)                                   # pedrisco graúdo, claro
        base = t.mistura(base, _escurece(cor, 1.9), t.mat_valor(pedra, -3.3 * detalhe, 2.4 * detalhe))
        oleo = t.ruido(v, 0.45 * escala, 3.0, 0.6, distorcao=0.6)                    # manchas médias (óleo, borracha)
        base = t.mistura(base, _escurece(cor, 0.42), t.mat_valor(oleo, -2.2 * detalhe, 2.2 * detalhe))
        claro = t.ruido(v, 0.8 * escala, 2.0, 0.5)                                   # asfalto lavado/ressecado (mais claro)
        base = t.mistura(base, _escurece(cor, 1.6), t.mat_valor(claro, -1.6 * detalhe, 1.6 * detalhe))
        vf = t.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", Scale=1.6 * escala); t.l(v, vf.inputs["Vector"])
        fis = t.n("ShaderNodeMapRange"); fis.inputs["From Min"].default_value = 0.0; fis.inputs["From Max"].default_value = 0.022
        fis.inputs["To Min"].default_value = 0.85 * detalhe; fis.inputs["To Max"].default_value = 0.0
        t.l(vf.outputs["Distance"], fis.inputs["Value"])
        msk = t.ruido(v, 0.7 * escala, 2.0, 0.5)                                    # fissuras só em parte da pista
        fm = t.n("ShaderNodeMath", operation="MULTIPLY"); t.l(fis.outputs["Result"], fm.inputs[0]); t.l(t.mat_valor(msk, -3.3, 3.4), fm.inputs[1])
        fc = t.n("ShaderNodeClamp"); t.l(fm.outputs[0], fc.inputs["Value"])
        base = t.mistura(base, lin("#1a1a1c"), fc.outputs["Result"])
        if faixas_x:   # óleo pingado no centro de cada faixa (faixa escura contínua, com falhas)
            sx = t.n("ShaderNodeSeparateXYZ"); t.l(v, sx.inputs["Vector"]); soma = None
            for xc in faixas_x:
                d = t.n("ShaderNodeMath", operation="SUBTRACT"); t.l(sx.outputs["X"], d.inputs[0]); d.inputs[1].default_value = xc
                a = t.n("ShaderNodeMath", operation="ABSOLUTE"); t.l(d.outputs[0], a.inputs[0])
                b = t.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP"); b.inputs["From Min"].default_value = 0.12
                b.inputs["From Max"].default_value = 0.5; b.inputs["To Min"].default_value = 1.0; b.inputs["To Max"].default_value = 0.0
                t.l(a.outputs[0], b.inputs["Value"])
                if soma is None:
                    soma = b.outputs["Result"]
                else:
                    mx_ = t.n("ShaderNodeMath", operation="MAXIMUM"); t.l(soma, mx_.inputs[0]); t.l(b.outputs["Result"], mx_.inputs[1]); soma = mx_.outputs[0]
            fal = t.ruido(v, 0.9 * escala, 3.0, 0.6)
            k = t.n("ShaderNodeMath", operation="MULTIPLY"); t.l(soma, k.inputs[0]); t.l(t.mat_valor(fal, -0.6 * detalhe, 1.6 * detalhe), k.inputs[1])
            kc = t.n("ShaderNodeClamp"); t.l(k.outputs[0], kc.inputs["Value"])
            base = t.mistura(base, _escurece(cor, 0.5), kc.outputs["Result"])
    if umidade > 0:
        _umidade(t, base, 0.88, umidade, v)
    else:
        t.l(base, t.b.inputs["Base Color"])
        t.l(t.mat_valor(grao, 0.78, 0.95), t.b.inputs["Roughness"])
    alt = t.n("ShaderNodeMath", operation="SUBTRACT"); t.l(grao, alt.inputs[0]); t.l(rach.outputs["Result"], alt.inputs[1])
    t.l(t.relevo(alt.outputs[0], 0.25, 0.01), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def concreto(cor="#a9a397", escala=1.0, desgaste=0.4, sujeira=0.3, placa_m=(1.0, 1.0), umidade=0.0, detalhe=0.0):
    """Placas de calçada: juntas pelo nó de tijolo (sem deslocamento entre fileiras).
    detalhe (E2, 0 = igual à E1): tom diferente por placa, granulado e manchas pequenas."""
    chave = ("concreto", cor, escala, desgaste, sujeira, placa_m, umidade, detalhe)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("concreto"); v = t.planar()
    br = t.n("ShaderNodeTexBrick", offset=0.0, squash=1.0, Scale=1.0 / placa_m[0], **{"Mortar Size": 0.012, "Brick Width": 1.0,
                                                                                        "Row Height": placa_m[1] / placa_m[0], "Bias": 0.0})
    br.inputs["Color1"].default_value = lin(cor); br.inputs["Color2"].default_value = _escurece(cor, 0.9)
    br.inputs["Mortar"].default_value = _escurece(cor, 0.45); t.l(v, br.inputs["Vector"])
    mancha = t.ruido(v, 2.5 * escala, 4.0, 0.6)
    base = t.mistura(br.outputs["Color"], _escurece(cor, 0.7), t.mat_valor(mancha, -0.3, 0.5 * desgaste + 0.1))
    if detalhe > 0:
        cel = t.n("ShaderNodeTexVoronoi", feature="F1", Scale=1.0 / max(placa_m[0], 0.3)); t.l(v, cel.inputs["Vector"])
        base = t.mistura(base, _escurece(cor, 0.78), t.mat_valor(cel.outputs["Distance"], -0.2 * detalhe, 0.55 * detalhe))   # placa a placa
        base = t.mistura(base, _escurece(cor, 1.18), t.mat_valor(cel.outputs["Color"], -0.6 * detalhe, 0.6 * detalhe))
        gr = t.ruido(v, 70 * escala, 2.0, 0.7)                                       # granulado
        base = t.mistura(base, _escurece(cor, 0.8), t.mat_valor(gr, -0.8 * detalhe, 1.6 * detalhe))
        mc = t.ruido(v, 5.0 * escala, 3.0, 0.6)                                      # manchas pequenas (chiclete, goteira)
        base = t.mistura(base, _escurece(cor, 0.62), t.mat_valor(mc, -2.85 * detalhe, 1.75 * detalhe))
    base = t.sujeira_base(base, sujeira, 0.25)
    _umidade(t, base, 0.88, umidade, v)
    junta = t.n("ShaderNodeMath", operation="SUBTRACT"); junta.inputs[0].default_value = 1.0; t.l(br.outputs["Factor"], junta.inputs[1])
    t.l(t.relevo(junta.outputs[0], 0.35, 0.01), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def reboco(cor="#e2c9a4", escala=1.0, desgaste=0.35, sujeira=0.35, detalhe=0.0):
    """detalhe (E3, 0 = igual à E1): manchas de repintura em placas, variação média de tom e granulado — para paredes
    grandes não lerem como cor chapada."""
    chave = ("reboco", cor, escala, desgaste, sujeira, detalhe)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("reboco"); v = t.coord("Object")
    textura = t.ruido(v, 22 * escala, 5.0, 0.6)
    nuvem = t.ruido(v, 0.8 * escala, 3.0, 0.5)
    base = t.rampa(nuvem, [(0.25, _escurece(cor, 0.86)), (0.6, lin(cor)), (0.85, _escurece(cor, 1.06))])
    if detalhe > 0:   # rampas centradas na faixa real do ruído (0,3–0,7)
        cel = t.n("ShaderNodeTexVoronoi", feature="F1", Scale=0.45 * escala, Randomness=0.8); t.l(v, cel.inputs["Vector"])
        base = t.mistura(base, _escurece(cor, 0.8), t.mat_valor(cel.outputs["Color"], -0.4 * detalhe, 1.0 * detalhe))      # repintura
        base = t.mistura(base, _escurece(cor, 1.12), t.mat_valor(cel.outputs["Distance"], 0.6 * detalhe, -0.4 * detalhe))  # bordas
        med = t.ruido(v, 3.0 * escala, 3.0, 0.6)
        base = t.mistura(base, _escurece(cor, 0.74), t.mat_valor(med, -1.4 * detalhe, 2.2 * detalhe))
        gr = t.ruido(v, 40 * escala, 2.0, 0.7)
        base = t.mistura(base, _escurece(cor, 0.86), t.mat_valor(gr, -0.6 * detalhe, 1.4 * detalhe))
    base = t.escorrido(base, desgaste)
    base = t.sujeira_base(base, sujeira, 1.0)
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.92
    t.l(t.relevo(textura, 0.18, 0.004), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def tijolo(cor="#9c4f35", escala=1.0, desgaste=0.3, sujeira=0.3):
    chave = ("tijolo", cor, escala, desgaste, sujeira)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("tijolo"); v = t.planar()
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


# ------------------------------------------------------------------ E1
PALETA_BAIRRO = {   # cores de fachada e acabamento típicas de bairro brasileiro (mais saturadas que a E0)
    "amarelo_ocre": "#e3a12f", "terracota": "#c25a36", "verde_agua": "#4fae9c", "azul_colonial": "#3a78c2",
    "rosa_salmao": "#e8806c", "lilas": "#9278c4", "creme": "#f0d29a", "verde_musgo": "#6a8f3a", "branco_gelo": "#ede6d8",
    "vermelho_tijolo": "#a8442b", "azul_piscina": "#3fa7d6", "laranja_queimado": "#d9702c",
}


def _umidade(t, base, rug_seco, umidade, v, poca_escala=0.35):
    """Piso molhado: escurece, baixa a rugosidade e cria poças (máscara de ruído) quase espelhadas."""
    if umidade <= 0:
        t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = rug_seco
        return
    poca = t.ruido(v, poca_escala * 2.2, 3.0, 0.55)   # poças menores e mais recortadas
    m = t.n("ShaderNodeMapRange"); m.inputs["From Min"].default_value = 0.66 - 0.08 * umidade; m.inputs["From Max"].default_value = 0.69 - 0.08 * umidade
    t.l(poca, m.inputs["Value"])
    molhado = t.mistura(base, (0.0, 0.0, 0.0, 1.0), 0.38 * umidade, "MIX")
    t.l(t.mistura(molhado, _escurece("#2a2c30", 1.0), m.outputs["Result"]), t.b.inputs["Base Color"])
    r = t.n("ShaderNodeMapRange"); r.inputs["To Min"].default_value = rug_seco * (1 - 0.7 * umidade); r.inputs["To Max"].default_value = 0.03
    t.l(m.outputs["Result"], r.inputs["Value"]); t.l(r.outputs["Result"], t.b.inputs["Roughness"])


def calcada_portuguesa(cor_a="#ece6da", cor_b="#2c2c30", escala=1.0, onda_m=1.6, desgaste=0.3, sujeira=0.3, umidade=0.0):
    """Pedras pequenas (Voronoi) com rejunte, em ondas preto e branco (padrão de calçada portuguesa)."""
    chave = ("calcada_portuguesa", cor_a, cor_b, escala, onda_m, desgaste, sujeira, umidade)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("calcada_portuguesa"); v = t.coord("Object")
    pedras = t.n("ShaderNodeTexVoronoi", Scale=22 * escala); t.l(v, pedras.inputs["Vector"])
    borda = t.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", Scale=22 * escala); t.l(v, borda.inputs["Vector"])
    # padrão de ondas avaliado no centro de cada pedra (cada pedra é preta OU branca, como na calçada real)
    sep = t.n("ShaderNodeSeparateXYZ"); t.l(pedras.outputs["Position"], sep.inputs["Vector"])
    k = 6.2832 / onda_m
    sy = t.n("ShaderNodeMath", operation="MULTIPLY"); t.l(sep.outputs["Y"], sy.inputs[0]); sy.inputs[1].default_value = k * 0.5
    sin_y = t.n("ShaderNodeMath", operation="SINE"); t.l(sy.outputs[0], sin_y.inputs[0])
    amp = t.n("ShaderNodeMath", operation="MULTIPLY"); t.l(sin_y.outputs[0], amp.inputs[0]); amp.inputs[1].default_value = 0.35 * onda_m
    sx = t.n("ShaderNodeMath", operation="ADD"); t.l(sep.outputs["X"], sx.inputs[0]); t.l(amp.outputs[0], sx.inputs[1])
    kx = t.n("ShaderNodeMath", operation="MULTIPLY"); t.l(sx.outputs[0], kx.inputs[0]); kx.inputs[1].default_value = k
    onda = t.n("ShaderNodeMath", operation="SINE"); t.l(kx.outputs[0], onda.inputs[0])
    faixa = t.n("ShaderNodeMath", operation="GREATER_THAN"); t.l(onda.outputs[0], faixa.inputs[0]); faixa.inputs[1].default_value = 0.35
    cor = t.mistura(lin(cor_a), lin(cor_b), faixa.outputs[0])
    var = t.mat_valor(pedras.outputs["Distance"], 0.0, 0.25)
    cor = t.mistura(cor, _escurece(cor_a, 0.7), var)
    rej = t.n("ShaderNodeMapRange"); rej.inputs["From Min"].default_value = 0.0; rej.inputs["From Max"].default_value = 0.06
    rej.inputs["To Min"].default_value = 1.0; rej.inputs["To Max"].default_value = 0.0; t.l(borda.outputs["Distance"], rej.inputs["Value"])
    cor = t.mistura(cor, lin("#7d756a"), rej.outputs["Result"])
    cor = t.sujeira_base(cor, sujeira, 0.2) if sujeira else cor
    _umidade(t, cor, 0.8, umidade, v)
    alt = t.n("ShaderNodeMath", operation="SUBTRACT"); alt.inputs[0].default_value = 1.0; t.l(rej.outputs["Result"], alt.inputs[1])
    t.l(t.relevo(alt.outputs[0], 0.45, 0.012), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def _grade_local(t, v, tam_m):
    """Coordenada local dentro de cada ladrilho: (fract(p/tam) − 0,5)."""
    mp = t.n("ShaderNodeVectorMath", operation="DIVIDE"); t.l(v, mp.inputs[0]); mp.inputs[1].default_value = (tam_m, tam_m, tam_m)
    fr = t.n("ShaderNodeVectorMath", operation="FRACTION"); t.l(mp.outputs[0], fr.inputs[0])
    sub = t.n("ShaderNodeVectorMath", operation="SUBTRACT"); t.l(fr.outputs[0], sub.inputs[0]); sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    sep = t.n("ShaderNodeSeparateXYZ"); t.l(sub.outputs[0], sep.inputs["Vector"])
    xy = t.n("ShaderNodeCombineXYZ"); t.l(sep.outputs["X"], xy.inputs["X"]); t.l(sep.outputs["Y"], xy.inputs["Y"])   # só o plano do ladrilho
    return xy.outputs[0]


def ladrilho_hidraulico(cor_fundo="#e8dcc4", cor_a="#b7452f", cor_b="#2f5f8a", tam_m=0.2, desgaste=0.35, sujeira=0.3):
    """Ladrilho de 20 cm com motivo geométrico (losango + círculo) e rejunte."""
    chave = ("ladrilho_hidraulico", cor_fundo, cor_a, cor_b, tam_m, desgaste, sujeira)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("ladrilho_hidraulico"); v = t.planar(); q = _grade_local(t, v, tam_m)
    sep = t.n("ShaderNodeSeparateXYZ"); t.l(q, sep.inputs["Vector"])
    ax = t.n("ShaderNodeMath", operation="ABSOLUTE"); t.l(sep.outputs["X"], ax.inputs[0])
    ay = t.n("ShaderNodeMath", operation="ABSOLUTE"); t.l(sep.outputs["Y"], ay.inputs[0])
    los = t.n("ShaderNodeMath", operation="ADD"); t.l(ax.outputs[0], los.inputs[0]); t.l(ay.outputs[0], los.inputs[1])
    raio = t.n("ShaderNodeVectorMath", operation="LENGTH"); t.l(q, raio.inputs[0])
    m_los = t.n("ShaderNodeMath", operation="LESS_THAN"); t.l(los.outputs[0], m_los.inputs[0]); m_los.inputs[1].default_value = 0.42
    m_circ = t.n("ShaderNodeMath", operation="LESS_THAN"); t.l(raio.outputs["Value"], m_circ.inputs[0]); m_circ.inputs[1].default_value = 0.16
    cor = t.mistura(lin(cor_fundo), lin(cor_a), m_los.outputs[0])
    cor = t.mistura(cor, lin(cor_b), m_circ.outputs[0])
    mx = t.n("ShaderNodeMath", operation="MAXIMUM"); t.l(ax.outputs[0], mx.inputs[0]); t.l(ay.outputs[0], mx.inputs[1])
    rej = t.n("ShaderNodeMath", operation="GREATER_THAN"); t.l(mx.outputs[0], rej.inputs[0]); rej.inputs[1].default_value = 0.485
    cor = t.mistura(cor, lin("#9c9284"), rej.outputs[0])
    gasto = t.ruido(v, 3.0, 4.0, 0.6)
    cor = t.mistura(cor, _escurece(cor_fundo, 0.75), t.mat_valor(gasto, -0.2, 0.45 * desgaste))
    cor = t.sujeira_base(cor, sujeira, 0.15) if sujeira else cor
    t.l(cor, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.55
    inv = t.n("ShaderNodeMath", operation="SUBTRACT"); inv.inputs[0].default_value = 1.0; t.l(rej.outputs[0], inv.inputs[1])
    t.l(t.relevo(inv.outputs[0], 0.3, 0.004), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def _azulejado(nome, cor, tam_m, rejunte, rug, variacao, chave_extra=()):
    chave = (nome, cor, tam_m, rejunte, rug, variacao) + chave_extra
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT(nome); v = t.planar()
    br = t.n("ShaderNodeTexBrick", offset=0.0, squash=1.0, Scale=1.0 / tam_m, **{"Mortar Size": rejunte, "Brick Width": 1.0, "Row Height": 1.0, "Bias": 0.0})
    br.inputs["Color1"].default_value = lin(cor); br.inputs["Color2"].default_value = _escurece(cor, 1.0 - variacao)
    br.inputs["Mortar"].default_value = lin("#d8d0c2"); t.l(v, br.inputs["Vector"])
    suj = t.ruido(v, 2.0, 3.0, 0.5)
    cor_f = t.mistura(br.outputs["Color"], _escurece(cor, 0.8), t.mat_valor(suj, -0.2, 0.25))
    t.l(cor_f, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = rug
    inv = t.n("ShaderNodeMath", operation="SUBTRACT"); inv.inputs[0].default_value = 1.0; t.l(br.outputs["Factor"], inv.inputs[1])
    t.l(t.relevo(inv.outputs[0], 0.4, 0.003), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def pastilha(cor="#3fa7d6", tam_m=0.025):
    """Pastilha de 2,5 cm (fachadas anos 70), cada peça com tom levemente diferente, vitrificada."""
    return _azulejado("pastilha", cor, tam_m, 0.08, 0.25, 0.22)


def azulejo(cor="#f2efe6", tam_m=0.15):
    return _azulejado("azulejo", cor, tam_m, 0.025, 0.12, 0.05)


def telha_ceramica(cor="#b5532f", escala=1.0, desgaste=0.4):
    """Telha capa-canal: ondas ao longo de x, fileiras ao longo de y, manchas de musgo e sujeira."""
    chave = ("telha", cor, escala, desgaste)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("telha_ceramica"); v = t.planar()
    onda = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", Scale=3.2 * escala, Distortion=0.0); t.l(v, onda.inputs["Vector"])
    fila = t.n("ShaderNodeTexBrick", offset=0.0, Scale=2.0 * escala, **{"Mortar Size": 0.02, "Brick Width": 4.0, "Row Height": 0.45})
    fila.inputs["Color1"].default_value = lin(cor); fila.inputs["Color2"].default_value = _escurece(cor, 0.85)
    fila.inputs["Mortar"].default_value = _escurece(cor, 0.4); t.l(v, fila.inputs["Vector"])
    musgo = t.ruido(v, 1.5, 4.0, 0.6)
    cor_f = t.mistura(fila.outputs["Color"], lin("#4f5a2e"), t.mat_valor(musgo, -0.4, 0.5 * desgaste))
    cor_f = t.mistura(cor_f, _escurece(cor, 0.6), t.mat_valor(onda.outputs["Factor"], 0.0, 0.35))
    t.l(cor_f, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.8
    t.l(t.relevo(onda.outputs["Factor"], 0.8, 0.04), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def concreto_aparente(cor="#9d9a93", tabua_m=0.18, desgaste=0.4):
    """Concreto de fôrma de tábua: faixas horizontais, veios e furos de amarração."""
    chave = ("concreto_aparente", cor, tabua_m, desgaste)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("concreto_aparente"); v = t.planar()
    tab = t.n("ShaderNodeTexBrick", offset=0.37, Scale=1.0 / 1.2, **{"Mortar Size": 0.006, "Brick Width": 1.2, "Row Height": tabua_m / 1.2})
    tab.inputs["Color1"].default_value = lin(cor); tab.inputs["Color2"].default_value = _escurece(cor, 0.88)
    tab.inputs["Mortar"].default_value = _escurece(cor, 0.7); t.l(v, tab.inputs["Vector"])
    veio = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", Scale=9.0, Distortion=6.0, **{"Detail": 3.0}); t.l(v, veio.inputs["Vector"])
    cor_f = t.mistura(tab.outputs["Color"], _escurece(cor, 0.8), t.mat_valor(veio.outputs["Factor"], 0.0, 0.18))
    cor_f = t.escorrido(cor_f, desgaste)
    t.l(cor_f, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.85
    t.l(t.relevo(veio.outputs["Factor"], 0.15, 0.003), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def metal_ferrugem(cor="#2f6f5f", ferrugem=0.45):
    """Metal pintado (portão, grade) com ferrugem nas manchas: a tinta descasca e a rugosidade sobe."""
    chave = ("metal_ferrugem", cor, ferrugem)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("metal_ferrugem"); v = t.coord("Object")
    r = t.ruido(v, 4.0, 6.0, 0.65)
    m = t.n("ShaderNodeMapRange"); m.inputs["From Min"].default_value = 0.62 - 0.25 * ferrugem; m.inputs["From Max"].default_value = 0.66 - 0.25 * ferrugem
    t.l(r, m.inputs["Value"])
    ferr = t.rampa(t.ruido(v, 25.0, 3.0, 0.6), [(0.3, lin("#5a2a14")), (0.7, lin("#a4541f"))])
    t.l(t.mistura(lin(cor), ferr, m.outputs["Result"]), t.b.inputs["Base Color"])
    t.l(t.mat_valor(m.outputs["Result"], 0.38, 0.9), t.b.inputs["Roughness"])
    t.l(t.mat_valor(m.outputs["Result"], 0.35, 0.0), t.b.inputs["Metallic"])
    t.l(t.relevo(m.outputs["Result"], 0.3, 0.004), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def madeira(cor="#8a5a3b", escala=1.0, pintada=None):
    chave = ("madeira", cor, escala, pintada)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("madeira"); v = t.coord("Object", (1.0, 1.0, 0.08))
    veio = t.n("ShaderNodeTexWave", wave_type="RINGS", Scale=6.0 * escala, Distortion=8.0, **{"Detail": 4.0}); t.l(v, veio.inputs["Vector"])
    base = t.rampa(veio.outputs["Factor"], [(0.2, _escurece(cor, 0.7)), (0.8, _escurece(cor, 1.15))])
    if pintada:
        descasca = t.ruido(t.coord("Object"), 6.0, 5.0, 0.6)
        mk = t.n("ShaderNodeMapRange"); mk.inputs["From Min"].default_value = 0.6; mk.inputs["From Max"].default_value = 0.63; t.l(descasca, mk.inputs["Value"])
        base = t.mistura(lin(pintada), base, mk.outputs["Result"])
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.7
    t.l(t.relevo(veio.outputs["Factor"], 0.2, 0.004), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def grama(cor="#5d8a35", escala=1.0, seca=0.2):
    chave = ("grama", cor, escala, seca)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("grama"); v = t.coord("Object")
    fino = t.ruido(v, 90 * escala, 2.0, 0.8); manchas = t.ruido(v, 1.2 * escala, 3.0, 0.5)
    base = t.rampa(fino, [(0.3, _escurece(cor, 0.6)), (0.7, _escurece(cor, 1.2))])
    base = t.mistura(base, lin("#a5944f"), t.mat_valor(manchas, -0.3, 0.7 * seca))
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.9
    t.l(t.relevo(fino, 0.6, 0.02), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def chapa_ondulada(cor="#8a9098", passo_m=0.08, desgaste=0.4, metal=0.35):
    """E3: porta de enrolar / chapa canelada — nervuras HORIZONTAIS (paredes: v = altura), com sujeira embaixo."""
    chave = ("chapa_ondulada", cor, passo_m, desgaste, metal)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("chapa_ondulada"); v = t.planar()
    w = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SIN", Scale=6.2832 / (10.0 * passo_m),
            Distortion=0.0, Detail=0.0); t.l(v, w.inputs["Vector"])
    base = t.mistura(_escurece(cor, 0.78), _escurece(cor, 1.12), w.outputs["Factor"])
    var = t.ruido(v, 3.0, 3.0, 0.6)
    base = t.mistura(base, _escurece(cor, 0.62), t.mat_valor(var, -0.4, 0.7 * desgaste))
    base = t.sujeira_base(base, 0.35 * desgaste + 0.1, 0.6)
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Metallic"].default_value = metal
    t.l(t.mat_valor(var, 0.38, 0.62), t.b.inputs["Roughness"])
    t.l(t.relevo(w.outputs["Factor"], 0.6, 0.01), t.b.inputs["Normal"])
    return _guardar(chave, t.m)


def listrado(cor_a="#c8382f", cor_b="#f1e9d8", largura_m=0.25, desgaste=0.3):
    """E3: lona de toldo com listras perpendiculares à fachada (variam ao longo de y LOCAL do objeto), desbotada pelo sol."""
    chave = ("listrado", cor_a, cor_b, largura_m, desgaste)
    if chave in _CACHE:
        return _CACHE[chave]
    t = _NT("listrado"); v = t.coord("Object")     # no kit de prédios, y local = ao longo da fachada
    sx = t.n("ShaderNodeSeparateXYZ"); t.l(v, sx.inputs["Vector"])
    k = t.n("ShaderNodeMath", operation="DIVIDE"); t.l(sx.outputs["Y"], k.inputs[0]); k.inputs[1].default_value = 2 * largura_m
    fr = t.n("ShaderNodeMath", operation="FRACT"); t.l(k.outputs[0], fr.inputs[0])
    st = t.n("ShaderNodeMath", operation="GREATER_THAN"); t.l(fr.outputs[0], st.inputs[0]); st.inputs[1].default_value = 0.5
    base = t.mistura(lin(cor_a), lin(cor_b), st.outputs[0])
    var = t.ruido(v, 1.5, 3.0, 0.5)
    base = t.mistura(base, lin("#f4efe4"), t.mat_valor(var, -0.2, 0.35 * desgaste))     # desbotado
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.85
    t.b.inputs["Sheen Weight"].default_value = 0.3
    return _guardar(chave, t.m)


CATALOGO = {"asfalto": asfalto, "concreto": concreto, "reboco": reboco, "tijolo": tijolo, "pintura": pintura, "vidro": vidro,
            "emissor": emissor, "borracha": borracha, "folhagem": folhagem, "terra": terra,
            "calcada_portuguesa": calcada_portuguesa, "ladrilho_hidraulico": ladrilho_hidraulico, "pastilha": pastilha,
            "azulejo": azulejo, "telha_ceramica": telha_ceramica, "concreto_aparente": concreto_aparente,
            "metal_ferrugem": metal_ferrugem, "madeira": madeira, "grama": grama,
            "chapa_ondulada": chapa_ondulada, "listrado": listrado}


def por_nome(nome, **params):
    return CATALOGO[nome](**params)
