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


def _lerp(a, b, k):
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
        pose[f"braco_{lado}"] = a1 - tr - ba
        pose[f"antebraco_{lado}"] = a2 - a1
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
    for sg in (1, -1):                       # o sentido da dobra do cotovelo que a vista permite
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
