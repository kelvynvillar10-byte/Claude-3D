#!/usr/bin/env python3
"""Verifica o ambiente do Modo Curioso Studio AI.

Aponta o que está AUSENTE, INCOMPATÍVEL (versão diferente da travada) ou com AVISO.
Roda testes funcionais reais: render do Blender (Cycles CPU), texto com as fontes
oficiais (skia), OCR, codificação 1080×1920 (FFmpeg) e leitura de áudio (librosa).

Uso:
  .venv/bin/python ambiente/verificar.py            # completo
  .venv/bin/python ambiente/verificar.py --rapido   # sem testes funcionais
  .venv/bin/python ambiente/verificar.py --rede     # também testa os serviços externos
Saída: tabela no terminal + _tmp/verificacao.json. Código de saída 1 se houver AUSENTE ou INCOMPATÍVEL.
"""
import json, os, platform, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
AMB = RAIZ / "ambiente"
PY_VERSAO = "3.13.14"
FFMPEG_PREFIXO = "6.1"
R = []  # resultados


def reg(grupo, item, status, detalhe=""):
    R.append({"grupo": grupo, "item": item, "status": status, "detalhe": detalhe})


def cmd(args, timeout=60):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, "não encontrado"
    except subprocess.TimeoutExpired:
        return 124, "tempo esgotado"


def sistema():
    os_rel = Path("/etc/os-release").read_text() if Path("/etc/os-release").exists() else ""
    nome = re.search(r'PRETTY_NAME="([^"]+)"', os_rel)
    nome = nome.group(1) if nome else platform.platform()
    reg("sistema", "SO", "OK" if "24.04" in nome else "AVISO", nome)
    reg("sistema", "Arquitetura", "OK" if platform.machine() == "x86_64" else "INCOMPATÍVEL", platform.machine())
    reg("sistema", "CPU", "OK", f"{os.cpu_count()} núcleos")
    try:
        mem = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1)) / 1e6
        reg("sistema", "RAM", "OK" if mem >= 8 else "AVISO", f"{mem:.1f} GB")
    except Exception:
        reg("sistema", "RAM", "AVISO", "não lida")
    livre = shutil.disk_usage(RAIZ).free / 1e9
    reg("sistema", "Disco livre", "OK" if livre >= 20 else "AVISO", f"{livre:.0f} GB")
    gpu = Path("/dev/dri").exists() or shutil.which("nvidia-smi")
    reg("sistema", "GPU", "OK" if gpu else "AVISO", "presente" if gpu else "ausente: Blender em CPU (previsto na arquitetura)")


def binarios():
    c, out = cmd(["ffmpeg", "-version"])
    v = re.search(r"ffmpeg version (\S+)", out)
    if c != 0 or not v:
        reg("programas", "ffmpeg", "AUSENTE", out[:80])
    else:
        enc = cmd(["ffmpeg", "-hide_banner", "-encoders"])[1]
        ok = v.group(1).startswith(FFMPEG_PREFIXO) and "libx264" in enc
        reg("programas", "ffmpeg", "OK" if ok else "INCOMPATÍVEL", f"{v.group(1)} (esperado {FFMPEG_PREFIXO}.x com libx264)")
    for b, pad in [("ffprobe", r"ffprobe version (\S+)"), ("git", r"git version (\S+)"),
                   ("git-lfs", r"git-lfs/(\S+)"), ("uv", r"uv (\S+)")]:
        args = [b, "version"] if b == "git-lfs" else ([b, "-version"] if b == "ffprobe" else [b, "--version"])
        c, out = cmd(args)
        m = re.search(pad, out)
        reg("programas", b, "OK" if c == 0 and m else "AUSENTE", m.group(1) if m else out[:60])
    for lib in ["libEGL.so.1", "libGL.so.1", "libgomp.so.1", "libXi.so.6", "libxkbcommon.so.0", "libSM.so.6", "libXxf86vm.so.1", "libfontconfig.so.1"]:
        c, out = cmd(["ldconfig", "-p"])
        reg("bibliotecas do sistema", lib, "OK" if lib in out else "AUSENTE")


