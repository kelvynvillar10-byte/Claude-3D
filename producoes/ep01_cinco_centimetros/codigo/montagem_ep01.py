#!/usr/bin/env python3
"""EP01 — DECUPAGEM e montagem: gera montagem.json (planos, câmera, Heitor, extras, rótulos, efeitos, legendas, sfx).

Tempos da narração final (narracao/edicoes/ep01_narracao/voz_palavras.json, 110,2 s). Cada plano cobre uma ideia
falada; os cortes caem nas pausas entre frases. Câmera: push-in com ease-out na maioria, pull-out forte nas revelações,
crash-zoom nos sustos. Fecha com a marca (fala "MODO CURIOSO") e a cartela com a pergunta para comentário (sem voz).
"""
import json, re
from pathlib import Path

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
NARR = RAIZ / "narracao" / "edicoes" / "ep01_narracao"
FPS = 30
CARTELA_CTA = 3.0

# ---------------------------------------------------------------- planos
# cam: tx/ty/tz (m, câmera 2.5D) e zoom: [início, fim]; ease: saida | suave | entrada | linear
# heitor: vista, pose, rostos [[t_rel, expressão]], pos (opcional; senão a da placa), andar {"para": [x,y,z], "tipo"}
# extras: gato | aranha | pata | sombra_gato | migalha | regua ; rotulos: [{"txt", "ancora": [x,y,z] ou "heitor_topo", "lado"}]
# efeitos: tremida [t0,t1] | vento | flash ; entrada: chicote | flash | corte
PLANOS = [
    # F1–F2: o despertar
    {"id": "S01", "fim": 1.98, "placa": "A_despertar", "cam": {"zoom": [1.10, 1.16]}, "ease": "saida",
     "heitor": {"rostos": [[0, "dormindo"], [0.9, "sonolento"]], "pose": "base"}},
    {"id": "S02", "fim": 3.70, "placa": "A_despertar", "cam": {"zoom": [1.20, 1.45]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "sonolento"], [0.35, "surpresa"]], "pose": "susto"}, "efeitos": {"tremida": [0.35, 0.7]}},
    {"id": "S03", "fim": 6.95, "placa": "N1_abertura_alto", "cam": {"zoom": [1.9, 1.0]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"pos": [0.99, 1.30, None], "rostos": [[0, "surpresa"]], "pose": "susto"},
     "rotulos": [{"txt": "5 cm", "ancora": "heitor_topo", "lado": 1, "regua": True}]},
    # F3: cama, celular, quarto
    {"id": "S04", "fim": 9.45, "placa": "B_cama_predio", "cam": {"zoom": [1.0, 1.12], "ty": [0.0, 0.004]}, "ease": "saida", "entrada": "corte",
     "heitor": {"vista": "costas", "rostos": [[0, "surpresa"]], "pose": "base"},
     "rotulos": [{"txt": "14 m", "sub": "PRA ELE", "ancora": [0.55, 0.40, 0.32], "lado": 1}]},
    {"id": "S05", "fim": 12.35, "placa": "D_celular", "cam": {"zoom": [1.0, 1.14]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "surpresa"], [1.6, "alegria"]], "pose": "base"},
     "rotulos": [{"txt": "4 m", "sub": "PRA ELE", "ancora": [0.12, 1.50, 0.70], "lado": -1}]},
    {"id": "S06", "fim": 15.0, "placa": "N2_chao_longe", "cam": {"zoom": [1.0, 1.10]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"vista": "costas", "pose": "base", "andar": {"para": [1.06, -1.27, 0.0], "tipo": "caminhada"}}},
    {"id": "S07", "fim": 17.85, "placa": "A_despertar", "cam": {"zoom": [1.35, 1.5]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "preocupacao"]], "pose": "base"}},
    # F4: o pior ainda estaria por vir (sombra do gato na parede)
    {"id": "S08", "fim": 20.85, "placa": "H_aranha_canto", "cam": {"zoom": [1.0, 1.08]}, "ease": "suave", "entrada": "corte",
     "heitor": {"rostos": [[0, "preocupacao"], [1.6, "medo"]], "pose": "base"},
     "extras": [{"tipo": "sombra_gato", "x": [0.95, 0.55], "y": 0.30, "alt": [0.55, 0.75]}]},
    # F5: gota
    {"id": "S09", "fim": 23.65, "placa": "N3_gota", "cam": {"zoom": [1.0, 1.12]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"pos": [0.932, -0.941, 0.0], "rostos": [[0, "surpresa"]], "pose": "base"}},
    {"id": "S10", "fim": 27.95, "placa": "N3_gota", "cam": {"zoom": [1.0, 1.08]}, "ease": "linear", "entrada": "corte",
     "heitor": {"vista": "perfil", "direcao": 1, "pose": "base", "pos": [0.927, -0.939, 0.0],
                "rostos": [[0, "preocupacao"]]}},
    # F6: moeda
    {"id": "S11", "fim": 31.55, "placa": "C_moeda", "cam": {"zoom": [1.0, 1.12]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"rostos": [[0, "pensativo"]], "pose": "base"},
     "rotulos": [{"txt": "27 mm", "sub": "MOEDA", "ancora": [-0.3615, -0.6428, 0.003], "lado": -1}]},
    # F7–F8: escada
    {"id": "S12", "fim": 34.65, "placa": "E_escada_base", "cam": {"zoom": [1.0, 1.0], "ty": [0.0, 0.01]}, "ease": "saida", "entrada": "corte",
     "heitor": {"vista": "costas", "pose": "base"}},
    {"id": "S13", "fim": 36.95, "placa": "F_degrau", "cam": {"zoom": [1.0, 1.12]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "preocupacao"]], "pose": "base"},
     "rotulos": [{"txt": "18 cm = 5 m", "sub": "PRA ELE", "ancora": [0.22, 0.56, 0.45], "lado": 1}]},
    {"id": "S14", "fim": 39.20, "placa": "F_degrau", "cam": {"zoom": [1.3, 1.42]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "bravo"]], "pose": "maos_alto"}},
    # F9: os animais da casa
    {"id": "S15", "fim": 41.45, "placa": "N6_quarto_geral", "cam": {"zoom": [1.0, 1.08]}, "ease": "saida", "entrada": "chicote"},
    {"id": "S16", "fim": 43.85, "placa": "G_sala_gato", "cam": {"zoom": [1.0, 1.10]}, "ease": "saida", "entrada": "corte",
     "heitor": {"vista": "costas", "pose": "base"},
     "extras": [{"tipo": "sombra_gato", "x": [0.95, 0.75], "y": 0.62, "alt": [0.35, 0.45]}]},
    # F10: aranha
    {"id": "S17", "fim": 45.30, "placa": "H_aranha_canto", "cam": {"zoom": [1.0, 1.55]}, "ease": "saida", "entrada": "flash",
     "heitor": {"rostos": [[0, "medo"]], "pose": "susto"},
     "extras": [{"tipo": "aranha", "pos": [1.865, 1.716, 0.0], "largura_m": 0.05, "fase": [0.0, 1.2], "levantar": [0.0, 0.3]}],
     "efeitos": {"tremida": [0.0, 0.35]}},
    {"id": "S18", "fim": 46.85, "placa": "H_aranha_canto", "cam": {"zoom": [1.25, 1.32]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "medo"]], "pose": "recuo"},
     "extras": [{"tipo": "aranha", "pos": [1.865, 1.716, 0.0], "largura_m": 0.05, "fase": [0.0, 0.0], "levantar": [0.4, 1.0]}]},
    # F11: gato
    {"id": "S19", "fim": 49.35, "placa": "G_sala_gato", "cam": {"zoom": [1.0, 1.10]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"vista": "costas", "pose": "base"},
     "extras": [{"tipo": "gato", "pos": [0.60, 0.06, 0.008], "altura_m": 0.28, "pose": "sentado", "direcao": -1, "pupila": [0.1, 0.1]}],
     "rotulos": [{"txt": "≈ 7 m", "sub": "PRA ELE", "ancora": [0.60, 0.06, 0.30], "lado": 1}]},
    {"id": "S20", "fim": 51.45, "placa": "G_sala_gato", "cam": {"zoom": [1.2, 1.3]}, "ease": "saida", "entrada": "corte",
     "heitor": {"vista": "costas", "pose": "base"},
     "extras": [{"tipo": "gato", "pos": [0.60, 0.06, 0.008], "altura_m": 0.28, "pose": "sentado", "direcao": -1, "pupila": [0.1, 0.5], "piscar": [0.8, 1.0]}]},
    {"id": "S21", "fim": 54.05, "insert": "olho_gato", "pupila": [0.1, 1.0], "zoom": [1.0, 1.35], "entrada": "corte",
     "efeitos": {"tremida": [1.3, 1.6]}},
    # F12–F13: movimento errado / perigo
    {"id": "S22", "fim": 56.35, "placa": "G_sala_gato", "cam": {"zoom": [1.15, 1.22]}, "ease": "suave", "entrada": "corte",
     "heitor": {"vista": "costas", "pose": "recuo"},
     "extras": [{"tipo": "gato", "pos": [0.60, 0.06, 0.008], "altura_m": 0.19, "pose": "agachado", "direcao": -1, "pupila": [1.0, 1.0]}]},
    {"id": "S23", "fim": 58.75, "placa": "G_sala_gato", "cam": {"zoom": [1.3, 1.6]}, "ease": "saida", "entrada": "flash",
     "heitor": {"vista": "frente", "rostos": [[0, "medo"]], "pose": "susto"},
     "extras": [{"tipo": "pata", "garras": [0.0, 1.0], "y": [-0.25, 0.30], "x": 0.55, "tam": 0.42}],
     "efeitos": {"tremida": [0.9, 1.4]}},
    # F14–F16: física (insert do quadrado-cubo intercalado com a força)
    {"id": "S24", "fim": 61.65, "placa": "A_despertar", "cam": {"zoom": [1.3, 1.45]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"rostos": [[0, "pensativo"], [1.8, "surpresa"]], "pose": "base"}},
    {"id": "S25", "legenda_y": 0.655, "fim": 65.05, "insert": "quadrado_cubo", "t": [0.0, 0.30], "entrada": "flash"},
    {"id": "S26", "legenda_y": 0.655, "fim": 68.05, "insert": "quadrado_cubo", "t": [0.30, 0.47], "zoom": [1.0, 1.04], "entrada": "corte"},
    {"id": "S27", "legenda_y": 0.655, "fim": 71.05, "insert": "quadrado_cubo", "t": [0.47, 0.65], "zoom": [1.06, 1.1], "entrada": "corte"},
    {"id": "S28", "fim": 73.75, "placa": "C_moeda", "cam": {"zoom": [1.0, 1.1]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"rostos": [[0, "alegria"]], "pose": "maos_alto"},
     "extras": [{"tipo": "migalha", "tam": 0.026}],
     "rotulos": [{"txt": "× 28", "sub": "MAIS FORTE (RELATIVO AO PESO)", "ancora": "heitor_topo", "lado": -1}]},
    {"id": "S29", "legenda_y": 0.655, "fim": 76.75, "insert": "quadrado_cubo", "t": [0.65, 1.0], "entrada": "corte"},
    # F17–F19: sobrevivência
    {"id": "S30", "fim": 80.15, "placa": "N3_gota", "cam": {"zoom": [1.0, 1.15]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"pos": [0.932, -0.941, 0.0], "rostos": [[0, "preocupacao"]], "pose": "base"}},
    {"id": "S31", "fim": 83.45, "placa": "N5_janela", "cam": {"zoom": [1.0, 1.08]}, "ease": "suave", "entrada": "corte",
     "heitor": {"rostos": [[0, "medo"]], "pose": "equilibrio", "vento": True}, "efeitos": {"vento": True, "tremida": [0.4, 2.6]}},
    {"id": "S32", "fim": 86.55, "placa": "N4_poca", "cam": {"zoom": [1.0, 1.12]}, "ease": "saida", "entrada": "chicote",
     "heitor": {"vista": "costas", "pose": "base", "pos": [-0.3625, -0.49, 0.0]}},
    {"id": "S33", "fim": 88.95, "placa": "C_moeda", "cam": {"zoom": [1.2, 1.32], "tx": [0.0, -0.004]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "pensativo"]], "pose": "base"}},
    {"id": "S34", "fim": 91.35, "placa": "N3_gota", "cam": {"zoom": [1.3, 1.45]}, "ease": "saida", "entrada": "corte",
     "heitor": {"pos": [0.932, -0.941, 0.0], "rostos": [[0, "triste"]], "pose": "base"}},
    # F20–F23: revelação final
    {"id": "S35", "fim": 94.75, "placa": "A_despertar", "cam": {"zoom": [1.2, 1.45]}, "ease": "suave", "entrada": "chicote",
     "heitor": {"rostos": [[0, "pensativo"], [2.2, "medo"]], "pose": "base"}},
    {"id": "S36", "fim": 97.95, "placa": "N6_quarto_geral", "cam": {"zoom": [1.12, 1.0]}, "ease": "saida", "entrada": "corte"},
    {"id": "S37", "fim": 101.95, "placa": "N2_chao_longe", "cam": {"zoom": [1.0, 1.08]}, "ease": "suave", "entrada": "corte",
     "heitor": {"vista": "costas", "pose": "base"}},
    {"id": "S38", "fim": 104.65, "placa": "B_cama_predio", "cam": {"zoom": [1.25, 1.35]}, "ease": "suave", "entrada": "corte",
     "heitor": {"vista": "frente", "rostos": [[0, "triste"]], "pose": "base"}},
    {"id": "S39", "fim": 108.05, "placa": "N7_quarto_alto", "cam": {"zoom": [3.0, 1.0]}, "ease": "saida", "entrada": "corte",
     "heitor": {"rostos": [[0, "triste"]], "pose": "base"}, "efeitos": {"circulo": True}},
    {"id": "S40", "fim": 110.40, "insert": "card_logo", "entrada": "flash"},
    {"id": "S41", "fim": 110.40 + CARTELA_CTA, "insert": "card_cta", "entrada": "corte"},
]

