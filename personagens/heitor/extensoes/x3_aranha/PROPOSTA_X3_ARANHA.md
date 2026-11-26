# Proposta X3: aranha (escalada, balanço no fio e gesto de lançar)

26/11/2026 · **X3 APROVADA pelo diretor em 26/11/2026** ("Aprovado"), como proposta. O rig v2 continua intocado. Nenhum episódio ou história foi produzido.

## 1. Justificativa
O próximo poder na ordem aprovada é a **aranha**. Para ele, o Heitor precisa de três coisas que o rig v2 não tem:
1. **escalar paredes**, com mãos e pés presos na parede enquanto o corpo sobe;
2. **balançar pendurado num fio**, girando em torno da mão que segura;
3. **um gesto para lançar o fio.**

Este último é um gesto **próprio do Modo Curioso**: braço estendido e mão aberta com a palma à mostra. Ele **não copia** o gesto de nenhum personagem de terceiros, como manda a regra. Também ficaram de fora outras poses de terceiros muito conhecidas: agachado com uma mão no chão, pendurado de cabeça para baixo.

## 2. O que muda e o que NÃO muda
**Nada muda no rig v2.** O código fica em `personagens/heitor/extensoes/x3_aranha/aranha.py`.
- Do rig, usa só a API pública: `pose_base`, `esqueleto`, `desenhar`, `MAOS`, `ik_braco`, `mira_braco`, `ik2`, `cotovelo_invertido`.
- Da **X2**, aprovada, usa o corpo inclinado e o vento na roupa e no cabelo, durante o balanço.

| Parte | Como é feita | O que garante a identidade e a física |
|---|---|---|
| **Escalada de costas** (vista de trás, subindo uma parede de frente para a câmera) | ciclo em pares diagonais: mão direita + pé esquerdo, depois o outro par. Os apoios ficam **presos na parede** enquanto o corpo sobe 0,36 H/s (cerca de 12 cm/s). Braços e pernas são resolvidos pela **IK do próprio rig** | apoio parado **não desliza** (medido); joelhos abertos para os lados; cotovelos sempre pela regra anatômica do rig |
| **Escalada de perfil** (parede ao lado) | o mesmo ciclo, com o corpo um pouco inclinado para trás, as mãos na parede e as pontas dos pés apoiadas | idem |
| **Balanço no fio** (perfil) | pêndulo que gira em torno da **mão que segura** (a esquerda, o braço de trás no perfil, para o rosto ficar livre). O corpo segue o fio com um pequeno atraso; pernas e braço livre reagem ao movimento; a X2 põe o vento na roupa e no cabelo | o fio chega exatamente na mão (medido no desenho); vento da X2 sem mudanças |
| **Gesto de lançar** | braço estendido para o alvo (`mira_braco` do rig), mão aberta com a palma à mostra (vista "palma" do próprio rig) e punho levemente dobrado | estampa continua legível (OCR); erro de mira medido |

**API:**
- `Escalada(vista).desenhar(canvas, x0, y0, altura_px, t)`
- `Balanco(...).desenhar(canvas, x_ancora, y_ancora, comprimento_px, altura_px, t)` (devolve onde está a mão, para o fio)
- `pose_lancar(pose, vista, lado, alvo)`

O **fio** em si (cor, brilho, como gruda) é do **poder de aranha** (E8 parte 3), não desta extensão. Na demonstração há um fio provisório, uma linha simples.

## 3. Demonstração
- `saidas/X3_folha.jpg`: escalada de costas e de perfil em vários instantes, balanço em 4 instantes e gesto de lançar para 6 alvos.
- `saidas/X3_aranha_demo.mp4` (teste, não é história; com a X1 ligada):
  - **escalada de costas** num pilar entre duas lojas, numa **placa nova** da mesma rua com a câmera de frente para a parede, renderizada para esta demonstração em 7,7 min;
  - **balanço no fio** (tarde, perfil);
  - **gesto de lançar** (manhã, frente).
