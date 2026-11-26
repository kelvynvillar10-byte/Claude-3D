#!/usr/bin/env python3
"""E9 — COMBINAÇÕES de poderes (teste de ação, NÃO é história). Usa só o que já foi aprovado: núcleo E7, os 5 poderes da
E8 e as extensões X1–X4. O rig v2 não é alterado.

Três planos, cada um com um poder DOMINANTE (que também move o Heitor) e um SECUNDÁRIO (a mesa reduz a 0,5):
  C1 (manhã, frente)  terra extremo (dominante) + eletricidade moderada no mesmo alvo (secundário)
                      + um 3º efeito ligado de propósito (poeira de demonstração): a mesa tem de SUPRIMIR e registrar
  C2 (tarde, perfil)  elasticidade: pegar a laranja (dominante) + eletricidade na mão e no corpo (secundário)
  C3 (noite, costas)  voo: decolagem vertical (dominante) + arcos elétricos no corpo (secundário)
Medidas: regra da mesa a cada quadro (≤ 1 dominante com ganho 1, ≤ 1 secundário com ganho ≤ 0,5, o resto 0 e
registrado), flashes por segundo, proteção do rosto/estampa, contatos (raio na mão; brilho da mão sobre a pele no
desenho real), determinismo, regressão, integridade, tempo.
"""
import hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "extensoes" / "x1_tom_de_luz"))
from cenografia.nucleo.atmosfera import Atmosfera                          # noqa: E402
import e0_testes as T0, e1_testes as T1, e6_cena_prova as E6, e8_testes as E8   # noqa: E402
import e8_voo_testes as EV, e8_elasticidade_testes as EL_T                 # noqa: E402
from efeitos.nucleo.base import Params, Mesa, Contexto, REGISTRO           # noqa: E402
from efeitos.nucleo import seguranca as SG, contatos as CT                 # noqa: E402
import tom_de_luz as X1                                                    # noqa: E402
OUT = RAIZ / "cenografia" / "testes" / "e9"; OUT.mkdir(parents=True, exist_ok=True)
FPS = 30; W, H = 1080, 1920
res = {}


def placas():
    out = {}
    for hor, nome in (("manha", "manha_frente"), ("tarde", "tarde_perfil"), ("noite", "noite_costas")):
        out[hor] = E6.placa(next(x for x in E6.PLANO["tomadas"] if x["nome"] == nome))[0]
    return out


