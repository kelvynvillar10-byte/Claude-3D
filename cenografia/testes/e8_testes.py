#!/usr/bin/env python3
"""E8 — testes dos PODERES eletricidade e terra (efeitos/poderes). Não mexem no rig: o Heitor só é POSADO com a API do
rig v2 (mira_braco para apontar o braço ao alvo, mistura_expr para a expressão), sem alteração.

E8-1 vídeo: 6 clipes (eletricidade e terra × discreto, moderado, extremo) na rua da E6 (manhã e noite)
E8-2 energia medida por fase e por intensidade (o que cada camada põe no quadro + luz) → ordem discreto < moderado < extremo
E8-3 contatos: o raio sai da MÃO do rig e chega ao ALVO (erro em px); redesenho a cada 2–3 quadros
E8-4 família de cor × camiseta (ΔE, CIELAB)
E8-5 segurança: flashes por segundo no vídeo pronto (≤ 3)
E8-6 proteção: cobertura máxima do rosto e da estampa (≤ 0,35)
E8-7 paleta do Heitor idêntica ao rig sozinho nos pixels sem efeito na frente
E8-8 terra: a face de cima do pedaço é o próprio fundo (erro médio); rachadura cresce sem voltar
E8-9 determinismo; E8-10 integridade (rig, identidade, skill)
"""
import copy, hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia.nucleo.atmosfera import Atmosfera                          # noqa: E402
import e0_testes as T0                                                      # noqa: E402
import e1_testes as T1                                                      # noqa: E402
import e6_cena_prova as E6                                                  # noqa: E402
import gestos as GE                                                         # noqa: E402  (rig v2: só a API)
from efeitos.nucleo.base import Params, Mesa, Contexto, Tela, carregar_plugins, REGISTRO   # noqa: E402
from efeitos.nucleo import seguranca as SG, protecao as PR, contatos as CT                 # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e8"; OUT.mkdir(parents=True, exist_ok=True)
HV, AN = T0.HV, T0.AN
FPS = 30; W, H = 1080, 1920; PE = (-5.1, 6.0, 0.154)
TOM = {"manha": E6.PLANO["tomadas"][0], "noite": E6.PLANO["tomadas"][2]}
CAMISETA = "#3d80d8"
carregar_plugins()
res = {}
CLIPES = [
    ("eletricidade_discreto", "eletricidade", "discreto", "manha", {"alvo": (-4.6, 8.4, 1.3)}, 3.2),
    ("eletricidade_moderado", "eletricidade", "moderado", "manha", {"alvo": (-4.15, 8.96, 2.25)}, 3.2),
    ("eletricidade_extremo", "eletricidade", "extremo", "noite", {"alvo": (-4.6, 8.8, 0.16), "alvo_no_chao": True}, 3.2),
    ("terra_discreto", "terra", "discreto", "manha", {"origem": PE, "alvo": (-5.0, 9.6, 0.154)}, 3.2),
    ("terra_moderado", "terra", "moderado", "noite", {"origem": PE, "alvo": (-5.75, 10.2, 0.154)}, 3.4),
    ("terra_extremo", "terra", "extremo", "manha", {"origem": PE, "alvo": (-4.55, 10.8, 0.154)}, 3.4),
]


def placas():
    return {k: E6.placa(t)[0] for k, t in TOM.items()}


def prof_frontal(P):
    """Profundidade do que está mais perto em cada pixel (câmera parada): para conferir se o chão está visível."""
    if "_prof_e8" not in P.__dict__:
        A = Atmosfera(P, "limpo", 11); P._pilha(P.m["camadas"], A.pesos(), {}, None, frontal=True); P._prof_e8 = P.ultima_prof_frontal.copy()
    return P._prof_e8


def fundo(P, hor):
    """O cenário sem personagem e sem efeitos, na resolução da placa (fonte da textura dos pedaços de terra)."""
    c = P.__dict__.setdefault("_fundo_e8", {})
    if hor not in c:
        A = Atmosfera(P, "limpo", 11)
        img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[hor], vinheta=0.0, grao=0.0)),
                       saida=(P.W, P.H))
        c[hor] = img.astype(np.float32) / 255.0
    return c[hor]


