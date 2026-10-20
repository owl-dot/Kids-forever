import json, subprocess, wave, struct, math
S="/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/cam1"
V=f"{S}/film.mp4"; A=f"{S}/narr.wav"
VID=90.0
# (label, src_start, src_end, dest_time)
P=[
("L1 Uzak sessiz yolda",0.00,4.26,7.0),
("L2 Yolun oburu",5.00,7.34,12.5),
("L3 Sag sol",7.96,10.24,17.0),
("L4 Acaba gecebilir",11.16,13.63,21.0),
("L5 Cesaret toynak",14.42,18.14,27.3),
("L6 Ici titremis",18.65,21.42,33.8),
("L7 Derin nefes",22.19,27.27,39.0),
("L8 vinnn araba",27.73,30.54,45.0),
("L9 Koro ucmus",31.20,32.78,48.4),
("L10 Hop pat",33.04,35.99,50.4),
("L11 Basi asagida",36.50,39.68,54.0),
("L12 Sasirmis",40.40,42.16,59.0),
("L13 Tozun icinden",42.96,46.43,66.5),
("L14 Yola bir daha",46.97,50.84,81.9),
("L15 Bir sonraki",51.58,54.21,86.6),
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
LOUD=('L3','L6','L13')
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
 "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",f"{S}/Caminandes1_Turkce.mp4",
 "-map","[narrout]","-c:a","aac","-b:a","160k",f"{S}/Caminandes1_Turkce_ses.m4a",
 "-map","[narrchk]","-c:a","pcm_s16le",f"{S}/chk_narr.wav","-map","[bedchk]","-c:a","pcm_s16le",f"{S}/chk_bed.wav"]
r=subprocess.run(cmd,capture_output=True,text=True)
print("rc",r.returncode); print(r.stderr[-1200:])
