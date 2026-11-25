"""Kit de RUA e CALÇADA (etapa E2) — bairro urbano brasileiro.

Convenção: a rua principal corre ao longo de y, com a pista centrada em x = 0. Topo do meio-fio e da calçada: 0,15 m.
Componentes (todos com parâmetros e semente; nenhum texto de marca real — só nomes inventados e "MODO CURIOSO"):
- rua_trecho    pista com remendos, faixas, sarjeta, tampas, bocas de lobo, meio-fio com rebaixos de garagem,
                calçadas por LOTE (cada casa com o seu piso, como nos bairros reais), piso tátil, canteiros, folhas, mato
- cruzamento    cruzamento com a rua transversal (ao longo de x), esquinas arredondadas, faixas de pedestre, linhas de
                retenção, piso de alerta nas esquinas
- poste_concreto  poste de concreto afunilado, cruzeta com isoladores, luminária LED, transformador opcional;
                  registra os pontos de fixação dos fios
- fiacao        cabos em catenária entre postes da mesma linha (energia + telecom), com sobras enroladas
- semaforo, placa_rua, placa_regulamentacao, hidrante, lixeira_poste
Peças presas a outras (luminária, placas, fios) têm a marca "suspenso" (o QA de "nada flutuando" sabe que é de propósito).
"""
import math
from mathutils import Vector
import bpy
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M, luz as L

H_CALC = 0.15    # topo do meio-fio e da calçada (m)
MF = 0.15        # largura do meio-fio (m)
SARJ = 0.30      # largura da sarjeta (m)


def _mats(um=0.0):
    return {"tinta_b": M.pintura("#ece6d6", rug=0.7, desgaste=0.6), "tinta_a": M.pintura("#e8b52a", rug=0.7, desgaste=0.5),
            "meiofio": M.concreto("#bdb6a8", placa_m=(1.0, 0.15), desgaste=0.5, sujeira=0.6, umidade=um),
            "sarjeta": M.concreto("#9e978a", placa_m=(1.0, 0.3), desgaste=0.6, sujeira=0.7, umidade=um),
            "ferro": M.metal_ferrugem("#3b3d40", ferrugem=0.3), "escuro": M.pintura("#0d0d0f", rug=0.9),
            "base": M.concreto("#7d776c", placa_m=(2.0, 2.0)), "tatil": M.pintura("#d9a51f", rug=0.6, desgaste=0.4),
            "metal": M.pintura("#5b6068", rug=0.4, metal=0.6, desgaste=0.3), "folha": M.pintura("#a8662c", rug=0.9),
            "folha2": M.pintura("#c99a3c", rug=0.9), "terra": M.terra(), "mato": M.folhagem("#5d7f34")}


def _calcada_mat(nome, um, rng):
    if nome == "calcada_portuguesa":
        return M.calcada_portuguesa(onda_m=rng.choice([1.2, 1.6, 2.0]), umidade=um)
    if nome == "ladrilho_hidraulico":
        return M.ladrilho_hidraulico(cor_a=rng.choice(["#b7452f", "#2f6f5f", "#c4952e"]), cor_b=rng.choice(["#2f5f8a", "#3a3a3a"]))
    if nome == "concreto":
        return M.concreto(rng.choice(["#aaa294", "#b8b0a0", "#9f9a90"]), placa_m=rng.choice([(1.0, 1.0), (0.6, 0.6), (1.5, 1.0)]), umidade=um, detalhe=1.0)
    return M.por_nome(nome)


def _grupo(nome, objs, loc, rot_z, col):
    """Agrupa objetos construídos na origem e posiciona/gira o grupo (semáforo, placas)."""
    e = bpy.data.objects.new(nome, None); col.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rot_z)
    for o in objs:
        o.parent = e
    return e


