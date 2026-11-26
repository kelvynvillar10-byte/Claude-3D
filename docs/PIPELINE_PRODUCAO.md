# Pipeline de Produção — Modo Curioso Studio AI

Versão 1.0 · Etapa 1 (auditoria). Esta é a proposta técnica. **Nenhum vídeo foi gerado ainda.**

Documentos relacionados: `AUDITORIA_REFERENCIAS.md` (inventário e medições), `MANUAL_DIRECAO_ARTE.md`, `MANUAL_ANIMACAO.md`, `PADRAO_EDICAO.md`.

---

## 1. Visão geral

```
PAUTA → ROTEIRO → VOZ → DECUPAGEM → ASSETS → ANIMAÇÃO → RENDER → MONTAGEM → ÁUDIO → QA → EXPORT
  │        │        │        │          │          │          │          │         │       │
  G0       G1       G2       G3         G4         G5         —          G6        G7      G8
```

Cada etapa entrega um arquivo versionado e passa por um portão de aprovação (G0–G8). Nenhuma etapa começa sem o portão anterior aprovado. Os portões G1, G3 e G8 precisam de aprovação humana. Os outros podem ser checados por script (seção 12).

| Etapa | Entrada | Saída (arquivo) | Portão |
|---|---|---|---|
| 0. Pauta | ideia "E se…?" | `pauta.md` (poder + 6–10 fatos científicos com fonte) | G0: todo número tem fonte |
| 1. Roteiro | pauta | `roteiro.md` com tempo-alvo por frase | G1: estrutura da seção 3 + aprovação humana |
| 2. Voz | roteiro | `voz.wav` + `voz_palavras.json` (tempo de cada palavra) | G2: ritmo e duração |
| 3. Decupagem | roteiro + voz | `decupagem.json` (lista de planos) | G3: aprovação humana |
| 4. Assets | decupagem | personagens, cenários, inserts | G4: confere com o Manual de Direção de Arte |
| 5. Animação | assets + decupagem | camadas por plano | G5: confere com o Manual de Animação |
| 6. Render | camadas | `planos/*.mov` ou sequência PNG | — |
| 7. Montagem | planos + voz | `montagem.json` → `video_sem_mix.mp4` | G6: confere com o Padrão de Edição |
| 8. Áudio | voz + SFX + música | `mix.wav` | G7: −14 LUFS, pico ≤ −1 dBTP |
| 9. QA | vídeo final | `qa_relatorio.json` | G8: checklist + aprovação humana |
| 10. Export | aprovado | `MC_<serie>_<ep>_v<n>.mp4` | — |

---

## 2. Etapa 0: pauta

