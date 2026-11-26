#!/usr/bin/env python3
"""Geração da narração do Modo Curioso (MiniMax), com direção por trecho e proteção de créditos.

Comandos (SEM `--autorizado` nada é enviado: só simulação com contagem de caracteres e custo):
  gerar.py simular <roteiro.json> [--direcao direcao.json]       folha de direção + caracteres + custo (sem rede)
  gerar.py teste <T2|T3|T4> [--autorizado ID]                     testes definidos em testes/planos.json
  gerar.py vozes --autorizado T1                                  consulta de vozes da conta (sem síntese)
  gerar.py gerar <roteiro.json> --direcao direcao.json --saida <pasta> --autorizado ID

Saídas de `gerar` (na pasta indicada): trechos/*.mp3 · cenas/*.mp3 · voz.mp3 (consolidada) · voz.wav (48 kHz, para a
mixagem) · voz_palavras.json (início/fim de cada palavra) · voz_registro.json (modelo, voz, parâmetros, consumo).
A montagem NUNCA acelera o áudio: só corta o silêncio das pontas de cada trecho e insere as pausas dirigidas.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import minimax as MM          # noqa: E402
import direcao as DR          # noqa: E402

SR = 48000


# ------------------------------------------------------------------ áudio
def decodificar(mp3):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"],
                         input=mp3, capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()


def codificar_mp3(y, caminho, kbps=192):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0", "-codec:a", "libmp3lame",
                    "-b:a", f"{kbps}k", str(caminho)], input=np.ascontiguousarray(y, np.float32).tobytes(), check=True)


def gravar_wav(y, caminho):
    import soundfile as sf
    sf.write(caminho, y, SR, subtype="PCM_24")


def aparar(y, limiar_db=-40.0, folga_s=0.02):
    """Corta o silêncio das pontas (não mexe no meio nem na velocidade). Devolve (áudio, segundos cortados no início)."""
    if not len(y):
        return y, 0.0
    env = np.convolve(np.abs(y), np.ones(480) / 480, "same"); lim = 10 ** (limiar_db / 20) * max(env.max(), 1e-9)
    on = np.where(env > lim)[0]
    if not len(on):
        return y, 0.0
    a = max(0, on[0] - int(folga_s * SR)); b = min(len(y), on[-1] + int(folga_s * SR))
    return y[a:b], a / SR


def maior_pausa_interna(y, limiar_db=-35.0):
    env = np.convolve(np.abs(y), np.ones(480) / 480, "same"); lim = 10 ** (limiar_db / 20) * max(env.max(), 1e-9)
    quieto = env < lim; maior = cur = 0; on = np.where(~quieto)[0]
    if not len(on):
        return 0.0
    for q in quieto[on[0]:on[-1]]:
        cur = cur + 1 if q else 0; maior = max(maior, cur)
    return maior / SR


# ------------------------------------------------------------------ tempos das palavras
def _palavras_das_legendas(legendas, deslocamento):
    """Aceita a lista de palavras da MiniMax (formato confirmado no T2). Tolerante: itens com texto e início/fim em ms."""
    if not isinstance(legendas, list):
        return None
    out = []
    for it in legendas:
        if not isinstance(it, dict):
            return None
        txt = it.get("text") or it.get("word"); ini = it.get("time_begin", it.get("start")); fim = it.get("time_end", it.get("end"))
        if txt is None or ini is None or fim is None:
            return None
        out.append({"w": txt.strip(), "ini": round(ini / 1000 - deslocamento, 3), "fim": round(fim / 1000 - deslocamento, 3)})
    return out


def _proporcional(blocos_txt, ini, fim):
    """Plano B: divide a duração do trecho pelos blocos e palavras na proporção das letras (como o piloto 01)."""
    palavras = [(bi, w) for bi, t in blocos_txt for w in t.split()]; letras = sum(len(w) for _, w in palavras) or 1
    out, acc = [], ini
    for bi, w in palavras:
        d = (fim - ini) * len(w) / letras; out.append({"w": w, "ini": round(acc, 3), "fim": round(acc + d, 3), "_bloco": bi}); acc += d
    return out


# ------------------------------------------------------------------ geração
def gerar(roteiro, direcao, saida, cliente, autorizacao):
    blocos = [b for _, b in DR._blocos(roteiro)]; cenas_de = [c for c, _ in DR._blocos(roteiro)]
    erros = DR.validar(direcao, len(blocos))
    if erros:
        raise MM.ErroNarracao("direção inválida: " + "; ".join(erros))
    saida = Path(saida); (saida / "trechos").mkdir(parents=True, exist_ok=True); (saida / "cenas").mkdir(exist_ok=True)
    cfg = cliente.cfg
    # contagem total ANTES de qualquer chamada; a execução inteira tem de caber na autorização
    payloads = []
    for t in direcao["trechos"]:
        emo = t.get("emocao_proposta") if MM.emocao_liberada(t.get("emocao_proposta"), cfg) else None
        payloads.append(MM.montar_payload(t["fala"], cfg, speed=t["speed"], vol=t["vol"], pitch=t["pitch"], emotion=emo))
    novos = [p for p in payloads if not (cliente.cache / f"{MM.chave_cache(p)}.mp3").exists()]
    cliente.verificar_orcamento(autorizacao, sum(MM.contar_caracteres(p["text"]) for p in novos))
    partes, palavras, reg_trechos, t_cur = [], [], [], 0.0
    cena_trechos = {}
    for i, (t, p) in enumerate(zip(direcao["trechos"], payloads)):
        r = cliente.sintetizar(p, autorizacao, f"trecho {i + 1}: {t['intencao']}")
        y, corte = aparar(decodificar(r["audio"]))
        if t["pausa_antes"] and partes:
            partes.append(np.zeros(int(t["pausa_antes"] * SR), np.float32)); t_cur += t["pausa_antes"]
        ini, fim = t_cur, t_cur + len(y) / SR
        pal = _palavras_das_legendas(r["legendas"], corte)
        metodo = "legendas da MiniMax" if pal else "proporcional às letras (plano B)"
        if pal:
            pal = [{**w, "ini": round(ini + w["ini"], 3), "fim": round(ini + w["fim"], 3)} for w in pal]
        else:
            pal = _proporcional([(k, blocos[k]["txt"]) for k in t["blocos"]], ini, fim)
        palavras += [{**w, "trecho": i + 1, "cena": t["cena"]} for w in pal]
        partes.append(y); codificar_mp3(y, saida / "trechos" / f"trecho_{i + 1:02d}.mp3")
        cena_trechos.setdefault(t["cena"], []).append((y, t))
        t_cur = fim
        if t["pausa_depois"] and i < len(direcao["trechos"]) - 1:
            partes.append(np.zeros(int(t["pausa_depois"] * SR), np.float32)); t_cur += t["pausa_depois"]
        reg_trechos.append({"trecho": i + 1, "cena": t["cena"], "intencao": t["intencao"], "fala": t["fala"], "speed": p["voice_setting"]["speed"],
                            "vol": p["voice_setting"]["vol"], "pitch": p["voice_setting"]["pitch"], "emocao": p["voice_setting"].get("emotion"),
                            "pausa_antes": t["pausa_antes"], "pausa_depois": t["pausa_depois"], "ini": round(ini, 3), "fim": round(fim, 3),
                            "metodo_tempos": metodo, "do_cache": r["do_cache"], "caracteres": MM.contar_caracteres(p["text"]),
                            "caracteres_cobrados": (r["meta"].get("extra_info") or {}).get("usage_characters"), "trace_id": r["meta"].get("trace_id")})
    voz = np.concatenate(partes)
    for cena, itens in cena_trechos.items():                    # áudio por cena: os trechos da cena com as pausas internas
        seq = []
        for k, (y, t) in enumerate(itens):
            if k and t["pausa_antes"]:
                seq.append(np.zeros(int(t["pausa_antes"] * SR), np.float32))
            seq.append(y)
            if k < len(itens) - 1 and t["pausa_depois"]:
                seq.append(np.zeros(int(t["pausa_depois"] * SR), np.float32))
        codificar_mp3(np.concatenate(seq), saida / "cenas" / f"{cena}.mp3")
    codificar_mp3(voz, saida / "voz.mp3"); gravar_wav(voz, saida / "voz.wav")
    dur = len(voz) / SR
    (saida / "voz_palavras.json").write_text(json.dumps({"duracao_voz": round(dur, 3), "palavras": palavras}, ensure_ascii=False, indent=1))
    registro = {"fornecedor": cfg["fornecedor"], "modelo": cfg["modelo"], "voice_id": cfg["voz"]["voice_id"], "status_da_voz": cfg["voz"]["status"],
                "velocidade_base": direcao["velocidade_base"], "direcao_revisada": direcao.get("revisado", False), "duracao_voz": round(dur, 3),
                "maior_pausa_interna_s": round(maior_pausa_interna(voz), 3), "aceleracao_pos_producao": "nenhuma (proibida)",
                "trechos": reg_trechos, "caracteres_total": sum(x["caracteres"] for x in reg_trechos),
                "caracteres_novos_pagos": sum(x["caracteres"] for x in reg_trechos if not x["do_cache"])}
    (saida / "voz_registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=1))
    return registro


# ------------------------------------------------------------------ testes T2–T4 (definidos em testes/planos.json)
def plano_teste(nome):
    return json.loads((AQUI / "testes" / "planos.json").read_text())[nome]


def simular_teste(nome, cfg):
    pl = plano_teste(nome); itens = []
    for v in pl["versoes"]:
        p = MM.montar_payload(v["texto"], cfg, speed=v.get("speed"), vol=v.get("vol"), pitch=v.get("pitch"), emotion=v.get("emotion"))
        itens.append({"id": v["id"], "texto": v["texto"], "caracteres": MM.contar_caracteres(p["text"]), "parametros": p["voice_setting"],
                      "cache": MM.chave_cache(p)})
    tot = sum(i["caracteres"] for i in itens)
    return {"teste": nome, "objetivo": pl["objetivo"], "itens": itens, "caracteres_total": tot, "custo_estimado_usd": MM.custo_estimado(tot, cfg)}


def executar_teste(nome, cliente, autorizacao):
    pl = plano_teste(nome); out = []; dest = AQUI / "testes" / "saidas"; dest.mkdir(parents=True, exist_ok=True)
    payloads = [(v, MM.montar_payload(v["texto"], cliente.cfg, speed=v.get("speed"), vol=v.get("vol"), pitch=v.get("pitch"),
                                      emotion=v.get("emotion"))) for v in pl["versoes"]]
    novos = [p for _, p in payloads if not (cliente.cache / f"{MM.chave_cache(p)}.mp3").exists()]
    cliente.verificar_orcamento(autorizacao, sum(MM.contar_caracteres(p["text"]) for p in novos))   # o teste inteiro cabe, ou nada sai
    for v, p in payloads:
        r = cliente.sintetizar(p, autorizacao, f"{nome} {v['id']}: {pl['objetivo']}")
        arq = dest / f"{nome}_{v['id']}.mp3"; arq.write_bytes(r["audio"])
        y = decodificar(r["audio"]); dur = len(y) / SR
        out.append({"id": v["id"], "arquivo": str(arq.relative_to(AQUI)), "duracao_s": round(dur, 3),
                    "palavras_por_min": round(len(v["texto"].split()) / dur * 60, 1) if dur else None, "do_cache": r["do_cache"],
                    "caracteres_cobrados": (r["meta"].get("extra_info") or {}).get("usage_characters"),
                    "tem_legendas_por_palavra": isinstance(r["legendas"], list), "legendas_tipo": type(r["legendas"]).__name__})
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    cfg = MM.carregar_config(); aut = a[a.index("--autorizado") + 1] if "--autorizado" in a else None
    try:
        if a[0] == "simular":
            rot = json.loads(Path(a[1]).read_text())
            d = json.loads(Path(a[a.index("--direcao") + 1]).read_text()) if "--direcao" in a else DR.propor(rot)
            texto, tot = DR.folha(d, cfg); print(texto)
            n = len(list(DR._blocos(rot))); e = DR.validar(d, n); print("\nvalidação:", "ok" if not e else e)
        elif a[0] == "teste":
            print(json.dumps(simular_teste(a[1], cfg), ensure_ascii=False, indent=1))
            if aut:
                print(json.dumps(executar_teste(a[1], MM.Cliente(cfg), aut), ensure_ascii=False, indent=1))
            else:
                print("\nSIMULAÇÃO: nada foi enviado (falta --autorizado)")
        elif a[0] == "vozes":
            if not aut:
                print("SIMULAÇÃO: a consulta de vozes não roda sem --autorizado T1"); sys.exit(0)
            nome = a[a.index("--nome") + 1] if "--nome" in a else None
            motivo = "T1: validar chave, região e existência da voz (sem síntese)" + (f"; procurar o nome '{nome}'" if nome else "")
            print(json.dumps(MM.Cliente(cfg).consultar_vozes(aut, motivo=motivo, nome=nome), ensure_ascii=False, indent=1))
        elif a[0] == "gerar":
            rot = json.loads(Path(a[1]).read_text()); d = json.loads(Path(a[a.index("--direcao") + 1]).read_text())
            if not aut:
                texto, tot = DR.folha(d, cfg); print(texto); print("\nSIMULAÇÃO: nada foi enviado (falta --autorizado)"); sys.exit(0)
            print(json.dumps(gerar(rot, d, a[a.index("--saida") + 1], MM.Cliente(cfg), aut), ensure_ascii=False, indent=1))
    except MM.ErroNarracao as e:
        print(f"PARADO: {e}"); sys.exit(2)