class MesaMedida(Mesa):
    """Mesa que também MEDE o que cada camada põe no quadro (energia) e a cobertura do rosto e da estampa."""
    def preparar(self, *a, **k):
        self.energia = 0.0; self.cobertura = None
        return super().preparar(*a, **k)

    def desenhar(self, P, cam, onde):
        c = super().desenhar(P, cam, onde)
        if c is not None:
            self.energia += float(c["rgba"][..., 3].mean() + c["add"].max(axis=2).mean())
            if onde == "frente" and self.ctx.personagem:
                self.cobertura = PR.cobertura(c, self.ctx)
            self.ultima_frente = c if onde == "frente" else getattr(self, "ultima_frente", None)
        return c


def lado_mao(P, alvo_mundo):
    """De frente, a mão ESQUERDA do Heitor fica à direita da tela: aponta com a mão do lado do alvo (o braço não cruza o peito)."""
    ctx = Contexto(P, {}, 0.0)
    return "e" if ctx.tela(alvo_mundo)[0] > ctx.tela(PE)[0] else "d"


def pose_poder(P, ef, t, alvo_mundo):
    """Pose do rig: braço direito levanta e aponta ao alvo (mira_braco, com assentamento), mão aberta; expressão de
    neutro → bravo e volta. Tudo pela API do rig (sem alterar o rig)."""
    ctx = Contexto(P, {}, t); x, y, _, _ = ctx.tela(PE); _, yt, _, _ = ctx.tela((PE[0], PE[1], PE[2] + 1.4)); u = (y - yt) / 4
    sx, sy, _, _ = ctx.tela(alvo_mundo); alvo_H = ((sx - x) / u, (sy - y) / u)
    base = HV.pose_base("frente"); base["respira"] = math.sin(2 * math.pi * t / 2.8)
    lado = lado_mao(P, alvo_mundo); mira = copy.deepcopy(base); GE.mira_braco(mira, "frente", lado, alvo_H)
    t_at, t_fim = ef.fases.inicio_de("ativacao"), ef.fases.inicio_de("encerramento")
    if t < t_fim:
        k = GE.curva((t - ef.fases.inicio_de("inicio")) / max(t_at + 0.25, 1e-6), "volta")
    else:
        k = 1 - GE.curva((t - t_fim) / max(ef.fases.duracao - t_fim, 1e-6), "suave")
    p = copy.deepcopy(base)
    for c in (f"braco_{lado}", f"antebraco_{lado}", f"mao_{lado}"):
        p[c] = base[c] + (mira[c] - base[c]) * k
    if k > 0.4:
        p[f"dedos_{lado}"] = GE.mao("aberta")
    rosto = GE.mistura_expr(HV.EXPRESSOES["neutro"], HV.EXPRESSOES["bravo"], min(1.0, max(0.0, k)))
    return p, rosto


def desenhista(mesa, pose, rosto):
    def f(cv, proj):
        u, v, z = mesa.ctx.placa(PE); ut, vt, zt = mesa.ctx.placa((PE[0], PE[1], PE[2] + 1.4))
        x, y, _ = proj(u, v, z); _, yt, _ = proj(ut, vt, zt); alt = y - yt
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
        HV.desenhar(cv, x, y, alt, vista="frente", pose=pose, rosto=rosto)
    return f


def mira_de(clipe, alvo):
    """Para onde o braço aponta: na terra, um pouco acima do alvo (gesto de comando), não para o chão."""
    return (alvo[0], alvo[1], alvo[2] + 0.9) if clipe[1] == "terra" else alvo


def criar(clipe, PL):
    nome, poder, intens, hor, kw, dur = clipe; P = PL[hor]; kw = dict(kw)
    if poder == "terra":
        kw.update(fundo=fundo(P, hor), prof=prof_frontal(P), faixa_x=(-6.75, -3.75), camera_pos=tuple(P.m["intrinsecos"]["pos"]))
    else:
        kw.update(mao=f"mao_{lado_mao(P, kw['alvo'])}")
    ef = REGISTRO[poder](Params(intensidade=intens, duracao=dur, semente=11), **kw)
    return ef, P, Atmosfera(P, "limpo", 11), mira_de(clipe, kw.get("alvo"))


