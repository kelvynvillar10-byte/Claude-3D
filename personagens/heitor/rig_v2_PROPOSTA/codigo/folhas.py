#!/usr/bin/env python3
"""Heitor rig v2 (PROPOSTA) — folhas da fase F1 (imagens estáticas para aprovação do diretor).

folhas/folha_modelo_v2.png       giro: frente, 3/4, perfil, costas + 3/4 e perfil espelhados, com linhas de alinhamento
folhas/folha_maos_v2.png         poses de mão (dorso, palma, lado) + cada dedo flexionando sozinho + contagem 1–5
folhas/folha_expressoes_v2.png   11 expressões de frente + surpresa, medo, alegria, preocupação em 3/4 e perfil
folhas/folha_articulacoes_v2.png poses estáticas que provam as juntas (ombro, cotovelo, punho, quadril, joelho, tornozelo)
"""
import copy, sys
from pathlib import Path
import skia

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import heitor_v2 as H   # noqa: E402

OUT = AQUI.parent / "folhas"; OUT.mkdir(exist_ok=True)
FUNDO = 0xFFEDEBE6; TXT = 0xFF1F2A44
F_T = skia.Font(H.NUNITO, 52); F_S = skia.Font(H.NUNITO, 30); F_P = skia.Font(H.NUNITO, 24)
CAB = "HEITOR — rig v2 (PROPOSTA, aguardando aprovação; não substitui nenhuma referência)"


def titulo(c, sub):
    c.drawString(CAB, 50, 75, F_T, skia.Paint(AntiAlias=True, Color=TXT))
    c.drawString(sub, 50, 120, F_S, skia.Paint(AntiAlias=True, Color=0xFF55607A))


def rotulo(c, txt, x, y, f=F_S):
    w = f.measureText(txt); c.drawString(txt, x - w / 2, y, f, skia.Paint(AntiAlias=True, Color=TXT))


def folha_modelo():
    W, Hh = 3800, 1750; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(FUNDO)
    titulo(c, "Giro com linhas de alinhamento · unidade H = altura da cabeça · altura total 4 H · paleta da especificação oficial")
    alt = 1300; chao = 1620; u = alt / 4
    linhas = [("topo 4,0 H", 4.0), ("olhos 3,44 H", 3.44), ("queixo 3,0 H", 3.0), ("ombro 2,76 H", 2.76),
              ("barra camiseta 1,72 H", 1.72), ("joelho 0,96 H", 0.96), ("tornozelo 0,22 H", 0.22), ("chão", 0.0)]
    for nome, h in linhas:
        y = chao - h * u
        c.drawLine(40, y, W - 40, y, skia.Paint(AntiAlias=True, Color=0x553D80D8, StrokeWidth=2, PathEffect=skia.DashPathEffect.Make([14, 10], 0)))
        c.drawString(nome, W - 330, y - 8, F_P, skia.Paint(AntiAlias=True, Color=0xFF3D80D8))
    vistas = [("frente", 1, "frente"), ("tres_quartos", 1, "3/4 (direita)"), ("perfil", 1, "perfil (direita)"), ("costas", 1, "costas"),
              ("tres_quartos", -1, "3/4 (esquerda, espelho)"), ("perfil", -1, "perfil (esquerda, espelho)")]
    for i, (v, d, nome) in enumerate(vistas):
        x = 300 + i * 560
        H.desenhar(c, x, chao, alt, vista=v, direcao=d)
        rotulo(c, nome, x, chao + 70)
    s.makeImageSnapshot().save(str(OUT / "folha_modelo_v2.png"), skia.kPNG)


def folha_maos():
    W, Hh = 3400, 2150; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(FUNDO)
    titulo(c, "Mãos com 5 dedos individuais: polegar (2 falanges) e indicador, médio, anelar, mínimo (3 falanges), cada junta com ângulo próprio")
    poses = ["relaxada", "aberta", "punho", "apontar", "segurar", "acenar", "joinha"]
    esc = 640   # px por H (a mão inteira tem ~0,4 H)
    for j, v in enumerate(["dorso", "palma", "lado"]):
        y = 200 + j * 400
        c.drawString(v.upper(), 50, y + 150, F_S, skia.Paint(AntiAlias=True, Color=TXT))
        for i, n in enumerate(poses):
            x = 420 + i * 410
            c.save(); c.translate(x, y); c.scale(esc, esc); H.desenhar_mao(c, H.MAOS[n], v, False, 1); c.restore()
            rotulo(c, n, x, y + 345, F_P)
    y0 = 1450
    c.drawString("CADA DEDO SOZINHO (dorso)", 50, y0 - 30, F_S, skia.Paint(AntiAlias=True, Color=TXT))
    for i, n in enumerate(["polegar", "indicador", "medio", "anelar", "minimo"]):
        d = copy.deepcopy(H.MAOS["aberta"]); d[n] = [60, 70] if n == "polegar" else [90, 95, 60]
        x = 200 + i * 320
        c.save(); c.translate(x, y0); c.scale(esc, esc); H.desenhar_mao(c, d, "dorso", False, 1); c.restore()
        rotulo(c, n, x, y0 + 345, F_P)
    c.drawString("CONTAGEM 1–5 (palma)", 1850, y0 - 30, F_S, skia.Paint(AntiAlias=True, Color=TXT))
    for k in range(1, 6):
        x = 1950 + (k - 1) * 300
        c.save(); c.translate(x, y0); c.scale(esc, esc); H.desenhar_mao(c, H.MAOS[f"conta_{k}"], "palma", False, 1); c.restore()
        rotulo(c, str(k), x, y0 + 345, F_P)
    s.makeImageSnapshot().save(str(OUT / "folha_maos_v2.png"), skia.kPNG)


