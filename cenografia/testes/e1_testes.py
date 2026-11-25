#!/usr/bin/env python3
"""Cenografia — testes da etapa E1 (materiais, céu e atmosfera, tempo de render). Renderiza, MEDE e documenta.

E1-1 folha de materiais (e1_materiais.py)
E1-2 placas: 5 horários (manhã, meio-dia, tarde dourada, crepúsculo, noite) × piso seco/molhado, com amostras por
     camada (tempo real medido por placa e por camada)
E1-3 grade 5 horários × 4 climas (limpo, nublado, neblina, chuva) + medidas de cor por célula
E1-4 vídeo de atmosfera: horários em sequência com nuvens derivando, chuva; Heitor rig v2 sem alteração
E1-5 continuidade das nuvens (sem saltos entre quadros) e determinismo (mesma semente = mesmo quadro)
E1-6 integridade (rig v2, ID-001..ID-004, skill)
Saídas: cenografia/testes/e1/ (folhas, vídeo, e1_metricas.json). Placas: .cache/ (fora do Git).
"""
import hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia import construir as CO                                    # noqa: E402
from cenografia.nucleo import receita as R, cache as C, medidas as MD      # noqa: E402
from cenografia.nucleo.compositor import Placa                            # noqa: E402
from cenografia.nucleo.atmosfera import Atmosfera, CLIMAS                 # noqa: E402
import e0_testes as T0                                                     # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e1"; OUT.mkdir(parents=True, exist_ok=True)
REC = RAIZ / "cenografia" / "receitas" / "e1_calcada.json"
HORARIOS = ["manha", "meio_dia", "tarde_dourada", "crepusculo", "noite"]
NOMES_H = {"manha": "manhã", "meio_dia": "meio-dia", "tarde_dourada": "tarde dourada", "crepusculo": "crepúsculo", "noite": "noite"}
CLIMAS_ORD = ["limpo", "nublado", "neblina", "chuva"]
AMOSTRAS_CAMADA = None      # a receita já traz as amostras por camada escolhidas no experimento (A: 4/16/24/24/16)
GRADE = dict(T0.GRADE)
EXPOSICAO = {"manha": -0.55, "meio_dia": -0.75, "tarde_dourada": -0.6, "crepusculo": -0.35, "noite": 0.0}
FPS = 30; W, H = 1080, 1920
res = {}


def receita(horario, molhado=False):
    r = R.carregar(REC); r["luz"]["preset"] = horario
    if AMOSTRAS_CAMADA:
        r["saida"]["amostras_por_camada"] = AMOSTRAS_CAMADA
    if molhado:
        for c in r["componentes"]:
            if c["tipo"] == "rua_reta":
                c["params"]["umidade"] = 0.85
    return r


def placa(horario, molhado=False):
    k, m, hit = CO.construir(receita(horario, molhado))
    return Placa(C.pasta(k)), m, hit


def quadro(P, horario, clima, t=0.0, heitor=True, semente=11, cam=None):
    A = Atmosfera(P, clima, semente)
    g = A.grade(dict(GRADE, exposicao=EXPOSICAO[horario]))
    return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, ceu_extra=A.ceu(t), frente_extra=A.frente(t), cam=cam or {},
                    personagem=T0.heitor(P, t) if heitor else None, profundidade_personagem=T0.DP(P) if heitor else None,
                    semente_grao=int(t * FPS))


# ------------------------------------------------------------------ E1-1
def t_materiais():
    p = subprocess.run([str(RAIZ / ".venv/bin/python"), str(Path(__file__).with_name("e1_materiais.py"))], capture_output=True, text=True)
    return json.loads((OUT / "e1_materiais.json").read_text())


# ------------------------------------------------------------------ E1-2
def t_placas():
    out = {}
    for h in HORARIOS:
        for molhado in (False, True):
            t = time.time(); P, m, hit = placa(h, molhado)
            out[f"{h}{'_molhado' if molhado else ''}"] = {"cache": "HIT" if hit else "MISS", "render_total_s": m["tempo_total_s"],
                                                           "por_camada_s": m["tempo_render_s"], "amostras_por_camada": m.get("amostras_por_camada")}
            print(h, molhado, out[f"{h}{'_molhado' if molhado else ''}"], flush=True)
    tot = [v["render_total_s"] for v in out.values()]
    out["_resumo"] = {"placas": len(tot), "media_s": round(float(np.mean(tot)), 1), "max_s": round(float(np.max(tot)), 1),
                      "dentro_meta_3_5_min": sum(1 for x in tot if x <= 300)}
    return out


