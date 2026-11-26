#!/usr/bin/env python3
"""E7 — testes do NÚCLEO DE EFEITOS (efeitos/nucleo). Mede, não supõe.

E7-1  regressão: o compositor sem efeitos dá o MESMO quadro da E6 (assinatura guardada antes da mudança)
E7-2  fases e intensidades (gráfico + continuidade do envelope)
E7-3  partículas: determinismo por semente; queda livre, quique, arrasto (velocidade terminal) e vento × fórmula
E7-4  corda: esticamento máximo; período de pêndulo × fórmula
E7-5  curva fractal: pontas nos contatos, determinismo, redesenho a cada 2 quadros
E7-6  luz 2D: só onde há superfície (céu intacto); queda com a distância × fórmula; imagem antes/depois
E7-7  profundidade: brilho ATRÁS do hidrante fica escondido; na frente, aparece
E7-8  segurança: estrobo (7,5 flashes/s) → governador → máximo de flashes em 1 s
E7-9  proteção do rosto e da estampa: cobertura com e sem proteção
E7-10 combinação: 3 efeitos ativos → 1 dominante + 1 secundário (×0,5) + o resto suprimido
E7-11 registro: um plugin novo num arquivo novo registra sozinho
E7-12 vídeo de demonstração (8 cenas curtas) + tempo de composição por efeito
E7-13 integridade (rig v2, identidade, skill)
Saídas: cenografia/testes/e7/.
"""
import copy, hashlib, json, math, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenografia.nucleo.compositor import Placa                             # noqa: E402
from cenografia.nucleo.atmosfera import Atmosfera                          # noqa: E402
import e0_testes as T0                                                      # noqa: E402
import e1_testes as T1                                                      # noqa: E402
import e6_cena_prova as E6                                                  # noqa: E402
from efeitos.nucleo.base import Params, Fases, Mesa, Efeito, Tela, Contexto, efeito, carregar_plugins, REGISTRO, INTENSIDADES, FASES  # noqa: E402
from efeitos.nucleo import particulas as PT, curvas as CV, corda as CD, seguranca as SG, protecao as PR   # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e7"; OUT.mkdir(parents=True, exist_ok=True)
HV, AN = T0.HV, T0.AN
FPS = 30; W, H = 1080, 1920
PE = (-5.1, 6.0, 0.154)                 # Heitor parado na calçada (câmera da calçada da E6)
TOM_MANHA, TOM_NOITE = E6.PLANO["tomadas"][0], E6.PLANO["tomadas"][2]
res = {}
carregar_plugins()


def placas():
    pm, _, _ = E6.placa(TOM_MANHA); pn, _, _ = E6.placa(TOM_NOITE)
    return {"manha": pm, "noite": pn}


def personagem(t):
    pose = HV.pose_base("frente"); pose["respira"] = math.sin(2 * math.pi * t / 2.8)
    return {"pe_mundo": PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1}


def desenhista(mesa, t):
    pc = mesa.ctx.personagem
    def f(cv, proj):
        u, v, z = mesa.ctx.placa(PE); ut, vt, zt = mesa.ctx.placa((PE[0], PE[1], PE[2] + 1.4))
        x, y, _ = proj(u, v, z); _, yt, _ = proj(ut, vt, zt); alt = y - yt
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
        HV.desenhar(cv, x, y, alt, vista="frente", pose=pc["pose"], rosto=AN.rosto_com_piscada("neutro", t))
    return f


def quadro(P, A, mesa, t, k, horario, cam=None, grade_extra=None):
    cam = cam or {}
    mesa.preparar(P, cam, t, k, personagem(t))
    g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[horario], **(grade_extra or {})))
    return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, cam=cam, personagem=desenhista(mesa, t), profundidade_personagem=mesa.ctx.placa(PE)[2],
                    efeitos=mesa, deslocamento_px=mesa.tremida(), semente_grao=k, ceu_extra=A.ceu(t))