def quadro(P, A, mesa, ef, alvo, t, k, hor, cam=None, grade_extra=None):
    cam = cam or {}; pose, rosto = pose_poder(P, ef, t, alvo)
    mesa.preparar(P, cam, t, k, {"pe_mundo": PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
    g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[hor], **(grade_extra or {})))
    img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, cam=cam, personagem=desenhista(mesa, pose, rosto),
                   profundidade_personagem=mesa.ctx.placa(PE)[2], efeitos=mesa, deslocamento_px=mesa.tremida(), semente_grao=k, ceu_extra=A.ceu(t))
    return img, pose, rosto


# ------------------------------------------------------------------ E8-1 / 2 / 3 / 5 / 6: vídeo + medidas por quadro
def t_video(PL):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "25", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E8_poderes.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); out = {}; folha = []; q = 0; lums_total = []
    for clipe in CLIPES:
        nome = clipe[0]; ef, P, A, alvo = criar(clipe, PL); mesa = MesaMedida([ef], fps=FPS); hor = clipe[3]
        n = int(clipe[5] * FPS); energia = {}; cob = {"rosto": 0.0, "estampa": 0.0}; tempos = []; lums = []; contatos = []; sementes = {}
        for k in range(n):
            t = k / FPS; cam = {"tz": 0.3 * (k / n) ** 1.3}; t0 = time.time()
            img, pose, _ = quadro(P, A, mesa, ef, alvo, t, q, hor, cam=cam); tempos.append(time.time() - t0)
            fase = ef.fases.em(t)[0] or "—"
            energia.setdefault(fase, []).append(mesa.energia + sum(L["forca"] for L in mesa.luzes(P, cam)) / 10)
            if mesa.cobertura:
                cob = {kk: max(cob[kk], mesa.cobertura[kk]) for kk in cob}
            if poder_eletrico(ef) and ef.ultimas_curvas and fase in ("uso", "impacto") and mesa.ativos:
                ctx = mesa.ctx; ini = ef.ultimas_curvas[0][0][0]; fim = ef.ultimas_curvas[0][0][-1]
                m = ctx.tela(CT.rig_mundo(ctx, ef.mao)); a_ = ctx.tela(alvo); i_ = ctx.tela(ini); f_ = ctx.tela(fim)
                contatos.append((math.hypot(i_[0] - m[0], i_[1] - m[1]), math.hypot(f_[0] - a_[0], f_[1] - a_[1]) if clipe[2] == "moderado" else 0.0))
                sementes.setdefault(int(t), set()).add(ef.ultimo_redesenho)
            rot = f"{clipe[1]} · {clipe[2]}"
            img = T0._texto(img, ["E8 · poderes (teste, não é história)", rot, f"fase: {fase}"], 1745, 25)
            img = T0._marca(img); pr.stdin.write(np.ascontiguousarray(img).tobytes()); q += 1
            l = SG.luminancia_relativa(cv2.resize(img, (135, 240), interpolation=cv2.INTER_AREA)); lums.append(l); lums_total.append(l)
            if k in (int(n * 0.3), int(n * 0.62)):
                folha.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{clipe[1][:5]} {clipe[2][:4]} {t:.1f}s"], 20, 17))
        out[nome] = {"quadros": n, "composicao_media_s": round(float(np.mean(tempos)), 2), "composicao_max_s": round(float(np.max(tempos)), 2),
                     "energia_media_por_fase": {f: round(float(np.mean(v)), 4) for f, v in energia.items()},
                     "energia_pico": round(float(max(max(v) for v in energia.values())), 4),
                     "cobertura_max_rosto_estampa": cob, "flashes": SG.analisar_flashes(lums, FPS)}
        if contatos:
            out[nome]["raio_ponta_mao_erro_px_max"] = round(max(c[0] for c in contatos), 2)
            if clipe[2] == "moderado":
                out[nome]["raio_ponta_alvo_erro_px_max"] = round(max(c[1] for c in contatos), 2)
            out[nome]["redesenhos_por_segundo"] = sorted({len(v) for v in sementes.values()})
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:500], flush=True)
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "E8_quadros.jpg"), np.vstack([np.hstack(folha[i:i + 4]) for i in range(0, 12, 4)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    ordem = {}
    for p in ("eletricidade", "terra"):
        pk = [out[f"{p}_{i}"]["energia_pico"] for i in ("discreto", "moderado", "extremo")]
        ordem[p] = {"picos": pk, "discreto_menor_que_moderado_menor_que_extremo": bool(pk[0] < pk[1] < pk[2])}
    out["_ordem_intensidades"] = ordem; out["_flashes_video_inteiro"] = SG.analisar_flashes(lums_total, FPS)
    return out


def poder_eletrico(ef):
    return ef.nome == "eletricidade"


# ------------------------------------------------------------------ E8-4
def _lab(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]); c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]); x, y, z = M @ c / np.array([0.95047, 1.0, 1.08883])
    f = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return np.array([116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))])


