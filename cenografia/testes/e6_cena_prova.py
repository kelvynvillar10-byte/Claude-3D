#!/usr/bin/env python3
"""Cenografia — E6: CENA DE PROVA (vídeo de TESTE, não é história).

A "rua de bairro" montada por receita (receitas/e6_rua.json) e um roteiro de câmera em receita
(receitas/e6_cena_prova.json): 3 tomadas, em 3 horários, com o Heitor rig v2 OFICIAL andando (ciclo de caminhada do
próprio rig, sem alteração) e câmera em paralaxe 2.5D sobre as placas renderizadas.

Medidas: tempo de render das placas e de composição por quadro; caminho livre (no Blender: nada no corredor do
Heitor entre 20 cm e 1,5 m); deslize do pé de apoio na tomada de perfil; continuidade entre quadros; paleta do
Heitor idêntica ao rig sozinho nos pixels não cobertos; quadro idêntico na repetição; integridade (rig, identidade, skill).
Saídas: cenografia/testes/e6/ (vídeo, folha de quadros, métricas, relatório à parte).
"""
import copy, hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia import construir as CO                                    # noqa: E402
from cenografia.nucleo import receita as R, cache as C, medidas as MD      # noqa: E402
from cenografia.nucleo.compositor import Placa                            # noqa: E402
from cenografia.nucleo.atmosfera import Atmosfera                         # noqa: E402
import e0_testes as T0                                                     # noqa: E402  (traz heitor_v2 e animacao do rig v2)
import e1_testes as T1                                                     # noqa: E402
import e4_testes as T4                                                     # noqa: E402
HV, AN = T0.HV, T0.AN

OUT = RAIZ / "cenografia" / "testes" / "e6"; OUT.mkdir(parents=True, exist_ok=True)
PLANO = json.loads((RAIZ / "cenografia" / "receitas" / "e6_cena_prova.json").read_text())
CENARIO = RAIZ / "cenografia" / "receitas" / PLANO["cenario"]
W, H = 1080, 1920; FPS = PLANO["fps"]; FUSAO = PLANO["fusao_s"]
ALT_M = 1.40                       # altura do Heitor (4 H)
H_M = ALT_M / 4.0                  # H = altura da cabeça = 0,35 m
V_M = AN.CAMINHADA["v"] * H_M      # velocidade do ciclo do rig no mundo (m/s): 0,63
Z_CALCADA = 0.154                  # topo da calçada (15 cm + variação dos lotes)
res = {}


def suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def receita(tom):
    r = R.carregar(CENARIO); r["camera"] = copy.deepcopy(tom["camera"]); r["luz"]["preset"] = tom["horario"]; r["ancoras"] = {}
    if tom["horario"] == "noite":
        for comp in r["componentes"]:
            if comp["tipo"] == "veiculo" and comp["params"].get("nome") in T4.EM_TRANSITO:
                comp["params"]["farois"] = True
    return r


def placa(tom):
    k, m, hit = CO.construir(receita(tom))
    return Placa(C.pasta(k)), m, hit


def projetar(P, p):
    """Mundo (m) → placa (px) + profundidade ao longo do eixo da câmera — a mesma geometria da câmera do Blender."""
    I = P.m["intrinsecos"]; d = np.asarray(p, float) - np.asarray(I["pos"])
    zc = float(d @ np.asarray(I["dir"])); xc = float(d @ np.asarray(I["dir_x"])); yc = float(d @ np.asarray(I["cima"]))
    return (I["cx"] + I["f_px"] * xc / zc, I["cy"] - I["f_px"] * yc / zc, zc)


