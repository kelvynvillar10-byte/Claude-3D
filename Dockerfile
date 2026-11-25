# Modo Curioso Studio AI — imagem reproduzível do ambiente de produção.
#
# Construir:   docker build -t modo-curioso-studio .
# Usar:        docker run --rm -it -v "$PWD":/studio modo-curioso-studio
# Verificar:   docker run --rm -v "$PWD":/studio modo-curioso-studio python ambiente/verificar.py
#
# Atrás de um proxy HTTPS com CA própria (como o ambiente cloud do Claude):
#   cp /caminho/da/ca.crt ambiente/docker/certs/   (arquivos *.crt não são versionados)
#   docker build --network host --build-arg HTTPS_PROXY=$HTTPS_PROXY --build-arg HTTP_PROXY=$HTTPS_PROXY -t modo-curioso-studio .
# Detalhes em ambiente/RESTAURAR.md.

# Ubuntu 24.04 fixado por digest (mesma base do ambiente de referência)
FROM ubuntu:24.04@sha256:562111b88caa79c71391c0c4d3c2114a7d5c35915c20561fd893cb1e07929e6b

ARG HTTPS_PROXY=""
ARG HTTP_PROXY=""
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    STUDIO_VENV=/opt/studio-venv \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PATH=/opt/studio-venv/bin:/root/.local/bin:$PATH

# CAs extras opcionais (proxy corporativo/cloud). Sem arquivos .crt, nada muda.
COPY ambiente/docker/certs/ /usr/local/share/ca-certificates/studio-extra/

# Pacotes de sistema (lista única, a mesma usada por ambiente/instalar.sh)
COPY ambiente/apt-pacotes.txt /tmp/apt-pacotes.txt
RUN apt-get update -qq \
 && apt-get install -y -qq --no-install-recommends ca-certificates \
 && update-ca-certificates \
 && apt-get install -y -qq --no-install-recommends $(grep -v '^#' /tmp/apt-pacotes.txt | sed '/^\s*$/d') \
 && rm -rf /var/lib/apt/lists/*

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt \
    UV_SYSTEM_CERTS=true

WORKDIR /studio
# Só o necessário para instalar (o repositório inteiro é montado em /studio na execução)
COPY ambiente/ /studio/ambiente/
COPY assets/fontes/ /studio/assets/fontes/
RUN bash ambiente/instalar.sh --sem-apt --sem-verificar \
 && rm -rf /root/.cache

# Sem proxy de build na imagem final
ENV HTTPS_PROXY="" HTTP_PROXY="" https_proxy="" http_proxy=""
CMD ["bash"]