# ------------------------------------------------------------------ E7-1
def t_regressao():
    ref = json.loads((OUT / "regressao_ref.json").read_text()); out = {}
    for tom in E6.PLANO["tomadas"]:
        pasta = Path(ref[tom["nome"]]["placa"])
        if not pasta.exists():
            out[tom["nome"]] = "placa antiga não está mais no cache: não verificável"; continue
        P = Placa(pasta); A = Atmosfera(P, tom["clima"], 11); img, _ = E6.quadro(P, A, tom, 2.0, 60)
        out[tom["nome"]] = {"identico_ao_de_antes_da_E7": hashlib.sha256(img.tobytes()).hexdigest() == ref[tom["nome"]]["sha256"]}
    # a placa NOVA (com a passada de albedo) também dá o mesmo quadro? (o render é determinístico; só ganhou uma saída)
    P, _, _ = E6.placa(E6.PLANO["tomadas"][0]); A = Atmosfera(P, "limpo", 11); img, _ = E6.quadro(P, A, E6.PLANO["tomadas"][0], 2.0, 60)
    out["placa_nova_com_albedo_mesmo_quadro"] = hashlib.sha256(img.tobytes()).hexdigest() == ref["manha_frente"]["sha256"]
    out["placa_nova_tem_albedo"] = all(P.camadas[c].get("albedo") is not None for c in P.camadas if c != "ceu")
    return out


# ------------------------------------------------------------------ E7-2
def t_fases():
    F = Fases(3.0); ts = np.linspace(0, 3.0, 3001); env = np.array([F.envelope(t) for t in ts])
    saltos = np.abs(np.diff(env)); W2, H2 = 1600, 700; s = skia.Surface(W2, H2); cv = s.getCanvas(); cv.clear(skia.Color(20, 22, 30))
    cores = [(70, 90, 160), (60, 130, 170), (60, 150, 110), (190, 120, 60), (150, 90, 150), (90, 90, 110)]
    fonte = skia.Font(T0.NUN, 22); branco = skia.Paint(Color=skia.ColorWHITE, AntiAlias=True)
    x0, x1, y0, y1 = 80, 1540, 620, 80; ymax = 2.6
    X = lambda t: x0 + (x1 - x0) * t / 3.0; Y = lambda v: y0 - (y0 - y1) * v / ymax
    for (f, a, b), c in zip(F.limites, cores):
        cv.drawRect(skia.Rect.MakeLTRB(X(a), y1, X(b), y0), skia.Paint(Color=skia.ColorSetARGB(70, *c)))
        cv.drawString(f, X(a) + 6, y0 + 32 if f != "encerramento" else y0 + 60, fonte, branco)
    for nome, fat, cor in (("discreto", INTENSIDADES["discreto"], (150, 200, 255)), ("moderado", 1.0, (255, 220, 120)), ("extremo", INTENSIDADES["extremo"], (255, 120, 90))):
        path = skia.Path(); path.moveTo(X(0), Y(0))
        for t, e in zip(ts[::10], env[::10]):
            path.lineTo(X(t), Y(e * fat))
        cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4, Color=skia.Color(*cor)))
        cv.drawString(nome, x1 - 160, Y(fat * 1.35) - 6, fonte, skia.Paint(Color=skia.Color(*cor), AntiAlias=True))
    cv.drawString("E7 · fases de todo efeito (envelope × intensidade) — 3 s", 80, 50, skia.Font(T0.NUN, 28), branco)
    cv2.imwrite(str(OUT / "E7_fases.png"), s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., [2, 1, 0]])
    return {"limites_s": {f: [round(a, 3), round(b, 3)] for f, a, b in F.limites}, "pico_impacto": round(float(env.max()), 3),
            "maior_salto_entre_amostras_de_1ms": round(float(saltos.max()), 4), "intensidades": INTENSIDADES,
            "envelope_comeca_e_termina_em_zero": bool(env[0] == 0 and abs(env[-1]) < 1e-9)}


