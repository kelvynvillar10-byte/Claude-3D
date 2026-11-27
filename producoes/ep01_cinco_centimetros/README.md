# EP01 — "E se você acordasse com apenas 5 centímetros?"

**Vídeo final:** `export/MC_ep01_cinco_centimetros_v1.mp4`
- **Formato:** 1080×1920 (9:16), 30 qps, **113,4 s**, H.264 + AAC.
- **Áudio:** −14 LUFS, pico ≤ −1 dBTP.
- **QA:** 12/12 (`saida/qa_relatorio.json`).
- **Folha de contato:** `saida/folha_contato_1qps.jpg`.

Produzido em 26/11/2026 com autorização do diretor para todas as etapas ("Pode seguir em todas as partes sem perguntar até a conclusão do vídeo").

## Entregas
| Item | Onde |
|---|---|
| Vídeo final | `export/MC_ep01_cinco_centimetros_v1.mp4` |
| Texto falado (referência) | `narracao_falada.txt`. Transcrito pelo Whisper e conferido contra o áudio, sem diferenças. |
| Narração final (pós-produção) | `narracao/edicoes/ep01_narracao/`: WAV 48 kHz, MP3, `voz_palavras.json`, marcações, relatório de edição, vídeo de conferência da sincronia |
| Decupagem e montagem | `montagem.json`, gerado por `codigo/montagem_ep01.py`: 41 planos, 93 legendas, 53 eventos de som |
| Cenários | 15 placas do Blender: `codigo/placas_ep01.py` + `cenografia/receitas/e10_*.json` (kit `cenografia/componentes/interior.py`) |
| Personagens | Heitor rig v2, sem alteração; gato e aranha originais em `personagens/animais/` |
| Insert científico | `inserts/quadrado_cubo.py` (lei do quadrado-cubo) |
| Áudio master | `saida/mix.wav`, gerado por `codigo/audio_ep01.py` |
| QA | `codigo/qa_ep01.py` → `saida/qa_relatorio.json` + folha de contato |

## Como reproduzir
```
.venv/bin/python producoes/ep01_cinco_centimetros/codigo/placas_ep01.py          # cenários (cache; ~6 min cada placa nova)
.venv/bin/python producoes/ep01_cinco_centimetros/codigo/montagem_ep01.py        # montagem.json
.venv/bin/python producoes/ep01_cinco_centimetros/codigo/audio_ep01.py           # saida/mix.wav
TRABALHADORES=3 MAX_PLACAS=1 .venv/bin/python producoes/ep01_cinco_centimetros/codigo/compor_ep01.py   # ~25 min
ffmpeg -i producoes/ep01_cinco_centimetros/_cache/video_sem_audio.mp4 -i producoes/ep01_cinco_centimetros/saida/mix.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart producoes/ep01_cinco_centimetros/export/MC_ep01_cinco_centimetros_v1.mp4
.venv/bin/python producoes/ep01_cinco_centimetros/codigo/qa_ep01.py producoes/ep01_cinco_centimetros/export/MC_ep01_cinco_centimetros_v1.mp4
```

## Decisões do diretor aplicadas
- Narração = **1ª geração do diretor no MiniMax Audio**, voz `Portuguese_CaptivatingStoryteller`, texto em "você". O texto falado difere do roteiro original (aranha, paredões, invencível); vale o falado.
- Fechamento com **pergunta para comentário**. A pergunta entra numa cartela escrita (3 s, sem voz), porque a narração escolhida termina em "MODO CURIOSO".
- Diretriz de duração do canal: 60–120 s.

## QA (medido)
| Verificação | Resultado |
|---|---|
| Formato | 1080×1920, 30 qps, H.264 + AAC |
| Duração | 113,40 s e 3.402 quadros, iguais aos da montagem |
| Legendas | 93 blocos, 2,5 palavras/bloco, 39 % com destaque amarelo |
| Marca d'água | exatamente "MODO CURIOSO" em todo quadro |
| Loudness | −14,1 LUFS, pico −1,3 dBTP |
| Personagem | 260 braços verificados nas poses do episódio e na caminhada: 0 cotovelos invertidos; rig v2 sem alteração |
| Cenários | 15 placas: nada flutuando, nenhum texto 3D |
| Números na tela | 11: 5 cm, 14 m, 4 m, 27 mm, 18 cm = 5 m, ≈ 7 m, ×28, ÷28, ÷21.952, ÷784, ×28 |
| Voz | sem aceleração: palavras idênticas ao original, 0 ms de diferença |

## Limitações (honestas)
1. **Duração de 113 s, acima da meta do EP01 (75–90 s).** A narração escolhida tem 91 s só de fala, e a edição não acelera a voz. Está dentro da diretriz do canal (60–120 s).
2. **Ritmo:** 21 cortes/min e plano mediano de 2,8 s, contra ~31 cortes/min e 1,7 s nas referências. Os planos acompanham as frases longas da narração. Mais cortes pedem mais placas ou mais variações de enquadramento.
3. **Animação econômica:** poses seguradas com respiração, piscada e trocas de expressão, como pede o padrão base. Não há atuação complexa; a caminhada só aparece em um plano.
4. **Gato e aranha** são desenhados por cima da cena, com a profundidade do Heitor. Nesses enquadramentos nada passa na frente deles.
5. **Trilha e efeitos sonoros** são procedurais e temporários: a biblioteca de música e SFX ainda é pendência do diretor.
6. **Dados a confirmar:** as medidas da moeda de R$ 1 (27 mm, 7 g) só aparecem como rótulo "27 mm". Não usei peso nem nenhum outro dado não confirmado.
7. A gota, a moeda e o "quase uma montanha" seguem o texto falado, que tem licença poética. A ciência do insert (quadrado-cubo) é exata.
