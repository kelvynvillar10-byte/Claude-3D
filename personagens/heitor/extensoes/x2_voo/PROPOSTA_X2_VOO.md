# Proposta X2: voo (poses de voo, roupa e cabelo ao vento)

26/11/2026 · **X2 APROVADA pelo diretor em 26/11/2026** ("Aprovado"), como proposta: inclui a barra solta sobre o cós do jeans (seção 5, item 1). O rig v2 continua intocado. Nenhum episódio ou história foi produzido.

## 1. Justificativa
O próximo poder na ordem aprovada é o **voo**. O rig v2 hoje só anda, corre, gesticula e aponta. Para voar, o Heitor precisa de três coisas que o rig não tem:
1. **poses de voo**: preparar, sair do chão, pairar, voar reto, fazer curva, pousar;
2. **corpo inclinado**: no voo reto ele fica quase deitado no ar; na curva, inclina para o lado;
3. **roupa e cabelo ao vento**: sem isso, ele parece um boneco parado sendo arrastado.

## 2. O que muda e o que NÃO muda
**Nada muda no rig v2.** O código fica em `personagens/heitor/extensoes/x2_voo/voo.py` e usa só a API pública do rig: `pose_base`, `esqueleto`, `desenhar`, `MAOS`, `EXPRESSOES`, `ik2`, `misturar`.

| Parte | Como é feita | O que garante a identidade |
|---|---|---|
| **Poses de voo** (11): perfil = agachar, impulso, pairar, cruzeiro, pousar · frente e costas = pairar, impulso, curva | são só **dados de pose** (ângulos do próprio esqueleto), como a caminhada do rig | todas dentro dos limites de junta do `modelo.json` e da regra do cotovelo do rig (medido em 484 poses) |
| **Corpo inclinado** | gira o desenho inteiro em torno da pelve, **por fora** do rig (transformação do canvas) | o desenho é o mesmo; sem inclinação, é **idêntico pixel a pixel** ao rig puro; a estampa gira junto e nunca espelha |
| **Vento: cabelo** | 4 mechas desenhadas **atrás** da cabeça, saindo do lado para onde o ar vai, ondulando | cores `cabelo`/`cabelo_s` e o mesmo contorno; o cabelo do rig continua inteiro por cima |
| **Vento: camiseta** | ondas nas laterais (atrás da silhueta), mangas abrindo (atrás) e a **barra solta** quando o ar corre do ombro para a barra | cores `camisa`/`camisa_s`. A barra é a **única peça que passa por cima do desenho**, e só sobre o cós do jeans, recortada para nunca cobrir braço, mão, camiseta, estampa ou rosto |

**API:** `voo.desenhar(canvas, x_pelve, y_pelve, altura_px, vista, direcao, pose, rosto, inclinacao, vento, t)`. O `vento` é a direção do ar em relação ao Heitor na tela (o contrário da velocidade); o módulo, de 0 a 1, dá a intensidade. Vento 0 resulta no rig sem vento.

## 3. Demonstração
- `saidas/X2_folha_poses.jpg`: as 12 situações de teste, **sem | com vento**, lado a lado.
- `saidas/X2_voo_demo.mp4` (teste, não é história; **com a X1 ligada**):
  - **tomada 1** (tarde, perfil): de pé, agacha, impulso, sobe, paira, inclina e sai voando;
  - **tomada 2** (manhã, frente): paira e faz curvas para os dois lados.
- `saidas/X2_voo_quadros.jpg`: quadros do vídeo.

A sombra no chão que diminui com a altura é desenhada pela cena da demonstração, não pela extensão. Ela é parte do poder de voo (E8 parte 2).

