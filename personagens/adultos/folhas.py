#!/usr/bin/env python3
"""Folhas de modelo do Juca e da Jandira (PROPOSTA para aprovação do diretor)."""
import copy, sys
from pathlib import Path
import skia
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rig_adulto as RA   # noqa: E402

OUT = AQUI / "folhas"; OUT.mkdir(exist_ok=True)
FUNDO = 0xFFEDEBE6; TXT = 0xFF1F2A44


def fontes(H):
    return skia.Font(H.NUNITO, 52), skia.Font(H.NUNITO, 30), skia.Font(H.NUNITO, 24)


def rotulo(c, f, txt, x, y):
    w = f.measureText(txt); c.drawString(txt, x - w / 2, y, f, skia.Paint(AntiAlias=True, Color=TXT))


def folha_modelo(nome):
    P = RA.carregar(nome); H = P.H
    FT, FS, FP = fontes(H)
    W, Hh = 3800, 1900; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(FUNDO)
    c.drawString(f"{P.nome.upper()} — rig adulto v1 (PROPOSTA, derivado do rig oficial Heitor v2.1)", 50, 75, FT, skia.Paint(AntiAlias=True, Color=TXT))
    c.drawString(P.esp["descricao"], 50, 120, FS, skia.Paint(AntiAlias=True, Color=0xFF55607A))
    alt = 1450; chao = 1770; u = alt / 5
    PR = H.PROP
    for nm, h in [("topo 5,0 H", 5.0), ("olhos 4,44 H", 4.44), ("ombro 3,72 H", 3.72), ("barra camiseta 2,25 H", 2.25),
                  ("joelho 1,23 H", 1.23), ("tornozelo 0,22 H", 0.22), ("chão", 0.0)]:
        y = chao - h * u
        c.drawLine(40, y, W - 40, y, skia.Paint(AntiAlias=True, Color=0x553D80D8, StrokeWidth=2, PathEffect=skia.DashPathEffect.Make([14, 10], 0)))
        c.drawString(nm, W - 330, y - 8, FP, skia.Paint(AntiAlias=True, Color=0xFF3D80D8))
    vistas = [("frente", 1, "frente"), ("tres_quartos", 1, "3/4 (direita)"), ("perfil", 1, "perfil (direita)"), ("costas", 1, "costas"),
              ("tres_quartos", -1, "3/4 (esquerda, espelho)"), ("perfil", -1, "perfil (esquerda, espelho)")]
    for i, (v, d, nm) in enumerate(vistas):
        x = 300 + i * 560
        H.desenhar(c, x, chao, alt, vista=v, direcao=d)
        rotulo(c, FS, nm, x, chao + 70)
    s.makeImageSnapshot().save(str(OUT / f"folha_modelo_{nome}.png"), skia.kPNG)


def folha_expressoes(nome):
    P = RA.carregar(nome); H = P.H
    FT, FS, FP = fontes(H)
    nomes = ["neutro", "alegria", "surpresa", "medo", "preocupacao", "triste", "bravo", "pensativo", "sonolento",
             "convencido", "dormindo", "vidrado", "irritada", "desconfiada"]
    extra = [("sonolento", {"olheira": 1.0, "barba": 1.0 if nome == "juca" else 0.0}, "amanhecer (olheira" + (" + barba" if nome == "juca" else "") + ")")]
    W, Hh = 3800, 2700; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(FUNDO)
    c.drawString(f"{P.nome.upper()} — expressões (rosto paramétrico do rig v2.1 + vidrado, irritada, desconfiada, olheira/barba)", 50, 75, FT, skia.Paint(AntiAlias=True, Color=TXT))
    tam = 280
    itens = [(n, None, n) for n in nomes] + extra
    for i, (n, mod, rot) in enumerate(itens):
        x = 230 + (i % 7) * 520; y = 330 + (i // 7) * 600
        e = copy.deepcopy(H.EXPRESSOES[n]); e.update(mod or {})
        c.save(); c.clipRect(skia.Rect.MakeXYWH(x - tam * 0.8, y - tam * 0.7, tam * 1.6, tam * 1.55))
        H.desenhar(c, x, y + tam * 4.5, tam * 5.0, vista="frente", rosto=e)
        c.restore(); rotulo(c, FP, rot, x, y + tam * 1.05)
    y = 2280
    for i, n in enumerate(["surpresa", "alegria", "vidrado" if nome == "juca" else "irritada"]):
        for j, v in enumerate(["tres_quartos", "perfil"]):
            x = 300 + i * 1200 + j * 480
            c.save(); c.clipRect(skia.Rect.MakeXYWH(x - tam * 0.8, y - tam * 0.7, tam * 1.6, tam * 1.55))
            H.desenhar(c, x, y + tam * 4.5, tam * 5.0, vista=v, rosto=n); c.restore()
            rotulo(c, FP, f"{n} · {'3/4' if j == 0 else 'perfil'}", x, y + tam * 1.05)
    s.makeImageSnapshot().save(str(OUT / f"folha_expressoes_{nome}.png"), skia.kPNG)


if __name__ == "__main__":
    for n in ("juca", "jandira"):
        folha_modelo(n); folha_expressoes(n)
    print("ok")
