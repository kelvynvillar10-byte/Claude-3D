#!/usr/bin/env python3
"""EP02 — PLACAS (cenários renderizados no Blender): 7 enquadramentos da sala + 3 da cidade do jogo.
A sala é uma só receita (ep02_sala.json); cada placa troca só a câmera (e o foco). A cidade do jogo reaproveita a rua
aprovada da E6 no horário "crepusculo" (céu laranja-rosa, postes acesos), sem marca e sem texto de terceiros.
Uso: placas_ep02.py [--previa] [--so=C1,C2]
"""
import copy, sys, time
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from cenografia import construir as CO                                     # noqa: E402
from cenografia.nucleo import receita as R, cache as C                     # noqa: E402

REC = RAIZ / "cenografia" / "receitas"
SALA = {   # câmera, ponto de foco (m) e abertura (0 = sem profundidade de campo)
    "C1_geral":     {"cam": {"pos": [2.35, 1.95, 1.75], "alvo": [-0.7, -1.0, 0.75], "lente_mm": 15}, "foco": None, "f": 0},
    "C2_sofa":      {"cam": {"pos": [0.3, 0.95, 1.08], "alvo": [0.0, -1.55, 0.78], "lente_mm": 24}, "foco": [0.0, -1.45, 0.9], "f": 4.0},
    "C3_lado":      {"cam": {"pos": [2.05, -1.25, 1.02], "alvo": [-0.6, -1.55, 0.82], "lente_mm": 24}, "foco": [0.0, -1.45, 0.9], "f": 4.0},
    "C4_ombro":     {"cam": {"pos": [-0.42, -1.98, 1.32], "alvo": [0.05, 2.2, 0.98], "lente_mm": 22}, "foco": [0.0, 2.1, 1.0], "f": 5.6},
    "C5_porta":     {"cam": {"pos": [1.05, -0.75, 1.45], "alvo": [-2.6, 0.85, 1.0], "lente_mm": 20}, "foco": [-2.2, 0.75, 1.0], "f": 4.0},
    "C6_mesa":      {"cam": {"pos": [0.36, 0.14, 0.74], "alvo": [0.06, -1.3, 0.52], "lente_mm": 26}, "foco": [0.12, -0.52, 0.43], "f": 4.0},
    "C7_tv":        {"cam": {"pos": [0.3, 0.55, 0.98], "alvo": [0.0, 2.2, 0.86], "lente_mm": 26}, "foco": [0.0, 2.1, 0.9], "f": 5.6},
}
CIDADE = {
    "G1_rua_baixa": {"cam": {"pos": [1.2, -4.0, 0.95], "alvo": [0.6, 30.0, 1.6], "lente_mm": 28}},
    "G2_rua_alta":  {"cam": {"pos": [-2.5, -6.0, 10.5], "alvo": [0.5, 28.0, 1.0], "lente_mm": 24}},
    "G3_calcada":   {"cam": {"pos": [-5.0, 0.0, 1.15], "alvo": [-4.6, 20.0, 1.55], "lente_mm": 35}},
}


def specs(previa=False):
    out = {}
    base = R.carregar(REC / "ep02_sala.json")
    for nome, pl in SALA.items():
        r = copy.deepcopy(base); r["camera"] = copy.deepcopy(pl["cam"])
        for c in r["componentes"]:
            if c["tipo"] == "camera_macro":
                c["params"] = {"clip_inicio_m": 0.02}
                if pl["f"]:
                    foco = float(np.linalg.norm(np.asarray(pl["foco"]) - np.asarray(pl["cam"]["pos"])))
                    c["params"].update(foco_m=round(foco, 3), abertura_f=pl["f"])
        out[nome] = dict(pl, receita=r, tipo="sala")
    rua = R.carregar(REC / "e6_rua.json")
    for nome, pl in CIDADE.items():
        r = copy.deepcopy(rua); r["camera"] = copy.deepcopy(pl["cam"]); r["luz"] = dict(r["luz"], preset="crepusculo")
        out[nome] = dict(pl, receita=r, tipo="cidade")
    if previa:
        for sp in out.values():
            sp["receita"]["saida"].update(largura=270, altura=480, amostras=8,
                                         amostras_por_camada={k: 2 for k in sp["receita"]["saida"].get("amostras_por_camada", {})})
    return out


def pasta(nome, S):
    return C.pasta(R.chave(S[nome]["receita"]))


if __name__ == "__main__":
    previa = "--previa" in sys.argv
    so = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--so=")), None)
    S = specs(previa)
    for nome, sp in S.items():
        if so and nome.split("_")[0] not in so:
            continue
        t = time.time(); k, m, hit = CO.construir(sp["receita"])
        qa = m.get("qa_cena", {})
        print(nome, k[:12], "cache" if hit else f"{time.time() - t:.0f} s", "flutuando:", qa.get("nada_flutuando", {}).get("flutuando"),
              "textos:", qa.get("textos"), C.pasta(k), flush=True)
