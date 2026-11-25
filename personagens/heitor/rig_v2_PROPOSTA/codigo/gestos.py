#!/usr/bin/env python3
"""Heitor rig v2 (PROPOSTA) — gestos e mãos animadas (fase F3).

- Clipe de quadros-chave por canal, com curvas: linear, suave (ease-in-out), saida (ease-out),
  volta (ease-out com overshoot: antecipação/assentamento).
- Interpola números, poses de mão (dedo a dedo, junta a junta) e EXPRESSÕES (transição suave dos parâmetros).
- ik_braco(): braço + antebraço(+mão) alcançam um ponto (apontar, pegar).
- Objeto: preso ao ENCAIXE da mão enquanto segurado; ao soltar, cai com gravidade e quica no chão.
"""
import copy, math
import heitor_v2 as H
import animacao as A


def curva(x, tipo="suave"):
    x = min(1.0, max(0.0, x))
    if tipo == "linear":
        return x
    if tipo == "saida":
        return 1 - (1 - x) ** 3
    if tipo == "entrada":
        return x ** 3
    if tipo == "volta":   # ease-out com overshoot (~10 %)
        c1 = 1.70158; c3 = c1 + 1
        return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    return x * x * (3 - 2 * x)


def mistura_expr(a, b, k):
    """Transição entre duas expressões (k: 0 → a, 1 → b).
    - Parâmetros contínuos (pálpebras, sobrancelhas, olhar, abertura, sorriso, largura) interpolam.
    - Troca de DESENHO de boca (ex.: 'linha' → 'o'): a boca de origem quase fecha, troca no meio e a nova abre —
      a troca acontece com a boca pequena, sem "pulo".
    - Troca de ESTILO de olho (pequeno escuro ↔ arregalado branco): escondida por uma piscada (fechado no meio)."""
    out = {}
    for key, va in a.items():
        vb = b.get(key, va)
        if key in ("boca", "abertura", "dentes", "branco"):
            continue
        if key == "sobr_e":
            va = va if va is not None else a["sobr"]; vb = vb if vb is not None else b["sobr"]
        out[key] = _lerp(va, vb, k)
    if a["boca"] == b["boca"]:
        out["boca"] = a["boca"]; out["abertura"] = _lerp(a["abertura"], b["abertura"], k)
        out["dentes"] = a["dentes"] if k < 0.5 else b["dentes"]
    else:
        meio = min(a["abertura"], b["abertura"]) * 0.3
        if k < 0.5:
            out.update(boca=a["boca"], abertura=_lerp(a["abertura"], meio, k * 2), dentes=a["dentes"])
        else:
            out.update(boca=b["boca"], abertura=_lerp(meio, b["abertura"], k * 2 - 1), dentes=b["dentes"])
    out["branco"] = a["branco"] if k < 0.5 else b["branco"]
    if a["branco"] != b["branco"]:   # fechado em k 0,30–0,70 (cobre a troca em 0,5 mesmo com passos grandes por quadro)
        pisc = min(1.0, max(0.0, (0.42 - abs(k - 0.5)) / 0.22))
        out["palp_sup"] = max(out["palp_sup"], pisc)
        out["_piscada_troca"] = pisc > 0
    return out


def _lerp(a, b, k):
    if isinstance(a, dict) and isinstance(b, dict) and "boca" in a and "boca" in b:
        return mistura_expr(a, b, k)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * k
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return [_lerp(x, y, k) for x, y in zip(a, b)]
    if isinstance(a, dict) and isinstance(b, dict):
        return {key: _lerp(a[key], b.get(key, a[key]), k) if key in b else a[key] for key in a}
    return b if k >= 0.5 else a


class Clipe:
    """canais: {nome: [(t, valor, curva_ate_aqui), ...]} — valor pode ser número, lista, pose de mão (dict) ou expressão (dict)."""

    def __init__(self, canais):
        self.canais = {k: sorted(v, key=lambda x: x[0]) for k, v in canais.items()}

    def valor(self, canal, t):
        ks = self.canais[canal]
        if t <= ks[0][0]:
            return copy.deepcopy(ks[0][1])
        for (t0, v0, _), (t1, v1, cv) in zip(ks, ks[1:]):
            if t <= t1:
                return _lerp(v0, v1, curva((t - t0) / max(1e-6, t1 - t0), cv))
        return copy.deepcopy(ks[-1][1])

    def aplicar(self, pose, t):
        for k in self.canais:
            if k == "rosto":
                continue
            pose[k] = self.valor(k, t)
        return pose


def expr(nome):
    return copy.deepcopy(H.EXPRESSOES[nome])


def mao(nome):
    return copy.deepcopy(H.MAOS[nome])


