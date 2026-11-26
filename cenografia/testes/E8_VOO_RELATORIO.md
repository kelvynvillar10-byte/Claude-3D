# Relatório da etapa E8 (parte 2): poder de voo

26/11/2026 · Autorizada pelo diretor depois da aprovação da extensão X2 ("Pode começar"). **E8 parte 2 APROVADA pelo diretor em 26/11/2026** ("Pode continuar"). Os dois achados continuam em aberto, sem correção.
- O rig v2 não foi alterado. O Heitor é desenhado pela **X2** (poses de voo, corpo inclinado, roupa e cabelo ao vento) e iluminado pela **X1** (tom de luz), as duas aprovadas.
- **Aranha e elasticidade não foram iniciadas.**
- Nenhum episódio ou história foi produzido.

## O que foi construído: `efeitos/poderes/voo.py`
Um arquivo, registrado com `@efeito("voo")`, que usa só o núcleo da E7 e a X2. Tem as 6 fases, as 3 intensidades, contatos no rig e no chão, segurança, proteção do rosto e da estampa, e uma marca que fica.

**Diferente da eletricidade e da terra, o poder de voo controla o MOVIMENTO do Heitor.** A cena pede `estado(t)` (posição, pose, vista, inclinação, expressão) e desenha com a X2. Assim, decolagem, arrancada e pouso ficam sempre sincronizados com os efeitos.

| Modo | Sequência |
|---|---|
| `pairar` | sobe devagar, paira e pousa de volta |
| `sair_voando` | agacha, decola, paira, **arranca** (o corpo deita a 72°) e sai do quadro |
| `subir` | decolagem vertical, como um foguete: sobe, estoura a barreira no alto e some |

| Fase | O que acontece |
|---|---|
| início | poeira começa a girar sob os pés; anéis de ar fracos |
| ativação | **decolagem**: anel de poeira no chão, onda de choque no chão, pedrinhas e tremida (moderado/extremo); **rachadura** que fica (extremo) |
| uso | **anéis de ar** girando em volta do corpo (sobem quando ele paira, correm para trás quando ele voa); **poeira soprada** no chão, mais fraca com a altura; **rastros** dos pés e **linhas de velocidade** quando ele está rápido |
| impacto | **arrancada**: anel de vapor em volta do Heitor, perpendicular ao movimento na tela; onda de choque no ar; tremida. No extremo: 3 anéis, **cone de vapor** e **quadro de impacto** |
| dissipação | rastros, anéis e poeira somem |
| encerramento | poeira assentando; a rachadura fica |

Outros pontos:
- **Família de cores:** branco-ar levemente azulado (`#e9f0ff`) e a poeira com a cor do chão daquele horário (amostrada no fundo, como na terra).
- **Luz:** o voo quase não brilha. Há só um clarão branco suave na arrancada; com a X1, ele aparece no Heitor.
- **Sombra no chão:** fica embaixo do Heitor e diminui, clareia e borra com a altura; some acima de 3 m.
- **Proteção do rosto e da estampa:** com o corpo inclinado, o poder informa onde estão o rosto e a estampa na tela, e a proteção do núcleo usa essa posição. A mudança no núcleo é compatível: sem essa informação, a proteção funciona como antes.

## Vídeo: `testes/e8_voo/E8_voo.mp4`
12,2 s (366 quadros) · 1080×1920 · 30 q/s · marca d'água "MODO CURIOSO" · legenda "voo (teste, não é história)", com a intensidade e a **fase atual**.

São 3 clipes na rua da cena de prova, com a X1 ligada e leve movimento de câmera:

| Clipe | Horário | Vista | Modo |
|---|---|---|---|
| voo · discreto | manhã | frente | paira e pousa |
| voo · moderado | tarde | perfil | decola e sai voando |
| voo · extremo | noite | costas | decolagem vertical |

Quadros: `E8_voo_quadros.jpg`.

## Medidas
| Teste | Resultado |
|---|---|
| **Ordem das intensidades, no MESMO clipe** (decolar e sair voando, tarde) | pico de energia: discreto **0,025** < moderado **0,107** < extremo **0,206** ✅ |
| **Energia por fase** (moderado) | início 0,001 · ativação 0,041 · uso 0,041 · **impacto 0,068** · dissipação 0,027 · encerramento 0,008. Picos na decolagem e na arrancada |
| **Contatos no desenho real** (o ponto calculado cai na parte certa do Heitor desenhado, a cada 6 quadros) | pé no tênis **100 %** (85 amostras); cabeça na cabeça **100 %**; rastro nasce no pé com erro **0,0 px** |
| **Sombra × altura** | some com a altura nos 3 clipes ✅ (opacidade 0,43 no chão → 0,21 a 1,35 m → 0,06 a 2,4 m) |
| **Família de cor × camiseta** (ΔE) | ar **60,3**; poeira 51,6 (manhã), 51,8 (tarde), 78,8 (noite). **Ar × eletricidade: 35,2** (os dois poderes não se confundem) |
| **Paleta do Heitor** (X1 desligada só aqui, para comparar com o desenho da X2 sozinho) | **99,97 % idêntica** em 90.334 pixels sem efeito na frente. Os outros 30 pixels diferem em **1 nível** (de 256), na borda mais fraca de um anel (cobertura 1/255) |
| **Segurança** (flashes por segundo, vídeo pronto) | **1 flash no vídeo inteiro** (máximo 1 por segundo; limite 3) |
| **Proteção do rosto e da estampa** (cobertura máxima) | discreto: rosto 0,29, estampa 0,35 · moderado e extremo: rosto **0,35**, estampa 0,00 (de perfil e de costas a estampa não aparece). No limite de 0,35, nunca acima |
| **Energia no vídeo** (pico por clipe) | discreto 0,031 · moderado 0,084 · extremo 0,174 |
| **Determinismo** | mesmo quadro duas vezes: **idêntico** |
| **Regressão** | as 3 tomadas da cena de prova, sem efeitos: **idênticas** à referência da E7 |
| **Integridade** | assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

