#!/usr/bin/env python3
"""Build a 1080x1920 YouTube Short: blurred bg + film clip + hook text + subscribe end card.
usage: short_build.py <key> [<key>...]   (or 'all')"""
import subprocess, sys, os, json
from PIL import Image, ImageDraw, ImageFont
exec(open("/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/shorts_src.py").read())
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
OUT = "/home/claude/kids-forever/out/"
TMP = S + "shorts/build/"
os.makedirs(TMP, exist_ok=True); os.makedirs(OUT, exist_ok=True)

# key: (src, start, hook line1, hook line2, film-audio bed?)
SH = {
 "bbb":   ("bbb", 100, "TAVŞANIN HAVUCU", "KİMİN OLACAK?", True),
 "cam3":  ("cam3", 14, "LAMA BUZDA KAYIYOR...", "TREN GELİYOR!", True),
 "wing":  ("wing", 7, "KIRMIZI DÜĞMEYE", "BASARSAN?", True),
 "sp1":   ("spring1", 30, "KARANLIK ORMANDA", "GARİP BİR IŞIK!", True),
 "sp2":   ("spring2", 85, "TOPRAĞIN ALTINDA", "NE SAKLI?", True),
 "sp3":   ("spring3", 48, "FİNALDE SENİ", "KİM BEKLİYOR?", True),
 "cam1":  ("cam1", 14, "LAMA YOLU", "GEÇEBİLECEK Mİ?", True),
 "glass": ("glass", 20, "BARDAK YARI BOŞ MU,", "YARI DOLU MU?", True),
 "sing1": ("sing1", 60, "UZAYDA YALNIZ", "BİR YILDIZ", True),
 "sing2": ("sing2", 28, "GÖKYÜZÜNDE GARİP", "IŞIKLAR DANS EDİYOR", True),
 "coffee":("coffee", 17, "KAHVE İÇİN", "KOŞUŞTURMACA!", True),
 "pebble":("pebble", 36, "KÜÇÜK ÇAKIL", "NEREYE GİDİYOR?", True),
 "krazy": ("krazy", 57, "KEDİ ARIYI", "YAKALAYABİLECEK Mİ?", False),
 "fanta": ("fanta", 10, "DÜNYANIN İLK", "ÇİZGİ FİLMLERİNDEN!", False),
}
def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit(1)
    return r.stdout
def dur(p): return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
def has_audio(p): return "audio" in run(["ffprobe","-v","error","-show_entries","stream=codec_type","-of","csv=p=0",p])
def fit(d, text, font_path, maxw, size):
    while True:
        f = ImageFont.truetype(font_path, size)
        if d.textlength(text, font=f) <= maxw or size < 30: return f
        size -= 2
def stroke_text(d, xy, text, f, fill, stroke=(10,20,60), sw=8):
    d.text((xy[0]+4, xy[1]+6), text, font=f, fill=(0,0,0,150), anchor="mm", stroke_width=sw, stroke_fill=(0,0,0,150))
    d.text(xy, text, font=f, fill=fill, anchor="mm", stroke_width=sw, stroke_fill=stroke)

def make_overlays(k, l1, l2):
    hook = Image.new("RGBA", (1080, 1920), (0,0,0,0)); d = ImageDraw.Draw(hook)
    f1 = fit(d, l1, FONT, 980, 92); f2 = fit(d, l2, FONT, 980, 92)
    stroke_text(d, (540, 300), l1, f1, (255,221,0))
    stroke_text(d, (540, 410), l2, f2, (255,255,255))
    fb = ImageFont.truetype(FONT, 46)
    stroke_text(d, (540, 1560), "TAM VİDEO KANALIMIZDA", fb, (255,255,255), sw=6)
    fc = ImageFont.truetype(FONT, 40)
    stroke_text(d, (540, 1625), "Kids forever", fc, (255,221,0), sw=6)
    hook.save(TMP+k+"_hook.png")
    end = Image.new("RGBA", (1080, 1920), (0,0,0,0)); d = ImageDraw.Draw(end)
    d.rectangle([0,0,1080,1920], fill=(8,14,40,170))
    d.rounded_rectangle([90, 700, 990, 940], radius=60, fill=(230,30,40,255), outline=(255,255,255,255), width=8)
    fa = fit(d, "ABONE OL", FONT, 800, 150)
    d.text((540, 820), "ABONE OL", font=fa, fill=(255,255,255), anchor="mm")
    f3 = ImageFont.truetype(FONT, 66)
    stroke_text(d, (540, 1060), "Tam videoyu izle!", f3, (255,221,0), sw=8)
    f4 = ImageFont.truetype(FONT, 44)
    stroke_text(d, (540, 1150), "Kids forever", f4, (255,255,255), sw=6)
    end.save(TMP+k+"_end.png")

def build(k):
    src, st, l1, l2, bed = SH[k]
    film = SRC[src]
    narr = R+"sv_"+("bbb" if k=="bbb" else k)+"/narr.mp3"
    nd = dur(narr)
    D = round(nd + 1.2, 2)
    if D > 29.5: D = 29.5
    endst = max(D - 5.5, 0)
    make_overlays(k, l1, l2)
    out = OUT+f"Short_{k}.mp4"
    fa = has_audio(film) and bed
    # inputs: 0 film, 1 narr, 2 hook, 3 end
    inp = ["-ss", str(st), "-t", str(D), "-i", film, "-i", narr, "-loop","1","-t",str(D),"-i",TMP+k+"_hook.png","-loop","1","-t",str(D),"-i",TMP+k+"_end.png"]
    vf = (f"[0:v]split=2[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3,eq=brightness=-0.15[bg];"
          f"[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v1];"
          f"[v1][2:v]overlay=0:0[v2];[v2][3:v]overlay=0:0:enable='gte(t,{endst})'[v]")
    nf = f"[1:a]loudnorm=I=-14:TP=-1.5:LRA=7,apad,atrim=0:{D},asetpts=PTS-STARTPTS[n]"
    if fa:
        af = nf + f";[0:a]volume=0.17,afade=t=in:d=0.5,afade=t=out:st={D-1.5}:d=1.5,atrim=0:{D}[f];[n][f]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[aout]"
    else:
        af = nf + ";[n]alimiter=limit=0.89[aout]"
    fc = vf + ";" + af
    run(["ffmpeg","-y","-v","error",*inp,"-filter_complex",fc,"-map","[v]","-map","[aout]","-t",str(D),
         "-c:v","libx264","-crf","22","-preset","medium","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","160k","-movflags","+faststart",out])
    m = subprocess.run(["ffmpeg","-v","info","-i",out,"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    li = [l for l in m.splitlines() if "I:" in l and "LUFS" in l][-1:] or [""]
    print(k, "dur", D, "narr", round(nd,1), "film_audio", fa, li[0].strip(), os.path.getsize(out)//1024, "KB")
    # preview frames
    for t,nm in ((2,"a"),(D-3,"b")):
        run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",out,"-frames:v","1","-vf","scale=360:-2",TMP+f"{k}_{nm}.jpg"])

if __name__ == "__main__":
    ks = list(SH) if sys.argv[1:] == ["all"] else sys.argv[1:]
    for k in ks: build(k)