def ik_braco(pose, vista, lado, alvo, cotovelo=1, iter=4):
    """cotovelo=None: escolhe automaticamente a solução anatômica (cotovelo para fora, nunca invertido)."""
    if cotovelo is None:
        sols = []
        for cv in (1, -1):
            p = copy.deepcopy(pose); e = _ik_braco(p, vista, lado, alvo, cv, iter)
            inv = cotovelo_invertido(p, vista, lado)[0]
            M = H.esqueleto(p, vista); ex = M[f"antebraco_{lado}"].mapXY(0, 0).x()
            lateral = -ex * (lado_tela(vista, lado) if vista != "perfil" else 0)
            if vista == "perfil":   # perfil: a solução com flexão para a frente (antebraço relativo <= 0)
                lateral = -p[f"antebraco_{lado}"]
            sols.append((inv, -lateral, e, cv))
        cv = sorted(sols)[0][3]
        return _ik_braco(pose, vista, lado, alvo, cv, iter)
    return _ik_braco(pose, vista, lado, alvo, cotovelo, iter)


def _ik_braco(pose, vista, lado, alvo, cotovelo=1, iter=4):
    """Ajusta braco_/antebraco_/mao_ para o ENCAIXE da mão chegar a 'alvo' (mundo, H; y para baixo, origem nos pés).
    Antebraço + mão tratados como um segmento rígido (mão reta, mao_=0). O encaixe não fica no eixo do antebraço
    (na vista de lado ele está deslocado para a palma), então a IK analítica é refinada por correção do alvo,
    medindo o encaixe REAL pelo esqueleto. Retorna o erro final (H) medido pelo esqueleto."""
    M = H.esqueleto(pose, vista)
    o = M[f"braco_{lado}"].mapXY(0, 0)
    l1 = H.OSS["braco"]; ex, ey = H.ENCAIXE[pose.get(f"mao_vista_{lado}") or H.VISTA_MAO[vista]]
    l2 = math.hypot(ex, H.OSS["antebraco"] + ey)
    tr = pose["tronco"]; ba = H.LAYOUT[vista][f"braco_{lado}"][1]
    tx, ty = alvo
    for _ in range(iter):
        a1, a2, _, _ = A.ik2(o.x(), o.y(), tx, ty, l1, l2, joelho=cotovelo)
        pose[f"braco_{lado}"] = _ang(a1 - tr - ba)
        pose[f"antebraco_{lado}"] = _ang(a2 - a1)
        pose[f"mao_{lado}"] = 0.0
        sx, sy = encaixe_mundo(pose, vista, lado)
        tx += alvo[0] - sx; ty += alvo[1] - sy
    sx, sy = encaixe_mundo(pose, vista, lado)
    return math.hypot(alvo[0] - sx, alvo[1] - sy)


def encaixe_mundo(pose, vista, lado):
    M = H.esqueleto(pose, vista)
    ex, ey = H.ENCAIXE[pose.get(f"mao_vista_{lado}") or H.VISTA_MAO[vista]]
    p = M[f"mao_{lado}"].mapXY(ex, ey)
    return p.x(), p.y()


class Objeto:
    """Bola simples (desenho próprio). Segurada: segue o encaixe. Solta: gravidade + quique + atrito."""
    G = 30.0   # H/s² (≈ 9,8 m/s² com H ≈ 0,35 m, levemente exagerado para leitura de animação)

    def __init__(self, x, y, raio=0.095, cor=0xFFE8722C):
        self.x, self.y, self.r, self.cor = x, y, raio, cor
        self.vx = self.vy = 0.0; self.segurado = False; self.hist = []

    def passo(self, dt, chao_y=0.0, apoio=None):
        if self.segurado:
            return
        self.vy += self.G * dt
        self.x += self.vx * dt; self.y += self.vy * dt
        lim = chao_y - self.r
        if apoio and apoio[0] <= self.x <= apoio[1] and self.y > apoio[2] - self.r and self.y - self.vy * dt <= apoio[2] - self.r:
            lim = apoio[2] - self.r
        if self.y > lim:
            self.y = lim
            self.vy = -self.vy * 0.5 if abs(self.vy) > 0.6 else 0.0
            self.vx *= 0.8

    def desenhar(self, c, x, y, escala=1.0):
        r = self.r * escala
        c.drawCircle(x, y, r, H.tinta(self.cor))
        H.sombra(c, _circ(x, y, r), 0xFFB8551C, 1, 0.3)
        c.drawCircle(x - r * 0.35, y - r * 0.35, r * 0.25, H.tinta(0x66FFFFFF))
        c.drawCircle(x, y, r, H.contorno())


def _circ(x, y, r):
    import skia
    p = skia.Path(); p.addCircle(x, y, r); return p