### Tempo de composição (CPU, 1080×1920, com o Heitor da X2, a X1 e o céu animado)
| Clipe | Média | Máximo |
|---|---|---|
| discreto | 4,68 s por quadro | 6,10 s |
| moderado | 5,23 s por quadro | 9,35 s |
| extremo | 6,09 s por quadro | 12,36 s (quadro de impacto, anéis e onda de choque juntos) |

Os 12,2 s de vídeo levaram ~32 min de composição. As placas já estavam prontas, vindas da E6.

## Problemas encontrados e corrigidos
1. **Anéis grossos como bambolês e anel da arrancada virando uma barra.** No perfil, o anel 3D perpendicular ao movimento fica de lado para a câmera e vira uma linha. Agora o anel da arrancada é desenhado na tela, perpendicular ao movimento visto, e se lê em qualquer câmera.
2. **Decolagem vertical rápida demais:** a arrancada acontecia fora do quadro. A subida foi refeita para ela acontecer com o Heitor inteiro na tela.
3. **Pés afundando ao agachar.** O agachar da pose já abaixa o quadril com os pés no chão; somar a descida de novo afundava os pés. Corrigido no poder: os contatos dão 100 % no tênis.
4. **Franja clara nas bordas** dos anéis e rastros. Era a mesma leitura não pré-multiplicada do skia da seção "Achados"; corrigida dentro do poder de voo. Com a leitura certa, os efeitos ficaram fracos e as opacidades foram reajustadas.
5. **Medições erradas, corrigidas:**
   - a faixa azul do tênis tem a mesma cor da camiseta (`#3d80d8`), e o teste a classificava como camiseta;
   - o pé de trás no perfil pode estar escondido pela outra perna, então só o pé da frente é conferido no perfil;
   - a sombra não era medida;
   - a borda suavizada de um traço (mistura com o contorno) era contada como erro.

## Achados (fora do poder de voo, NÃO corrigidos; dependem de você)
1. **Núcleo de efeitos (E7) lê o skia não pré-multiplicado.** Vários desenhos do núcleo e da E8 parte 1 leem a imagem do skia nesse formato e a somam como se fosse pré-multiplicada: curvas e raios, arcos da eletricidade, rastros, corda, polígonos, a textura da rachadura e os traços da terra.
   - **Efeito medido** num traço de brilho igual ao do raio: o brilho somado fica **5,6×** maior e a largura visível **1,8×** maior que o desenhado (46 px em vez de 26 px).
   - Ou seja, o visual aprovado da eletricidade é mais forte do que os números do código dizem.
   - **Corrigir muda o visual já aprovado** (E7 e E8 parte 1): o brilho ficaria mais fraco e precisaria de novo ajuste e nova aprovação.
   - O poder de voo já lê do jeito certo.
2. **Demonstração da X2:** no agachar da tomada de perfil, os pés afundavam até ~12 cm. É calculado, não medido no vídeo. O motivo foi o mesmo erro do item 3 acima, na cena da demonstração; a extensão em si está certa.
   - O auxiliar `pelve_na_tela`/`altura_pelve` da X2 leva a esse erro: o ponto que a X2 recebe é "os pés + 1,72 H", não a pelve real.
   - Proponho corrigir o texto e o auxiliar da X2, sem mudar o desenho. Mesmo assim, só com a sua autorização, porque a X2 está aprovada.

## Limitações (registradas, não escondidas)
1. **O ar é 2D:** os anéis e as linhas não fazem sombra nem dobram com o vento do cenário.
2. **A poeira soprada é de partículas,** sem folhas ou papéis voando.
3. **Voo reto de frente para a câmera** não existe (limitação da X2): de frente há pairar, impulso e curva.
4. **Pouso com impacto** (aterrissagem forte com rachadura) não foi feito; no modo `pairar` o pouso é suave.
5. **Energia medida** é cobertura, brilho, distorção, tremida e luz: serve para comparar as intensidades do mesmo poder, não poderes diferentes.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e8_voo_testes.py                      # tudo (vídeo ≈ 30 min)
.venv/bin/python cenografia/testes/e8_voo_testes.py previa /caminho.jpg  # quadros-chave (≈ 3 min)
.venv/bin/python cenografia/testes/e8_voo_testes.py V3_contatos          # um teste
```

## Próximos passos (cada um só com aprovação)
1. **Proposta X3, aranha:** poses de escalada e de balanço na teia, apresentada à parte com justificativa, demonstração e testes, depois o poder de aranha.
2. **Proposta X4, elasticidade:** membros elásticos, só braços e pernas, depois o poder de elasticidade.
3. **E9:** combinações (teste de ação de 10–15 s, sem história) e relatório final.
4. **Decisões suas sobre os achados 1 e 2.**
