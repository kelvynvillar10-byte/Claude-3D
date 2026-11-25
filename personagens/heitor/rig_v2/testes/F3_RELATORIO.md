# Relatório da fase F3 — Heitor rig v2 (PROPOSTA)

25/11/2026 · Mãos e gestos: dedos individuais, segurar e soltar um objeto, acenar, apontar e reações.
> Registro histórico da fase de proposta. **O rig v2 foi aprovado como oficial em 25/11/2026** (ver `RELATORIO_FINAL.md`).

**Nada aqui está aprovado automaticamente.** F1 e F2 foram aprovadas pelo diretor; a F3 aguarda avaliação.

## O que foi construído
| Componente | Arquivo | Função |
|---|---|---|
| Clipes de gesto | `codigo/gestos.py` (`Clipe`, `curva`) | Quadros-chave por canal, com curvas `suave`, `saida`, `entrada` e `volta` (passa do ponto e assenta). Interpola números, poses de mão dedo a dedo e junta a junta, e expressões parâmetro a parâmetro |
| Alcançar | `gestos.py` (`ik_braco`) | Braço e antebraço levam o **ponto de pega da mão** até um alvo. O erro é medido no esqueleto real e corrigido iterativamente |
| Apontar | `gestos.py` (`mira_braco`, `erro_mira`) | Braço quase reto (cotovelo a 8°) com o eixo da mão e do indicador **mirando** o alvo. É diferente de alcançar: a mão não vai até o alvo |
| Objeto segurado | `heitor_v2.py` (`ENCAIXE`, parâmetro `objeto` de `desenhar_mao`) e `gestos.py` (`Objeto`) | O objeto fica preso ao ponto de pega e é desenhado na camada certa. Na vista de lado, fica entre a palma e o indicador, para o dedo "abraçar" o objeto. Ao soltar: gravidade, quique (restituição 0,5) e atrito |

Mudança no rig: só no desenho da mão **quando há objeto**. Sem objeto, a mão é desenhada exatamente como antes, e a F1 foi reverificada: 6/6 vistas OK, valores idênticos.

## Testes executados (vídeo renderizado e medição pela cinemática real do rig)
Vídeos em 1080×1920, 30 qps, H.264. Todos juntos (24 s): `F3_todos_os_testes.mp4`. Métricas: `f3_metricas.json`. Folha quadro a quadro: `*_folha.jpg`.

| Teste | Arquivo | Resultado medido | Verificação visual |
|---|---|---|---|
| T4 dedos individuais | `T4_dedos_individuais.mp4` (7,9 s) | Cada dedo dobra sozinho: polegar 70°, os outros 95°. **Movimento dos outros dedos na janela de cada um: 0,0°**. Depois: contagem 1–5, punho, abrir e "onda" dos dedos | Dorso e palma lado a lado. A dobra lê como dedo dobrando, por escorço na vista frontal da mão. Contagem legível (conferida no quadro do "2") |
| T5 segurar e soltar | `T5_segurar_soltar.mp4` (5,2 s) | Pega aos **1,33 s**, segura **61 quadros**; **distância bola–mão enquanto segura: 0,0** (presa ao ponto de pega); erro de alcance ≤ **0,0085 H** (~2 px); solta aos **3,37 s**; a bola **não atravessa o chão** e para no chão | Estende o braço com a mão abrindo, a mão fecha em volta da bola, ergue até o peito, estende, abre os dedos, a bola cai e quica. Expressão: pensativo → alegria → surpresa → preocupação |
| T6 acenar e apontar | `T6_acenar_apontar.mp4` (6,2 s) | Aceno: **2,2 Hz medido** (FFT) para 2,2 Hz pedido, amplitude ±24° no antebraço; **erro de mira 0,0°** nos 40 quadros em que segura o apontar | De frente: braço ao lado com o antebraço para cima e a palma aberta, acenando com alegria; abaixa; aponta para a estrela com o indicador, com surpresa |
| T6b reações | `T6b_reacoes.mp4` (5,0 s) | Susto: **antecipação** (agacha 0,11 H) → pulo de **0,28 H** → pouso amortecido → tremor; **pés parados no chão quando não está no ar (variação 0,0 H)**. Comemoração: agacha, pula, punho erguido com **overshoot de 11,1°** que assenta | Susto: "mãos ao alto" (braços abertos, antebraços para cima, dedos esticados) e olhos arregalados (medo), depois preocupação. Comemoração: alegria, punho cerrado erguido com o antebraço para cima |

## Correção pedida pelo diretor: cotovelos invertidos
O diretor apontou que a anatomia dos cotovelos parecia invertida. **Confirmado** nos quadros: no aceno (T6), no susto e no punho da comemoração (T6b), e também na pose "acenar" da folha de articulações da F1, o braço subia e o antebraço dobrava **para fora**, com o cotovelo apontando para a cabeça. Nenhuma métrica anterior verificava isso.

- **Regra anatômica, agora verificável** (`gestos.cotovelo_invertido`, tolerância de 5°):
  - No perfil, o antebraço só dobra para a frente.
  - De frente, de costas e no 3/4, com o braço acima da horizontal, o antebraço só dobra para cima, em direção à cabeça.
  - Abaixo da horizontal os dois sentidos são possíveis, porque o úmero gira (mão na barriga, mão para fora).