- Formato: "E se tu acordasse amanhã e ___?" (parte 1) ou continuação de série com personagem nomeado.
- Duração (diretriz permanente do canal, aprovada em 26/11/2026): formato principal de **1 a 2 min (60–120 s)**; vídeo longo só como formato especial, quando o tema justificar. A duração sai do potencial do tema e da necessidade narrativa: não prolongar artificialmente nem cortar informação importante só para caber em 2 min. Ritmo natural, pausas expressivas e boa retenção.
- Liste de 6 a 10 conceitos científicos, cada um com **um número real e a fonte**. Exemplos medidos nas referências: densidade 0,92 (borracha boia, v15), 343 m/s (som no ar, v12), 4.000 bar (jato d'água, v10), ×20.000 (intensificador de luz, v18/v20), 59 % de água no corpo (v17), 0,14 s (duração de um soco, v14), 1.400 km/h (bala, v19).
- Contraste "no filme × na vida real" sempre que der.
- Verifique as regras fixas do canal (seção 0 do Manual de Direção de Arte): nada de personagem, logo ou marca de terceiros. As referências citam JoJo (v01, v19), One Piece/Luffy (v15), o filme Lucy e o jogo Clash (v14), e caricaturas de pessoa real (cientista estilo Einstein em v14). Nós não fazemos isso.

## 3. Etapa 1: roteiro

Modelo de 91 s (mediana das referências). Episódios de série podem ir a 117–141 s (v10, v16–v20).

| Tempo | Bloco | Regra |
|---|---|---|
| 0–1 s | Gancho | "E se tu acordasse amanhã e…?!" ou ação em andamento com nome ("O Will tava…", "O Caio…") ou "Tu é o ___ e tem o elemento ___". Quebrado em 3–5 legendas. |
| 1–10 s | Situação | Personagem nomeado + 2ª pessoa ("tu", "tua mão"). Primeiro gag. |
| a cada 8–12 s | Conceito | Um número real na tela por conceito (≥ 6 por vídeo). |
| a cada 10–15 s | Gag físico | Exemplos vistos: braço elástico desliga o despertador (v15), frigideira gruda na mão (v07), olhos boiando do invisível (v20). |
| ~50 % | Rival | Antagonista entra (brutamontes da academia v07, rival do futebol v15, caçador v10, Rei Mago v16/v17). |
| 70–75 % | Clímax | Maior efeito visual do vídeo. |
| últimos 5 s | Final | "Segue aí" + gancho "na parte dois" e/ou pergunta "Comenta aí…" / "Tu queria ter?" (v13). |

- Velocidade de narração: ≈195 palavras/min (dado do Padrão; nossa medição por OCR está em `AUDITORIA_REFERENCIAS.md`). Isso dá cerca de 290–300 palavras para 91 s.
- Escreva o roteiro já dividido em blocos de 2–3 palavras (é como a legenda vai aparecer).
- Falas de personagem entre aspas.

## 4. Etapa 2: voz

- **Decisão ID-001:** voz sintética licenciada, criada a partir de uma descrição de características gerais (sem clonar ninguém). Opção recomendada: ElevenLabs Voice Design, sujeita ao teste de amostra. Perfil alvo, proibições e protocolo de teste em `IDENTIDADE_OFICIAL.md`.
- **Integração em teste (2026):** MiniMax T2A V2 (`speech-2.8-hd`) com diretor de narração, em `narracao/` (ver `narracao/README.md`). Voz candidata, não aprovada; a ID-001 só muda depois da aprovação da voz.
- **Fluxo atual (aprovado pelo diretor em 26/11/2026):** o diretor gera a narração no site MiniMax Audio (voz `Portuguese_CaptivatingStoryteller`) e envia o áudio com o texto; a pós-produção em `narracao/pos/` (ver `narracao/pos/README.md`) faz análise, direção de edição por frase, pausas, destaques, tratamento (preset da assinatura sonora), tempos das palavras do áudio FINAL, marcações para a edição e QA. O original é sempre preservado.
- Pausas na pós-produção (regra aprovada em 26/11/2026, substitui a compressão fixa anterior): pausa-alvo por intenção; suspense e revelação até 0,7 s, surpresa até 0,5 s, ação até 0,15 s; **nenhuma pausa ≥ 0,8 s**; pausa sem pontuação acima de 0,25 s é inadequada e vira 0,10 s. **Nunca acelerar com rubberband/time-stretch**, porque gera eco e voz duplicada; tom e velocidade da voz nunca são alterados.
- Loudness da narração: −16 LUFS, pico ≤ −1,5 dBTP (a mixagem final continua em −14 LUFS e −1 dBTP).
- Medido nas referências: nenhuma pausa ≥ 0,8 s no meio do vídeo em 12 de 13 vídeos (detector de silêncio a −35 dB).
- Saída obrigatória: alinhamento de palavras (`voz_palavras.json`, início e fim de cada palavra). Ele dirige legendas, cortes e SFX.
- Alinhamento de palavras sem modelos externos (opção aprovada em 26/11/2026): espeak-ng como referência com tempos exatos + DTW + ajuste pelas pausas medidas (`narracao/pos/alinhar.py`). Precisão medida no teste F0 contra tempos verdadeiros (vozes sintéticas); na voz real, confirmar pela escuta. Whisper continua opcional (exige liberar o Hugging Face na rede).

## 5. Etapa 3: decupagem (`decupagem.json`)

Um registro por plano:

```json
{
  "plano": 12,
  "inicio": 18.40, "fim": 20.05,
  "texto_voz": "a porta de aço voou",
  "cenario": "joalheria_noite",
  "enquadramento": "close",
  "personagens": [{"id": "heitor", "pose": "grito", "expressao": "bravo"}],
  "camera": {"tipo": "push-in", "zoom_total": 0.10, "curva": "ease-out"},
  "efeitos": ["onda_choque", "tremida_impacto"],
  "insert_cientifico": null,
  "rotulo_numero": {"texto": "194 dB", "cor": "amarelo"},
  "legenda_posicao": "baixo",
  "transicao_entrada": "corte",
  "sfx": ["whoosh", "impacto"]
}
```

Alvos para a lista inteira (detalhe no Padrão de Edição): plano mediano de 1,5 a 2,0 s, ≈30 cortes/min, push-in em cerca de 2 de cada 3 planos, primeiro corte entre 1 e 2 s.

## 6. Etapa 4: assets

| Biblioteca | Conteúdo | Formato proposto |
|---|---|---|
| Personagens | Heitor (elenco fixo) + coadjuvantes reutilizáveis, trocando só a roupa; estampa "Modo Curioso" a partir do arquivo-mestre `assets/marca/camiseta_modo_curioso.svg` (ID-002) | Boneco 2D recortado: cada parte do corpo é uma camada com ponto de pivô (SVG/PNG em camadas). Expressões como trocas de olho, sobrancelha e boca. |
| Cenários | Quarto, cozinha, escola, rua de bairro, academia, campo, vila medieval, laboratório, base noturna | 3D low-poly com materiais simples e luz motivada, renderizado como fundo (ou pintura 2.5D com camadas para paralaxe) |
| Inserts científicos | Átomos, moléculas, neurônio, corpo holográfico, câmera térmica, visão noturna, espaço | Modelos reutilizáveis sobre fundo azul-marinho com bokeh |
| UI/tela | Celular com app, ficha "CONFIDENCIAL", notebook de loja, notícia | Templates vetoriais com a marca exatamente "MODO CURIOSO" (ID-004), a partir do arquivo-mestre `assets/marca/cenario_MODO_CURIOSO.svg` |
| Tipografia | Legenda (condensada bold) e rótulos (arredondada) | Fontes livres: Roboto Condensed 800 e, por exemplo, Nunito/Baloo para rótulos |
| Áudio | Whoosh, impacto, pop, riser, ambiente; trilhas | Biblioteca licenciada, com a licença registrada por arquivo |

## 7. Etapa 5: animação

Ver `MANUAL_ANIMACAO.md`. Resumo: animação pose a pose com poses seguradas no nível base. Nível "ação" (antecipação → golpe → overshoot) só nos momentos de poder. O movimento de câmera é aplicado depois, na composição, como transformação 2D da imagem do plano. Por isso o plano é renderizado com margem de segurança (pelo menos 15 % maior que 1080×1920) para permitir push-in, pan e tremida sem borda.

## 8. Etapa 6: render

- Formato final: 1080×1920, 30 qps. Das 13 referências processadas, 9 estão em 60 qps (HEVC) e 4 em 30 qps (H.264). Propomos 30 qps como padrão e 60 qps como opção.
- Camadas separadas por plano: fundo, personagens, FX, rótulos. A legenda **não** entra no render do plano: ela é aplicada na montagem.
- Grão, vinheta e gradação de cor ficam num único passo de acabamento na montagem, para que todos os planos fiquem iguais.

## 9. Etapa 7: montagem

- A montagem é descrita em `montagem.json` (planos, tempos, transições, câmera, legendas) e renderizada por script (FFmpeg, ou um compositor em Python/Node). Assim a edição é reprodutível e dá para checar por script.
- Ordem das camadas: plano → câmera (push/pan/tilt/roll/tremida) → transições → acabamento de cor (sombras roxo-azuladas, vinheta, grão, bloom) → rótulos → legendas → marca d'água "MODO CURIOSO" (ID-003; fica fora da gradação de cor, da vinheta e do grão).

## 10. Etapa 8: áudio

- Voz é o centro. Música por baixo com ducking. SFX baixos em cada corte e em cada efeito.
- Alvos: −14 LUFS integrado; pico real ≤ −1,0 dBTP (as referências chegam a −0,8 dBTP; deixamos 0,2 dB de folga); LRA de 3 a 4 LU.
- Medido nas referências: −14,1 a −14,3 LUFS em 12 de 13 (o v16 está em −21 LUFS, fora do padrão); 1,6 a 1,8 eventos sonoros por segundo.

## 11. Etapa 10: export

- H.264 High, yuv420p, 1080×1920, 30 qps, CRF 18 (ou VBR 12–16 Mb/s), AAC 48 kHz 192 kb/s, `+faststart`.
- Nome: `MC_<serie>_<episodio>_v<versao>.mp4`. Exemplo: `MC_magnetismo_p1_v3.mp4`.

## 12. QA automático (reaproveita a análise desta auditoria)

Os scripts em `tools/analise/` mediram as referências. Rodados no nosso vídeo final, eles geram `qa_relatorio.json` e comparam com as faixas-alvo:

| Métrica | Alvo | Referências (13 MP4) |
|---|---|---|
| Duração | 60–120 s (diretriz de 26/11/2026; especial longo quando o tema justificar) | 81–141 s |
| Plano mediano | 1,5–2,0 s | 1,25–2,40 s (mediana 1,73) |
| Cortes/min | 27–34 | 22,5–32,7 (mediana 28,4; detector conta 5–12 % a menos) |
| % planos com movimento de câmera | ≥ 85 % | 86–100 % (mediana 96 %) |
| Vinheta (cantos/centro) | 0,50–0,66 | 0,39–0,67 (mediana 0,57) |
| Sombras Lab b | < −4 (tinta azul) | −19,4 a −1,4 (mediana −11,5); 12 de 13 abaixo de −4 |
| Loudness | −14 ± 0,5 LUFS | −13,9 a −14,3 em 12 de 13 (v16: −21,0) |
| Grafia da marca (OCR) | Camiseta "Modo Curioso" (ID-002/003); marca d'água "MODO CURIOSO" (ID-003); marca no cenário "MODO CURIOSO" (ID-004). Qualquer outra grafia reprova | — (regra nossa) |
| Legendas | 2–3 palavras/bloco, centro entre 15 % e 80 % da altura, ~40 % com destaque amarelo | 64 blocos/min; 84 % entre 60 % e 80 % da altura; amarelo em 43 % (0–61 %) |

O que o script não mede (aprovação humana no G8): leitura da história, humor, precisão científica, direitos autorais, expressão dos personagens.

## 13. Estrutura de pastas proposta

```
Claude-3D/
  docs/                      manuais e auditoria
  tools/analise/             scripts de medição e QA
  referencias/               MP4 e miniaturas de referência (mover para Git LFS)
  assets/
    personagens/<id>/        partes, expressões, folha de modelo
    cenarios/<id>/
    inserts/
    ui/  fontes/  audio/sfx/  audio/musica/
  producoes/<serie>_<ep>/
    pauta.md roteiro.md voz.wav voz_palavras.json decupagem.json
    planos/ montagem.json mix.wav qa_relatorio.json export/
```

Observação: hoje os 13 MP4 (~190 MB) estão versionados direto no Git, na raiz. Recomendo movê-los para `referencias/` com Git LFS antes de o repositório crescer. Isso não foi feito nesta etapa, para não mexer nos arquivos originais sem a sua aprovação.

## 14. Ferramentas: o que existe neste ambiente (verificado)

> **Atualização de 25/11/2026:** o ambiente agora é reproduzível e versionado em `ambiente/` (instalação, versões exatas, verificação, restauração) e no `Dockerfile`. Versões atuais em `ambiente/VERSOES.md`. A tabela abaixo é o levantamento original da Etapa 1. O Python do projeto passou a ser o 3.13.14 gerenciado pelo uv, num ambiente virtual `.venv`.

| Ferramenta | Situação |
|---|---|
| FFmpeg / FFprobe 6.1.1 | Disponível. Decodifica H.264 e HEVC dos 13 MP4. |
| Python 3.13 + NumPy, Pillow | Disponível |
| OpenCV 5.1 (headless), RapidOCR | Instalados nesta sessão via pip (fluxo óptico, OCR das legendas) |
| Node 22, Chromium + Playwright | Disponíveis (opção para render 2D vetorial por canvas/SVG) |
| ImageMagick (`convert`) | Disponível |
| Blender | Não instalado. `bpy` 5.3.0 existe no PyPI (Blender como módulo Python, para render 3D sem interface). A validar na próxima etapa. |
| Whisper / reconhecimento de fala | Bloqueado: o download do modelo no Hugging Face foi recusado pela rede do ambiente |
| TTS (voz) | Direção decidida (ID-001); fornecedor recomendado: ElevenLabs Voice Design, a testar. O endpoint com tempos por caractere também resolve o alinhamento de legendas |

## 15. Arquitetura técnica de produção (proposta para aprovação)

Versão 1.0, de 25/11/2026. **Status: proposta, não executada.** Nada foi instalado nem renderizado para escrever esta seção. As compatibilidades marcadas como "verificado" foram checadas sem instalar (resolução de pacotes). Os tempos e custos marcados como "estimativa" precisam ser medidos no teste técnico (seção 17).

### 15.0 Visão geral

```
 roteiro.md ──► TTS com tempos (API externa) ──► voz.wav + tempos por caractere
                                                     │
                                                     ▼
                                       linha do tempo (montagem.json)  ◄── decupagem.json
                                    palavras · blocos de legenda · planos · SFX · rótulos
                                                     │
            ┌────────────────────────────┬───────────┴─────────────┬────────────────────┐
            ▼                            ▼                         ▼                    ▼
  cenários 3D low-poly          personagens 2D recortados     inserts / rótulos      áudio
  (Blender bpy, Cycles CPU)     (rig vetorial, skia-python)   (skia-python)          (FFmpeg)
  → fundos estáticos em camadas → camadas por quadro          → camadas por quadro   SFX + música + voz
            └───────────────┬────────────┴─────────────────────────┘                    │
                            ▼                                                           │
              compositor Python (skia + NumPy): câmera, transições, cor,                │
              vinheta, grão, bloom, rótulos, legendas, marca d'água                     │
                            │  quadros RGB 1080×1920 por pipe                           │
                            ▼                                                           ▼
                    FFmpeg (libx264) ◄───────────────────────────────────── mix.wav (−14 LUFS)
                            │
                            ▼
                  MC_<serie>_<ep>_v<n>.mp4 ──► QA automático (tools/analise) ──► aprovação humana
```

Princípio: **tudo vem de arquivos de dados versionados** (roteiro, linha do tempo, rig, cenas). O vídeo é sempre re-renderizável e conferível por script. Nenhuma etapa depende de geração de imagem ou de vídeo por IA, que é a principal fonte de inconsistência de personagem e de letras erradas.

### 15.1 Motor de renderização

**Híbrido, com dois motores e um compositor:**

| Camada | Motor | Por quê |
|---|---|---|
| Cenários 3D | **Blender como módulo Python (`bpy` 5.3.0), render Cycles em CPU**. Compatível com o Python 3.13 deste ambiente (verificado; ainda não instalado nem testado) | Materiais, luz motivada, névoa e profundidade como nas referências; roda sem interface, por script |
| Personagens, inserts, rótulos, legendas | **skia-python** (versão 144.1, compatível, verificado) | Desenho vetorial 2D rápido em CPU, antialiasing de qualidade, texto com qualquer fonte, matrizes de transformação para o rig |
| Composição final | **Compositor próprio em Python** (skia + NumPy) | Câmera, transições, gradação, vinheta, grão e bloom aplicados igual em todos os planos |
| Codificação | **FFmpeg 6.1.1** (já instalado) | H.264/AAC, loudness, mixagem |

**Restrição decisiva: não há GPU neste ambiente** (nenhum `/dev/dri`, nenhuma placa NVIDIA). Por isso:
- **o Blender não renderiza animação quadro a quadro.** Ele renderiza **um fundo estático por plano**, maior que a tela e separado em 2–3 camadas de profundidade (fundo, meio, primeiro plano);
- o movimento de câmera é feito no compositor, como transformação 2D dessas camadas, com paralaxe entre elas. Isso reproduz o que as referências fazem: push-in lento em 74 % dos planos, pan, tilt, crash-zoom;
- EEVEE (o motor rápido do Blender) **funciona em modo software** neste ambiente, mas é lento: 51 s numa cena mínima, contra ~1 s do Cycles. Fica fora do pipeline, salvo se o teste técnico mostrar vantagem em cenas reais.

**Alternativa descartada:** render 3D completo da animação (personagens 3D). É lento demais sem GPU (estimativa: horas por vídeo) e se afasta do estilo 2D chapado definido no Manual de Direção de Arte.

### 15.2 Criação de personagens e cenários

> **Atualização de 25/11/2026: rig oficial do Heitor = rig v2** (`personagens/heitor/rig_v2/`, aprovado pelo diretor; substitui o rig v1 do piloto 01). Diferenças em relação ao plano original abaixo:
> - O rig é **código Python** (`codigo/heitor_v2.py` + `modelo.json` com paleta, proporções, ossos e limites), e não um `rig.json` de SVG em camadas. As partes são vetores desenhados por código no sistema de cada osso.
> - Esqueleto FK com ombro, cotovelo, punho, quadril, joelho e tornozelo; IK de 2 ossos; mãos com 5 dedos individuais; rosto paramétrico.
> - Animação reutilizável: ciclos de caminhada e corrida, camadas, gestos, transição de expressões e sincronia labial (`animacao.py`, `gestos.py`, `fala.py`).
> - **No cenário 3D:** fundo estático do Blender + âncoras 3D → 2D (`cena_t8_blender.py` e `t8()` em `testes_f4.py`).
> - **QA do personagem:** consistência entre vistas, estampa por OCR, cotovelos sem inversão (`verificar_cotovelos.py`) e marca do cenário nunca coberta (oclusão medida quadro a quadro).

**Personagens: boneco 2D recortado (cutout rig), em vetor.**
- Cada personagem é um arquivo de rig (`assets/personagens/<id>/rig.json`), uma árvore de partes: tronco → cabeça → (cabelo, olhos, sobrancelhas, boca); tronco → braço → antebraço → mão; quadril → coxa → perna → pé.
- Cada parte é uma forma vetorial (caminhos SVG) com cor base, um tom de sombra e um contorno fino opcional, com ponto de pivô na articulação.
- O rosto é uma biblioteca de trocas: olhos (ponto, arregalado branco, fechado, "><", brilhando), sobrancelhas (reta, V, arqueada), boca (linha, "o", aberta, sorriso). São as expressões da seção 2.5 do Manual de Animação.
- 4 vistas (frente, 3/4, perfil, costas), cada uma com seu conjunto de partes.
- A estampa "Modo Curioso" é uma parte filha do tronco, gerada do arquivo-mestre `assets/marca/camiseta_modo_curioso.svg` (texto já convertido em curvas, fonte Nunito ExtraBold), com variantes pré-deformadas por vista (ID-002 e ID-003).
- **Quem desenha:** eu escrevo os vetores por código a partir das especificações (cores e proporções do Heitor já definidas), gero a folha de modelo e itero com você até aprovar. Alternativa: um ilustrador entrega os SVG em camadas, e eu monto o rig.

**Cenários: 3D low-poly montado por script.**
- Cada cenário é um script `bpy` (`assets/cenarios/<id>/cena.py`): geometria, materiais (madeira, tijolo, azulejo, grama, asfalto), luz motivada (sol rasante, abajur, tocha), névoa volumétrica e câmeras nomeadas por enquadramento.
- Objetos de contexto vêm de uma biblioteca de modelos **CC0** (domínio público, uso comercial livre). Fontes previstas: Kenney, Quaternius, Poly Haven. Depende de liberar esses hosts na rede.
- Saída por plano: camadas PNG com transparência (fundo, meio, primeiro plano) em 1350×2400 (25 % de margem para o movimento de câmera) e um mapa de profundidade para desfoque.
- **Inserts científicos** (átomos, moléculas, holograma, térmica, visão noturna): desenhados em skia-python sobre fundo azul-marinho com bokeh, ou em Blender quando precisam de volume (rede cristalina, corpo holográfico).

### 15.3 Consistência visual dos personagens

| Mecanismo | Como garante |
|---|---|
| Rig único por personagem | O mesmo arquivo de vetores é usado em todo plano de todo episódio. O personagem não é redesenhado, só posado |
| Paleta travada | As cores vêm do rig (hex da especificação), nunca escolhidas no plano |
| Biblioteca fechada de expressões e poses | Só existem as trocas aprovadas na folha de modelo; nenhuma expressão "nova" no meio de um episódio |
| Estampa a partir do arquivo-mestre | A marca "Modo Curioso" nunca é redigitada; as variantes por vista são geradas uma vez e aprovadas |
| Proporção fixa | Altura em cabeças e tamanho relativo entre personagens definidos no rig; o enquadramento muda a escala do plano, não a do personagem |
| Luz por plano, não por personagem | O personagem recebe um "tom de luz" do cenário (multiplicador quente ou frio + direção da sombra), parametrizado, e a gradação final é comum a tudo |
| Versão do rig | `rig.json` versionado no Git; cada episódio registra a versão usada |
| QA visual | Folha de contato automática de cada episódio, conferida por mim quadro a quadro e por você contra a folha de modelo |

### 15.4 Movimentos de câmera e animações

**Câmera (no compositor):**
- Cada plano tem uma câmera virtual 2D: zoom, deslocamento x/y, giro, com curva de easing (ease-out padrão).
- As camadas do cenário se movem com fatores de paralaxe diferentes (fundo 0,6×, meio 1,0×, primeiro plano 1,4×). O personagem acompanha a camada em que está.
- Biblioteca de movimentos com os valores medidos na auditoria: push-in (6 %/s, total ~9 %), pull-out, pan, tilt, giro (~6°), crash-zoom (+40 % ou mais), punch-zoom (+7 % em 0,18 s), chicote (0,13 s com borrão de movimento), tremida de impacto (1,4 % do quadro, decaimento em 0,3–0,5 s, 18–24 Hz).
- Desfoque de profundidade e de movimento simulados no compositor.

**Animação de personagem (no rig):**
- Quadros-chave por parte (rotação nas juntas, posição, troca de expressão), interpolados com easing.
- **Nível base:** pose a pose com pose segurada, "respiração" (1–2 % de escala do tronco) e piscada automática; boca com 3 estados nas batidas da frase (sem sincronia labial), como as referências.
- **Nível ação:** antecipação → golpe → overshoot → assentamento, ciclos de corrida, quadro de impacto, só nos momentos de poder.
- **Efeitos:** biblioteca procedural em skia-python (ondas de choque, raios, partículas, fogo, gelo, vapor, contorno de poder), parametrizada por tempo.

### 15.5 Sincronização entre narração, imagens, legendas e efeitos sonoros

**Fonte única de tempo:** os tempos devolvidos pelo TTS.
1. **Voz:** o TTS gera `voz.wav` e os tempos de início e fim de cada caractere (endpoint `with-timestamps` da ElevenLabs). Juntamos os caracteres em palavras: `voz_palavras.json`.
2. **Compressão de pausas** (regra do canal: pausa ≥ 0,8 s vira 0,42 s; pausa de 0,18–0,8 s vira 0,18 s). Feita por nós com corte no silêncio, **remapeando os tempos das palavras** depois de cada pausa encurtada. Nunca time-stretch.
3. **Legendas:** o roteiro já vem dividido em blocos de 2–3 palavras. Cada bloco começa no início da 1ª palavra e termina no início do bloco seguinte. A palavra-chave do bloco vai em amarelo.
4. **Planos:** cada plano começa e termina em fronteiras de bloco de legenda (o corte cai entre blocos, como nas referências). O plano mediano alvo é de 1,5–2,0 s.
5. **Rótulos e efeitos:** o número aparece no quadro em que começa a palavra do número; o efeito, na palavra que o nomeia (marcação no roteiro, ex.: `{efeito:onda_choque}voou`).
6. **SFX:** um evento em cada corte com chicote, em cada tremida, em cada pop de rótulo e no clímax, posicionado no quadro exato do evento visual.
7. **Conversão para quadros:** `quadro = round(tempo × 30)`. Tudo vive em `montagem.json`, que o compositor e o mixador leem.
8. **Conferência:** o QA mede a coincidência entre cortes e SFX e confere se cada legenda está dentro da janela da palavra. Opcional: uma 2ª checagem com Whisper, se o Hugging Face for liberado.

### 15.6 Ferramentas, bibliotecas, APIs e serviços externos

| Item | Tipo | Uso | Situação |
|---|---|---|---|
| FFmpeg 6.1.1 | Local | Codificação, mixagem, loudness, análise | Instalado |
| Python 3.13, NumPy, Pillow | Local | Compositor, scripts | Instalados |
| OpenCV, RapidOCR, librosa | Local (pip) | QA automático (câmera, legendas, voz) | Instalados nesta sessão |
| skia-python 144.1 | Local (pip) | Render 2D (personagens, inserts, rótulos, legendas, composição) | **Instalado e testado** (25/11/2026) |
| bpy 5.3.0 (Blender) | Local (pip) | Render 3D dos cenários | **Instalado e testado**: Cycles CPU em ~1 s numa cena mínima de 270×480 |
| Fontes Roboto Condensed e Nunito | Arquivos (licença OFL) | Legenda, marca d'água, estampa, rótulos | **Versionadas** em `assets/fontes/`, com instâncias estáticas ExtraBold (800) e hashes |
| ElevenLabs API (Voice Design + TTS com tempos) | **Serviço externo pago** | Voz oficial e tempos de palavra | Exige plano pago, chave de API e liberar `api.elevenlabs.io` na rede |
| Modelos 3D CC0 (Kenney, Quaternius, Poly Haven) | Download externo, gratuito | Objetos de cenário | Exige liberar esses hosts |
| Biblioteca de SFX e música licenciada | Externo (gratuito ou pago) | Efeitos e trilha | **A decidir**. Precisa de licença válida para redes sociais, registrada por arquivo |
| Whisper (Hugging Face) | Download externo, gratuito | Checagem opcional de sincronia | Bloqueado hoje pela rede; opcional |
| GitHub + Git LFS | Externo | Versionamento de código, dados e assets pesados | Repositório existe; LFS a configurar |
| Node 22 + Chromium/Playwright | Local | Não necessário nesta arquitetura (reserva para prévias HTML) | Instalados |

### 15.7 O que roda localmente e o que depende de serviço externo

| Etapa | Onde roda | Dependência externa |
|---|---|---|
| Pauta e roteiro | Local (Claude + arquivos) | — |
| Voz (TTS) | **Externo** | ElevenLabs (rede + chave + plano) |
| Compressão de pausas e alinhamento | Local | — |
| Decupagem e linha do tempo | Local | — |
| Modelagem e render dos cenários | Local (CPU) | Download inicial de modelos CC0 |
| Rig e animação dos personagens | Local | Download inicial das fontes |
| Inserts, rótulos, legendas, efeitos | Local | — |
| Composição e codificação | Local | — |
| Mixagem e master | Local | Biblioteca de SFX e música (download/licença) |
| QA automático | Local | Whisper opcional |
| Armazenamento | **Externo** | GitHub (+ LFS) |
| Aprovação humana (voz, sotaque, folha de modelo, vídeo) | Você | — |

Depois que fontes, modelos, SFX e música estiverem baixados e versionados, **a única dependência externa por episódio é o TTS**.

### 15.8 Custos e limitações técnicas

**Custos:**

| Item | Custo | Observação |
|---|---|---|
| ElevenLabs | Assinatura mensal (o uso comercial exige plano pago) | **Preço não verificado por mim.** Conferir o plano e a cota de caracteres. Um episódio de ~300 palavras tem ~1.800 caracteres por geração, mais as regravações |
| Música e SFX | Zero (bibliotecas CC0 ou de licença livre) ou assinatura (bibliotecas comerciais) | Decisão sua; a licença precisa cobrir as plataformas de publicação |
| Modelos 3D, fontes, Blender, skia, FFmpeg | Zero | Licenças CC0, OFL, GPL, BSD e LGPL, compatíveis com uso comercial do vídeo |
| GitHub LFS | Zero até a cota gratuita; pago acima dela | Conferir a cota atual da conta |
| Processamento | Incluído no ambiente | Ver as limitações abaixo |

**Limitações:**
1. **Sem GPU:** os cenários viram fundos estáticos em camadas (15.1). Estimativa de render: 30–90 s por fundo em Cycles CPU, ~47 planos, ou seja, 0,5–1,5 h por episódio só de fundos, menos quando planos reaproveitam o mesmo cenário. **A medir no teste.**
2. **CPU de 4 núcleos e 15 GB de RAM:** a composição 2D em skia é estimada em 0,1–0,3 s por quadro, ou 5–15 min para 2.730 quadros (91 s a 30 qps). **A medir.**
3. **Ambiente efêmero:** o container é descartado quando a sessão para. Tudo precisa ser commitado e enviado ao GitHub ao fim de cada etapa. Renders intermediários podem ser recriados a partir dos dados.
4. **Rede restrita:** a ElevenLabs, os sites de modelos CC0, o Google Fonts e o Hugging Face precisam ser liberados nas configurações do ambiente.
5. **Eu não escuto áudio:** sotaque, naturalidade e mixagem precisam de aprovação humana. Eu confiro só os números (loudness, pausas, tom, sincronia).
6. **Animação limitada por design:** o rig recortado entrega o nível base das referências com consistência total. O nível ação (corridas, golpes) dá mais trabalho por plano e deve ficar concentrado nos momentos de poder.
7. **Detalhe dos cenários:** cenários ricos em objetos dependem da biblioteca CC0. Montar tudo do zero por script é possível, mas lento.
8. **Sotaque gaúcho:** não é garantido pelo TTS (ver ID-001).

### 15.9 Geração do vídeo final em 1080×1920

1. O compositor lê `montagem.json` e, para cada quadro (30 qps), monta as camadas do plano:
   - fundo em camadas → personagens → efeitos;
   - câmera virtual (transformação e paralaxe) aplicada sobre a área de 1350×2400, recortando 1080×1920;
   - acabamento comum: gradação (sombra Lab b ≈ −10, alta luz b ≈ +18), vinheta (~0,57), bloom, grão;
   - por cima: rótulos, legendas e, por último, a marca d'água **"MODO CURIOSO"**, fora da gradação.
2. Os quadros saem em RGB 8 bits por pipe direto para o FFmpeg, sem gravar milhares de PNG:
   `ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i mix.wav -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 192k -ar 48000 -movflags +faststart MC_<serie>_<ep>_v<n>.mp4`
3. Áudio (`mix.wav`) feito antes, com FFmpeg:
   - voz com pausas comprimidas;
   - música com ducking (`sidechaincompress`);
   - SFX nos quadros da linha do tempo;
   - `loudnorm` em duas passadas para −14 LUFS e limitador de pico real em −1 dBTP.
4. QA automático com `tools/analise`: duração, cortes/min, plano mediano, movimento de câmera, vinheta, cor, loudness, legendas (posição, palavras, amarelo), grafia da marca d'água. O relatório sai em `qa_relatorio.json`.
5. Folha de contato do episódio para a minha revisão visual e a sua aprovação final.

## 16. Decisões pendentes (suas)

1. **Aprovar a arquitetura da seção 15**, em especial o motor híbrido (Blender para fundos + rig 2D em skia + compositor próprio).
2. **Voz:** direção decidida (ID-001). Falta contratar o plano, aprovar a amostra no teste da seção 1.5 de `IDENTIDADE_OFICIAL.md` e liberar o acesso (rede e chave de API).
3. **Rede do ambiente:** liberar `api.elevenlabs.io` e os hosts de assets (modelos CC0, fontes). Liberar o Hugging Face é opcional (checagem de sincronia com Whisper).
4. **Música e SFX:** escolher a biblioteca (CC0/gratuita ou assinatura comercial) com licença válida para as plataformas de publicação.
5. ~~Quem desenha o rig dos personagens~~ **Decidido em 25/11/2026:** por código. O rig v2 do Heitor foi aprovado como oficial (`personagens/heitor/rig_v2/`).
6. **Git LFS** para os assets pesados e os MP4 de referência.
7. **Arquivo `Padrão Modo Curioso.md`:** ele não está no repositório (detalhe na auditoria). Reenviar, ou confirmar que a versão no skill do canal é a oficial. Desde 25/11/2026, a cópia do skill alinhada à identidade oficial está em `skills/modo-curioso-padrao/SKILL.md`.

## 17. Próxima etapa proposta (sem gerar o vídeo completo)

1. Teste técnico de 10 s: 1 cenário, o Heitor, 5 planos, legenda, câmera e mix. Serve para validar a arquitetura da seção 15 de ponta a ponta, **medir os tempos reais de render** (15.8) e passar pelo QA automático. Depende das decisões 1–3 da seção 16.
2. ~~Folha de modelo do Heitor nas 4 vistas e 9 expressões~~ **Feito:** rig v2 oficial (4 vistas, 11 expressões, mãos, caminhada e corrida, gestos, fala), aprovado em 25/11/2026.
3. Só depois disso: o primeiro episódio completo.