## 4. Testes (`teste_x2.py`, medidas em `saidas/x2_metricas.json`)
| Teste | Resultado |
|---|---|
| **Desenho do rig intacto** (12 situações, com × sem vento, pixel a pixel) | Em 8 situações, **0 pixel** do rig muda. Nas 4 com a barra solta (impulso de perfil e de frente, cruzeiro e o espelho dele), muda **1,7–1,8 %** do rig, **só** em cores do jeans: `jeans`, `jeans_s`, `barra` (costuras dos bolsos), `contorno` e mistura de borda. **Nenhuma** cor proibida (pele, camiseta, estampa, cabelo, olhos) coberta em nenhum caso |
| **Paleta das peças novas** | 95,8–100 % dos pixels em cores oficiais permitidas; o resto é a borda suavizada entre duas delas. **Nenhuma outra cor** |
| **Estampa (OCR)** nas poses de frente, com e sem vento, inclusive o corpo a ±22° | **"Modo Curioso" lido nas 8 leituras.** Na pose de impulso o OCR também lê "88": são os dedos do punho fechado, não há texto novo |
| **Juntas** (11 poses × 33 instantes + transições de pé → agachar → impulso → pairar → cruzeiro → pousar, e as de frente e costas) | **484 poses, 0 violação** (quadril, joelho, tornozelo, punho e regra do cotovelo do rig) |
| **Quanto o vento acrescenta** | área de 0,8–2,1 % (pairar, curva, pousar) a 4,2 % (cruzeiro); alcance máximo além da silhueta **0,30 H**, as mechas no cruzeiro |
| **Determinismo** | mesmo quadro duas vezes: **idêntico**; vento 0 = sem vento: **idêntico**; sem inclinação = rig puro: **idêntico** |
| **Tempo** (CPU, 900 px de altura) | 10,2 ms sem vento → **12,0 ms** com vento por desenho |
| **Integridade** | assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

## 5. Riscos e limitações
1. **A barra solta cobre o cós do jeans** (até 1,8 % do desenho, só jeans). É a única exceção à regra "o vento nunca cobre o desenho" e é como uma camiseta de verdade se comporta. Se você preferir, ela pode ficar só atrás; aí o vento na camiseta quase não aparece no voo reto, porque o quadril e o braço cobrem.
2. **O vento é 2D, atrás da silhueta:** as ondas só aparecem onde passam da borda do desenho. Não há dobra de tecido por cima da camiseta, e o jeans e o tênis não balançam.
3. **Voo de frente vindo para a câmera** (escorço forte dos braços) **não está incluído.** De frente há pairar, impulso e curva; o voo reto é de perfil. Se for necessário, é uma pose a mais, apresentada depois.
4. **As poses são de cartum**, com os limites anatômicos medidos. A leitura estética é sua.

## 6. Vídeo (medido)
`X2_voo_demo.mp4`: 300 quadros (**10,0 s**), 1080×1920, 30 q/s, marca d'água "MODO CURIOSO". Tomada 1: 6 s; tomada 2: 4 s. Composição média **2,56 s** por quadro (máximo 3,62 s, CPU), com cenário, céu animado, X1 e X2. Total: 13,3 min. As placas já estavam prontas, vindas da E6.

**O que eu vi nos quadros:**
- a decolagem lê bem: agacha, sai com o punho para cima e paira com as mechas subindo;
- no voo reto, o cabelo vai para trás e a barra da camiseta tremula;
- na tomada de frente, a estampa continua legível durante as curvas.

**O que não foi verificado:** a leitura estética e o ritmo são seus. Não testei voo com chuva nem à noite (a X1 cuida da luz).

## 7. Como ligar e como desfazer
- **Ligar** (só depois da aprovação): no desenhista do plano, chamar `voo.desenhar(...)` em vez de `heitor_v2.desenhar(...)`.
- **Desfazer:** voltar a chamar `heitor_v2.desenhar`. Nenhum arquivo do rig e nenhum quadro aprovado depende da X2.

## 8. Como reproduzir
```
.venv/bin/python personagens/heitor/extensoes/x2_voo/teste_x2.py            # tudo (vídeo ≈ 20 min)
.venv/bin/python personagens/heitor/extensoes/x2_voo/teste_x2.py X2_1_intacto X2_8_folha   # só um teste
```