# ------------------------------------------------------------------ trecho de rua
@componente("rua_trecho")
def rua_trecho(ctx, p, rng, col):
    y0, y1 = p["y0"], p["y1"]; Lp = p.get("largura_pista", 7.0); C = p.get("largura_calcada", 3.2); um = p.get("umidade", 0.0)
    m = _mats(um); nome = p.get("nome", f"trecho_{int(y0)}")
    G.caixa(nome + "_pista", (-Lp / 2 + SARJ, y0, -0.05), (Lp / 2 - SARJ, y1, 0.0), M.asfalto(desgaste=p.get("desgaste", 0.55), umidade=um, detalhe=p.get("detalhe_asfalto", 1.0),
                                                                           faixas_x=(-(Lp / 2 - SARJ) / 2, (Lp / 2 - SARJ) / 2)), col)
    for s in (-1, 1):
        xa, xb = sorted((s * (Lp / 2 - SARJ), s * Lp / 2))
        G.caixa(f"{nome}_sarjeta{s}", (xa, y0, -0.05), (xb, y1, 0.004), m["sarjeta"], col)
    # remendos de asfalto (mais novos e mais escuros, ou velhos e mais claros)
    for i in range(p.get("remendos", 4)):
        w, l = rng.uniform(0.8, 2.2), rng.uniform(1.0, 3.2); x = rng.uniform(-Lp / 2 + 0.5, Lp / 2 - 0.5 - w); y = rng.uniform(y0 + 1, y1 - 1 - l)
        G.caixa(f"{nome}_remendo{i}", (x, y, -0.01), (x + w, y + l, 0.006),
                M.asfalto(cor=rng.choice(["#36363a", "#56565a"]), desgaste=0.25, umidade=um), col)
    # sinalização horizontal
    marc = p.get("marcacao", "tracejada_branca")
    if marc == "dupla_amarela":
        for dx in (-0.12, 0.12):
            G.caixa(f"{nome}_eixo{dx}", (dx - 0.05, y0, 0.0), (dx + 0.05, y1, 0.004), m["tinta_a"], col)
    else:
        y = y0 + 0.5; i = 0
        while y < y1 - 1:
            G.caixa(f"{nome}_tracejada{i}", (-0.06, y, 0.0), (0.06, y + min(3.0, y1 - y), 0.004), m["tinta_b"], col); y += 7.0; i += 1
    for s in (-1, 1):
        xb = s * (Lp / 2 - SARJ - 0.25)
        G.caixa(f"{nome}_bordo{s}", (xb - 0.05, y0, 0.0), (xb + 0.05, y1, 0.004), m["tinta_b"], col)
    # tampas de inspeção (ferro, circulares)
    for i in range(p.get("tampas", 2)):
        x = rng.uniform(-Lp / 2 + 1.2, Lp / 2 - 1.2); y = rng.uniform(y0 + 2, y1 - 2)
        G.cilindro(f"{nome}_tampa{i}", (x, y, -0.01), 0.34, 0.018, m["ferro"], col, lados=28)
        G.cilindro(f"{nome}_tampa_aro{i}", (x, y, -0.01), 0.40, 0.012, m["sarjeta"], col, lados=28)
    # lados: meio-fio, bocas de lobo, calçadas por lote
    lotes_tipos = p.get("calcadas", ["calcada_portuguesa", "concreto", "ladrilho_hidraulico", "concreto"])
    for s in p.get("lados", [-1, 1]):
        x_mf0, x_mf1 = sorted((s * Lp / 2, s * (Lp / 2 + MF)))
        x_c0, x_c1 = sorted((s * (Lp / 2 + MF), s * (Lp / 2 + MF + C)))
        G.caixa(f"{nome}_base{s}", (x_c0, y0, -0.05), (x_c1, y1, H_CALC - 0.01), m["base"], col)
        y = y0; k = 0; rebaixos = []
        while y < y1 - 0.5:
            comp = min(rng.uniform(8.0, 14.0), y1 - y)
            tipo = rng.choice(lotes_tipos); mat = _calcada_mat(tipo, um, rng); dz = rng.uniform(-0.006, 0.008)
            garagem = rng.random() < p.get("garagens", 0.3) and comp > 6
            if garagem:   # rebaixo do meio-fio + rampa da garagem no começo da calçada
                g0 = y + rng.uniform(1.0, comp - 4.0); g1 = g0 + 3.0; rebaixos.append((g0, g1))
                xr0, xr1 = sorted((s * (Lp / 2 + MF), s * (Lp / 2 + MF + 0.6)))
                G.rampa(f"{nome}_rampa{s}_{k}", xr0, xr1, g0, g1, 0.03, H_CALC + dz, "+x" if s > 0 else "-x", mat, col)
                xa0, xa1 = sorted((s * (Lp / 2 + MF + 0.6), s * (Lp / 2 + MF + C)))
                partes = [((x_c0, y), (x_c1, g0)), ((xa0, g0), (xa1, g1)), ((x_c0, g1), (x_c1, y + comp - 0.02))]
            else:
                partes = [((x_c0, y), (x_c1, y + comp - 0.02))]
            for j, ((ax0, ay0), (ax1, ay1)) in enumerate(partes):
                if ay1 - ay0 > 0.05:
                    G.caixa(f"{nome}_calc{s}_{k}_{j}", (ax0, ay0, -0.05), (ax1, ay1, H_CALC + dz), mat, col)
            if rng.random() < p.get("piso_tatil", 0.4):   # piso tátil direcional (só em alguns lotes, como na vida real)
                xt = s * (Lp / 2 + MF + C * 0.55)
                G.caixa(f"{nome}_tatil{s}_{k}", (xt - 0.125, y + 0.05, H_CALC + dz), (xt + 0.125, y + comp - 0.07, H_CALC + dz + 0.006), m["tatil"], col)
            if rng.random() < p.get("canteiros", 0.5) and comp > 5:   # canteiro elevado junto ao meio-fio
                yc_ = y + rng.uniform(1.5, comp - 2.0); xc_ = s * (Lp / 2 + MF + 0.65)
                for (bx0, by0, bx1, by1) in ((-0.5, -0.5, 0.5, -0.43), (-0.5, 0.43, 0.5, 0.5), (-0.5, -0.43, -0.43, 0.43), (0.43, -0.43, 0.5, 0.43)):
                    G.caixa(f"{nome}_cant{s}_{k}_{bx0}{by0}", (xc_ + bx0, yc_ + by0, H_CALC), (xc_ + bx1, yc_ + by1, H_CALC + 0.08), m["meiofio"], col, chanfro=0.01)
                G.caixa(f"{nome}_terra{s}_{k}", (xc_ - 0.43, yc_ - 0.43, H_CALC), (xc_ + 0.43, yc_ + 0.43, H_CALC + 0.06), m["terra"], col)
            y += comp; k += 1
        # meio-fio em segmentos (rebaixado nas garagens)
        cortes = sorted(rebaixos); ya = y0
        for i, (g0, g1) in enumerate(cortes + [(y1, y1)]):
            if g0 - ya > 0.05:
                G.caixa(f"{nome}_meiofio{s}_{i}", (x_mf0, ya, -0.05), (x_mf1, g0, H_CALC), m["meiofio"], col, chanfro=0.02)
            if g1 > g0:
                G.caixa(f"{nome}_meiofio_reb{s}_{i}", (x_mf0, g0, -0.05), (x_mf1, g1, 0.03), m["meiofio"], col, chanfro=0.01)
            ya = g1
        # bocas de lobo (abertura no meio-fio + grelha na sarjeta)
        yb = y0 + rng.uniform(4, 10)
        while yb < y1 - 3:
            if not any(g0 - 1 < yb < g1 + 1 for g0, g1 in rebaixos):
                xf = s * Lp / 2
                xa, xb = sorted((xf, xf + s * 0.04))
                G.caixa(f"{nome}_boca{s}_{int(yb)}", (xa, yb, 0.02), (xb, yb + 1.0, 0.11), m["escuro"], col)
                xg0, xg1 = sorted((s * (Lp / 2 - 0.05), s * (Lp / 2 - SARJ + 0.02)))
                G.caixa(f"{nome}_grelha_fundo{s}_{int(yb)}", (xg0, yb, -0.02), (xg1, yb + 1.0, 0.0), m["escuro"], col)
                for b in range(7):
                    G.caixa(f"{nome}_grelha{s}_{int(yb)}_{b}", (xg0, yb + 0.04 + b * 0.14, 0.0), (xg1, yb + 0.1 + b * 0.14, 0.006), m["ferro"], col)
            yb += rng.uniform(18, 28)
        # folhas secas e mato nas juntas — apoiados na superfície real (pista, meio-fio rebaixado ou rampa da garagem)
        def z_sup(xf, yf):
            d = abs(xf) - Lp / 2
            if d < 0:
                return 0.0
            if any(g0 <= yf <= g1 for g0, g1 in rebaixos):
                if d < MF:
                    return 0.03
                if d < MF + 0.6:
                    return 0.03 + (H_CALC - 0.03) * (d - MF) / 0.6
            return H_CALC
        for i in range(p.get("folhas", 50)):
            xf = s * (Lp / 2 + rng.uniform(-0.25, MF + C * 0.8)); yf = rng.uniform(y0, y1)
            zf = z_sup(xf, yf) + (0.005 if abs(xf) < Lp / 2 else 0.002)
            o = G.caixa(f"{nome}_folha{s}_{i}", (-0.04, -0.025, 0.0), (0.04, 0.025, 0.002), rng.choice([m["folha"], m["folha2"]]), col)
            o.location = (xf, yf, zf); o.rotation_euler = (0, 0, rng.uniform(0, 6.28))   # gira em torno do próprio centro
        for i in range(p.get("mato", 10)):
            yf = rng.uniform(y0, y1); xf = s * (Lp / 2 + MF + rng.uniform(0.0, 0.05))
            o = G.esfera(f"{nome}_mato{s}_{i}", (0, 0, 0), rng.uniform(0.04, 0.09), m["mato"], col, sub=2)
            o.location = (xf, yf, z_sup(xf, yf) + 0.01); o.scale = (1.0, 1.0, rng.uniform(0.5, 1.1))


