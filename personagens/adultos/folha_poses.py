#!/usr/bin/env python3
"""Folha de poses-chave do EP02 (PROPOSTA): Juca jogando no sofá, Jandira com a caixa e irritada."""
import copy, json, sys
from pathlib import Path
import skia
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rig_adulto as RA, poses as PO   # noqa: E402

OUT = AQUI / "folhas"; OUT.mkdir(exist_ok=True)
J = RA.carregar("juca"); D = RA.carregar("jandira")
F = skia.Font(J.H.NUNITO, 30); FT = skia.Font(J.H.NUNITO, 52)
TXT = 0xFF1F2A44


def mundo(x_pe, y_pe, alt, wx, wy, d=1):
    u = alt / 5.0; return x_pe + wx * u * d, y_pe + wy * u


def sofa_frente(c, x, chao, alt, assento_H):
    u = alt / 5
    c.drawRoundRect(skia.Rect.MakeLTRB(x - 1.2 * u, chao - (assento_H + 1.35) * u, x + 1.2 * u, chao - assento_H * u), 0.15 * u, 0.15 * u, PO._pt(0xFFB5523B))
    c.drawRoundRect(skia.Rect.MakeLTRB(x - 1.45 * u, chao - (assento_H + 0.55) * u, x - 0.95 * u, chao - 0.2 * u), 0.12 * u, 0.12 * u, PO._pt(0xFF9C4431))
    c.drawRoundRect(skia.Rect.MakeLTRB(x + 0.95 * u, chao - (assento_H + 0.55) * u, x + 1.45 * u, chao - 0.2 * u), 0.12 * u, 0.12 * u, PO._pt(0xFF9C4431))
    c.drawRoundRect(skia.Rect.MakeLTRB(x - 1.0 * u, chao - assento_H * u, x + 1.0 * u, chao - 0.2 * u), 0.1 * u, 0.1 * u, PO._pt(0xFFC45E45))
    for r in (skia.Rect.MakeLTRB(x - 1.2 * u, chao - (assento_H + 1.35) * u, x + 1.2 * u, chao - assento_H * u),
              skia.Rect.MakeLTRB(x - 1.0 * u, chao - assento_H * u, x + 1.0 * u, chao - 0.2 * u)):
        c.drawRoundRect(r, 0.12 * u, 0.12 * u, PO._ln(PO.CONTORNO, 0.02 * u))


def sofa_perfil(c, x, chao, alt, assento_H, frente=True):
    u = alt / 5
    if frente:
        r = skia.Rect.MakeLTRB(x - 0.5 * u, chao - (assento_H - 0.18) * u, x + 0.85 * u, chao - 0.2 * u)
        c.drawRoundRect(r, 0.1 * u, 0.1 * u, PO._pt(0xFFC45E45)); c.drawRoundRect(r, 0.1 * u, 0.1 * u, PO._ln(PO.CONTORNO, 0.02 * u))
    else:
        c.drawRoundRect(skia.Rect.MakeLTRB(x - 0.62 * u, chao - (assento_H + 1.3) * u, x - 0.22 * u, chao - 0.2 * u), 0.15 * u, 0.15 * u, PO._pt(0xFFB5523B))
        c.drawRoundRect(skia.Rect.MakeLTRB(x - 0.62 * u, chao - (assento_H + 1.3) * u, x - 0.22 * u, chao - 0.2 * u), 0.15 * u, 0.15 * u, PO._ln(PO.CONTORNO, 0.02 * u))


