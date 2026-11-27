# EP02 — "E se sua namorada te desse um PS5 com GTA 6 instalado?"

**Status:** produzido com autorização total do diretor (27/11/2026: "permissão para prosseguir com tudo autorizado em todos os
processos até o término do vídeo"), **aguardando avaliação do diretor**.

**Vídeo:** `export/MC_ep02_presente_videogame_v1.mp4` (1080×1920, 30 qps, H.264 + AAC, −14 LUFS).
**QA:** `saida/qa_relatorio.json` · **Folha de contato:** `saida/folha_contato_1qps.jpg` · **Mapa fala → imagem:** `saida/mapa_fala_imagem.json`.

## Decisões deste episódio
- **Roteiro:** texto do diretor, narrado com a **voz do próprio diretor** (gerada por ele no MiniMax Audio,
  arquivo `…Kelvyn_villar_Rodrigues.mp3`). Pedido do diretor: manter "PS5" e "GTA 6" na fala, como fã do jogo.
- **Marcas:** a narração e a legenda citam o console e o jogo (é a fala). **Na imagem não há marca de terceiros:**
  o videogame, o controle, a tela de instalação, o HUD e a cidade do jogo são desenhos próprios e genéricos, sem logotipo,
  sem a arte, a fonte ou o mapa do jogo real (regra fixa do canal; checklist 9).
- **Personagens:** Juca e Jandira (nomes do diretor; aparência proposta e aprovada em 27/11/2026), rig adulto v1 em
  `personagens/adultos/`, derivado do Heitor v2.1 sem alterá-lo.
- **Animação:** padrão de animação dinâmica aprovado (cena de prova de 27/11/2026): câmera em movimento em todo plano,
  personagens sempre agindo, cada termo-chave da narração com evento visual no instante em que é dito.

## Narração (`narracao/edicoes/ep02_narracao/`, QA 13/13)
- 85,9 s depois da edição de pausas; −16,1 LUFS; pico −1,8 dBTP; nenhuma palavra cortada ou acelerada; tom preservado (+0,6 %).
- Direção revisada frase a frase (destaques: "enorme", "felicidade", "fria", "primeira"; suspense antes da passagem
  do tempo e da revelação final).
- **Preset novo para a voz do diretor** (`narracao/pos/preset_ep02_voz_diretor.json`): o preset v1 deixava a voz grave do
  MP3 do site brilhante demais (sibilância +4,9 dB; reprovava no QA). O novo tira o realce de presença/ar, contém os agudos
  acima de 5 kHz e comprime menos (1,8:1). Resultado: variação máxima +2,2 dB por banda. Usado com
  `NARRACAO_PRESET=narracao/pos/preset_ep02_voz_diretor.json` (o `processar.py` ganhou essa opção; sem ela, nada muda).

## Cenários (Blender, `cenografia/componentes/sala_ep02.py`, receita `cenografia/receitas/ep02_sala.json`)
Sala de apartamento em escala humana: sofá de costas para a janela (a luz do dia muda ao fundo), TV de 55" na parede
oposta com a tela trocada no compositor, mesa de centro com prato feito, porta aberta para o corredor, luminária de pé,
estante e quadro. 7 enquadramentos (C1–C7, ~4–5 min cada) + 3 da cidade do jogo (a rua aprovada da E6, no horário
crepúsculo). A hora do dia é reiluminação dos grupos de luz (tarde → fim de tarde → noite → madrugada → amanhecer),
sem novo render; a luz da TV é o grupo "efeito", com as cores do jogo.

## Decupagem (49 planos, `codigo/cenas_ep02.py`)
Mapa completo em `saida/mapa_fala_imagem.json`. Números na tela: 0 h de uso, 100 % instalado, 72 → 140 BPM, 96–126 km/h,
16:00 → 18:00, 2/5/10 HORAS DEPOIS, 21:00, 02:00, 65 → 22 °C, 0 m, 06:12, MISSÃO 1 · 3 %.

## Áudio (`codigo/audio_ep02.py`)
Voz do diretor + trilha de comédia procedural (Dó maior, 112 BPM, mais "synth" dentro do jogo, mais baixa no amanhecer
triste) + 98 efeitos procedurais ligados às ações (passos, brilhos, TV ligando, coração 72→140, moedas, motor, relógio
acelerado, passarinhos, "uó-uó-uó"). Ducking de 9 dB sob a voz. Master −14 LUFS.

## Reproduzir
```
.venv/bin/python producoes/ep02_presente_videogame/codigo/placas_ep02.py          # placas (cache em .cache/cenografia)
.venv/bin/python producoes/ep02_presente_videogame/codigo/audio_ep02.py           # saida/mix.wav
TRABALHADORES=3 MAX_PLACAS=2 .venv/bin/python producoes/ep02_presente_videogame/codigo/cenas_ep02.py
ffmpeg -i producoes/ep02_presente_videogame/_cache/video_sem_audio.mp4 -i producoes/ep02_presente_videogame/saida/mix.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest \
  producoes/ep02_presente_videogame/export/MC_ep02_presente_videogame_v1.mp4
.venv/bin/python producoes/ep02_presente_videogame/codigo/qa_ep02.py producoes/ep02_presente_videogame/export/MC_ep02_presente_videogame_v1.mp4
```
Memória: com 4 trabalhadores e 3 placas em cache por processo o container ficou sem memória; use 3 e `MAX_PLACAS=2`.
