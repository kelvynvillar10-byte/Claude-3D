#!/usr/bin/env python3
"""Cenografia — testes da etapa E4 (veículos). Renderiza, MEDE e documenta.

E4-1 giro de 360° de cada veículo (hatch, sedã, SUV, picape, furgão, ônibus, moto): 48 ângulos por veículo, vídeo em
     grade (E4_giro_360.mp4) e folha com 8 ângulos (E4_giro_angulos.jpg). Tempo real por quadro.
E4-2 escala: medidas reais de cada veículo no Blender (comprimento, largura, altura, roda) × faixa típica de referência;
     pneus tocando o chão.
E4-3 cenas de prova: o quarteirão da E3 com carros estacionados e trânsito parado — calçada e esquina na tarde e à noite
     (faróis acesos nos veículos em trânsito). Tempo real por placa.
E4-4 QA da cena (nada flutuando, textos) e determinismo/cache.
E4-5 integridade (rig v2, ID-001..ID-004, skill) e paleta do Heitor no quadro.
Saídas: cenografia/testes/e4/. Placas: .cache/ (fora do Git).
"""
import copy, json, math, re, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia import construir as CO                                    # noqa: E402
from cenografia.nucleo import receita as R, cache as C, medidas as MD      # noqa: E402
from cenografia.nucleo.compositor import Placa                            # noqa: E402
import e0_testes as T0                                                     # noqa: E402
import e2_testes as T2                                                     # noqa: E402
import e3_testes as T3                                                     # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e4"; OUT.mkdir(parents=True, exist_ok=True)
TMP = RAIZ / "_tmp" / "e4_giro"
REC = RAIZ / "cenografia" / "receitas" / "e4_quarteirao.json"
TIPOS = ["hatch", "seda", "suv", "picape", "furgao", "onibus", "moto"]
NOMES = {"hatch": "hatch compacto", "seda": "sedã", "suv": "SUV", "picape": "picape cabine dupla", "furgao": "furgão de entrega",
         "onibus": "ônibus urbano", "moto": "moto 150 cc"}
# faixas TÍPICAS de mercado (referência aproximada, conhecimento geral — não foram medidas neste projeto)
REFERENCIA = {"hatch": ((3.8, 4.1), (1.65, 1.76), (1.42, 1.56)), "seda": ((4.4, 4.75), (1.70, 1.82), (1.40, 1.50)),
              "suv": ((4.2, 4.6), (1.76, 1.87), (1.58, 1.72)), "picape": ((5.1, 5.4), (1.80, 1.92), (1.74, 1.86)),
              "furgao": ((4.8, 5.5), (1.90, 2.06), (2.25, 2.60)), "onibus": ((11.5, 13.2), (2.45, 2.60), (2.95, 3.35)),
              "moto": ((1.9, 2.1), (0.70, 0.82), (1.00, 1.15))}
N_GIRO = 48; CW, CH = 480, 360
CENAS = [("calcada_tarde", "calcada", "tarde_dourada"), ("esquina_tarde", "esquina", "tarde_dourada"),
         ("calcada_noite", "calcada", "noite"), ("esquina_noite", "esquina", "noite")]
NOMES_C = {"calcada_tarde": "calçada · tarde dourada", "esquina_tarde": "esquina · tarde dourada",
           "calcada_noite": "calçada · noite (faróis)", "esquina_noite": "esquina · noite (faróis)"}
EM_TRANSITO = ("bus", "carro_espera", "moto_espera")
res = {}


# ------------------------------------------------------------------ E4-1 / E4-2: estúdio de giro
def _receita_giro(tipo):
    from cenografia.componentes.veiculos import TIPOS as TV
    L = 2.0 if tipo == "moto" else TV[tipo]["L"]; Hh = {"onibus": 3.1, "furgao": 2.4, "moto": 1.1}.get(tipo, 1.6)
    d = max(5.2, L * 1.2 + 2.0)
    r = R.carregar(REC); r["nome"] = f"e4_giro_{tipo}"; r["semente"] = 600 + TIPOS.index(tipo)
    r["saida"].update(largura=CW, altura=CH, overscan=0.0)
    r["camera"] = {"pos": [d * 0.82, -d * 0.57, Hh * 0.55 + 0.9], "alvo": [0.0, 0.0, Hh * 0.42], "lente_mm": 35}
    r["luz"]["preset"] = "meio_dia"; r["luz"]["efeito"] = []; r["camadas"] = ["ceu", "meio"]; r["ancoras"] = {}
    r["componentes"] = [{"tipo": "chao", "camada": "meio", "params": {"nome": "piso", "x0": -30, "x1": 30, "y0": -30, "y1": 30, "z": 0.0,
                                                                     "material": "concreto"}},
                        {"tipo": "veiculo", "camada": "meio", "params": {"nome": "v", "tipo": tipo, "x": 0.0, "y": 0.0, "rot_graus": 0.0,
                                                                         "cor": {"hatch": "#9e1f1f", "seda": "#a9adb3", "suv": "#1d1f22", "picape": "#e9e9e6",
                                                                                 "furgao": "#e9e9e6", "moto": "#1f4e8c"}.get(tipo), "metal": 0.4}}]
    return r


