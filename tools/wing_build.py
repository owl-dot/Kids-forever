import json, subprocess, wave, struct, math
S="/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/wing"
V=f"{S}/film.mp4"; A=f"{S}/narr.wav"
VID=238.02
# (label, src_start, src_end, dest_time)
P=[
('L1 Bir varmis',0.0,6.06,5.8),
('L2 Adi Pamuk',6.49,11.19,12.11),
('L3 Gemi yamali',11.61,15.52,17.06),
('L4 Listesine',16.09,19.56,21.22),
('L5 Kapidan kopek',20.12,23.53,24.94),
('L6 Adi Fistik',23.86,28.95,28.6),
('L7 Kalp kalp',29.7,33.19,39.2),
('L8 Ben de binmek',33.65,35.68,43.2),
('L9 Dur dur',36.12,42.43,45.6),
('L11 Dugmelere',42.78,48.13,52.2),
('L12 Kirmizi dugme',48.5,51.17,66.0),
('L13 Sakin basma',51.73,54.28,69.5),
('L14 Bam',54.83,58.02,86.8),
('L15 Gokyuzune',58.49,61.08,91.0),
('L16 Alarm',61.59,65.28,96.0),
('L17 Korkudan',65.79,71.06,104.0),
('L18 Yamalar',71.61,75.54,109.6),
('L19a Kolu cekmis',75.96,77.38,119.5),
('L19b Makasla',77.78,80.33,133.6),
('L20 Kanatlar',80.68,83.74,139.8),
('L21 Suzulmeye',84.12,87.57,143.5),
('L22 Gulumsemis',88.02,91.62,150.0),
('L23 Yesil kirlar',91.97,94.03,160.5),
('L24 Pat',94.57,98.11,164.5),
('L25 Sapasaglam',98.74,101.82,168.4),
('L26 Liste tik',102.24,107.18,171.8),
('L27 Yeni arkadas',107.73,112.06,177.2),
('L28 Bir sonraki',112.42,116.38,182.0),
]
iv=sorted([(d,d+(e-s),n) for n,s,e,d in P])
for (a1,b1,n1),(a2,b2,n2) in zip(iv,iv[1:]):
    assert b1<=a2-0.2,(n1,n2,round(b1,2),a2)
assert iv[-1][1]<VID-0.3
json.dump(P,open(f"{S}/placements.json","w"),ensure_ascii=False,indent=1)
# per-cue gain: normalise speech RMS to TARGET
w=wave.open(A); sr=w.getframerate(); raw=w.readframes(w.getnframes())
x=struct.unpack('<%dh'%(len(raw)//2),raw)
TARGET=-14.0
def rms_db(s,e):
    seg=x[int(s*sr):int(e*sr)]; blk=int(0.03*sr); vals=[]
    for i in range(0,len(seg)-blk,blk):
        b=seg[i:i+blk]; r=math.sqrt(sum(v*v for v in b)/blk)/32768
        if r>10**(-45/20): vals.append(r*r)
    return 10*math.log10(sum(vals)/len(vals)) if vals else -60
G={}
for n,s,e,d in P:
    r=rms_db(s,e); G[n]=max(-3.0,min(12.0,TARGET-r)); print(f"{n:24s} rms {r:6.1f} gain {G[n]:+5.1f}")
DUCK=0.80
LOUD=('L9','L13','L14','L19a','L24')
for k in list(G):
    if k.split()[0] in LOUD: G[k]=min(14.0,G[k]+2.0)
terms=[f"clip(min((t-{a-0.25:.3f})/0.25\\,({b+0.45:.3f}-t)/0.45)\\,0\\,1)" for a,b,n in iv]
expr=terms[0]
for t in terms[1:]: expr=f"max({expr}\\,{t})"
vol=f"volume=volume='1-{DUCK}*{expr}':eval=frame"
n=len(P)
fc=[f"[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit={n}"+"".join(f"[s{i}]" for i in range(n))]
for i,(name,s,e,d) in enumerate(P):
    dur=e-s; ms=int(round(d*1000))
    fc.append(f"[s{i}]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,volume={G[name]:.2f}dB,afade=t=in:st=0:d=0.02,afade=t=out:st={dur-0.06:.3f}:d=0.06,adelay={ms}|{ms}[p{i}]")
fc.append("".join(f"[p{i}]" for i in range(n))+f"amix=inputs={n}:normalize=0:dropout_transition=0,alimiter=limit=0.80:attack=5:release=60:level=disabled,apad,atrim=end={VID:.3f},asplit=3[narr][narrout][narrchk]")
fc.append(f"[0:a]aresample=44100,{vol},asplit=2[bed][bedchk]")
fc.append("[bed][narr]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84:attack=5:release=80:level=disabled[aout]")
open(f"{S}/fc.txt","w").write(";\n".join(fc))
cmd=["ffmpeg","-nostdin","-hide_banner","-y","-i",V,"-i",A,"-filter_complex_script",f"{S}/fc.txt",
 "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",f"{S}/WingIt_Turkce.mp4",
 "-map","[narrout]","-c:a","aac","-b:a","160k",f"{S}/WingIt_Turkce_ses.m4a",
 "-map","[narrchk]","-c:a","pcm_s16le",f"{S}/chk_narr.wav","-map","[bedchk]","-c:a","pcm_s16le",f"{S}/chk_bed.wav"]
r=subprocess.run(cmd,capture_output=True,text=True)
print("rc",r.returncode); print(r.stderr[-1200:])
