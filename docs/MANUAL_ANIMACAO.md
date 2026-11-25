# Manual de Animação — Modo Curioso Studio AI

Versão 1.0 · Etapa 1. Baseado nos **13 MP4 processados** (folhas de contato a cada 2,5 s, tiras densas de 3–6 qps em trechos de close, e medição de movimento por fluxo óptico em todos os quadros) e no Padrão Modo Curioso (versão do skill).

Convenção: **[medido]** = medido por nós. **[visto]** = observado quadro a quadro. **[padrão]** = vem do Padrão / `index.html`, não reverificado.

> **Aviso:** o Padrão cita uma referência **v21** ("a mais animada", bonecos recortados animados no 1). **Esse vídeo não está no repositório.** As regras do "nível ação" abaixo vêm do Padrão e não foram verificadas por nós.

---

## 1. Princípio: quem se mexe é a câmera, não o boneco

Nas referências a sensação de movimento vem de três fontes, nesta ordem:
1. **Câmera:** quase todo plano tem movimento [medido: 86–98 % dos planos, por vídeo]. Ver seção 5.
2. **Efeitos:** partículas, ondas, raios, poeira, tremidas.
3. **Troca de pose e de expressão:** o personagem passa de uma pose para outra e segura.

A animação do personagem é **limitada, pose a pose**. Isso barateia a produção e é parte do estilo: não tente "consertar" com animação full.

## 2. Nível base (a maioria dos planos)

### 2.1 Pose a pose com pose segurada [visto]
- A troca de pose acontece em 2–4 quadros [padrão], ou **seca, sem intermediário** [visto: v18 a 55 s, de bravo para susto num corte interno de pose].
- Depois da troca, a pose fica **segurada** por 1–2 s, enquanto a câmera continua se movendo.
- Exemplo medido (v18, 54,6–58,6 s): close do Davi bravo (sobrancelha em V, boca fechada) → o dardo chega → olhos brancos arregalados e boca aberta, segurados ~2 s; a mão sobe numa única troca.

### 2.2 Boca: sem sincronia labial [visto + padrão]
- **Não há leitura de fonema.** No máximo a boca alterna entre "o" pequeno e linha (v10, 89,6–91,6 s, "CINCO ANOS"), sem acompanhar as sílabas.
- Na maior parte dos planos a boca fica fixa. A fala é carregada pela **legenda** e pela narração em off.
- Regra para nós: boca com 3 estados (fechada/linha, "o", aberta), trocados nas batidas da frase, não por sílaba.

### 2.3 Expressão muda dentro do plano [visto]
- A sobrancelha e os olhos mudam **no meio do plano**, na batida da fala (v10: neutro → bravo no mesmo close).
- Close de reação: 1 a 3 trocas de expressão.

### 2.4 Sempre vivo [padrão]
- Mesmo parado: respiração leve (escala vertical do tronco de 1–2 % em ciclo de ~3 s) e balanço de cabeça.
- Piscada ocasional (a cada 3–5 s, 3 quadros).

### 2.5 Biblioteca de expressões (rosto 2D em camadas)
| Expressão | Olhos | Sobrancelha | Boca |
|---|---|---|---|
| Neutro | ponto escuro com brilho | reta | linha |
| Convencido / tédio | pálpebra meio fechada | reta e baixa | meio sorriso de lado |
| Surpreso | arregalados, pupila pequena | alta e arqueada | "o" |
| Susto | **brancos, pupila mínima** | muito alta | aberta (interior escuro) |
| Bravo | ponto, levemente apertados | **em V** | linha para baixo ou dentes cerrados |
| Esforço / dor | **"><"** | franzida | aberta tensa |
| Triste / preocupado | ponto, olhando para baixo | inclinada para cima no centro | curva para baixo |
| Pensativo | olhando para cima e para o lado | uma levantada | "o" pequeno de lado |
| Sonolento / dormindo | fechados (linha curva) | relaxada | aberta (ronco, v13) |
| Feliz | arco fechado ou ponto | alta | sorriso |
| Poder ativo | **brilhando** (ciano, branco ou roxo) | conforme a emoção | conforme a emoção |

## 3. Nível ação (momentos de poder, golpe, clímax) [padrão, não verificado: v21 ausente]

Use só nos momentos de poder e de clímax. No resto, o nível base basta.
- Boneco 2D recortado com membros girando nas juntas e interpolação suave com easing, **animado no 1** (todo quadro muda).
- **Antecipação → ação → overshoot → assentamento** em toda ação.
- Ciclo completo de corrida.
- Soco termina em **quadro de impacto**: estilhaços ou silhuetas claras sobre linhas radiais, 1–2 quadros.
- Expressão troca dentro do plano: 2–3 trocas por close (surpreso → "><" → bravo).

O que verificamos nas referências que temos e que bate com isso [visto]: braço elástico atravessando o quarto (v15), corrida do personagem veloz (v19), quedas e voos de cima (v01), gelo crescendo e jato de fogo (v18).

## 4. Movimento local medido [medido]

O fluxo óptico separa o movimento da câmera (transformação de semelhança: zoom, pan, tilt, giro) do movimento **dentro** do quadro (personagens, efeitos). A métrica "movimento local" é a fração de pontos rastreados que **não** seguem a câmera, por plano (mediana do vídeo). Valores por vídeo estão em `AUDITORIA_REFERENCIAS.md`.

