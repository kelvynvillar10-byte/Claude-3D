# Proposta X1: tom de luz no personagem

26/11/2026 · **X1 APROVADA pelo diretor em 26/11/2026** ("Aprovar x1, ajuste não e corrigir borda não"). Decisões:
- **força padrão mantida** (`forca=1.0`, piso noturno 0,62), sem ajuste;
- **a borda do compositor NÃO será corrigida** (seção 5): os quadros aprovados ficam como estão.

Ligada por quem compõe (parâmetro `tom_personagem`); o padrão do compositor continua `None`, para que os quadros já aprovados não mudem. O rig v2 continua intocado.

## 1. Justificativa
Hoje o Heitor é sempre desenhado com a mesma luz, qualquer que seja o horário ou o efeito. Isso aparece em dois casos:
- **à noite**, ele fica claro demais em relação à rua e parece "colado";
- **na eletricidade**, o raio ilumina o cenário mas não ilumina o Heitor. Essa limitação está registrada no relatório da E8 como a mais visível.

Todos os poderes com luz (eletricidade agora; voo e os outros depois) dependem disso.

## 2. O que muda e o que NÃO muda
**Não muda nada no rig v2.** O código fica fora de `personagens/heitor/rig_v2/` (em `personagens/heitor/extensoes/x1_tom_de_luz/`). A extensão atua **depois** do desenho, sobre a camada pronta do Heitor dentro do compositor.

| Não muda | Muda (só a luz) |
|---|---|
| esqueleto, poses, deformação, roupa, cabelo, expressões | **tom do plano:** cor da luz ambiente, medida no cenário em volta dele. De dia só a cor; à noite também o brilho, com **piso de 0,62** |
| forma e silhueta: **alfa idêntico, medido** | **luz de contorno** do lado do sol ou da lua (direção do manifesto da placa), na cor do horário, e um degradê leve de volume |
| o traço preto do contorno do rig (a luz é albedo × cor, então o preto continua preto) | **luz dos efeitos:** cada luz de efeito (posição 3D, cor, força) acende o lado do Heitor voltado para ela e cai com a distância |
| a paleta oficial quando a luz é neutra (**diferença 0** em 8 bits) | |
| a grafia "Modo Curioso" e "MODO CURIOSO" (ID-004): a estampa é a mesma, só iluminada | |

**Limites embutidos:**
- piso de brilho à noite 0,62;
- luz somada no máximo 0,55 (linear) por pixel;
- força de uma luz de efeito no máximo 1,5;
- só o miolo opaco do desenho recebe luz somada.

## 3. Demonstração
- `saidas/X1_comparativo.jpg`: 6 situações, sem e com, lado a lado.
- `saidas/X1_lado_a_lado.mp4`: eletricidade extrema à noite, depois a tomada noturna da cena de prova, sem | com.

## 4. Testes (`teste_x1.py`, medidas em `saidas/x1_metricas.json`)
| Teste | Resultado |
|---|---|
| **Desligado = idêntico** (as 3 tomadas da cena de prova × referência da E7) | **idêntico** nas 3 (SHA-256) |
| **Luz neutra = mesmas cores** | diferença máxima **0** (8 bits); alfa idêntico |
| **Alfa (silhueta)** nas 6 situações | **idêntico** em todas |
| **Legibilidade da estampa** (contraste WCAG × camiseta; sem → com; medida nos 3 planos de poder, onde a estampa tem pixels suficientes) | "Modo": 3,21 → 3,14 / 2,97 / 3,17 (**mínimo 92,5 %** do original). "Curioso": 2,28 → 2,18 / 2,22 / 2,21 (**mínimo 95,6 %**) |
| **Contorno: área** (% do personagem / % do rosto) | dia e noite sem efeito: 13–16 % / 9–11 %; com eletricidade: 26–28 % / 18–20 % |
| **Tempo extra** por quadro (CPU) | de −0,3 a +0,8 s, dentro da variação de medida; abaixo de 1 s |

**Desvio de cor das cores oficiais** (ΔE CIELAB, média dos pixels que sem tom têm a cor oficial exata):

