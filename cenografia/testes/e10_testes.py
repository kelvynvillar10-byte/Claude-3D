#!/usr/bin/env python3
"""E10 parte 1 — quarto do EP01 em escala MACRO, com o Heitor rig v2 a 0,05 m (testes; não é o episódio).

Quatro planos da decupagem, cada um uma placa (câmera própria, foco e abertura físicos):
  A_despertar   em cima do edredom, olhando para os travesseiros (o lençol vira deserto)
  B_cama_predio do chão, em contra-plongée: a cama vira um prédio de ~14 m na escala dele
  C_moeda       no chão: moeda genérica de 27 mm, gotas, migalhas e poeira ao lado do Heitor
  D_celular     em cima do criado-mudo: celular de 15 cm de pé, como um painel gigante
Saídas em cenografia/testes/e10/: um PNG 1080×1920 por plano, folha comparativa e e10_resultado.json.
Uso: e10_testes.py [--rapido]   (--rapido: 270×480 e poucas amostras, para conferir enquadramento)
"""
import copy, json, math, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "cenografia" / "testes"))
sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "rig_v2" / "codigo"))
from cenografia import construir as CO                                   # noqa: E402
from cenografia.nucleo import receita as R, cache as C                    # noqa: E402
from cenografia.nucleo.compositor import Placa                            # noqa: E402
import heitor_v2 as HV                                                     # noqa: E402
sys.path.insert(0, str(RAIZ / "personagens" / "animais"))
import gato as GATO, aranha as ARANHA                                      # noqa: E402
import e1_testes as T1                                                     # noqa: E402
GRADE = dict(T1.GRADE, exposicao=0.55, saturacao=1.6, grao=0.006)         # interior: mais aberto que a rua (calibrado no E10)
PESOS = {"ceu": 1.0, "sol": 1.0, "artificial": 1.0, "efeito": 0.0}       # "artificial" = tela do celular (abajur apagado)

RAPIDO = "--rapido" in sys.argv
OUT = RAIZ / "cenografia" / "testes" / ("e10_rapido" if RAPIDO else "e10"); OUT.mkdir(parents=True, exist_ok=True)
BASE = RAIZ / "cenografia" / "receitas" / "e10_quarto.json"
RECEITAS = RAIZ / "cenografia" / "receitas"
SO = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--planos=")), None)
ALT_M = 0.05                                                               # o Heitor com 5 cm
W, H = (270, 480) if RAPIDO else (1080, 1920)


def _cama(r):
    i = next(k for k, c in enumerate(r["componentes"]) if c["tipo"] == "cama")
    return i, r["componentes"][i]["params"]


def z_edredom(r, x, y):
    """Altura do edredom: a MESMA função e a mesma semente do componente 'cama'."""
    from cenografia.componentes.interior import superficie_edredom
    i, p = _cama(r)
    return superficie_edredom(p, R.rng(r["semente"], i, "cama").uniform(0, 100), x, y)


