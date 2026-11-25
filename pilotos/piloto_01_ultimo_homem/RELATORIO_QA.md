# Relatório de qualidade — Piloto 01 (v3)

Arquivo: `saida/MC_piloto01_ultimo_homem_v3.mp4` · 25/11/2026 · teste técnico de integração, **não é episódio**.
Dados brutos do QA automático: `saida/qa_relatorio.json`. Folhas de contato: `saida/folha_contato.jpg` (2 qps) e `saida/folha_contato_completa_10qps.jpg` (o vídeo inteiro, 100 quadros).

## 1. Resultado do controle de qualidade

| # | Verificação pedida | Resultado | Evidência |
|---|---|---|---|
| 1 | Consistência do personagem em todos os quadros | **OK, com ressalva** | O mesmo rig vetorial (cores travadas, proporções, estampa) em P1, P2, P4 e P6, conferido nas folhas de contato. Ressalva: é o **rig v1 PROPOSTA**, ainda não aprovado. A pose deitada é o rig em pé girado |
| 2 | Cenário corresponde à narração | **OK** | Cada plano mostra o que a narração diz no mesmo instante (tabela do `ROTEIRO.md`). Quarto e rua estão no mesmo mundo 3D: a janela do quarto dá para a rua mostrada em P3 e P4 |
| 3 | Grafia da camiseta e das marcas | **OK** | OCR: "Modo Curioso" só na camiseta (P1 e P4); marca d'água "MODO CURIOSO" em **100 %** dos quadros lidos (10 qps), canto superior direito. Nenhuma grafia conflitante. Marca no cenário: ver a limitação 6 |
| 4 | Sincronia voz × imagem × legenda × efeitos | **OK** | Os 6 cortes caem entre falas (1,50 · 2,70 · 4,00 · 5,73 · 7,27 · 7,80 s). As **13/13 legendas** foram lidas por OCR dentro da janela da própria fala. Expressões, olhar, impacto, flash e vibração disparam na palavra marcada no roteiro (todos derivados de `voz/tempos.json` via `montagem.json`) |
| 5 | Áudio, volume e distorção | **OK** | −14,3 LUFS integrado; pico real −1,3 dBTP; **0 amostras clipadas**. Eu não escuto o áudio: não avaliei timbre nem naturalidade |
| 6 | Resolução, FPS e duração | **OK** | 1080×1920, 30 qps, 300 quadros, 10,000 s, H.264 High yuv420p (BT.709), AAC 48 kHz estéreo 192 kb/s |
| 7 | Assistir ao vídeo inteiro | **Feito (por quadros)** | Revi os 100 quadros a 10 qps e quadros em resolução cheia. Isso gerou 7 correções (seção 3). Não ouvi o áudio; conferi só por medição |
| 8 | Folha de contato | **Feito** | `saida/folha_contato.jpg`, `saida/folha_contato_completa_10qps.jpg` |

### Medições contra o padrão do canal

| Métrica | Piloto | Padrão (referências) | Situação |
|---|---|---|---|
| Plano mediano | 1,50 s | 1,5–2,0 s | ✓ |
| Cortes por minuto | 36 | 28–34 | Um pouco acima (6 cortes em 10 s, ritmo de gancho) |
| Vinheta (cantos/centro) | 0,62 | ~0,57–0,62 | ✓ |
| Sombras (Lab b) | −3,0 | ≈ −10 | **Abaixo do alvo**: tinta azul-arroxeada fraca |
| Altas luzes (Lab b) | +15,6 | ≈ +18 | ✓ (próximo) |
| Luma mediana | 0,32 | 0,41 | Mais escuro que as referências |
| Saturação | 0,48 | 0,38 | Mais saturado |
| Loudness | −14,3 LUFS | −14 | ✓ |
| LRA | 0,9 LU | ~3,8 | Muito comprimido |
| Legendas: palavras por bloco | 2,2 | 2–3 | ✓ |
| Destaque amarelo | 7 de 13 blocos (54 %) | ~40 % | Um pouco acima |

## 2. O que funcionou
- **Integração real das ferramentas:** Blender (bpy 5.3, Cycles CPU) → skia (personagem, efeitos, legendas, marca) → NumPy/OpenCV (gradação, bloom, vinheta, grão) → FFmpeg (H.264/AAC), tudo por script e reproduzível a partir de `montagem.json`.
- **Mundo 3D coerente:** um único cenário com o quarto no 4º andar e a rua vazia, sete câmeras e âncoras 3D→2D que posicionam e dimensionam o personagem pela perspectiva de cada câmera.
- **Personagem integrado à luz:** tinta de luz por plano, contraluz com halo na janela (P2), sombra de contato no asfalto (P4), cobertor em primeiro plano sobre o corpo (P1).
- **Câmera dinâmica:** push-in, punch-zoom, pull-out de revelação, pan, chicote, crash-zoom, tremida de impacto e de vibração.
- **Sincronia por construção:** os tempos da voz comandam cortes, legendas, expressões e efeitos; o QA confirmou 13/13 legendas na janela certa.
- **Identidade:** "Modo Curioso" na camiseta (recebendo a sombra do tecido), "MODO CURIOSO" na marca d'água em todo quadro, fontes oficiais, texto da marca sempre em curvas a partir dos arquivos-mestre.
- **Tempos reais medidos:** fundos 3D em 13 min 51 s (7 planos, 24 amostras, 1350×2400) + 3 min para refazer P7; composição de 300 quadros em ~2 min; áudio em 15 s; QA em ~1 min.

