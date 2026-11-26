#!/usr/bin/env python3
"""Cenografia — testes da etapa E5 (ambientação). Renderiza, MEDE e documenta.

E5-1 folhas de componentes: árvores (frondosa ×2, ipê amarelo, ipê rosa, palmeira, arbusto) e mobiliário/comércio
     (contêiner, sacos de lixo, ponto de ônibus, banca, cones, bicicleta, vaso, mesa de bar, engradados, frutas, banco).
E5-2 cenas de prova: o quarteirão da E4 ambientado — calçada e esquina na tarde, calçada à noite e uma vista nova da
     calçada da direita ("rua"), 1080×1920. Tempo real por placa.
E5-3 QA da cena: nada flutuando, NADA ATRAVESSANDO (BVH), textos; contagem do que o espalhamento colocou.
E5-4 área vazia: E5 × E4 nas mesmas câmeras.
E5-5 determinismo e cache.  E5-6 integridade (rig v2, ID-001..ID-004, skill) e paleta do Heitor.
Saídas: cenografia/testes/e5/. Placas: .cache/ (fora do Git).
"""
import copy, json, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia import construir as CO                                    # noqa: E402
from cenografia.nucleo import receita as R, cache as C, medidas as MD      # noqa: E402
from cenografia.nucleo.compositor import Placa                            # noqa: E402
from cenografia.nucleo.atmosfera import Atmosfera                         # noqa: E402
import e0_testes as T0                                                     # noqa: E402
import e1_testes as T1                                                     # noqa: E402
import e2_testes as T2                                                     # noqa: E402
import e3_testes as T3                                                     # noqa: E402
import e4_testes as T4                                                     # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e5"; OUT.mkdir(parents=True, exist_ok=True)
REC = RAIZ / "cenografia" / "receitas" / "e5_quarteirao.json"
CAMS = dict(T2.CAMS, rua={"camera": {"pos": [5.3, -4.0, 1.45], "alvo": [4.4, 20.0, 2.2], "lente_mm": 30}, "heitor": None})
CENAS = [("calcada_tarde", "calcada", "tarde_dourada"), ("esquina_tarde", "esquina", "tarde_dourada"),
         ("rua_tarde", "rua", "tarde_dourada"), ("calcada_noite", "calcada", "noite")]
NOMES_C = {"calcada_tarde": "calçada · tarde dourada", "esquina_tarde": "esquina · tarde dourada", "rua_tarde": "calçada da direita · tarde",
           "calcada_noite": "calçada · noite"}
res = {}


def receita(cam, horario="tarde_dourada"):
    r = R.carregar(REC); c = CAMS[cam]; r["camera"] = copy.deepcopy(c["camera"]); r["luz"]["preset"] = horario
    if c["heitor"]:
        x, y, z = c["heitor"]; r["ancoras"] = {"heitor_pe": [x, y, z], "heitor_topo": [x, y, z + 1.4]}
    else:
        r["ancoras"] = {}
    if horario == "noite":
        for comp in r["componentes"]:
            if comp["tipo"] == "veiculo" and comp["params"].get("nome") in T4.EM_TRANSITO:
                comp["params"]["farois"] = True
    return r


def placa(cam, horario="tarde_dourada"):
    k, m, hit = CO.construir(receita(cam, horario))
    return Placa(C.pasta(k)), m, hit


# ------------------------------------------------------------------ E5-1
FOLHAS = {
    "arvores": ({"pos": [19.0, 11.0, 3.2], "alvo": [0.0, 11.0, 4.0], "lente_mm": 20},
                [("arvore", {"especie": "frondosa", "y": -3.0}, "frondosa"), ("arvore", {"especie": "frondosa", "y": 5.0}, "frondosa (outra semente)"),
                 ("arvore", {"especie": "ipe", "flor": "amarelo", "y": 12.5}, "ipê amarelo"), ("arvore", {"especie": "ipe", "flor": "rosa", "y": 18.5}, "ipê rosa"),
                 ("arvore", {"especie": "palmeira", "y": 24.0}, "palmeira"), ("mobiliario", {"tipo": "arbusto", "y": 27.5, "x": 2.0}, "arbusto")]),
    "mobiliario": ({"pos": [7.5, 9.6, 2.2], "alvo": [0.0, 9.6, 1.0], "lente_mm": 20},
                   [("mobiliario", {"tipo": t, "y": y}, n) for t, y, n in
                    [("banco", -1.6, "banco"), ("conteiner", 0.6, "contêiner"), ("sacos", 2.2, "sacos de lixo"), ("ponto_onibus", 4.7, "ponto de ônibus"),
                     ("banca", 9.0, "banca"), ("cones", 12.7, "cones"), ("bicicleta", 14.6, "bicicleta"), ("vaso", 15.9, "vaso"),
                     ("mesa_bar", 17.8, "mesa de bar"), ("engradados", 19.6, "engradados"), ("frutas", 21.4, "bancada de frutas")]]),
}


