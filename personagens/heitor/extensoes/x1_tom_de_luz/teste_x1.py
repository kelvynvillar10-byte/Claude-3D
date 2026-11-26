#!/usr/bin/env python3
"""Testes e demonstração da EXTENSÃO X1 (tom de luz no personagem) — APROVADA pelo diretor em 26/11/2026.

1 desligado = idêntico (regressão do encaixe no compositor)
2 o desenho não muda: alfa idêntico; luz neutra = mesmas cores (≤ 1/255)
3 legibilidade da estampa: contraste (WCAG) "Modo" e "Curioso" × camiseta, sem e com o tom, em cada situação
4 cores oficiais: ΔE e giro de matiz de pele, camiseta e cabelo, em cada situação
5 contorno: largura (% da altura) e quanto pega do rosto
6 comparativo (imagem) e vídeo lado a lado (sem | com); tempo extra por quadro
7 integridade do rig v2 (assinatura) — a extensão fica FORA de rig_v2/
"""
import copy, hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "cenografia" / "testes")); sys.path.insert(0, str(AQUI))
from cenografia.nucleo.compositor import Placa                     # noqa: E402
from cenografia.nucleo.atmosfera import Atmosfera                  # noqa: E402
import e0_testes as T0, e1_testes as T1, e6_cena_prova as E6, e8_testes as E8   # noqa: E402
from efeitos.nucleo.base import Mesa                               # noqa: E402
from efeitos.nucleo import protecao as PR                          # noqa: E402
import tom_de_luz as X1                                            # noqa: E402

OUT = AQUI / "saidas"; OUT.mkdir(exist_ok=True)
HV, AN = T0.HV, T0.AN; FPS = 30; W, H = 1080, 1920
OFICIAIS = {"pele": "#ffd9c2", "camiseta": "#3d80d8", "cabelo": "#3a2316", "estampa_modo": "#f2efe8", "estampa_curioso": "#ffc21f"}
res = {}


# ------------------------------------------------------------------ situações (cena + personagem + luzes)
def situacao_e6(nome_tom, t):
    tom = next(x for x in E6.PLANO["tomadas"] if x["nome"] == nome_tom); P, _, _ = E6.placa(tom); A = Atmosfera(P, tom["clima"], 11)
    e = E6.estado(P, tom, t)
    pers = {"pe_mundo": e["mundo"], "altura_m": E6.ALT_M}
    def compor(tom_fn, k=0):
        g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[tom["horario"]]))
        return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, cam=e["mov"], personagem=E6.desenhista(e, t, tom),
                        profundidade_personagem=e["pe"][2], semente_grao=k, ceu_extra=A.ceu(t), tom_personagem=tom_fn)
    return P, compor, pers, [], (e["pose"], tom["vista"], e["direcao"])


def situacao_e8(i_clipe, k):
    PL = E8.placas(); clipe = E8.CLIPES[i_clipe]; ef, P, A, alvo = E8.criar(clipe, PL); mesa = Mesa([ef], fps=FPS); hor = clipe[3]
    for kk in range(k):
        pose, _ = E8.pose_poder(P, ef, kk / FPS, alvo); mesa.preparar(P, {}, kk / FPS, kk, {"pe_mundo": E8.PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
    pose, rosto = E8.pose_poder(P, ef, k / FPS, alvo)
    info = {"pe_mundo": E8.PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1}
    estado = {"pronto": False}
    def compor(tom_fn, kk=k):
        mesa.preparar(P, {}, k / FPS, k, info)
        g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[hor]))
        return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, personagem=E8.desenhista(mesa, pose, rosto), profundidade_personagem=mesa.ctx.placa(E8.PE)[2],
                        efeitos=mesa, deslocamento_px=mesa.tremida(), semente_grao=k, ceu_extra=A.ceu(k / FPS), tom_personagem=tom_fn)
    mesa.preparar(P, {}, k / FPS, k, info); luzes = mesa.luzes(P, {})
    return P, compor, {"pe_mundo": E8.PE, "altura_m": 1.4}, luzes, (pose, "frente", 1)


