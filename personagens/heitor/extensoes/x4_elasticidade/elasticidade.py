"""EXTENSÃO X4 (PROPOSTA, aguardando aprovação) — ELASTICIDADE: braços e pernas que esticam (só eles).

NÃO altera o rig v2. Usa o ESCORÇO do próprio rig (esc_antebraco_*, esc_coxa_*): o rig já sabe encurtar um osso no
próprio eixo sem achatar mão nem pé (o filho não herda a escala). Com valores MAIORES que 1, o mesmo mecanismo alonga.
Regras de identidade (medidas no teste):
- estica só o ANTEBRAÇO (o braço de cima tem a manga: fica do tamanho original) e só a COXA (a canela tem a barra
  dobrada da calça: fica do tamanho original); a mão, o tênis, a manga e a barra não mudam de tamanho nem de forma;
- a espessura do membro não muda (o rig escala só o comprimento; o contorno é desenhado depois, com traço normal);
- volta EXATAMENTE ao comprimento original (escorço 1,0) no fim, depois de uma mola amortecida.
Movimentos (próprios do Modo Curioso; nada de soco esticado nem de outros gestos de personagens de terceiros):
1. ALCANCE: a mão vai até um ponto longe (pegar, tocar), o braço estica reto, com a mola na ida e na volta;
2. PERNAS DE PAU: as coxas esticam e o Heitor fica alto, com os pés no chão; depois volta.
"""
import copy, math, sys
from pathlib import Path
import numpy as np
import skia

