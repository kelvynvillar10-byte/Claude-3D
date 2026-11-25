#!/usr/bin/env python3
"""Piloto 01 — gera montagem.json (fonte única de verdade da edição) a partir de voz/tempos.json.

Cortes caem nas fronteiras dos blocos de legenda (entre falas), como nas referências.
Cada plano define fundo, câmera virtual, personagem (vista, expressões por tempo), efeitos,
posição da legenda e eventos sonoros. O compositor e o mixador leem só este arquivo.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
T = json.loads((P / "voz" / "tempos.json").read_text())
B = T["blocos"]
FPS, DUR = 30, 10.0


def bloco(txt):
    return next(b for b in B if b["txt"] == txt)


def palavra(txt_bloco, w):
    return next(p for p in bloco(txt_bloco)["palavras"] if p["w"].strip("?!.,").lower() == w.lower())


def corte(a, b):   # meio do intervalo entre o fim de um bloco e o início do próximo, em quadro inteiro
    return round(((bloco(a)["fim"] + bloco(b)["ini"]) / 2) * FPS) / FPS


c1 = corte("acordasse amanhã", "e descobrisse")
c2 = corte("que é o", "último homem")
c3 = corte("do mundo?!", "Nenhum carro.")
c4 = corte("Nenhuma voz.", "Oito bilhões")
c5 = corte("de pessoas", "sumiram.")
c6 = corte("sumiram.", "Até que")
t_amanha = palavra("acordasse amanhã", "amanhã")["ini"]
t_ultimo = palavra("último homem", "último")["ini"]
t_carro = palavra("Nenhum carro.", "carro")["ini"]
t_voz = palavra("Nenhuma voz.", "voz")["ini"]
t_pessoas = bloco("de pessoas")["ini"]
t_vibrou = palavra("o celular vibrou.", "vibrou")["ini"]

planos = [
    {"id": "P1", "nome": "Acorda", "ini": 0.0, "fim": c1, "fundo": "p1_travesseiro",
     "narra": "E se tu acordasse amanhã", "vê": "close: Heitor deitado acorda e arregala os olhos",
     "camera": {"z": [1.0, 1.10], "curva": "ease_out", "alvo": "cabeca", "punch": [{"t": t_amanha, "amp": 0.05}]},
     "personagem": {"vista": "frente", "pose": "deitado", "luz": 1, "tinta": [255, 232, 205],
                    "expr": [[0.0, "dormindo"], [0.62, "acordando"], [t_amanha, "surpreso"]]},
     "efeitos": ["poeira_luz"], "legenda": "topo"},
    {"id": "P2", "nome": "Janela", "ini": c1, "fim": c2, "fundo": "p2_janela",
     "narra": "e descobrisse que é o", "vê": "Heitor de costas olha a cidade pela janela",
     "camera": {"z": [1.0, 1.08], "curva": "ease_in_out", "alvo": "cabeca"},
     "personagem": {"vista": "costas", "pose": "em_pe", "luz": -1, "contraluz": True, "tinta": [150, 150, 190],
                    "expr": [[0.0, "neutro"]]},
     "efeitos": ["poeira_luz"], "legenda": "baixo"},
    {"id": "P3", "nome": "Revelação", "ini": c2, "fim": c3, "fundo": "p3_cidade",
     "narra": "último homem do mundo?!", "vê": "da janela, a rua inteira vazia (pull-out forte)",
     "camera": {"z": [1.75, 1.0], "curva": "ease_out", "dur_mov": 0.85, "centro_rel": [0.52, 0.60]},
     "efeitos": ["nevoa_forte"], "legenda": "baixo"},
    {"id": "P4", "nome": "Rua vazia", "ini": c3, "fim": c4, "fundo": "p4_rua",
     "narra": "Nenhum carro. Nenhuma voz.", "vê": "Heitor sozinho no meio da rua, carros abandonados",
     "camera": {"z": [1.0, 1.07], "curva": "linear", "pan": [-70, 40], "alvo": "pe"},
     "personagem": {"vista": "frente", "pose": "em_pe", "luz": 1, "tinta": [255, 226, 196], "sombra_chao": True,
                    "expr": [[0.0, "neutro"]], "olhar": [[0.0, 0.0], [t_carro, -1.0], [t_voz, 1.0]]},
     "efeitos": ["nevoa"], "legenda": "baixo"},
    {"id": "P5", "nome": "Inserto 8 bilhões", "ini": c4, "fim": c5, "fundo": "p5_terra",
     "narra": "Oito bilhões de pessoas", "vê": "Terra com as luzes das pessoas apagando; contador cai até 1",
     "camera": {"z": [1.0, 1.08], "curva": "ease_out"},
     "efeitos": ["insert_terra"], "contador": {"de": 8_200_000_000, "ate": 1, "t0": t_pessoas, "t1": c5 - 0.05},
     "rotulo": {"txt": "8,2 BILHÕES", "sub": "PESSOAS NA TERRA · ONU, 2025"},
     "legenda": "baixo", "entrada": {"tipo": "fusao", "dur": 0.13}},
    {"id": "P6", "nome": "Sumiram", "ini": c5, "fim": c6, "fundo": "p6_close",
     "narra": "sumiram.", "vê": "close do Heitor assustado; tremida de impacto",
     "camera": {"z": [1.12, 1.0], "curva": "ease_out", "dur_mov": 0.2, "alvo": "cabeca", "tremida": {"amp": 0.014, "dur": 0.45}},
     "personagem": {"vista": "frente", "pose": "em_pe", "luz": 1, "tinta": [255, 228, 200],
                    "expr": [[0.0, "assustado"]]},
     "legenda": "topo", "entrada": {"tipo": "flash", "dur": 0.07}},
    {"id": "P7", "nome": "Celular", "ini": c6, "fim": DUR, "fundo": "p7_celular",
     "narra": "Até que o celular vibrou.", "vê": "celular no asfalto acende e vibra",
     "camera": {"z": [1.0, 1.12], "curva": "ease_out", "centro_rel": [0.5, 0.5],
                "vibra": {"t": t_vibrou, "pulsos": 3, "amp": 0.004}},
     "tela_acende": t_vibrou - 0.03, "legenda": "topo", "exposicao": {"fundo": 1.9, "fundo_acesa": 0.62}},
]

legendas = []
for b in B:
    pl = next(p for p in planos if p["ini"] <= b["ini"] < p["fim"])
    legendas.append({"ini": b["ini"], "fim": b["fim"] + 0.06, "txt": b["txt"].upper(),
                     "dest": (b["dest"] or "").upper(), "pos": pl["legenda"]})
cortes_t = [p["ini"] for p in planos[1:]]
for i in range(len(legendas) - 1):   # legenda fica até a próxima entrar, mas não atravessa um corte
    fim = max(legendas[i]["fim"], legendas[i + 1]["ini"])
    for c in cortes_t:
        if legendas[i]["ini"] < c < fim:
            fim = c
    legendas[i]["fim"] = fim
legendas[-1]["fim"] = DUR

sfx = [
    {"t": 0.0, "tipo": "ambiente", "dur": DUR},
    {"t": 0.0, "tipo": "trilha", "dur": c5},
    {"t": t_amanha, "tipo": "pop"},
    {"t": c2 - 0.12, "tipo": "whoosh"},
    {"t": t_ultimo, "tipo": "impacto_grave"},
    {"t": c3, "tipo": "vento"},
    {"t": c4 - 0.05, "tipo": "fusao_whoosh"},
    {"t": t_pessoas, "tipo": "ticks", "dur": c5 - t_pessoas},
    {"t": c4, "tipo": "riser", "dur": c5 - c4},
    {"t": c5, "tipo": "impacto_grave"},
    {"t": c5, "tipo": "silencio_trilha"},
    {"t": t_vibrou, "tipo": "vibracao", "pulsos": 3},
]
transicoes = [{"t": c2, "tipo": "chicote", "dur": 0.13}]
m = {"fps": FPS, "duracao": DUR, "resolucao": [1080, 1920], "voz": "voz/voz.wav",
     "aviso_voz": "TEMPORÁRIA (espeak-ng); a voz oficial segue a ID-001",
     "personagem": "Heitor rig v1 (PROPOSTA)", "planos": planos, "legendas": legendas,
     "transicoes": transicoes, "sfx": sfx,
     "marca_dagua": {"texto": "MODO CURIOSO", "fonte": "RobotoCondensed-ExtraBold", "altura_px": 30,
                     "margem_dir": 40, "margem_topo": 60, "MODO": "#FFFFFF@60%", "CURIOSO": "#ffc21f"}}
(P / "montagem.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
print("cortes:", [round(p["ini"], 2) for p in planos[1:]], "· planos:", [(p["id"], round(p["fim"] - p["ini"], 2)) for p in planos])