def python_e_pacotes():
    v = platform.python_version()
    venv = sys.prefix != sys.base_prefix
    reg("python", "versão", "OK" if v == PY_VERSAO else "INCOMPATÍVEL", f"{v} (esperado {PY_VERSAO})")
    alvo = Path(os.environ.get("STUDIO_VENV", RAIZ / ".venv")).resolve()
    reg("python", "ambiente virtual", "OK" if venv and Path(sys.prefix).resolve() == alvo else "AVISO", sys.prefix)
    from importlib import metadata
    lock = {}
    for linha in (AMB / "requirements.lock.txt").read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)", linha)
        if m:
            lock[m.group(1).lower().replace("_", "-")] = m.group(2)
    diretos = [l.split("==")[0].strip().lower() for l in (AMB / "requirements.in").read_text().splitlines()
               if l.strip() and not l.startswith("#")]
    falt = incomp = 0
    for nome, ver in sorted(lock.items()):
        try:
            inst = metadata.version(nome)
        except metadata.PackageNotFoundError:
            falt += 1
            reg("pacotes python", nome, "AUSENTE", f"esperado {ver}")
            continue
        if inst != ver:
            incomp += 1
            reg("pacotes python", nome, "INCOMPATÍVEL", f"{inst} (esperado {ver})")
        elif nome in diretos:
            reg("pacotes python", nome, "OK", inst)
    reg("pacotes python", f"lock completo ({len(lock)} pacotes)", "OK" if not (falt or incomp) else "INCOMPATÍVEL",
        f"{falt} ausentes, {incomp} com versão diferente")


def fontes():
    c, out = cmd([sys.executable, str(AMB / "fontes.py"), "--verificar"])
    for linha in out.splitlines():
        st, nome = linha.split(maxsplit=1)
        reg("fontes", nome, st)


def funcionais():
    tmp = Path(tempfile.mkdtemp(prefix="mc_verif_"))
    # Blender
    try:
        t = time.time()
        import bpy
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        bpy.ops.mesh.primitive_cube_add(size=1)
        bpy.ops.object.light_add(type="SUN", location=(2, -2, 3))
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        sc.collection.objects.link(cam); sc.camera = cam
        cam.location = (3, -3, 2.5); cam.rotation_euler = (1.1, 0, 0.78)
        sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 8
        sc.render.resolution_x, sc.render.resolution_y = 135, 240
        sc.render.filepath = str(tmp / "cycles.png")
        bpy.ops.render.render(write_still=True)
        ok = (tmp / "cycles.png").exists()
        reg("teste funcional", f"Blender {bpy.app.version_string} · Cycles CPU", "OK" if ok else "INCOMPATÍVEL", f"{time.time()-t:.1f} s")
    except Exception as e:
        reg("teste funcional", "Blender · Cycles CPU", "INCOMPATÍVEL", str(e)[:120])
    # skia + fontes oficiais + OCR
    try:
        import skia
        surf = skia.Surface(900, 260)
        cv = surf.getCanvas(); cv.clear(skia.Color(61, 128, 216))
        nun = skia.Font(skia.Typeface.MakeFromFile(str(RAIZ / "assets/fontes/Nunito-ExtraBold.ttf")), 90)
        rob = skia.Font(skia.Typeface.MakeFromFile(str(RAIZ / "assets/fontes/RobotoCondensed-ExtraBold.ttf")), 80)
        p = skia.Paint(AntiAlias=True, Color=skia.Color(242, 239, 232))
        cv.drawString("Modo", 40, 110, nun, p)
        p.setColor(skia.Color(255, 194, 31)); cv.drawString("Curioso", 40 + nun.measureText("Modo "), 110, nun, p)
        p.setColor(skia.ColorWHITE); cv.drawString("MODO CURIOSO", 40, 225, rob, p)
        surf.makeImageSnapshot().save(str(tmp / "skia.png"))
        reg("teste funcional", f"skia {skia.__version__} · texto com fontes oficiais", "OK")
        try:
            from rapidocr_onnxruntime import RapidOCR
            txt = " ".join(x[1] for x in (RapidOCR()(str(tmp / "skia.png"))[0] or []))
            ok = "Curioso" in txt and "CURIOSO" in txt
            reg("teste funcional", "OCR (RapidOCR)", "OK" if ok else "AVISO", f"leu: {txt}")
        except Exception as e:
            reg("teste funcional", "OCR (RapidOCR)", "INCOMPATÍVEL", str(e)[:120])
    except Exception as e:
        reg("teste funcional", "skia · texto", "INCOMPATÍVEL", str(e)[:120])
    # FFmpeg 1080x1920 H.264 + AAC
    out = tmp / "teste.mp4"
    c, msg = cmd(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=1",
                  "-f", "lavfi", "-i", "sine=f=440:d=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                  "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)], timeout=120)
    if c == 0:
        info = cmd(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height,codec_name",
                    "-of", "csv=p=0", str(out)])[1]
        reg("teste funcional", "FFmpeg · 1080×1920 H.264/AAC", "OK" if "1080,1920" in info else "INCOMPATÍVEL", info)
    else:
        reg("teste funcional", "FFmpeg · 1080×1920 H.264/AAC", "INCOMPATÍVEL", msg[:120])
    # librosa (áudio extraído em WAV, como no pipeline) + OpenCV
    try:
        import librosa
        cmd(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-ac", "1", "-ar", "16000", str(tmp / "teste.wav")])
        y, sr = librosa.load(str(tmp / "teste.wav"), sr=16000)
        reg("teste funcional", f"librosa {librosa.__version__} · leitura de áudio", "OK" if len(y) > 10000 else "INCOMPATÍVEL", f"{len(y)/sr:.1f} s")
    except Exception as e:
        reg("teste funcional", "librosa · leitura de áudio", "INCOMPATÍVEL", str(e)[:120])
    try:
        import cv2
        cap = cv2.VideoCapture(str(out)); ok, fr = cap.read()
        reg("teste funcional", f"OpenCV {cv2.__version__} · leitura de vídeo", "OK" if ok and fr.shape[:2] == (1920, 1080) else "INCOMPATÍVEL")
    except Exception as e:
        reg("teste funcional", "OpenCV · leitura de vídeo", "INCOMPATÍVEL", str(e)[:120])
    shutil.rmtree(tmp, ignore_errors=True)


def rede():
    import urllib.request
    alvos = {
        "pypi.org": ("https://pypi.org/simple/", "instalar pacotes Python"),
        "raw.githubusercontent.com": ("https://raw.githubusercontent.com/google/fonts/main/ofl/nunito/OFL.txt", "recriar fontes"),
        "api.elevenlabs.io": ("https://api.elevenlabs.io/v1/models", "voz (TTS)"),
        "huggingface.co": ("https://huggingface.co/api/models?limit=1", "Whisper (opcional)"),
        "kenney.nl": ("https://kenney.nl/", "modelos 3D CC0"),
        "polyhaven.com": ("https://polyhaven.com/", "modelos 3D CC0"),
    }
    for host, (url, uso) in alvos.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "studio-check/1.0"})
            code = urllib.request.urlopen(req, timeout=15).status
            reg("rede", host, "OK", f"HTTP {code} · {uso}")
        except urllib.error.HTTPError as e:
            # 401/403 do próprio serviço = alcançável (sem credencial)
            bloq = "no rule or network setting allows" in (e.read().decode(errors="ignore") or "")
            reg("rede", host, "AVISO" if bloq else "OK", f"{'bloqueado pela rede' if bloq else 'alcançável'} (HTTP {e.code}) · {uso}")
        except Exception as e:
            motivo = "bloqueado pela rede do ambiente (liberar o host nas configurações)" if "403" in str(e) else f"inacessível ({str(e)[:60]})"
            reg("rede", host, "AVISO", f"{motivo} · {uso}")


