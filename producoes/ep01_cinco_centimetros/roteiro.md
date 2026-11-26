# EP01 — E se você acordasse com apenas 5 centímetros?

> **Decisão do diretor (26/11/2026):** vale a **1ª narração gerada**, em "você", cujo texto falado está em `narracao_falada.txt`,
> transcrito pelo Whisper e conferido. Narração final em `narracao/edicoes/ep01_narracao/`: 110,2 s, −16 LUFS, QA 13/13.
> **A decupagem passa a seguir o texto falado:** aranha em vez de formiga, "paredões", "quase uma montanha" e "invencível".
> O roteiro v2 com "tu" fica abaixo só como referência, sem uso.

# (Referência, sem uso) roteiro v2 com "tu"

Decisões do diretor (26/11/2026):
- **Duração:** caminho C, texto com cerca de 230 palavras e geração em velocidade 1,08. Meta de 75 a 90 s.
- **Tratamento:** "tu".
- **Fechamento:** pergunta para comentário.
- **Escopo:** autorização para todas as etapas da produção.

O texto falado está em `narracao.txt`, que é a fonte única. Cópia abaixo, por cena.

## Como gerar no MiniMax Audio (recomendado: uma única geração)
- **Voz e modelo:** `Portuguese_CaptivatingStoryteller`, speech-2.8-hd, idioma Portuguese.
- **Parâmetros:** velocidade **1,08**; tom 0; volume padrão; emoção **automática**.
- **Uma geração só, com o texto inteiro de `narracao.txt`,** para economizar créditos e manter a voz igual do começo ao fim.
- **Pausas:** quem cuida é a edição. Não precisa marcar nada no texto.
- **Se uma frase sair ruim:** gere de novo só ela, com os mesmos parâmetros. A ficha por trecho (`ficha_geracao_por_trecho.md`) sugere velocidade, tom e emoção por intenção, se tu quiser experimentar.
- **Estimativa:** 232 palavras e 1.180 caracteres, o que dá cerca de 75 s de fala e cerca de 88 s depois da edição. A estimativa vem do ritmo medido na tua primeira geração (171 palavras/min a 1,0).

## Narração por cena

**CENA 01 — O despertar** (mistério e surpresa, ~9 s)
> E se tu acordasse amanhã… com apenas cinco centímetros de altura?
> Tua cama vira um prédio de quatro andares. Teu celular, uma tela de quatro metros.

**CENA 02 — Um mundo gigante** (curiosidade e descoberta, ~13 s)
> Uma moeda de um real fica do tamanho de uma mesa… e pesa quatro vezes mais que tu.
> Cada degrau da escada vira um muro de cinco metros.
> Mas o pior ainda estava por vir…

**CENA 03 — O primeiro perigo** (suspense e tensão, ~13 s)
> Uma formiga, agora do tamanho de um rato, te encara.
> E o gato da sala? Pra ti, ele tem sete metros… e acabou de te ver.
> Um movimento errado… e não tem segunda chance.

**CENA 04 — A física muda tudo** (surpresa e explicação, ~20 s)
> Só que a física tá do teu lado.
> Ao encolher vinte e oito vezes, teu peso cai vinte e duas mil vezes. Já a tua força cai só setecentas e oitenta vezes.
> Em relação ao teu peso, tu fica quase trinta vezes mais forte. Como uma formiga.
> Dá pra erguer uma migalha maior que tu… e correr pra debaixo da cama.

**CENA 05 — A sobrevivência** (tensão e aventura, ~15 s)
> Cair da mesa? Nada. Pra um corpo tão leve, o impacto quase não existe.
> Mas nem tudo fica fácil.
> Um vento da janela te derruba. E saindo de uma poça, tu carrega quase metade do teu peso em água.

**CENA 06 — A revelação final** (impacto e reflexão, ~15 s)
> E sabe qual é a parte mais assustadora?
> O mundo não mudou nada…
> Só que, dessa vez, foi tu que ficou pequeno demais pra ele.
> Comenta aí: qual seria o primeiro lugar que tu tentaria alcançar? Segue aí!

A marca "MODO CURIOSO" entra na tela, como marca d'água e no fechamento. Ela não é falada, para a narração terminar na pergunta.

## Ciência: contas e fontes
Fator de escala: o Heitor tem 1,40 m (altura do rig v2); 1,40 m ÷ 0,05 m = **28**.

