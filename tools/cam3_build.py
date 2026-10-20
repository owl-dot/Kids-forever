import json, subprocess, wave, struct, math
S="/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/cam3"
V=f"{S}/film.mp4"; A=f"{S}/narr.wav"
VID=150.18
# (label, src_start, src_end, dest_time)
P=[
("L1a Karli Patagonya",0.00,2.81,3.3),
("L1b Kucuk lama Koro",3.31,5.50,6.4),
("L2a Buzun ustunde cicek",6.03,10.20,8.8),
("L2b Kayar pat",10.67,12.53,13.2),
("L2c Yuzustu",13.06,15.04,15.3),
("L3 Penguen Oti",15.60,19.65,18.0),
("L4a Hop cicegi kapar",19.93,21.95,22.4),
("L4b Koro bozulur",22.19,23.42,25.3),
("L5 Oti rayina kacar",23.80,26.97,27.0),
("L6 Tren gelir",27.26,29.73,31.0),
("L7 Koro korkar",30.19,31.18,34.0),
("L8a gelir gelir",31.56,33.45,39.0),
("L8b Vuus",33.72,34.40,42.6),
("L8c gecer gider",35.03,36.43,43.7),
("L8d Koro saskin",36.79,38.86,45.4),
("L9a Oti ortaya",39.25,41.21,47.7),
("L9b Havada meyve",41.48,43.51,50.4),
("L9c Dilini uzatir",43.97,47.17,52.7),
("L10a Madene duser",47.48,49.67,56.3),
("L10b Sarkan meyveler",49.95,53.65,59.6),
("L11a Madenci arabasi",54.05,56.19,63.6),
("L11b Cat",56.61,59.22,66.0),
("L12a Disari firlarlar",59.73,60.67,69.0),
("L12b Koro sevinir",61.18,63.69,70.3),
("L13a Ucar",64.20,69.55,74.0),
("L13b Bulutlar",69.89,71.41,83.2),
("L14a Kara duser",71.88,74.28,93.0),
("L14b Pat",74.79,75.09,95.7),
("L14c Oti sirtinda",75.47,76.97,96.5),
("L15 Oti uzaklasir",77.23,79.72,101.3),
("L16 Koro uzgun",80.12,83.09,104.2),
("L17a Aksam olur",83.45,84.10,111.6),
("L17b Deniz kenari",84.68,88.96,112.6),
("L17c Karni ac",89.55,90.64,117.2),
("L18a Birden Oti",91.15,92.26,118.8),
("L18b Kollarinda meyve",92.79,94.43,120.2),
("L18c Penguenler",94.83,97.96,122.4),
("L19a Koro mutlu",98.40,99.62,126.0),
("L19b Ziyafet",100.12,102.85,127.6),
("L19c Birlikte yerler",103.46,104.41,130.8),
("L20a Fener",105.04,107.64,134.0),
("L20b Yeni arkadas",107.99,111.56,137.0),
("L21 Bir sonraki masal",112.29,114.81,141.5),
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
    r=rms_db(s,e); G[n]=max(-3.0,min(9.0,TARGET-r)); print(f"{n:24s} rms {r:6.1f} gain {G[n]:+5.1f}")
DUCK=0.72
LOUD=('L6','L8a','L8b','L8c','L10a','L11b','L12a','L12b','L13a','L13b','L14a','L14b','L14c','L21')
for k in list(G):
    if k.split()[0] in LOUD: G[k]=min(11.0,G[k]+2.5)
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
fc.append("[bed][narr]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:attack=5:release=80:level=disabled[aout]")
open(f"{S}/fc.txt","w").write(";\n".join(fc))
cmd=["ffmpeg","-nostdin","-hide_banner","-y","-i",V,"-i",A,"-filter_complex_script",f"{S}/fc.txt",
 "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",f"{S}/Caminandes3_Turkce.mp4",
 "-map","[narrout]","-c:a","aac","-b:a","160k",f"{S}/Caminandes3_Turkce_ses.m4a",
 "-map","[narrchk]","-c:a","pcm_s16le",f"{S}/chk_narr.wav","-map","[bedchk]","-c:a","pcm_s16le",f"{S}/chk_bed.wav"]
r=subprocess.run(cmd,capture_output=True,text=True)
print("rc",r.returncode); print(r.stderr[-1200:])
