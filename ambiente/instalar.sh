#!/usr/bin/env bash
# Instala e configura o ambiente do Modo Curioso Studio AI.
# Idempotente: pode rodar quantas vezes quiser. Alvo: Ubuntu 24.04, x86_64.
#
# Uso:
#   bash ambiente/instalar.sh            # instalação completa + verificação
#   bash ambiente/instalar.sh --sem-apt  # pula os pacotes de sistema (sem root ou já instalados)
#   bash ambiente/instalar.sh --exato    # instala os pacotes apt nas versões exatas de apt-versoes.lock.txt
#   bash ambiente/instalar.sh --sem-verificar
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
PY_VERSAO="3.13.14"      # versão exata do Python, distribuída pelo uv (python-build-standalone); ver VERSOES.md
VENV="${STUDIO_VENV:-$RAIZ/.venv}"   # local do ambiente virtual (no Docker: /opt/studio-venv)
UV_VERSAO="0.11.32"      # versão exata do uv
SEM_APT=0; EXATO=0; VERIFICAR=1
for a in "$@"; do
  case "$a" in
    --sem-apt) SEM_APT=1 ;;
    --exato) EXATO=1 ;;
    --sem-verificar) VERIFICAR=0 ;;
    *) echo "opção desconhecida: $a"; exit 2 ;;
  esac
done
passo() { printf '\n==> %s\n' "$*"; }

passo "Sistema"
. /etc/os-release 2>/dev/null || true
echo "SO: ${PRETTY_NAME:-desconhecido} · arquitetura: $(uname -m)"
if [ "${VERSION_ID:-}" != "24.04" ]; then
  echo "AVISO: o ambiente de referência é Ubuntu 24.04. Outras versões podem trazer FFmpeg e bibliotecas diferentes."
fi

# 1. Pacotes de sistema
if [ "$SEM_APT" = 0 ]; then
  passo "Pacotes de sistema (apt)"
  SUDO=""; [ "$(id -u)" != 0 ] && SUDO="sudo"
  export DEBIAN_FRONTEND=noninteractive
  $SUDO apt-get update -qq
  if [ "$EXATO" = 1 ]; then
    mapfile -t PKGS < <(grep -v '^#' ambiente/apt-versoes.lock.txt | grep -v AUSENTE)
  else
    mapfile -t PKGS < <(grep -v '^#' ambiente/apt-pacotes.txt | sed '/^\s*$/d')
  fi
  $SUDO apt-get install -y -qq --no-install-recommends "${PKGS[@]}"
fi

# 2. Git LFS (assets pesados e MP4 de referência)
passo "Git LFS"
if command -v git-lfs >/dev/null 2>&1; then
  git lfs install --skip-repo >/dev/null && echo "git-lfs $(git lfs version | awk '{print $1}' | cut -d/ -f2) configurado"
else
  echo "AVISO: git-lfs ausente (rode sem --sem-apt)"
fi

# 3. uv (gerenciador de Python e pacotes)
passo "uv $UV_VERSAO"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1 || [ "$(uv --version | awk '{print $2}')" != "$UV_VERSAO" ]; then
  python3 -m pip install --quiet --user --break-system-packages "uv==$UV_VERSAO" 2>/dev/null \
    || python3 -m pip install --quiet --user "uv==$UV_VERSAO"
fi
uv --version

# 4. Python exato + ambiente virtual do projeto
passo "Python $PY_VERSAO e ambiente virtual $VENV"
# Sempre o Python gerenciado pelo uv, na versão exata (igual em qualquer máquina).
uv python install "$PY_VERSAO"
PYBIN="$(uv python find "$PY_VERSAO")"
echo "Python: $PYBIN"
if [ ! -x "$VENV/bin/python" ] || [ "$("$VENV/bin/python" -c 'import platform;print(platform.python_version())')" != "$PY_VERSAO" ]; then
  rm -rf "$VENV"
  uv venv --python "$PYBIN" "$VENV"
fi

# 5. Bibliotecas Python nas versões exatas do lock
passo "Bibliotecas Python (ambiente/requirements.lock.txt)"
uv pip sync --python "$VENV/bin/python" ambiente/requirements.lock.txt

# 6. Fontes oficiais (versionadas em assets/fontes; recriadas se faltarem)
passo "Fontes oficiais"
"$VENV/bin/python" ambiente/fontes.py

# 7. Verificação
if [ "$VERIFICAR" = 1 ]; then
  passo "Verificação"
  "$VENV/bin/python" ambiente/verificar.py
fi

passo "Pronto. Ative com: source $VENV/bin/activate"
