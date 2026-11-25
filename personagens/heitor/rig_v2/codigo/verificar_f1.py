#!/usr/bin/env python3
"""Heitor rig v2 — verificação automática da fase F1 (consistência visual entre ângulos).

Para cada vista (frente, 3/4, perfil, costas, 3/4 espelhado, perfil espelhado), desenha o personagem
sozinho e mede EM PIXELS:
  - topo da cabeça, linha dos olhos (pixels de pupila/íris), barra da camiseta (fim do azul da camisa no tronco),
    barra da calça (fim da cor 'barra'), sola (último pixel opaco) → alturas em H; tolerância ±2 % da altura total;
  - paleta: fração dos pixels opacos dentro de ±12 (RGB) de uma cor oficial (o resto é antisserrilhado/mistura);
  - estampa: OCR do tronco — "Modo Curioso" deve aparecer na frente e no 3/4 (também espelhado) e NÃO no perfil/costas.
Saída: verificacao/f1_consistencia.json e verificacao/f1_consistencia.md
"""
import json, sys, unicodedata
from pathlib import Path
import numpy as np, skia

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import heitor_v2 as H   # noqa: E402

OUT = AQUI.parent / "verificacao"; OUT.mkdir(exist_ok=True)
ALT, CHAO, W, HH = 1200, 1300, 900, 1400
u = ALT / 4
VISTAS = [("frente", 1), ("tres_quartos", 1), ("perfil", 1), ("costas", 1), ("tres_quartos", -1), ("perfil", -1)]


def render(v, d):
    s = skia.Surface(W, HH); c = s.getCanvas(); c.clear(0x00000000)
    H.desenhar(c, W / 2, CHAO, ALT, vista=v, direcao=d)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)


def rgb(hexs):
    h = hexs.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])


PAL = {k: rgb(v) for k, v in H.MOD["paleta"].items()}


def mascara(a, nomes, tol=14):
    m = np.zeros(a.shape[:2], bool)
    for n in nomes:
        m |= (np.abs(a[..., :3].astype(int) - PAL[n]).max(-1) <= tol) & (a[..., 3] > 200)
    return m


def altura_H(y):
    return round((CHAO - y) / u, 3)


from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
res = []
for v, d in VISTAS:
    a = render(v, d); op = a[..., 3] > 128
    ys, xs = np.nonzero(op)
    r = {"vista": v + (" (espelho)" if d < 0 else ""), "topo_H": altura_H(ys.min()), "sola_H": altura_H(ys.max() + 1)}
    olho = mascara(a, ["olho"], tol=4)                       # só a íris (#6a3d20), tolerância estreita
    olho[: int(CHAO - 4.0 * u)] = False; olho[int(CHAO - 3.0 * u):] = False   # só na cabeça (entre queixo e topo)
    r["olhos_H"] = altura_H(np.nonzero(olho)[0].mean()) if olho.sum() > 30 else None
    cx = int(xs.mean()); faixa = slice(cx - int(0.12 * u), cx + int(0.12 * u))   # coluna central do tronco (sem braços)
    cam = mascara(a, ["camisa", "camisa_s"]); cam[:, :faixa.start] = False; cam[:, faixa.stop:] = False
    cam[int(CHAO - 1.0 * u):] = False   # ignora a faixa azul do tênis (mesmo azul da camiseta)
    r["barra_camiseta_H"] = altura_H(np.nonzero(cam)[0].max() + 1)
    bar = mascara(a, ["barra"])
    r["barra_calca_H"] = altura_H(np.nonzero(bar)[0].max() + 1) if bar.sum() > 30 else None
    tot = op.sum(); dentro = np.zeros(a.shape[:2], bool)
    for k in PAL:
        dentro |= np.abs(a[..., :3].astype(int) - PAL[k]).max(-1) <= 12
    r["paleta_pct"] = round(100 * float((dentro & op).sum()) / tot, 1)
    # OCR da estampa (tronco), sobre fundo neutro
    y0, y1 = int(CHAO - 2.8 * u), int(CHAO - 1.7 * u)
    rgbimg = (a[..., :3] * (a[..., 3:] / 255) + 237 * (1 - a[..., 3:] / 255)).astype(np.uint8)[y0:y1]
    txt = " ".join(t for _, t, cf in (ocr(rgbimg[..., ::-1].copy())[0] or []))
    norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().upper().replace(" ", "")
    r["ocr_tronco"] = txt; r["estampa_lida"] = "MODOCURIOSO" in norm
    r["estampa_esperada"] = v in ("frente", "tres_quartos")
    res.append(r)

ref = res[0]; tol = 0.02 * 4.0   # ±2 % da altura total, em H
for r in res:
    falhas = []
    for k in ("topo_H", "sola_H", "olhos_H", "barra_camiseta_H", "barra_calca_H"):
        if r[k] is None or ref[k] is None:
            continue
        if abs(r[k] - ref[k]) > tol:
            falhas.append(f"{k} {r[k]} vs {ref[k]}")
    if r["estampa_lida"] != r["estampa_esperada"]:
        falhas.append("estampa " + ("ausente" if r["estampa_esperada"] else "indevida"))
    r["ok"] = not falhas; r["falhas"] = falhas
(OUT / "f1_consistencia.json").write_text(json.dumps({"tolerancia_H": tol, "resultados": res}, ensure_ascii=False, indent=1))
linhas = ["# Verificação automática F1 — consistência entre ângulos (Heitor rig v2)", "",
          f"Medido em pixels (altura 1200 px; 1 H = 300 px). Tolerância: ±{tol:.2f} H (2 % da altura).", "",
          "| Vista | Topo | Olhos | Barra camiseta | Barra calça | Sola | Paleta oficial | Estampa (OCR) | Resultado |", "|" + "---|" * 9]
for r in res:
    est = ("lida" if r["estampa_lida"] else "não lida") + (" ✓" if r["estampa_lida"] == r["estampa_esperada"] else " ✗")
    linhas.append(f"| {r['vista']} | {r['topo_H']} | {r['olhos_H'] if r['olhos_H'] is not None else '—'} | {r['barra_camiseta_H']} | "
                  f"{r['barra_calca_H']} | {r['sola_H']} | {r['paleta_pct']} % | {est} | {'OK' if r['ok'] else 'FALHA: ' + '; '.join(r['falhas'])} |")
(OUT / "f1_consistencia.md").write_text("\n".join(linhas) + "\n")
print("\n".join(linhas))
