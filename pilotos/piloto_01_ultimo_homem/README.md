# Piloto 01 — "O último homem do mundo" (teste técnico de 10 s)

Primeiro piloto técnico do Modo Curioso Studio AI, autorizado em 25/11/2026. **Não é um episódio.** Serve para validar a integração Blender → skia → FFmpeg com a identidade oficial (ID-001 a ID-004).

**Vídeo final:** [`saida/MC_piloto01_ultimo_homem_v3.mp4`](saida/MC_piloto01_ultimo_homem_v3.mp4): 1080×1920 (9:16), 30 qps, 10,0 s, H.264 + AAC, −14,3 LUFS.

## Entrega

| Item pedido | Arquivo |
|---|---|
| Vídeo final MP4 | `saida/MC_piloto01_ultimo_homem_v3.mp4` |
| Roteiro da narração | `ROTEIRO.md` (e `roteiro.json`, os blocos de legenda) |
| Arquivo de montagem | `montagem.json` (planos, câmera, personagem, efeitos, legendas, efeitos sonoros, marca d'água) |
| Arquivos e recursos | `voz/` (voz temporária e tempos), `recursos/marca/` (arquivos-mestre em SVG e texturas da marca), `recursos/heitor_rig_v1_PROPOSTA/` (rig e folha de modelo), `recursos/tela_celular.png`, `recursos/fundos_3d_previa/` (fundos do Blender), `saida/mix.wav` (áudio master) |
| Folha de contato | `saida/folha_contato.jpg` (2 qps) e `saida/folha_contato_completa_10qps.jpg` (o vídeo inteiro) |
| Relatório de qualidade e limitações | `RELATORIO_QA.md` (e `saida/qa_relatorio.json`) |
| Código (reproduzível) | `codigo/` |

## Decisões tomadas com o diretor antes da produção
- **Personagem:** "Heitor rig v1 PROPOSTA", construído só a partir da especificação, porque não existiam arquivos vetoriais oficiais. **Aguarda aprovação.**
- **Voz:** espeak-ng local, **temporária** (ElevenLabs e Hugging Face bloqueados; nenhum serviço pago usado).
- **Narração:** com "tu", no padrão do canal.

## Como reproduzir
```bash
cd pilotos/piloto_01_ultimo_homem
apt-get install -y espeak-ng                 # só para a voz temporária deste piloto
../../.venv/bin/python codigo/marca.py       # arquivos-mestre e texturas da marca
../../.venv/bin/python codigo/heitor_rig.py  # rig v1 e folha de modelo
../../.venv/bin/python codigo/voz.py         # narração temporária + tempos
../../.venv/bin/python codigo/montagem.py    # montagem.json
../../.venv/bin/python codigo/cenas_blender.py --amostras 24   # fundos 3D (~17 min em CPU)
../../.venv/bin/python codigo/audio.py       # efeitos sonoros, trilha, ducking, master −14 LUFS
../../.venv/bin/python codigo/compor.py --audio saida/mix.wav --saida saida/MC_piloto01_ultimo_homem_v3.mp4
../../.venv/bin/python codigo/qa.py MC_piloto01_ultimo_homem_v3.mp4
```
Os renders intermediários ficam em `_cache/` (fora do Git).
