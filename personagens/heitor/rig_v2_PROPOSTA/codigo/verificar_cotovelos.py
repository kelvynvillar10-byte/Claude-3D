#!/usr/bin/env python3
"""Heitor rig v2 (PROPOSTA) — auditoria da regra anatômica do cotovelo (ver gestos.cotovelo_invertido).

Verifica todas as poses desenhadas nas folhas da F1, todos os quadros dos ciclos da F2 (caminhada e corrida,
perfil/frente/costas) e lê o resultado dos testes da F3 (medido durante a renderização).
Saída: verificacao/cotovelos.md
"""
import json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import heitor_v2 as H   # noqa: E402
import animacao as A    # noqa: E402
import gestos as G      # noqa: E402


def auditar(registros):
    inv = []
    for i, (v, p) in enumerate(registros):
        for l in ("d", "e"):
            r, ab, rel = G.cotovelo_invertido(p, v, l)
            if r:
                inv.append(f"#{i} {v} braço_{l}: braço {ab:.0f}°, antebraço {rel:+.0f}°")
    return inv


linhas = ["# Auditoria dos cotovelos — Heitor rig v2 (PROPOSTA)", "",
          "Regra: no perfil o antebraço só dobra para a frente; de frente/costas/3-4, com o braço acima da horizontal, "
          "o antebraço só dobra para cima (em direção à cabeça). Tolerância 5°.", "",
          "| Conjunto | Poses/quadros verificados | Cotovelos invertidos |", "|---|---|---|"]
# F1: folhas
import folhas  # noqa: E402
H.AUDITORIA = []
folhas.folha_modelo(); folhas.folha_expressoes(); folhas.folha_articulacoes()
f1 = list(H.AUDITORIA); H.AUDITORIA = None
inv = auditar(f1); linhas.append(f"| F1 folhas (modelo, expressões, articulações) | {len(f1)} | {len(inv)} |"); det = inv[:]
# F2: ciclos
f2 = []
for vista in ("perfil", "frente", "costas"):
    for tipo in ("caminhada", "corrida"):
        for q in range(60):
            f2.append((vista, A.pose_locomocao(q / 30, vista, tipo)[0]))
inv = auditar(f2); linhas.append(f"| F2 caminhada e corrida (3 vistas, 2 s cada) | {len(f2)} | {len(inv)} |"); det += inv
# F3: medido na renderização
m = json.loads((AQUI.parent / "testes" / "f3_metricas.json").read_text())
for k, v in m.items():
    linhas.append(f"| F3 {k} | todos os quadros | {v.get('quadros_com_cotovelo_invertido', 'não medido')} |")
if det:
    linhas += ["", "## Ocorrências", ""] + [f"- {d}" for d in det]
(AQUI.parent / "verificacao" / "cotovelos.md").write_text("\n".join(linhas) + "\n")
print("\n".join(linhas))