def estado(P, tom, t):
    """Onde está o Heitor (mundo e placa), pose do rig, direção na tela e movimento de câmera no instante t."""
    (x0, y0), (dx, dy) = tom["caminho"]["inicio"], tom["caminho"]["direcao"]
    s = V_M * t; mundo = (x0 + dx * s, y0 + dy * s, Z_CALCADA)
    pe = projetar(P, mundo); topo = projetar(P, (mundo[0], mundo[1], Z_CALCADA + ALT_M))
    frente = projetar(P, (mundo[0] + dx * 0.3, mundo[1] + dy * 0.3, Z_CALCADA))
    direcao = 1 if (tom["vista"] != "perfil" or frente[0] >= pe[0]) else -1
    pose, diag = AN.pose_locomocao(t, vista=tom["vista"], tipo="caminhada")
    pose["respira"] = 0.0
    u = t / tom["dur_s"]; mov = {k: a + (b - a) * suave(u) for k, (a, b) in tom["movimento"].items()}
    return {"mundo": mundo, "pe": pe, "topo": topo, "direcao": direcao, "pose": pose, "diag": diag, "mov": mov}


def desenhista(e, t, tom):
    def desenhar(cv, proj):
        x, y, _ = proj(*e["pe"]); _, yt, _ = proj(*e["topo"]); alt = y - yt
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
        HV.desenhar(cv, x, y, alt, vista=tom["vista"], direcao=e["direcao"], pose=e["pose"],
                    rosto=AN.rosto_com_piscada("neutro", t) if tom["vista"] != "costas" else None)
    return desenhar


def quadro(P, A, tom, t, n_quadro, grade_extra=None, extras=True):
    e = estado(P, tom, t)
    g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[tom["horario"]], **(grade_extra or {})))
    img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, cam=e["mov"], personagem=desenhista(e, t, tom),
                   profundidade_personagem=e["pe"][2], semente_grao=n_quadro,
                   ceu_extra=A.ceu(t) if extras else None, frente_extra=A.frente(t) if extras else None)
    return img, e


# ------------------------------------------------------------------ E6-1: placas
def t_placas():
    out = {}
    for tom in PLANO["tomadas"]:
        P, m, hit = placa(tom)
        out[tom["nome"]] = {"cache": "HIT" if hit else "MISS", "montagem_s": m.get("tempo_montagem_s"), "render_total_s": m["tempo_total_s"],
                            "por_camada_s": m["tempo_render_s"], "objetos": m["objetos"],
                            "flutuando": len(m["qa_cena"]["nada_flutuando"]["flutuando"]),
                            "atravessando": len(m["qa_cena"].get("nada_atravessando", {}).get("atravessando", []))}
        print(tom["nome"], json.dumps(out[tom["nome"]], ensure_ascii=False), flush=True)
    return out


# ------------------------------------------------------------------ E6-2: caminho livre (no Blender)
def t_caminho():
    import bpy
    from mathutils import Vector
    out = {}
    _, cena, *_ = CO._montar(receita(PLANO["tomadas"][0]))
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    for tom in PLANO["tomadas"]:
        (x0, y0), (dx, dy) = tom["caminho"]["inicio"], tom["caminho"]["direcao"]
        comp = V_M * tom["dur_s"]; obst = {}; n = 0
        for i in range(int(comp / 0.1) + 1):
            s = i * 0.1
            for lat in (-0.25, 0.0, 0.25):
                x = x0 + dx * s - dy * lat; y = y0 + dy * s + dx * lat; n += 1
                ok, loc, _, _, ob, _ = cena.ray_cast(dg, Vector((x, y, 1.5)), Vector((0, 0, -1)))
                if ok and loc.z > 0.2:
                    obst[ob.name] = round(max(obst.get(ob.name, 0), loc.z), 2)
                ok2, loc2, *_ = cena.ray_cast(dg, Vector((x, y, 0.1)), Vector((0, 0, -1)))
        out[tom["nome"]] = {"comprimento_m": round(comp, 2), "raios": n, "obstaculos_entre_20cm_e_1_5m": obst}
    return out