def _medir(cena, tipo):
    from mathutils import Vector
    def bb(objs):
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        return (min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)), (max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    raiz = cena.objects["v"]; filhos = [o for o in raiz.children_recursive if o.type in ("MESH", "FONT")]
    sem_retro = [o for o in filhos if "retro" not in o.name and "haste" not in o.name and "guidao" not in o.name]
    (x0, y0, z0), (x1, y1, z1) = bb(sem_retro); (_, Y0, _), (_, Y1, _) = bb(filhos)
    rodas = [o for o in filhos if "roda" in o.name and "caixa" not in o.name]
    (_, _, rz0), (_, _, rz1) = bb(rodas[:1])
    ref = REFERENCIA[tipo]; L, W, H = x1 - x0, (Y1 - Y0 if tipo == "moto" else y1 - y0), z1 - z0   # moto: largura no guidão
    dentro = lambda v, f: f[0] <= v <= f[1]
    return {"comprimento_m": round(L, 2), "largura_sem_retrovisor_m": round(W, 2), "largura_com_retrovisor_m": round(Y1 - Y0, 2),
            "altura_m": round(H, 2), "diametro_roda_m": round(rz1 - rz0, 2), "pneu_mais_baixo_z_m": round(min(bb([o])[0][2] for o in rodas), 3),
            "referencia_tipica (C, L, A)": ref,
            "dentro_da_referencia": {"comprimento": dentro(L, ref[0]), "largura": dentro(W, ref[1]), "altura": dentro(H, ref[2])}}


def t_giro():
    import bpy
    TMP.mkdir(parents=True, exist_ok=True); out = {}
    for tipo in TIPOS:
        r = _receita_giro(tipo)
        _, cena, *_ = CO._montar(r)
        cena.cycles.samples = 24; cena.cycles.use_denoising = True; cena.render.use_compositing = False
        cena.render.film_transparent = False; cena.render.image_settings.file_format = "PNG"
        cena.view_settings.view_transform = "AgX"
        for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
            try:
                cena.view_settings.look = look; break
            except TypeError:
                pass
        for o in cena.objects:
            if o.type in ("MESH", "CURVE", "FONT", "EMPTY"):
                o.visible_camera = True
        cena.view_settings.exposure = -1.2
        bpy.context.view_layer.update()            # sem isto, matrix_world dos filhos ainda não reflete a posição (medida errada)
        out[tipo] = _medir(cena, tipo); raiz = cena.objects["v"]; tempos = []
        for k in range(N_GIRO):
            raiz.rotation_euler = (raiz.rotation_euler.x, 0.0, 2 * math.pi * k / N_GIRO)
            cena.render.filepath = str(TMP / f"{tipo}_{k:03d}.png"); t = time.time()
            bpy.ops.render.render(write_still=True); tempos.append(time.time() - t)
        out[tipo].update(quadros=N_GIRO, render_por_quadro_s=round(float(np.mean(tempos)), 2), objetos=len(raiz.children_recursive))
        print(tipo, json.dumps(out[tipo], ensure_ascii=False), flush=True)
    # folha: 8 ângulos por veículo
    linhas = []
    for tipo in TIPOS:
        cel = []
        for k in range(0, N_GIRO, N_GIRO // 8):
            im = cv2.imread(str(TMP / f"{tipo}_{k:03d}.png"))[..., ::-1]
            cel.append(cv2.resize(im, (240, 180), interpolation=cv2.INTER_AREA))
        lin = np.hstack(cel); m = out[tipo]
        linhas.append(T0._texto(lin, [f"{NOMES[tipo]} · {m['comprimento_m']:.2f} × {m['largura_sem_retrovisor_m']:.2f} × {m['altura_m']:.2f} m"], 30, 20))
    cv2.imwrite(str(OUT / "E4_giro_angulos.jpg"), np.vstack(linhas)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    # vídeo: grade 4 × 2, duas voltas a 16 q/s
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x720", "-r", "16", "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E4_giro_360.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    info = np.full((CH, CW, 3), 24, np.uint8)
    info = T0._texto(info, ["E4 · veículos", "giro de 360°", "48 ângulos", "sem marca, placa em branco"], 70, 34)
    for q in range(2 * N_GIRO):
        k = q % N_GIRO; cel = []
        for tipo in TIPOS:
            im = cv2.imread(str(TMP / f"{tipo}_{k:03d}.png"))[..., ::-1]
            cel.append(T0._texto(np.ascontiguousarray(im), [NOMES[tipo]], 34, 24))
        cel.append(info)
        quadro = np.vstack([np.hstack(cel[:4]), np.hstack(cel[4:])])
        pr.stdin.write(np.ascontiguousarray(quadro).tobytes())
    pr.stdin.close(); pr.wait()
    out["_resumo"] = {"dentro_da_referencia": {t: all(out[t]["dentro_da_referencia"].values()) for t in TIPOS},
                      "pneus_no_chao": {t: abs(out[t]["pneu_mais_baixo_z_m"]) <= 0.01 for t in TIPOS}}
    return out


# ------------------------------------------------------------------ E4-3: cenas do quarteirão
def receita(cam, horario="tarde_dourada"):
    r = R.carregar(REC); c = T2.CAMS[cam]; r["camera"] = copy.deepcopy(c["camera"]); r["luz"]["preset"] = horario
    x, y, z = c["heitor"]; r["ancoras"] = {"heitor_pe": [x, y, z], "heitor_topo": [x, y, z + 1.4]}
    if horario == "noite":
        for comp in r["componentes"]:
            if comp["tipo"] == "veiculo" and comp["params"].get("nome") in EM_TRANSITO:
                comp["params"]["farois"] = True
    return r


def placa(cam, horario="tarde_dourada"):
    k, m, hit = CO.construir(receita(cam, horario))
    return Placa(C.pasta(k)), m, hit


def t_cenas():
    out = {}; quadros = {}
    for nome, cam, h in CENAS:
        P, m, hit = placa(cam, h)
        img = T2.quadro(P, h, "limpo")
        cv2.imwrite(str(OUT / f"E4_{nome}.jpg"), img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        quadros[nome] = img
        out[nome] = {"cache": "HIT" if hit else "MISS", "render_total_s": m["tempo_total_s"], "por_camada_s": m["tempo_render_s"],
                     "objetos": m["objetos"], "medidas_cor": MD.quadro(img)}
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:400], flush=True)
    tw, th = 360, 640
    folha = np.hstack([T2._rotulo(cv2.resize(quadros[n], (tw, th), interpolation=cv2.INTER_AREA), NOMES_C[n].split(" · ")) for n, *_ in CENAS])
    cv2.imwrite(str(OUT / "E4_cenas.png"), folha[..., ::-1])
    pares = []
    for nome in ("calcada_tarde", "esquina_tarde"):
        e3 = cv2.imread(str(RAIZ / "cenografia" / "testes" / "e3" / f"E3_{nome}.jpg"))[..., ::-1]
        pares += [T2._rotulo(cv2.resize(e3, (tw, th), interpolation=cv2.INTER_AREA), ["E3 (antes)", nome.split("_")[0]]),
                  T2._rotulo(cv2.resize(quadros[nome], (tw, th), interpolation=cv2.INTER_AREA), ["E4 (agora)", nome.split("_")[0]])]
    cv2.imwrite(str(OUT / "E4_antes_depois.png"), np.hstack(pares)[..., ::-1])
    tot = [v["render_total_s"] for v in out.values() if v["cache"] == "MISS"]
    out["_resumo"] = {"placas_renderizadas_agora": len(tot), "media_s": round(float(np.mean(tot)), 1) if tot else None,
                      "max_s": round(float(np.max(tot)), 1) if tot else None, "dentro_meta_3_5_min": sum(1 for x in tot if x <= 300)}
    return out


# ------------------------------------------------------------------ E4-4
def t_qa():
    out = {}; permitidos = set(R.carregar(REC)["textos_permitidos"])
    for nome, cam, h in CENAS:
        _, m, _ = placa(cam, h); q = m["qa_cena"]
        out[nome] = {"flutuando": q["nada_flutuando"]["flutuando"], "malhas_verificadas": q["nada_flutuando"]["malhas_verificadas"],
                     "textos_fora_da_lista": [t for t in q["textos"] if not T3.texto_ok(t, permitidos)], "textos": q["textos"]}
    r = receita("calcada")
    a, n1 = T2._hash_geometria(r); b, n2 = T2._hash_geometria(r)
    r2 = receita("calcada"); r2["semente"] += 1; c, n3 = T2._hash_geometria(r2)
    import bpy
    _, cena, *_ = CO._montar(r)
    veic = [o for o in cena.objects if o.get("veiculo")]
    tipos = {}
    for o in veic:
        tipos[o["veiculo"]] = tipos.get(o["veiculo"], 0) + 1
    out["_resumo"] = {"objetos_flutuando": sum(len(v["flutuando"]) for v in out.values()),
                      "textos_fora_da_lista": sorted({t for v in out.values() for t in v["textos_fora_da_lista"]}),
                      "veiculos_na_cena": len(veic), "por_tipo": tipos,
                      "mesma_receita_mesma_geometria": a == b and n1 == n2, "outra_semente_geometria_diferente": a != c,
                      "regra_textos": "palavras da lista permitida (inclui CENTRO, do letreiro do ônibus) ou números só com algarismos; placas de veículo SEM caracteres"}
    return out


# ------------------------------------------------------------------ E4-5
def t_integridade():
    P, _, _ = placa("calcada")
    return T0.t_integridade(P, None)


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e4_metricas.json"
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
    rodar("E4_1_giro_e_escala", t_giro)
    rodar("E4_3_cenas", t_cenas)
    rodar("E4_4_qa_determinismo", t_qa)
    rodar("E4_5_integridade", t_integridade)
