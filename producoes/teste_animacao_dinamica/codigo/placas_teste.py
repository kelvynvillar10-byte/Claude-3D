#!/usr/bin/env python3
"""Cena de prova da ANIMAÇÃO DINÂMICA — placas (cenários do Blender).
Reaproveita as placas do EP01 (sala do gato, canto da aranha) e acrescenta dois enquadramentos novos, baixos e próximos,
para o Heitor aparecer grande o bastante para atuar (caminhar, virar, olhar para cima, tropeçar).
Uso: placas_teste.py [--previa]   (--previa: 270×480 com poucas amostras, só para conferir enquadramento)
"""
import copy, sys, time
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "producoes" / "ep01_cinco_centimetros" / "codigo"))
sys.path.insert(0, str(RAIZ / "cenografia" / "testes"))
import placas_ep01 as PE                                                   # noqa: E402
from cenografia import construir as CO                                     # noqa: E402
from cenografia.nucleo import receita as R, cache as C                     # noqa: E402

REC = RAIZ / "cenografia" / "receitas"
NOVAS = {
    # lateral, rente ao chão: o Heitor anda da esquerda para a direita na borda do tapete; ao fundo, mesa e sofá
    "T1_sala_lado": {"base": "e10_sala.json", "cam": {"pos": [0.29, -0.38, 0.022], "alvo": [0.31, 0.40, 0.075], "lente_mm": 18},
                     "heitor": [0.30, -0.10, 0.008], "abertura": 4.0},
    # contra-plongée por trás do Heitor: ele em primeiro plano, o gato enorme à frente
    "T2_sala_baixo": {"base": "e10_sala.json", "cam": {"pos": [0.33, -0.33, 0.014], "alvo": [0.56, 0.12, 0.13], "lente_mm": 16},
                      "heitor": [0.40, -0.17, 0.008], "abertura": 5.6},
}


def specs(previa=False):
    out = {k: PE.specs()[k] for k in ("G_sala_gato", "H_aranha_canto")}
    for nome, pl in NOVAS.items():
        r = R.carregar(REC / pl["base"]); r["camera"] = copy.deepcopy(pl["cam"])
        foco = float(np.linalg.norm(np.asarray(pl["heitor"]) + [0, 0, 0.03] - np.asarray(pl["cam"]["pos"])))
        for c in r["componentes"]:
            if c["tipo"] == "camera_macro":
                c["params"] = {"foco_m": round(foco, 4), "abertura_f": pl["abertura"]}
        if previa:
            r["saida"].update(largura=270, altura=480, amostras=8, amostras_por_camada={"ceu": 1, "longe": 4, "meio": 6, "perto": 6})
        out[nome] = dict(pl, receita=r, foco=foco)
    return out


def pasta(nome, S):
    return C.pasta(R.chave(S[nome]["receita"]))


if __name__ == "__main__":
    previa = "--previa" in sys.argv
    S = specs(previa)
    for nome, sp in S.items():
        t = time.time(); k, m, hit = CO.construir(sp["receita"])
        qa = m.get("qa_cena", {})
        print(nome, k[:12], "cache" if hit else f"{time.time() - t:.0f} s", "flutuando:", qa.get("nada_flutuando", {}).get("flutuando"),
              "textos:", qa.get("textos"), flush=True)
