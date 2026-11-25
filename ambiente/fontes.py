#!/usr/bin/env python3
"""Garante as fontes oficiais do Modo Curioso em assets/fontes/.

- Baixa as fontes variáveis (licença OFL) do repositório google/fonts, se faltarem.
- Gera as instâncias estáticas no peso 800 (ExtraBold) com fontTools.
- Confere os hashes SHA-256 registrados em ambiente/fontes.sha256.

Uso: python ambiente/fontes.py [--verificar]
"""
import hashlib, sys, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR = RAIZ / "assets" / "fontes"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
ORIGENS = {
    "Nunito[wght].ttf": "nunito/Nunito%5Bwght%5D.ttf",
    "OFL_nunito.txt": "nunito/OFL.txt",
    "RobotoCondensed[wght].ttf": "robotocondensed/RobotoCondensed%5Bwght%5D.ttf",
    "OFL_robotocondensed.txt": "robotocondensed/OFL.txt",
}
INSTANCIAS = {  # estática: (variável de origem, peso)
    "Nunito-ExtraBold.ttf": ("Nunito[wght].ttf", 800),            # estampa "Modo Curioso" e rótulos
    "RobotoCondensed-ExtraBold.ttf": ("RobotoCondensed[wght].ttf", 800),  # legendas e marca d'água "MODO CURIOSO"
}
HASHES = RAIZ / "ambiente" / "fontes.sha256"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def esperado():
    d = {}
    if HASHES.exists():
        for linha in HASHES.read_text().splitlines():
            if linha.strip():
                h, n = linha.split(maxsplit=1)
                d[n.strip()] = h
    return d


def verificar():
    exp, ok = esperado(), True
    for n in list(ORIGENS) + list(INSTANCIAS):
        p = DIR / n
        if not p.exists():
            print(f"FALTA        {n}"); ok = False
        elif n in exp and sha(p) != exp[n]:
            print(f"INCOMPATÍVEL {n} (hash diferente)"); ok = False
        else:
            print(f"OK           {n}")
    return ok


def garantir():
    DIR.mkdir(parents=True, exist_ok=True)
    for n, url in ORIGENS.items():
        if not (DIR / n).exists():
            print("baixando", n)
            urllib.request.urlretrieve(BASE + url, DIR / n)
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for n, (src, peso) in INSTANCIAS.items():
        if not (DIR / n).exists():
            print("gerando", n)
            inst = instancer.instantiateVariableFont(TTFont(DIR / src), {"wght": peso}, updateFontNames=True)
            inst.recalcTimestamp = False  # saída determinística (hash estável)
            inst.save(DIR / n)
    if not HASHES.exists():
        HASHES.write_text("".join(f"{sha(DIR / n)}  {n}\n" for n in sorted(list(ORIGENS) + list(INSTANCIAS))))
    return verificar()


if __name__ == "__main__":
    sys.exit(0 if (verificar() if "--verificar" in sys.argv else garantir()) else 1)
