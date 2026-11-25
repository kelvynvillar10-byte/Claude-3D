"""Cenografia — kit de PRÉDIOS (E3): fachadas de bairro brasileiro por gramática, em 3 estilos.

Estilos
- residencial  prédio baixo (3–6 andares): portaria com marquise, garagem, rodapé de pastilha/pedra, janelas com
               moldura e peitoril, varandas (grade ou mureta) com varal, ar-condicionado, janelinhas de banheiro,
               cinta entre andares, platibanda, torre da caixa d'água e antenas.
- comercial    térreo de lojas (1–2 por prédio) + 0–2 andares: loja aberta (interior aceso com prateleiras, produtos,
               balcão e luz que derrama na calçada) ou fechada (porta de enrolar), toldo listrado, letreiro com nome
               GENÉRICO (só palavras comuns, nunca marca), placa "ALUGA-SE" em janelas vazias.
- sobrado      casa de 2 pavimentos recuada atrás do muro: portão de garagem, portão social com grade, arandela,
               número, piso da garagem, janelas com grade, telhado cerâmico de duas águas.

Componentes registrados
- fachada_quadra   divide uma frente de quadra em lotes por semente e escolhe estilo, largura, altura e cor de cada
                   um; o lote da esquina ganha fachada também na lateral.
- predio_residencial, predio_comercial, sobrado   um lote isolado (para folhas e cenas montadas à mão).

Convenção local: a fachada fica no plano x = 0 voltada para −x (a rua); o prédio ocupa x de 0 a D e y de 0 a L.
O lote é posicionado no mundo por um objeto-raiz (rotação 0° ou 180°). Cada FACE (frente ou lateral) tem a sua
raiz, e tudo nela é construído em coordenadas da face: x ≤ 0 para fora, y ao longo da fachada, z para cima.
Peças repetidas (molduras, folhas de janela, grades, ar-condicionado, lajes de varanda) são INSTÂNCIAS da mesma
malha, com material por objeto: pouca memória, render mais rápido.
"""
import math
import bpy, bmesh
from mathutils import Vector
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M, luz as LZ

Z0 = 0.15            # altura da calçada (os vãos do térreo começam aqui)
H_ANDAR = 2.9
NOMES_LOJA = ["PADARIA", "MERCADINHO", "BAZAR", "PAPELARIA", "LANCHONETE", "FARMÁCIA", "SALÃO", "AÇOUGUE",
              "HORTIFRUTI", "SAPATARIA", "ÓTICA", "CHAVEIRO"]     # palavras comuns, sem marca
TEXTOS_KIT = NOMES_LOJA + ["ALUGA-SE"]                                  # + números de casa (só algarismos)
CORTINAS = ["#c9b79a", "#8fa7b8", "#d9cfc0", "#b98c7a", "#a7b98c", "#e0d6c2", "#9b8fb8"]
ROUPAS = ["#d9443a", "#3a78c2", "#f0d29a", "#4fae9c", "#ffffff", "#e8806c", "#2b2e33", "#9278c4"]


# ------------------------------------------------------------------ infraestrutura: raízes, instâncias
def _raiz(nome, col, loc, rot_z, pai=None):
    e = bpy.data.objects.new(nome, None); col.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rot_z)
    e.parent = pai
    return e


def _malha(chave, caixas):
    """Malha-protótipo (compartilhada) feita de caixas [(c0, c1), …]. Fica em bpy.data: cada montagem recria."""
    nome = "proto_" + chave
    me = bpy.data.meshes.get(nome)
    if me is not None:
        return me
    bm = bmesh.new()
    for c0, c1 in caixas:
        r = bmesh.ops.create_cube(bm, size=1.0)
        d = [b - a for a, b in zip(c0, c1)]; c = [(a + b) / 2 for a, b in zip(c0, c1)]
        for v in r["verts"]:
            v.co = Vector((c[0] + v.co.x * d[0], c[1] + v.co.y * d[1], c[2] + v.co.z * d[2]))
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free(); me.materials.append(None)
    return me


def _inst(nome, me, loc, mat, col, lightgroup=None):
    o = bpy.data.objects.new(nome, me); col.objects.link(o); o.location = loc
    o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = mat; o["suspenso"] = True
    if lightgroup:
        o.lightgroup = lightgroup
    return o


def _laje_inclinada(nome, x_a, z_a, x_b, z_b, y0, y1, esp, mat, col):
    """Placa inclinada (toldo, água de telhado): borda A em (x_a, z_a), borda B em (x_b, z_b), de y0 a y1."""
    bm = bmesh.new(); vs = []
    for (x, z) in ((x_a, z_a), (x_b, z_b)):
        for y in (y0, y1):
            vs.append(bm.verts.new((x, y, z))); vs.append(bm.verts.new((x, y, z - esp)))
    # índices: A-y0-cima 0, A-y0-baixo 1, A-y1-cima 2, A-y1-baixo 3, B-y0-cima 4, B-y0-baixo 5, B-y1-cima 6, B-y1-baixo 7
    for f in ((0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (0, 1, 3, 2), (4, 6, 7, 5)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nome, me); o.data.materials.append(mat); col.objects.link(o); o["suspenso"] = True
    return o


def _tinta_real(h, k=0.25, base="#d8cfc0"):
    """Puxa a cor da paleta 25 % para um cinza quente: parede grande pintada com a cor pura satura demais ao sol."""
    a = [int(h[i:i + 2], 16) for i in (1, 3, 5)]; c = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - k) + y * k):02x}" for x, y in zip(a, c))


