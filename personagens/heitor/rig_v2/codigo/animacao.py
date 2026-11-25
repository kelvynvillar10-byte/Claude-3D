#!/usr/bin/env python3
"""Heitor rig v2 — sistema de animação corporal (fase F2).

- ik2(): IK analítica de 2 ossos (coxa+canela ou braço+antebraço), com o joelho para a frente.
- Ciclo de CAMINHADA e de CORRIDA procedurais, definidos em coordenadas de mundo (H):
  o pé de apoio fica PLANTADO no chão (não desliza); o pé em balanço segue um arco; a pelve sobe/desce;
  braço oposto à perna; rolagem do pé (calcanhar → ponta).
- Vista de perfil: IK real. Frente/costas: os mesmos dados do perfil projetados com ESCORÇO
  (o osso encurta quando aponta para a câmera) + balanço lateral do quadril.
- Camadas: combinar uma pose base (ex.: caminhada) com sobreposições parciais com peso e máscara.
- Rosto: piscada automática e respiração.

Convenção de ângulo (igual ao heitor_v2): 0° = osso apontando para baixo; positivo = ponta vai para −x (tela).
"""
import copy, math
import heitor_v2 as H

L_COXA, L_CANELA = H.OSS["coxa"], H.OSS["canela"]
ALT_TORNOZELO = H.PROP["tornozelo"]   # 0,22 H do chão


def ang_osso(dx, dy):
    """Ângulo absoluto (graus) de um osso cuja direção é (dx, dy) em coordenadas de tela (y para baixo)."""
    return math.degrees(math.atan2(-dx, dy))


def ik2(hx, hy, tx, ty, l1, l2, joelho=1):
    """IK de 2 ossos. Retorna (ang_abs_1, ang_abs_2, (jx, jy), erro). joelho=+1 → junta do meio para +x."""
    dx, dy = tx - hx, ty - hy
    d = math.hypot(dx, dy); dmax = (l1 + l2) * 0.9995
    dd = min(max(d, abs(l1 - l2) + 1e-4), dmax)
    phi = math.atan2(dy, dx)
    alfa = math.acos(max(-1.0, min(1.0, (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd))))
    th = phi - joelho * alfa
    jx, jy = hx + l1 * math.cos(th), hy + l1 * math.sin(th)
    ex, ey = hx + dx / d * dd, hy + dy / d * dd
    a1 = ang_osso(jx - hx, jy - hy); a2 = ang_osso(ex - jx, ey - jy)
    return a1, a2, (jx, jy), math.hypot(ex - tx, ey - ty)


def suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ parâmetros dos ciclos
CAMINHADA = dict(T=0.86, v=1.80, apoio=0.62, levante=0.16, bob=0.035, desce=0.10, braco=22.0, antebraco=(-12, -26),
                 tronco=3.0, cabeca=-1.5, chute=0.0, rolagem=24.0)
CORRIDA = dict(T=0.56, v=4.00, apoio=0.38, levante=0.46, bob=0.04, desce=0.21, braco=42.0, antebraco=(-92, -100),
               tronco=12.0, cabeca=-6.0, chute=0.3, rolagem=30.0)


def _pe_ciclo(t, fase0, P, quadril_x):
    """Posição do tornozelo (mundo, H, y para cima a partir do chão) e ângulo do pé, para uma perna."""
    T, v, sf = P["T"], P["v"], P["apoio"]
    passada = v * T
    ph = (t / T + fase0) % 1.0
    t0 = t - ph * T                                   # instante do último contato
    xc = v * t0 + passada * sf / 2 + quadril_x        # o pé toca o chão à frente do quadril
    if ph < sf:   # APOIO: pé plantado
        x = xc; s = ph / sf
        ang = 0.0; y = ALT_TORNOZELO
        if s > 0.72:   # calcanhar sobe (rolagem até a ponta): o tornozelo sobe para a ponta ficar no chão
            r = suave((s - 0.72) / 0.28); ang = P["rolagem"] * r; y += 0.30 * math.sin(math.radians(ang))
        elif s < 0.1:  # contato de calcanhar: ponta ainda levantada
            ang = -10 * (1 - s / 0.1)
        return x, y, ang, True, ph
    s = (ph - sf) / (1 - sf)   # BALANÇO
    prog = suave(s) if P["chute"] == 0 else suave(s ** (1 + P["chute"]))   # na corrida o pé fica atrás e sobe (chute)
    x = xc + passada * prog
    # o balanço parte da altura em que o apoio terminou (calcanhar já levantado) — sem salto entre quadros
    y_saida = 0.30 * math.sin(math.radians(P["rolagem"])) * (1 - suave(s / 0.4))
    y = ALT_TORNOZELO + y_saida + P["levante"] * math.sin(math.pi * s) ** (1.0 if P["chute"] == 0 else 0.8)
    ang = P["rolagem"] * (1 - suave(s / 0.35)) if s < 0.35 else -10 * suave((s - 0.6) / 0.4)
    return x, y, ang, False, ph


