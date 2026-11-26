"""DIRETOR DE NARRAÇÃO: intenção de cada trecho do roteiro → velocidade, pausas, intensidade (volume), tom e emoção.

Fluxo (sem gastar créditos):
1. `propor(roteiro)` faz um RASCUNHO por regras (palavras e pontuação do português) e agrupa blocos seguidos da mesma cena
   e da mesma intenção num TRECHO (cada trecho = uma chamada, porque os parâmetros valem para a chamada inteira);
2. o Claude REVISA o rascunho trecho a trecho e grava `direcao.json` com a intenção final e uma justificativa curta;
3. o diretor aprova (ou corrige) a FOLHA DE DIREÇÃO antes de qualquer síntese — ajustes se fazem aqui, não regenerando áudio.
Nada aqui chama a API nem outra IA.
"""
import json, re

INTENCOES = ["curiosidade", "entusiasmo", "misterio", "suspense", "surpresa", "tensao", "emocao", "explicacao"]
NOMES = {"curiosidade": "Curiosidade", "entusiasmo": "Entusiasmo", "misterio": "Mistério", "suspense": "Suspense",
         "surpresa": "Surpresa", "tensao": "Tensão", "emocao": "Emoção", "explicacao": "Explicação neutra"}
# tabela de partida (proposta aprovada no plano). velocidade = fator sobre a velocidade-base calibrada; pausas em segundos
# (inseridas como silêncio na montagem, de graça; a regra do pipeline proíbe pausa ≥ 0,8 s). emoção: só se a voz aceitar.
TABELA = {
    "curiosidade": {"fator_velocidade": 1.05, "pausa_antes": 0.00, "pausa_depois": 0.12, "vol": 1.00, "pitch": 1, "emocao": None},
    "entusiasmo":  {"fator_velocidade": 1.12, "pausa_antes": 0.00, "pausa_depois": 0.06, "vol": 1.10, "pitch": 1, "emocao": "happy"},
    "misterio":    {"fator_velocidade": 0.95, "pausa_antes": 0.30, "pausa_depois": 0.12, "vol": 0.90, "pitch": -1, "emocao": "calm"},
    "suspense":    {"fator_velocidade": 0.93, "pausa_antes": 0.35, "pausa_depois": 0.06, "vol": 0.95, "pitch": -1, "emocao": "calm"},
    "surpresa":    {"fator_velocidade": 1.10, "pausa_antes": 0.25, "pausa_depois": 0.12, "vol": 1.15, "pitch": 2, "emocao": "surprised"},
    "tensao":      {"fator_velocidade": 1.08, "pausa_antes": 0.06, "pausa_depois": 0.06, "vol": 1.05, "pitch": 0, "emocao": "fearful"},
    "emocao":      {"fator_velocidade": 0.95, "pausa_antes": 0.20, "pausa_depois": 0.20, "vol": 0.95, "pitch": -1, "emocao": "sad"},
    "explicacao":  {"fator_velocidade": 1.00, "pausa_antes": 0.00, "pausa_depois": 0.12, "vol": 1.00, "pitch": 0, "emocao": None},
}
PAUSA_MAX = 0.42            # nunca uma pausa dirigida ≥ 0,8 s; teto prático 0,42 s (regra de pausas do pipeline)

# pistas do rascunho (ordem = prioridade). São sugestões; a decisão final é a revisão do trecho.
PISTAS = [
    ("surpresa", [r"\?!", r"!\?", r"\bde repente\b", r"\bsimplesmente\b", r"\bincr[ií]vel\b", r"\bnão acredit"]),
    ("suspense", [r"\.\.\.|…", r"\baté que\b", r"\bsó que\b", r"\bmas ent[aã]o\b", r"\bfoi a[ií] que\b"]),
    ("misterio", [r"\bningu[eé]m sabe\b", r"\bsegredo", r"\bmist[eé]ri", r"\bestranh", r"\bdesconhecid", r"\binexplic"]),
    ("tensao",   [r"\bperigo", r"\bcorr[ea]", r"\bexplod", r"\brápido\b", r"\bsumi", r"\bmorr", r"\bdesespero", r"\bnunca mais\b"]),
    ("emocao",   [r"\bsaudade", r"\bfam[ií]lia", r"\bchor", r"\bsozinh", r"\bamor\b", r"\bdespedi"]),
    ("curiosidade", [r"^\s*e se\b", r"\bvoc[eê] sabia\b", r"^\s*por que\b", r"^\s*como\b", r"\?\s*$", r"\bimagin"]),
    ("entusiasmo", [r"!\s*$", r"\buau\b", r"\bolha\b", r"\bdemais\b", r"\bmilh[õo]es\b", r"\bbilh[õo]es\b", r"\bgigante"]),
]


def classificar(texto):
    """Rascunho: (intenção, pista encontrada). Sem pista → explicação neutra."""
    t = texto.lower()
    for nome, pats in PISTAS:
        for p in pats:
            if re.search(p, t):
                return nome, p
    return "explicacao", None