- `saidas/X3_aranha_quadros.jpg`: quadros do vídeo.

## 4. Testes (`teste_x3.py`, medidas em `saidas/x3_metricas.json`)
| Teste | Resultado |
|---|---|
| **Apoios presos na parede** (a cada quadro, 2 ciclos, no desenho a 900 px de altura) | costas: deslize máximo **0,003 px** por quadro; perfil: **0,000 px**. IK alcança a pegada com erro máximo de **0,0001 H** |
| **Contatos no desenho real** (o ponto da pegada cai na mão; o do pé, no tênis) | escalada de costas: mão na mão **100 %**, pé no tênis **100 %** · perfil: **100 % / 100 %** · balanço: o fio chega na mão em **100 %** (18 amostras) |
| **Juntas e cotovelos** (165 poses: ciclos completos, balanço, lançar para 6 alvos) | **0 violação** |
| **Estampa (OCR)** no gesto de lançar de frente, 4 alvos | **"Modo Curioso" lido nas 4.** O OCR também lê "88", "80" ou "38": são os dedos, não há texto novo. Erro de mira: **0,0°** |
| **Determinismo** | mesmo quadro duas vezes: **idêntico** (escalada e balanço) |
| **Tempo de desenho** (CPU, 900 px) | escalada 13–14 ms; balanço 10 ms (rodada final) |

## 5. Riscos e limitações
1. **Na vista de costas, o ponto de pegada do próprio rig fica fora da mão direita.** A função `encaixe_mundo` não espelha o encaixe nessa vista; é um limite do rig. A X3 contorna mirando o centro da palma, que fica sempre sobre a mão, sem mexer no rig.
2. **Joelhos abertos de costas:** a coxa gira para o lado (abdução), o que na vista de trás é o natural para escalar. O limite usado foi ±100°; o `modelo.json` só define o quadril na vista de lado.
3. **Escalada só sobe** (não desce nem anda de lado). **Balanço só de perfil.** Outras direções, como de frente vindo para a câmera, ficam para depois, se forem necessárias.
4. **O fio é provisório** na demonstração. O fio de verdade vem com o poder (E8 parte 3).
5. **As poses são de cartum**, com os limites medidos. A leitura estética é sua.

## 6. Vídeo e integridade (medido)
`X3_aranha_demo.mp4`: 366 quadros (**12,2 s**), 1080×1920, 30 q/s, marca d'água "MODO CURIOSO". Escalada 4,5 s, balanço 5,2 s, lançar 2,5 s. Composição média **2,41 s** por quadro (máximo 4,09 s, CPU), com a X1 ligada e, no balanço, a X2. Total: 15,4 min.

**Integridade:**
- assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`);
- nenhuma alteração pendente nesses caminhos;
- F1 6/6 OK.

**O que eu vi nos quadros:**
- a escalada lê bem: o pilar entre as lojas, os braços acima da cabeça e o corpo subindo;
- no balanço, o fio sai da mão de trás, o rosto fica livre e o cabelo vai para trás;
- no gesto de lançar, a mão aparece aberta com a palma à mostra.

**O que não foi verificado:** a leitura estética e o ritmo são seus. A placa nova não vai para o repositório (fica no cache de placas, como as outras); ela é refeita pela receita em ~8 min.

## 7. Como ligar e como desfazer
- **Ligar** (só depois da aprovação): no desenhista do plano, usar `Escalada(...).desenhar`, `Balanco(...).desenhar` ou `pose_lancar`.
- **Desfazer:** não usar. Nenhum arquivo do rig e nenhum quadro aprovado depende da X3.

## 8. Como reproduzir
```
.venv/bin/python personagens/heitor/extensoes/x3_aranha/teste_x3.py           # tudo (vídeo ≈ 20 min; a placa nova fica no cache)
.venv/bin/python personagens/heitor/extensoes/x3_aranha/teste_x3.py X3_1_plantados X3_7_folha
```