| Afirmação | Conta | Situação |
|---|---|---|
| Peso cai 22 mil vezes | massa ∝ L³ → 28³ = 21.952 | lei do quadrado-cubo (Galileu, 1638; Haldane, *On Being the Right Size*, 1926) |
| Força cai 780 vezes | força muscular ∝ área da seção do músculo ∝ L² → 28² = 784 | idem |
| Quase 30× mais forte **em relação ao próprio peso** | 21.952 ÷ 784 = 28 | correto **só** como força relativa; a força absoluta é muito menor (o texto diz "em relação ao teu peso") |
| Cama = prédio de 4 andares | cama ~50 cm × 28 = 14 m ≈ 4 andares de ~3,2 m | estimativa com medidas típicas |
| Celular = tela de 4 m | ~15 cm × 28 = 4,2 m | estimativa |
| Moeda de R$ 1 = mesa, 4× teu peso | 27 mm × 28 = 76 cm; 7,0 g ÷ 1,6 g ≈ 4,4 | **a confirmar:** dados da moeda (27 mm, 7,0 g) e massa do Heitor (35 kg, típica de 10–12 anos) → 35 kg ÷ 21.952 = 1,6 g |
| Degrau = muro de 5 m | ~18 cm × 28 = 5,0 m | degraus residenciais têm de 16 a 18 cm |
| Formiga = tamanho de um rato | formiga doméstica de 3–5 mm × 28 = 8–14 cm | depende da espécie; a saúva seria maior |
| Gato de 7 m | ~25 cm de altura × 28 = 7 m | estimativa |
| Cair da mesa sem se machucar | energia do impacto ∝ L³, resistência dos ossos ∝ L² | princípio bem estabelecido para animais pequenos (Haldane, 1926); é uma estimativa, não um experimento |
| Quase metade do peso em água | película de ~0,5 mm (Haldane) × pele de ~1,15 m² ÷ 784 ≈ 0,7 g ÷ 1,6 g ≈ 45 % | ordem de grandeza (Haldane: "um rato molhado carrega mais ou menos o próprio peso em água") |
| Vento derruba | corpo leve e arrasto grande em relação ao peso | qualitativo |
| Premissa | encolher uma pessoa é ficção | o texto apresenta como hipótese ("E se tu acordasse") |

## Números na tela (pelo menos 6)
5 cm · 14 m (cama) · 4 m (celular) · 76 cm e 4× (moeda) · 5 m (degrau) · 7 m (gato) · ×28 · ÷22.000 · ÷780 · ×28 em relação ao peso · ~45 % (água)

## Decupagem v1 (a ajustar pelos tempos reais da narração final, `voz_palavras.json`)
- **Técnica de escala:**
  - câmera a 2–3 cm do chão;
  - grande-angular e desfoque forte de fundo, com aparência de macrofotografia;
  - Heitor 2D pelas âncoras 3D → 2D, com 0,05 m;
  - poses seguradas, e o movimento vem da câmera e dos efeitos.
- **Cenários e personagens novos (extensão autorizada):**
  - quarto (cama, criado-mudo, celular, janela);
  - escada interna;
  - chão com moeda, migalhas e poça;
  - sala com o gato;
  - formiga;
  - insert científico.
- **Reaproveitamento:** pose de escalada (X3) e roupa e cabelo ao vento (X2).

| Cena | Planos | Rótulos |
|---|---|---|
| 01 | close do Heitor sonolento → olhos arregalados (troca escondida por piscada) → pull-out forte: o lençol vira um deserto → contra-plongée da cama → celular como painel | 5 cm · 14 m · 4 m |
| 02 | moeda ao lado do Heitor, com régua → tilt pelos degraus, um muro por degrau → Heitor escalando → sombra do gato na parede ("o pior…") | 76 cm · ×4 · 5 m |
| 03 | formiga em primeiro plano, com push-in → Heitor recua → olho do gato em plano detalhe → crash-zoom → pata entra no quadro → quadro segurado | 7 m |
| 04 | insert azul-marinho: cubo encolhendo, barras de peso e força → "fantasma" translúcido do Heitor em tamanho normal → Heitor erguendo a migalha → corre para debaixo da cama | ×28 · ÷22.000 · ÷780 · ×28 |
| 05 | Heitor cai da mesa e se levanta (gag) → vento da janela derruba (reuso da X2) → sai da poça, encharcado | ~45 % |
| 06 | planos cada vez mais abertos → pull-out muito forte até o quarto inteiro, com o Heitor como um ponto no chão → pergunta para comentário em legenda → marca | — |
