#!/usr/bin/env python3
"""Cenografia — testes da etapa E3 (prédios). Renderiza, MEDE e documenta.

E3-1 folha de variações: 3 estilos (residencial, comercial, sobrado) × 4 sementes, um lote por célula.
E3-2 cenas de prova: o quarteirão da E2 com os prédios da E3 (calçada e esquina na tarde, calçada à noite, esquina
     com chuva), 1080×1920, com o Heitor rig v2 parado para escala. Tempo real por placa e por camada.
E3-3 QA da cena: nada flutuando, textos 3D × lista permitida (palavras comuns + números só com algarismos), escala
     dos prédios (pé-direito, alturas, janelas), instâncias.
E3-4 área vazia: E3 × E2 nas mesmas câmeras.
E3-5 determinismo (mesma semente → mesma geometria; outra semente → outros prédios) e cache.
E3-6 integridade (rig v2, ID-001..ID-004, skill) e paleta do Heitor no quadro.
Saídas: cenografia/testes/e3/. Placas: .cache/ (fora do Git).
"""
import copy, hashlib, json, re, sys, time
from pathlib import Path
import numpy as np, cv2

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia import construir as CO                                    # noqa: E402
from cenografia.nucleo import receita as R, cache as C, medidas as MD      # noqa: E402
from cenografia.nucleo.compositor import Placa                            # noqa: E402
from cenografia.nucleo.atmosfera import Atmosfera                         # noqa: E402
import e0_testes as T0                                                     # noqa: E402
import e1_testes as T1                                                     # noqa: E402
import e2_testes as T2                                                     # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e3"; OUT.mkdir(parents=True, exist_ok=True)
REC = RAIZ / "cenografia" / "receitas" / "e3_quarteirao.json"
W, H = 1080, 1920
CAMS = T2.CAMS
CENAS = [("calcada_tarde", "calcada", "tarde_dourada", "limpo"), ("esquina_tarde", "esquina", "tarde_dourada", "limpo"),
         ("calcada_noite", "calcada", "noite", "limpo"), ("esquina_chuva", "esquina", "tarde_dourada", "chuva")]
NOMES = {"calcada_tarde": "calçada · tarde dourada", "esquina_tarde": "esquina · tarde dourada",
         "calcada_noite": "calçada · noite", "esquina_chuva": "esquina · chuva (piso molhado)"}
NUMERO = re.compile(r"^\d{1,4}$")
res = {}


def receita(cam, horario="tarde_dourada", molhado=False):
    r = R.carregar(REC); c = CAMS[cam]; r["camera"] = copy.deepcopy(c["camera"]); r["luz"]["preset"] = horario
    if c["heitor"]:
        x, y, z = c["heitor"]; r["ancoras"] = {"heitor_pe": [x, y, z], "heitor_topo": [x, y, z + 1.4]}
    else:
        r["ancoras"] = {}
    if molhado:
        for comp in r["componentes"]:
            if comp["tipo"] in ("rua_trecho", "cruzamento"):
                comp["params"]["umidade"] = 0.85
    return r


def placa(cam, horario="tarde_dourada", molhado=False):
    k, m, hit = CO.construir(receita(cam, horario, molhado))
    return Placa(C.pasta(k)), m, hit


def texto_ok(t, permitidos):
    return t in permitidos or bool(NUMERO.match(t))


# ------------------------------------------------------------------ E3-1
LARGURAS = {"residencial": [11.0, 13.0, 12.0, 14.0], "comercial": [7.0, 10.0, 8.5, 11.0], "sobrado": [7.0, 8.0, 6.5, 8.5]}


def receita_celula(estilo, i):
    r = R.carregar(REC); L = LARGURAS[estilo][i]
    r["nome"] = f"e3_variacao_{estilo}_{i}"; r["semente"] = 500 + 10 * list(LARGURAS).index(estilo) + i
    r["saida"].update(largura=540, altura=960); r["saida"]["amostras_por_camada"] = {"ceu": 4, "meio": 16}
    r["camera"] = {"pos": [5.0, L / 2, 1.6], "alvo": [-6.85, L / 2, {"residencial": 7.0, "comercial": 4.0, "sobrado": 3.6}[estilo]],
                   "lente_mm": 14 if estilo == "residencial" else 16}
    r["luz"]["preset"] = "tarde_dourada"; r["luz"]["efeito"] = []; r["camadas"] = ["ceu", "meio"]; r["ancoras"] = {}
    r["componentes"] = [
        {"tipo": "rua_trecho", "camada": "meio", "params": {"nome": "cel", "y0": -14, "y1": L + 14, "folhas": 20, "mato": 4}},
        {"tipo": "fachada_quadra", "camada": "meio", "params": {"nome": "v", "x_fachada": -6.85, "lado": -1, "y0": 0.0, "y1": L,
                                                                 "profundidade": 10.0, "lotes": [{"estilo": estilo, "largura": L}]}},
        {"tipo": "chao", "camada": "meio", "params": {"nome": "fundo", "x0": -400, "x1": -16.9, "y0": -300, "y1": L + 300, "material": "grama"}}]
    return r


