"""EXTENSÃO X2 (APROVADA em 26/11/2026) — VOO: poses de voo, corpo inclinado e roupa e cabelo ao vento.

NÃO altera o rig v2 (só usa a API pública: pose_base, esqueleto, desenhar, MAOS, EXPRESSOES, ik2, misturar).
Três partes:
1. POSES DE VOO — só DADOS de pose (ângulos dentro dos limites do modelo.json; cotovelo pela regra do gestos.py):
   agachar (antecipação), impulso, pairar, cruzeiro, curva, pousar. Perfil e frente/costas.
2. CORPO INCLINADO — o desenho inteiro gira em torno da pelve (transformação do canvas FORA do rig): no cruzeiro
   o corpo fica quase horizontal, na curva ele se inclina. A estampa gira junto, sem espelhar (ID-002/ID-003).
3. VENTO — uma camada desenhada ATRÁS do Heitor: mechas de cabelo, barra da camiseta abrindo, ondas nas laterais
   e nas mangas. Só cores da paleta oficial e o mesmo contorno. Como fica atrás, o desenho original do rig não é
   coberto em nenhum pixel: o vento só aparece onde passa da silhueta.
"""
import copy, math, sys
from pathlib import Path
import numpy as np
import skia

AQUI = Path(__file__).resolve().parent
RIG = AQUI.parents[1] / "rig_v2" / "codigo"
if str(RIG) not in sys.path:
    sys.path.insert(0, str(RIG))
import heitor_v2 as HV          # noqa: E402
import animacao as AN           # noqa: E402

C = HV.C; LW = HV.LW
ALT_PELVE = HV._ALT_PELVE        # pelve: 1,72 H do chão na pose de pé
LIMITES = {"coxa": (-100, 60), "canela": (-5, 150), "pe": (-40, 40), "mao": (-70, 70)}   # convenção das poses (ver PROPOSTA)


# ------------------------------------------------------------------ 1. poses
def _pernas_plantadas(p, desce):
    """Perfil: a pelve desce 'desce' H e os pés ficam no chão (IK do próprio rig)."""
    L = HV.LAYOUT["perfil"]; pel = ALT_PELVE - desce
    for s, dx in (("d", 0.08), ("e", 0.0)):
        qx = L[f"coxa_{s}"][0]
        a1, a2, _, _ = AN.ik2(qx, -(pel - 0.02), qx + dx, -AN.ALT_TORNOZELO, AN.L_COXA, AN.L_CANELA, joelho=1)
        p[f"coxa_{s}"] = a1; p[f"canela_{s}"] = a2 - a1; p[f"pe_{s}"] = -a2
    p["raiz"] = [0.0, desce]


def _perfil(nome, t):
    p = HV.pose_base("perfil"); s = math.sin(2 * math.pi * t / 1.6); s2 = math.sin(2 * math.pi * t / 1.6 - 1.0)
    if nome == "agachar":           # antecipação da decolagem: pelve desce, tronco para a frente, braços para trás
        _pernas_plantadas(p, 0.34)
        p.update(tronco=16.0, cabeca=-12.0, braco_d=42.0, antebraco_d=-18.0, braco_e=34.0, antebraco_e=-14.0, mao_d=10.0, mao_e=10.0)
    elif nome == "impulso":         # saída do chão: corpo esticado, punho para cima, pontas dos pés
        p.update(tronco=-2.0, cabeca=-14.0, braco_d=-148.0, antebraco_d=-8.0, braco_e=14.0, antebraco_e=-8.0,
                 coxa_d=2.0, canela_d=6.0, pe_d=38.0, coxa_e=6.0, canela_e=10.0, pe_e=36.0)
        p["dedos_d"] = copy.deepcopy(HV.MAOS["punho"])
    elif nome == "pairar":          # parado no ar: pernas soltas (uma dobrada), braços um pouco abertos, sobe e desce
        p.update(tronco=-3.0, cabeca=2.0 * s2, braco_d=-18.0 + 4 * s, antebraco_d=-24.0, mao_d=12.0, braco_e=12.0 - 4 * s, antebraco_e=-20.0,
                 coxa_d=-16.0 + 4 * s2, canela_d=30.0 - 5 * s2, pe_d=34.0, coxa_e=4.0 - 3 * s2, canela_e=14.0 + 4 * s2, pe_e=30.0)
        p["raiz"] = [0.0, 0.035 * s]
    elif nome == "cruzeiro":        # voo reto (usar com inclinação ~72°): punho à frente, outro braço junto ao corpo
        p.update(tronco=0.0, cabeca=-56.0 + 2 * s, braco_d=-150.0, antebraco_d=0.0, mao_d=0.0, braco_e=10.0, antebraco_e=-6.0,
                 coxa_d=4.0 + 2 * s2, canela_d=8.0, pe_d=38.0, coxa_e=14.0 - 2 * s2, canela_e=48.0 + 6 * s2, pe_e=34.0)
        p["dedos_d"] = copy.deepcopy(HV.MAOS["punho"])
    elif nome == "pousar":          # aproximação do pouso (inclinação ~ −8°): pernas à frente, braços equilibrando
        p.update(tronco=-6.0, cabeca=10.0, braco_d=-74.0, antebraco_d=-16.0, mao_d=-10.0, braco_e=34.0, antebraco_e=-22.0,
                 coxa_d=-34.0, canela_d=30.0, pe_d=8.0, coxa_e=-20.0, canela_e=40.0, pe_e=12.0)
        p["dedos_d"] = copy.deepcopy(HV.MAOS["aberta"])
    else:
        raise KeyError(nome)
    return p


