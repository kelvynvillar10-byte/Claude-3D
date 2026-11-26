# E10 parte 1 — quarto do EP01 em escala macro (teste; não é o episódio)

26/11/2026. Autorizada pelo diretor dentro da produção do EP01 ("E se você acordasse com apenas 5 centímetros?").
- **O que não mudou:** o Heitor rig v2, o núcleo da cenografia e as etapas E0–E9. O kit novo só registra componentes.
- **Como a escala é feita:** o quarto tem medidas reais e o Heitor entra no compositor com **0,05 m** de altura, ou seja, 28 vezes menor que os 1,40 m dele.

## Entregas
| Peça | Onde |
|---|---|
| Kit de interior (16 componentes, materiais com relevo para close) | `cenografia/componentes/interior.py` |
| Receita do quarto (manhã) | `cenografia/receitas/e10_quarto.json` |
| Teste dos 4 planos | `cenografia/testes/e10_testes.py` → `cenografia/testes/e10/` |

## Os 4 planos (1080×1920, Heitor rig v2 sem alteração)
Valores medidos:

| Plano | Situação da decupagem | Câmera | Foco / abertura | Heitor | Render |
|---|---|---|---|---|---|
| A_despertar | em cima do edredom: o travesseiro vira montanha | 2,2 cm acima do edredom, 20 mm | 0,224 m / f4 | 363 px, a 0,22 m | 469 s |
| B_cama_predio | do chão: a lateral da cama sobe como um prédio | 1,2 cm do chão, 14 mm | 0,256 m / f5,6 | 265 px, a 0,22 m | 454 s |
| C_moeda | moeda de 27 mm do tamanho de uma mesa; gotas, migalhas, poeira | 5 cm do chão, 28 mm | 0,173 m / f4 | 643 px, a 0,18 m | 396 s |
| D_celular | o celular de 15 cm de pé vira um painel aceso | 2,4 cm acima do tampo, 20 mm | 0,199 m / f4 | 413 px, a 0,19 m | 467 s |

- **QA da cena** (Blender, antes do render): nenhuma peça flutuando nos 4 planos e **nenhum texto 3D** (a lista permitida é vazia). Peças apoiadas em outras (estrado, gaveta, travesseiros, celular no suporte, cortinas, quadro) estão marcadas como apoiadas.
- **Sem marcas:**
  - a moeda é genérica, com aro e núcleo de dois metais, sem reproduzir desenho de moeda real;
  - a tela do celular é um degradê abstrato;
  - o quadro é arte geométrica;
  - o carrinho é um brinquedo genérico.
- **Luz da manhã:**
  - sol pela janela (a janela foi posta onde o sol da manhã atinge a cama);
  - luz difusa do céu pelo vão da janela (grupo "ceu");
  - tela do celular no grupo "artificial";
  - abajur apagado (só acende quando a receita pede).
- **Gradação do interior:** exposição +0,55, saturação 1,6, grão 0,006. É mais aberta que a da rua, que deixava o quarto escuro demais.

## Limitações e próximos ajustes (vistos nas imagens)
1. **Moiré** na lateral do edredom vista de longe (plano B): a trama do tecido (0,7 mm) fica do tamanho de um pixel. Correção prevista: reduzir o relevo da trama com a distância.
2. O sol direto aparece pouco nos 4 enquadramentos; a luz dominante é a difusa da janela. Para mais calor, posso mover o Heitor para a mancha de sol ou ajustar a janela.
3. O Heitor está na pose base (frente, braços ao lado do corpo), com troca só de expressão. As poses de cena (acordar, olhar para cima, recuar) vêm na animação.
4. Render de ~7–8 min por plano em CPU (32 amostras nas camadas principais + OIDN).

## Próxima: E10 parte 2
- **Escada:** degraus de 18 cm vistos como paredões.
- **Sala com o gato:** gato e aranha como personagens 2D originais.
- **Sobrevivência:** vento na janela e poça.
- **Insert científico:** quadrado-cubo, peso ÷21.952 e força ÷784.