def pose_locomocao(t, vista="perfil", tipo="caminhada"):
    """Pose do esqueleto no instante t (s) + diagnóstico (alvos, erros de IK, apoio)."""
    P = CAMINHADA if tipo == "caminhada" else CORRIDA
    p = H.pose_base(vista)
    T, sf = P["T"], P["apoio"]
    ph_d = (t / T) % 1.0
    # pelve: caminhada → mais baixa no contato duplo; corrida → mais baixa no meio do apoio
    if tipo == "caminhada":
        bob = -P["bob"] * 0.5 * math.cos(4 * math.pi * ph_d)
    else:
        bob = -P["bob"] * math.cos(4 * math.pi * (ph_d - sf / 2))
    pelve_y = H.PROP["barra_camisa"] - P["desce"] + bob      # altura da pelve (H, para cima)
    X = P["v"] * t                                            # pelve avança no mundo
    diag = {"pelve_x": X, "pelve_y": pelve_y, "pernas": {}}
    L = H.LAYOUT["perfil"]
    for s, f0 in (("d", 0.0), ("e", 0.5)):
        qx = L[f"coxa_{s}"][0]
        ax, ay, pang, apoio, ph = _pe_ciclo(t, f0, P, qx)
        # IK no plano do perfil (tela: y para baixo)
        hx, hy = X + qx, -(pelve_y - 0.02)
        a1, a2, joelho, erro = ik2(hx, hy, ax, -ay, L_COXA, L_CANELA, joelho=1)
        diag["pernas"][s] = {"alvo": (ax, ay), "apoio": apoio, "erro_ik": erro, "fase": ph, "coxa_abs": a1, "canela_abs": a2}
        if vista == "perfil":
            p[f"coxa_{s}"] = a1; p[f"canela_{s}"] = a2 - a1; p[f"pe_{s}"] = pang - a2
        else:   # frente/costas: projeção com escorço (mesma altura do tornozelo que no perfil)
            p[f"coxa_{s}"] = 0.0; p[f"canela_{s}"] = 0.0; p[f"pe_{s}"] = 0.0
            p[f"esc_coxa_{s}"] = max(0.35, math.cos(math.radians(a1)))
            p[f"esc_canela_{s}"] = max(0.35, math.cos(math.radians(a2)))
            # pé à frente (mais perto da câmera na frente) aparece um pouco mais baixo; nas costas, mais alto
            prof = (ax - X) * (0.13 if vista == "frente" else -0.13)
            p[f"_prof_{s}"] = prof
    # braços opostos às pernas
    for s, sinal in (("d", 1), ("e", -1)):
        sw = P["braco"] * math.cos(2 * math.pi * ph_d) * sinal   # +: para trás; braço direito atrás quando a perna direita está à frente
        frente = max(0.0, -sw / P["braco"])
        anteb = P["antebraco"][0] + (P["antebraco"][1] - P["antebraco"][0]) * frente
        if vista == "perfil":
            p[f"braco_{s}"] = sw; p[f"antebraco_{s}"] = anteb
        else:
            # na frente/costas o braço que vai para a frente cruza um pouco para o meio do corpo (e o que vai para trás abre)
            lado_tela = (1 if s == "d" else -1) * (1 if vista == "frente" else -1)   # +1 = braço do lado esquerdo da tela
            p[f"braco_{s}"] = lado_tela * (2.0 - 9.0 * (sw / P["braco"]) * (-1 if vista == "frente" else 1))
            p[f"esc_braco_{s}"] = max(0.5, math.cos(math.radians(sw)))
            p[f"esc_antebraco_{s}"] = max(0.4, math.cos(math.radians(sw + anteb)))
            p[f"antebraco_{s}"] = 0.0
        if tipo == "corrida":
            p[f"dedos_{s}"] = copy.deepcopy(H.MAOS["segurar"])
    p["tronco"] = P["tronco"] if vista == "perfil" else 0.0
    p["cabeca"] = P["cabeca"] if vista == "perfil" else 0.0
    # pelve: posição relativa (o desenho acompanha a pelve; o mundo anda por baixo)
    p["raiz"] = [0.0, -(pelve_y - H.PROP["barra_camisa"])]
    if vista != "perfil":   # balanço lateral do quadril para o lado do pé de apoio + leve inclinação
        lado = math.sin(2 * math.pi * ph_d) * (1 if vista == "frente" else -1)
        p["raiz"][0] = 0.05 * lado; p["tronco"] = -2.5 * lado; p["cabeca"] = 2.0 * lado
    return p, diag


# ------------------------------------------------------------------ camadas e rosto
ANGULOS = [k for k in H.pose_base("frente") if not k.startswith(("dedos_", "mao_vista", "raiz"))]


def misturar(base, camadas):
    """camadas: lista de (pose_parcial, peso 0–1, mascara: lista de chaves ou None=todas as presentes)."""
    out = copy.deepcopy(base)
    for parcial, peso, mascara in camadas:
        for k, v in parcial.items():
            if mascara is not None and k not in mascara:
                continue
            if isinstance(v, (int, float)) and isinstance(out.get(k), (int, float)):
                out[k] = out[k] * (1 - peso) + v * peso
            elif peso >= 0.5:
                out[k] = copy.deepcopy(v)
    return out


def piscada(t, periodo=3.4, dur=0.12, deslocamento=0.7):
    """Retorna fechamento da pálpebra 0–1 (piscada automática, 3–4 quadros)."""
    x = (t + deslocamento) % periodo
    if x < dur:
        return math.sin(math.pi * x / dur)
    return 0.0


def rosto_com_piscada(nome, t):
    e = copy.deepcopy(H.EXPRESSOES[nome])
    pf = piscada(t)
    if pf > 0:
        e["palp_sup"] = max(e["palp_sup"], pf if pf < 0.9 else 1.0)
    return e