# ------------------------------------------------------------------ E6-3: vídeo
def t_video():
    tomadas = PLANO["tomadas"]; placas = {}; atm = {}
    for tom in tomadas:
        placas[tom["nome"]], _, _ = placa(tom); atm[tom["nome"]] = Atmosfera(placas[tom["nome"]], tom["clima"], 11)
    n_tom = [int(round(t["dur_s"] * FPS)) for t in tomadas]; n_fus = int(round(FUSAO * FPS))
    total = sum(n_tom) - n_fus * (len(tomadas) - 1)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E6_cena_prova.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    tempos, difs, alturas, ocl, folha, prev = [], [], {t["nome"]: [] for t in tomadas}, {t["nome"]: 0 for t in tomadas}, [], None
    inicio = [sum(n_tom[:i]) - n_fus * i for i in range(len(tomadas))]
    marcos = {(i, int(round(f * n_tom[i]))) for i in range(len(tomadas)) for f in (0.1, 0.4, 0.7, 0.95)}
    for q in range(total):
        t0 = time.time(); ativos = [(i, q - inicio[i]) for i in range(len(tomadas)) if 0 <= q - inicio[i] < n_tom[i]]
        imgs = []
        for i, k in ativos:
            tom = tomadas[i]; P = placas[tom["nome"]]
            img, e = quadro(P, atm[tom["nome"]], tom, k / FPS, q)
            imgs.append((i, k, img))
            if len(ativos) == 1:
                alturas[tom["nome"]].append(e["pe"][1] - e["topo"][1])
                if getattr(P, "ultima_oclusao", None) is not None:
                    x, y = int(e["pe"][0]), int(e["pe"][1] - (e["pe"][1] - e["topo"][1]) * 0.5)
                    if 0 <= y < P.H and 0 <= x < P.W and P.ultima_oclusao[y, x] > 0.5:
                        ocl[tom["nome"]] += 1
            if (i, k) in marcos:
                folha.append((i, k, img))
        if len(imgs) == 2:     # fusão entre tomadas
            a = (imgs[1][1] + 0.5) / n_fus
            img = (imgs[0][2].astype(np.float32) * (1 - a) + imgs[1][2].astype(np.float32) * a).astype(np.uint8)
        else:
            img = imgs[0][2]
        i_rot = imgs[-1][0]
        img = T0._texto(img, ["E6 · cena de prova (teste, não é história)", tomadas[i_rot]["rotulo"]], 1790, 26)
        img = T0._marca(img)
        tempos.append(time.time() - t0)
        if prev is not None and len(imgs) == 1 and imgs[0][1] > 0:
            difs.append(float(np.abs(img.astype(np.int16) - prev.astype(np.int16)).mean()))
        prev = img; pr.stdin.write(np.ascontiguousarray(img).tobytes())
    pr.stdin.close(); pr.wait()
    # folha de quadros: 4 por tomada
    lin = []
    for i, tom in enumerate(tomadas):
        cel = [T0._texto(cv2.resize(im, (270, 480), interpolation=cv2.INTER_AREA), [f"{tom['nome']} · {k / FPS:.1f} s"], 20, 18)
               for (j, k, im) in sorted(folha, key=lambda z: (z[0], z[1])) if j == i]
        lin.append(np.hstack(cel))
    cv2.imwrite(str(OUT / "E6_quadros.jpg"), np.vstack(lin)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    meio = {tom["nome"]: MD.quadro(next(im for (j, k, im) in folha if j == i and abs(k / FPS - 0.4 * tom["dur_s"]) < 0.05))
            for i, tom in enumerate(tomadas)}
    return {"quadros": total, "duracao_s": round(total / FPS, 2), "fps": FPS, "composicao_media_s": round(float(np.mean(tempos)), 2),
            "composicao_max_s": round(float(np.max(tempos)), 2),
            "diferenca_media_entre_quadros_8bit": round(float(np.mean(difs)), 2), "maior_diferenca_entre_quadros_8bit": round(float(np.max(difs)), 2),
            "altura_heitor_px": {k: [round(min(v), 1), round(max(v), 1)] for k, v in alturas.items()},
            "quadros_com_heitor_parcialmente_coberto": ocl, "medidas_cor_quadro_40pct": meio}


# ------------------------------------------------------------------ E6-4: pé de apoio (perfil)
def t_pe():
    """Deslize do pé de apoio na tomada de perfil, medido CONTRA O MUNDO: durante cada apoio, o tornozelo desenhado
    (pelve projetada + deslocamento do ciclo do rig) é comparado com a projeção de um ponto PARADO no mundo, no lugar
    onde esse pé pisou, com o mesmo movimento de câmera. Deslize = variação dessa diferença ao longo do apoio."""
    tom = next(t for t in PLANO["tomadas"] if t["vista"] == "perfil"); P, _, _ = placa(tom)
    (x0, y0), (dx, dy) = tom["caminho"]["inicio"], tom["caminho"]["direcao"]
    trilhas = {"d": [], "e": []}; deslize = []; camera_move = []
    for k in range(int(tom["dur_s"] * FPS)):
        t = k / FPS; e = estado(P, tom, t); mov = e["mov"]
        x, y, _ = P.projetar_ponto(*e["pe"], **mov); _, yt, _ = P.projetar_ponto(*e["topo"], **mov); u = (y - yt) / 4.0
        for s in ("d", "e"):
            pd = e["diag"]["pernas"][s]; desloc_H = pd["alvo"][0] - e["diag"]["pelve_x"]
            x_des = x + e["direcao"] * desloc_H * u
            if pd["apoio"]:
                if not trilhas[s]:
                    sm = V_M * t + desloc_H * H_M; trilhas[s] = [("ref", (x0 + dx * sm, y0 + dy * sm, Z_CALCADA))]
                ref = projetar(P, trilhas[s][0][1]); xr, _, _ = P.projetar_ponto(*ref, **mov)
                trilhas[s].append(x_des - xr); camera_move.append(xr)
            elif trilhas[s]:
                v = [d for d in trilhas[s][1:]]
                if len(v) > 3:
                    deslize.append(max(v) - min(v))
                trilhas[s] = []
    return {"apoios_medidos": len(deslize), "deslize_max_px": round(max(deslize), 2) if deslize else None,
            "deslize_medio_px": round(float(np.mean(deslize)), 2) if deslize else None,
            "obs": "px na placa (1350 de largura); ponto de referência parado no mundo, mesmo movimento de câmera"}


# ------------------------------------------------------------------ E6-5: paleta do Heitor, determinismo, integridade
def t_integridade():
    out = {"paleta": {}}
    for tom in PLANO["tomadas"]:
        P, _, _ = placa(tom); A = Atmosfera(P, tom["clima"], 11); t = tom["dur_s"] * 0.5; e = estado(P, tom, t)
        s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0)
        desenhista(e, t, tom)(cv, lambda x, y, z: P.projetar_ponto(x, y, z, **e["mov"]))
        so = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        x0, y0 = (P.W - W) // 2, (P.H - H) // 2; so = so[y0:y0 + H, x0:x0 + W]
        sem = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=dict(T1.GRADE, exposicao=T1.EXPOSICAO[tom["horario"]], vinheta=0.0, grao=0.0),
                       cam=e["mov"], personagem=desenhista(e, t, tom), profundidade_personagem=e["pe"][2])
        occ = P.ultima_oclusao[y0:y0 + H, x0:x0 + W]; m = (so[..., 3] == 255) & (occ < 0.01)
        dif = np.abs(sem.astype(int) - so[..., :3].astype(int)).max(axis=2)[m]
        out["paleta"][tom["nome"]] = {"pixels_medidos": int(m.sum()), "identicos_pct": round(100 * float((dif == 0).mean()), 2) if dif.size else None,
                                      "cobertos_por_algo_mais_perto": int(((so[..., 3] == 255) & (occ >= 0.01)).sum())}
        if tom is PLANO["tomadas"][0]:
            a, _ = quadro(P, A, tom, 1.0, 30); b, _ = quadro(P, A, tom, 1.0, 30)
            out["mesmo_quadro_duas_vezes_identico"] = hashlib.sha256(a.tobytes()).hexdigest() == hashlib.sha256(b.tobytes()).hexdigest()
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    out.update(assinatura_rig_identidade_skill=hashlib.sha256(ls.encode()).hexdigest(), alteracoes_pendentes_nesses_caminhos=dif or "nenhuma",
               verificar_f1_vistas_ok=f1.count("| OK |"), velocidade_m_s=round(V_M, 3))
    return out


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e6_metricas.json"
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
    rodar("E6_1_placas", t_placas)
    rodar("E6_2_caminho_livre", t_caminho)
    rodar("E6_4_pe_de_apoio", t_pe)
    rodar("E6_5_integridade", t_integridade)
    rodar("E6_3_video", t_video)