def planos(r):
    zA = z_edredom(r, 0.99, 1.30)
    return {
        "A_despertar": {"cam": {"pos": [0.95, 1.08, zA + 0.022], "alvo": [1.0, 1.9, zA + 0.11], "lente_mm": 20},
                        "heitor": [0.99, 1.30, zA], "abertura": 4.0, "rosto": "surpresa",
                        "rotulo": "em cima do edredom: os travesseiros viram montanhas"},
        "B_cama_predio": {"cam": {"pos": [0.20, 0.02, 0.012], "alvo": [0.62, 0.40, 0.30], "lente_mm": 14},
                          "heitor": [0.37, 0.21, 0.0], "abertura": 5.6, "rosto": "surpresa",
                          "rotulo": "do chão: a cama vira um prédio de 14 m na escala dele"},
        "C_moeda": {"cam": {"pos": [-0.42, -0.815, 0.05], "alvo": [-0.335, -0.62, 0.006], "lente_mm": 28},
                    "heitor": [-0.338, -0.664, 0.0], "abertura": 4.0, "rosto": "pensativo",
                    "rotulo": "no chão: moeda de 27 mm, gotas, migalhas e poeira"},
        "D_celular": {"cam": {"pos": [0.34, 1.29, 0.574], "alvo": [0.12, 1.52, 0.625], "lente_mm": 20},
                      "heitor": [0.215, 1.445, 0.55], "abertura": 4.0, "rosto": "surpresa",
                      "rotulo": "no criado-mudo: o celular de pé vira um painel de 4 m"},
        # ---- E10 parte 2
        "E_escada_base": {"base": "e10_escada.json", "cam": {"pos": [0.08, -0.34, 0.05], "alvo": [0.0, 0.55, 0.62], "lente_mm": 16},
                          "heitor": [0.02, -0.07, 0.0], "abertura": 4.0, "rosto": None, "vista": "costas",
                          "rotulo": "pé da escada: cada degrau de 18 cm é um paredão de 5 m na escala dele"},
        "F_degrau": {"base": "e10_escada.json", "cam": {"pos": [0.10, 0.37, 0.415], "alvo": [-0.02, 0.62, 0.48], "lente_mm": 18},
                     "heitor": [0.0, 0.50, 0.36], "abertura": 4.0, "rosto": "preocupacao",
                     "rotulo": "no meio da escada: o próximo espelho é um muro mais alto que ele"},
        "G_sala_gato": {"base": "e10_sala.json", "cam": {"pos": [0.12, -0.62, 0.035], "alvo": [0.55, 0.35, 0.18], "lente_mm": 18},
                        "heitor": [0.2, -0.4, 0.008], "abertura": 5.6, "rosto": None, "vista": "costas",
                        "extras": [{"tipo": "gato", "pos": [0.78, 0.12, 0.008], "altura_m": 0.19, "pose": "agachado", "direcao": -1, "pupila": 1.0}],
                        "rotulo": "sala: o gato (personagem original 2D) agachado, caçando, diante do Heitor"},
        "H_aranha_canto": {"base": "e10_sala.json", "cam": {"pos": [1.72, 1.42, 0.022], "alvo": [2.09, 1.89, 0.05], "lente_mm": 22},
                           "heitor": [1.85, 1.60, 0.0], "abertura": 4.0, "rosto": "medo",
                           "extras": [{"tipo": "aranha", "pos": [1.975, 1.775, 0.0], "largura_m": 0.04, "levantar_frente": 0.6}],
                           "rotulo": "canto do rodapé: a aranha (personagem original 2D) atrás do Heitor"},
    }


def receita(r0, pl):
    r = copy.deepcopy(R.carregar(RECEITAS / pl["base"]) if pl.get("base") else r0); r["camera"] = copy.deepcopy(pl["cam"])
    foco = float(np.linalg.norm(np.asarray(pl["heitor"]) + [0, 0, ALT_M * 0.6] - np.asarray(pl["cam"]["pos"])))
    for c in r["componentes"]:
        if c["tipo"] == "camera_macro":
            c["params"] = {"foco_m": round(foco, 4), "abertura_f": pl["abertura"]}
    if RAPIDO:
        r["saida"] = {"largura": W, "altura": H, "overscan": 0.25, "amostras": 16,
                      "amostras_por_camada": {"ceu": 2, "longe": 12, "meio": 16, "perto": 16}}
    return r, foco


def projetar(P, p):
    I = P.m["intrinsecos"]; d = np.asarray(p, float) - np.asarray(I["pos"])
    zc = float(d @ np.asarray(I["dir"])); xc = float(d @ np.asarray(I["dir_x"])); yc = float(d @ np.asarray(I["cima"]))
    return (I["cx"] + I["f_px"] * xc / zc, I["cy"] - I["f_px"] * yc / zc, zc)