def _frente(nome, t, vista):
    p = HV.pose_base(vista); s = math.sin(2 * math.pi * t / 1.6); s2 = math.sin(2 * math.pi * t / 1.6 - 1.0)
    fora = 1 if vista == "frente" else -1      # + = ponta do braço direito vai para fora (lado esquerdo da tela, na frente)
    if nome == "pairar":
        p.update(braco_d=fora * (20.0 + 3 * s), antebraco_d=fora * 10.0, braco_e=-fora * (20.0 + 3 * s), antebraco_e=-fora * 10.0,
                 coxa_d=fora * 4.0, coxa_e=-fora * 3.0, esc_coxa_e=0.84 + 0.04 * s2, esc_canela_e=0.92, cabeca=1.5 * s2, tronco=1.0 * s)
        p["_prof_e"] = 0.05 * fora; p["raiz"] = [0.0, 0.035 * s]
    elif nome == "impulso":
        p.update(braco_d=fora * 170.0, antebraco_d=0.0, braco_e=-fora * 16.0, antebraco_e=-fora * 6.0, cabeca=0.0)
        p["dedos_d"] = copy.deepcopy(HV.MAOS["punho"])
    elif nome == "curva":           # inclinação lateral (usar com inclinação ±22°): braços abertos
        p.update(braco_d=fora * (62.0 + 3 * s), antebraco_d=fora * 8.0, braco_e=-fora * (62.0 - 3 * s), antebraco_e=-fora * 8.0,
                 coxa_d=fora * 3.0, coxa_e=-fora * 5.0, esc_coxa_d=0.9, esc_canela_d=0.86, cabeca=0.0)
        p["dedos_d"] = copy.deepcopy(HV.MAOS["aberta"]); p["dedos_e"] = copy.deepcopy(HV.MAOS["aberta"])
    else:
        raise KeyError(nome)
    return p


POSES = {"perfil": ("agachar", "impulso", "pairar", "cruzeiro", "pousar"), "frente": ("pairar", "impulso", "curva"),
         "costas": ("pairar", "impulso", "curva")}
INCLINACAO = {"agachar": 0.0, "impulso": 0.0, "pairar": 0.0, "cruzeiro": 72.0, "pousar": -8.0, "curva": 22.0}


def pose_voo(nome, vista="perfil", t=0.0):
    """Pose de voo (dict do rig) no instante t (s); as poses 'pairar' e 'cruzeiro' respiram/oscilam com t."""
    return _perfil(nome, t) if vista == "perfil" else _frente(nome, t, vista)


def transicao(pa, pb, k):
    """Mistura de duas poses (0 → pa, 1 → pb), com o misturador de camadas do próprio rig."""
    return AN.misturar(pa, [(pb, max(0.0, min(1.0, k)), None)])


def altura_pelve(pose):
    """Altura da pelve sobre o chão (H) nesta pose — para posicionar o Heitor quando ele está de pé ou agachado."""
    return ALT_PELVE - pose["raiz"][1]


# ------------------------------------------------------------------ 3. vento (camada atrás)
def _ruido(semente, k):
    return math.sin(12.9898 * (k + 1) + 78.233 * (semente + 1)) * 0.5 + 0.5


def _linear_inv(c):
    m = c.getTotalMatrix(); A = np.array([[m.getScaleX(), m.getSkewX()], [m.getSkewY(), m.getScaleY()]], float)
    return np.linalg.inv(A)