def main():
    W, Hh = 4200, 1900; s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(0xFFEDEBE6)
    c.drawString("EP02 — poses-chave (PROPOSTA): Juca jogando no sofá · Jandira com a caixa e irritada · objetos genéricos, sem marca", 50, 75, FT, skia.Paint(AntiAlias=True, Color=TXT))
    alt = 1250; chao = 1720; u = alt / 5
    relat = {}
    assento = J.H.PROP["joelho"] + 0.02
    # 1 — Juca jogando, frente
    x = 380
    sofa_frente(c, x, chao, alt, assento)
    p, (cx, cy), ang = PO.jogando(J, "frente", t=0.4)
    J.H.desenhar(c, x, chao, alt, "frente", 1, p, "alegria")
    PO.controle(c, *mundo(x, chao, alt, cx, cy), u, ang)
    relat["juca_jogando_frente"] = p
    # 2 — Juca jogando, perfil
    x = 1050
    sofa_perfil(c, x, chao, alt, assento, frente=False)
    sofa_perfil(c, x, chao, alt, assento, frente=True)
    p, (cx, cy), ang = PO.jogando(J, "perfil", t=0.4)
    p["objeto_d"] = PO.objeto_mundo(lambda cc, px, py: PO.controle(cc, px + 0.1 * u, py - 0.05 * u, u * 1.1, -25, perfil=True))
    J.H.desenhar(c, x, chao, alt, "perfil", 1, p, "vidrado")
    relat["juca_jogando_perfil"] = p
    # 3 — Juca no amanhecer (olheira + barba), frente
    x = 1720
    sofa_frente(c, x, chao, alt, assento)
    p, (cx, cy), ang = PO.jogando(J, "frente", t=1.3, intensidade=0.5)
    e = copy.deepcopy(J.H.EXPRESSOES["vidrado"]); e.update({"olheira": 1.0, "barba": 1.0, "palp_sup": 0.3})
    J.H.desenhar(c, x, chao, alt, "frente", 1, p, e)
    PO.controle(c, *mundo(x, chao, alt, cx, cy), u, ang)
    relat["juca_amanhecer"] = p
    # 4 — Jandira com a caixa, frente
    x = 2420; altD = alt * 0.94
    p, (bx, by) = PO.segurando_caixa(D, "frente")
    D.H.desenhar(c, x, chao, altD, "frente", 1, p, "alegria")
    PO.caixa_presente(c, *mundo(x, chao, altD, bx, by), altD / 5, larg=1.1, alt=0.85)
    relat["jandira_caixa_frente"] = p
    # 5 — Jandira com a caixa, perfil (andando)
    x = 3000
    p, (bx, by) = PO.segurando_caixa(D, "perfil")
    ca, _ = D.A.pose_locomocao(0.2, "perfil", "caminhada")
    for k in ("coxa_d", "coxa_e", "canela_d", "canela_e", "pe_d", "pe_e", "raiz"):
        p[k] = ca[k]
    PO.segurando_caixa  # (braços recalculados com a pelve da caminhada)
    p2, _ = PO.segurando_caixa(D, "perfil", y_centro=by + p["raiz"][1])
    for k in ("braco_d", "braco_e", "antebraco_d", "antebraco_e", "mao_d", "mao_e", "dedos_d", "dedos_e"):
        p[k] = p2[k]
    yb = by + p["raiz"][1]
    p["objeto_d"] = PO.objeto_mundo(lambda cc, px, py: PO.caixa_presente(cc, *mundo(x, chao, altD, 0.62, yb), altD / 5, larg=0.8, alt=0.85))
    D.H.desenhar(c, x, chao, altD, "perfil", 1, p, "alegria")
    relat["jandira_caixa_perfil"] = p
    # 6 — Jandira de braços cruzados, irritada
    x = 3700
    p = PO.bracos_cruzados(D, "frente")
    D.H.desenhar(c, x, chao, altD, "frente", 1, p, "irritada")
    relat["jandira_bracos_cruzados"] = p
    for i, nm in enumerate(["Juca jogando (frente)", "Juca jogando (perfil, vidrado)", "Juca ao amanhecer (olheira + barba)",
                            "Jandira chega com a caixa", "Jandira andando com a caixa", "Jandira irritada (braços cruzados)"]):
        xs = [380, 1050, 1720, 2420, 3000, 3700][i]; w = F.measureText(nm)
        c.drawString(nm, xs - w / 2, chao + 70, F, skia.Paint(AntiAlias=True, Color=TXT))
    s.makeImageSnapshot().save(str(OUT / "folha_poses_ep02.png"), skia.kPNG)
    # regra do cotovelo (mesma verificação do rig v2.1)
    res = {}
    for nome, pp in relat.items():
        P = J if nome.startswith("juca") else D
        vista = "perfil" if "perfil" in nome else "frente"
        res[nome] = {lado: bool(P.G.cotovelo_invertido(pp, vista, lado)[0]) for lado in ("d", "e")}
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