SITUACOES = [
    ("manhã (cena de prova)", lambda: situacao_e6("manha_frente", 3.0)),
    ("tarde dourada, perfil", lambda: situacao_e6("tarde_perfil", 3.0)),
    ("noite, de costas", lambda: situacao_e6("noite_costas", 2.0)),
    ("eletricidade moderada (manhã)", lambda: situacao_e8(1, 40)),
    ("eletricidade extrema (noite)", lambda: situacao_e8(2, 42)),
    ("terra extrema (manhã)", lambda: situacao_e8(5, 75)),
]


# ------------------------------------------------------------------ medidas sobre a camada do personagem
def camada_heitor(P, pers, pose_info, cam=None):
    """O Heitor sozinho (RGBA como o skia entrega ao compositor: cor não pré-multiplicada; placa) — o mesmo desenho que o compositor recebe."""
    pose, vista, direcao = pose_info; cam = cam or {}
    I = P.m["intrinsecos"]; pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))
    def placa(p):
        d = np.asarray(p, float) - pos; z = float(d @ dr); return P.cx + P.f * float(d @ dx) / z, P.cy - P.f * float(d @ cima) / z, z
    pe = np.asarray(pers["pe_mundo"]); u, v, z = placa(pe); ut, vt, zt = placa(pe + [0, 0, pers["altura_m"]])
    s = skia.Surface(P.W, P.H); c = s.getCanvas(); c.clear(0)
    x, y, _ = P.projetar_ponto(u, v, z, **cam); _, yt, _ = P.projetar_ponto(ut, vt, zt, **cam)
    HV.desenhar(c, x, y, y - yt, vista=vista, direcao=direcao, pose=pose)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0, (x, y, y - yt)


def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def _lab(rgb255):
    c = np.asarray(rgb255, float) / 255; c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]); x, y, z = M @ c / np.array([0.95047, 1.0, 1.08883])
    f = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return np.array([116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))])


def _contraste(a255, b255):
    def L(c):
        c = np.asarray(c, float) / 255; c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    l1, l2 = sorted([L(a255), L(b255)], reverse=True); return (l1 + 0.05) / (l2 + 0.05)


def medir(fig0, fig1):
    """Cores médias (8 bits) dos pixels que, sem tom, têm exatamente as cores oficiais; com e sem tom."""
    a = fig0[..., 3] > 0.999; rgb0 = np.round(fig0[..., :3] * 255); out = {}
    for nome, h in OFICIAIS.items():
        alvo = _hex(h) if not nome.startswith("estampa") else np.round(0.93 * _hex(h) + 0.07 * _hex(OFICIAIS["camiseta"]))   # o rig pinta a estampa com 93 % de opacidade
        m = a & (np.abs(rgb0 - alvo).max(-1) <= 1)
        if m.sum() < 20:
            continue
        c0 = (fig0[..., :3][m] * 255).mean(0); c1 = (fig1[..., :3][m] * 255).mean(0)
        l0, l1 = _lab(c0), _lab(c1); h0, h1 = math.degrees(math.atan2(l0[2], l0[1])), math.degrees(math.atan2(l1[2], l1[1]))
        out[nome] = {"pixels": int(m.sum()), "cor_sem": [int(v) for v in c0], "cor_com": [int(v) for v in c1], "delta_E": round(float(np.linalg.norm(l1 - l0)), 1),
                     "giro_matiz_graus": round(((h1 - h0 + 180) % 360) - 180, 1), "_c0": c0, "_c1": c1}
    if "camiseta" in out:
        for est in ("estampa_modo", "estampa_curioso"):
            if est in out:
                out[est]["contraste_sem"] = round(_contraste(out[est]["_c0"], out["camiseta"]["_c0"]), 2)
                out[est]["contraste_com"] = round(_contraste(out[est]["_c1"], out["camiseta"]["_c1"]), 2)
    for v in out.values():
        v.pop("_c0", None); v.pop("_c1", None)
    return out


# ------------------------------------------------------------------ testes
def t_regressao():
    ref = json.loads((RAIZ / "cenografia" / "testes" / "e7" / "regressao_ref.json").read_text()); out = {}
    for tom in E6.PLANO["tomadas"]:
        P = Placa(ref[tom["nome"]]["placa"]); A = Atmosfera(P, tom["clima"], 11); img, _ = E6.quadro(P, A, tom, 2.0, 60)
        out[tom["nome"]] = hashlib.sha256(img.tobytes()).hexdigest() == ref[tom["nome"]]["sha256"]
    return {"desligado_identico_ao_de_antes": out}