def parametros(intencao, velocidade_base=1.0):
    t = TABELA[intencao]
    return {"speed": round(min(2.0, max(0.5, velocidade_base * t["fator_velocidade"])), 3), "vol": t["vol"], "pitch": t["pitch"],
            "emocao_proposta": t["emocao"], "pausa_antes": min(PAUSA_MAX, t["pausa_antes"]), "pausa_depois": min(PAUSA_MAX, t["pausa_depois"])}


def _blocos(roteiro):
    """Aceita o formato por cenas ({"cenas": [{"id", "blocos": [{"txt", "fala"}]}]}) e o formato do piloto ({"blocos": [... "plano"]})."""
    if "cenas" in roteiro:
        for c in roteiro["cenas"]:
            for b in c["blocos"]:
                yield c["id"], b
    else:
        for b in roteiro["blocos"]:
            yield f"cena_{b.get('plano', 1):02d}", b


def propor(roteiro, velocidade_base=1.0):
    """Rascunho de direção: blocos seguidos da mesma cena e mesma intenção viram um trecho (uma chamada)."""
    trechos = []
    frase = []                                            # a intenção é decidida pela FRASE inteira, não por 2–3 palavras soltas
    itens = list(_blocos(roteiro))
    inten = []
    i = 0
    while i < len(itens):
        j = i
        while j < len(itens) - 1 and not re.search(r"[.?!…]\s*$", itens[j][1]["fala"]) and itens[j + 1][0] == itens[i][0]:
            j += 1
        texto_frase = " ".join(b["fala"] for _, b in itens[i:j + 1])
        nome, pista = classificar(texto_frase)
        inten += [(nome, pista)] * (j - i + 1); i = j + 1
    for k, ((cena, b), (nome, pista)) in enumerate(zip(itens, inten)):
        if trechos and trechos[-1]["cena"] == cena and trechos[-1]["intencao"] == nome:
            trechos[-1]["blocos"].append(k); trechos[-1]["fala"] += " " + b["fala"]
        else:
            trechos.append({"cena": cena, "blocos": [k], "fala": b["fala"], "intencao": nome,
                            "justificativa": f"rascunho por regra ({pista})" if pista else "rascunho: sem pista → explicação neutra"})
    for t in trechos:
        t.update(parametros(t["intencao"], velocidade_base))
    return {"velocidade_base": velocidade_base, "trechos": trechos, "revisado": False}


def validar(direcao, n_blocos):
    """Confere: intenções conhecidas, cada bloco em exatamente um trecho e em ordem, faixas e pausas; e que a narração
    NÃO use os mesmos parâmetros do começo ao fim (exigência do diretor), quando houver mais de um trecho."""
    erros = []; vistos = []
    for t in direcao["trechos"]:
        if t["intencao"] not in INTENCOES:
            erros.append(f"intenção desconhecida: {t['intencao']}")
        if not 0.5 <= t["speed"] <= 2.0:
            erros.append(f"velocidade fora da faixa: {t['speed']}")
        if t["pausa_antes"] >= 0.8 or t["pausa_depois"] >= 0.8:
            erros.append("pausa dirigida ≥ 0,8 s (proibida pelo pipeline)")
        vistos += t["blocos"]
    if vistos != list(range(n_blocos)):
        erros.append("blocos faltando, repetidos ou fora de ordem nos trechos")
    sets = {(t["speed"], t["vol"], t["pitch"], t.get("emocao_proposta")) for t in direcao["trechos"]}
    if len(direcao["trechos"]) > 1 and len(sets) == 1:
        erros.append("todos os trechos com os mesmos parâmetros: a direção precisa variar a interpretação")
    return erros


def folha(direcao, cfg):
    """Folha de direção (texto) com caracteres e custo estimado de cada trecho — para o diretor aprovar ANTES da síntese."""
    from minimax import contar_caracteres, custo_estimado
    linhas = ["| # | Cena | Intenção | Fala | Vel. | Vol. | Tom | Emoção proposta | Pausas (antes/depois) | Caract. | Custo est. (US$) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    tot = 0
    for i, t in enumerate(direcao["trechos"], 1):
        n = contar_caracteres(t["fala"]); tot += n
        emo = t.get("emocao_proposta") or "automática"
        if t.get("emocao_proposta") and t["emocao_proposta"] not in cfg["emocoes_aceitas_pela_voz"]:
            emo += " (ainda não confirmada → vai sem emoção)"
        linhas.append(f"| {i} | {t['cena']} | {NOMES[t['intencao']]} | {t['fala']} | {t['speed']} | {t['vol']} | {t['pitch']:+d} | {emo} | "
                      f"{t['pausa_antes']:.2f} / {t['pausa_depois']:.2f} s | {n} | {custo_estimado(n, cfg):.4f} |")
    linhas.append(f"\n**Total:** {tot} caracteres · ~US$ {custo_estimado(tot, cfg):.4f} (preço de referência, não confirmado no painel)")
    return "\n".join(linhas), tot