def _mat_fachada(spec, rng):
    if isinstance(spec, dict):
        s = dict(spec); return M.por_nome(s.pop("nome"), **s)
    cor = spec or _tinta_real(rng.choice(list(M.PALETA_BAIRRO.values())))
    return M.reboco(cor, desgaste=rng.uniform(0.3, 0.6), detalhe=1.0)


# ------------------------------------------------------------------ peças de fachada (coordenadas da face)
class Face:
    """Constrói elementos numa face (plano x = 0, voltada para −x). Usa instâncias para o que se repete."""
    def __init__(self, nome, col, rng, mats):
        self.nome, self.col, self.rng, self.m = nome, col, rng, mats; self.n = 0

    def _id(self, t):
        self.n += 1; return f"{self.nome}_{t}{self.n}"

    def janela(self, y, z, w, h, peitoril=True, grade=False, acesa=None, folhas=None, aluga=False, x=0.0):
        """Janela com moldura (saliente), 2 folhas (vidro, cortina ou acesa), peitoril e grade opcional."""
        r = self.rng; m = self.m; e = 0.07
        cx = [((-0.05, -w / 2 - e, -e), (0.0, -w / 2, h + e)), ((-0.05, w / 2, -e), (0.0, w / 2 + e, h + e)),
              ((-0.05, -w / 2, h), (0.0, w / 2, h + e)), ((-0.05, -w / 2, -e), (0.0, w / 2, 0.0)),
              ((-0.045, -0.02, 0.0), (0.0, 0.02, h))]
        if peitoril:
            cx.append(((-0.13, -w / 2 - 0.12, -e - 0.06), (0.0, w / 2 + 0.12, -e)))
        _inst(self._id("mol"), _malha(f"mol_{w:.2f}_{h:.2f}_{int(peitoril)}", cx), (x, y, z), m["moldura"], self.col)
        folha = _malha(f"folha_{w:.2f}_{h:.2f}", [((-0.028, 0.0, 0.0), (-0.018, w / 2 - 0.02, h))])
        acesa = (r.random() < m["p_acesa"]) if acesa is None else acesa
        for lado, y_f in ((0, y - w / 2), (1, y + 0.02)):
            if acesa:
                mt, lg = m["acesa"], "artificial"
            else:
                k = r.random(); lg = None
                mt = m["vidro"] if k < 0.45 else (M.pintura(r.choice(CORTINAS), rug=0.85) if k < 0.85 else m["persiana"])
            if folhas is not None:
                mt, lg = folhas[lado], None
            _inst(self._id("folha"), folha, (x, y_f, z), mt, self.col, lg)
        if grade:
            nb = max(2, int(w / 0.13)); barras = [((-0.08, -w / 2 + i * w / nb - 0.008, 0.0), (-0.065, -w / 2 + i * w / nb + 0.008, h)) for i in range(1, nb)]
            barras += [((-0.08, -w / 2, zz - 0.012), (-0.065, w / 2, zz + 0.012)) for zz in (0.05, h / 2, h - 0.05)]
            _inst(self._id("grade"), _malha(f"grade_{w:.2f}_{h:.2f}", barras), (x, y, z), m["ferro"], self.col)
        if aluga:   # placa ALUGA-SE presa na janela
            G.caixa(self._id("aluga"), (-0.035, y - 0.32, z + h * 0.45), (-0.03, y + 0.32, z + h * 0.45 + 0.3), M.pintura("#f2d03a", rug=0.6), self.col)["suspenso"] = True
            G.texto(self._id("aluga_t"), "ALUGA-SE", (-0.038, y, z + h * 0.45 + 0.15), 0.12, M.pintura("#c8231f", rug=0.5), self.col,
                    rot=(math.radians(90), 0, math.radians(-90)))

    def ar_condicionado(self, y, z):
        _inst(self._id("ac"), _malha("ac", [((-0.3, -0.4, 0.0), (0.0, 0.4, 0.55)), ((-0.34, -0.3, -0.05), (0.0, -0.26, 0.0)),
                                             ((-0.34, 0.26, -0.05), (0.0, 0.3, 0.0))]), (0, y, z), self.m["ac"], self.col)
        _inst(self._id("acg"), _malha("ac_grade", [((-0.305, -0.36, 0.06), (-0.3, 0.12, 0.49))]), (0, y, z), self.m["escuro"], self.col)

    def varanda(self, y, z_piso, larg, prof=1.0, guarda="grade", varal=False):
        """Laje em balanço + guarda-corpo (grade de ferro ou mureta) + varal opcional com roupas."""
        m = self.m
        _inst(self._id("laje"), _malha(f"laje_{larg:.2f}_{prof:.2f}", [((-prof, -larg / 2, -0.14), (0.0, larg / 2, 0.0))]),
              (0, y, z_piso), m["laje"], self.col)
        if guarda == "grade":
            nb = max(3, int((larg + 2 * prof) / 0.12))
            bar = [((-prof, -larg / 2, 0.98), (-prof + 0.04, larg / 2, 1.02)), ((-prof, -larg / 2, 0.98), (0.0, -larg / 2 + 0.04, 1.02)),
                   ((-prof, larg / 2 - 0.04, 0.98), (0.0, larg / 2, 1.02))]
            for i in range(int(larg / 0.12)):
                yy = -larg / 2 + 0.06 + i * 0.12; bar.append(((-prof + 0.01, yy - 0.008, 0.0), (-prof + 0.026, yy + 0.008, 0.98)))
            for s in (-1, 1):
                yb = s * (larg / 2 - 0.02)
                for i in range(int(prof / 0.12)):
                    xx = -prof + 0.12 + i * 0.12; bar.append(((xx - 0.008, yb - 0.008, 0.0), (xx + 0.008, yb + 0.008, 0.98)))
            _inst(self._id("gc"), _malha(f"gc_{larg:.2f}_{prof:.2f}", bar), (0, y, z_piso), m["ferro"], self.col)
        else:
            mur = [((-prof, -larg / 2, 0.0), (-prof + 0.1, larg / 2, 1.0)), ((-prof, -larg / 2, 0.0), (0.0, -larg / 2 + 0.1, 1.0)),
                   ((-prof, larg / 2 - 0.1, 0.0), (0.0, larg / 2, 1.0))]
            _inst(self._id("mur"), _malha(f"mur_{larg:.2f}_{prof:.2f}", mur), (0, y, z_piso), m["mureta"], self.col)
        if varal:
            r = self.rng; zv = z_piso + 1.9; xv = -prof * 0.55
            G.cilindro_eixo(self._id("varal"), (xv, y - larg / 2 + 0.15, zv), (xv, y + larg / 2 - 0.15, zv), 0.004, m["ferro"], self.col)["suspenso"] = True
            yy = y - larg / 2 + 0.3
            while yy < y + larg / 2 - 0.5:
                lw, lh = r.uniform(0.28, 0.5), r.uniform(0.35, 0.75)
                o = G.caixa(self._id("roupa"), (xv - 0.006, yy, zv - lh), (xv + 0.006, yy + lw, zv), M.pintura(r.choice(ROUPAS), rug=0.9), self.col)
                o["suspenso"] = True; yy += lw + r.uniform(0.05, 0.25)

    def faixa(self, y0, y1, z0, z1, mat, salto=0.04, t="faixa"):
        """Faixa horizontal colada na fachada (rodapé, cinta entre andares, platibanda, viga)."""
        G.caixa(self._id(t), (-salto, y0, z0), (0.0, y1, z1), mat, self.col, chanfro=0.01)["suspenso"] = True

    def texto(self, corpo, y, z, tam, mat, x=-0.02):
        G.texto(self._id("txt"), corpo, (x, y, z), tam, mat, self.col, rot=(math.radians(90), 0, math.radians(-90)))


