#!/usr/bin/env python3
"""Cenografia — testes da etapa E2 (ruas e calçadas: quarteirão modular). Renderiza, MEDE e documenta.

E2-1 cenas de prova em resolução final (1080×1920): 3 câmeras (calçada, esquina, de cima) na tarde dourada,
     calçada à noite e esquina com chuva (piso molhado). Tempo real por placa e por camada.
E2-2 folha de componentes: o kit de rua enfileirado numa calçada, com rótulos.
E2-3 QA da cena (no Blender, antes do render): nada flutuando, textos 3D × lista permitida, medidas de escala.
E2-4 área vazia: blocos do quadro sem detalhe (fora do céu), E2 × cena da E1.
E2-5 determinismo da montagem (mesma receita → mesma geometria) e cache.
E2-6 integridade (rig v2, ID-001..ID-004, skill) e paleta do Heitor no quadro.
Saídas: cenografia/testes/e2/. Placas: .cache/ (fora do Git).
"""
import copy, hashlib, json, subprocess, sys, time
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

OUT = RAIZ / "cenografia" / "testes" / "e2"; OUT.mkdir(parents=True, exist_ok=True)
REC = RAIZ / "cenografia" / "receitas" / "e2_quarteirao.json"
W, H = 1080, 1920
# câmera + âncora do Heitor (mundo, m) por vista. "de_cima" é vista de conferência do piso: sem personagem.
CAMS = {
    "calcada": {"camera": {"pos": [-5.0, 0.0, 1.15], "alvo": [-4.6, 20.0, 1.55], "lente_mm": 35}, "heitor": [-5.0, 4.2, 0.15]},
    "esquina": {"camera": {"pos": [1.8, 17.5, 1.25], "alvo": [-3.0, 28.0, 1.9], "lente_mm": 35}, "heitor": [-4.0, 21.5, 0.15]},
    "de_cima": {"camera": {"pos": [-1.5, 6.0, 4.2], "alvo": [-4.5, 13.0, 0.0], "lente_mm": 30}, "heitor": None},
}
# (nome, câmera, horário, clima) — o clima "chuva" usa a placa com piso molhado
CENAS = [("calcada_tarde", "calcada", "tarde_dourada", "limpo"), ("esquina_tarde", "esquina", "tarde_dourada", "limpo"),
         ("de_cima_tarde", "de_cima", "tarde_dourada", "limpo"), ("calcada_noite", "calcada", "noite", "limpo"),
         ("esquina_chuva", "esquina", "tarde_dourada", "chuva")]
NOMES = {"calcada_tarde": "calçada · tarde dourada", "esquina_tarde": "esquina · tarde dourada", "de_cima_tarde": "de cima · tarde dourada",
         "calcada_noite": "calçada · noite", "esquina_chuva": "esquina · chuva (piso molhado)"}
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


def quadro(P, horario, clima, heitor=True, grade_extra=None, t=0.0):
    A = Atmosfera(P, clima, 11)
    g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[horario], **(grade_extra or {})))
    tem = heitor and "heitor_pe" in P.m["ancoras"]
    return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, ceu_extra=A.ceu(t), frente_extra=A.frente(t),
                    personagem=T0.heitor(P, t) if tem else None, profundidade_personagem=T0.DP(P) if tem else None)


def mascara_ceu(P):
    """True onde só há céu (nenhuma camada de cenário cobre o pixel), no recorte de saída."""
    cob = np.zeros((P.H, P.W), bool)
    for c, d in P.camadas.items():
        if c != "ceu":
            cob |= d["alfa"] > 0.5
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2
    return ~cob[y0:y0 + H, x0:x0 + W]