def t_folhas():
    out = {}
    for nome, (cam, itens) in FOLHAS.items():
        r = R.carregar(REC); r["nome"] = f"e5_folha_{nome}"; r["semente"] = 51
        r["saida"].update(largura=1920, altura=1080); r["saida"]["amostras_por_camada"] = {"ceu": 4, "meio": 24}
        r["camera"] = cam; r["luz"]["efeito"] = []; r["camadas"] = ["ceu", "meio"]
        comps = [{"tipo": "chao", "camada": "meio", "params": {"nome": "piso", "x0": -400, "x1": 400, "y0": -400, "y1": 400, "z": 0.15, "material": "grama"}}]
        ancoras = {}
        for i, (tipo, p, rot) in enumerate(itens):
            q = dict(p); q.setdefault("x", 0.0); q.update(nome=f"i{i}", z=0.15)
            if tipo == "mobiliario":
                q["rot_graus"] = 180
            comps.append({"tipo": tipo, "camada": "meio", "params": q})
            ancoras[f"r{i}"] = [q["x"], q["y"], 0.2]
        r["componentes"] = comps; r["ancoras"] = ancoras
        k, m, hit = CO.construir(r); P = Placa(C.pasta(k)); A = Atmosfera(P, "limpo", 11)
        img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["tarde_dourada"] - 0.2, vinheta=0.4)),
                       saida=(1920, 1080))
        s = skia.Surface(1920, 1080); cv = s.getCanvas()
        cv.drawImage(skia.Image.fromarray(np.dstack([img, np.full(img.shape[:2], 255, np.uint8)]).copy(), colorType=skia.kRGBA_8888_ColorType), 0, 0)
        x0, y0 = (P.W - 1920) // 2, (P.H - 1080) // 2; fonte = skia.Font(T0.NUN, 22)
        fundo = skia.Paint(Color=skia.ColorSetARGB(200, 20, 16, 40), AntiAlias=True); branco = skia.Paint(Color=skia.ColorWHITE, AntiAlias=True)
        for i, (_, _, rot) in enumerate(itens):
            x, y, _ = P.m["ancoras"][f"r{i}"]; x -= x0; y = min(1040, y - y0 + 30 + (i % 2) * 34); w = fonte.measureText(rot) + 20
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - 26, w, 34), 8, 8), fundo); cv.drawString(rot, x - w / 2 + 10, y - 2, fonte, branco)
        im = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3]
        im = T0._texto(im, [f"E5 · folha de {'árvores e vegetação' if nome == 'arvores' else 'mobiliário e comércio'}"], 50, 30)
        cv2.imwrite(str(OUT / f"E5_folha_{nome}.jpg"), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        q = m["qa_cena"]
        out[nome] = {"render_total_s": m["tempo_total_s"], "objetos": m["objetos"], "flutuando": q["nada_flutuando"]["flutuando"],
                     "atravessando": q.get("nada_atravessando", {}).get("atravessando"), "textos": q["textos"]}
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:400], flush=True)
    return out


# ------------------------------------------------------------------ E5-2
def t_cenas():
    out = {}; quadros = {}
    for nome, cam, h in CENAS:
        P, m, hit = placa(cam, h)
        img = T2.quadro(P, h, "limpo")
        cv2.imwrite(str(OUT / f"E5_{nome}.jpg"), img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92]); quadros[nome] = img
        out[nome] = {"cache": "HIT" if hit else "MISS", "render_total_s": m["tempo_total_s"], "por_camada_s": m["tempo_render_s"],
                     "objetos": m["objetos"], "medidas_cor": MD.quadro(img)}
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:400], flush=True)
    tw, th = 360, 640
    folha = np.hstack([T2._rotulo(cv2.resize(quadros[n], (tw, th), interpolation=cv2.INTER_AREA), NOMES_C[n].split(" · ")) for n, *_ in CENAS])
    cv2.imwrite(str(OUT / "E5_cenas.png"), folha[..., ::-1])
    pares = []
    for nome in ("calcada_tarde", "esquina_tarde"):
        e4 = cv2.imread(str(RAIZ / "cenografia" / "testes" / "e4" / f"E4_{nome}.jpg"))[..., ::-1]
        pares += [T2._rotulo(cv2.resize(e4, (tw, th), interpolation=cv2.INTER_AREA), ["E4 (antes)", nome.split("_")[0]]),
                  T2._rotulo(cv2.resize(quadros[nome], (tw, th), interpolation=cv2.INTER_AREA), ["E5 (agora)", nome.split("_")[0]])]
    cv2.imwrite(str(OUT / "E5_antes_depois.png"), np.hstack(pares)[..., ::-1])
    tot = [v["render_total_s"] for v in out.values() if v["cache"] == "MISS"]
    out["_resumo"] = {"placas_renderizadas_agora": len(tot), "media_s": round(float(np.mean(tot)), 1) if tot else None,
                      "max_s": round(float(np.max(tot)), 1) if tot else None, "dentro_meta_3_5_min": sum(1 for x in tot if x <= 300)}
    return out


