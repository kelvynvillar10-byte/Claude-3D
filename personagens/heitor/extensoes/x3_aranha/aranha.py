"""EXTENSÃO X3 (PROPOSTA, aguardando aprovação) — ARANHA: escalada, balanço no fio e gesto de lançar.

NÃO altera o rig v2. Usa só a API pública do rig (pose_base, esqueleto, desenhar, MAOS, ik_braco, mira_braco, ik2,
cotovelo_invertido) e a extensão X2 aprovada (corpo inclinado e roupa/cabelo ao vento, para o balanço).
Três partes:
1. ESCALADA (costas e perfil): ciclo com os 4 apoios PLANTADOS na parede (mãos e pés presos no lugar enquanto o corpo
   sobe), em pares diagonais (mão direita + pé esquerdo, depois o outro par), resolvido por IK do próprio rig.
2. BALANÇO NO FIO (perfil): pêndulo que gira em torno da MÃO que segura o fio (não da pelve); o corpo segue o fio com
   um pequeno atraso, as pernas e o braço livre reagem ao movimento, e a X2 põe o vento na roupa e no cabelo.
3. GESTO DE LANÇAR (próprio do Modo Curioso): braço estendido para o alvo com a MÃO ABERTA e a palma voltada para
   ele (empurrão). Não copia gestos de personagens de terceiros.
"""
import copy, math, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent
for p in (AQUI.parents[1] / "rig_v2" / "codigo", AQUI.parent / "x2_voo"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import heitor_v2 as HV          # noqa: E402
import animacao as AN           # noqa: E402
import gestos as GE             # noqa: E402
import voo as X2                # noqa: E402

LIM_COXA_FRENTE = (-100, 100)
PALMA = (0.0, 0.13)             # centro da palma no osso da mão (sempre sobre a mão, em qualquer vista)


def palma(pose, vista, lado):
    q = HV.esqueleto(pose, vista)[f"mao_{lado}"].mapXY(*PALMA); return q.x(), q.y()


def ik_palma(pose, vista, lado, alvo, iter=5):
    """Leva o CENTRO DA PALMA até 'alvo' (H): a IK do rig leva o encaixe; corrige o alvo pela distância medida."""
    tx, ty = alvo
    for _ in range(iter):
        GE.ik_braco(pose, vista, lado, (tx, ty), cotovelo=None); px, py = palma(pose, vista, lado)
        tx += alvo[0] - px; ty += alvo[1] - py
    px, py = palma(pose, vista, lado)
    return math.hypot(alvo[0] - px, alvo[1] - py)   # costas/frente: coxa abre para o lado (abdução, vista de trás) — ver PROPOSTA


# ------------------------------------------------------------------ IK das pernas (mesma IK de 2 ossos do rig)
def ik_perna(pose, vista, lado, alvo, joelho):
    """Leva o TORNOZELO (origem do osso do pé) até 'alvo' (H, origem nos pés, y para baixo). Retorna o erro (H)."""
    M = HV.esqueleto(pose, vista); q = M[f"coxa_{lado}"].mapXY(0, 0); ca = HV.LAYOUT[vista][f"coxa_{lado}"][1]
    a1, a2, _, _ = AN.ik2(q.x(), q.y(), alvo[0], alvo[1], AN.L_COXA, AN.L_CANELA, joelho=joelho)
    pose[f"coxa_{lado}"] = a1 - ca; pose[f"canela_{lado}"] = a2 - a1
    M = HV.esqueleto(pose, vista); t = M[f"pe_{lado}"].mapXY(0, 0)
    return math.hypot(t.x() - alvo[0], t.y() - alvo[1])


# ------------------------------------------------------------------ 1. escalada
class Escalada:
    """Ciclo de escalada. Unidades em H (altura da cabeça), y para baixo, origem = pés do Heitor no começo.
    passo: quanto cada mão/pé sobe por ciclo; periodo: s por ciclo; o corpo sobe passo/periodo H/s."""
    def __init__(self, vista="costas", passo=0.5, periodo=1.4):
        assert vista in ("costas", "perfil")
        self.vista, self.S, self.T = vista, passo, periodo; self.v = passo / periodo
        if vista == "costas":     # lado d fica em +x na vista de costas
            self.base = {"mao_d": (0.74, -3.70), "mao_e": (-0.74, -3.70), "pe_d": (0.46, -0.50), "pe_e": (-0.46, -0.50)}
            self.joelho = {"d": 1, "e": -1}
        else:                     # perfil: parede à direita (+x); mãos e pontas dos pés na parede
            self.base = {"mao_d": (0.50, -3.52), "mao_e": (0.48, -3.40), "pe_d": (0.30, -0.95), "pe_e": (0.28, -0.80)}
            self.joelho = {"d": 1, "e": 1}
        self.defasagem = {"mao_d": 0.0, "pe_e": 0.0, "mao_e": 0.5, "pe_d": 0.5}

    def origem(self, t):
        """Posição (H) da origem do esqueleto (pés de referência) no instante t: sobe em velocidade constante."""
        return np.array([0.0, -self.v * t])

    def apoio(self, nome, t):
        """Ponto (H, no plano da parede) onde está a mão/pé no instante t, e se está plantado (True) ou em movimento."""
        ph = t / self.T + self.defasagem[nome]; k = math.floor(ph); x = ph - k
        bx, by = self.base[nome]
        # pegada k (no mundo da parede): cada uma fica S acima da anterior; relativa ao corpo, vai de base−S/4 a base+S/4
        dfs = self.defasagem[nome]
        y_planta = lambda kk: by + self.S * (0.25 - (kk + 1) + dfs)
        if x >= 0.5:
            return np.array([bx, y_planta(k)]), True
        a = np.array([bx, y_planta(k - 1)]); b = np.array([bx, y_planta(k)]); s = GE.curva(x / 0.5, "suave")
        p = a + (b - a) * s
        lado = 1 if bx > 0 else -1
        if self.vista == "costas":
            p[0] += lado * 0.12 * math.sin(math.pi * s)                       # a mão/pé desencosta e faz um arco
        else:
            p[0] -= 0.14 * math.sin(math.pi * s)
        return p, False

    def pose(self, t):
        """Pose do rig (IK do rig) no instante t; mais o diagnóstico (erros de alcance em H)."""
        vista = self.vista; p = HV.pose_base(vista); o = self.origem(t)
        sw = math.sin(2 * math.pi * t / self.T)
        if vista == "costas":
            p["tronco"] = 3.0 * sw; p["raiz"] = [0.04 * sw, 0.0]; p["cabeca"] = -2.0 * sw
        else:
            p["tronco"] = -7.0 + 1.5 * sw; p["cabeca"] = -14.0; p["raiz"] = [-0.22, -0.25]
        erros = {}
        for s in ("d", "e"):
            p[f"dedos_{s}"] = copy.deepcopy(HV.MAOS["segurar"])
        for nome in ("pe_d", "pe_e", "mao_d", "mao_e"):
            alvo, _ = self.apoio(nome, t); rel = (alvo[0] - o[0], alvo[1] - o[1]); s = nome[-1]
            if nome.startswith("pe_"):
                erros[nome] = ik_perna(p, vista, s, rel, self.joelho[s])
                M = HV.esqueleto(p, vista); q0 = M[f"canela_{s}"].mapXY(0, 0); q1 = M[f"pe_{s}"].mapXY(0, 0)
                a2 = AN.ang_osso(q1.x() - q0.x(), q1.y() - q0.y())
                p[f"pe_{s}"] = -a2 if vista == "costas" else float(np.clip(-a2 - 90 + 20, -40, 40))   # perfil: ponta do pé na parede
            else:
                erros[nome] = ik_palma(p, vista, s, rel)
        return p, erros

    def desenhar(self, c, x0, y0, altura_px, t, rosto=None):
        """(x0, y0): tela dos pés do Heitor no começo da escalada. Retorna as matrizes do esqueleto e a pose."""
        p, _ = self.pose(t); u = altura_px / 4.0; o = self.origem(t)
        M = HV.desenhar(c, x0 + o[0] * u, y0 + o[1] * u, altura_px, vista=self.vista, direcao=1, pose=p, rosto=rosto)
        return M, p

    def ponto_tela(self, x0, y0, altura_px, t, nome):
        """Onde a mão (encaixe) ou o tornozelo do DESENHO está na tela — para conferir que o apoio não desliza."""
        p, _ = self.pose(t); u = altura_px / 4.0; o = self.origem(t)
        if nome.startswith("mao_"):
            qx, qy = palma(p, self.vista, nome[-1])
        else:
            q = HV.esqueleto(p, self.vista)[nome].mapXY(0, 0); qx, qy = q.x(), q.y()
        return x0 + (o[0] + qx) * u, y0 + (o[1] + qy) * u


# ------------------------------------------------------------------ 2. balanço no fio (perfil)
class Balanco:
    """Pêndulo: âncora na tela (ax, ay), comprimento L (px) do fio até a mão, amplitude (graus), período (s).
    O Heitor segura o fio com a mão ESQUERDA (o braço de trás no perfil: o rosto fica livre); o corpo gira em torno da mão."""
    def __init__(self, amplitude=38.0, periodo=2.4, atraso=0.12, direcao=1):
        self.A, self.T, self.atraso, self.dir = amplitude, periodo, atraso, direcao

    def angulo(self, t):
        """Ângulo do fio (graus; + = mão à direita da âncora) e velocidade angular (graus/s)."""
        w = 2 * math.pi / self.T
        return self.A * math.sin(w * t), self.A * w * math.cos(w * t)

    def pose(self, t):
        fi, dfi = self.angulo(t); k = max(-1.0, min(1.0, dfi / (self.A * 2 * math.pi / self.T + 1e-9)))   # −1..1 (sentido)
        p = HV.pose_base("perfil"); kk = k * self.dir
        p.update(braco_e=180.0, antebraco_e=0.0, mao_e=0.0, cabeca=-8.0 - 6.0 * kk, tronco=-4.0 * kk,
                 braco_d=-35.0 * kk + 10.0, antebraco_d=-25.0,
                 coxa_d=-28.0 - 22.0 * kk, canela_d=40.0 + 20.0 * max(0.0, kk), pe_d=25.0,
                 coxa_e=-8.0 - 26.0 * kk, canela_e=58.0 + 15.0 * max(0.0, -kk), pe_e=30.0)
        p["dedos_e"] = copy.deepcopy(HV.MAOS["segurar"]); p["dedos_d"] = copy.deepcopy(HV.MAOS["aberta"])
        return p

    def geometria(self, ax, ay, L, altura_px, t):
        """(x_ref, y_ref, inclinação, mão, pose) para voo.desenhar (X2): a mão fica exatamente no fio."""
        fi, dfi = self.angulo(t); f2, _ = self.angulo(t - self.atraso)
        mao = (ax + L * math.sin(math.radians(fi)), ay + L * math.cos(math.radians(fi)))
        inc = -f2 * self.dir                         # o corpo segue o fio com um pequeno atraso (inércia)
        p = self.pose(t); u = altura_px / 4.0
        qx, qy = GE.encaixe_mundo(p, "perfil", "e")
        ox, oy = qx * u * self.dir, X2.ALT_PELVE * u + qy * u
        th = math.radians(inc * self.dir); c, s = math.cos(th), math.sin(th)
        rx, ry = ox * c - oy * s, ox * s + oy * c
        return mao[0] - rx, mao[1] - ry, inc, mao, p

    def vento(self, ax, ay, L, altura_px, t, dt=1 / 60):
        """Vento para a X2: contra a velocidade da pelve na tela, intensidade pela velocidade em m/s (H = 0,35 m)."""
        x0, y0, *_ = self.geometria(ax, ay, L, altura_px, t); x1, y1, *_ = self.geometria(ax, ay, L, altura_px, t + dt)
        v = np.array([x1 - x0, y1 - y0]) / dt; n = np.linalg.norm(v)
        if n < 1e-6:
            return (0.0, 0.0)
        mps = n / (altura_px / 4.0) * 0.35
        return tuple(-v / n * min(1.0, mps / 5.0))

    def desenhar(self, c, ax, ay, L, altura_px, t, rosto=None):
        x, y, inc, mao, p = self.geometria(ax, ay, L, altura_px, t)
        X2.desenhar(c, x, y, altura_px, vista="perfil", direcao=self.dir, pose=p, rosto=rosto, inclinacao=inc,
                    vento=self.vento(ax, ay, L, altura_px, t), t=t)
        return mao


# ------------------------------------------------------------------ 3. gesto de lançar
def pose_lancar(pose, vista, lado, alvo_H, abertura=1.0):
    """Braço estendido para o alvo (mira_braco do rig), mão aberta, punho levemente dobrado para trás (palma para o
    alvo). abertura 0..1 mistura de 'segurar' para 'aberta'. Retorna o erro de mira (graus)."""
    erro = GE.mira_braco(pose, vista, lado, alvo_H, dobra=6.0)
    pose[f"mao_{lado}"] = -22.0 * abertura * (1 if vista == "perfil" or lado == "d" else -1)
    pose[f"dedos_{lado}"] = copy.deepcopy(HV.MAOS["aberta" if abertura >= 0.5 else "segurar"])
    if vista in ("frente", "tres_quartos") and abertura >= 0.5:
        pose[f"mao_vista_{lado}"] = "palma"                 # palma aberta à mostra (vista do próprio rig)
    return erro


def limites(pose, vista):
    """Limites das juntas (X2.limites) + abertura das coxas de frente/costas."""
    fora = X2.limites(pose, vista)
    if vista in ("frente", "costas"):
        for s in ("d", "e"):
            lo, hi = LIM_COXA_FRENTE; v = pose[f"coxa_{s}"]
            if not lo <= v <= hi:
                fora.append((f"coxa_{s}", round(v, 1), (lo, hi)))
            if not -5 <= abs(pose[f"canela_{s}"]) <= 150:
                fora.append((f"canela_{s}", round(pose[f"canela_{s}"], 1), "joelho 0–150°"))
    return fora
