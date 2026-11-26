# Modo Curioso Studio AI — instruções para o Claude

Responda em português do Brasil. O usuário é o diretor do estúdio. Ele aprova cada etapa antes da execução.

## Ao abrir uma sessão nova
0. Use o ambiente cloud **"Claude-3D"**: o script de configuração dele roda `ambiente/instalar.sh` sozinho em cada container novo.
1. Ambiente: rode `.venv/bin/python ambiente/verificar.py --rapido`. Se falhar ou `.venv` não existir, rode `bash ambiente/restaurar.sh` (procedimento em `ambiente/RESTAURAR.md`). Use sempre `.venv/bin/python`, nunca o Python do sistema.
2. Leia `docs/IDENTIDADE_OFICIAL.md`. Ele prevalece sobre qualquer outro documento ou skill.
3. Estado e próximos passos: `docs/PIPELINE_PRODUCAO.md`, seções 15 (arquitetura), 16 (decisões pendentes) e 17 (próxima etapa).

## Estado atual (atualize ao fim de cada etapa)
- Concluído: auditoria dos 13 MP4 (`docs/AUDITORIA_REFERENCIAS.md`), manuais, identidade oficial (ID-001 a ID-004), arquitetura técnica (proposta, seção 15), ambiente reproduzível (`ambiente/`, `Dockerfile`).
- Piloto técnico 01 (10 s) produzido em `pilotos/piloto_01_ultimo_homem/` e **aguardando avaliação do diretor**. Feito com o rig v1, hoje substituído pelo v2; voz temporária espeak-ng.
- **Rig oficial do Heitor: v2** em `personagens/heitor/rig_v2/` (aprovado pelo diretor em 25/11/2026; F1–F4, `RELATORIO_FINAL.md`). Use-o em toda produção nova; ele substitui o rig v1. QA do personagem: `verificar_f1.py`, `verificar_cotovelos.py`, oclusão da marca no cenário.
- **Cenografia** (`cenografia/`): direção aprovada (procedural no Blender + efeitos 2D/2.5D; estilizado cinematográfico; bairro urbano brasileiro; sem sites externos; ordem dos poderes: eletricidade, terra, voo, aranha, elasticidade). E0 a E6 **aprovadas** (cena de prova: `cenografia/testes/e6/E6_cena_prova.mp4`); E7 (núcleo de efeitos em `efeitos/`) **aprovada**; E8 parte 1 (poderes eletricidade e terra, `efeitos/poderes/`) **aprovada** (`cenografia/testes/E8_RELATORIO.md`). **Extensão X1 "tom de luz no personagem" aprovada** em 26/11/2026 (`personagens/heitor/extensoes/x1_tom_de_luz/`; fora do rig; força padrão, sem ajuste): usar `tom_personagem=fazer_tom(...)` nas composições novas com o Heitor. Borda do compositor (camada não pré-multiplicada somada como pré-multiplicada): **o diretor decidiu NÃO corrigir**. **Extensão X2 "voo" aprovada** em 26/11/2026 (`personagens/heitor/extensoes/x2_voo/`; poses de voo, corpo inclinado, roupa e cabelo ao vento, barra solta sobre o cós do jeans; fora do rig): usar `voo.desenhar(...)` nos planos de voo. Próximo: poder de voo (E8 parte 2), depois as extensões de aranha e elasticidade, cada uma com aprovação específica. Voo, aranha e elasticidade só depois da aprovação específica das extensões do rig (apresentar cada uma à parte). Nenhuma extensão do rig sem aprovação específica.
- **Não iniciar produção em escala nem novos pilotos sem autorização explícita do usuário.**
- Pendências do usuário: aprovar a arquitetura; plano e chave da ElevenLabs; liberar hosts na rede; biblioteca de música e SFX; Git LFS liberado quando tecnicamente necessário (ainda não usado).

## Regras fixas
- Camiseta (e patch do figurino): exatamente "Modo Curioso". Marca d'água: exatamente "MODO CURIOSO". Marca dentro do cenário (telas, envelopes, fichas, placas): exatamente "MODO CURIOSO" (ID-004). Qualquer outra grafia reprova no QA.
- Nunca copiar personagens, marcas ou obras de terceiros (as referências citam JoJo, One Piece, Lucy, Clash; nós não). Nunca clonar voz sem autorização por escrito.
- Não inventar análises: diga o que foi medido, o que foi visto e o que não pôde ser verificado.
- Chaves de API nunca no repositório (use o mecanismo de credenciais do ambiente).
- Mudou dependência: siga "Mudar uma dependência" em `ambiente/RESTAURAR.md` (lock + `VERSOES.md` + Docker).
- Ao fim de cada etapa: commit e push no branch de trabalho.

## Comandos úteis
- Análise e QA de vídeo: `tools/analise/` (ver o README da pasta).
- Fontes oficiais: `assets/fontes/Nunito-ExtraBold.ttf` (estampa, rótulos), `assets/fontes/RobotoCondensed-ExtraBold.ttf` (legendas, marca d'água).