def t_variacoes():
    out = {}; linhas = []
    for estilo in LARGURAS:
        cel = []
        for i in range(4):
            k, m, hit = CO.construir(receita_celula(estilo, i)); P = Placa(C.pasta(k)); A = Atmosfera(P, "limpo", 11)
            img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["tarde_dourada"] - 0.35, vinheta=0.5)),
                           saida=(540, 960))
            permitidos = set(R.carregar(REC)["textos_permitidos"])
            out[f"{estilo}_{i}"] = {"semente": receita_celula(estilo, i)["semente"], "largura_m": LARGURAS[estilo][i], "render_s": m["tempo_total_s"],
                                    "cache": "HIT" if hit else "MISS", "objetos": m["objetos"],
                                    "flutuando": m["qa_cena"]["nada_flutuando"]["flutuando"], "textos": m["qa_cena"]["textos"],
                                    "textos_fora": [t for t in m["qa_cena"]["textos"] if not texto_ok(t, permitidos)]}
            cel.append(T0._texto(img, [estilo, f"semente {out[f'{estilo}_{i}']['semente']} · {LARGURAS[estilo][i]:.1f} m"], 40, 30))
            print(estilo, i, json.dumps(out[f"{estilo}_{i}"], ensure_ascii=False)[:300], flush=True)
        linhas.append(np.hstack(cel))
    folha = np.vstack(linhas)
    cv2.imwrite(str(OUT / "E3_variacoes.jpg"), folha[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return out


# ------------------------------------------------------------------ E3-2
def t_cenas():
    out = {}; quadros = {}
    for nome, cam, h, clima in CENAS:
        P, m, hit = placa(cam, h, molhado=(clima == "chuva"))
        img = T2.quadro(P, h, clima)
        cv2.imwrite(str(OUT / f"E3_{nome}.jpg"), img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        quadros[nome] = img
        out[nome] = {"cache": "HIT" if hit else "MISS", "render_total_s": m["tempo_total_s"], "por_camada_s": m["tempo_render_s"],
                     "objetos": m["objetos"], "medidas_cor": MD.quadro(img)}
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:400], flush=True)
    # E2 × E3 lado a lado (mesma câmera, mesma luz)
    tw, th = 360, 640; pares = []
    for nome in ("calcada_tarde", "esquina_tarde"):
        e2 = cv2.imread(str(RAIZ / "cenografia" / "testes" / "e2" / f"E2_{nome}.jpg"))[..., ::-1]
        pares += [T2._rotulo(cv2.resize(e2, (tw, th), interpolation=cv2.INTER_AREA), ["E2 (antes)", NOMES[nome].split(" · ")[0]]),
                  T2._rotulo(cv2.resize(quadros[nome], (tw, th), interpolation=cv2.INTER_AREA), ["E3 (agora)", NOMES[nome].split(" · ")[0]])]
    cv2.imwrite(str(OUT / "E3_antes_depois.png"), np.hstack(pares)[..., ::-1])
    folha = np.hstack([T2._rotulo(cv2.resize(quadros[n], (tw, th), interpolation=cv2.INTER_AREA), NOMES[n].split(" · ")) for n, *_ in CENAS])
    cv2.imwrite(str(OUT / "E3_cenas.png"), folha[..., ::-1])
    tot = [v["render_total_s"] for v in out.values() if v["cache"] == "MISS"]
    out["_resumo"] = {"placas_renderizadas_agora": len(tot), "media_s": round(float(np.mean(tot)), 1) if tot else None,
                      "max_s": round(float(np.max(tot)), 1) if tot else None, "dentro_meta_3_5_min": sum(1 for x in tot if x <= 300),
                      "alvos_skill": MD.ALVOS}
    return out


# ------------------------------------------------------------------ E3-3
def _medir_predios(r):
    import bpy
    _, cena, *_ = CO._montar(r)
    bpy.context.view_layer.update()
    corpos, janelas, alturas_andar = [], [], []
    for o in cena.objects:
        if o.type != "MESH":
            continue
        mn, mx = T2_bbox(o)
        if o.name.endswith("_corpo"):
            corpos.append(round(mx.z - mn.z, 2))
        if "_mol" in o.name and o.data.name.startswith("proto_mol_1.20_1.25"):
            janelas.append((round(mx.z - mn.z, 2), round(max(mx.x - mn.x, mx.y - mn.y), 2)))
    malhas = {}
    for o in cena.objects:
        if o.type == "MESH":
            malhas[o.data.name] = malhas.get(o.data.name, 0) + 1
    inst = sum(n for k, n in malhas.items() if k.startswith("proto_"))
    return {"predios": len(corpos), "altura_corpo_m": {"min": min(corpos), "max": max(corpos)},
            "moldura_janela_padrao_m (altura, largura) — vão 1,20 × 1,25 + moldura 7 cm": janelas[0] if janelas else None,
            "objetos_malha": sum(malhas.values()), "malhas_distintas": len(malhas),
            "objetos_instanciados (malha compartilhada)": inst, "prototipos": sum(1 for k in malhas if k.startswith("proto_"))}


def T2_bbox(o):
    from mathutils import Vector
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))


