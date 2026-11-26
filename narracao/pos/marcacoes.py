"""Marcações para a edição audiovisual (tempos do ÁUDIO FINAL). São sugestões: nenhum efeito sonoro é adicionado aqui."""
import direcao_edicao as DE

FORTES = {"surpresa", "descoberta", "acao"}


def gerar(palavras, direcao, duracao_s):
    fr = []
    for f in direcao["frases"]:
        a, b = f["palavras"]
        fr.append({"n": f["n"], "intencao": f["intencao"], "nome": DE.NOMES[f["intencao"]], "texto": f["texto"],
                   "ini": palavras[a]["ini"], "fim": palavras[b]["fim"]})
    destaques = [{"frase": f["n"], "palavra": palavras[d["i"]]["w"], "i": d["i"], "ini": palavras[d["i"]]["ini"],
                  "fim": palavras[d["i"]]["fim"], "ganho_db": d["db"]} for f in direcao["frases"] for d in f["destaques"]]
    pausas = []
    for k in range(len(palavras) - 1):
        a, b = palavras[k]["fim"], palavras[k + 1]["ini"]
        if b - a >= 0.15:
            fa = next(f for f in fr if f["ini"] <= palavras[k]["ini"] <= f["fim"])
            fb = next(f for f in fr if f["ini"] <= palavras[k + 1]["ini"] <= f["fim"])
            funcao = ("respiro entre frases" if fa is not fb else "pausa interna")
            if fa is not fb and fb["intencao"] in FORTES:
                funcao = f"pausa antes de {fb['nome'].lower()}"
            elif fa is not fb and fa["intencao"] in ("suspense", "misterio"):
                funcao = "pausa de suspense"
            pausas.append({"ini": round(a, 3), "fim": round(b, 3), "dur": round(b - a, 3), "depois_de": palavras[k]["w"],
                           "antes_de": palavras[k + 1]["w"], "funcao": funcao})
    cortes = []
    for i, f in enumerate(fr):
        if i == 0:
            continue
        ant = fr[i - 1]
        cortes.append({"t": round((ant["fim"] + f["ini"]) / 2, 3), "tipo": "corte entre frases",
                       "motivo": f"{ant['nome']} → {f['nome']}"})
    for f in fr:                                              # frases longas: corte possível na vírgula mais central
        if f["fim"] - f["ini"] > 3.5:
            internas = [p for p in pausas if f["ini"] < p["ini"] < f["fim"] and p["funcao"] == "pausa interna"]
            if internas:
                p = min(internas, key=lambda p: abs(p["ini"] - (f["ini"] + f["fim"]) / 2))
                cortes.append({"t": round((p["ini"] + p["fim"]) / 2, 3), "tipo": "corte interno (frase longa)", "motivo": f"frase {f['n']}"})
    cortes.sort(key=lambda c: c["t"])
    impactos = [{"t": f["ini"], "frase": f["n"], "motivo": f"início de {f['nome'].lower()}"} for f in fr if f["intencao"] in FORTES]
    impactos += [{"t": d["ini"], "frase": d["frase"], "motivo": f"palavra de destaque: {d['palavra']}"} for d in destaques]
    impactos.sort(key=lambda x: x["t"])
    sfx = []
    for p in pausas:
        if p["funcao"].startswith("pausa antes de"):
            sfx.append({"ini": p["ini"], "fim": p["fim"], "sugestao": "subida curta (riser) ou respiro de ambiente terminando na próxima palavra",
                        "motivo": p["funcao"]})
        elif p["funcao"] == "pausa de suspense":
            sfx.append({"ini": p["ini"], "fim": p["fim"], "sugestao": "ambiente grave/tensão baixa", "motivo": p["funcao"]})
    for f in fr:
        if f["intencao"] == "acao":
            sfx.append({"ini": f["ini"], "fim": f["fim"], "sugestao": "impacto ou whoosh sincronizado à palavra de ação", "motivo": "frase de ação"})
    transicoes = [{"t": c["t"], "de": fr[i]["nome"], "para": fr[i + 1]["nome"]}
                  for i, c in enumerate([c for c in cortes if c["tipo"] == "corte entre frases"]) if fr[i]["intencao"] != fr[i + 1]["intencao"]]
    return {"duracao_s": round(duracao_s, 3), "frases": fr, "destaques": destaques, "pausas": pausas, "cortes_visuais": cortes,
            "impactos": impactos, "espacos_para_sfx": sfx, "transicoes": transicoes,
            "observacao": "Tempos do áudio final. Sugestões para a edição audiovisual; nenhum efeito sonoro foi adicionado."}