def area_vazia(img, ceu, bloco=60, limiar=0.012):
    """Fração dos blocos de 60×60 px (fora do céu) sem detalhe: desvio-padrão da luminância < 1,2 %.
    Medido sobre o quadro SEM grão e SEM personagem (o grão inventaria detalhe)."""
    L = (0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]).astype(np.float32) / 255.0
    vazios = total = 0; mapa = np.zeros((H // bloco, W // bloco), np.int8)
    for i in range(H // bloco):
        for j in range(W // bloco):
            s = (slice(i * bloco, (i + 1) * bloco), slice(j * bloco, (j + 1) * bloco))
            if ceu[s].mean() > 0.5:
                mapa[i, j] = -1; continue
            total += 1
            if L[s].std() < limiar:
                vazios += 1; mapa[i, j] = 1
    return {"blocos_fora_do_ceu": total, "blocos_vazios": vazios, "area_vazia_pct": round(100 * vazios / max(total, 1), 1)}, mapa


def _rotulo(img, linhas):
    return T0._texto(img, linhas, 40, 30)


# ------------------------------------------------------------------ E2-1
def t_cenas():
    out = {}; quadros = {}
    for nome, cam, h, clima in CENAS:
        t = time.time(); P, m, hit = placa(cam, h, molhado=(clima == "chuva"))
        img = quadro(P, h, clima)
        cv2.imwrite(str(OUT / f"E2_{nome}.jpg"), img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        quadros[nome] = img
        out[nome] = {"cache": "HIT" if hit else "MISS", "render_total_s": m["tempo_total_s"], "por_camada_s": m["tempo_render_s"],
                     "objetos": m["objetos"], "medidas_cor": MD.quadro(img)}
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:400], flush=True)
    # folha com as 5 cenas lado a lado
    tw, th = 360, 640
    folha = np.hstack([_rotulo(cv2.resize(quadros[n], (tw, th), interpolation=cv2.INTER_AREA), NOMES[n].split(" · ")) for n, *_ in CENAS])
    cv2.imwrite(str(OUT / "E2_cenas.png"), folha[..., ::-1])
    tot = [v["render_total_s"] for v in out.values() if v["cache"] == "MISS"]
    out["_resumo"] = {"placas_renderizadas_agora": len(tot), "media_s": round(float(np.mean(tot)), 1) if tot else None,
                      "max_s": round(float(np.max(tot)), 1) if tot else None, "dentro_meta_3_5_min": sum(1 for x in tot if x <= 300),
                      "alvos_skill": MD.ALVOS}
    return out


# ------------------------------------------------------------------ E2-2
FOLHA_ITENS = [   # (rótulo, tipo, params, ponto do rótulo no mundo)
    ("poste de concreto + transformador", "poste_concreto", {"x": -3.95, "y": 0.6, "lado": 1, "linha": "a", "id": 214, "transformador": True}, [-3.95, 0.6, 8.6]),
    ("semáforo (veicular + pedestre)", "semaforo", {"x": -4.15, "y": 3.2, "rot_graus": 90, "estado": "vermelho"}, [-4.15, 3.2, 4.6]),
    ("placa de rua (nomes inventados)", "placa_rua", {"x": -4.3, "y": 6.2, "nomes": ["R. DAS JABUTICABAS", "R. VAGALUME"]}, [-4.3, 6.2, 3.4]),
    ("regulamentação: velocidade", "placa_regulamentacao", {"x": -4.15, "y": 8.6, "tipo": "velocidade", "limite": 30, "rot_graus": 90}, [-4.15, 8.6, 3.2]),
    ("regulamentação: proibido estacionar", "placa_regulamentacao", {"x": -4.15, "y": 10.6, "tipo": "proibido_estacionar", "rot_graus": 90}, [-4.15, 10.6, 3.2]),
    ("hidrante", "hidrante", {"x": -4.3, "y": 12.3}, [-4.3, 12.3, 1.2]),
    ("lixeira de poste", "lixeira_poste", {"x": -6.3, "y": 13.8}, [-6.3, 13.8, 1.7]),
    ("poste de concreto + fiação", "poste_concreto", {"x": -3.95, "y": 15.4, "lado": 1, "linha": "a", "id": 215}, [-3.95, 15.4, 8.6]),
]


def t_folha_componentes():
    r = R.carregar(REC)
    r["nome"] = "e2_folha_componentes"; r["descricao"] = "Folha de componentes da E2 (kit de rua enfileirado)."
    r["saida"]["largura"], r["saida"]["altura"] = 1920, 1080
    r["camera"] = {"pos": [4.5, 8.0, 4.3], "alvo": [-4.4, 8.0, 4.3], "lente_mm": 18}   # nivelada: verticais paralelas
    r["luz"]["efeito"] = []
    comps = [{"tipo": "rua_trecho", "camada": "meio", "params": {"nome": "folha", "y0": -8, "y1": 24, "marcacao": "tracejada_branca",
                                                                   "remendos": 3, "tampas": 2, "lados": [-1]}}]
    comps.append({"tipo": "predio_bloco", "camada": "meio", "params": {"nome": "fundo", "x0": -14, "x1": -6.85, "y0": -8, "y1": 24, "altura": 6.0,
                                                                     "lado": -1, "terreo": False, "mat": {"nome": "reboco", "cor": "#d9cbb4", "desgaste": 0.3}}})
    for i, (rot, tipo, p, pto) in enumerate(FOLHA_ITENS):
        comps.append({"tipo": tipo, "camada": "meio", "params": p})
    comps.append({"tipo": "fiacao", "camada": "meio", "params": {"sobras": 0.6}})
    r["componentes"] = comps; r["camadas"] = ["ceu", "meio"]
    r["ancoras"] = {f"r{i}": pto for i, (_, _, _, pto) in enumerate(FOLHA_ITENS)}
    t = time.time(); k, m, hit = CO.construir(r); P = Placa(C.pasta(k))
    A = Atmosfera(P, "limpo", 11)
    img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["tarde_dourada"], vinheta=0.4)),
                   saida=(1920, 1080))   # céu do próprio render: num quadro largo, as nuvens 2D ficam com cara de camuflagem (limitação anotada)
    # rótulos (2D, fonte oficial Nunito), ancorados na projeção real de cada peça
    s = skia.Surface(1920, 1080); cv = s.getCanvas()
    cv.drawImage(skia.Image.fromarray(np.dstack([img, np.full(img.shape[:2], 255, np.uint8)]).copy(), colorType=skia.kRGBA_8888_ColorType), 0, 0)
    x0, y0 = (P.W - 1920) // 2, (P.H - 1080) // 2
    fonte = skia.Font(T0.NUN, 22); fundo = skia.Paint(Color=skia.ColorSetARGB(200, 20, 16, 40), AntiAlias=True)
    branco = skia.Paint(Color=skia.ColorWHITE, AntiAlias=True)
    feitos = []
    for i, (rot, *_r) in sorted(enumerate(FOLHA_ITENS), key=lambda e: P.m["ancoras"][f"r{e[0]}"][0]):
        x, y, _ = P.m["ancoras"][f"r{i}"]; x -= x0; y -= y0
        w = fonte.measureText(rot) + 20; x = max(w / 2 + 10, min(1910 - w / 2, x)); y = max(40, min(900, y))
        while any(abs(x - fx) < (w + fw) / 2 + 6 and abs(y - fy) < 40 for fx, fy, fw in feitos):   # sem rótulos sobrepostos
            y -= 40
        feitos.append((x, y, w))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - 26, w, 34), 8, 8), fundo)
        cv.drawString(rot, x - w / 2 + 10, y - 2, fonte, branco)
    out = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3]
    out = T0._texto(out, ["E2 · folha de componentes (kit de rua)", "fiação, calçada por lote, boca de lobo, piso tátil, sarjeta, remendos e tampas vêm do trecho de rua"], 1000, 26)
    cv2.imwrite(str(OUT / "E2_folha_componentes.jpg"), out[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    return {"cache": "HIT" if hit else "MISS", "render_total_s": m["tempo_total_s"], "objetos": m["objetos"], "qa_cena": m["qa_cena"]}


# ------------------------------------------------------------------ E2-3
def t_qa():
    out = {}
    permitidos = set(R.carregar(REC)["textos_permitidos"])
    for nome, cam, h, clima in CENAS:
        P, m, _ = placa(cam, h, molhado=(clima == "chuva"))
        q = m["qa_cena"]; fora = sorted(set(q["textos"]) - permitidos)
        out[nome] = {"flutuando": q["nada_flutuando"]["flutuando"], "malhas_verificadas": q["nada_flutuando"]["malhas_verificadas"],
                     "textos": q["textos"], "textos_fora_da_lista": fora, "medidas": q["medidas"]}
    out["_resumo"] = {"objetos_flutuando": sum(len(v["flutuando"]) for v in out.values()),
                      "textos_fora_da_lista": sorted({t for v in out.values() for t in v["textos_fora_da_lista"]}),
                      "ocr": "não executado: não há OCR instalado no ambiente; a conferência é feita na fonte (texto exato de cada objeto de texto da cena)"}
    return out


# ------------------------------------------------------------------ E2-4
def t_area_vazia():
    out = {}; mapas = []
    for nome, cam, h, clima in CENAS:
        if clima != "limpo" or h != "tarde_dourada":
            continue
        P, _, _ = placa(cam, h)
        img = quadro(P, h, clima, heitor=False, grade_extra={"grao": 0.0})
        out[nome], mapa = area_vazia(img, mascara_ceu(P)); mapas.append((nome, img, mapa))
    # referência: a cena da E1 (mesma calçada da E0, volumes provisórios, rua reta), tarde dourada, limpo
    P1, _, _ = T1.placa("tarde_dourada")
    A = Atmosfera(P1, "limpo", 11)
    img1 = P1.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["tarde_dourada"], grao=0.0)), ceu_extra=A.ceu(0.0))
    out["referencia_E1_calcada_tarde"], mapa1 = area_vazia(img1, mascara_ceu(P1)); mapas.append(("E1 (referência)", img1, mapa1))
    # imagem: blocos vazios em magenta translúcido
    tw, th = 360, 640; paineis = []
    for nome, img, mapa in mapas:
        v = img.copy().astype(np.float32)
        for i in range(mapa.shape[0]):
            for j in range(mapa.shape[1]):
                if mapa[i, j] == 1:
                    s = (slice(i * 60, (i + 1) * 60), slice(j * 60, (j + 1) * 60)); v[s] = v[s] * 0.45 + np.array([255, 0, 200]) * 0.55
        paineis.append(_rotulo(cv2.resize(v.astype(np.uint8), (tw, th), interpolation=cv2.INTER_AREA), [nome, "magenta = bloco sem detalhe"]))
    cv2.imwrite(str(OUT / "E2_area_vazia.png"), np.hstack(paineis)[..., ::-1])
    return out