- **Verificador validado:** reprova as 5 poses antigas e aprova as corrigidas, a "mão na barriga" e o perfil do T5. Também reprova uma hiperextensão de perfil criada de propósito.
- **Poses corrigidas:** aceno (braço a 108°, antebraço +62° ±24°), susto ("mãos ao alto"), punho erguido e a pose "acenar" da folha F1. A função de apontar agora só dobra o cotovelo no sentido anatômico.
- **Auditoria completa** (`codigo/verificar_cotovelos.py` → `verificacao/cotovelos.md`): 31 poses das folhas da F1, 360 quadros da F2 (caminhada e corrida nas 3 vistas) e todos os quadros da F3, com **0 cotovelos invertidos**. O T4 só mostra a mão, então não entra nessa conta. A F1 foi reverificada: 6/6 OK.
- Cada teste da F3 agora registra `quadros_com_cotovelo_invertido` em `f3_metricas.json`.

## Correção do escorço (autorizada pelo diretor)
**Antes:**
- Em `esqueleto()`, cada osso filho herdava a escala de escorço do pai: a coxa encurtando fazia a canela e o pé encurtarem junto, e o mesmo valia para braço, antebraço e mão.
- A perna de frente ficava curta demais e o tênis e a mão ficavam achatados.

**Agora:** o filho nasce na ponta encurtada do pai, mas tem só o próprio escorço. A mão e o pé nunca são achatados.

**Re-medição completa:**
- **F1:** as 4 folhas são idênticas byte a byte (mesmo checksum), porque não usam escorço. Verificação: 6/6 OK.
- **F2 perfil** (caminhada, corrida, camadas): métricas **idênticas** às aprovadas, porque o perfil não usa escorço.
- **F2 frente e costas:** a altura do tornozelo do pé de apoio, descontado o deslocamento de profundidade intencional, agora parte de **0,22 H, igual ao perfil**. Antes partia de 0,234 H na caminhada e 0,264 H na corrida, ou seja, o pé flutuava. O tênis deixou de ser achatado.
- **Profundidade de frente e de costas:** a diferença entre os pés passou a ser **simétrica em torno do chão**. O pé mais perto da câmera aparece até 0,07 H mais baixo, e o mais longe, mais alto. Antes, o erro de escala empurrava os dois para cima. O ajuste de profundidade (0,13) é o mesmo aprovado na F2. Se você achar o efeito forte demais, basta reduzir esse número.
- **F3:** todas as métricas se mantêm. Cotovelos: 0 invertidos em F1, F2 e F3.

## Problemas encontrados pelos testes e corrigidos
1. **T4: as duas mãos se sobrepunham e saíam do quadro.** Escala e espaçamento refeitos.
2. **T5: a mão nunca pegava a bola.** O ponto de pega na vista de lado fica fora do eixo do antebraço, e a IK ignorava isso: dizia "erro 0", mas errava por ~0,05–0,08 H. Agora a IK mede o ponto real e corrige, e o erro reportado é o medido.
3. **T5: a bola parecia apoiada em cima dos dedos.** O ponto de pega estava do lado errado da mão (o do polegar). Foi movido para a concha dos dedos e a ordem de camadas foi ajustada.
4. **T5: a bola caía encostada no tênis.** O ponto de soltura foi adiantado.
5. **T6: apontar com IK de alcance dobrava o cotovelo**, com erro de mira de 24°. Criada a função de **mira** (braço quase reto, eixo da mão para o alvo): erro de 0,0°.
6. **T6: a estrela-alvo ficava fora da tela**, e o braço que acena era cortado na borda. Enquadramento refeito.
7. **T6b: a pose de susto parecia "mãos na cintura".** Braços refeitos para subir e abrir.
8. **T6b: no agachamento, os pés flutuavam até 0,05 H.** Causa encontrada no rig: a escala de escorço da coxa era **herdada** pela canela e pelo pé. **Corrigido no rig com autorização do diretor** (ver "Correção do escorço"). Agora coxa e canela encurtam por igual, e os pés ficam exatos (0,0 H).

## Limitações (registradas, não escondidas)
1. **Mão de frente em tamanho de cena é pequena** (~0,4 H, ~115 px num personagem de 1.150 px). Gestos amplos (acenar, apontar, punho) leem bem. Dedos isolados só leem em close; por isso o T4 é um close da mão.
2. **A pegada na vista de lado é estilizada:** o indicador abraça o objeto pela frente, e os outros três dedos são um bloco atrás. Objetos que exigem pegada específica (alça, caneta) precisarão de pontos de pega e poses de mão próprios.
3. ~~Herança da escala de escorço~~: **corrigida** com autorização do diretor (ver "Correção do escorço").
4. **O agachamento de frente** só encurta as pernas (escorço). Não há joelhos abrindo para os lados, o que daria mais leitura de peso.
5. **A física da bola é simples** (gravidade, quique e atrito; sem rotação nem colisão com o corpo). Na queda, a bola é desenhada na frente da perna, como se estivesse do lado próximo da câmera.
6. **Os dedos chegam a −10°** (leve hiperextensão) no overshoot ao abrir a mão. Maior variação: 34,9°/quadro, nas trocas rápidas da contagem. É intencional (gesto rápido, como o de um dedo que estala), mas pode ser suavizado trocando a curva `volta` por `saida`.
7. **Blender CPU:** não afeta estes testes (personagem 2D; os 4 testes renderizam em menos de 1 minuto no total).
8. **Naturalidade:** as métricas garantem isolamento dos dedos, objeto preso à mão, mira, frequência e pés no chão. Se o gesto "parece natural" é avaliação visual e cabe ao diretor.

## Próxima fase (só com autorização): F4
Expressões animadas (T7: transições entre surpresa, medo, alegria e preocupação, com piscada e fala), teste em cena (T8: o Heitor num cenário, combinando caminhada, gesto e objeto) e relatório final do rig v2.