# ------------------------------------------------------------------ cruzamento
def _esquina(nome, sx, sy, Lp, yc, Wc, C, R, Lx, Ly, mat_calc, m, col):
    """Quadra de esquina: meio-fio em L com canto arredondado (raio R) + calçada sobre ele."""
    A = MF + C

    def poly(off, raio):
        pts = [(raio + off * 0, off), (Lx, off), (Lx, A), (A, A), (A, Ly), (off, Ly), (off, raio)]
        cx = cy = R
        arco = [(cx + raio * math.cos(math.radians(a)), cy + raio * math.sin(math.radians(a))) for a in range(190, 271, 10)][:-1]
        pts = [(R, off)] + pts[1:7] + arco
        out = [(Lp / 2 + u if sx > 0 else -Lp / 2 - u, yc + Wc / 2 + v if sy > 0 else yc - Wc / 2 - v) for u, v in pts]
        return out if sx * sy > 0 else list(reversed(out))
    G.prisma(nome + "_meiofio", poly(0.0, R), -0.05, H_CALC, m["meiofio"], col)
    G.prisma(nome + "_calcada", poly(MF, R - MF), H_CALC - 0.02, H_CALC + 0.004, mat_calc, col)


@componente("cruzamento")
def cruzamento(ctx, p, rng, col):
    yc = p["yc"]; Lp = p.get("largura_pista", 7.0); Wc = p.get("largura_transversal", 7.0); C = p.get("largura_calcada", 3.2)
    X = p.get("braco", 22.0); R = p.get("raio_esquina", 2.2); Ly = p.get("comp_esquina", 6.0); um = p.get("umidade", 0.0)
    m = _mats(um); nome = p.get("nome", "cruz")
    asf = M.asfalto(desgaste=0.6, umidade=um, detalhe=p.get("detalhe_asfalto", 1.0))
    G.caixa(nome + "_centro", (-Lp / 2, yc - Wc / 2, -0.05), (Lp / 2, yc + Wc / 2, 0.0), asf, col)
    for sx in (-1, 1):
        xa, xb = sorted((sx * Lp / 2, sx * X))
        G.caixa(f"{nome}_braco{sx}", (xa, yc - Wc / 2 + SARJ, -0.05), (xb, yc + Wc / 2 - SARJ, 0.0), asf, col)
        for sy in (-1, 1):
            ya, yb = sorted((yc + sy * (Wc / 2 - SARJ), yc + sy * Wc / 2))
            G.caixa(f"{nome}_sarj{sx}{sy}", (xa + (R if sx > 0 else 0), ya, -0.05), (xb - (0 if sx > 0 else R), yb, 0.004), m["sarjeta"], col)
            # rua principal ao lado da quadra de esquina (os trechos começam depois de 'comp_esquina')
            ya2, yb2 = sorted((yc + sy * Wc / 2, yc + sy * (Wc / 2 + Ly)))
            xs0, xs1 = sorted((sx * (Lp / 2 - SARJ), sx * Lp / 2))
            G.caixa(f"{nome}_sarjp{sx}{sy}", (xs0, ya2 + (R if sy > 0 else 0), -0.05), (xs1, yb2 - (0 if sy > 0 else R), 0.004), m["sarjeta"], col)
            xp0, xp1 = sorted((0.0, sx * (Lp / 2 - SARJ)))
            G.caixa(f"{nome}_pistap{sx}{sy}", (xp0, ya2, -0.05), (xp1, yb2, 0.0), asf, col)
            mat = _calcada_mat(rng.choice(p.get("calcadas", ["calcada_portuguesa", "concreto"])), um, rng)
            _esquina(f"{nome}_esq{sx}{sy}", sx, sy, Lp, yc, Wc, C, R, X - Lp / 2, Ly, mat, m, col)
            # piso de alerta (amarelo) na calçada, na ponta da faixa de pedestre da rua principal
            xa0, xa1 = sorted((sx * (Lp / 2 + MF + 0.05), sx * (Lp / 2 + MF + 0.65)))
            ym = yc + sy * (Wc / 2 + 2.5)
            G.caixa(f"{nome}_alerta{sx}{sy}", (xa0, ym - 0.6, H_CALC + 0.004), (xa1, ym + 0.6, H_CALC + 0.012), m["tatil"], col)
    # faixas de pedestre (zebra) nos 4 lados + linhas de retenção
    for sy in (-1, 1):   # atravessando a rua principal
        ya, yb = sorted((yc + sy * (Wc / 2 + 1.0), yc + sy * (Wc / 2 + 4.0)))
        x = -Lp / 2 + SARJ + 0.2; i = 0
        while x + 0.4 <= Lp / 2 - SARJ - 0.2:
            G.caixa(f"{nome}_zebra_p{sy}_{i}", (x, ya, 0.0), (x + 0.4, yb, 0.004), m["tinta_b"], col); x += 0.9; i += 1
        yr = yc + sy * (Wc / 2 + 5.0)
        xr0, xr1 = sorted((0.0, -sy * (Lp / 2 - SARJ)))
        G.caixa(f"{nome}_retencao_p{sy}", (xr0, min(yr, yr + sy * 0.4), 0.0), (xr1, max(yr, yr + sy * 0.4), 0.004), m["tinta_b"], col)
    for sx in (-1, 1):   # atravessando a rua transversal
        xa, xb = sorted((sx * (Lp / 2 + 1.0), sx * (Lp / 2 + 4.0)))
        y = yc - Wc / 2 + SARJ + 0.2; i = 0
        while y + 0.4 <= yc + Wc / 2 - SARJ - 0.2:
            G.caixa(f"{nome}_zebra_t{sx}_{i}", (xa, y, 0.0), (xb, y + 0.4, 0.004), m["tinta_b"], col); y += 0.9; i += 1
    # eixo da transversal (tracejado)
    for sx in (-1, 1):
        x = sx * (Lp / 2 + 6.0)
        while abs(x) < X - 2:
            xa, xb = sorted((x, x + sx * 3.0))
            G.caixa(f"{nome}_eixo_t{int(x)}", (xa, yc - 0.06, 0.0), (xb, yc + 0.06, 0.004), m["tinta_b"], col); x += sx * 7.0