def t_situacoes():
    out = {}; pares = []
    for rot, f in SITUACOES:
        P, compor, pers, luzes, pose_info = f(); reg = []
        compor(None)                                                   # aquecimento (cache de camadas), fora da medida de tempo
        t0 = time.time(); sem = compor(None); t_sem = time.time() - t0
        t0 = time.time(); com = compor(X1.fazer_tom(pers, luzes, registro=reg)); t_com = time.time() - t0
        fig0, (x, y, alt) = camada_heitor(P, pers, pose_info); prm = reg[-1]
        fig1 = X1.aplicar(fig0, prm)
        cores = medir(fig0, fig1)
        rim = np.zeros(fig0.shape[:2], np.float32)
        for r in prm["rims"] + prm["brilhos"]:
            rim = np.maximum(rim, X1._contorno(fig0[..., 3], r["dir"].astype(np.float32), max(prm["altura_px"], 10)))
        rosto = (((np.mgrid[0:P.H, 0:P.W][1] - x) / (0.15 * alt)) ** 2 + ((np.mgrid[0:P.H, 0:P.W][0] - (y - alt + 0.13 * alt)) / (0.14 * alt)) ** 2) <= 1
        dentro = fig0[..., 3] > 0.5
        out[rot] = {"multiplicador_brilho": round(prm["multiplicador"], 3), "tinta_rgb": [round(float(v), 3) for v in prm["tinta"]],
                    "luzes_de_efeito": len(prm["brilhos"]), "alfa_identico": bool(np.array_equal(fig0[..., 3], fig1[..., 3])),
                    "contorno_pct_do_personagem": round(100 * float(((rim > 0.05) & dentro).sum() / max(dentro.sum(), 1)), 2),
                    "contorno_pct_do_rosto": round(100 * float(((rim > 0.05) & rosto & dentro).sum() / max((rosto & dentro).sum(), 1)), 2),
                    "cores": cores, "tempo_extra_s": round(t_com - t_sem, 2)}
        print(rot, json.dumps(out[rot], ensure_ascii=False)[:400], flush=True)
        x0, y0 = (P.W - W) // 2, (P.H - H) // 2
        jan = lambda im: im[max(0, int(y - alt * 1.25) - y0):int(y + alt * 0.2) - y0, max(0, int(x - alt * 0.7) - x0):int(x + alt * 0.7) - x0]
        a_, b_ = jan(sem), jan(com); hh = 640; esc = hh / a_.shape[0]
        a_ = cv2.resize(a_, (int(a_.shape[1] * esc), hh)); b_ = cv2.resize(b_, (int(b_.shape[1] * esc), hh))
        pares.append(T0._texto(np.hstack([T0._texto(a_, ["sem tom"], 26, 22), T0._texto(b_, ["com tom (X1)"], 26, 22)]), [rot], 600, 24))
    larg = max(p.shape[1] for p in pares)
    pares = [np.pad(p, ((0, 0), (0, larg - p.shape[1]), (0, 0))) for p in pares]
    cv2.imwrite(str(OUT / "X1_comparativo.jpg"), np.vstack([np.hstack(pares[i:i + 3]) for i in (0, 3)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return out


def t_neutro():
    """Luz neutra (tinta 1, sem contorno, sem volume, sem efeitos) → mesmas cores (só arredondamento)."""
    P, _, pers, _, pose_info = situacao_e6("manha_frente", 3.0); fig0, _ = camada_heitor(P, pers, pose_info)
    prm = {"tinta": np.ones(3), "rims": [], "brilhos": [], "centro": np.array([P.W / 2, P.H / 2]), "altura_px": 500, "volume": 0.0}
    fig1 = X1.aplicar(fig0, prm); d = np.abs(fig1 - fig0).max() * 255
    return {"diferenca_maxima_8bit": round(float(d), 3), "alfa_identico": bool(np.array_equal(fig0[..., 3], fig1[..., 3]))}


def t_video():
    """Lado a lado (sem | com): eletricidade extrema à noite (3,2 s) e a tomada da noite da cena de prova (3 s)."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x960", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "X1_lado_a_lado.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); n = 0; t0 = time.time()
    PL = E8.placas(); clipe = E8.CLIPES[2]; ef, P, A, alvo = E8.criar(clipe, PL); mesa = Mesa([ef], fps=FPS)
    for k in range(int(clipe[5] * FPS)):
        t = k / FPS; pose, rosto = E8.pose_poder(P, ef, t, alvo); info = {"pe_mundo": E8.PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1}
        par = []
        for tom_on in (False, True):
            mesa.preparar(P, {}, t, k, info); tom = X1.fazer_tom({"pe_mundo": E8.PE, "altura_m": 1.4}, mesa.luzes(P, {})) if tom_on else None
            g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["noite"]))
            im = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, personagem=E8.desenhista(mesa, pose, rosto), profundidade_personagem=mesa.ctx.placa(E8.PE)[2],
                          efeitos=mesa, deslocamento_px=mesa.tremida(), semente_grao=k, ceu_extra=A.ceu(t), tom_personagem=tom)
            par.append(T0._texto(cv2.resize(im, (540, 960), interpolation=cv2.INTER_AREA), ["com tom (X1)" if tom_on else "sem tom"], 20, 22))
        q = T0._marca(np.hstack(par)); pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
    tom6 = next(x for x in E6.PLANO["tomadas"] if x["nome"] == "noite_costas"); P6, _, _ = E6.placa(tom6); A6 = Atmosfera(P6, "limpo", 11)
    for k in range(90):
        t = k / FPS; e = E6.estado(P6, tom6, t); par = []
        for tom_on in (False, True):
            tom = X1.fazer_tom({"pe_mundo": e["mundo"], "altura_m": E6.ALT_M}) if tom_on else None
            im = P6.compor(pesos=A6.pesos(), nevoa=A6.nevoa(), grade=A6.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["noite"])), cam=e["mov"],
                           personagem=E6.desenhista(e, t, tom6), profundidade_personagem=e["pe"][2], semente_grao=k, ceu_extra=A6.ceu(t), tom_personagem=tom)
            par.append(T0._texto(cv2.resize(im, (540, 960), interpolation=cv2.INTER_AREA), ["com tom (X1)" if tom_on else "sem tom"], 20, 22))
        q = T0._marca(np.hstack(par)); pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
    pr.stdin.close(); pr.wait()
    return {"quadros": n, "duracao_s": round(n / FPS, 1), "tempo_total_s": round(time.time() - t0, 1)}


def t_borda_compositor():
    """DIAGNÓSTICO (não corrige): o compositor soma a cor do Heitor como se fosse pré-multiplicada, mas o skia entrega
    não pré-multiplicada. Nos pixels de borda (alfa parcial) isso clareia a borda. Mede quanto, num quadro real."""
    out = {}
    for nome in ("manha_frente", "noite_costas"):
        P, _, pers, _, pi = situacao_e6(nome, 3.0); fig, (x, y, alt) = camada_heitor(P, pers, pi); a = fig[..., 3:4]
        borda = (a[..., 0] > 0.004) & (a[..., 0] < 0.996)
        erro = (fig[..., :3] * (1 - a)).max(-1) * 255              # atual − correto, antes do fundo
        out[nome] = {"pixels_de_borda": int(borda.sum()), "pixels_do_heitor": int((a[..., 0] > 0.5).sum()),
                     "clareamento_medio_8bit": round(float(erro[borda].mean()), 1), "clareamento_maximo_8bit": round(float(erro[borda].max()), 1),
                     "pixels_com_mais_de_20": int((erro[borda] > 20).sum())}
    return out


def t_integridade():
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    return {"assinatura_rig_identidade_skill": hashlib.sha256(ls.encode()).hexdigest(), "alteracoes_pendentes_nesses_caminhos": dif or "nenhuma",
            "verificar_f1_vistas_ok": f1.count("| OK |")}


if __name__ == "__main__":
    so = sys.argv[1:]; caminho = OUT / "x1_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())
    for nome, f in (("X1_1_regressao", t_regressao), ("X1_2_neutro", t_neutro), ("X1_3_situacoes", t_situacoes), ("X1_4_video", t_video), ("X1_5_integridade", t_integridade), ("X1_6_borda_compositor", t_borda_compositor)):
        if so and nome not in so:
            continue
        t = time.time(); res[nome] = f(); res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False, default=str)[:900], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