def git():
    c, out = cmd(["git", "-C", str(RAIZ), "rev-parse", "--abbrev-ref", "HEAD"])
    reg("repositório", "branch", "OK" if c == 0 else "AVISO", out)
    c, out = cmd(["git", "-C", str(RAIZ), "lfs", "ls-files"])
    reg("repositório", "arquivos LFS", "OK" if c == 0 else "AVISO", f"{len(out.splitlines())} arquivos" if c == 0 else out[:60])


def main():
    sistema(); binarios(); python_e_pacotes(); fontes(); git()
    if "--rapido" not in sys.argv:
        funcionais()
    if "--rede" in sys.argv:
        rede()
    larg = max(len(r["item"]) for r in R)
    grupo = None
    for r in R:
        if r["grupo"] != grupo:
            grupo = r["grupo"]; print(f"\n[{grupo}]")
        print(f"  {r['status']:<13} {r['item']:<{larg}}  {r['detalhe']}")
    cont = {s: sum(1 for r in R if r["status"] == s) for s in ["OK", "AVISO", "AUSENTE", "INCOMPATÍVEL"]}
    print("\nResumo:", " · ".join(f"{k}: {v}" for k, v in cont.items()))
    (RAIZ / "_tmp").mkdir(exist_ok=True)
    (RAIZ / "_tmp" / "verificacao.json").write_text(json.dumps({"resultados": R, "resumo": cont}, ensure_ascii=False, indent=1))
    falhou = cont["AUSENTE"] or cont["INCOMPATÍVEL"]
    print("RESULTADO:", "FALHOU (corrija os itens AUSENTE/INCOMPATÍVEL)" if falhou else "AMBIENTE PRONTO")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()