AQUI = Path(__file__).resolve().parent
for p in (AQUI.parents[1] / "rig_v2" / "codigo", AQUI.parent / "x2_voo", AQUI.parent / "x3_aranha"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import heitor_v2 as HV          # noqa: E402
import animacao as AN           # noqa: E402
import gestos as GE             # noqa: E402
import voo as X2                # noqa: E402
import aranha as X3             # noqa: E402

ESC_MAX_BRACO = 8.0              # antebraço até 8× (≈ 1,2 m de antebraço a mais por unidade; ~4,4 m de alcance a mais)
ESC_MAX_PERNA = 3.0              # coxa até 3× (o Heitor fica com ~2,9 m)
L_ANTEBRACO, L_COXA = HV.OSS["antebraco"], HV.OSS["coxa"]


def _ang(a):
    return GE._ang(a)


# ------------------------------------------------------------------ mola (ida e volta elástica)
def mola(t, dur_ida=0.35, segura=0.6, dur_volta=0.45):
    """0 → 1 (com passada de ~12 % e assentamento) → segura → volta a 0 (com um pequeno quique) → 0 EXATO."""
    if t <= 0:
        return 0.0
    if t < dur_ida:
        return GE.curva(t / dur_ida, "volta")
    if t < dur_ida + segura:
        x = (t - dur_ida) / segura
        return 1.0 + 0.04 * math.exp(-x * 5) * math.sin(x * 18)
    tv = t - dur_ida - segura
    if tv < dur_volta:
        x = tv / dur_volta; return max(0.0, 1.0 - GE.curva(x, "volta"))
    return 0.0


def duracao_mola(dur_ida=0.35, segura=0.6, dur_volta=0.45):
    return dur_ida + segura + dur_volta


# ------------------------------------------------------------------ 1. alcance
def alcance(pose, vista, lado, alvo_H, k=1.0, iter=6):
    """Pose com o braço esticado até o CENTRO DA PALMA chegar a 'alvo_H' (H, origem nos pés, y para baixo), braço reto.
    k (0..1, a mola): quanto do caminho já foi — mistura a pose de partida com a final, e o escorço vai de 1 ao final.
    Retorna (pose nova, erro em H da pose final, escorço final). O braço de cima só aponta (comprimento e manga originais)."""
    fin = copy.deepcopy(pose)
    M = HV.esqueleto(fin, vista); o = M[f"braco_{lado}"].mapXY(0, 0)
    dx, dy = alvo_H[0] - o.x(), alvo_H[1] - o.y()
    a_abs = AN.ang_osso(dx, dy); tr = fin["tronco"]; ba = HV.LAYOUT[vista][f"braco_{lado}"][1]
    fin[f"braco_{lado}"] = _ang(a_abs - tr - ba); fin[f"antebraco_{lado}"] = 0.0; fin[f"mao_{lado}"] = 0.0
    fin[f"dedos_{lado}"] = copy.deepcopy(HV.MAOS["aberta"])
    if vista in ("frente", "tres_quartos"):
        fin[f"mao_vista_{lado}"] = "palma"            # mão aberta de frente (vista do próprio rig), não de lado
    esc = 1.0
    for _ in range(iter):                       # só o comprimento do antebraço muda: converge pela distância ao longo do eixo
        fin[f"esc_antebraco_{lado}"] = esc; px, py = X3.palma(fin, vista, lado)
        falta = (dx * (alvo_H[0] - px) + dy * (alvo_H[1] - py)) / max(math.hypot(dx, dy), 1e-9)
        esc = max(1.0, min(ESC_MAX_BRACO, esc + falta / L_ANTEBRACO))
    fin[f"esc_antebraco_{lado}"] = esc
    px, py = X3.palma(fin, vista, lado); erro = math.hypot(alvo_H[0] - px, alvo_H[1] - py)
    k = max(0.0, k)
    if k >= 1.0 and k <= 1.0:
        return fin, erro, esc
    base = copy.deepcopy(pose); base[f"braco_{lado}"] = _ang(base[f"braco_{lado}"])
    out = X2.transicao(base, fin, min(1.0, k)) if k <= 1.0 else copy.deepcopy(fin)
    out[f"esc_antebraco_{lado}"] = max(1.0, min(ESC_MAX_BRACO, 1.0 + (esc - 1.0) * k))   # k > 1: a passada da mola estica um pouco além
    if k > 1.0:
        out[f"braco_{lado}"] = fin[f"braco_{lado}"]
    if k <= 0.0:
        out = copy.deepcopy(pose)
    return out, erro, out.get(f"esc_antebraco_{lado}", 1.0)


# ------------------------------------------------------------------ 2. pernas de pau
def pernas_de_pau(pose, k_esc):
    """Coxas com escorço k_esc (≥ 1) e a pelve sobe o mesmo tanto: os pés ficam no chão. Retorna a altura total (H)."""
    k_esc = max(1.0, min(ESC_MAX_PERNA, k_esc))
    for s in ("d", "e"):
        pose[f"esc_coxa_{s}"] = k_esc
    pose["raiz"] = [pose["raiz"][0], -(k_esc - 1.0) * L_COXA]
    return 4.0 + (k_esc - 1.0) * L_COXA


# ------------------------------------------------------------------ desenho (corrige a ponta do antebraço esticado)
LIMIAR_ESC = 2.0                 # abaixo disto a ponta arredondada do antebraço fica escondida sob a mão (como no rig)


def desenhar(c, x_pe, y_pe, altura_px, vista="frente", direcao=1, pose=None, rosto=None, luz=-1):
    """Igual a heitor_v2.desenhar, mas com o antebraço esticado a ponta arredondada dele (que o escorço também
    alonga) não passa da mão: duas passadas recortadas —
    A) o Heitor esticado, inteiro (fora da faixa além do punho os pixels são os do rig);  B) só a faixa além do punho é
    apagada e redesenhada a partir do Heitor com o antebraço normal deslocado para o punho esticado (a mão e a ponta do
    antebraço exatamente como o rig desenha sem esticar). Tudo numa camada própria (saveLayer): a faixa apagada não apaga
    o fundo nem a sombra desenhados antes."""
    pose = pose or HV.pose_base(vista); u = altura_px / 4.0
    lados = [s for s in ("d", "e") if pose.get(f"esc_antebraco_{s}", 1.0) > LIMIAR_ESC]
    if not lados:
        return HV.desenhar(c, x_pe, y_pe, altura_px, vista=vista, direcao=direcao, pose=pose, rosto=rosto, luz=luz)
    M = HV.esqueleto(pose, vista); faixas = []
    for s in lados:
        w0 = M[f"mao_{s}"].mapXY(0, 0); w1 = M[f"mao_{s}"].mapXY(0, 1)
        a = np.array([w1.x() - w0.x(), w1.y() - w0.y()]); a /= np.linalg.norm(a); n = np.array([-a[1], a[0]]); w = np.array([w0.x(), w0.y()])
        cantos = [w - a * 0.03 + n * 0.42, w + a * 0.75 + n * 0.42, w + a * 0.75 - n * 0.42, w - a * 0.03 - n * 0.42]
        path = skia.Path(); path.moveTo(*[float(v) for v in cantos[0]])
        for q in cantos[1:]:
            path.lineTo(*[float(v) for v in q])
        path.close()
        mtx = skia.Matrix(); mtx.setTranslate(x_pe, y_pe); mtx.preScale(u * direcao, u); path.transform(mtx)
        normal = copy.deepcopy(pose); normal[f"esc_antebraco_{s}"] = 1.0
        wn = HV.esqueleto(normal, vista)[f"mao_{s}"].mapXY(0, 0)
        faixas.append((path, normal, (w[0] - wn.x()) * u * direcao, (w[1] - wn.y()) * u))
    c.saveLayer()                                                       # camada própria: a borracha não apaga o que está embaixo
    Mret = HV.desenhar(c, x_pe, y_pe, altura_px, vista=vista, direcao=direcao, pose=pose, rosto=rosto, luz=luz)   # sem recorte: fora da faixa, pixels do rig
    for path, normal, dx, dy in faixas:
        c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
        c.drawPaint(skia.Paint(BlendMode=skia.BlendMode.kClear))          # apaga só a faixa, dentro da camada
        HV.desenhar(c, x_pe + dx, y_pe + dy, altura_px, vista=vista, direcao=direcao, pose=normal, rosto=rosto, luz=luz)
        c.restore()
    c.restore()
    return Mret


def limites(pose, vista):
    """Juntas (X2/X3) e o escorço dentro da faixa da extensão."""
    fora = X3.limites(pose, vista)
    for s in ("d", "e"):
        for k, mx in ((f"esc_antebraco_{s}", ESC_MAX_BRACO), (f"esc_coxa_{s}", ESC_MAX_PERNA)):
            v = pose.get(k, 1.0)
            if not 0.35 <= v <= mx + 1e-9:
                fora.append((k, round(v, 3), (0.35, mx)))
    return fora