Resultado: mediana de **0,09** (9 % dos pontos rastreados se movem de forma independente da câmera). O mínimo é v16 (0,021, planos de diálogo e paisagem) e o máximo é v06 (0,18, chuva, raios e partículas de sal). Em v12 e v13 (0,14) dominam os efeitos de poder.

Leitura: valores baixos confirmam animação limitada (a maior parte da imagem anda junto com a câmera); os picos coincidem com planos de efeito (partículas, fogo, gelo).

## 5. Câmera (aplicada na composição)

| Movimento | Alvo | Medido nos 13 MP4 [medido] | Padrão [padrão] |
|---|---|---|---|
| Push-in lento | ~2 de cada 3 planos; 4–10 %/s; total 5–15 % no plano | 64–79 % dos planos; mediana por vídeo de 2,4 a 9,8 %/s | 62 %; 5,9 %/s; total 9 % |
| Pull-out | ~10–15 % dos planos | 9–29 % (mediana 14 %) | 10 %; −7 %/s; total −13 % |
| Pan | ~1 de cada 5 planos; ~14 % da largura | 14–53 % (mediana 34 %)† | 22 % |
| Tilt | ~1 de cada 5 planos; ~16 % da altura | 9–38 % (mediana 17 %)† | 24 % |
| Giro (roll) | ~10 %; ~6° | 12–53 % (mediana 28 %)† | 10 % |
| Crash-zoom | ~13–20 %; +40 % ou mais | 8–32 % (mediana 19 %) | 13 % |
| Plano parado | só em suspense | 0–14 % dos planos (mediana 4 %) | 7,5 % |
| Chicote (whip) | 0,13 s; borrão de movimento | 0–6,6/min (mediana 1,0); detector conservador, conta menos | 8/min |
| Tremida de impacto | ~1,4 % do quadro, 0,25–0,6 s | **não medido de forma confiável** pelo nosso detector | 28/min |

† Limite superior: o fluxo óptico soma paralaxe e movimento de personagem ao pan, ao tilt e ao giro. Os valores do relatório (22 %, 24 %, 10 %) são mais próximos da intenção de câmera.

**Curvas:** ease-out na maioria dos planos (o movimento começa rápido e assenta), ease-in-out em cerca de 1/4, ease-in em cerca de 1/8 [padrão].

**Tremida de impacto (receita):** deslocamento aleatório amortecido, amplitude inicial de 1,4 % do quadro, decaimento exponencial em 0,3–0,5 s, frequência de 18–24 Hz, junto com um SFX de impacto.

**Punch-zoom:** +7 % em 0,18 s (forte: até +75 %), ease-out [padrão].

**Mergulho de escala:** zoom contínuo enorme (×20 ou mais) da mão até a pele, as células e os átomos [padrão]. Visto como "entrar" num insert científico (v06, v07, v14).

Margem de render: renderize cada plano pelo menos **15 % maior** que 1080×1920 (ou em vetor) para o push-in e a tremida não mostrarem borda.

## 6. Efeitos animados (biblioteca) [visto]

| Efeito | Como se move | Onde |
|---|---|---|
| Ondas concêntricas / de choque | anéis translúcidos expandindo com ease-out e desaparecendo | v01 (água), v12, v13, v19 (ar "vira parede") |
| Raios e eletricidade | linhas brancas/azuladas quebradas, troca a cada 1–2 quadros, com bloom | v06, v15 |
| Aura de poder | contorno brilhante pulsando + partículas subindo | v01, v18 |
| Gelo crescendo | blocos surgindo em etapas de baixo para cima + estilhaços | v18 |
| Fogo | bola com textura de lava girando, faíscas, rastro | v12, v13, v18 |
| Jato d'água / água viva | linha branca em alta velocidade; serpente translúcida | v10 |
| Partículas | poeira dourada no feixe de luz, vapor, bolhas, letras/átomos flutuando | todos |
| Objetos flutuando | sobe devagar com balanço leve (ease-in-out) | v13 |
| Vapor tomando a tela | nuvem branca expandindo até estourar o quadro | v01 (~50 s) |
| Rede atômica | esferas puxadas por fios ou montando uma forma | v10, v16 |
| Holograma | personagem/objeto em azul translúcido com partículas internas | v14, v17 |

## 7. Ritmo da animação com a fala

- Toda troca de pose ou expressão cai **numa batida da narração** (o fim de uma frase ou a palavra-chave em amarelo).
- O efeito principal do plano começa junto com a palavra que o nomeia ("e a porta **voou**" → onda de choque no "voou").
- O número científico entra **junto** com a palavra do número (rótulo com pop de 97 → 100 % em 2 quadros).

## 8. Checklist de animação (por plano)
1. A câmera se move (salvo suspense)? Com ease-out?
2. Existe pelo menos uma troca de pose ou de expressão, ou um efeito animado?
3. As trocas caem nas batidas da narração?
4. Boca sem tentar sincronia labial (3 estados no máximo)?
5. Personagem "vivo" quando segurado (respiração e piscada)?
6. Nos momentos de poder: antecipação, golpe, overshoot e quadro de impacto?
7. Margem de render suficiente para o movimento de câmera?