DESTAQUES_EXTRA = {"5", "centímetros", "prédio", "televisão", "gigante", "impossível", "pior", "gota", "obstáculo", "enorme",
                   "montanha", "escada", "paredões", "perigo", "animais", "aranha", "assustadora", "gato", "predador", "errado",
                   "curioso", "peso", "força", "forte", "invencível", "ar", "poça", "comida", "água", "mundo", "pequeno"}


def legendas():
    """Blocos de 2–3 palavras pelos tempos reais; quebra em pontuação e em pausa ≥ 0,25 s; destaque em amarelo."""
    pal = json.loads((NARR / "voz_palavras.json").read_text())
    det = json.loads((NARR / "palavras_final_detalhe.json").read_text())
    texto = (NARR / "texto.txt").read_text()
    blocos, cur = [], []
    for k, (p, d) in enumerate(zip(pal, det)):
        pont = texto[d["c1"]:d["c1"] + 2]
        cur.append((p, pont))
        prox = pal[k + 1] if k + 1 < len(pal) else None
        quebra = bool(re.match(r"\s*[.?!…,:]", pont)) or (prox is not None and prox["ini"] - p["fim"] >= 0.25)
        if len(cur) >= 3 or quebra or prox is None or (len(cur) == 2 and len("".join(x[0]["w"] for x in cur)) > 16):
            blocos.append(cur); cur = []
    out = []
    for i, b in enumerate(blocos):
        ini = b[0][0]["ini"]; fim = blocos[i + 1][0][0]["ini"] if i + 1 < len(blocos) else b[-1][0]["fim"] + 0.35
        fim = min(fim, b[-1][0]["fim"] + 0.6)
        palavras = [x[0]["w"].upper() + ("?" if "?" in x[1] else "") for x in b]
        dest = [x[0]["w"].upper() for x in b if x[0]["w"].lower() in DESTAQUES_EXTRA]
        out.append({"ini": round(ini, 3), "fim": round(fim, 3), "txt": " ".join(palavras), "dest": dest[:1]})
    return out