# ------------------------------------------------------------------ os três planos
class Plano:
    """Um plano de combinação: cria os efeitos, sabe preparar a mesa, desenhar o Heitor e compor o quadro."""
    def __init__(self, nome, PL):
        self.nome = nome; self.PL = PL
        if nome == "C1":
            self.hor = "manha"; self.P = PL["manha"]; alvo = (-4.55, 10.8, 0.154)
            terra = REGISTRO["terra"](Params(intensidade="extremo", duracao=3.4, semente=11),
                                      origem=E8.PE, alvo=alvo, fundo=E8.fundo(self.P, "manha"), prof=E8.prof_frontal(self.P),
                                      faixa_x=(-6.75, -3.75), camera_pos=tuple(self.P.m["intrinsecos"]["pos"]))
            eletr = REGISTRO["eletricidade"](Params(intensidade="moderado", duracao=3.4, semente=12), alvo=alvo, alvo_no_chao=True,
                                             mao=f"mao_{E8.lado_mao(self.P, alvo)}")
            poeira = REGISTRO["demo_poeira"](Params(intensidade="moderado", duracao=3.0, semente=13, cor="#c9b08a"), inicio=0.2,
                                             origem=(-5.6, 7.0, 0.154))
            poeira.prioridade = 1
            self.dom, self.sec, self.extra = terra, eletr, [poeira]; self.mira = E8.mira_de(("", "terra"), alvo)
            self.dur = 3.4; self.cam = {"tz": (0.0, 0.3)}; self.rotulo = "terra (dominante) + eletricidade (secundário)"
        elif nome == "C2":
            self.hor = "tarde"; self.P = PL["tarde"]
            self.dom = REGISTRO["elasticidade"](Params(intensidade="moderado", semente=41), modo="pegar", origem=(-5.1, 2.7, 0.154), alvo=(-6.9, 4.4, 1.45))
            self.sec = REGISTRO["eletricidade"](Params(intensidade="moderado", duracao=self.dom.fases.duracao, semente=14), mao="mao_d")
            self.sec.prioridade = 1; self.extra = []
            self.dur = self.dom.fases.duracao; self.cam = {"tx": (-0.15, 0.1)}; self.rotulo = "elasticidade (dominante) + eletricidade (secundário)"
        else:
            self.hor = "noite"; self.P = PL["noite"]
            self.dom = REGISTRO["voo"](Params(intensidade="extremo", duracao=4.0, semente=21), modo="subir", origem=(-5.1, 6.4, 0.154),
                                       direcao=(0, 1, 0), vista="costas", fundo=E8.fundo(self.P, "noite"))
            self.sec = REGISTRO["eletricidade"](Params(intensidade="moderado", duracao=3.2, semente=15), inicio=0.3, mao="mao_d")
            self.sec.prioridade = 1; self.extra = []
            self.dur = 4.0; self.cam = {"tz": (0.0, 0.3), "ty": (0.0, 0.08)}; self.rotulo = "voo (dominante) + eletricidade (secundário)"
        self.A = Atmosfera(self.P, "limpo", 11); self.efeitos = [self.dom, self.sec] + self.extra

    def camera(self, t):
        u = min(1.0, t / self.dur); s = u * u * (3 - 2 * u)
        return {k: a + (b - a) * s for k, (a, b) in self.cam.items()}

    def preparar(self, mesa, t, k):
        cam = self.camera(t); P = self.P
        if self.nome == "C1":
            pose, rosto = E8.pose_poder(P, self.dom, t, self.mira); self._pose = (pose, rosto)
            pc = {"pe_mundo": E8.PE, "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1}
        elif self.nome == "C2":
            pc = self.dom.personagem(Contexto(P, cam, t, k, FPS))
        else:
            pc = self.dom.personagem(None, t)
        mesa.preparar(P, cam, t, k, pc)
        return cam

    def desenhista(self, mesa):
        if self.nome == "C1":
            return E8.desenhista(mesa, *self._pose)
        if self.nome == "C2":
            return EL_T.desenhista(self.dom, mesa)
        return EV.desenhista(self.dom, mesa)

    def profundidade(self, mesa, cam):
        if self.nome == "C1":
            return mesa.ctx.placa(E8.PE)[2]
        if self.nome == "C2":
            return self.dom.estado(mesa.ctx)["z"] + cam.get("tz", 0.0)
        return self.dom.tela_personagem(mesa.ctx)[3] + cam.get("tz", 0.0)

    def quadro(self, mesa, t, k):
        cam = self.preparar(mesa, t, k); P, A = self.P, self.A
        tom = X1.fazer_tom({"pe_mundo": mesa.ctx.personagem["pe_mundo"], "altura_m": 1.4}, luzes=mesa.luzes(P, cam))
        return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[EL_T.HOR[self.hor]])), cam=cam,
                        personagem=self.desenhista(mesa), profundidade_personagem=self.profundidade(mesa, cam), efeitos=mesa,
                        deslocamento_px=mesa.tremida(), semente_grao=k, ceu_extra=A.ceu(t), tom_personagem=tom)