## 3. Problemas encontrados e corrigidos durante o QA
1. A sombra da camiseta escondia o último "o" da estampa ("Modo Curios"). Corrigido: a sombra agora multiplica o tecido e a estampa juntos.
2. O ícone do pôster lembrava o logotipo do React (marca de terceiros). Substituído por uma lupa desenhada do zero.
3. Um filtro de cor pintava de creme o quadro inteiro nos planos com personagem. Corrigido com matriz de cor que preserva a transparência.
4. A pose deitada saiu orientada para fora do quadro (ponto de referência atrás da câmera). Agora a direção do corpo vem da máscara do cobertor.
5. A legenda "SUMIRAM." cobria o rosto em P6. Movida para o topo.
6. Pico real de −0,7 dBTP depois da codificação AAC. Master refeito com folga: −1,3 dBTP no MP4 final.
7. Celular escuro e notificação ilegível em P7. Exposição ajustada e P7 rerenderizado com foco na tela (f/5,6).
8. O outdoor "MODO CURIOSO" aparecia cortado na borda superior de P3 (contraria a ID-004, seção 4.4). P3 foi reenquadrado; o outdoor fica fora do quadro.
9. Uma legenda atravessava um corte por ~0,1 s. Agora a legenda termina no corte.

## 4. Limitações (o que não funcionou ou ficou abaixo do padrão)
1. **Voz temporária e robótica** (espeak-ng). Não atende à qualidade da ID-001, e sotaque e naturalidade não foram avaliados por escuta. A ElevenLabs e o Hugging Face seguem bloqueados pela rede.
2. **Personagem não oficial:** rig v1 PROPOSTA, feito só a partir da especificação em texto. Só tem frente e costas; faltam 3/4, perfil, poses (deitado, andar, correr) e animação de membros. Movimento atual: piscada, olhar, troca de expressão, respiração.
3. **Integração 2D/3D parcial:** o personagem recebe tinta, halo e sombra de contato, mas não projeta sombra realista no cenário. A oclusão só existe onde foi preparada (cobertor).
4. **Cor:** sombras pouco azuladas (Lab b −3 contra ≈ −10), imagem mais escura (luma 0,32) e mais saturada que as referências.
5. **P2:** a moldura da janela iluminada pelo sol parece uma linha brilhante "estourada".
6. **ID-004 não ficou visível no corte final:** o pôster do quarto não entra em nenhum enquadramento, e o outdoor foi tirado do quadro para não aparecer cortado. A marca no cenário foi produzida nos dois objetos (`recursos/marca/`), mas o vídeo não a mostra inteira.
7. **Trilha e efeitos sonoros procedurais** (gerados por código), sem biblioteca licenciada. São funcionais, mas simples. LRA de 0,9 LU (muito comprimido).
8. **Tempo por palavra estimado:** o tempo de cada bloco é exato (síntese bloco a bloco), mas o de cada palavra dentro do bloco é proporcional ao número de letras.
9. **Arquivo pesado:** 34 MB em 10 s (~27 Mb/s), por causa do grão em CRF 18. Para publicação, ajustar CRF ou grão.
10. **Número da ONU** (8,2 bilhões em 2025) citado de memória, sem verificação online nesta sessão.
11. **Planeta estilizado** (continentes procedurais, não um mapa real).
12. **QA:** o detector de cortes acusa o flash (7,30 s) e o acender da tela (8,87 s) como cortes falsos. O detector de grafia só lê a estampa com erro quando ela é pequena (P4).
13. **espeak-ng** foi instalado só para este piloto (`apt install espeak-ng=1.51+dfsg-12build1`). Não entrou no ambiente oficial (`ambiente/`), porque a voz é temporária.

## 5. Melhorias necessárias antes de episódios completos
1. **Voz oficial (ID-001):** liberar `api.elevenlabs.io`, aprovar a voz no teste de amostra e usar os tempos por caractere da API.
2. **Aprovar o rig do Heitor** (ou receber as artes oficiais) e completar: vistas 3/4 e perfil, poses deitado e sentado, ciclo de caminhada, braços articulados, biblioteca de bocas.
3. **Gradação:** reforçar a tinta azul-arroxeada das sombras e calibrar luma e saturação para os alvos medidos. Ajustar a luz das cenas no Blender (menos branco estourado).
4. **Integração:** sombra projetada do personagem a partir da luz da cena e camadas de oclusão planejadas por plano.
5. **Planejar a marca no cenário (ID-004)** já na decupagem, com um enquadramento em que ela caiba inteira.
6. **Áudio:** biblioteca licenciada de efeitos sonoros e música; mais faixa dinâmica (LRA de 3 a 4 LU).
7. **Desempenho:** cache das cenas 3D entre planos e episódios; testar EEVEE e menos amostras com redução de ruído.
8. **QA:** ignorar flashes e mudanças de tela na detecção de cortes; checagem de ID-004 com região esperada por plano.
9. **Promover o código do piloto** (`codigo/`) a módulos do estúdio, depois da sua aprovação, sem duplicar.
