#!/usr/bin/env bash
# Reconstrói o Modo Curioso Studio AI num container novo (depois do descarte do anterior).
#
# Caso 1, já dentro do repositório clonado (sessão nova do Claude Code):
#   bash ambiente/restaurar.sh
# Caso 2, máquina vazia:
#   git clone https://github.com/kelvynvillar10-byte/Claude-3D.git && cd Claude-3D && bash ambiente/restaurar.sh
#
# Opções: --branch <nome> (padrão: o branch atual) · --sem-apt · --docker (constrói a imagem em vez de instalar no sistema)
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
BRANCH=""; SEM_APT=""; DOCKER=0
while [ $# -gt 0 ]; do
  case "$1" in
    --branch) BRANCH="$2"; shift ;;
    --sem-apt) SEM_APT="--sem-apt" ;;
    --docker) DOCKER=1 ;;
    *) echo "opção desconhecida: $1"; exit 2 ;;
  esac
  shift
done
export PATH="$HOME/.local/bin:$PATH"
passo() { printf '\n==> %s\n' "$*"; }

passo "1/5 Código e documentos"
if [ -n "$BRANCH" ]; then
  git fetch origin "$BRANCH" && git checkout "$BRANCH" && git pull --ff-only origin "$BRANCH"
else
  git pull --ff-only 2>/dev/null || echo "(sem pull: branch sem upstream ou alterações locais)"
fi
echo "branch: $(git rev-parse --abbrev-ref HEAD) · commit: $(git rev-parse --short HEAD)"

passo "2/5 Arquivos grandes (Git LFS)"
if command -v git-lfs >/dev/null 2>&1; then git lfs pull || true; else echo "git-lfs ainda não instalado; será instalado no passo 3"; fi

if [ "$DOCKER" = 1 ]; then
  passo "3/5 Imagem Docker"
  docker build -t modo-curioso-studio .
  passo "4/5 Verificação dentro da imagem"
  docker run --rm -v "$RAIZ":/studio modo-curioso-studio python ambiente/verificar.py
else
  passo "3/5 Instalação (ambiente/instalar.sh)"
  bash ambiente/instalar.sh $SEM_APT --sem-verificar
  command -v git-lfs >/dev/null 2>&1 && git lfs pull || true
  passo "4/5 Verificação"
  .venv/bin/python ambiente/verificar.py --rede
fi

passo "5/5 Estado do projeto"
echo "Leia CLAUDE.md e docs/IDENTIDADE_OFICIAL.md antes de produzir."
ls docs/
