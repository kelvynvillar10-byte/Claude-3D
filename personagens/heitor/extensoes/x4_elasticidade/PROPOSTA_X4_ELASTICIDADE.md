# Proposta X4: elasticidade (braços e pernas que esticam, só eles)

26/11/2026 · **X4 APROVADA pelo diretor em 26/11/2026** ("Aprovado e pode continuar"), como proposta. O rig v2 continua intocado. Nenhum episódio ou história foi produzido.

## 1. Justificativa
A elasticidade é o último poder da ordem aprovada. Ela exige que **braços e pernas mudem de comprimento**, e o rig v2 não tem esse movimento. É a extensão mais delicada para a identidade, porque mexe na proporção do corpo. Por isso ela se limita a:
- **só braços e pernas** (tronco, cabeça, mãos e pés nunca mudam);
- **voltar exatamente** ao corpo original no fim.

**Movimentos próprios do Modo Curioso:**
- **alcance**: a mão vai longe, pega ou toca algo e volta;
- **pernas de pau**: as pernas crescem, ele fica alto e volta.

**Ficaram de fora de propósito** o soco esticado com o braço enrolado e outros golpes de borracha muito conhecidos de personagens de terceiros, como manda a regra.

## 2. O que muda e o que NÃO muda
**Nada muda no rig v2.** O código fica em `personagens/heitor/extensoes/x4_elasticidade/elasticidade.py`.

O rig já tem o **escorço**: ele encurta um osso no próprio eixo sem achatar a mão nem o pé, porque o osso filho não herda a escala. A X4 usa esse mesmo mecanismo do próprio rig com valores **maiores que 1**.

| Regra | Por quê | Medido |
|---|---|---|
| estica só o **antebraço** (até 8×) | o braço de cima tem a **manga**, que fica do tamanho original | manga igual ao rig sem esticar |
| estica só a **coxa** (até 3×), e a pelve sobe o mesmo tanto | a canela tem a **barra dobrada da calça**; os pés ficam no chão | tênis e barra iguais; tronco e cabeça só sobem |
| a **mão** é sempre a do rig | o escorço também alongaria a ponta arredondada do antebraço, que a partir de ~5× apareceria além dos dedos | mão idêntica (IoU 1,0) |
| **espessura** igual | o rig escala só o comprimento; o contorno é desenhado depois, com traço normal | largura do antebraço medida |
| **volta exata** | uma **mola** amortecida: estica com uma passada de ~12 %, segura, volta com um pequeno quique e termina em 1,0 exato | desenho final **idêntico** ao rig |

**Como a mão fica sempre a do rig:** a X4 desenha numa camada própria.
1. Primeiro desenha o Heitor esticado, inteiro. Fora da região além do punho, os pixels são exatamente os do rig.
2. Depois apaga **só** a faixa além do punho e a redesenha a partir do Heitor com o antebraço normal, deslocado para o punho esticado.

**API:**
- `alcance(pose, vista, lado, alvo, k)` devolve a pose; `k` vem da `mola(t)`.
- `pernas_de_pau(pose, escala)`.
- `elasticidade.desenhar(...)` substitui `heitor_v2.desenhar` quando o braço está esticado.

## 3. Demonstração
- `saidas/X4_folha.jpg`: alcance para 5 alvos (frente e perfil) e pernas de pau ×1,0, ×1,8 e ×2,6.
- `saidas/X4_elasticidade_demo.mp4` (teste, não é história; com a X1 ligada):
  - **alcance de frente** até a placa "30" (manhã);
  - **alcance de perfil** até a prateleira da quitanda (tarde);
  - **pernas de pau** de perfil (tarde).
- `saidas/X4_elasticidade_quadros.jpg`: quadros do vídeo.