# ------------------------------------------------------------------ postes e fiação
@componente("poste_concreto")
def poste_concreto(ctx, p, rng, col):
    x, y = p["x"], p["y"]; alt = p.get("altura", 9.5); lado = p.get("lado", 1); linha = p.get("linha", "a")
    concreto = M.concreto("#a49e92", placa_m=(1.0, 0.7), desgaste=0.6, sujeira=0.5)
    bm_pts = []
    import bmesh
    bm = bmesh.new()
    for (z, a, b) in ((H_CALC, 0.15, 0.10), (alt, 0.08, 0.06)):
        for (u, v) in ((-a, -b), (a, -b), (a, b), (-a, b)):
            bm_pts.append(bm.verts.new((x + u, y + v, z)))
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    for idx in f:
        bm.faces.new([bm_pts[i] for i in idx])
    corpo = G._chanfro(G._obj(f"poste_{linha}_{x}_{y}", bm, concreto, col), 0.015)
    m = _mats(); metal = m["metal"]
    # cruzeta com isoladores (fios de energia ao longo de y)
    zc = alt - 0.35
    o = G.caixa(f"poste_cruzeta_{x}_{y}", (x - 0.85, y - 0.05, zc - 0.05), (x + 0.85, y + 0.05, zc + 0.05), concreto, col, chanfro=0.01); o["suspenso"] = True
    pontos = []
    for dx in (-0.7, 0.0, 0.7):
        iso = G.cilindro(f"poste_iso_{x}_{y}_{dx}", (x + dx, y, zc + 0.05), 0.035, 0.14, M.pintura("#d8dbd8", rug=0.2), col, lados=10); iso["suspenso"] = True
        pontos.append((x + dx, y, zc + 0.2))
    # cabos de telecom mais baixos
    for dz in (6.3, 6.0):
        pontos.append((x - lado * 0.12, y, dz))
    ctx.setdefault("fios", {}).setdefault(linha, []).append(pontos)
    # luminária LED em braço curvo
    if p.get("luminaria", True):
        z0 = alt - 1.6; pa = (x, y, z0); pb = (x + lado * 0.8, y, z0 + 0.45); pc = (x + lado * 1.8, y, z0 + 0.6)
        for i, (a, b) in enumerate(((pa, pb), (pb, pc))):
            br = G.cilindro_eixo(f"poste_braco_{x}_{y}_{i}", a, b, 0.035, metal, col); br["suspenso"] = True
        cx = pc[0] + lado * 0.25
        lum = G.caixa(f"poste_lum_{x}_{y}", (cx - 0.32, y - 0.15, pc[2] - 0.06), (cx + 0.32, y + 0.15, pc[2] + 0.06), metal, col, chanfro=0.03); lum["suspenso"] = True
        led = G.caixa(f"poste_led_{x}_{y}", (cx - 0.26, y - 0.11, pc[2] - 0.075), (cx + 0.26, y + 0.11, pc[2] - 0.06), M.emissor(p.get("cor_luz", "#fff1dc"), 14.0), col)
        led["suspenso"] = True; led.lightgroup = "artificial"
        L.luz_ponto(f"poste_luz_{x}_{y}", (cx, y, pc[2] - 0.15), p.get("watts", 700), p.get("cor_luz", "#fff1dc"), "artificial",
                    raio=0.2, tipo="SPOT", alvo=(cx, y, 0), angulo=125)
    if p.get("transformador", False):
        tr = G.cilindro(f"poste_trafo_{x}_{y}", (x - lado * 0.45, y, 7.0), 0.33, 1.1, M.pintura("#7d8a83", rug=0.5, metal=0.3, desgaste=0.4), col, lados=18)
        tr["suspenso"] = True
        sup = G.caixa(f"poste_trafo_sup_{x}_{y}", (x - lado * 0.45 - 0.05, y - 0.05, 6.9), (x, y + 0.05, 7.0), metal, col); sup["suspenso"] = True
    if p.get("numero", True):   # placa de identificação do poste: só números (nada de marca)
        G.texto(f"poste_num_{x}_{y}", str(p.get("id", rng.randint(100, 999))), (x + lado * 0.137, y, 2.6), 0.09,
                M.pintura("#1b1b1b"), col, rot=(math.radians(90), 0, math.radians(90 * lado)))   # na face voltada para a rua
    return corpo