# ------------------------------------------------------------------ E1-3
def t_grade():
    tw, th = 270, 480; linhas = []; medidas = {}
    for h in HORARIOS:
        celulas = []
        for c in CLIMAS_ORD:
            P, _, _ = placa(h, molhado=(c == "chuva"))
            img = quadro(P, h, c, t=0.0, heitor=False)
            medidas[f"{h}/{c}"] = MD.quadro(img)
            celulas.append(T0._texto(cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA), [NOMES_H[h], c], 30, 20))
        linhas.append(np.hstack(celulas))
    folha = np.vstack(linhas)
    cv2.imwrite(str(OUT / "E1_grade_horarios_climas.png"), folha[..., ::-1])
    return medidas


# ------------------------------------------------------------------ E1-4 / E1-5
def t_video():
    seq = [("manha", "limpo"), ("meio_dia", "limpo"), ("tarde_dourada", "limpo"), ("tarde_dourada", "nublado"),
           ("tarde_dourada", "chuva"), ("crepusculo", "limpo"), ("noite", "limpo"), ("noite", "neblina")]
    dur, fus = 2.0, 0.5
    placas = {}
    for h, c in seq:
        placas[(h, c == "chuva")] = placas.get((h, c == "chuva")) or placa(h, c == "chuva")[0]
    n = int(len(seq) * dur * FPS); tempos = []; saltos = []; prev = None
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E1_atmosfera.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for q in range(n):
        t = q / FPS; i = min(len(seq) - 1, int(t / dur)); h, c = seq[i]; t0 = time.time()
        img = quadro(placas[(h, c == "chuva")], h, c, t=t)
        tl = t - i * dur
        if i > 0 and tl < fus:     # fusão com o plano anterior
            h2, c2 = seq[i - 1]; img2 = quadro(placas[(h2, c2 == "chuva")], h2, c2, t=t)
            k = tl / fus; img = (img.astype(np.float32) * k + img2.astype(np.float32) * (1 - k)).astype(np.uint8)
        img = T0._marca(T0._texto(img, ["E1 · céu e atmosfera", f"{NOMES_H[h]} · {c}"], 1760, 30))
        tempos.append(time.time() - t0)
        if prev is not None and not (i > 0 and tl < fus + 1 / FPS) and int((t - 1 / FPS) / dur) == i:
            ceu = slice(0, int(H * 0.35))
            saltos.append(float(np.abs(img[ceu].astype(int) - prev[ceu].astype(int)).mean()))
        prev = img; pr.stdin.write(np.ascontiguousarray(img).tobytes())
    pr.stdin.close(); pr.wait()
    return {"quadros": n, "composicao_media_s": round(float(np.mean(tempos)), 2), "composicao_max_s": round(float(np.max(tempos)), 2),
            "ceu_diferenca_media_entre_quadros_8bit": round(float(np.mean(saltos)), 2), "ceu_maior_diferenca_entre_quadros_8bit": round(float(np.max(saltos)), 2)}


def t_determinismo():
    P, _, _ = placa("tarde_dourada")
    a = quadro(P, "tarde_dourada", "limpo", t=1.0); b = quadro(P, "tarde_dourada", "limpo", t=1.0)
    A2 = Atmosfera(P, "limpo", 12); c = P.compor(pesos=A2.pesos(), nevoa=A2.nevoa(), grade=A2.grade(dict(GRADE, exposicao=EXPOSICAO["tarde_dourada"])),
                                                ceu_extra=A2.ceu(1.0), personagem=T0.heitor(P, 1.0), profundidade_personagem=T0.DP(P), semente_grao=30)
    return {"mesma_semente_identico": hashlib.sha256(a.tobytes()).hexdigest() == hashlib.sha256(b.tobytes()).hexdigest(),
            "outra_semente_diferente": bool(np.abs(a.astype(int) - c.astype(int)).max() > 0)}


def t_integridade():
    P, _, _ = placa("tarde_dourada")
    T0.heitor(P, 0.0)
    r = T0.t_integridade(P, None)
    return r


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e1_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())

    def rodar(nome, f):
        if so and nome not in so:
            return
        t = time.time(); res[nome] = f()
        if isinstance(res[nome], dict):
            res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False)[:700], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    rodar("E1_1_materiais", t_materiais)
    rodar("E1_2_placas", t_placas)
    rodar("E1_3_grade", t_grade)
    rodar("E1_4_video", t_video)
    rodar("E1_5_determinismo", t_determinismo)
    rodar("E1_6_integridade", t_integridade)