def sfx(planos):
    ev = [{"t": 0.0, "tipo": "trilha", "dur": 110.4}, {"t": 0.0, "tipo": "ambiente", "dur": 110.4 + CARTELA_CTA}]
    for pl in planos[1:]:
        if pl.get("entrada") in ("chicote",):
            ev.append({"t": round(pl["ini"] - 0.12, 3), "tipo": "whoosh"})
        elif pl.get("entrada") == "flash":
            ev.append({"t": round(pl["ini"], 3), "tipo": "impacto_grave"})
        else:
            ev.append({"t": round(pl["ini"], 3), "tipo": "pop"})
    extra = {"S03": [{"dt": 0.0, "tipo": "riser", "dur": 1.2}], "S08": [{"dt": 0.4, "tipo": "riser", "dur": 2.4}],
             "S09": [{"dt": 0.3, "tipo": "gota"}], "S17": [{"dt": 0.1, "tipo": "patinhas", "dur": 1.2}], "S21": [{"dt": 0.0, "tipo": "riser", "dur": 1.3}],
             "S23": [{"dt": 0.9, "tipo": "impacto_grave"}, {"dt": 0.85, "tipo": "chiado_gato"}], "S31": [{"dt": 0.0, "tipo": "vento", "dur": 3.2}],
             "S32": [{"dt": 0.2, "tipo": "gota"}], "S39": [{"dt": 0.0, "tipo": "riser", "dur": 3.0}], "S40": [{"dt": 0.0, "tipo": "impacto_grave"}]}
    for pl in planos:
        for e in extra.get(pl["id"], []):
            d = dict(e); d["t"] = round(pl["ini"] + d.pop("dt"), 3); ev.append(d)
    return sorted(ev, key=lambda e: e["t"])


def main():
    ini = 0.0
    for pl in PLANOS:
        pl["ini"] = round(ini, 3); ini = pl["fim"]
    dur = PLANOS[-1]["fim"]
    M = {"episodio": "EP01 — E se você acordasse com apenas 5 centímetros?", "fps": FPS, "duracao": round(dur, 3), "resolucao": [1080, 1920],
         "voz": str((NARR / "voz_final.wav").relative_to(RAIZ)), "planos": PLANOS, "legendas": legendas(), "sfx": sfx(PLANOS),
         "marca_dagua": {"texto": "MODO CURIOSO", "altura_px": 30, "margem_dir": 46, "margem_topo": 64},
         "cta": "COMENTA AÍ: QUAL LUGAR DA SUA CASA VOCÊ TENTARIA ALCANÇAR?"}
    (P / "montagem.json").write_text(json.dumps(M, ensure_ascii=False, indent=1) + "\n")
    durs = [p["fim"] - p["ini"] for p in PLANOS]
    print(f"{len(PLANOS)} planos · {dur:.2f} s · plano mediano {sorted(durs)[len(durs) // 2]:.2f} s · {len(M['legendas'])} legendas · "
          f"{len(M['sfx'])} eventos de som")


if __name__ == "__main__":
    main()
