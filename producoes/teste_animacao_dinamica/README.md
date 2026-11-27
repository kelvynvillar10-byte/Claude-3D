# Cena de prova — animação dinâmica (27/11/2026)

**Vídeo:** `export/MC_teste_animacao_dinamica_v1.mp4` (1080×1920, 30 qps, **19,7 s**, H.264 + AAC, −14 LUFS).
**Folha de contato:** `saida/folha_contato_2qps.jpg`. **QA:** 11/11 (`saida/qa_relatorio.json`).

Mesmo trecho da narração final do EP01 (39,20–58,90 s: "Mas existe um perigo ainda maior… e você poderia estar em
perigo"), refeito com a diretriz de animação dinâmica: personagens sempre em movimento, câmera que acompanha a ação,
cenário vivo e cada palavra-chave com ação na tela. A voz é a mesma do EP01, sem edição; o EP01 não foi alterado.

## Comparação medida com o mesmo trecho do EP01
| | EP01 (v1) | Cena de prova |
|---|---|---|
| Planos | 10 | 13 |
| Plano mediano | 2,28 s | 1,35 s |
| Cortes/min | 27 | 37 |
| Planos com o Heitor andando ou correndo | 0 | 6 (andar, recuar, correr) |
| Animais que se deslocam | 0 | gato anda e dá o bote; aranha corre e avança |
| Câmera em movimento | zoom lento em todo plano, sem acompanhamento | 100 % dos quadros: acompanha o alvo, zoom brusco, aproximação, subida |
| Quadros com ação visível (deslocamento, gesto, troca de pose/vista) | não medido no EP01 (poses seguradas) | 91 % |

## O que acontece na tela (mapa fala → imagem, `saida/mapa_fala_imagem.json`)
| Palavra | Ação |
|---|---|
| perigo | o Heitor caminha pelo tapete; a câmera acompanha |
| maior | ele para, vira para a câmera assustado; aproximação rápida |
| animais | a sombra do gato varre o chão enquanto ele olha em volta |
| casa | ele chega ao canto da parede |
| aranha | a aranha entra correndo; zoom brusco nela; ele pula de susto |
| assustadora | ela ergue as patas da frente; ele recua tremendo, braços à frente |
| gato / curioso | o gato entra andando (ciclo de 4 patas); o Heitor olha para cima |
| inofensivo | o gato sentado inclina a cabeça e pisca devagar; a câmera sobe até o rosto dele |
| predador | close do olho: a pupila dilata |
| movimento / errado | o Heitor recua passo a passo e tropeça |
| (poderia) | a pata desce com as garras; ele pula e vira para fugir |
| perigo | ele corre; o gato dá o bote onde ele estava (impacto e poeira) |

## Ferramentas novas (propostas A1–A3, fora do rig)
`codigo/atuacao.py`. O rig v2.1 não foi alterado.
- **Trajeto do personagem:** andar, correr, andar de costas, parar, virar (perfil → três-quartos → frente), pulo de susto, tropeço, pose de pé viva (respiração, peso, cabeça, tremor de medo), expressão e direção do olhar no tempo.
- **Pés sem deslizar:** o personagem avança no mundo à velocidade exata do ciclo do rig (caminhada 9 cm/s, corrida 20 cm/s na escala de 5 cm). Andar para trás usa o ciclo com o tempo invertido. O gato ganhou um ciclo de caminhada com pés plantados (`personagens/animais/gato.py`).
- **Câmera que acompanha:** um recorte 2D dentro da sobra da placa faz o enquadramento sem revelar a borda. Uma parte vira translação real, com paralaxe limitada pelo chão mais próximo. O atraso natural é de 0,2–0,35 s, há borrão de movimento nas panorâmicas rápidas e uma deriva de zoom em todo plano.
- **Cenário vivo:** poeira no feixe de luz (cintila, flutua e tem paralaxe), sombra do gato, nuvem de poeira no impacto.
- Duas placas novas da sala, baixas e próximas, para o Heitor aparecer grande o bastante para atuar: `T1_sala_lado` e `T2_sala_baixo` (`codigo/placas_teste.py`, ~6 min cada). Nada flutuando, nenhum texto 3D.

## QA (medido)
Formato, duração, ritmo, movimento dos personagens, câmera, mapa fala → imagem (13 palavras no plano certo), cotovelos (1.104 braços, 0 invertidos), rig intacto, pés sem deslizar (0,00 mm), loudness (−14,1 LUFS, −1,5 dBTP), marca d'água.

## Limitações (honestas)
1. **Ritmo:** plano mediano de 1,35 s, um pouco abaixo da faixa de 1,5–2 s da diretriz. Isso segue as frases curtas deste trecho. Planos podem ser fundidos se o diretor preferir.
2. **D02 e D08** têm menos ação (47 % e 74 % dos quadros): são a virada para a câmera e a subida da câmera até o gato. O personagem respira e treme o tempo todo, mas ali o movimento principal é da câmera.
3. Gato e aranha continuam desenhados sobre o cenário, com a profundidade do Heitor. Em D05 o Heitor fica cortado na borda durante o zoom na aranha; em D13 (plano aberto da fuga) ele aparece pequeno.
4. As trocas de pose do gato (andando → sentado → agachado) acontecem no corte, não animadas.
5. Num ângulo exato do braço, o skia falha ao unir os contornos do rig. O desenho repete com 0,3° de diferença; é invisível e o rig não foi tocado.
6. Sombras de contato são desenhadas depois da composição, para não clarear na borda semitransparente (achado do compositor que o diretor decidiu não corrigir).
7. Trilha e efeitos continuam procedurais e temporários.

## Reproduzir
```
.venv/bin/python producoes/teste_animacao_dinamica/codigo/placas_teste.py          # placas (cache)
.venv/bin/python producoes/teste_animacao_dinamica/codigo/audio_teste.py           # saida/mix.wav
TRABALHADORES=3 MAX_PLACAS=1 .venv/bin/python producoes/teste_animacao_dinamica/codigo/cena_dinamica.py
ffmpeg -i producoes/teste_animacao_dinamica/_cache/video_sem_audio.mp4 -i producoes/teste_animacao_dinamica/saida/mix.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest producoes/teste_animacao_dinamica/export/MC_teste_animacao_dinamica_v1.mp4
.venv/bin/python producoes/teste_animacao_dinamica/codigo/qa_teste.py producoes/teste_animacao_dinamica/export/MC_teste_animacao_dinamica_v1.mp4
```
