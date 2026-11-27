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

## QA (`saida/qa_relatorio.json`) — 16/16
| Verificação | Resultado medido |
|---|---|
| Formato / duração | 1080×1920 · 30 qps · H.264 + AAC · 88,4 s (narração 85,4 s + cartela final) |
| Ritmo | 49 planos · mediana 1,65 s · 33 cortes/min · 1 plano acima de 3 s |
| Movimento dos personagens | 87 % dos quadros com ação visível; plano com menos ação: 64 % (1ª passada: 69 %; 30 planos refeitos com mais movimento) |
| Câmera | em movimento em 100 % dos quadros, nenhum plano parado |
| Mapa fala → imagem | 48 palavras-chave, cada uma com a ação no plano certo no instante em que é dita |
| Cotovelos | 4.716 braços verificados (todas as poses de todos os quadros), 0 invertidos |
| Rig do Heitor | intacto |
| Pés | 0,00 mm de deslize no ciclo (o personagem avança à velocidade do ciclo) |
| Loudness | −14,1 LUFS · pico −1,5 dBTP |
| Números na tela | 13 rótulos grandes |
| Legendas | 89 blocos · média 2,6 palavras · máx. 3 · amarelo em 27 % dos blocos |
| Identidade | marca d'água "MODO CURIOSO"; estampas "Modo Curioso"; nenhum logotipo de terceiros na imagem |

## Limitações (honestas)
1. **Destaque amarelo nas legendas em 27 % dos blocos** (o padrão medido é ~42 %). Aumentar exige refazer todos os quadros.
2. **Juca sentado de frente:** o rig é 2D, então a coxa vista de frente é só um encurtamento; em alguns planos (C1, C2) ele pode
   parecer meio "de pé na frente do sofá". De perfil (C3) e de costas (C4) lê bem.
3. **Zoom brusco nas telas:** em P11 ("instalado") e P44 ("primeira missão") o fim do zoom corta a borda do texto da TV
   ("INSTALADO", "CONCLUÍDA").
4. **Personagens desenhados por cima do cenário** com a profundidade do personagem mais próximo (mesmo compositor do EP01):
   quando há dois personagens em profundidades diferentes, o mais distante não é coberto pelos móveis.
5. **Close do botão (P21, P46):** é um insert 2D (mão do rig + videogame) porque o plano da TV é estreito demais para o
   Juca caber em pé ao lado do rack.
6. **A cidade do jogo** é a rua aprovada da E6 (bairro brasileiro) ao crepúsculo, com HUD próprio; não imita o jogo real.
7. **Trilha e efeitos** continuam procedurais (biblioteca de música/SFX ainda é pendência do diretor).
8. **Render:** com 3 processos, o trecho 29–59 s caiu por falta de memória na 1ª tentativa; foi refeito em partes e emendado
   (`codigo/refazer_planos.py`). Contagem final de quadros conferida: 2.652.
