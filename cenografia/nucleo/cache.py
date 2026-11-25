"""Cenografia — cache de placas (E0).

Cada placa renderizada fica em .cache/cenografia/<chave>/ (fora do Git, ver .gitignore) com um manifest.json:
receita, chave, versão do núcleo, tempos de render e o sha256 de cada arquivo gerado.
- valido(chave)  → True só se o manifesto existe E todos os arquivos existem com o hash registrado
  (arquivo apagado ou corrompido = cache inválido → renderiza de novo).
"""
import hashlib, json
from pathlib import Path
from .receita import RAIZ

RAIZ_CACHE = RAIZ / ".cache" / "cenografia"


def pasta(chave):
    return RAIZ_CACHE / chave


def sha256_arquivo(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def manifesto(chave):
    m = pasta(chave) / "manifest.json"
    return json.loads(m.read_text()) if m.exists() else None


def valido(chave):
    m = manifesto(chave)
    if not m or m.get("estado") != "completo":
        return False
    for rel, h in m["arquivos"].items():
        p = pasta(chave) / rel
        if not p.exists() or sha256_arquivo(p) != h:
            return False
    return True


def gravar_manifesto(chave, meta):
    d = pasta(chave)
    arquivos = {str(p.relative_to(d)): sha256_arquivo(p) for p in sorted(d.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    meta = dict(meta, chave=chave, arquivos=arquivos, estado="completo")
    (d / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    return meta
