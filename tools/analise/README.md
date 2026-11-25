# Ferramentas de análise de referência e QA

Scripts usados na auditoria da Etapa 1 (ver `docs/AUDITORIA_REFERENCIAS.md`). Eles também servem de QA automático para os nossos vídeos (ver `docs/PIPELINE_PRODUCAO.md`, seção 12).

Dependências: FFmpeg 6+, Python 3.11+, `numpy`, `pillow`, `opencv-python-headless`, `rapidocr-onnxruntime`.

| Script | O que faz | Uso |
|---|---|---|
| `match2.py` | Identifica qual MP4 corresponde a cada miniatura `vNN_k.jpg` (busca quadro a quadro, 4 qps) | `python3 match2.py <pasta_trabalho> <pasta_repo>` (precisa de `<pasta_trabalho>/mapnames.txt`) |
| `analyze.py` | Por vídeo: cortes (histograma HSV), câmera (fluxo óptico LK + transformação de semelhança: zoom, pan, tilt, giro), luma, saturação, contraste, vinheta, cor Lab de sombras e altas luzes, EBU R128, silêncios, eventos sonoros | `python3 analyze.py <video.mp4> <tag> <pasta_saida>` |
| `ocr.py` | OCR das legendas a 2 qps (texto, posição, tamanho, pixels brancos e amarelos) | `python3 ocr.py <video.mp4> <tag> <pasta_saida>` |
| `summarize.py` | Consolida as métricas de `analyze.py` em `summary.json` | `python3 summarize.py <pasta_trabalho>` (lê `<pasta_trabalho>/out/mNN.json`) |
| `subs.py` | Consolida as métricas de legenda em `subs.json` | `python3 subs.py <pasta_trabalho>` |
| `tables.py`, `subs_table.py` | Geram as tabelas Markdown da auditoria | `python3 tables.py <pasta_trabalho>` |

`mapa_mp4_referencias.txt` liga a tag interna (m01–m13), o arquivo MP4 e o número da referência no `index.html` (v01–v20).

Limitações conhecidas (detalhes na auditoria):
- O detector de cortes conta 5–12 % menos cortes que o relatório `index.html` (perde cortes entre planos de cor parecida).
- O detector de chicote é conservador e conta menos que o relatório. A tremida curta de impacto não é medida de forma confiável.
- A contagem de palavras por OCR subestima um pouco, porque o OCR às vezes junta duas palavras.