@componente("fiacao")
def fiacao(ctx, p, rng, col):
    """Cabos entre postes consecutivos da mesma linha. Energia: finos e tensos; telecom: mais grossos e mais caídos,
    com sobras enroladas em alguns postes (a 'cara' da fiação dos bairros)."""
    preto = M.pintura("#121214", rug=0.6)
    for linha, postes in ctx.get("fios", {}).items():
        for i, (a, b) in enumerate(zip(postes, postes[1:])):
            for k, (pa, pb) in enumerate(zip(a, b)):
                telecom = k >= 3
                G.catenaria(f"fio_{linha}_{i}_{k}", pa, pb, rng.uniform(0.35, 0.7) if telecom else rng.uniform(0.18, 0.32),
                            0.012 if telecom else 0.007, preto, col)
            if rng.random() < p.get("sobras", 0.5):
                c = a[3]; bpy.ops.mesh.primitive_torus_add(major_radius=0.28, minor_radius=0.025, location=(c[0], c[1] + 0.3, c[2] - 0.3))
                o = bpy.context.active_object; o.name = f"fio_sobra_{linha}_{i}"; o.data.materials.append(preto); o["suspenso"] = True
                o.rotation_euler = (math.radians(90), 0, 0)
                for cc in o.users_collection:
                    cc.objects.unlink(o)
                col.objects.link(o)