# ------------------------------------------------------------------ E5-3
def t_qa():
    out = {}; permitidos = set(R.carregar(REC)["textos_permitidos"])
    for nome, cam, h in CENAS:
        _, m, _ = placa(cam, h); q = m["qa_cena"]
        out[nome] = {"flutuando": q["nada_flutuando"]["flutuando"], "malhas_verificadas": q["nada_flutuando"]["malhas_verificadas"],
                     "pecas_verificadas_colisao": q["nada_atravessando"]["pecas_verificadas"], "atravessando": q["nada_atravessando"]["atravessando"],
                     "textos_fora_da_lista": [t for t in q["textos"] if not T3.texto_ok(t, permitidos)]}
    import bpy
    _, cena, *_ = CO._montar(receita("calcada"))
    cont = {}
    for o in cena.objects:
        if not (o.get("ambientacao") and o.parent is None):
            continue
        nm = o.name; partes = nm.split("_")
        if nm.startswith("arb_"):
            tipo = "árvore em canteiro novo" if partes[2].startswith("n") else ("arbusto em canteiro da rua" if partes[-1] == "arbusto" else "árvore em canteiro da rua")
        elif nm.startswith("bar_"):
            tipo = "engradados" if partes[1].startswith("eng") else "mesa de bar"
        elif nm.startswith("ponto_"):
            tipo = "ponto_onibus"
        else:
            tipo = partes[-1]
        cont[tipo] = cont.get(tipo, 0) + 1
    malhas = {}
    for o in cena.objects:
        if o.type == "MESH":
            malhas[o.data.name] = malhas.get(o.data.name, 0) + 1
    out["_resumo"] = {"objetos_flutuando": sum(len(v["flutuando"]) for v in out.values()),
                      "pecas_atravessando": sum(len(v["atravessando"]) for v in out.values()),
                      "textos_fora_da_lista": sorted({t for v in out.values() for t in v["textos_fora_da_lista"]}),
                      "colocado_pelo_espalhamento": cont,
                      "aglomerados_de_folhas_instanciados": sum(n for k, n in malhas.items() if k.startswith("proto_aglom")),
                      "prototipos_de_aglomerado": sum(1 for k in malhas if k.startswith("proto_aglom"))}
    return out


# ------------------------------------------------------------------ E5-4
def t_area_vazia():
    out = {}; paineis = []
    for nome, cam in (("calcada_tarde", "calcada"), ("esquina_tarde", "esquina")):
        for etapa, f in (("E4", T4.placa), ("E5", placa)):
            P, _, _ = f(cam)
            img = T2.quadro(P, "tarde_dourada", "limpo", heitor=False, grade_extra={"grao": 0.0})
            out[f"{etapa}_{nome}"], mp = T2.area_vazia(img, T2.mascara_ceu(P))
            v = img.copy().astype(np.float32)
            for i in range(mp.shape[0]):
                for j in range(mp.shape[1]):
                    if mp[i, j] == 1:
                        s = (slice(i * 60, (i + 1) * 60), slice(j * 60, (j + 1) * 60)); v[s] = v[s] * 0.45 + np.array([255, 0, 200]) * 0.55
            paineis.append(T2._rotulo(cv2.resize(v.astype(np.uint8), (360, 640), interpolation=cv2.INTER_AREA), [f"{etapa} {nome}", "magenta = sem detalhe"]))
    cv2.imwrite(str(OUT / "E5_area_vazia.png"), np.hstack(paineis)[..., ::-1])
    return out


# ------------------------------------------------------------------ E5-5 / E5-6
def t_determinismo():
    r = receita("calcada")
    a, n1 = T2._hash_geometria(r); b, n2 = T2._hash_geometria(r)
    r2 = receita("calcada"); r2["semente"] += 1; c, n3 = T2._hash_geometria(r2)
    t = time.time(); _, _, hit = placa("calcada"); dt = time.time() - t
    return {"mesma_receita_mesma_geometria": a == b and n1 == n2, "objetos": n1, "outra_semente_geometria_diferente": a != c,
            "cache_segunda_chamada": "HIT" if hit else "MISS", "cache_tempo_s": round(dt, 2)}


def t_integridade():
    P, _, _ = placa("calcada")
    return T0.t_integridade(P, None)


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e5_metricas.json"
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
    rodar("E5_1_folhas", t_folhas)
    rodar("E5_2_cenas", t_cenas)
    rodar("E5_3_qa", t_qa)
    rodar("E5_4_area_vazia", t_area_vazia)
    rodar("E5_5_determinismo", t_determinismo)
    rodar("E5_6_integridade", t_integridade)