def _dir_local(c, vento):
    """Direção do vento (tela) no sistema do osso atual do canvas; e intensidade 0–1."""
    v = np.asarray(vento, float); I = float(min(1.0, np.linalg.norm(v)))
    if I < 1e-6:
        return np.array([0.0, 1.0]), 0.0
    d = _linear_inv(c) @ (v / np.linalg.norm(v)); return d / (np.linalg.norm(d) + 1e-12), I


def _fita(pts, larg, fechar_base=True):
    """Polígono de uma fita ao longo de uma linha central 'pts' (N×2) com largura 'larg' (N)."""
    pts = np.asarray(pts, float); t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
    n = np.stack([-t[:, 1], t[:, 0]], 1); a = pts + n * larg[:, None] / 2; b = pts - n * larg[:, None] / 2
    p = skia.Path(); p.moveTo(*a[0])
    for q in a[1:]:
        p.lineTo(*q)
    for q in b[::-1]:
        p.lineTo(*q)
    p.close(); return p


def _pintar(c, forma, cor, cor_s, sombra_lado=None):
    c.drawPath(forma, HV.tinta(cor))
    if sombra_lado is not None:
        c.save(); c.clipPath(forma, doAntiAlias=True); c.drawPath(sombra_lado, HV.tinta(cor_s)); c.restore()
    c.drawPath(forma, HV.contorno())


def _mechas(c, vista, vento, t, semente):
    w, I = _dir_local(c, vento)
    if I < 0.05:
        return
    hy, R = -0.58, 0.5
    cand = []
    for k in range(48):
        ph = 2 * math.pi * k / 48; n = np.array([math.cos(ph), math.sin(ph)]); p = np.array([0.0, hy]) + R * n
        regiao = p[1] < hy + 0.12 or (vista == "perfil" and p[0] < -0.1 and p[1] < hy + 0.3) or vista == "costas"
        if regiao:
            cand.append((float(n @ w), ph))
    cand.sort(reverse=True); escolhidas = []
    for d, ph in cand:      # 4 mechas no lado de onde o ar sai, espaçadas ≥ 22°
        if d < -0.2:
            break
        if all(abs((ph - q + math.pi) % (2 * math.pi) - math.pi) > math.radians(22) for q in escolhidas):
            escolhidas.append(ph)
        if len(escolhidas) == 4:
            break
    f = 1.6 + 3.0 * I
    for j, ph in enumerate(sorted(escolhidas)):
        n = np.array([math.cos(ph), math.sin(ph)]); raiz = np.array([0.0, hy]) + 0.78 * R * n
        d0 = 0.35 * n + w; d0 /= np.linalg.norm(d0); perp = np.array([-d0[1], d0[0]])
        Lm = (0.16 + 0.26 * I) * (0.8 + 0.4 * _ruido(semente, j))
        u = np.linspace(0, 1, 14)
        onda = 0.05 * I * u ** 1.5 * np.sin(2 * math.pi * (f * t - 1.3 * u) + 6.28 * _ruido(semente, j + 9))
        pts = raiz[None] + d0[None] * (Lm * u)[:, None] + perp[None] * onda[:, None]
        larg = 0.12 * (1 - u) ** 0.8 + 0.004
        forma = _fita(pts, larg)
        lado = _fita(pts + perp[None] * 0.03, larg * 0.5)
        _pintar(c, forma, C["cabelo"], C["cabelo_s"], lado)


def _borda_ondulada(a, b, saida, amp, k_ondas, fase, n=24):
    """Polígono entre o segmento a→b e uma borda ondulada deslocada para 'saida' (vetor) com amplitude variável."""
    u = np.linspace(0, 1, n); base = a[None] + (b - a)[None] * u[:, None]
    desloc = (amp(u) * (0.65 + 0.35 * np.sin(2 * math.pi * k_ondas * u - fase)))[:, None] * saida[None]
    p = skia.Path(); p.moveTo(*base[0])
    for q in (base + desloc):
        p.lineTo(*q)
    p.lineTo(*base[-1]); p.close(); return p