def _mats(rng, p):
    return {"moldura": M.pintura(p.get("cor_moldura") or rng.choice(["#f3eee4", "#e9e2d2", "#d8d2c4", "#ffffff"]), rug=0.6),
            "vidro": M.vidro(), "acesa": M.emissor(rng.choice(["#ffd9a0", "#ffe6c0", "#fff1d6"]), 2.2),
            "persiana": M.chapa_ondulada("#d9d4c8", passo_m=0.03, desgaste=0.2, metal=0.0),
            "ferro": M.pintura(rng.choice(["#2b2e33", "#3d4148", "#f0ece2", "#2f5d62"]), rug=0.45, metal=0.5, desgaste=0.35),
            "ac": M.pintura("#e6e4dc", rug=0.5, desgaste=0.4), "escuro": M.pintura("#3a3d42", rug=0.6),
            "laje": M.reboco("#e9e2d2", desgaste=0.5, detalhe=1.0), "mureta": M.reboco(_tinta_real(rng.choice(list(M.PALETA_BAIRRO.values()))), desgaste=0.4, detalhe=1.0),
            "p_acesa": p.get("acesas", 0.15)}


def _topo(nome, col, rng, L, D, H, platibanda_mat, caixa=True, antenas=True, torre=False):
    """Platibanda em volta do terraço + caixa d'água (fibra azul ou concreto) + antenas. Coordenadas do lote."""
    pl = 0.9
    for c0, c1 in (((-0.06, -0.06, H), (0.16, L + 0.06, H + pl)), ((D - 0.16, -0.06, H), (D + 0.06, L + 0.06, H + pl)),
                   ((-0.06, -0.06, H), (D + 0.06, 0.16, H + pl)), ((-0.06, L - 0.16, H), (D + 0.06, L + 0.06, H + pl))):
        G.caixa(f"{nome}_plat{c0[0]:.1f}{c0[1]:.1f}{c1[1]:.1f}", c0, c1, platibanda_mat, col, chanfro=0.015)["suspenso"] = True
    G.caixa(f"{nome}_rufo", (-0.12, -0.1, H + pl), (0.22, L + 0.1, H + pl + 0.06), M.concreto("#c9c2b4", placa_m=(1.0, 0.3)), col)["suspenso"] = True
    zb = H
    if caixa:
        xc, yc = rng.uniform(D * 0.45, D * 0.7), rng.uniform(L * 0.25, L * 0.75)
        if torre:   # torre da escada/caixa d'água acima do terraço
            G.caixa(f"{nome}_torre", (xc - 1.4, yc - 1.4, H), (xc + 1.4, yc + 1.4, H + 2.4), platibanda_mat, col, chanfro=0.02)
            zb = H + 2.4
        if rng.random() < 0.6:
            G.cilindro(f"{nome}_cx", (xc, yc, zb), rng.uniform(0.6, 0.8), 1.0, M.pintura("#3a6fb0", rug=0.5, desgaste=0.4), col, raio_topo=0.55, lados=24)
            G.cilindro(f"{nome}_cxt", (xc, yc, zb + 1.0), 0.6, 0.1, M.pintura("#3a6fb0", rug=0.5), col, raio_topo=0.15, lados=24)["suspenso"] = True
        else:
            G.caixa(f"{nome}_cx", (xc - 0.9, yc - 0.9, zb), (xc + 0.9, yc + 0.9, zb + 1.3), M.concreto("#b8b0a2", placa_m=(1.0, 0.4), desgaste=0.7), col, chanfro=0.02)
    if antenas:
        for i in range(rng.randint(1, 3)):
            xa, ya = rng.uniform(1.0, D - 1.0), rng.uniform(1.0, L - 1.0); ha = rng.uniform(1.6, 3.2)
            haste = M.pintura("#8d9299", rug=0.4, metal=0.7)
            G.cilindro(f"{nome}_ant{i}", (xa, ya, H), 0.025, ha, haste, col, lados=8)
            if rng.random() < 0.5:   # parabólica
                d = G.esfera(f"{nome}_parab{i}", (0, 0, 0), 0.45, M.pintura("#d8d8d2", rug=0.5), col, sub=2)
                d.scale = (0.25, 1.0, 1.0); d.location = (xa - 0.15, ya, H + ha - 0.3); d.rotation_euler = (0, math.radians(-25), rng.uniform(0, 6.28)); d["suspenso"] = True
            else:                     # antena de TV (espinha de peixe)
                for k in range(5):
                    G.caixa(f"{nome}_yagi{i}_{k}", (xa - 0.6 + k * 0.28, ya - 0.3 + k * 0.04, H + ha - 0.1), (xa - 0.58 + k * 0.28, ya + 0.3 - k * 0.04, H + ha - 0.08), haste, col)["suspenso"] = True
                G.caixa(f"{nome}_yagib{i}", (xa - 0.62, ya - 0.012, H + ha - 0.11), (xa + 0.62, ya + 0.012, H + ha - 0.07), haste, col)["suspenso"] = True


