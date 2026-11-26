"""Cliente do MiniMax T2A V2 (síntese de voz) com PROTEÇÃO DE CRÉDITOS e DA CHAVE.

Regras (do diretor, obrigatórias):
- nenhuma síntese sem autorização registrada em `orcamento.json` (por teste/execução, com teto de caracteres);
- contagem de caracteres ANTES de cada chamada; a chamada é recusada antes de sair se passar do teto;
- cache por (modelo, voz, texto, todos os parâmetros): o que já foi gerado nunca é pago de novo;
- nenhuma nova tentativa automática: em qualquer falha registra e PARA (pode ter havido cobrança);
- registro de cada chamada em `consumo.jsonl` (caracteres enviados e cobrados, modelo, voz, motivo, resultado);
- a chave nunca é gravada, impressa ou incluída em mensagens de erro.

Chave: lida de `MINIMAX_API_KEY` (variável de ambiente). Se ela não existir e o ambiente usar um SEGREDO DE REDE, o
proxy do ambiente insere a chave verdadeira na chamada; o código manda um valor de mentira (`MINIMAX_SEGREDO_DE_REDE=1`).
"""
import datetime as _dt, hashlib, json, os, re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PAUSA = re.compile(r"<#(\d{1,2}(?:\.\d{1,2})?)#>")
# códigos de erro (espelho da documentação oficial, errors.md): o que significa e se adianta tentar de novo
ERROS = {1000: "erro desconhecido do sistema", 1001: "tempo esgotado no servidor", 1002: "limite de requisições (rate limit)",
         1004: "não autorizado: chave inválida ou de outra região", 1008: "saldo insuficiente", 1024: "erro interno",
         1026: "texto de entrada marcado como sensível", 1027: "saída marcada como sensível", 1033: "erro em serviço dependente",
         1041: "limite de conexões", 1042: "caracteres invisíveis/ilegais acima de 10 %", 2013: "parâmetros inválidos",
         2042: "sem permissão para este voice_id", 2045: "rajada de requisições", 2049: "chave de API inválida",
         2056: "limite do plano atingido"}


class ErroNarracao(Exception):
    """Erro com mensagem já limpa (sem a chave)."""


class RecusaOrcamento(ErroNarracao):
    pass


def _agora():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def carregar_config(caminho=None):
    return json.loads(Path(caminho or AQUI / "config_voz.json").read_text())


def contar_caracteres(texto):
    """Contagem local, conservadora: conta TUDO (inclusive as marcas de pausa <#x#>), antes de qualquer chamada."""
    return len(texto)


def custo_estimado(caracteres, cfg):
    return round(caracteres * cfg["preco_referencia_usd_por_milhao_caracteres"] / 1e6, 5)


