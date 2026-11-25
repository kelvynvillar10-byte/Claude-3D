#!/usr/bin/env python3
"""Cenografia — constrói a PLACA de uma receita (E0).

Uso: .venv/bin/python cenografia/construir.py cenografia/receitas/e0_esquina.json [--forcar] [--destino DIR]

1. Calcula a chave (hash da receita + versão do núcleo + código dos geradores).
2. Se o cache tem essa chave íntegra → não renderiza nada (cache hit).
3. Senão: monta a cena no Blender (componentes registrados), renderiza cada camada com grupos de luz,
   grava EXR + manifesto (tempos, intrínsecos da câmera, âncoras, hash de cada arquivo).
"""
import json, shutil, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from cenografia.nucleo import receita as R, cache as C   # noqa: E402


def _montar(r):
    import bpy
    from cenografia.nucleo import geometria as G, luz as L, camera as CAM, materiais as M, render as RD, registro as REG
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M._CACHE.clear()
    REG.carregar_kits()
    cena = bpy.context.scene
    RD.configurar(cena, r["saida"]["amostras"], r["semente"], R.GRUPOS_LUZ)
    P = L.ceu_e_sol(r["luz"]["preset"])
    cam, W, H = CAM.criar(r["camera"], r["saida"])
    cols = {c: G.colecao(f"camada_{c}") for c in r["camadas"] if c != "ceu"}
    ctx = {"cena": cena, "receita": r}
    t = time.time()
    for i, comp in enumerate(r["componentes"]):
        REG.REGISTRO[comp["tipo"]](ctx, comp.get("params", {}), R.rng(r["semente"], i, comp["tipo"]), cols[comp.get("camada", "meio")])
    for i, e in enumerate(r["luz"].get("efeito", [])):   # luzes de efeito: intensidade unitária, escaladas no compositor
        L.luz_ponto(f"efeito_{i}", e["pos"], e.get("watts", 100.0), e.get("cor", "#ffffff"), "efeito", raio=e.get("raio", 0.1))
    t_montagem = time.time() - t
    ancoras = {k: CAM.projetar(cam, v, W, H) for k, v in r.get("ancoras", {}).items()}
    return bpy, cena, cam, W, H, cols, P, ancoras, t_montagem


def construir(caminho_ou_receita, forcar=False, destino=None):
    r = R.carregar(caminho_ou_receita) if not isinstance(caminho_ou_receita, dict) else R.validar(dict(caminho_ou_receita))
    k = R.chave(r)
    if destino is None and not forcar and C.valido(k):
        return k, C.manifesto(k), True
    pasta = Path(destino) if destino else C.pasta(k)
    if pasta.exists():
        shutil.rmtree(pasta)
    pasta.mkdir(parents=True)
    t0 = time.time()
    bpy, cena, cam, W, H, cols, P, ancoras, t_mont = _montar(r)
    from cenografia.nucleo import render as RD, camera as CAM
    tempos = {}
    for c in r["camadas"]:
        tempos[c] = RD.render_camada(cena, cols, c, pasta / c, R.GRUPOS_LUZ)
    meta = {"receita": r, "versao_nucleo": R.VERSAO_NUCLEO, "resolucao": [W, H], "camadas": r["camadas"], "grupos_luz": R.GRUPOS_LUZ,
            "pesos_padrao": P["pesos"], "preset_luz": r["luz"]["preset"], "sol_dir": P["sol_dir"], "noite": bool(P.get("noite")),
            "intrinsecos": CAM.intrinsecos(cam, W, H), "ancoras": ancoras,
            "tempo_montagem_s": round(t_mont, 2), "tempo_render_s": tempos, "tempo_total_s": round(time.time() - t0, 2),
            "objetos": len(cena.objects), "amostras": r["saida"]["amostras"], "blender": bpy.app.version_string}
    if destino:
        (pasta / "manifest.json").write_text(json.dumps(dict(meta, chave=k, estado="completo"), ensure_ascii=False, indent=1))
        return k, meta, False
    return k, C.gravar_manifesto(k, meta), False


def render_verificacao(caminho_ou_receita, destino, cam=None, luzes=None):
    """Render COMPLETO de verificação (todas as camadas visíveis, uma imagem), para comparar com o compositor:
    cam = {tx, ty, tz} em metros no referencial da câmera (direita, cima, frente);
    luzes = {grupo: (fator, cor_hex|None)} aplicados às luzes REAIS da cena (céu, sol, lâmpadas, emissores)."""
    import bpy
    from mathutils import Vector
    from cenografia.nucleo import render as RD
    from cenografia.nucleo.materiais import lin
    r = R.carregar(caminho_ou_receita) if not isinstance(caminho_ou_receita, dict) else R.validar(dict(caminho_ou_receita))
    bpy_, cena, camobj, W, H, cols, P, ancoras, _ = _montar(r)
    cam = cam or {}; luzes = luzes or {}
    m = camobj.matrix_world.to_3x3()
    camobj.location = camobj.location + m @ Vector((cam.get("tx", 0.0), cam.get("ty", 0.0), -cam.get("tz", 0.0)))

    def tinta(cor):
        return Vector(lin(cor)[:3]) if cor else Vector((1, 1, 1))
    for g, (f, cor) in luzes.items():
        t = tinta(cor)
        if g == "ceu":
            bg = cena.world.node_tree.nodes["Background"]; bg.inputs["Strength"].default_value *= f
            if cor:
                nt = cena.world.node_tree; ceu = [n for n in nt.nodes if n.bl_idname == "ShaderNodeTexSky"][0]
                mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
                nt.links.new(ceu.outputs["Color"], mx.inputs[6]); mx.inputs[7].default_value = lin(cor); nt.links.new(mx.outputs[2], bg.inputs["Color"])
            continue
        for o in cena.objects:
            if o.lightgroup != g:
                continue
            if o.type == "LIGHT":
                o.data.energy *= f; o.data.color = Vector(o.data.color) * t
            elif o.type == "MESH":
                for ms in o.material_slots:
                    b = ms.material.node_tree.nodes["Principled BSDF"]
                    if not ms.material.get("_escalado"):
                        b.inputs["Emission Strength"].default_value *= f
                        b.inputs["Emission Color"].default_value = tuple(Vector(b.inputs["Emission Color"].default_value[:3]) * t) + (1.0,)
                        ms.material["_escalado"] = True
    for o in cena.objects:
        if o.type in ("MESH", "CURVE", "EMPTY"):
            o.visible_camera = True
    cena.render.film_transparent = False
    Path(destino).mkdir(parents=True, exist_ok=True)
    RD._grafo(cena, Path(destino), R.GRUPOS_LUZ)
    t = time.time(); bpy.ops.render.render(write_still=False)
    return round(time.time() - t, 2)


if __name__ == "__main__":
    args = sys.argv[1:]
    forcar = "--forcar" in args
    destino = args[args.index("--destino") + 1] if "--destino" in args else None
    k, m, hit = construir(args[0], forcar=forcar, destino=destino)
    print(json.dumps({"chave": k[:16], "cache": "HIT" if hit else "MISS", "tempo_render_s": m["tempo_render_s"],
                      "tempo_total_s": m["tempo_total_s"]}, ensure_ascii=False))
