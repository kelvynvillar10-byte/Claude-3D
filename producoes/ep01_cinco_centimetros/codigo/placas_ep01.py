#!/usr/bin/env python3
"""EP01 — todas as PLACAS (cenários renderizados) do episódio: as 8 da E10 (A–H, mesmas chaves de cache) + 7 novas.
Cada placa: receita-base, câmera, posição do Heitor no mundo (m) e abertura; o foco é a distância até o Heitor.
Uso: placas_ep01.py [--so=N1,N2]   (renderiza o que faltar; o resto vem do cache)
"""
import copy, sys, time
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "cenografia" / "testes"))
import e10_testes as ET                                                    # noqa: E402  (A–H, mesmas receitas)
from cenografia import construir as CO                                     # noqa: E402
from cenografia.nucleo import receita as R, cache as C                     # noqa: E402

REC = RAIZ / "cenografia" / "receitas"
NOVAS = {
    "N1_abertura_alto": {"base": "e10_quarto.json", "cam": {"pos": [0.80, 0.80, 0.92], "alvo": [0.99, 1.30, 0.53], "lente_mm": 32},
                         "heitor": None, "abertura": 8.0, "foco_ponto": [0.99, 1.30, 0.55]},
    "N2_chao_longe": {"base": "e10_quarto.json", "cam": {"pos": [1.25, -1.55, 0.02], "alvo": [-0.9, 1.4, 0.35], "lente_mm": 16},
                      "heitor": [1.10, -1.33, 0.0], "abertura": 5.6},
    "N3_gota": {"base": "e10_quarto_gota.json", "cam": {"pos": [0.86, -1.13, 0.016], "alvo": [0.96, -0.93, 0.012], "lente_mm": 28},
                "heitor": [0.895, -1.0, 0.0], "abertura": 4.0},
    "N4_poca": {"base": "e10_quarto.json", "cam": {"pos": [-0.27, -0.62, 0.016], "alvo": [-0.44, -0.38, 0.006], "lente_mm": 20},
                "heitor": [-0.335, -0.535, 0.0], "abertura": 4.0},
    "N5_janela": {"base": "e10_quarto.json", "cam": {"pos": [-0.62, -1.28, 0.022], "alvo": [-0.95, -1.88, 0.30], "lente_mm": 18},
                  "heitor": [-0.80, -1.60, 0.0], "abertura": 4.0},
    "N6_quarto_geral": {"base": "e10_quarto.json", "cam": {"pos": [-1.45, -1.65, 1.35], "alvo": [0.7, 1.2, 0.55], "lente_mm": 18},
                        "heitor": None, "abertura": 0.0},
    "N7_quarto_alto": {"base": "e10_quarto.json", "cam": {"pos": [1.45, -1.65, 2.45], "alvo": [-0.15, 0.25, 0.0], "lente_mm": 22},
                       "heitor": [-0.15, 0.25, 0.008], "abertura": 0.0},
}


def specs():
    r0 = R.carregar(REC / "e10_quarto.json")
    out = {}
    for nome, pl in ET.planos(r0).items():
        r, foco = ET.receita(r0, pl)
        out[nome] = dict(pl, receita=r, foco=foco)
    for nome, pl in NOVAS.items():
        r = R.carregar(REC / pl["base"]); r["camera"] = copy.deepcopy(pl["cam"])
        alvo = pl.get("foco_ponto") or (np.asarray(pl["heitor"]) + [0, 0, 0.03] if pl["heitor"] else None)
        foco = float(np.linalg.norm(np.asarray(alvo) - np.asarray(pl["cam"]["pos"]))) if alvo is not None else 0.0
        for c in r["componentes"]:
            if c["tipo"] == "camera_macro":
                c["params"] = {"foco_m": round(foco, 4), "abertura_f": pl["abertura"]} if pl["abertura"] else {}
        out[nome] = dict(pl, receita=r, foco=foco)
    return out


def pasta(nome, S=None):
    S = S or specs()
    return C.pasta(R.chave(S[nome]["receita"]))


if __name__ == "__main__":
    so = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--so=")), None)
    S = specs()
    for nome, sp in S.items():
        if so and nome.split("_")[0] not in so:
            continue
        t = time.time(); k, m, hit = CO.construir(sp["receita"])
        qa = m.get("qa_cena", {})
        print(nome, k[:12], "cache" if hit else f"{time.time() - t:.0f} s", "flutuando:", qa.get("nada_flutuando", {}).get("flutuando"),
              "textos:", qa.get("textos"), flush=True)