# ------------------------------------------------------------------ vídeo + medidas por quadro
def t_video(PL):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E9_combinacoes.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); out = {}; folha = []; q = 0; lums_total = []
    for nome in ("C1", "C2", "C3"):
        pl = Plano(nome, PL); mesa = E8.MesaMedida(pl.efeitos, fps=FPS); n = int(pl.dur * FPS)
        regra = {"quadros_com_2_dominantes": 0, "secundario_ganho_max": 0.0, "suprimidos_registrados": 0, "quadros_com_3_ativos": 0}
        cob = {"rosto": 0.0, "estampa": 0.0}; tempos = []; lums = []; contato = []
        for k in range(n):
            t = k / FPS; t0 = time.time(); img = pl.quadro(mesa, t, q); tempos.append(time.time() - t0)
            ganhos = sorted((e.ganho for e in pl.efeitos if e.ativo(mesa.ctx)), reverse=True)
            ativos_brutos = [e for e in pl.efeitos if e.ativo(mesa.ctx)]
            if len(ativos_brutos) >= 3:
                regra["quadros_com_3_ativos"] += 1
            # ganho base da mesa (antes do governador de flashes): dominante 1, secundário 0,5, demais 0
            base = sorted(ativos_brutos, key=lambda e: (-e.prioridade, -e.p.fator))
            if len(base) >= 2 and base[0] is not pl.dom:
                regra["quadros_com_2_dominantes"] += 1
            if len(ganhos) >= 2:
                regra["secundario_ganho_max"] = max(regra["secundario_ganho_max"], round(ganhos[1] / max(ganhos[0], 1e-9), 3))
            if mesa.cobertura:
                cob = {kk: max(cob[kk], mesa.cobertura[kk]) for kk in cob}
            if nome == "C1" and pl.sec.ultimas_curvas and pl.dom.fases.em(t)[0] in ("uso", "impacto") and pl.sec in mesa.ativos:
                m = mesa.ctx.tela(CT.rig_mundo(mesa.ctx, pl.sec.mao)); i_ = mesa.ctx.tela(pl.sec.ultimas_curvas[0][0][0])
                contato.append(math.hypot(i_[0] - m[0], i_[1] - m[1]))
            fase = pl.dom.fases.em(t)[0] or "—"
            img = T0._marca(T0._texto(img, ["E9 · combinações (teste, não é história)", pl.rotulo, f"fase: {fase}"], 1745, 25))
            pr.stdin.write(np.ascontiguousarray(img).tobytes()); q += 1
            l = SG.luminancia_relativa(cv2.resize(img, (135, 240), interpolation=cv2.INTER_AREA)); lums.append(l); lums_total.append(l)
            if k in (int(n * 0.3), int(n * 0.55), int(n * 0.8)):
                folha.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{nome} {t:.1f}s {fase}"], 20, 17))
        regra["suprimidos_registrados"] = sum(len(r["suprimidos"]) for r in mesa.registro)
        out[nome] = {"combinacao": pl.rotulo, "quadros": n, "regra_da_mesa": regra, "cobertura_max_rosto_estampa": cob,
                     "flashes": SG.analisar_flashes(lums, FPS), "composicao_media_s": round(float(np.mean(tempos)), 2),
                     "composicao_max_s": round(float(np.max(tempos)), 2)}
        if contato:
            out[nome]["raio_sai_da_mao_erro_px_max"] = round(max(contato), 2)
        print(nome, json.dumps(out[nome], ensure_ascii=False)[:700], flush=True)
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "E9_quadros.jpg"), np.vstack([np.hstack(folha[i:i + 3]) for i in range(0, 9, 3)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    out["_flashes_video_inteiro"] = SG.analisar_flashes(lums_total, FPS)
    return out


def t_contatos(PL):
    """C2 e C3: o brilho da mão da eletricidade (contato do núcleo, CT.rig) cai sobre a pele no desenho real do Heitor
    (esticado pela X4 / voando pela X2)."""
    out = {}
    for nome in ("C2", "C3"):
        pl = Plano(nome, PL); mesa = Mesa(pl.efeitos, fps=FPS); n = int(pl.dur * FPS); ok = []
        for k in range(n):
            t = k / FPS; pl.preparar(mesa, t, k)
            if k % 4 or pl.sec not in mesa.ativos:
                continue
            s = skia.Surface(pl.P.W, pl.P.H); cv = s.getCanvas(); cv.clear(0); pl.desenhista(mesa)(cv, None)
            img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
            x, y, _ = CT.rig(mesa.ctx, pl.sec.mao); ix, iy = int(round(x)), int(round(y))
            if 0 <= ix < pl.P.W and 0 <= iy < pl.P.H:
                ok.append(bool(img[iy, ix, 3] > 200 and EL_T._na_pele(img[iy, ix, :3])))
        out[nome] = {"brilho_da_mao_sobre_a_pele_pct": round(100 * float(np.mean(ok)), 1) if ok else None, "amostras": len(ok)}
    return out


def t_det(PL):
    hs = []
    for _ in range(2):
        pl = Plano("C1", PL); mesa = Mesa(pl.efeitos, fps=FPS); kq = int(2.0 * FPS)
        for kk in range(kq):
            pl.preparar(mesa, kk / FPS, kk)
        hs.append(hashlib.sha256(pl.quadro(mesa, kq / FPS, kq).tobytes()).hexdigest())
    return {"mesmo_quadro_duas_vezes_identico": hs[0] == hs[1]}


if __name__ == "__main__":
    so = sys.argv[1:]; caminho = OUT / "e9_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())
    PL = placas()

    def rodar(nome, f, *a):
        if so and nome not in so:
            return
        t = time.time(); res[nome] = f(*a)
        if isinstance(res[nome], dict):
            res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False, default=str)[:1500], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    rodar("E9_contatos", t_contatos, PL)
    rodar("E9_determinismo", t_det, PL)
    rodar("E9_regressao", EV.t_regressao)
    rodar("E9_video", t_video, PL)
    rodar("E9_integridade", E8.t_integridade)
