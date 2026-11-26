"""Cenografia — QA da CENA no Blender (E2): roda depois de montar a cena, antes do render.

- nada_flutuando: para cada malha (exceto as marcadas "suspenso": fios, placas, luminárias…), um raio desce do ponto
  mais baixo; a folga até a superfície de baixo tem de ser ≤ 2 cm (ou o objeto está no nível do chão, z ≤ 2 cm).
- textos: todo texto 3D da cena (para conferir com a lista de textos permitidos: nomes inventados e "MODO CURIOSO").
- medidas: dimensões reais de peças de referência (meio-fio, faixa, poste), para conferir a escala.
Não altera nada na cena.
"""
import bpy
from mathutils import Vector

FOLGA_MAX = 0.02


def _bbox_mundo(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), \
        Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))


def _apoio_abaixo(cena, dg, o, ori):
    """Primeira superfície abaixo de 'ori' que NÃO é do próprio objeto (o raio atravessa o objeto e segue)."""
    for _ in range(8):
        ok, loc, _, _, ob, _ = cena.ray_cast(dg, ori, Vector((0, 0, -1)))
        if not ok:
            return None
        if ob is not None and ob.name == o.name:
            ori = loc - Vector((0, 0, 0.0005)); continue
        return loc.z
    return None


def nada_flutuando(cena):
    """Objeto apoiado = existe superfície (de outro objeto) a até 2 cm abaixo do seu ponto mais baixo, ou ele está
    enterrado nela (folga negativa, ex.: tufo de mato no meio-fio), ou está no nível do chão. O raio parte do TOPO do
    objeto e desce atravessando-o (o próprio objeto é ignorado): acha o apoio mesmo quando ele está parcialmente
    enterrado em outra peça."""
    dg = bpy.context.evaluated_depsgraph_get(); flut = []; n = 0
    for o in cena.objects:
        if o.type != "MESH" or o.get("suspenso"):
            continue
        n += 1
        mn, mx = _bbox_mundo(o)
        if mn.z <= FOLGA_MAX:
            continue
        zc = mx.z + 0.001; folgas = []   # parte de CIMA do objeto e desce, pulando o próprio objeto
        for fx, fy in ((0.5, 0.5), (0.25, 0.25), (0.75, 0.75), (0.25, 0.75), (0.75, 0.25)):
            ori = Vector((mn.x + (mx.x - mn.x) * fx, mn.y + (mx.y - mn.y) * fy, zc))
            z_ap = _apoio_abaixo(cena, dg, o, ori)
            folgas.append(mn.z - (z_ap if z_ap is not None else 0.0))
        folga = min(folgas)
        if folga > FOLGA_MAX:
            flut.append({"objeto": o.name, "folga_m": round(folga, 3), "z_min": round(mn.z, 3)})
    return {"malhas_verificadas": n, "flutuando": flut}


def textos(cena):
    return sorted({o.data.body for o in cena.objects if o.type == "FONT"})


def medidas(cena, prefixos=("trecho_1_meiofio", "poste_", "cruz_zebra_p", "trecho_1_pista")):
    out = {}
    for o in cena.objects:
        for pre in prefixos:
            if o.name.startswith(pre) and pre not in out and o.type == "MESH":
                mn, mx = _bbox_mundo(o)
                out[pre] = {"objeto": o.name, "dx": round(mx.x - mn.x, 3), "dy": round(mx.y - mn.y, 3), "dz": round(mx.z - mn.z, 3),
                            "z_topo": round(mx.z, 3)}
    return out


def nada_atravessando(cena):
    """E5: cada peça de ambientação (rótulo 'ambientacao') não pode atravessar a geometria vizinha (BVH, triângulos
    reais; o chão — topo ≤ 20 cm — não conta). O espalhamento já testa na hora de colocar; aqui é a conferência final,
    que pega também o que outro componente pôs depois."""
    from cenografia.componentes.ambientacao import colisoes, _limpar_cache
    _limpar_cache()
    grupos = [o for o in cena.objects if o.get("ambientacao")]; ruins = []
    for g in grupos:
        hits = colisoes(cena, [g] + list(g.children_recursive), ignorar=[g["ignorar_colisao"]] if g.get("ignorar_colisao") else ())
        if hits:
            ruins.append({"peca": g.name, "atravessa": hits[:5]})
    return {"pecas_verificadas": len(grupos), "atravessando": ruins}


def verificar(cena):
    bpy.context.view_layer.update()
    out = {"nada_flutuando": nada_flutuando(cena), "textos": textos(cena), "medidas": medidas(cena)}
    if any(o.get("ambientacao") for o in cena.objects):
        out["nada_atravessando"] = nada_atravessando(cena)
    return out