| Situação | pele | camiseta | cabelo | Observação |
|---|---|---|---|---|
| manhã | 5,8 | 2,2 | 1,7 | luz levemente fria da manhã |
| tarde dourada, perfil | 1,5 | 1,8 | 1,5 | |
| noite, de costas | **16,0** | **14,0** | 4,6 | proposital: escurece até o piso 0,62 (luz quente dos postes) |
| eletricidade moderada (manhã) | 10,5 | 4,6 | 3,0 | luz ciano do raio do lado da mão |
| eletricidade extrema (noite) | 9,2 | 4,5 | 4,3 | noite + raio |
| terra extrema (manhã) | 3,5 | 2,0 | 0,8 | sem luz de efeito |

**Integridade do rig:**
- assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`);
- nenhuma alteração pendente nesses caminhos;
- F1 6/6 OK.

**Vídeo:** 186 quadros (6,2 s) sem | com, compostos em 25,7 min. São 2 composições por quadro, ≈ 4,1 s cada, em CPU.

**O que eu vi no vídeo e no comparativo:**
- à noite, o Heitor escurece e esquenta junto com a rua e deixa de parecer colado;
- na eletricidade, o lado voltado para a mão acende em ciano, com contorno ciano;
- de dia a diferença é discreta: um contorno claro do lado do sol;
- sem halo e sem tremulação visível.

**O que não foi verificado:** a avaliação estética é sua, e planos longos com o fundo mudando muito em volta ainda não foram testados.

**Correções feitas durante a proposta:**
1. A primeira versão somava luz branca e também na borda suavizada. Isso deixava um halo borrado em volta do Heitor e lavava o rosto de branco no raio à noite.
2. Agora a luz somada é albedo × cor da luz, só no miolo opaco, e a força de uma luz de efeito tem teto de 1,5.

## 5. Achado durante os testes (fora da X1; não corrigido)
O skia entrega a camada do Heitor com **cor não pré-multiplicada**, mas o compositor (desde a E1) a soma como se fosse pré-multiplicada. Na borda suavizada do desenho (pixels de alfa parcial), a cor entra sem ser ponderada pelo alfa, e a borda fica um pouco mais clara.

Medido (`X1_6_borda_compositor`):
- manhã: 1.899 pixels de borda (o Heitor tem 43.015), clareamento médio de **23,5 níveis** (8 bits), 1.040 pixels acima de 20;
- noite: 2.477 pixels, média 23,2.

É uma linha de 1 pixel, pouco visível no tamanho final. Mesmo assim, é um erro.

**A correção é de uma linha** (pedir `alphaType=kPremul` ao skia), mas **muda levemente todos os quadros já aprovados**, a partir da E6. Por isso não corrigi sem a sua decisão. A X1 foi feita para funcionar com o formato atual e não piora esse efeito: só o miolo opaco recebe luz somada.

## 6. Riscos
1. **Desvio de cor da identidade à noite** (ΔE 14–16 na pele e na camiseta). É o objetivo da extensão, mas é a maior mudança na aparência. O piso 0,62 pode subir, se você preferir o Heitor mais claro à noite.
2. **A medida do ambiente é por quadro.** Se o fundo em volta muda bruscamente (por exemplo um carro passando colado), o tom pode variar. No vídeo não vi tremulação; para planos longos, dá para suavizar no tempo.
3. **A luz é 2D:** não há sombra de um braço sobre o corpo, e o lado iluminado segue a silhueta, não o volume 3D.

## 7. Como ligar e como desfazer
- **Ligar** (só depois da aprovação): passar `tom_personagem=fazer_tom({"pe_mundo": ..., "altura_m": ...}, luzes=mesa.luzes(P, {}))` para `Placa.compor`.
- **Desfazer:** não passar o parâmetro (padrão `None`). Nenhum arquivo do rig e nenhum quadro aprovado depende da X1.
- **Força ajustável:** `fazer_tom(..., forca=0.5)` reduz o contorno, o volume e a luz dos efeitos pela metade.

## 8. Como reproduzir
```
.venv/bin/python personagens/heitor/extensoes/x1_tom_de_luz/teste_x1.py     # tudo (vídeo ≈ 30 min)
.venv/bin/python personagens/heitor/extensoes/x1_tom_de_luz/teste_x1.py X1_3_situacoes   # só o comparativo e as medidas
```