def _faces_laterais(lateral, L, D):
    """Faces laterais com fachada (lote de esquina): 'inicio' = lado y = 0, 'fim' = lado y = L (coordenadas do lote)."""
    out = []
    if lateral in ("inicio", "ambos"):
        out.append(("lat0", (D, 0.0, 0.0), math.radians(90), D))
    if lateral in ("fim", "ambos"):
        out.append(("lat1", (0.0, L, 0.0), math.radians(-90), D))
    return out


def _grade_janelas(F, ext, z_andares, w=1.2, h=1.25, passo=3.0, ac=0.3, grade_terreo=False):
    """Janelas em grade numa face (laterais e andares de escritório)."""
    r = F.rng; n = max(1, int((ext - 1.0) / passo))
    for z in z_andares:
        for j in range(n):
            y = ext / 2 + (j - (n - 1) / 2) * passo
            F.janela(y, z + 0.95, w, h, grade=grade_terreo and z < 1.0)
            if r.random() < ac:
                F.ar_condicionado(y + w / 2 + 0.55, z + 1.0)


# ------------------------------------------------------------------ estilos
def residencial(nome, col, rng, L, D, p):
    """Prédio residencial baixo. Constrói em coordenadas do lote (laterais em coordenadas da face). Retorna a altura."""
    n_and = p.get("andares") or rng.randint(3, 6); H_t = 3.2; H = Z0 + H_t + n_and * H_ANDAR
    mat = _mat_fachada(p.get("mat"), rng); mats = _mats(rng, p); mat2 = _mat_fachada(p.get("mat2"), rng)
    G.caixa(f"{nome}_corpo", (0.0, 0.0, 0.0), (D, L, H), mat, col, chanfro=0.02)
    rodape = M.pastilha(rng.choice(["#6d7f8c", "#8c6d5a", "#4a6b5d", "#7a7a7a"])) if rng.random() < 0.6 else M.concreto("#8f897d", placa_m=(0.6, 0.4))
    F = Face(nome + "_f", col, rng, mats)
    # térreo: portaria central com marquise, garagem, janelas com grade, número, interfone
    F.faixa(0.0, L, 0.0, Z0 + 0.9, rodape, 0.03, "rodape")
    yp = L / 2 + rng.uniform(-L * 0.15, L * 0.15)
    F.janela(yp, Z0, 1.5, 2.35, peitoril=False, acesa=False, folhas=[mats["vidro"], mats["vidro"]])
    G.caixa(F._id("marq"), (-1.1, yp - 1.3, Z0 + 2.65), (0.0, yp + 1.3, Z0 + 2.8), mats["laje"], col, chanfro=0.02)["suspenso"] = True
    luz_m = G.caixa(F._id("marql"), (-0.7, yp - 0.15, Z0 + 2.63), (-0.4, yp + 0.15, Z0 + 2.65), M.emissor("#fff1d6", 6.0), col); luz_m.lightgroup = "artificial"; luz_m["suspenso"] = True
    num = str(rng.randint(100, 1999)); F.texto(num, yp, Z0 + 2.95, 0.22, mats["moldura"], x=-0.03)
    G.caixa(F._id("interf"), (-0.04, yp + 0.95, Z0 + 1.3), (0.0, yp + 1.12, Z0 + 1.55), mats["escuro"], col)["suspenso"] = True
    yg = 1.6 if yp > L / 2 else L - 1.6
    if L > 9:
        G.caixa(F._id("garagem"), (-0.05, yg - 1.35, Z0), (0.0, yg + 1.35, Z0 + 2.3), M.chapa_ondulada(rng.choice(["#8a9098", "#5c6b73", "#7d5f4a"])), col)["suspenso"] = True
    for yj in (yp - 2.6, yp + 2.6):
        if 0.9 < yj < L - 0.9 and abs(yj - yg) > 2.2:
            F.janela(yj, Z0 + 1.1, 1.0, 1.1, grade=True)
    # andares: padrão de vãos simétrico, repetido em todos os andares (como num prédio real)
    nv = max(2, int(L / 3.0)); passo = L / nv; meio = [rng.choice(["janela", "janela", "varanda", "banheiro", "dupla"]) for _ in range((nv + 1) // 2)]
    padrao = meio + meio[: nv // 2][::-1]
    guarda = rng.choice(["grade", "mureta"]); cinta = rng.random() < 0.75
    escada = rng.random() < p.get("p_escada", 0.65)
    if escada:   # coluna da escada em outra cor/material, saliente, com janelinhas nos patamares (muito comum no Brasil)
        mat_esc = M.pastilha(rng.choice(["#3fa7d6", "#e3a12f", "#4fae9c", "#c25a36", "#ede6d8"])) if rng.random() < 0.5 else mat2
        F.faixa(yp - 1.15, yp + 1.15, Z0 + 2.85, H + 0.6, mat_esc, 0.1, "escada")
        for k in range(n_and):
            F.janela(yp, Z0 + H_t + k * H_ANDAR + 1.35, 0.9, 0.55, peitoril=False, x=-0.1)
    for k in range(n_and):
        z = Z0 + H_t + k * H_ANDAR
        if cinta:
            F.faixa(-0.02, L + 0.02, z - 0.12, z + 0.04, mat2, 0.05, "cinta")
        for j, tipo in enumerate(padrao):
            y = passo * (j + 0.5)
            if escada and abs(y - yp) < 1.15 + 0.9:
                continue
            if tipo == "varanda":
                F.janela(y, z, 1.6, 2.1, peitoril=False)
                F.varanda(y, z, min(passo - 0.4, 2.8), 1.0, guarda, varal=rng.random() < 0.35)
            elif tipo == "banheiro":
                F.janela(y, z + 1.5, 0.6, 0.6, peitoril=False)
            elif tipo == "dupla":
                F.janela(y, z + 0.95, 1.8, 1.25)
                if rng.random() < 0.35:
                    F.ar_condicionado(y + 1.45, z + 1.05)
            else:
                F.janela(y, z + 0.95, 1.2, 1.25)
                if rng.random() < 0.3:
                    F.ar_condicionado(y + 1.15, z + 1.0)
    for nm, orig, rot, ext in _faces_laterais(p.get("lateral"), L, D):
        Fl = Face(f"{nome}_{nm}", col, rng, mats)
        Fl.faixa(0.0, ext, 0.0, Z0 + 0.9, rodape, 0.03, "rodape")
        _grade_janelas(Fl, ext, [Z0 + H_t + k * H_ANDAR for k in range(n_and)], ac=0.3)
        _grade_janelas(Fl, ext, [Z0], w=1.0, h=1.1, passo=3.4, ac=0.0, grade_terreo=True)
    _topo(nome, col, rng, L, D, H, mat2 if rng.random() < 0.5 else mat, torre=n_and >= 4)
    return H


def comercial(nome, col, rng, L, D, p):
    n_sup = p.get("andares", rng.randint(0, 2)); H_l = 3.3; H = Z0 + H_l + n_sup * H_ANDAR; rec = 0.7
    mat = _mat_fachada(p.get("mat") or rng.choice([{"nome": "pastilha", "cor": rng.choice(["#3fa7d6", "#e3a12f", "#4fae9c", "#e8806c"])}, None, None]), rng)
    mats = _mats(rng, p); mat2 = _mat_fachada(p.get("mat2"), rng)
    G.caixa(f"{nome}_terreo", (rec, 0.0, 0.0), (D, L, Z0 + H_l), M.reboco("#e9e2d2", desgaste=0.4, detalhe=1.0), col)
    G.caixa(f"{nome}_corpo", (0.0, 0.0, Z0 + H_l - 0.35), (D, L, H), mat, col, chanfro=0.02)
    G.caixa(f"{nome}_piso", (0.0, 0.0, 0.0), (rec + 0.02, L, Z0 + 0.02), M.ladrilho_hidraulico(tam_m=0.2), col)
    F = Face(nome + "_f", col, rng, mats)
    nl = 1 if L < 8 else rng.choice([1, 2]); lw = L / nl
    nomes = list(NOMES_LOJA); rng.shuffle(nomes)
    for i in range(nl):
        y0, y1 = i * lw, (i + 1) * lw; yc = (y0 + y1) / 2
        for yy in (y0 + 0.18, y1 - 0.18):   # pilares nas divisas
            G.caixa(F._id("pilar"), (0.0, yy - 0.18, 0.0), (rec, yy + 0.18, Z0 + H_l), mat2, col)
        aberta = rng.random() < p.get("p_aberta", 0.65)
        cor_let = rng.choice(["#c8231f", "#1d4f9c", "#2f7d3a", "#e3a12f", "#5a2d82", "#d9702c"])
        if aberta:
            fundo = G.caixa(F._id("interior"), (rec - 0.02, y0 + 0.36, Z0), (rec - 0.005, y1 - 0.36, Z0 + H_l - 0.4), M.emissor("#fff1d6", 0.9), col)
            fundo.lightgroup = "artificial"; fundo["suspenso"] = True
            for k in range(3):   # prateleiras com produtos genéricos (caixinhas coloridas)
                zp = Z0 + 0.5 + k * 0.6
                G.caixa(F._id("prat"), (rec - 0.32, y0 + 0.5, zp), (rec - 0.02, y1 - 0.5, zp + 0.03), M.pintura("#d8d2c4", rug=0.6), col)["suspenso"] = True
                yy = y0 + 0.55
                while yy < y1 - 0.7:
                    pw, ph = rng.uniform(0.1, 0.3), rng.uniform(0.12, 0.4)
                    G.caixa(F._id("prod"), (rec - 0.28, yy, zp + 0.03), (rec - 0.06, yy + pw, zp + 0.03 + ph),
                            M.pintura(rng.choice(ROUPAS + ["#e3a12f", "#c25a36"]), rug=0.6), col)["suspenso"] = True
                    yy += pw + rng.uniform(0.02, 0.12)
            G.caixa(F._id("balcao"), (0.08, y0 + 0.5, Z0), (0.42, y0 + 0.5 + min(1.6, lw * 0.35), Z0 + 1.05), M.pintura(cor_let, rug=0.5, desgaste=0.4), col)["suspenso"] = True
            G.caixa(F._id("rolo"), (0.02, y0 + 0.36, Z0 + H_l - 0.65), (0.26, y1 - 0.36, Z0 + H_l - 0.4), M.chapa_ondulada("#8a9098"), col)["suspenso"] = True
            lamp = G.caixa(F._id("lamp"), (rec * 0.3, yc - 0.6, Z0 + H_l - 0.44), (rec * 0.6, yc + 0.6, Z0 + H_l - 0.42), M.emissor("#ffffff", 8.0), col)
            lamp.lightgroup = "artificial"; lamp["suspenso"] = True
            lz = LZ.luz_ponto(F._id("luz"), (rec * 0.5, yc, Z0 + H_l - 0.6), p.get("watts_loja", 120), "#fff1d6", "artificial", raio=0.3)
        else:
            G.caixa(F._id("porta_enr"), (0.04, y0 + 0.36, Z0), (0.08, y1 - 0.36, Z0 + H_l - 0.4),
                    M.chapa_ondulada(rng.choice(["#8a9098", "#5c6b73", "#a8442b", "#2f5d62"]), desgaste=0.6), col)["suspenso"] = True
        # letreiro (nome genérico) e toldo listrado
        G.caixa(F._id("letreiro"), (-0.12, y0 + 0.4, Z0 + H_l - 0.35), (0.0, y1 - 0.4, Z0 + H_l + 0.3), M.pintura(cor_let, rug=0.45, desgaste=0.3), col, chanfro=0.015)["suspenso"] = True
        corpo = nomes[i % len(nomes)]
        F.texto(corpo, yc, Z0 + H_l - 0.03, min(0.42, (lw - 1.2) / max(4, len(corpo)) * 1.6), M.pintura("#f8f4ea", rug=0.5), x=-0.125)
        if rng.random() < p.get("p_toldo", 0.55):
            cores = rng.choice([("#c8231f", "#f1e9d8"), ("#2f5d62", "#f1e9d8"), ("#2f7d3a", "#f1e9d8"), ("#1d4f9c", "#f1e9d8"), ("#e3a12f", "#c25a36")])
            _laje_inclinada(F._id("toldo"), 0.0, Z0 + H_l - 0.42, -1.3, Z0 + H_l - 0.95, y0 + 0.45, y1 - 0.45, 0.03, M.listrado(*cores), col)
    for k in range(n_sup):
        z = Z0 + H_l + k * H_ANDAR
        nj = max(1, int(L / 2.6)); pj = L / nj
        vaga = rng.random() < 0.3
        for j in range(nj):
            F.janela(pj * (j + 0.5), z + 0.9, min(1.9, pj - 0.7), 1.3, aluga=vaga and j == nj // 2)
            if not vaga and rng.random() < 0.3:
                F.ar_condicionado(pj * (j + 0.5) + min(1.9, pj - 0.7) / 2 + 0.5, z + 1.0)
    for nm, orig, rot, ext in _faces_laterais(p.get("lateral"), L, D):
        Fl = Face(f"{nome}_{nm}", col, rng, mats)
        _grade_janelas(Fl, ext, [Z0 + H_l + k * H_ANDAR for k in range(n_sup)], ac=0.3)
        # térreo lateral: portas de enrolar (depósito, garagem) alternadas com janelas gradeadas, sobre um rodapé
        Fl.faixa(0.0, ext, 0.0, Z0 + 0.7, M.concreto("#8f897d", placa_m=(0.6, 0.4)), 0.03, "rodape")
        Fl.faixa(0.0, ext, Z0 + H_l - 0.45, Z0 + H_l - 0.3, mat2, 0.06, "viga")
        yy = rng.uniform(1.6, 2.4)
        while yy < ext - 1.4:
            if rng.random() < 0.5:
                G.caixa(Fl._id("porta_enr"), (-0.05, yy - 1.3, Z0), (0.0, yy + 1.3, Z0 + 2.6),
                        M.chapa_ondulada(rng.choice(["#8a9098", "#5c6b73", "#2f5d62", "#a8442b"]), desgaste=0.6), col)["suspenso"] = True
                yy += 3.6
            else:
                Fl.janela(yy, Z0 + 1.0, 1.2, 1.1, grade=True); yy += 2.8
    _topo(nome, col, rng, L, D, H, mat2, caixa=n_sup > 0 or rng.random() < 0.5, antenas=rng.random() < 0.7)
    return H


def sobrado(nome, col, rng, L, D, p):
    rec = p.get("recuo", rng.uniform(3.0, 4.2)); H = Z0 + 2 * 3.0; mats = _mats(rng, p)
    mat = _mat_fachada(p.get("mat"), rng); mat_muro = _mat_fachada(p.get("mat_muro"), rng)
    G.caixa(f"{nome}_corpo", (rec, 0.3, 0.0), (D, L - 0.3, H), mat, col, chanfro=0.02)
    G.caixa(f"{nome}_piso", (0.0, 0.0, 0.0), (rec + 0.02, L, Z0 + 0.02), M.concreto("#a8a294", placa_m=(1.0, 1.0), detalhe=1.0), col)
    # muro com capa, portão de garagem, portão social com grade, arandela e número
    F = Face(nome + "_f", col, rng, mats); hm = 2.0
    yg0, yg1 = (0.25, 3.25) if rng.random() < 0.5 else (L - 3.25, L - 0.25)
    ys0, ys1 = (yg1 + 0.4, yg1 + 1.4) if yg0 < 1 else (yg0 - 1.4, yg0 - 0.4)
    trechos = sorted([(0.0, min(yg0, ys0)), (min(yg1, ys1), max(yg0, ys0)), (max(yg1, ys1), L)])
    for a, b in trechos:
        if b - a > 0.05:
            G.caixa(F._id("muro"), (0.0, a, 0.0), (0.18, b, Z0 + hm), mat_muro, col)
            G.caixa(F._id("capa"), (-0.04, a, Z0 + hm), (0.22, b, Z0 + hm + 0.06), M.concreto("#cfc8ba", placa_m=(1.0, 0.3)), col)["suspenso"] = True
    G.caixa(F._id("portao"), (0.05, yg0, Z0), (0.09, yg1, Z0 + hm - 0.05), M.chapa_ondulada(rng.choice(["#2f5d62", "#5c6b73", "#7d5f4a", "#a8442b", "#ede6d8"]), desgaste=0.5), col)["suspenso"] = True
    F.janela((ys0 + ys1) / 2, Z0, ys1 - ys0, hm - 0.1, peitoril=False, grade=True, acesa=False, folhas=[mats["escuro"], mats["escuro"]])
    arand = G.caixa(F._id("arand"), (-0.12, ys1 + 0.15, Z0 + 1.75), (0.0, ys1 + 0.3, Z0 + 1.95), M.emissor("#ffe3bd", 5.0), col); arand.lightgroup = "artificial"; arand["suspenso"] = True
    F.texto(str(rng.randint(10, 999)), (ys0 + ys1) / 2, Z0 + hm - 0.35, 0.16, mats["moldura"], x=-0.01)
    # casa: frente em x = rec (outra face, mais recuada)
    Fc = Face(nome + "_casa", col, rng, mats)
    p["_recuo_real"] = rec
    Fc.janela(L / 2 + 1.0, Z0 + 3.0 + 0.95, 1.4, 1.2, grade=rng.random() < 0.5)
    if rng.random() < 0.5:
        Fc.janela(L / 2 - 1.6, Z0 + 3.0, 1.4, 2.1, peitoril=False); Fc.varanda(L / 2 - 1.6, Z0 + 3.0, 2.0, 0.8, "grade", varal=rng.random() < 0.4)
    else:
        Fc.janela(L / 2 - 1.6, Z0 + 3.0 + 0.95, 1.0, 1.1)
    Fc.janela(L / 2 - 1.2, Z0, 0.9, 2.1, peitoril=False, acesa=False, folhas=[M.madeira("#7a4a2a"), M.madeira("#7a4a2a")])
    Fc.janela(L / 2 + 1.0, Z0 + 0.95, 1.4, 1.1, grade=True)
    Fc.faixa(0.3, L - 0.3, Z0 + 2.9, Z0 + 3.05, M.reboco("#f1e8d8"), 0.05, "cinta")
    # telhado cerâmico de duas águas (cumeeira ao longo da fachada)
    tel = M.telha_ceramica(rng.choice(["#b5532f", "#a24a2a", "#c2643a", "#8f4a33"]))
    xm = (rec + D) / 2; zc = H + rng.uniform(1.4, 1.9); bei = 0.55
    _laje_inclinada(f"{nome}_tel_f", rec - bei, H - 0.15, xm, zc, -0.1 + 0.3, L - 0.3 + 0.1, 0.07, tel, col)
    _laje_inclinada(f"{nome}_tel_t", xm, zc, D + bei, H - 0.15, -0.1 + 0.3, L - 0.3 + 0.1, 0.07, tel, col)
    for yy in (0.3, L - 0.3):   # oitões (triângulos de parede nas pontas)
        bm = bmesh.new(); vs = [bm.verts.new((rec, yy, H)), bm.verts.new((D, yy, H)), bm.verts.new((xm, yy, zc - 0.05))]
        bm.faces.new(vs); me = bpy.data.meshes.new(f"{nome}_oitao{yy:.1f}"); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(me.name, me); o.data.materials.append(mat); col.objects.link(o); o["suspenso"] = True
        s = o.modifiers.new("esp", "SOLIDIFY"); s.thickness = 0.15
    G.cilindro(f"{nome}_cx", (D - 1.6, L / 2 + rng.uniform(-1, 1), H + 0.2), 0.55, 0.85, M.pintura("#3a6fb0", rug=0.5, desgaste=0.4), col, raio_topo=0.5, lados=20)["suspenso"] = True
    return zc


ESTILOS = {"residencial": residencial, "comercial": comercial, "sobrado": sobrado}


# ------------------------------------------------------------------ montagem de um lote no mundo
def _pose(orient, lado, f, a, b):
    """Origem e rotação do lote. orient "x": fachada no plano x = f, lote de y = a a b; "y": plano y = f, de x = a a b.
    lado: para onde vai o CORPO do prédio (+1: +x ou +y; −1: −x ou −y); a fachada olha para o lado oposto."""
    if orient == "x":
        return ((f, a, 0.0), 0.0) if lado > 0 else ((f, b, 0.0), math.pi)
    return ((b, f, 0.0), math.pi / 2) if lado > 0 else ((a, f, 0.0), -math.pi / 2)


def _espelhado(orient, lado):
    """True quando y = 0 do lote cai na ponta MAIOR do intervalo (a, b) no mundo."""
    return (orient == "x" and lado < 0) or (orient == "y" and lado > 0)


def _lote(estilo, nome, col, rng, x_f, lado, ya, yb, D, p):
    """Lote de ya a yb (mundo) com a fachada no plano x_f (ou y_f, com p["_orient"] = "y") voltada para a rua."""
    L = yb - ya
    loc, rot = _pose(p.get("_orient", "x"), lado, x_f, ya, yb)
    raiz = _raiz(nome, col, loc, rot)
    antes = set(col.objects)
    luzes0 = {o.name for o in bpy.data.objects if o.type == "LIGHT"}
    H = ESTILOS[estilo](nome, col, rng, L, D, p)
    # todos os objetos novos: faces e corpo já estão em coordenadas do lote, exceto as peças das FACES laterais e da
    # casa do sobrado, que foram feitas em coordenadas da face e precisam da raiz da face
    novos = [o for o in col.objects if o not in antes and o is not raiz]
    for o in novos:
        if o.parent is None:
            o.parent = raiz
    for o in bpy.data.objects:   # luzes das lojas (ficam na coleção da cena)
        if o.type == "LIGHT" and o.name not in luzes0 and o.parent is None:
            o.parent = raiz
    return raiz, H


def _reparentar_face(col, raiz, prefixo, orig, rot):
    """Move as peças de uma face (nome começa com 'prefixo') para uma raiz própria com origem e rotação da face."""
    rf = _raiz(prefixo + "_raiz", col, orig, rot, pai=raiz)
    for o in list(col.objects):
        if o.name.startswith(prefixo + "_") and o.parent is raiz and o is not rf:
            o.parent = rf
    return rf


def construir_lote(estilo, nome, col, rng, x_f, lado, ya, yb, D, p):
    raiz, H = _lote(estilo, nome, col, rng, x_f, lado, ya, yb, D, p)
    L = yb - ya
    for nm, orig, rot, ext in _faces_laterais(p.get("lateral"), L, D):
        _reparentar_face(col, raiz, f"{nome}_{nm}", orig, rot)
    if estilo == "sobrado":
        _reparentar_face(col, raiz, f"{nome}_casa", (p.get("_recuo_real", 0.0), 0.0, 0.0), 0.0)
    return raiz, H


# ------------------------------------------------------------------ componentes registrados
def _lado_lateral(orient, lado, lateral_mundo):
    """'inicio'/'fim' no MUNDO (coordenada menor / maior) → no lote (y = 0 / y = L)."""
    if lateral_mundo in (None, "ambos") or not _espelhado(orient, lado):
        return lateral_mundo
    return {"inicio": "fim", "fim": "inicio"}[lateral_mundo]


@componente("fachada_quadra")
def fachada_quadra(ctx, p, rng, col):
    """Frente de quadra: lotes por semente. Fachada no plano x = x_fachada (lotes de y0 a y1) OU no plano y = y_fachada
    (lotes de x0 a x1). params: lado (para onde vai o corpo do prédio), profundidade (9),
    estilos {"residencial": peso, "comercial": peso, "sobrado": peso}, esquina_inicio/esquina_fim (bool: o lote da
    ponta ganha fachada lateral), lotes (lista fixa opcional [{"estilo", "largura", …params}])."""
    orient = "y" if "y_fachada" in p else "x"
    x_f = p["y_fachada"] if orient == "y" else p["x_fachada"]
    lado = p.get("lado", -1); y0, y1 = (p["x0"], p["x1"]) if orient == "y" else (p["y0"], p["y1"]); D = p.get("profundidade", 9.0)
    pesos = p.get("estilos", {"residencial": 0.4, "comercial": 0.35, "sobrado": 0.25})
    larguras = {"residencial": (10.0, 15.0), "comercial": (6.5, 11.0), "sobrado": (6.5, 8.5)}
    nome = p.get("nome", f"quadra_{int(y0)}")
    lotes = []
    if p.get("lotes"):
        y = y0
        for i, l in enumerate(p["lotes"]):
            lotes.append((l["estilo"], y, min(y1, y + l["largura"]), {k: v for k, v in l.items() if k not in ("estilo", "largura")})); y += l["largura"]
    else:
        y = y0
        while y1 - y > 0.5:
            est = rng.choices(list(pesos), weights=list(pesos.values()))[0]
            a, b = larguras[est]; w = rng.uniform(a, b)
            if y1 - (y + w) < 5.0:      # o último lote absorve a sobra
                w = y1 - y
                if w > 16:
                    w = w / 2
            lotes.append((est, y, y + w, {})); y += w
    for i, (est, ya, yb, extra) in enumerate(lotes):
        lat = None
        if i == 0 and p.get("esquina_inicio"):
            lat = "inicio"
        if i == len(lotes) - 1 and p.get("esquina_fim"):
            lat = "ambos" if lat else "fim"
        if lat and est == "sobrado":
            est = "residencial"          # esquina: prédio com fachada nas duas ruas
        pr = dict(extra); pr["lateral"] = _lado_lateral(orient, lado, lat); pr["_orient"] = orient
        construir_lote(est, f"{nome}_{i}_{est[:3]}", col, rng, x_f, lado, ya, yb, D, pr)


@componente("chao")
def chao(ctx, p, rng, col):
    """Terreno simples (fundo de lote, quintal, terreno baldio): caixa de x0..x1, y0..y1, topo em z (0,15 = calçada)."""
    G.caixa(p.get("nome", "chao"), (p["x0"], p["y0"], -0.05), (p["x1"], p["y1"], p.get("z", Z0)),
            M.por_nome(p.get("material", "terra")) if isinstance(p.get("material", "terra"), str) else _mat_fachada(p["material"], rng), col)


def _isolado(estilo):
    def f(ctx, p, rng, col):
        construir_lote(estilo, p.get("nome", f"{estilo}_{int(p['y0'])}"), col, rng, p["x_fachada"], p.get("lado", -1),
                       p["y0"], p["y1"], p.get("profundidade", 9.0), p)
    return f


componente("predio_residencial")(_isolado("residencial"))
componente("predio_comercial")(_isolado("comercial"))
componente("sobrado")(_isolado("sobrado"))