def _camiseta(c, vista, vento, t, semente, so_barra=False):
    w, I = _dir_local(c, vento)
    if I < 0.05:
        return
    f = 2.0 + 4.0 * I; fase = 2 * math.pi * f * t
    lados = {"frente": (-0.42, 0.42, 0.47), "costas": (-0.42, 0.42, 0.47), "tres_quartos": (-0.36, 0.35, 0.41), "perfil": (-0.21, 0.23, 0.27)}[vista]
    xa, xb, xm = lados; topo = HV.OMBRO_Y - 0.1
    # barra abrindo: aba que sai da barra na direção do vento (só quando o ar corre do ombro para a barra)
    ao_longo = max(0.0, float(w[1]))
    abre = (0.06 + 0.10 * I) * ao_longo     # ≤ 0,16 H: termina dentro do cós do jeans
    dirb = np.array([w[0] * 0.8, max(0.35, w[1])]); dirb /= np.linalg.norm(dirb)
    u = np.linspace(0, 1, 28); xs = xa + (xb - xa) * u; base = np.stack([xs, np.full_like(xs, -0.02)], 1)
    flare = (u - 0.5) * 2 * (0.05 + 0.12 * I) * ao_longo   # mais larga que o quadril: aparece dos dois lados
    env = 0.25 + 0.75 * np.sqrt(np.sin(math.pi * u))          # cantos arredondados (sem pontas)
    borda = base + dirb[None] * (abre * env * (0.75 + 0.25 * np.sin(2 * math.pi * 3 * u - fase + 6.28 * _ruido(semente, 3))))[:, None]
    borda[:, 0] += flare * np.sqrt(np.sin(math.pi * np.clip(u, 0.08, 0.92)))
    p = skia.Path(); p.moveTo(*base[0])
    for q in borda:
        p.lineTo(*q)
    p.lineTo(*base[-1]); p.close()
    sombra = skia.Path(); sombra.addRect(skia.Rect.MakeLTRB(-2, 0.02 + abre * 0.45, 2, 2))
    if abre > 0.03:
        _pintar(c, p, C["camisa"], C["camisa_s"], sombra)
    if so_barra:
        return
    # laterais: ondas que correm na direção do vento, mais fortes perto da barra e do lado de onde o ar sai
    meio = {"frente": (-0.45, 0.45), "costas": (-0.45, 0.45), "tres_quartos": (-0.40, 0.38), "perfil": (-0.24, 0.265)}[vista]
    for sx, x_hem, x_meio in ((-1, xa, meio[0]), (1, xb, meio[1])):   # ancorada NA borda da silhueta do rig
        n_out = np.array([sx, 0.0]); a = np.array([x_meio, topo + 0.3]); b = np.array([x_hem, -0.04])
        ganho = 0.5 + max(0.0, float(n_out @ w))
        amp = lambda uu, g=ganho: 0.09 * I * g * (0.3 + 0.7 * uu) * np.clip(5 * (1 - uu), 0, 1) * np.clip(6 * uu, 0, 1)   # some nas pontas
        forma = _borda_ondulada(a, b, n_out, amp, 2.5, fase * (1 if w[1] >= 0 else -1) + sx)
        _pintar(c, forma, C["camisa"], C["camisa_s"])


def _manga(c, vento, t, semente, distante):
    w, I = _dir_local(c, vento)
    if I < 0.05:
        return
    I = I * max(0.0, float(w[1]))          # a manga só abre quando o ar sai pela abertura dela
    if I < 0.08:
        return
    fase = 2 * math.pi * (2.0 + 4.0 * I) * t + 6.28 * _ruido(semente, 5)
    dirm = np.array([w[0], w[1]]); dirm /= np.linalg.norm(dirm)
    u = np.linspace(0, 1, 14); xs = -0.13 + 0.26 * u; base = np.stack([xs, np.full_like(xs, 0.16)], 1)
    borda = base + dirm[None] * ((0.04 + 0.08 * I) * (0.7 + 0.3 * np.sin(2 * math.pi * 2 * u - fase)))[:, None]
    borda[:, 0] += (u - 0.5) * 2 * (0.03 + 0.06 * I)
    p = skia.Path(); p.moveTo(*base[0])
    for q in borda:
        p.lineTo(*q)
    p.lineTo(*base[-1]); p.close()
    cor = C["camisa_s"] if distante else C["camisa"]
    _pintar(c, p, cor, C["camisa_s"])


def desenhar_vento(c, M, vista, vento, t, semente):
    """Só a camada de vento (no sistema já escalado do personagem)."""
    def no_osso(m, f):
        c.save(); c.concat(m); f(); c.restore()
    for item in HV.ORDEM[vista]:
        nome = item.rstrip("*"); dist = item.endswith("*")
        if nome.startswith("braco_"):
            no_osso(M[nome], lambda: _manga(c, vento, t, semente + (1 if nome.endswith("e") else 2), dist))
    no_osso(M["tronco"], lambda: _camiseta(c, vista, vento, t, semente))
    no_osso(M["cabeca"], lambda: _mechas(c, vista, vento, t, semente))