def t_cor():
    from efeitos.poderes import eletricidade as EL, terra as TE
    cam = _lab(CAMISETA); out = {}
    for nome, h in (("eletricidade_halo", EL.HALO), ("eletricidade_nucleo", EL.NUCLEO), ("terra", "#8a5a3a"),
                    ("terra_rocha", "#%02x%02x%02x" % tuple(int(v * 255) for v in TE.ROCHA)), ("poeira", "#%02x%02x%02x" % tuple(int(v * 255) for v in TE.POEIRA))):
        out[nome] = {"cor": h, "delta_E_camiseta": round(float(np.linalg.norm(_lab(h) - cam)), 1)}
    out["regra"] = "ΔE > 25: cor bem diferente da camiseta (a partir de ~10 já se distingue)"
    return out


# ------------------------------------------------------------------ E8-7 / 8 / 9
def t_heitor_terra_det(PL):
    out = {}
    # paleta do Heitor no meio da eletricidade discreta (arcos pelo corpo ativos)
    clipe = CLIPES[0]; ef, P, A, alvo = criar(clipe, PL); mesa = MesaMedida([ef], fps=FPS); k = int(1.6 * FPS)
    for kk in range(k):
        pose, _ = pose_poder(P, ef, kk / FPS, alvo); mesa.preparar(P, {}, kk / FPS, kk, {"pe_mundo": PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
    t = k / FPS; pose, rosto = pose_poder(P, ef, t, alvo)
    mesa.preparar(P, {}, t, k, {"pe_mundo": PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
    sem = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=dict(T1.GRADE, exposicao=T1.EXPOSICAO["manha"], vinheta=0.0, grao=0.0),
                   personagem=desenhista(mesa, pose, rosto), profundidade_personagem=mesa.ctx.placa(PE)[2], efeitos=mesa)
    s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0); desenhista(mesa, pose, rosto)(cv, lambda x, y, z: P.projetar_ponto(x, y, z))
    so = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2; so = so[y0:y0 + H, x0:x0 + W]; occ = P.ultima_oclusao[y0:y0 + H, x0:x0 + W]
    fr = mesa.ultima_frente; cobf = (fr["rgba"][..., 3] + fr["add"].max(axis=2))[y0:y0 + H, x0:x0 + W] if fr is not None else np.zeros((H, W))
    m = (so[..., 3] == 255) & (occ < 0.01) & (cobf < 0.004); cob = (so[..., 3] == 255) & (cobf >= 0.004)
    dif = np.abs(sem.astype(int) - so[..., :3].astype(int)).max(axis=2)[m]
    out["paleta_heitor"] = {"pixels_sem_efeito_na_frente": int(m.sum()), "identicos_pct": round(100 * float((dif == 0).mean()), 2),
                            "pixels_do_heitor_com_arco_na_frente": int(cob.sum())}
    # terra: a face de cima do pedaço (sem levantar) é o próprio fundo
    clipe = CLIPES[4]; ef, P, A, alvo = criar(clipe, PL); ctx = Contexto(P, {}, 0.0); ef.preparar(ctx); tela = Tela(P.W, P.H); erros = []
    cam_pos = np.asarray(P.m["intrinsecos"]["pos"], float); fz = fundo(P, "manha")
    for qd in ef.pedacos:
        ef._desenhar_pedaco(ctx, tela, qd, qd["c"], np.zeros(3), 1.0, cam_pos)
    if not tela.vazio():
        a = tela.rgba[..., 3]; mm = a > 0.98
        cor = tela.rgba[..., :3][mm] / a[mm][:, None]; erros = np.abs(cor - fz[mm]).mean(axis=1) * 255
    out["terra_face_de_cima_igual_ao_fundo"] = {"pixels": int(len(erros)), "erro_medio_8bit": round(float(np.mean(erros)), 2) if len(erros) else None,
                                                "obs": "pedaço parado no lugar: a textura recortada tem de bater com o fundo (interpolação da homografia)"}
    g = [ef._crescimento(t) for t in np.linspace(0, ef.fases.duracao, 200)]
    out["terra_rachadura_cresce_sem_voltar"] = bool(np.all(np.diff(g) >= -1e-9)); out["terra_pedacos"] = len(ef.pedacos)
    # determinismo
    clipe = CLIPES[2]; quadros = []
    for _ in range(2):
        ef, P, A, alvo = criar(clipe, PL); mesa = Mesa([ef], fps=FPS); img = None
        for kk in range(int(1.9 * FPS) + 1):
            if kk == int(1.9 * FPS):
                img, _, _ = quadro(P, A, mesa, ef, alvo, kk / FPS, kk, "noite")
            else:
                pose, _ = pose_poder(P, ef, kk / FPS, alvo); mesa.preparar(P, {}, kk / FPS, kk, {"pe_mundo": PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
        quadros.append(hashlib.sha256(img.tobytes()).hexdigest())
    out["mesmo_quadro_duas_vezes_identico"] = quadros[0] == quadros[1]
    return out


def t_integridade():
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    return {"assinatura_rig_identidade_skill": hashlib.sha256(ls.encode()).hexdigest(), "alteracoes_pendentes_nesses_caminhos": dif or "nenhuma",
            "verificar_f1_vistas_ok": f1.count("| OK |")}


def previa(PL, saida):
    """Quadros-chave de cada clipe (para conferir antes do vídeo)."""
    ims = []
    for clipe in CLIPES:
        ef, P, A, alvo = criar(clipe, PL); mesa = Mesa([ef], fps=FPS); hor = clipe[3]
        alvos = [int(ef.fases.inicio_de("uso") * FPS + 6), int(ef.fases.inicio_de("impacto") * FPS + 4), int(ef.fases.inicio_de("dissipacao") * FPS + 6)]
        for k in range(max(alvos) + 1):
            if k in alvos:
                img, _, _ = quadro(P, A, mesa, ef, alvo, k / FPS, k, hor)
                ims.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{clipe[0]} q{k}"], 20, 16))
            else:
                pose, _ = pose_poder(P, ef, k / FPS, alvo); mesa.preparar(P, {}, k / FPS, k, {"pe_mundo": PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
    cv2.imwrite(saida, np.vstack([np.hstack(ims[i:i + 9]) for i in range(0, len(ims), 9)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == "__main__":
    so = sys.argv[1:]
    if so and so[0] == "previa":
        previa(placas(), so[1]); sys.exit(0)
    caminho = OUT / "e8_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())

    def rodar(nome, f, *a):
        if so and nome not in so:
            return
        t = time.time(); res[nome] = f(*a)
        if isinstance(res[nome], dict):
            res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False)[:900], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    rodar("E8_4_cor", t_cor)
    if not so or {"E8_1_video", "E8_7_heitor_terra_det"} & set(so):
        PL = placas()
        rodar("E8_7_heitor_terra_det", t_heitor_terra_det, PL)
        rodar("E8_1_video", t_video, PL)
    rodar("E8_10_integridade", t_integridade)
