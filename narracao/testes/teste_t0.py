#!/usr/bin/env python3
"""T0 — testes SEM REDE e SEM CRÉDITOS. A MiniMax é substituída por uma sessão FALSA local (gera um tom com o ffmpeg).
Tudo roda numa pasta temporária: o orçamento e o registro de consumo verdadeiros não são tocados.

Confere: validação dos parâmetros; voz proibida recusada; contagem; recusa sem autorização e acima do teto (sem chamar a
rede); cache (a mesma combinação não chama de novo); erro da API → para, sem nova tentativa; falha de rede → para e debita
por segurança; a chave nunca aparece nos arquivos; diretor de narração (classificação, trechos, variação obrigatória);
geração completa (trechos, cenas, consolidada, voz.wav 48 kHz, voz_palavras.json, registro) sem aceleração.
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
import minimax as MM, direcao as DR, gerar as GR   # noqa: E402

CHAVE_FALSA = "sk-TESTE-nao-e-real-0123456789-SEGREDO"
res = {}


class Resp:
    def __init__(self, status, corpo):
        self.status_code = status; self._c = corpo

    def json(self):
        if isinstance(self._c, Exception):
            raise self._c
        return self._c


class SessaoFalsa:
    """Imita o T2A V2: devolve áudio (hex), usage_characters e legendas por palavra. Pode simular erro ou queda de rede."""
    def __init__(self, modo="ok", legendas=True):
        self.chamadas = 0; self.modo = modo; self.legendas = legendas; self.headers_vistos = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.chamadas += 1; self.headers_vistos.append(headers)
        if self.modo == "rede":
            raise TimeoutError("simulado")
        if self.modo == "erro":
            return Resp(200, {"base_resp": {"status_code": 2013, "status_msg": "invalid params"}, "trace_id": "t-falso"})
        txt = json["text"]; vel = json["voice_setting"]["speed"]; dur = max(0.3, 0.065 * len(txt) / vel)
        mp3 = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d=0.15", "-f", "lavfi", "-i",
                              f"sine=frequency=220:sample_rate=44100:duration={dur}", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=0.15",
                              "-filter_complex", "[0][1][2]concat=n=3:v=0:a=1", "-f", "mp3", "pipe:1"], capture_output=True, check=True).stdout
        palavras = MM.PAUSA.sub(" ", txt).split(); t = 150.0; leg = []
        for w in palavras:
            d = dur * 1000 * len(w) / max(1, sum(len(x) for x in palavras)); leg.append({"text": w, "time_begin": t, "time_end": t + d}); t += d
        return Resp(200, {"data": {"audio": mp3.hex(), "status": 2, **({"subtitle_file": leg} if self.legendas else {})},
                          "extra_info": {"usage_characters": len(txt), "audio_length": int(dur * 1000)}, "trace_id": "t-falso",
                          "base_resp": {"status_code": 0, "status_msg": "success"}})


def pasta_teste(autorizacoes):
    d = Path(tempfile.mkdtemp(prefix="narracao_t0_"))
    shutil.copy(RAIZ / "config_voz.json", d / "config_voz.json")
    (d / "orcamento.json").write_text(json.dumps({"teto_total_caracteres": 1500, "consumido_caracteres": 0, "autorizacoes": autorizacoes}))
    (d / "consumo.jsonl").write_text("")
    return d


def ok(nome, cond, info=""):
    res[nome] = {"ok": bool(cond), **({"info": info} if info else {})}
    print(("OK   " if cond else "FALHA"), nome, info)


def main():
    os.environ["MINIMAX_API_KEY"] = CHAVE_FALSA
    cfg = MM.carregar_config()
    # 1. validação
    falhas = 0
    for kw in ({"speed": 2.5}, {"speed": 0.4}, {"vol": 0}, {"vol": 11}, {"pitch": 13}, {"emotion": "raiva"}):
        try:
            MM.montar_payload("Teste.", cfg, **kw)
        except MM.ErroNarracao:
            falhas += 1
    ok("validacao_recusa_fora_da_faixa", falhas == 6, f"{falhas}/6 recusados")
    try:
        MM.montar_payload("Teste <#1,5#> errado.", cfg); ok("pausa_malformada_recusada", False)
    except MM.ErroNarracao:
        ok("pausa_malformada_recusada", True)
    VOZ = "Portuguese_CaptivatingStoryteller"; CLONE = "moss_audio_f28d61d6-e90b-11f1-b491-2a43200a7deb"
    c2 = json.loads(json.dumps(cfg)); c2["voz"]["voice_id"] = CLONE          # o clone retirado tem de ser recusado ANTES do envio
    try:
        MM.montar_payload("Teste.", c2); ok("voz_proibida_recusada", False)
    except MM.ErroNarracao as e:
        ok("voz_proibida_recusada", "proibida" in str(e) and CLONE in cfg["vozes_proibidas"])
    p = MM.montar_payload("Olá, Modo Curioso.", cfg)
    ok("voz_principal_sem_troca_automatica", cfg["voz"]["voice_id"] == VOZ and cfg["troca_automatica_de_voz"] is False
       and not cfg["vozes_alternativas"] and p["voice_setting"]["voice_id"] == VOZ)
    ok("clone_nunca_no_payload", CLONE not in json.dumps(p) and "ttv-voice" not in json.dumps(p))
    ok("payload_basico", p["model"] == "speech-2.8-hd" and p["voice_setting"]["voice_id"] == VOZ
       and p["subtitle_enable"] and p["language_boost"] == "Portuguese" and "emotion" not in p["voice_setting"], json.dumps(p["voice_setting"]))
    ok("contagem", MM.contar_caracteres("Olá, Modo Curioso.") == 18)

    # 2. orçamento: sem autorização e acima do teto → nada sai
    d = pasta_teste({}); s = SessaoFalsa(); cl = MM.Cliente(MM.carregar_config(d / "config_voz.json"), pasta=d, sessao=s)
    try:
        cl.sintetizar(p, "T2", "teste"); ok("recusa_sem_autorizacao", False)
    except MM.RecusaOrcamento:
        ok("recusa_sem_autorizacao", s.chamadas == 0, "0 chamadas")
    d = pasta_teste({"T2": {"max_caracteres": 10}}); s = SessaoFalsa(); cl = MM.Cliente(MM.carregar_config(d / "config_voz.json"), pasta=d, sessao=s)
    try:
        cl.sintetizar(p, "T2", "teste"); ok("recusa_acima_do_limite", False)
    except MM.RecusaOrcamento:
        ok("recusa_acima_do_limite", s.chamadas == 0, "18 > 10: 0 chamadas")

    # 3. sucesso + cache + registro + débito
    d = pasta_teste({"T2": {"max_caracteres": 18}}); s = SessaoFalsa(); cl = MM.Cliente(MM.carregar_config(d / "config_voz.json"), pasta=d, sessao=s)
    r1 = cl.sintetizar(p, "T2", "teste"); r2 = cl.sintetizar(p, "T2", "teste")
    o = json.loads((d / "orcamento.json").read_text()); reg = [json.loads(x) for x in (d / "consumo.jsonl").read_text().splitlines()]
    ok("cache_nao_repete_chamada", s.chamadas == 1 and r2["do_cache"] and r1["audio"] == r2["audio"], f"{s.chamadas} chamada")
    ok("debito_e_registro", o["consumido_caracteres"] == 18 and len(reg) == 1 and reg[0]["caracteres_cobrados"] == 18
       and reg[0]["voice_id"] and reg[0]["motivo"] and reg[0]["resultado"] == "ok", json.dumps(reg[0], ensure_ascii=False)[:160])
    ok("cabecalho_com_chave_so_na_requisicao", s.headers_vistos[0]["Authorization"] == f"Bearer {CHAVE_FALSA}")

    # 4. erro da API → para, sem nova tentativa
    d = pasta_teste({"T2": {"max_caracteres": 100}}); s = SessaoFalsa("erro"); cl = MM.Cliente(MM.carregar_config(d / "config_voz.json"), pasta=d, sessao=s)
    try:
        cl.sintetizar(p, "T2", "teste"); ok("erro_api_para", False)
    except MM.ErroNarracao as e:
        ok("erro_api_para", s.chamadas == 1 and "2013" in str(e), str(e)[:90])
    # 5. queda de rede → para e debita por segurança
    d = pasta_teste({"T2": {"max_caracteres": 100}}); s = SessaoFalsa("rede"); cl = MM.Cliente(MM.carregar_config(d / "config_voz.json"), pasta=d, sessao=s)
    try:
        cl.sintetizar(p, "T2", "teste"); ok("queda_de_rede_para", False)
    except MM.ErroNarracao as e:
        o = json.loads((d / "orcamento.json").read_text())
        ok("queda_de_rede_para", s.chamadas == 1 and o["consumido_caracteres"] == 18, "debitado por segurança, sem nova tentativa")

    # 6. diretor de narração
    rot = json.loads((AQUI / "roteiro_teste.json").read_text())
    dr = DR.propor(rot); n = len(list(DR._blocos(rot)))
    intents = [t["intencao"] for t in dr["trechos"]]
    ok("direcao_varia_parametros", not DR.validar(dr, n) and len({(t["speed"], t["vol"], t["pitch"]) for t in dr["trechos"]}) > 1,
       f"{len(dr['trechos'])} trechos: {intents}")
    texto, tot = DR.folha(dr, cfg)
    ok("folha_de_direcao", tot == sum(len(t["fala"]) for t in dr["trechos"]), f"{tot} caracteres")
    ok("classificacao_exemplos", DR.classificar("E se você descobrisse isso?")[0] == "curiosidade" and DR.classificar("Até que o celular vibrou...")[0] == "suspense"
       and DR.classificar("Ninguém sabe o segredo.")[0] == "misterio" and DR.classificar("A água ferve a 100 graus.")[0] == "explicacao")

    # 7. geração completa (com e sem legendas da API)
    for leg in (True, False):
        d = pasta_teste({"T5": {"max_caracteres": 1000}}); s = SessaoFalsa(legendas=leg); cl = MM.Cliente(MM.carregar_config(d / "config_voz.json"), pasta=d, sessao=s)
        sai = d / "saida"; reg = GR.gerar(rot, dr, sai, cl, "T5")
        import soundfile as sf
        info = sf.info(sai / "voz.wav"); pal = json.loads((sai / "voz_palavras.json").read_text())
        mono = all(pal["palavras"][i]["ini"] <= pal["palavras"][i]["fim"] <= pal["palavras"][i + 1]["ini"] + 1e-3 for i in range(len(pal["palavras"]) - 1))
        soma = sum(t["fim"] - t["ini"] for t in reg["trechos"]); pausas = 0.0
        for i, t in enumerate(dr["trechos"]):
            pausas += (t["pausa_antes"] if i else 0) + (t["pausa_depois"] if i < len(dr["trechos"]) - 1 else 0)
        arquivos = sorted(x.name for x in sai.iterdir())
        ok(f"geracao_completa_legendas_{'api' if leg else 'plano_b'}",
           info.samplerate == 48000 and mono and abs(reg["duracao_voz"] - (soma + pausas)) < 0.01 and len(list((sai / "cenas").iterdir())) == len({t["cena"] for t in dr["trechos"]})
           and pal["palavras"][-1]["fim"] <= reg["duracao_voz"] + 1e-3 and reg["aceleracao_pos_producao"].startswith("nenhuma"),
           f"{arquivos}; {len(pal['palavras'])} palavras; duração = trechos + pausas ({reg['duracao_voz']} s); tempos: {reg['trechos'][0]['metodo_tempos']}")
        if leg:
            r2 = GR.gerar(rot, dr, d / "saida2", cl, "T5")
            ok("geracao_repetida_usa_cache", r2["caracteres_novos_pagos"] == 0 and s.chamadas == len(dr["trechos"]), f"{s.chamadas} chamadas no total")

    # 8. a chave nunca aparece em arquivo nenhum (inclusive cache, registro, saídas)
    vazou = []
    for base in [Path(tempfile.gettempdir())]:
        for f in base.glob("narracao_t0_*/**/*"):
            if f.is_file() and CHAVE_FALSA.encode() in f.read_bytes():
                vazou.append(str(f))
    for f in RAIZ.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".jsonl", ".py", ".md") and CHAVE_FALSA.encode() in f.read_bytes() and f.name != "teste_t0.py":
            vazou.append(str(f))
    ok("chave_nunca_gravada", not vazou, f"{len(vazou)} arquivo(s) com a chave")

    # 9. simulação real dos testes T2–T4 (contagem exata, sem rede)
    sims = {t: GR.simular_teste(t, cfg) for t in ("T2", "T3", "T4")}
    ok("simulacao_T2_T4", all(s_["caracteres_total"] > 0 for s_ in sims.values()),
       ", ".join(f"{t}: {s_['caracteres_total']} caract. (~US$ {s_['custo_estimado_usd']})" for t, s_ in sims.items()))
    orc_real = json.loads((RAIZ / "orcamento.json").read_text()); reg_real = (RAIZ / "consumo.jsonl").read_text()
    sintese_autorizada = {k: v for k, v in orc_real["autorizacoes"].items() if v.get("max_caracteres", 0) > 0}
    sinteses = [json.loads(l) for l in reg_real.splitlines() if l.strip() and "modelo" in json.loads(l)]
    debitado = sum(r.get("caracteres_cobrados") or r.get("caracteres_enviados", 0) for r in sinteses)
    sem_aut = [r["autorizacao"] for r in sinteses if r["autorizacao"] not in orc_real["autorizacoes"]]
    ok("orcamento_real_coerente", orc_real["consumido_caracteres"] == debitado and orc_real["consumido_caracteres"] <= orc_real["teto_total_caracteres"]
       and not sem_aut, f"consumido {orc_real['consumido_caracteres']} = debitado no registro {debitado}; "
       f"{len(sinteses)} chamada(s) de síntese, todas com autorização registrada ({list(sintese_autorizada)})")
    for f in Path(tempfile.gettempdir()).glob("narracao_t0_*"):
        shutil.rmtree(f, ignore_errors=True)
    falhou = [k for k, v in res.items() if not v["ok"]]
    (AQUI / "saidas" / "t0_resultado.json").write_text(json.dumps({"resultado": "OK" if not falhou else "FALHA", "falhas": falhou, "testes": res,
                                                                   "chamadas_reais_a_minimax": 0, "creditos_gastos": 0}, ensure_ascii=False, indent=1))
    print("\nT0:", "TUDO OK" if not falhou else f"FALHAS: {falhou}", "· chamadas reais à MiniMax: 0 · créditos: 0")
    return 0 if not falhou else 1


if __name__ == "__main__":
    sys.exit(main())