## 4. Testes (`teste_x4.py`, medidas em `saidas/x4_metricas.json`)
| Teste | Resultado |
|---|---|
| **Mão** (5 alcances, escorço de 4,5× a 7,9×; comparada com a do rig no mesmo lugar) | forma **idêntica** (IoU **1,000**); 99,5–99,8 % dos pixels iguais; o resto é anti-aliasing da costura no punho, coberta pela mão |
| **Manga** (o braço de cima não estica) | 99,8–100 % dos pixels iguais (diferenças de anti-aliasing do contorno do braço, até 28 níveis de 256) |
| **Tênis e barra da calça** (pernas de pau) | ×1,8: 99,99 %; ×2,6: 99,87–99,93 % dos pixels iguais. As diferenças ficam **acima da barra** (0,48–0,55 H do chão), onde a ponta arredondada da coxa esticada encosta na canela, na mesma cor do jeans. **Tênis e barra em si não mudam** |
| **Tronco e cabeça** (pernas de pau) | iguais, só deslocados para cima (99,3–99,7 % dos pixels) |
| **Espessura do antebraço** (no meio do osso) | esticado 33,0–33,5 px × normal 33,0–33,5 px: diferença ≤ **0,5 px** (a 800 px de altura) |
| **Volta exata** (fim da mola) | mola = **0,0** e desenho **idêntico byte a byte** ao rig (3 alcances e pernas de pau) |
| **Alcance** (a palma chega ao alvo) | erro **0,0 px** nos 5 alvos |
| **Juntas e escorço** (308 poses ao longo das animações) | **0 violação** (na passada da mola o escorço é limitado ao teto) |
| **Estampa (OCR)** durante o alcance de frente | **"Modo Curioso" lido nas 3** |
| **Determinismo** | mesmo quadro: **idêntico** |
| **Desenho fora da mão** | com o braço esticado, `elasticidade.desenhar` só muda pixels até ~110 px da palma (a faixa redesenhada) e não apaga o fundo (0 pixels pretos sobre fundo cinza) |

**Vídeo:** 240 quadros (**8,0 s**), 1080×1920, 30 q/s, marca d'água "MODO CURIOSO"; composição média **2,06 s** por quadro (máximo 3,25 s, CPU), com a X1 ligada.

**Integridade:**
- assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`);
- nenhuma alteração pendente nesses caminhos;
- F1 6/6 OK.

**Correções feitas durante a proposta:**
1. A ponta arredondada do antebraço esticado aparecia além dos dedos. Corrigido com a faixa redesenhada.
2. O primeiro recorte do skia mudava levemente o anti-aliasing do corpo todo (693 pixels). Corrigido: o Heitor é desenhado sem recorte e só a faixa é apagada e redesenhada.
3. A borracha apagava o fundo quando o desenho era feito direto sobre um fundo opaco (quadrados pretos na folha). Corrigido com uma camada própria.
4. A passada da mola passava do teto do escorço. Agora é limitada.

**O que não foi verificado:** a leitura estética e o ritmo são seus.

## 5. Riscos e limitações
1. **Alongar 8× é muito.** É o teto técnico; na produção, você pode definir um teto menor.
2. **O braço estica em linha reta** (não faz curva nem enrola). Curvas exigiriam desenhar o braço fora do rig, o que é outra extensão.
3. **O antebraço esticado afina um pouco mais devagar** (a forma do rig vai de 0,165 H no cotovelo a 0,13 H no punho, agora numa distância maior). A largura no meio continua a mesma (medido).
4. **A costura da faixa redesenhada** fica no punho, coberta pela mão. Medido: menos de 0,6 % dos pixels da mão com diferença de anti-aliasing.
5. **As poses são de cartum**, com os limites medidos. A leitura estética é sua.

## 6. Como ligar e como desfazer
- **Ligar** (só depois da aprovação): usar `alcance`/`pernas_de_pau` na pose e `elasticidade.desenhar` no lugar de `heitor_v2.desenhar`.
- **Desfazer:** não usar. Com escorço 1, `elasticidade.desenhar` é o próprio `heitor_v2.desenhar` (medido: idêntico).

## 7. Como reproduzir
```
.venv/bin/python personagens/heitor/extensoes/x4_elasticidade/teste_x4.py          # tudo (vídeo ≈ 10 min)
.venv/bin/python personagens/heitor/extensoes/x4_elasticidade/teste_x4.py X4_1_partes X4_8_folha
```