# ------------------------------------------------------------------ requisição
def montar_payload(texto, cfg, speed=None, vol=None, pitch=None, emotion=None, modelo=None, tempos=True):
    """Monta e VALIDA a requisição. Recusa (antes de gastar) parâmetros fora das faixas documentadas, voz proibida,
    emoção não aceita pela voz e marcas de pausa malformadas."""
    modelo = modelo or cfg["modelo"]; vid = cfg["voz"]["voice_id"]; lim = cfg["limites"]; p = cfg["padrao_voz"]
    if modelo not in cfg["modelos_permitidos"]:
        raise ErroNarracao(f"modelo '{modelo}' não está na lista permitida {cfg['modelos_permitidos']}")
    if vid in cfg["vozes_proibidas"]:
        raise ErroNarracao(f"voz proibida: {cfg['vozes_proibidas'][vid]}")
    if not texto or not texto.strip():
        raise ErroNarracao("texto vazio")
    if len(texto) > lim["texto_max_caracteres"]:
        raise ErroNarracao(f"texto com {len(texto)} caracteres (máximo {lim['texto_max_caracteres']})")
    for m in re.finditer(r"<#[^>]*#>", texto):
        if not PAUSA.fullmatch(m.group(0)) or not 0.01 <= float(PAUSA.fullmatch(m.group(0)).group(1)) <= 99.99:
            raise ErroNarracao(f"marca de pausa inválida: {m.group(0)} (use <#0.25#>, de 0,01 a 99,99 s)")
    speed = p["speed"] if speed is None else float(speed); vol = p["vol"] if vol is None else float(vol)
    pitch = p["pitch"] if pitch is None else int(pitch)
    if not lim["speed"][0] <= speed <= lim["speed"][1]:
        raise ErroNarracao(f"velocidade {speed} fora de {lim['speed']}")
    if not 0 < vol <= lim["vol_max"]:
        raise ErroNarracao(f"volume {vol} fora de (0, {lim['vol_max']}]")
    if not lim["pitch"][0] <= pitch <= lim["pitch"][1]:
        raise ErroNarracao(f"tom {pitch} fora de {lim['pitch']}")
    vs = {"voice_id": vid, "speed": round(speed, 3), "vol": round(vol, 3), "pitch": pitch}
    if emotion:
        if emotion not in cfg["emocoes_documentadas"]:
            raise ErroNarracao(f"emoção '{emotion}' não documentada")
        vs["emotion"] = emotion
    payload = {"model": modelo, "text": texto, "stream": False, "voice_setting": vs, "audio_setting": dict(cfg["audio"]),
               "language_boost": cfg["language_boost"], "output_format": cfg["output_format"]}
    if tempos and cfg["tempos_por_palavra"]["subtitle_enable"]:
        payload["subtitle_enable"] = True; payload["subtitle_type"] = cfg["tempos_por_palavra"]["subtitle_type"]
    return payload


def emocao_liberada(emotion, cfg):
    """Emoção só entra numa geração depois que o teste a confirmou para ESTA voz (lista 'emocoes_aceitas_pela_voz')."""
    return emotion in cfg["emocoes_aceitas_pela_voz"]


