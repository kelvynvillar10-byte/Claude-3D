# Modo Curioso Studio AI — instruções para o Claude

Responda em português do Brasil. O usuário é o diretor do estúdio. Ele aprova cada etapa antes da execução.

## Ao abrir uma sessão nova
0. Use o ambiente cloud **"Claude-3D"**: o script de configuração dele roda `ambiente/instalar.sh` sozinho em cada container novo.
1. Ambiente: rode `.venv/bin/python ambiente/verificar.py --rapido`. Se falhar ou `.venv` não existir, rode `bash ambiente/restaurar.sh` (procedimento em `ambiente/RESTAURAR.md`). Use sempre `.venv/bin/python`, nunca o Python do sistema.
2. Leia `docs/IDENTIDADE_OFICIAL.md`. Ele prevalece sobre qualquer outro documento ou skill.
3. Estado e próximos passos: `docs/PIPELINE_PRODUCAO.md`, seções 15 (arquitetura), 16 (decisões pendentes) e 17 (próxima etapa).

## Estado atual (atualize ao fim de cada etapa)
- Concluído: auditoria dos 13 MP4 (`docs/AUDITORIA_REFERENCIAS.md`), manuais, identidade oficial (ID-001 a ID-003), arquitetura técnica (proposta, seção 15), ambiente reproduzível (`ambiente/`, `Dockerfile`).
- **Não iniciar o vídeo-piloto sem autorização explícita do usuário.**
- Pendências do usuário: aprovar a arquitetura; plano e chave da ElevenLabs; liberar hosts na rede; biblioteca de música e SFX; quem desenha o rig; Git LFS.

## Regras fixas
- Camiseta: exatamente "Modo Curioso". Marca d'água: exatamente "MODO CURIOSO".
- Nunca copiar personagens, marcas ou obras de terceiros (as referências citam JoJo, One Piece, Lucy, Clash; nós não). Nunca clonar voz sem autorização por escrito.
- Não inventar análises: diga o que foi medido, o que foi visto e o que não pôde ser verificado.
- Chaves de API nunca no repositório (use o mecanismo de credenciais do ambiente).
- Mudou dependência: siga "Mudar uma dependência" em `ambiente/RESTAURAR.md` (lock + `VERSOES.md` + Docker).
- Ao fim de cada etapa: commit e push no branch de trabalho.

## Comandos úteis
- Análise e QA de vídeo: `tools/analise/` (ver o README da pasta).
- Fontes oficiais: `assets/fontes/Nunito-ExtraBold.ttf` (estampa, rótulos), `assets/fontes/RobotoCondensed-ExtraBold.ttf` (legendas, marca d'água).
