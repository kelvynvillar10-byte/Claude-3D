"""Cenografia — receitas de cena (E0).

Uma RECEITA é um JSON que descreve a cena inteira: saída, câmera, horário, camadas e componentes (cada um com
parâmetros e semente). A receita é a fonte da verdade: a mesma receita + o mesmo código geram a mesma placa.

- carregar(caminho)       → dict validado
- chave(receita)          → hash sha256 da receita normalizada + VERSÃO do núcleo + código dos geradores
                            (mudar a receita OU o código do gerador invalida o cache)
- rng(semente, *chaves)   → random.Random determinístico por componente
"""
import hashlib, json, random
from pathlib import Path

VERSAO_NUCLEO = "E0.1"
RAIZ = Path(__file__).resolve().parents[2]
CENOGRAFIA = RAIZ / "cenografia"
CAMADAS_PADRAO = ["ceu", "longe", "meio", "perto", "frente"]   # do fundo para a frente
GRUPOS_LUZ = ["ceu", "sol", "artificial", "efeito"]              # grupos de luz (reacender no compositor)

_OBRIG = {"nome": str, "semente": int, "saida": dict, "camera": dict, "luz": dict, "componentes": list}


class ErroReceita(ValueError):
    pass


def validar(r):
    for k, tp in _OBRIG.items():
        if k not in r:
            raise ErroReceita(f"receita sem o campo obrigatório '{k}'")
        if not isinstance(r[k], tp):
            raise ErroReceita(f"campo '{k}' deveria ser {tp.__name__}")
    s = r["saida"]
    for k in ("largura", "altura", "overscan", "amostras"):
        if k not in s:
            raise ErroReceita(f"saida.{k} ausente")
    camadas = r.get("camadas", CAMADAS_PADRAO)
    for i, c in enumerate(r["componentes"]):
        if "tipo" not in c:
            raise ErroReceita(f"componente {i} sem 'tipo'")
        if c.get("camada", "meio") not in camadas or c.get("camada") == "ceu":
            raise ErroReceita(f"componente {i} ({c['tipo']}): camada inválida '{c.get('camada')}' (o céu é só o mundo)")
    return r


def carregar(caminho):
    r = json.loads(Path(caminho).read_text())
    r.setdefault("camadas", CAMADAS_PADRAO)
    return validar(r)


def _normalizar(x):
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: _normalizar(v) for k, v in sorted(x.items())}
    if isinstance(x, list):
        return [_normalizar(v) for v in x]
    return x


def hash_codigo():
    """Hash do código dos geradores (núcleo + componentes): mudar o gerador invalida o cache."""
    h = hashlib.sha256()
    for p in sorted((CENOGRAFIA / "nucleo").glob("*.py")) + sorted((CENOGRAFIA / "componentes").glob("*.py")):
        if p.name == "compositor.py" or p.name == "medidas.py":   # não afetam a placa renderizada
            continue
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()


def chave(r):
    base = json.dumps(_normalizar(r), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((VERSAO_NUCLEO + "|" + hash_codigo() + "|" + base).encode()).hexdigest()


def rng(semente, *chaves):
    h = hashlib.sha256(("|".join([str(semente)] + [str(c) for c in chaves])).encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))