def chave_cache(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


# ------------------------------------------------------------------ cliente
class Cliente:
    """Toda chamada passa por: contagem → orçamento → cache → (só então) rede → registro."""

    def __init__(self, cfg=None, pasta=AQUI, sessao=None):
        self.cfg = cfg or carregar_config(); self.pasta = Path(pasta)
        self.cache = self.pasta / "cache"; self.orc_path = self.pasta / "orcamento.json"; self.reg_path = self.pasta / "consumo.jsonl"
        self.sessao = sessao                              # testes injetam uma sessão falsa; None = requests de verdade

    # ---- chave (nunca sai daqui)
    def _chave(self):
        k = os.environ.get("MINIMAX_API_KEY", "").strip()
        if k:
            return k
        if os.environ.get("MINIMAX_SEGREDO_DE_REDE") == "1":
            return "segredo-de-rede"                      # o proxy do ambiente troca pelo valor verdadeiro
        raise ErroNarracao("chave ausente: defina MINIMAX_API_KEY fora do Git ou configure o segredo de rede do ambiente")

    def _limpar(self, texto):
        k = os.environ.get("MINIMAX_API_KEY", "")
        s = str(texto)
        return s.replace(k, "[CHAVE OCULTA]") if k else s

    # ---- orçamento
    def orcamento(self):
        return json.loads(self.orc_path.read_text())

    def verificar_orcamento(self, autorizacao, caracteres):
        o = self.orcamento(); a = o["autorizacoes"].get(autorizacao)
        if a is None:
            raise RecusaOrcamento(f"sem autorização registrada para '{autorizacao}' em orcamento.json: nada foi enviado")
        if o["consumido_caracteres"] + caracteres > o["teto_total_caracteres"]:
            raise RecusaOrcamento(f"passaria do teto total ({o['consumido_caracteres']} + {caracteres} > {o['teto_total_caracteres']}): nada foi enviado")
        if a.get("usado", 0) + caracteres > a["max_caracteres"]:
            raise RecusaOrcamento(f"passaria do limite autorizado para '{autorizacao}' ({a.get('usado', 0)} + {caracteres} > {a['max_caracteres']}): nada foi enviado")

    def _debitar(self, autorizacao, caracteres):
        o = self.orcamento(); o["consumido_caracteres"] += caracteres
        a = o["autorizacoes"].setdefault(autorizacao, {"max_caracteres": 0}); a["usado"] = a.get("usado", 0) + caracteres
        self.orc_path.write_text(json.dumps(o, ensure_ascii=False, indent=1) + "\n")

    def _registrar(self, **campos):
        campos = {"data": _agora(), **campos}
        with open(self.reg_path, "a") as f:
            f.write(self._limpar(json.dumps(campos, ensure_ascii=False)) + "\n")

    def _post(self, caminho, corpo):
        url = self.cfg["host"] + caminho
        if self.cfg.get("enviar_group_id"):
            url += f"?GroupId={self.cfg['group_id']}"
        headers = {"Authorization": f"Bearer {self._chave()}", "Content-Type": "application/json"}
        if self.sessao is not None:
            return self.sessao.post(url, headers=headers, json=corpo, timeout=self.cfg["timeout_s"])
        import requests
        return requests.post(url, headers=headers, json=corpo, timeout=self.cfg["timeout_s"])

    # ---- síntese
    def sintetizar(self, payload, autorizacao, motivo):
        """Devolve {"audio": bytes, "legendas": ..., "meta": ..., "do_cache": bool}. Levanta erro (e PARA) em qualquer falha."""
        cid = chave_cache(payload); mp3 = self.cache / f"{cid}.mp3"; meta_p = self.cache / f"{cid}.json"
        if mp3.exists() and meta_p.exists():
            meta = json.loads(meta_p.read_text())
            return {"audio": mp3.read_bytes(), "legendas": meta.get("legendas"), "meta": meta, "do_cache": True}
        n = contar_caracteres(payload["text"])
        self.verificar_orcamento(autorizacao, n)
        base = {"autorizacao": autorizacao, "motivo": motivo, "modelo": payload["model"], "voice_id": payload["voice_setting"]["voice_id"],
                "parametros": {k: v for k, v in payload["voice_setting"].items() if k != "voice_id"}, "caracteres_enviados": n,
                "custo_estimado_usd": custo_estimado(n, self.cfg), "saldo": "não confirmado (a resposta de síntese não informa)"}
        try:
            r = self._post(self.cfg["caminho_t2a"], payload)
        except Exception as e:                            # rede/tempo esgotado: não se sabe se houve cobrança
            self._debitar(autorizacao, n)                 # conta como gasto, por segurança
            self._registrar(**base, resultado=f"FALHA DE REDE: {type(e).__name__}", cobranca="desconhecida (debitado por segurança)")
            raise ErroNarracao(self._limpar(f"falha de rede ({type(e).__name__}). PARADO: pode ter havido cobrança; não repita sem avaliar"))
        try:
            j = r.json()
        except Exception:
            self._debitar(autorizacao, n)
            self._registrar(**base, resultado=f"HTTP {r.status_code} sem JSON", cobranca="desconhecida (debitado por segurança)")
            raise ErroNarracao(f"resposta HTTP {r.status_code} sem JSON. PARADO: pode ter havido cobrança")
        br = j.get("base_resp") or {}; cod = br.get("status_code"); extra = j.get("extra_info") or {}
        cobrados = extra.get("usage_characters")
        if r.status_code != 200 or cod != 0:
            self._debitar(autorizacao, cobrados if cobrados is not None else n)
            self._registrar(**base, resultado=f"ERRO {cod}: {ERROS.get(cod, br.get('status_msg', '?'))}", http=r.status_code,
                            caracteres_cobrados=cobrados, cobranca="informada" if cobrados is not None else "desconhecida (debitado por segurança)",
                            trace_id=j.get("trace_id"))
            raise ErroNarracao(f"MiniMax recusou: código {cod} ({ERROS.get(cod, br.get('status_msg', 'sem descrição'))}), HTTP {r.status_code}. "
                               "PARADO: nenhuma nova tentativa automática")
        dados = j.get("data") or {}
        try:
            audio = bytes.fromhex(dados["audio"])
        except Exception:
            self._debitar(autorizacao, cobrados if cobrados is not None else n)
            self._registrar(**base, resultado="resposta sem áudio decodificável", caracteres_cobrados=cobrados, trace_id=j.get("trace_id"))
            raise ErroNarracao("resposta sem áudio decodificável. PARADO")
        legendas = dados.get("subtitle_file") or j.get("subtitle_file") or dados.get("subtitle")
        cobr = cobrados if cobrados is not None else n
        self._debitar(autorizacao, cobr)
        meta = {"payload_sem_texto": {k: v for k, v in payload.items() if k != "text"}, "texto": payload["text"], "extra_info": extra,
                "trace_id": j.get("trace_id"), "legendas": legendas, "data": _agora(), "autorizacao": autorizacao, "motivo": motivo}
        self.cache.mkdir(parents=True, exist_ok=True); mp3.write_bytes(audio); meta_p.write_text(self._limpar(json.dumps(meta, ensure_ascii=False, indent=1)))
        self._registrar(**base, resultado="ok", caracteres_cobrados=cobrados, duracao_audio=extra.get("audio_length"),
                        trace_id=j.get("trace_id"), arquivo_cache=f"cache/{cid}.mp3")
        return {"audio": audio, "legendas": legendas, "meta": meta, "do_cache": False}

    # ---- consulta sem síntese (T1)
    def consultar_vozes(self, autorizacao, motivo="T1: validar chave, região e existência da voz (sem síntese)"):
        """Consulta de vozes da conta: não envia texto (0 caractere). NÃO presumimos que seja gratuita: o resultado e o
        que a API disser sobre cobrança ficam registrados para o diretor avaliar."""
        if autorizacao not in self.orcamento()["autorizacoes"]:
            raise RecusaOrcamento(f"sem autorização registrada para '{autorizacao}': nada foi enviado")
        try:
            r = self._post(self.cfg["caminho_consulta_vozes"], {"voice_type": "all"})
            j = r.json()
        except Exception as e:
            self._registrar(autorizacao=autorizacao, motivo=motivo, caracteres_enviados=0, resultado=f"FALHA: {type(e).__name__}")
            raise ErroNarracao(self._limpar(f"consulta falhou ({type(e).__name__}). PARADO"))
        br = j.get("base_resp") or {}; cod = br.get("status_code")
        vid = self.cfg["voz"]["voice_id"]; achada = vid in json.dumps(j)
        categorias = {k: len(v) for k, v in j.items() if isinstance(v, list)}
        onde = [k for k, v in j.items() if isinstance(v, list) and vid in json.dumps(v)]
        proibida = [k for k in self.cfg["vozes_proibidas"] if k in json.dumps(j)]
        self._registrar(autorizacao=autorizacao, motivo=motivo, caracteres_enviados=0, http=r.status_code,
                        resultado=f"código {cod}: {ERROS.get(cod, br.get('status_msg', ''))}", voz_encontrada=achada, categoria_da_voz=onde,
                        vozes_por_categoria=categorias, clone_antigo_ainda_na_conta=bool(proibida), host=self.cfg["host"], trace_id=j.get("trace_id"),
                        cobranca="nenhum campo de cobrança na resposta" if not any(k in json.dumps(j).lower() for k in ("usage", "charge", "cost", "balance")) else "ver resposta")
        return {"http": r.status_code, "codigo": cod, "mensagem": br.get("status_msg"), "voz_encontrada": achada, "categoria_da_voz": onde,
                "vozes_por_categoria": categorias, "clone_antigo_ainda_na_conta": bool(proibida),
                "campos_da_resposta": sorted(j.keys()), "trace_id": j.get("trace_id")}
