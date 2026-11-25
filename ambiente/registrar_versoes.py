#!/usr/bin/env python3
"""Gera ambiente/VERSOES.md com as versões exatas do ambiente atual.
Rode depois de qualquer mudança de dependência:  .venv/bin/python ambiente/registrar_versoes.py
"""
import datetime, platform, re, subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
AMB = RAIZ / "ambiente"


def out(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return "?"


def m(pad, txt):
    r = re.search(pad, txt)
    return r.group(1) if r else "?"


osr = Path("/etc/os-release").read_text()
docker_base = m(r"FROM (\S+)", (RAIZ / "Dockerfile").read_text())
py_inst = m(r'PY_VERSAO="([^"]+)"', (AMB / "instalar.sh").read_text())
uv_inst = m(r'UV_VERSAO="([^"]+)"', (AMB / "instalar.sh").read_text())
linhas = [
    "# Versões exatas do ambiente — Modo Curioso Studio AI", "",
    f"Gerado por `ambiente/registrar_versoes.py` em {datetime.date.today():%d/%m/%Y}. Não edite à mão.", "",
    "## Programas", "", "| Programa | Versão exata | Origem |", "|---|---|---|",
    f"| Sistema operacional | {m(r'PRETTY_NAME=\"([^\"]+)\"', osr)} | imagem base |",
    f"| Imagem Docker base | `{docker_base}` | Docker Hub (fixada por digest) |",
    f"| Python | {py_inst} (em uso: {platform.python_version()}) | uv / python-build-standalone |",
    f"| uv | {uv_inst} (em uso: {m(r'uv (\S+)', out(['uv', '--version']))}) | PyPI |",
    f"| FFmpeg | {m(r'ffmpeg version (\S+)', out(['ffmpeg', '-version']))} | apt (Ubuntu) |",
    f"| Git | {m(r'git version (\S+)', out(['git', '--version']))} | apt |",
    f"| Git LFS | {m(r'git-lfs/(\S+)', out(['git', 'lfs', 'version']))} | apt |",
    f"| Blender (bpy) | {out(['python', '-c', 'import bpy;print(bpy.app.version_string)']) or '?'} | PyPI (bpy) |",
    "", "## Pacotes de sistema (apt)", "",
    "Fonte: `ambiente/apt-versoes.lock.txt` (use `bash ambiente/instalar.sh --exato` para instalar exatamente estas).", "",
    "| Pacote | Versão |", "|---|---|",
]
for l in (AMB / "apt-versoes.lock.txt").read_text().splitlines():
    if "=" in l and not l.startswith("#"):
        p, v = l.split("=", 1); linhas.append(f"| {p} | {v} |")
linhas += ["", "## Bibliotecas Python", "",
           "Fonte: `ambiente/requirements.lock.txt` (gerado por `uv pip compile` a partir de `ambiente/requirements.in`). Diretas em **negrito**.", "",
           "| Pacote | Versão |", "|---|---|"]
diretos = {l.split("==")[0].strip().lower() for l in (AMB / "requirements.in").read_text().splitlines() if l.strip() and not l.startswith("#")}
for l in (AMB / "requirements.lock.txt").read_text().splitlines():
    r = re.match(r"^([A-Za-z0-9_.\-]+)==(\S+)", l)
    if r:
        n = r.group(1); linhas.append(f"| {'**'+n+'**' if n.lower() in diretos else n} | {r.group(2)} |")
linhas += ["", "## Fontes (licença SIL OFL 1.1)", "", "Fonte: `ambiente/fontes.sha256`.", "", "| Arquivo | SHA-256 |", "|---|---|"]
for l in (AMB / "fontes.sha256").read_text().splitlines():
    h, n = l.split(maxsplit=1); linhas.append(f"| {n} | `{h}` |")
(AMB / "VERSOES.md").write_text("\n".join(linhas) + "\n")
print("ok:", AMB / "VERSOES.md")
