# Narração: MiniMax T2A V2 com diretor de narração

**Etapa 2 do pipeline (voz).** Em teste. **A voz `ttv-voice-2026112700223026-9zUmd7PO` é candidata, NÃO aprovada.** O clone antigo está proibido no código. Nenhum episódio ou piloto foi produzido.

## Regras de economia (do diretor, embutidas no código)
- **Nada é sintetizado sem autorização** registrada em `orcamento.json`, com o limite de caracteres de cada teste ou execução. O teto total dos testes é de 1.500 caracteres; isso é limite, não meta.
- **A contagem vem antes de cada chamada.** Se a execução inteira não couber na autorização, **nada sai**.
- **Cache versionado** (`cache/`): a mesma combinação de texto, modelo, voz e parâmetros nunca é paga de novo, inclusive em sessões novas.
- **Nenhuma nova tentativa automática.** Em qualquer falha, registra e para. Em queda de rede, os caracteres são debitados por segurança, porque não dá para saber se houve cobrança.
- **Registro de cada chamada** em `consumo.jsonl`:
  - caracteres enviados e caracteres cobrados (`usage_characters`);
  - custo estimado;
  - saldo, só se a API informar;
  - modelo e voz;
  - motivo e resultado;
  - identificador da chamada (`trace_id`).
- **Direção antes da síntese:** ajustes se fazem na folha de direção, nunca regenerando áudio por mudanças pequenas.

## Chave da API (nunca no Git, no chat ou no código)
- **Opção A, recomendada:** segredo de rede do ambiente "Claude-3D". O proxy insere a chave nas chamadas para `api.minimax.io`, e ela não entra no container. Rode com `MINIMAX_SEGREDO_DE_REDE=1`.
- **Opção B:** variável de ambiente `MINIMAX_API_KEY`, cadastrada nas configurações do ambiente ou no seu computador, fora do Git (`.env` está no `.gitignore`).
- **Proteção:** a chave nunca é gravada nem impressa; o teste T0 varre os arquivos procurando-a.

## Diretor de narração (`direcao.py`)
São 8 intenções: curiosidade, entusiasmo, mistério, suspense, surpresa, tensão, emoção e explicação neutra.

O fluxo tem três passos:
1. Um **rascunho por regras** classifica cada frase.
2. O **Claude revisa** trecho a trecho e grava `direcao.json`, com uma justificativa por trecho.
3. O **diretor aprova a folha** antes de qualquer síntese.

Funcionamento:
- **Um trecho é uma chamada**, porque velocidade, volume, tom e emoção valem para a chamada inteira. A cobrança é por caractere, então dividir não encarece.
- **Pausas entre trechos** viram silêncio inserido na montagem, que é de graça.
- **Emoções** só entram depois que o teste as confirma para esta voz (`emocoes_aceitas_pela_voz`). Antes disso, o trecho vai sem emoção.
- **Variação obrigatória:** a validação recusa uma direção com os mesmos parâmetros em toda a narração.

## Saídas por vídeo (`gerar.py gerar`)
- `trechos/*.mp3`, `cenas/*.mp3`, `voz.mp3` (consolidada) e `voz.wav` (48 kHz, para a mixagem);
- `voz_palavras.json`, com o início e o fim de cada palavra:
  - fonte principal: os tempos por palavra da própria MiniMax;
  - plano B: a duração de cada trecho dividida pelas letras.
- `voz_registro.json`: modelo, voz e status dela, parâmetros por trecho, maior pausa interna e caracteres.

**Sem aceleração na pós-produção:** a montagem só apara o silêncio das pontas e insere as pausas dirigidas. A velocidade se corrige na direção.

## Comandos
```
.venv/bin/python narracao/testes/teste_t0.py                         # T0: sem rede, sem créditos
.venv/bin/python narracao/gerar.py teste T2                          # simulação: contagem e custo (nada é enviado)
.venv/bin/python narracao/gerar.py simular narracao/testes/roteiro_teste.json --direcao narracao/testes/direcao_teste.json
# só com autorização registrada no orcamento.json:
.venv/bin/python narracao/gerar.py vozes --autorizado T1
.venv/bin/python narracao/gerar.py teste T2 --autorizado T2
```

## Testes planejados (`testes/planos.json`)
| Teste | O que faz | Caracteres | Situação |
|---|---|---|---|
| T0 | testes sem rede | 0 | **feito: 21/21 OK** |
| T1 | consulta de vozes, sem síntese | 0 | **2 consultas, ambas código 1004 (não autenticou)**: a 1ª com a senha de login por engano, a 2ª depois de trocar pela API Secret Key; sem cobrança indicada; parado aguardando o diretor |
| T2 | "Olá, Modo Curioso." (voz + modelo + tempos por palavra) | 18 | aguarda autorização |
| T3 | "Olha só." com happy e surprised | 16 | aguarda autorização |
| T4 | comparativo A, B e C | 208 | aguarda autorização |
| T5 | roteiro de teste com 3 cenas (194 caracteres) | 194 | só com nova autorização expressa |

**Fontes da API:** um espelho da documentação oficial (speech.md, errors.md) e o MiniMax-MCP oficial. A documentação em `platform.minimax.io` está bloqueada pela rede deste ambiente.