# ------------------------------------------------------------------ E2-5
def _hash_geometria(r):
    import bpy
    bpy_, cena, *_ = CO._montar(r)
    dg = bpy.context.evaluated_depsgraph_get(); h = hashlib.sha256()
    for o in sorted(cena.objects, key=lambda o: o.name):
        h.update(o.name.encode()); h.update(np.asarray(o.matrix_world, np.float32).round(5).tobytes())
        if o.type == "MESH":
            me = o.evaluated_get(dg).to_mesh(); a = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", a)
            h.update(a.round(5).tobytes()); o.evaluated_get(dg).to_mesh_clear()
    return h.hexdigest(), len(cena.objects)


def t_determinismo():
    r = receita("calcada")
    a, n1 = _hash_geometria(r); b, n2 = _hash_geometria(r)
    r2 = receita("calcada"); r2["semente"] = 22; c, _ = _hash_geometria(r2)
    t = time.time(); _, _, hit = placa("calcada"); dt = time.time() - t
    return {"mesma_receita_mesma_geometria": a == b and n1 == n2, "objetos": n1, "outra_semente_geometria_diferente": a != c,
            "cache_segunda_chamada": "HIT" if hit else "MISS", "cache_tempo_s": round(dt, 2)}


# ------------------------------------------------------------------ E2-6
def t_integridade():
    P, _, _ = placa("calcada")
    return T0.t_integridade(P, None)


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e2_metricas.json"
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
    rodar("E2_1_cenas", t_cenas)
    rodar("E2_2_folha_componentes", t_folha_componentes)
    rodar("E2_3_qa", t_qa)
    rodar("E2_4_area_vazia", t_area_vazia)
    rodar("E2_5_determinismo", t_determinismo)
    rodar("E2_6_integridade", t_integridade)
