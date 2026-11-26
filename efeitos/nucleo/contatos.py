"""CONTATOS: pontos onde o efeito se prende.
- No rig v2 (sem alterar o rig): mão, pé, cabeça, peito — calculados com o esqueleto do próprio rig (FK) e a mesma
  transformação que o desenho usa (pés na tela, altura em px, direção).
- No cenário: qualquer ponto 3D (parede, chão, poste, veículo), projetado com a câmera da placa.
Retornam pontos na TELA da placa (x, y, profundidade) já com o movimento de câmera."""
import sys
from pathlib import Path
_RIG = Path(__file__).resolve().parents[2] / "personagens" / "heitor" / "rig_v2" / "codigo"
if str(_RIG) not in sys.path:
    sys.path.insert(0, str(_RIG))
import heitor_v2 as HV   # noqa: E402  (rig v2 oficial — só leitura: esqueleto e pontos)

PONTOS_RIG = {"mao_d": ("mao_d", 0.0, 0.17), "mao_e": ("mao_e", 0.0, 0.17), "pe_d": ("pe_d", 0.05, 0.05), "pe_e": ("pe_e", 0.05, 0.05),
              "cabeca": ("cabeca", 0.0, -0.55), "peito": ("tronco", 0.0, -0.75)}


def rig(ctx, nome):
    pc = ctx.personagem; osso, lx, ly = PONTOS_RIG[nome]
    M = HV.esqueleto(pc["pose"], pc["vista"]); q = HV.ponto_mundo(M[osso], lx, ly)
    x, y, _, z = pc["pe_tela"]; _, yt, _, _ = pc["topo_tela"]; u = (y - yt) / 4.0
    return (x + q.x() * u * pc.get("direcao", 1), y + q.y() * u, z)


def rig_mundo(ctx, nome):
    """O mesmo ponto do rig levado ao MUNDO (no plano do personagem), para efeitos 3D (partículas saindo da mão)."""
    pc = ctx.personagem; x, y, z = rig(ctx, nome)
    I = ctx.P.m["intrinsecos"]; import numpy as np
    pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))
    # desfaz o movimento de câmera (aproximação: plano do personagem) e reprojeta o raio da câmera nessa profundidade
    cam = ctx.cam; zz = pc["pe_tela"][3] + cam.get("tz", 0.0); zoom = cam.get("zoom", 1.0)
    u = ((x - ctx.P.cx) / zoom * (zz - cam.get("tz", 0.0)) + ctx.P.f * cam.get("tx", 0.0)) / zz
    v = ((y - ctx.P.cy) / zoom * (zz - cam.get("tz", 0.0)) - ctx.P.f * cam.get("ty", 0.0)) / zz
    return pos + (dr + (u / ctx.P.f) * dx - (v / ctx.P.f) * cima) * zz


def mundo(ctx, p):
    x, y, _, z = ctx.tela(p)
    return (x, y, z)