def desenhista(pe, topo, rosto, vista="frente", extras=()):
    """pe/topo já projetados na placa (px, px, profundidade); proj aplica o movimento de câmera 2.5D.
    extras: animais já projetados (desenhados ANTES do Heitor: ficam atrás dele)."""
    def desenhar(cv, proj):
        for ex in extras:
            x, y, _ = proj(*ex["pe"]); _, yt, _ = proj(*ex["topo"]); tam = y - yt
            if ex["tipo"] == "gato":
                cv.drawOval(skia.Rect.MakeXYWH(x - 0.5 * tam, y - 0.03 * tam, 1.0 * tam, 0.06 * tam),
                            skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 30, 22, 20), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.02 * tam)))
                GATO.desenhar(cv, x, y, tam, pose=ex.get("pose", "sentado"), direcao=ex.get("direcao", 1), pupila=ex.get("pupila", 0.25), olhar=ex.get("olhar", 0.0))
            else:
                cv.drawOval(skia.Rect.MakeXYWH(x - 0.4 * tam, y - 0.06 * tam, 0.8 * tam, 0.12 * tam),
                            skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(90, 30, 22, 20), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.03 * tam)))
                ARANHA.desenhar(cv, x, y, tam, levantar_frente=ex.get("levantar_frente", 0.0))
        x, y, _ = proj(*pe); _, yt, _ = proj(*topo); alt = y - yt
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.2 * alt, y - 0.02 * alt, 0.4 * alt, 0.04 * alt),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(120, 30, 22, 20), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.015 * alt)))
        HV.desenhar(cv, x, y, alt, vista=vista, direcao=1, pose=None, rosto=rosto)
    return desenhar


def main():
    r0 = R.carregar(BASE); res = {"planos": {}, "rapido": RAPIDO}
    imgs = []
    for nome, pl in planos(r0).items():
        if SO and nome.split("_")[0] not in SO:
            continue
        r, foco = receita(r0, pl)
        t = time.time(); k, m, hit = CO.construir(r); dt = time.time() - t
        P = Placa(C.pasta(k))
        pe = tuple(pl["heitor"]); topo = (pe[0], pe[1], pe[2] + ALT_M)
        ppe, ptopo = projetar(P, pe), projetar(P, topo)
        extras = []
        for ex in pl.get("extras", []):
            q = tuple(ex["pos"])
            if ex["tipo"] == "gato":
                topo_ex = (q[0], q[1], q[2] + ex["altura_m"])
            else:                                                    # aranha: a "altura" no desenho = envergadura (medida na horizontal)
                topo_ex = (q[0], q[1], q[2] + ex["largura_m"])
            extras.append(dict(ex, pe=projetar(P, q), topo=projetar(P, topo_ex)))
        img = np.asarray(P.compor(personagem=desenhista(ppe, ptopo, pl["rosto"], pl.get("vista", "frente"), extras), profundidade_personagem=ppe[2], grade=GRADE, pesos=PESOS))
        cv2.imwrite(str(OUT / f"{nome}.png"), cv2.cvtColor(img[..., :3], cv2.COLOR_RGB2BGR))
        imgs.append(img[..., :3])
        qa = m.get("qa_cena", {})
        res["planos"][nome] = {"rotulo": pl["rotulo"], "chave": k[:16], "cache": hit, "render_s": round(dt, 1), "foco_m": round(foco, 3),
                               "abertura_f": pl["abertura"], "heitor_altura_px_placa": round(ppe[1] - ptopo[1], 1),
                               "heitor_dist_camera_m": round(ppe[2], 3),
                               "flutuando": qa.get("nada_flutuando", {}).get("flutuando"), "textos_3d": qa.get("textos")}
        print(nome, res["planos"][nome], flush=True)
    folha = np.concatenate([cv2.resize(i, (W // 2 if not RAPIDO else W, H // 2 if not RAPIDO else H)) for i in imgs], axis=1)
    cv2.imwrite(str(OUT / (f"folha_e10_{'_'.join(SO)}.png" if SO else "folha_e10.png")), cv2.cvtColor(folha, cv2.COLOR_RGB2BGR))
    anterior = json.loads((OUT / "e10_resultado.json").read_text()) if (OUT / "e10_resultado.json").exists() and SO else {"planos": {}}
    anterior["planos"].update(res["planos"]); anterior["rapido"] = RAPIDO
    (OUT / "e10_resultado.json").write_text(json.dumps(anterior, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