# ------------------------------------------------------------------ 2. desenho com o corpo inclinado
def desenhar(c, x_pelve, y_pelve, altura_px, vista="perfil", direcao=1, pose=None, rosto=None, luz=-1,
             inclinacao=0.0, vento=(0.0, 0.0), t=0.0, semente=0, so_vento=False, sem_vento=False):
    """Desenha o Heitor em voo. (x_pelve, y_pelve): pelve na tela (centro da rotação).
    inclinacao: graus, + = cabeça para o lado em que ele olha (direcao). vento: direção do ar em relação ao Heitor
    (tela; módulo 0–1 = intensidade), ou seja, o contrário da velocidade. Retorna as matrizes do esqueleto (mundo H)."""
    pose = pose or HV.pose_base(vista); u = altura_px / 4.0
    c.save(); c.translate(x_pelve, y_pelve); c.rotate(inclinacao * direcao)
    y_pe = ALT_PELVE * u
    if not sem_vento:
        c.save(); c.translate(0, y_pe); c.scale(u * direcao, u)
        desenhar_vento(c, HV.esqueleto(pose, vista), vista, vento, t, semente)
        c.restore()
    M = None if so_vento else HV.desenhar(c, 0.0, y_pe, altura_px, vista=vista, direcao=direcao, pose=pose, rosto=rosto, luz=luz)
    if not sem_vento and not so_vento:     # a barra solta passa POR CIMA do cós do jeans (como a camiseta de verdade)
        c.save(); c.translate(0, y_pe); c.scale(u * direcao, u)
        c.clipPath(regiao_sobre_quadril(M, vista), doAntiAlias=True); c.concat(M["tronco"])
        _camiseta(c, vista, vento, t, semente, so_barra=True)
        c.restore()
    c.restore()
    return M


def regiao_sobre_quadril(M, vista):
    """Onde a barra solta pode passar por cima do desenho: só o bloco do quadril (jeans), abaixo da linha da barra,
    MENOS braços, antebraços e mãos (nunca cobre pele, mãos, camiseta, estampa ou rosto)."""
    w = {"frente": 0.40, "costas": 0.40, "tres_quartos": 0.36, "perfil": 0.24}[vista]
    q = skia.Path(); q.addRect(skia.Rect.MakeLTRB(-w - 0.01, 0.006, w + 0.01, 0.2)); q.transform(M["raiz"])
    tira = skia.Path(); ordem = [i.rstrip("*") for i in HV.ORDEM[vista]]
    for s_ in ("d", "e"):
        if ordem.index(f"braco_{s_}") < ordem.index("quadril"):     # braço desenhado ANTES do quadril fica atrás dele
            continue
        for osso, forma in ((f"braco_{s_}", HV.forma_braco()), (f"antebraco_{s_}", HV.forma_antebraco())):
            f_ = skia.Path(forma); f_.transform(M[osso]); tira = skia.Op(tira, f_, skia.PathOp.kUnion_PathOp) or tira
        m_ = skia.Path(); m_.addCircle(0, 0.13, 0.26); m_.transform(M[f"mao_{s_}"]); tira = skia.Op(tira, m_, skia.PathOp.kUnion_PathOp) or tira
        mg = skia.Path(); mg.addRect(skia.Rect.MakeLTRB(-0.16, -0.12, 0.16, 0.28)); mg.transform(M[f"braco_{s_}"]); tira = skia.Op(tira, mg, skia.PathOp.kUnion_PathOp) or tira
    return skia.Op(q, tira, skia.PathOp.kDifference_PathOp) or q


def pelve_na_tela(x_pe, y_pe, altura_px, pose):
    """Para quem posiciona pelos pés (de pé/agachado): a pelve fica acima dos pés por altura_pelve(pose)."""
    return x_pe, y_pe - altura_pelve(pose) * altura_px / 4.0


def limites(pose, vista):
    """Lista de violações (junta, valor, faixa) — convenção das poses: coxa + = para trás; canela + = flexão do joelho."""
    import gestos as G
    fora = []
    for s in ("d", "e"):
        if vista == "perfil":
            for j in ("coxa", "canela", "pe"):
                lo, hi = LIMITES[j]; v = pose[f"{j}_{s}"]
                if not lo <= v <= hi:
                    fora.append((f"{j}_{s}", round(v, 1), (lo, hi)))
        lo, hi = LIMITES["mao"]; v = pose[f"mao_{s}"]
        if not lo <= v <= hi:
            fora.append((f"mao_{s}", round(v, 1), (lo, hi)))
        inv, _, rel = G.cotovelo_invertido(pose, vista, s)
        if inv or not -150 <= rel <= 150:
            fora.append((f"cotovelo_{s}", round(rel, 1), "regra anatômica (gestos.cotovelo_invertido)"))
    return fora