# ------------------------------------------------------------------ E7-3
def t_particulas():
    def sim(semente, n=40, passos=60):
        s = PT.Sistema(semente, gravidade=1.0, arrasto=0.3, turbulencia=0.5, chao_z=0.0)
        s.emitir(n, (0, 0, 1), (1, 0, 2), dispersao=1.0, vida=(5, 6))
        for _ in range(passos):
            s.passo()
        return s.pos.copy()
    a, b, c = sim(7), sim(7), sim(8)
    # queda livre (sem arrasto) por 1 s, a partir do repouso a 10 m
    s = PT.Sistema(1, gravidade=1.0); s.emitir(1, (0, 0, 10), (0, 0, 0), dispersao=0.0, vida=(9, 9))
    for _ in range(30):
        s.passo()
    z_med, z_teo = float(s.pos[0, 2]), 10 - 0.5 * 9.81
    # quique: solto de 1 m, restituição 0,5 → altura do 1º rebote ≈ 0,25 m
    s = PT.Sistema(1, gravidade=1.0, chao_z=0.0, restituicao=0.5); s.emitir(1, (0, 0, 1), (0, 0, 0), dispersao=0.0, vida=(9, 9))
    zs = []
    for _ in range(120):
        s.passo(); zs.append(float(s.pos[0, 2]))
    zs = np.array(zs); i_chao = next(i for i in range(1, len(zs) - 1) if zs[i] <= zs[i - 1] and zs[i + 1] > zs[i])   # 1º contato
    rebote = float(zs[i_chao:i_chao + 25].max())
    # arrasto: velocidade terminal = g/k
    s = PT.Sistema(1, gravidade=1.0, arrasto=2.0); s.emitir(1, (0, 0, 100), (0, 0, 0), dispersao=0.0, vida=(99, 99))
    for _ in range(150):
        s.passo()
    v_term, v_teo = float(-s.vel[0, 2]), 9.81 / 2.0
    # vento: com arrasto, a velocidade horizontal tende à do vento
    s = PT.Sistema(1, gravidade=0.0, arrasto=2.0, vento=(1.5, 0, 0)); s.emitir(1, (0, 0, 0), (0, 0, 0), dispersao=0.0, vida=(99, 99))
    for _ in range(150):
        s.passo()
    return {"mesma_semente_identico": bool(np.array_equal(a, b)), "outra_semente_diferente": bool(not np.array_equal(a, c)),
            "queda_livre_1s": {"medido_m": round(z_med, 4), "formula_m": round(z_teo, 4), "erro_cm": round(abs(z_med - z_teo) * 100, 2)},
            "quique_restituicao_0_5": {"rebote_m": round(rebote, 3), "esperado_m": 0.25},
            "arrasto_velocidade_terminal": {"medido_m_s": round(v_term, 3), "formula_g_sobre_k_m_s": round(v_teo, 3)},
            "vento_1_5_m_s": {"velocidade_horizontal_m_s": round(float(s.vel[0, 0]), 3)}}


# ------------------------------------------------------------------ E7-4
def t_corda():
    c = CD.Corda((0, 0, 3), (2, 0, 3), n=24, comprimento=2.2)
    for _ in range(90):
        c.passo()
    est = c.esticamento_max()
    L = 1.0; c2 = CD.Corda((0, 0, 3), (L * math.sin(0.25), 0, 3 - L * math.cos(0.25)), n=20, comprimento=L, amortecimento=1.0, iteracoes=60)
    c2.solta_b = True; xs = []
    for _ in range(240):
        c2.passo(); xs.append(float(c2.p[-1, 0]))
    xs = np.array(xs); cruz = [i for i in range(1, len(xs)) if xs[i - 1] > 0 >= xs[i]]
    T_med = float(np.mean(np.diff(cruz))) / FPS if len(cruz) > 2 else None
    T_haste = 2 * math.pi * math.sqrt(2 * L / (3 * 9.81)); T_simples = 2 * math.pi * math.sqrt(L / 9.81)
    return {"esticamento_max_pct": round(est * 100, 3), "pendulo_1m": {"periodo_medido_s": round(T_med, 3) if T_med else None,
            "haste_uniforme_s": round(T_haste, 3), "pendulo_simples_s": round(T_simples, 3),
            "obs": "uma corda solta se comporta entre a haste uniforme (massa distribuída) e o pêndulo simples; dobra e amortece"}}