# ------------------------------------------------------------------ sinalização vertical e mobiliário
@componente("semaforo")
def semaforo(ctx, p, rng, col):
    x, y = p["x"], p["y"]; rot = math.radians(p.get("rot_graus", 0.0)); estado = p.get("estado", "verde")
    metal = M.pintura("#2d3035", rug=0.45, metal=0.5, desgaste=0.35); objs = []
    objs.append(G.cilindro(f"sem_poste_{x}_{y}", (0, 0, H_CALC), 0.07, 3.3, metal, col))
    caixa = G.caixa(f"sem_caixa_{x}_{y}", (-0.16, -0.14, 2.55), (0.16, 0.12, 3.45), metal, col, chanfro=0.02); caixa["suspenso"] = True; objs.append(caixa)
    cores = {"vermelho": "#ff3b2f", "amarelo": "#ffb21f", "verde": "#2fe07a"}
    for i, (nome_c, z) in enumerate((("vermelho", 3.28), ("amarelo", 3.0), ("verde", 2.72))):
        aceso = nome_c == estado
        mat = M.emissor(cores[nome_c], 9.0) if aceso else M.pintura("#1d2022", rug=0.25)
        lente = G.cilindro(f"sem_lente_{nome_c}_{x}_{y}", (0, 0, 0), 0.095, 0.03, mat, col, lados=20)
        lente.rotation_euler = (math.radians(90), 0, 0); lente.location = (0, -0.155, z); lente["suspenso"] = True; objs.append(lente)
        if aceso:
            lente.lightgroup = "artificial"
        visor = G.caixa(f"sem_visor_{nome_c}_{x}_{y}", (-0.12, -0.3, z + 0.08), (0.12, -0.14, z + 0.11), metal, col); visor["suspenso"] = True; objs.append(visor)
    ped = G.caixa(f"sem_ped_{x}_{y}", (-0.13, -0.11, 2.0), (0.13, 0.11, 2.4), metal, col, chanfro=0.015); ped["suspenso"] = True; objs.append(ped)
    figura = G.caixa(f"sem_ped_luz_{x}_{y}", (-0.07, -0.115, 2.12), (0.07, -0.11, 2.3), M.emissor("#ff5a3c" if estado == "verde" else "#3cf08a", 5.0), col)
    figura["suspenso"] = True; figura.lightgroup = "artificial"; objs.append(figura)
    _grupo(f"semaforo_{x}_{y}", objs, (x, y, 0), rot, col)