def cabeca(c, x, y, tam, vista, expr, d=1):
    """Recorte da cabeça: desenha o personagem grande e corta na região da cabeça."""
    alt = tam * 4.0
    c.save(); c.clipRect(skia.Rect.MakeXYWH(x - tam * 0.75, y - tam * 0.62, tam * 1.5, tam * 1.38))
    H.desenhar(c, x, y + tam * 3.5, alt, vista=vista, direcao=d, rosto=expr)
    c.restore()


def folha_expressoes():
    W, Hh = 3600, 1900; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(FUNDO)
    titulo(c, "Expressões: olhos pequenos e escuros com brilho (branco só no susto/medo), pálpebras, sobrancelha grossa, bocas — sem bochecha rosada")
    nomes = ["neutro", "alegria", "surpresa", "medo", "preocupacao", "triste", "bravo", "pensativo", "sonolento", "convencido", "dormindo"]
    tam = 300
    for i, n in enumerate(nomes):
        x = 230 + (i % 6) * 560; y = 420 + (i // 6) * 520
        cabeca(c, x, y, tam, "frente", n); rotulo(c, n, x, y + tam * 0.95)
    y = 1520
    c.drawString("3/4 e perfil:", 50, y - 200, F_S, skia.Paint(AntiAlias=True, Color=TXT))
    for i, n in enumerate(["surpresa", "medo", "alegria", "preocupacao"]):
        for j, v in enumerate(["tres_quartos", "perfil"]):
            x = 330 + i * 820 + j * 380
            cabeca(c, x, y, 250, v, n); rotulo(c, f"{n} · {'3/4' if j == 0 else 'perfil'}", x, y + 250 * 0.95, F_P)
    s.makeImageSnapshot().save(str(OUT / "folha_expressoes_v2.png"), skia.kPNG)


def folha_articulacoes():
    W, Hh = 4300, 1800; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(FUNDO)
    titulo(c, "Juntas funcionais (poses ESTÁTICAS — animação só na fase F2): ombro, cotovelo, punho, dedos, quadril, joelho, tornozelo, tronco, cabeça")
    alt = 1150; chao = 1580
    poses = []
    p = H.pose_base("frente"); p.update({"braco_d": 108, "antebraco_d": 62, "mao_d": -10, "dedos_d": H.MAOS["acenar"], "mao_vista_d": "palma"}); poses.append(("frente", p, "alegria", "acenar (ombro+cotovelo+punho)"))
    p = H.pose_base("frente"); p.update({"braco_e": -78, "antebraco_e": -8, "dedos_e": H.MAOS["apontar"], "mao_vista_e": "dorso", "cabeca": -4}); poses.append(("frente", p, "surpresa", "apontar"))
    p = H.pose_base("tres_quartos"); p.update({"braco_d": 40, "antebraco_d": -95, "dedos_d": H.MAOS["segurar"], "mao_vista_d": "dorso"}); poses.append(("tres_quartos", p, "pensativo", "segurar (dedos fechados)"))
    p = H.pose_base("perfil"); p.update({"coxa_d": -55, "canela_d": 85, "pe_d": -10, "coxa_e": 20, "canela_e": 15, "braco_d": -40, "antebraco_d": -70, "braco_e": 40, "antebraco_e": -30, "tronco": 8}); poses.append(("perfil", p, "medo", "quadril, joelho, tornozelo"))
    p = H.pose_base("perfil"); p.update({"tronco": 20, "cabeca": -10, "coxa_d": -20, "canela_d": 30, "coxa_e": 30, "canela_e": 10, "braco_d": 60, "antebraco_d": -90, "braco_e": -60, "antebraco_e": -90,
                                          "dedos_d": H.MAOS["punho"], "dedos_e": H.MAOS["punho"]}); poses.append(("perfil", p, "bravo", "tronco inclinado, punhos"))
    p = H.pose_base("frente"); p.update({"braco_d": 25, "antebraco_d": -140, "braco_e": -25, "antebraco_e": 140, "dedos_d": H.MAOS["punho"], "dedos_e": H.MAOS["punho"],
                                          "coxa_d": 12, "canela_d": -18, "coxa_e": -12, "canela_e": 18}); poses.append(("frente", p, "preocupacao", "cotovelos dobrados, joelhos"))
    for i, (v, pp, ex, nome) in enumerate(poses):
        x = 420 + i * 690
        H.desenhar(c, x, chao, alt, vista=v, pose=pp, rosto=ex)
        rotulo(c, nome, x, chao + 70, F_P)
    s.makeImageSnapshot().save(str(OUT / "folha_articulacoes_v2.png"), skia.kPNG)


if __name__ == "__main__":
    folha_modelo(); folha_maos(); folha_expressoes(); folha_articulacoes()
    print("ok:", sorted(p.name for p in OUT.iterdir()))
