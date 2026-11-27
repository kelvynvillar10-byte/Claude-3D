# Juca e Jandira — rig adulto v1 (PROPOSTA, aguardando aprovação do diretor)

Personagens do EP02 ("E se a sua namorada te desse um videogame…"). Nomes definidos pelo diretor em 27/11/2026; aparência proposta pelo Claude.

- **Rig:** `rig_adulto.py` carrega uma cópia própria do rig oficial do Heitor v2.1 (`heitor_v2`, `animacao`, `gestos`) por personagem e troca só paleta, proporções de adulto (5 H), ossos, larguras, cabelo, tronco, calça e calçado. **O rig do Heitor não foi alterado.** Esqueleto, IK, mãos de 5 dedos, rosto, expressões, caminhada/corrida e a regra do cotovelo são os do v2.1.
- **Modelos:** `modelos.json` (paleta hex, proporções, ossos, larguras).
- **Juca:** ~28 anos, pele morena, cabelo crespo curto, barba rala, camiseta verde "Modo Curioso", moletom cinza, chinelo.
- **Jandira:** ~27 anos (em cena, 94 % da altura do Juca), cabelo longo ondulado com risca lateral, cílios, camiseta roxa "Modo Curioso", jeans, tênis branco com faixa roxa.
- **Expressões novas:** `vidrado` (olhos arregalados no jogo), `irritada`, `desconfiada`; parâmetros de rosto `olheira` e `barba` (0–1) para a passagem de tempo.
- **Poses e objetos do EP02:** `poses.py` (sentado jogando, segurando a caixa, braços cruzados; controle, caixa de presente e console genéricos, sem marca).
- **Folhas:** `folhas/folha_modelo_*.png`, `folhas/folha_expressoes_*.png`, `folhas/folha_poses_ep02.png`. Regerar: `../../.venv/bin/python folhas.py && ../../.venv/bin/python folha_poses.py` (a segunda também confere os cotovelos: 0 invertidos nas 6 poses).

Limitações: o cabelo da Jandira não balança ainda (fica para a animação); as vistas espelhadas trocam o lado da risca do cabelo (mesma limitação do Heitor); o controle de perfil é um desenho frontal comprimido (trapaça 2D).