@componente("placa_rua")
def placa_rua(ctx, p, rng, col):
    """Placa de nome de rua (azul, letras brancas). Os nomes vêm da receita e devem ser INVENTADOS."""
    x, y = p["x"], p["y"]; nomes = p["nomes"]; metal = M.pintura("#3b3f45", rug=0.4, metal=0.5)
    azul = M.pintura("#1d4f9c", rug=0.5, desgaste=0.25); branco = M.pintura("#f4f2ec", rug=0.5)
    G.cilindro(f"placa_rua_poste_{x}_{y}", (x, y, H_CALC), 0.04, 2.9, metal, col)
    for i, (nome, ang) in enumerate(zip(nomes, (0.0, 90.0))):
        z = 2.75 - i * 0.3; a = math.radians(ang)
        d = Vector((math.cos(a), math.sin(a), 0)); n = Vector((-math.sin(a), math.cos(a), 0))
        c = Vector((x, y, z)) + d * 0.42
        pl = G.caixa(f"placa_rua_{i}_{x}_{y}", (-0.42, -0.012, -0.11), (0.42, 0.012, 0.11), azul, col, chanfro=0.008)
        pl.location = c; pl.rotation_euler = (0, 0, a); pl["suspenso"] = True
        for lado in (1, -1):
            G.texto(f"placa_rua_txt_{i}_{lado}_{x}_{y}", nome, tuple(c + n * 0.014 * lado * -1), 0.105, branco, col,
                    rot=(math.radians(90), 0, a + (0 if lado > 0 else math.pi)))


