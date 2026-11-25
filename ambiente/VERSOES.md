# Versões exatas do ambiente — Modo Curioso Studio AI

Gerado por `ambiente/registrar_versoes.py` em 25/11/2026. Não edite à mão.

## Programas

| Programa | Versão exata | Origem |
|---|---|---|
| Sistema operacional | Ubuntu 24.04.5 LTS | imagem base |
| Imagem Docker base | `ubuntu:24.04@sha256:562111b88caa79c71391c0c4d3c2114a7d5c35915c20561fd893cb1e07929e6b` | Docker Hub (fixada por digest) |
| Python | 3.13.14 (em uso: 3.13.14) | uv / python-build-standalone |
| uv | 0.11.32 (em uso: 0.11.32) | PyPI |
| FFmpeg | 6.1.1-3ubuntu5 | apt (Ubuntu) |
| Git | 2.43.0 | apt |
| Git LFS | 3.4.1 | apt |
| Blender (bpy) | 5.3.0 | PyPI (bpy) |

## Pacotes de sistema (apt)

Fonte: `ambiente/apt-versoes.lock.txt` (use `bash ambiente/instalar.sh --exato` para instalar exatamente estas).

| Pacote | Versão |
|---|---|
| ffmpeg | 7:6.1.1-3ubuntu5 |
| git | 1:2.43.0-1ubuntu7.4 |
| git-lfs | 3.4.1-1ubuntu0.4 |
| curl | 8.5.0-2ubuntu10.16 |
| ca-certificates | 20260816ubuntu0.24.04.2 |
| python3-pip | 24.0+dfsg-1ubuntu1.3 |
| libegl1 | 1.7.0-1build1 |
| libgl1 | 1.7.0-1build1 |
| libgles2 | 1.7.0-1build1 |
| libglx-mesa0 | 25.2.8-0ubuntu0.24.04.5 |
| libgomp1 | 14.2.0-4ubuntu2~24.04.1 |
| libxi6 | 2:1.8.1-1build1 |
| libxxf86vm1 | 1:1.1.4-1build4 |
| libxfixes3 | 1:6.0.0-2build1 |
| libxrender1 | 1:0.9.10-1.1build1 |
| libxkbcommon0 | 1.6.0-1build1 |
| libsm6 | 2:1.2.3-1build3 |
| libice6 | 2:1.0.10-1build3 |
| libx11-6 | 2:1.8.7-1ubuntu0.1 |
| libxext6 | 2:1.3.4-1build2 |
| libfontconfig1 | 2.15.0-1.1ubuntu2 |
| libfreetype6 | 2.13.2+dfsg-1ubuntu0.2 |

## Bibliotecas Python

Fonte: `ambiente/requirements.lock.txt` (gerado por `uv pip compile` a partir de `ambiente/requirements.in`). Diretas em **negrito**.

| Pacote | Versão |
|---|---|
| attrs | 26.1.0 |
| **bpy** | 5.3.0 |
| cattrs | 26.2.1 |
| certifi | 2026.11.20 |
| cffi | 2.1.1 |
| charset-normalizer | 3.5.3 |
| cloudpickle | 3.1.3 |
| cython | 3.3.1 |
| decorator | 5.3.2 |
| flatbuffers | 25.12.19 |
| **fonttools** | 4.68.0 |
| idna | 3.20 |
| joblib | 1.6.0 |
| lazy-loader | 0.6 |
| **librosa** | 1.0.1 |
| llvmlite | 0.50.0 |
| msgpack | 1.2.4 |
| narwhals | 2.29.0 |
| numba | 0.68.1 |
| **numpy** | 2.5.5 |
| onnxruntime | 1.32.0 |
| opencv-python | 5.1.0.95 |
| **opencv-python-headless** | 5.1.0.95 |
| packaging | 26.4 |
| **pillow** | 13.0.0 |
| platformdirs | 4.14.8 |
| pooch | 1.9.0 |
| protobuf | 7.36.2 |
| pybind11 | 3.1.0 |
| pyclipper | 1.4.0 |
| pycparser | 3.12 |
| pyyaml | 6.0.4 |
| **rapidocr-onnxruntime** | 1.4.4 |
| requests | 2.34.2 |
| scikit-learn | 1.9.1 |
| **scipy** | 1.18.1 |
| shapely | 2.2.0 |
| six | 1.17.0 |
| **skia-python** | 144.1 |
| soundfile | 0.14.0 |
| soxr | 1.1.0 |
| threadpoolctl | 3.8.0 |
| tqdm | 4.70.1 |
| typing-extensions | 4.16.0 |
| urllib3 | 2.8.0 |
| zstandard | 0.25.0 |

## Fontes (licença SIL OFL 1.1)

Fonte: `ambiente/fontes.sha256`.

| Arquivo | SHA-256 |
|---|---|
| Nunito-ExtraBold.ttf | `27c38af8199cb0cee9f19c455ea86aaaf0c97cf406eeea424046ab8239de5526` |
| Nunito[wght].ttf | `bb55a5ca5c2042335b3991af27c4d0705d0ef41cac6164ac737fd8f2a1e85207` |
| OFL_nunito.txt | `580df76c95a1ec5ab878ceb25bb3d85c6a076804e9c970c8c6972aea775fdf65` |
| OFL_robotocondensed.txt | `0e4cc6ece88573545be2ed25835363662a6182ba4a4c1b5c8feda52add30e8a6` |
| RobotoCondensed-ExtraBold.ttf | `47643d6545d9fef227e8229e0beea343cdbe94d058ce45263bb6e9f106626be7` |
| RobotoCondensed[wght].ttf | `dace262afcee68a5276f200d8026c57221735c0118ab5fda8c2c0d3dc409a8d0` |