def t_qa():
    out = {}; permitidos = set(R.carregar(REC)["textos_permitidos"])
    for nome, cam, h, clima in CENAS:
        _, m, _ = placa(cam, h, molhado=(clima == "chuva"))
        q = m["qa_cena"]
        out[nome] = {"flutuando": q["nada_flutuando"]["flutuando"], "malhas_verificadas": q["nada_flutuando"]["malhas_verificadas"],
                     "textos": q["textos"], "textos_fora_da_lista": [t for t in q["textos"] if not texto_ok(t, permitidos)]}
    out["escala_e_instancias"] = _medir_predios(receita("calcada"))
    out["_resumo"] = {"objetos_flutuando": sum(len(v["flutuando"]) for k, v in out.items() if k in dict((c[0], 1) for c in CENAS)),
                      "textos_fora_da_lista": sorted({t for k, v in out.items() if k in dict((c[0], 1) for c in CENAS) for t in v["textos_fora_da_lista"]}),
                      "regra_textos": "palavras da lista permitida (nomes de rua inventados, palavras comuns de comércio, ALUGA-SE, MODO CURIOSO) ou números só com algarismos (1 a 4)",
                      "ocr": "não executado: não há OCR instalado no ambiente; a conferência é feita na fonte (texto exato de cada objeto de texto)"}
    return out


# ------------------------------------------------------------------ E3-4
def t_area_vazia():
    out = {}; paineis = []
    for nome, cam in (("calcada_tarde", "calcada"), ("esquina_tarde", "esquina")):
        P, _, _ = placa(cam)
        img = T2.quadro(P, "tarde_dourada", "limpo", heitor=False, grade_extra={"grao": 0.0})
        out[f"E3_{nome}"], mapa = T2.area_vazia(img, T2.mascara_ceu(P))
        P2, _, _ = T2.placa(cam)
        img2 = T2.quadro(P2, "tarde_dourada", "limpo", heitor=False, grade_extra={"grao": 0.0})
        out[f"E2_{nome}"], mapa2 = T2.area_vazia(img2, T2.mascara_ceu(P2))
        for rot, im, mp in (("E2 " + nome, img2, mapa2), ("E3 " + nome, img, mapa)):
            v = im.copy().astype(np.float32)
            for i in range(mp.shape[0]):
                for j in range(mp.shape[1]):
                    if mp[i, j] == 1:
                        s = (slice(i * 60, (i + 1) * 60), slice(j * 60, (j + 1) * 60)); v[s] = v[s] * 0.45 + np.array([255, 0, 200]) * 0.55
            paineis.append(T2._rotulo(cv2.resize(v.astype(np.uint8), (360, 640), interpolation=cv2.INTER_AREA), [rot, "magenta = sem detalhe"]))
    cv2.imwrite(str(OUT / "E3_area_vazia.png"), np.hstack(paineis)[..., ::-1])
    return out


# ------------------------------------------------------------------ E3-5
def t_determinismo():
    r = receita("calcada")
    a, n1 = T2._hash_geometria(r); b, n2 = T2._hash_geometria(r)
    r2 = receita("calcada"); r2["semente"] = r["semente"] + 1; c, n3 = T2._hash_geometria(r2)
    t = time.time(); _, _, hit = placa("calcada"); dt = time.time() - t
    return {"mesma_receita_mesma_geometria": a == b and n1 == n2, "objetos": n1, "outra_semente_geometria_diferente": a != c,
            "objetos_outra_semente": n3, "cache_segunda_chamada": "HIT" if hit else "MISS", "cache_tempo_s": round(dt, 2)}


# ------------------------------------------------------------------ E3-6
def t_integridade():
    P, _, _ = placa("calcada")
    return T0.t_integridade(P, None)


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e3_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())

    def rodar(nome, f):
        if so and nome not in so:
            return
        t = time.time(); res[nome] = f()
        if isinstance(res[nome], dict):
            res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False)[:900], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    rodar("E3_1_variacoes", t_variacoes)
    rodar("E3_2_cenas", t_cenas)
    rodar("E3_3_qa", t_qa)
    rodar("E3_4_area_vazia", t_area_vazia)
    rodar("E3_5_determinismo", t_determinismo)
    rodar("E3_6_integridade", t_integridade)