@componente("placa_regulamentacao")
def placa_regulamentacao(ctx, p, rng, col):
    """Placas sem marca: 'velocidade' (círculo branco, borda vermelha, número) e 'proibido_estacionar' (azul, borda e
    tarja vermelhas). Voltadas para 'rot_graus' (0 = face para −y, para quem vem de −y)."""
    x, y = p["x"], p["y"]; rot = math.radians(p.get("rot_graus", 0.0)); tipo = p.get("tipo", "velocidade")
    metal = M.pintura("#3b3f45", rug=0.4, metal=0.5); objs = [G.cilindro(f"reg_poste_{x}_{y}", (0, 0, H_CALC), 0.035, 2.35, metal, col)]
    vermelho = M.pintura("#c8231f", rug=0.5); fundo = M.pintura("#f4f2ec" if tipo == "velocidade" else "#1d4f9c", rug=0.5)
    anel = G.cilindro(f"reg_anel_{x}_{y}", (0, 0, 0), 0.32, 0.015, vermelho, col, lados=40); anel.rotation_euler = (math.radians(90), 0, 0); anel.location = (0, -0.04, 2.25)
    disco = G.cilindro(f"reg_disco_{x}_{y}", (0, 0, 0), 0.25, 0.017, fundo, col, lados=40); disco.rotation_euler = (math.radians(90), 0, 0); disco.location = (0, -0.042, 2.25)
    for o in (anel, disco):
        o["suspenso"] = True; objs.append(o)
    if tipo == "velocidade":
        t = G.texto(f"reg_txt_{x}_{y}", str(p.get("limite", 30)), (0, -0.062, 2.25), 0.26, M.pintura("#141414"), col, rot=(math.radians(90), 0, 0))
        objs.append(t)
    else:
        tarja = G.caixa(f"reg_tarja_{x}_{y}", (-0.24, -0.008, -0.03), (0.24, 0.008, 0.03), vermelho, col)
        tarja.location = (0, -0.058, 2.25); tarja.rotation_euler = (0, math.radians(45), 0); tarja["suspenso"] = True; objs.append(tarja)
    _grupo(f"placa_reg_{x}_{y}", objs, (x, y, 0), rot, col)


@componente("hidrante")
def hidrante(ctx, p, rng, col):
    x, y = p["x"], p["y"]; verm = M.pintura("#b3261e", rug=0.45, desgaste=0.5)
    G.cilindro(f"hid_corpo_{x}_{y}", (x, y, H_CALC), 0.11, 0.55, verm, col, lados=20, chanfro=0.01)
    G.esfera(f"hid_topo_{x}_{y}", (x, y, H_CALC + 0.55), 0.115, verm, col)
    for s in (-1, 1):
        G.cilindro_eixo(f"hid_bico_{s}_{x}_{y}", (x, y, H_CALC + 0.38), (x + s * 0.18, y, H_CALC + 0.38), 0.045, M.pintura("#d9b23a", rug=0.4), col)["suspenso"] = True


@componente("lixeira_poste")
def lixeira_poste(ctx, p, rng, col):
    x, y = p["x"], p["y"]; lar = M.pintura(p.get("cor", "#e2701f"), rug=0.5, desgaste=0.45)
    G.cilindro(f"lix_poste_{x}_{y}", (x, y, H_CALC), 0.03, 1.1, M.pintura("#3b3f45", rug=0.4, metal=0.5), col)
    c = G.cilindro(f"lix_cesto_{x}_{y}", (x + 0.2, y, H_CALC + 0.55), 0.18, 0.5, lar, col, lados=20, raio_topo=0.2)
    c["suspenso"] = True