# ------------------------------------------------------------------ E7-5
def t_curva():
    a, b = np.array([0.0, 0, 1]), np.array([2.0, 1, 1.5])
    c1 = CV.fractal(a, b, np.random.default_rng(5)); c2 = CV.fractal(a, b, np.random.default_rng(5)); c3 = CV.fractal(a, b, np.random.default_rng(6))
    princ = c1[0][0]
    k_seeds = [(k, k // 2) for k in range(6)]
    return {"ponta_inicial_erro_m": float(np.linalg.norm(princ[0] - a)), "ponta_final_erro_m": float(np.linalg.norm(princ[-1] - b)),
            "pontos_na_principal": len(princ), "ramos": len(c1) - 1, "mesma_semente_identica": bool(np.array_equal(c1[0][0], c2[0][0])),
            "outra_semente_diferente": bool(not np.array_equal(c1[0][0], c3[0][0])),
            "redesenho": "semente = base·1000 + quadro // 2 → muda a cada 2 quadros: " + ", ".join(f"q{k}→{s}" for k, s in k_seeds)}


# ------------------------------------------------------------------ E7-6
class _LuzFixa(Efeito):
    def luzes(self, ctx):
        return [{"pos": self.kw["pos"], "cor": (0.5, 0.8, 1.0), "forca": self.kw.get("forca", 3.0), "raio": 0.3}]


def t_luz2d(PL):
    P = PL["noite"]; A = Atmosfera(P, "limpo", 11); pos = (-5.6, 7.8, 0.9)
    m0 = Mesa([]); m1 = Mesa([_LuzFixa(Params(duracao=99), pos=pos)])
    a = quadro(P, A, m0, 1.0, 30, "noite", grade_extra={"grao": 0.0}); b = quadro(P, A, m1, 1.0, 30, "noite", grade_extra={"grao": 0.0})
    cv2.imwrite(str(OUT / "E7_luz2d.jpg"), np.hstack([T0._texto(a, ["sem luz do efeito"], 60, 34), T0._texto(b, ["com luz 2D do efeito", "(albedo + profundidade da placa)"], 60, 34)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    # céu intacto: compara pixels onde só há céu
    ceu = np.ones((P.H, P.W), bool)
    for c, d in P.camadas.items():
        if c != "ceu":
            ceu &= d["alfa"] < 0.01
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2; ceu = ceu[y0:y0 + H, x0:x0 + W]
    dif = np.abs(a.astype(int) - b.astype(int)).max(axis=2)
    # queda com a distância, no linear: luz extra da camada 'perto' ÷ albedo × (d² + r²) deve ser ≈ forca·cos (constante)
    X, n = P.geometria_camada("perto"); alb = P.camadas["perto"]["albedo"]; ex = P.luz_extra("perto", m1.efeitos[0].luzes(None))
    d = np.asarray(pos, np.float32)[None, None, :] - X; d2 = (d * d).sum(2); cosl = np.maximum(0, (n * d).sum(2) / np.sqrt(d2))
    ok = (P.camadas["perto"]["alfa"] > 0.5) & (alb.mean(2) > 0.05) & (cosl > 0.2)
    k = (ex.mean(2) / np.maximum(alb.mean(2), 1e-6) * (d2 + 0.09) / np.maximum(cosl, 1e-6))[ok]
    prox = (d2[ok] < 4); longe = (d2[ok] > 9)
    return {"pixels_de_ceu_alterados": int((dif[ceu] > 0).sum()), "pixels_de_ceu": int(ceu.sum()),
            "pixels_alterados_no_quadro_pct": round(100 * float((dif > 2).mean()), 1),
            "forca_recuperada_perto_menos_de_2m": round(float(np.median(k[prox])), 3) if prox.any() else None,
            "forca_recuperada_longe_mais_de_3m": round(float(np.median(k[longe])), 3) if longe.any() else None, "forca_usada": 3.0}


# ------------------------------------------------------------------ E7-7
class _Pontos(Efeito):
    def desenhar(self, ctx, onde, tela):
        if onde == "atras":
            for p in self.kw["pontos"]:
                x, y, s, z = ctx.tela(p); tela.mancha(x, y, 0.12 * ctx.px_por_m(z), (1.0, 0.9, 0.5), 1.0, z, "add")


def t_profundidade(PL):
    P = PL["manha"]; ctx = Contexto(P, {}, 0, 0)
    atras, frente = (-4.3, 7.4, 0.55), (-4.3, 5.9, 0.55)          # o hidrante está em (−4,3; 6,6)
    out = {}
    for nome, pt in (("atras_do_hidrante", atras), ("na_frente_do_hidrante", frente)):
        m = Mesa([_Pontos(Params(duracao=99), pontos=[pt])]); m.preparar(P, {}, 0.5, 15, None)
        P._pilha(P.m["camadas"], Atmosfera(P, "limpo", 11).pesos(), {}, None, frontal=True); zf = P.ultima_prof_frontal
        cam_ = m.desenhar(P, {}, "atras"); x, y, _, z = ctx.tela(pt); r = int(0.12 * ctx.px_por_m(z))
        jan = (slice(int(y) - r, int(y) + r), slice(int(x) - r, int(x) + r))
        vis = (cam_["z"][jan] <= zf[jan] + 0.15) & (cam_["add"][jan].max(2) > 0.05); tot = cam_["add"][jan].max(2) > 0.05
        out[nome] = {"visivel_pct": round(100 * float(vis.sum() / max(tot.sum(), 1)), 1)}
    return out


# ------------------------------------------------------------------ E7-8
def t_seguranca(PL):
    P = PL["noite"]; A = Atmosfera(P, "limpo", 11); out = {}
    for nome, lim in (("sem_governador", 1000), ("com_governador", 3)):
        ef = REGISTRO["demo_estrobo"](Params(duracao=3.0), pos=(-5.4, 7.0, 1.4)); m = Mesa([ef], limite_flashes=lim); lums = []
        for k in range(90):
            img = quadro(P, A, m, k / FPS, k, "noite", grade_extra={"grao": 0.0})
            lums.append(SG.luminancia_relativa(cv2.resize(img, (135, 240), interpolation=cv2.INTER_AREA)))
        out[nome] = SG.analisar_flashes(lums, FPS, area=0.05)
    out["limite_por_segundo"] = 3; out["obs"] = "área mínima reduzida para 5 % da tela (mais rigoroso que os 25 % da regra) para este teste"
    return out


# ------------------------------------------------------------------ E7-9
class _Brilho(Efeito):
    def desenhar(self, ctx, onde, tela):
        if onde == "frente":
            from efeitos.nucleo import contatos as CT
            x, y, z = CT.rig(ctx, "cabeca"); tela.mancha(x, y + 0.6 * abs(ctx.personagem["pe_tela"][1] - ctx.personagem["topo_tela"][1]) * 0.25, 160, (1.0, 0.95, 0.8), 1.0, z - 0.2, "add")
            tela.mancha(x, y, 120, (0.9, 0.9, 1.0), 0.9, z - 0.2, "alpha")


def t_protecao(PL):
    P = PL["manha"]; out = {}
    for nome, prot in (("sem_protecao", False), ("com_protecao", True)):
        m = Mesa([_Brilho(Params(duracao=99))], protecao=prot); m.preparar(P, {}, 1.0, 30, personagem(1.0))
        out[nome] = PR.cobertura(m.desenhar(P, {}, "frente"), m.ctx)
    out["limite"] = PR.LIMITE
    return out


# ------------------------------------------------------------------ E7-10 / E7-11
def t_combinacao(PL):
    P = PL["manha"]
    efs = [REGISTRO["demo_faiscas"](Params(intensidade="extremo", duracao=3)), REGISTRO["demo_poeira"](Params(duracao=3), origem=(-5, 7.5, 0.16)),
           REGISTRO["demo_calor"](Params(intensidade="discreto", duracao=3), origem=(-4.3, 9, 0.3))]
    m = Mesa(efs); m.preparar(P, {}, 1.0, 30, personagem(1.0))
    return {"ganhos": {e.nome: round(e.ganho, 3) for e in efs}, "registro_suprimidos": m.registro[:1]}


def t_registro():
    antes = sorted(REGISTRO)
    with tempfile.TemporaryDirectory() as d:
        Path(d, "poder_de_teste.py").write_text("from efeitos.nucleo.base import Efeito, efeito\n@efeito('poder_de_teste')\nclass X(Efeito):\n    pass\n")
        import efeitos.poderes as pod
        pod.__path__.append(d); carregar_plugins(); pod.__path__.remove(d)
    depois = sorted(REGISTRO); novo = sorted(set(depois) - set(antes)); REGISTRO.pop("poder_de_teste", None)
    return {"plugins_do_nucleo": antes, "novo_arquivo_registrou": novo}


# ------------------------------------------------------------------ E7-12: vídeo de demonstração
CENAS = [
    ("faíscas (partículas, gravidade, quique, luz 2D)", "manha", "demo_faiscas", dict(cor="#ffb347", duracao=2.8, direcao=(0.7, -0.6, 0.0)), {}),
    ("arco fractal mão ↔ fachada (redesenho a cada 2 quadros)", "manha", "demo_arco", dict(cor="#b9a7ff", duracao=2.8), {"alvo": (-6.85, 8.2, 1.9)}),
    ("poeira (cobre; atrás e na frente conforme a profundidade)", "manha", "demo_poeira", dict(cor="#cdb48c", duracao=2.8), {"origem": (-5.0, 7.0, 0.16)}),
    ("calor (distorção) + fumaça", "manha", "demo_calor", dict(duracao=2.8), {"origem": (-4.4, 8.8, 0.25)}),
    ("corda com física (presa na fachada; a mão solta no impacto)", "manha", "demo_corda", dict(cor="#f2efe8", duracao=3.2), {"ancora": (-6.85, 7.4, 3.4)}),
    ("onda de choque + tremida + rachadura + quadro de impacto", "manha", "demo_onda", dict(duracao=2.8), {"origem": (-4.9, 8.2, 0.16)}),
    ("orbe de luz à noite (luz 2D no cenário + rastro)", "noite", "demo_orbe", dict(cor="#7fd4ff", duracao=3.2), {"centro": (-5.3, 8.6, 1.5), "raio": 1.5}),
    ("combinação: faíscas (dominante) + orbe (secundário ×0,5)", "noite", None, None, {}),
]


def t_video(PL):
    atm = {k: Atmosfera(P, "limpo", 11) for k, P in PL.items()}
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "25", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E7_nucleo_efeitos.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); tempos = {}; folha = []; q = 0
    for rot, hor, nome, prm, kw in CENAS:
        if nome is None:
            efs = [REGISTRO["demo_faiscas"](Params(cor="#ffb347", duracao=3.0, direcao=(0.7, -0.6, 0.0), intensidade="extremo")),
                   REGISTRO["demo_orbe"](Params(cor="#7fd4ff", duracao=3.0), centro=(-5.3, 8.6, 1.5), raio=1.5)]
            dur = 3.0
        else:
            efs = [REGISTRO[nome](Params(**prm), **kw)]; dur = efs[0].fases.duracao
        mesa = Mesa(efs, fps=FPS); P, A = PL[hor], atm[hor]; n = int(dur * FPS); ts = []
        for k in range(n):
            t = k / FPS; cam = {"tz": 0.35 * (k / n) ** 1.2}; t0 = time.time()
            img = quadro(P, A, mesa, t, q, hor, cam=cam); ts.append(time.time() - t0)
            fase = mesa.efeitos[0].fases.em(t)[0] or "—"
            img = T0._texto(img, ["E7 · núcleo de efeitos (demonstração, não é poder)", rot, f"fase: {fase}"], 1745, 25)
            img = T0._marca(img); pr.stdin.write(np.ascontiguousarray(img).tobytes()); q += 1
            if k == int(n * 0.55):
                folha.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [rot.split(" (")[0][:26]], 20, 17))
        tempos[nome or "combinacao"] = {"media_s": round(float(np.mean(ts)), 2), "max_s": round(float(np.max(ts)), 2), "quadros": n}
        print(nome, tempos[nome or "combinacao"], flush=True)
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "E7_cenas.jpg"), np.vstack([np.hstack(folha[:4]), np.hstack(folha[4:])])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return {"quadros": q, "duracao_s": round(q / FPS, 1), "composicao_por_efeito": tempos}


# ------------------------------------------------------------------ E7-13
def t_integridade():
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    return {"assinatura_rig_identidade_skill": hashlib.sha256(ls.encode()).hexdigest(), "alteracoes_pendentes_nesses_caminhos": dif or "nenhuma",
            "verificar_f1_vistas_ok": f1.count("| OK |")}


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e7_metricas.json"
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
    rodar("E7_1_regressao", t_regressao)
    rodar("E7_2_fases", t_fases)
    rodar("E7_3_particulas", t_particulas)
    rodar("E7_4_corda", t_corda)
    rodar("E7_5_curva", t_curva)
    rodar("E7_11_registro", t_registro)
    precisa = {"E7_6_luz2d", "E7_7_profundidade", "E7_8_seguranca", "E7_9_protecao", "E7_10_combinacao", "E7_12_video"}
    if not so or precisa & set(so):
        PL = placas()
        rodar("E7_6_luz2d", t_luz2d, PL)
        rodar("E7_7_profundidade", t_profundidade, PL)
        rodar("E7_9_protecao", t_protecao, PL)
        rodar("E7_10_combinacao", t_combinacao, PL)
        rodar("E7_8_seguranca", t_seguranca, PL)
        rodar("E7_12_video", t_video, PL)
    rodar("E7_13_integridade", t_integridade)