def mira_braco(pose, vista, lado, alvo, dobra=8.0, iter=8):
    """APONTAR: braço quase reto (cotovelo levemente dobrado, 'dobra' graus) com o eixo da mão (e do indicador)
    mirando 'alvo' — diferente de ik_braco, que leva a mão ATÉ o alvo. Resolve o ângulo do ombro pelo método da
    secante, medindo o eixo real da mão pelo esqueleto (vale para vistas espelhadas). Retorna o erro final (graus)."""
    def aplicar(b, sg):
        pose[f"braco_{lado}"] = b; pose[f"antebraco_{lado}"] = sg * dobra; pose[f"mao_{lado}"] = 0.0
        return erro_mira(pose, vista, lado, alvo)
    melhor = None
    for sg in (sentido_flexao(vista, lado),):   # dobra só no sentido anatômico (ver regra do cotovelo abaixo)
        for b0 in (-90.0, 90.0, 0.0, 180.0):   # vários pontos de partida (evita o ramo errado)
            x0, x1 = b0, b0 + 10.0; f0, f1 = aplicar(x0, sg), aplicar(x1, sg)
            for _ in range(iter):
                if abs(f1 - f0) < 1e-9:
                    break
                x0, x1, f0 = x1, x1 - f1 * (x1 - x0) / (f1 - f0), f1
                f1 = aplicar(x1, sg)
            if melhor is None or abs(f1) < abs(melhor[0]) - 1e-6:
                melhor = (f1, x1, sg)
    aplicar(melhor[1], melhor[2])
    return abs(melhor[0])


def erro_mira(pose, vista, lado, alvo):
    """Ângulo (graus, com sinal na convenção dos ossos) entre o eixo da mão e a direção punho → alvo."""
    M = H.esqueleto(pose, vista)
    p0 = M[f"mao_{lado}"].mapXY(0, 0); p1 = M[f"mao_{lado}"].mapXY(0, 1)
    eixo = A.ang_osso(p1.x() - p0.x(), p1.y() - p0.y()); dirc = A.ang_osso(alvo[0] - p0.x(), alvo[1] - p0.y())
    return (dirc - eixo + 180) % 360 - 180


# ------------------------------------------------------------------ regra anatômica do cotovelo
# O cotovelo só dobra para o lado da flexão (limite do modelo: cotovelo 0–150°). Em 2D isso vira:
# - perfil (personagem virado para +x; a vista espelhada usa os mesmos valores): o antebraço vai para a FRENTE,
#   ou seja, ângulo relativo do antebraço <= 0 (tolerância de 5°).
# - frente/costas/3-4: o úmero pode girar, então os dois sentidos são possíveis com o braço ABAIXO da horizontal
#   (mão na barriga ou mão para fora). Com o braço ACIMA da horizontal, o antebraço só pode dobrar para CIMA,
#   em direção à cabeça (aceno, "mãos ao alto", punho erguido); dobrar para fora/baixo deixaria o cotovelo
#   apontando para a cabeça — articulação invertida.
TOL_COTOVELO = 5.0


def lado_tela(vista, lado):
    """+1 se o ombro desse braço fica no lado esquerdo da tela (x < 0), −1 se no direito."""
    return 1 if H.LAYOUT[vista][f"braco_{lado}"][0] < 0 else -1


def sentido_flexao(vista, lado, braco_abs=0.0):
    """Sinal do ângulo relativo do antebraço que corresponde a FLEXÃO (dobra anatômica) nesta vista."""
    if vista == "perfil":
        return -1
    return lado_tela(vista, lado)   # braço erguido: dobra em direção à cabeça


def _ang(a):
    """Normaliza um ângulo para (−180°, 180°]."""
    return (a + 180.0) % 360.0 - 180.0 if (a + 180.0) % 360.0 != 0 else 180.0


def cotovelo_invertido(pose, vista, lado):
    """Retorna (invertido?, ângulo absoluto do braço, ângulo relativo do antebraço) — ângulos normalizados.
    Perfil: o antebraço só dobra para a frente (relativo <= +5°).
    Frente/costas/3-4 (geometria real do esqueleto): o cotovelo está INVERTIDO quando está acima do ombro e a dobra
    aponta para a cabeça (o "bico" do cotovelo vira para dentro). Abaixo do ombro os dois sentidos são possíveis
    (mão na barriga; "não sei" com os antebraços para fora), porque o úmero gira."""
    rel = _ang(pose[f"antebraco_{lado}"])
    ab = _ang(pose[f"braco_{lado}"] + H.LAYOUT[vista][f"braco_{lado}"][1] + pose.get("tronco", 0.0))
    if vista == "perfil":
        return rel > TOL_COTOVELO, ab, rel
    if abs(rel) <= TOL_COTOVELO:
        return False, ab, rel
    M = H.esqueleto(pose, vista)
    S = M[f"braco_{lado}"].mapXY(0, 0); E = M[f"antebraco_{lado}"].mapXY(0, 0); P = M[f"mao_{lado}"].mapXY(0, 0)
    C = M["cabeca"].mapXY(0, -0.58)
    lx, ly = P.x() - S.x(), P.y() - S.y(); L = math.hypot(lx, ly) or 1e-9
    ex, ey = E.x() - S.x(), E.y() - S.y()
    k = (ex * lx + ey * ly) / (L * L)
    nx, ny = ex - k * lx, ey - k * ly                     # para onde o "bico" do cotovelo aponta
    acima = E.y() < S.y() - 0.02
    para_cabeca = nx * (C.x() - S.x()) + ny * (C.y() - S.y()) > 0
    return (acima and para_cabeca), ab, rel