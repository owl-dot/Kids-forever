import json, subprocess, wave, struct, math, sys
S="/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/sing"
K=int(sys.argv[1])
starts={1:0.0,2:197.458}; ends={1:197.458,2:391.0417}
T0=starts[K]; VID=ends[K]-T0
# film-time destinations per line (1-based line no.)
DEST={1:6.0,2:15.0,3:28.0,4:33.0,5:40.0,6:48.0,7:55.0,8:65.3,9:70.8,10:77.0,11:83.5,12:91.0,13:104.0,14:112.0,15:119.0,16:125.5,17:134.0,18:143.0,19:151.0,20:159.0,21:170.0,22:186.5,23:199.0,24:206.0,25:216.0,26:227.5,27:232.0,28:239.0,29:245.0,30:251.0,31:262.0,32:268.5,33:274.0,34:282.0,35:289.0,36:298.0,37:308.0,38:317.5,39:322.0,40:329.0,41:336.0,42:344.0}
rng={1:range(1,23),2:range(23,43)}[K]
al=json.load(open(f"{S}/align.json")); segs=al['segs']; words=al['words']
ls={}
for si,j0,j1 in al['al']:
    a,b=segs[si]
    for ln in {words[j]['line']+1 for j in range(j0,j1)}:
        ls.setdefault(ln,[a,b]); ls[ln][0]=min(ls[ln][0],a); ls[ln][1]=max(ls[ln][1],b)
LOUD=set(json.load(open(f"{S}/loud.json"))) if len(sys.argv)>2 else set()
P=[(f"L{ln}",ls[ln][0],ls[ln][1],round(DEST[ln]-T0,3)) for ln in rng]
iv=sorted([(d,d+(e-s),n) for n,s,e,d in P])
for (a1,b1,n1),(a2,b2,n2) in zip(iv,iv[1:]): assert b1<=a2-0.2,(n1,n2,round(b1,2),a2)
assert iv[-1][1]<VID-0.3,(iv[-1],VID)
V=f"{S}/part{K}_film.mp4"; A=f"{S}/narr.wav"
w=wave.open(A); sr=w.getframerate(); raw=w.readframes(w.getnframes()); x=struct.unpack('<%dh'%(len(raw)//2),raw)
TARGET=-14.0
def rms_db(s,e):
    seg=x[int(s*sr):int(e*sr)]; blk=int(0.03*sr); vals=[]
    for i in range(0,len(seg)-blk,blk):
        b=seg[i:i+blk]; r=math.sqrt(sum(v*v for v in b)/blk)/32768
        if r>10**(-45/20): vals.append(r*r)
    return 10*math.log10(sum(vals)/len(vals)) if vals else -60
G={}
for n,s,e,d in P:
    r=rms_db(s,e); G[n]=max(-3.0,min(12.0,TARGET-r))
    if n in LOUD: G[n]=min(14.0,G[n]+2.0)
DUCK=0.80
terms=[f"clip(min((t-{a-0.25:.3f})/0.25\\,({b+0.45:.3f}-t)/0.45)\\,0\\,1)" for a,b,n in iv]
expr=terms[0]
for t in terms[1:]: expr=f"max({expr}\\,{t})"
vol=f"volume=volume='1-{DUCK}*{expr}':eval=frame"
n=len(P)
fc=[f"[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit={n}"+"".join(f"[s{i}]" for i in range(n))]
for i,(name,s,e,d) in enumerate(P):
    dur=e-s; ms=int(round(d*1000))
    fc.append(f"[s{i}]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,volume={G[name]:.2f}dB,afade=t=in:st=0:d=0.02,afade=t=out:st={dur-0.06:.3f}:d=0.06,adelay={ms}|{ms}[p{i}]")
fc.append("".join(f"[p{i}]" for i in range(n))+f"amix=inputs={n}:normalize=0:dropout_transition=0,alimiter=limit=0.80:attack=5:release=60:level=disabled,apad,atrim=end={VID:.3f},asplit=2[narr][narrchk]")
fc.append(f"[0:a]aresample=44100,{vol},asplit=2[bed][bedchk]")
fc.append("[bed][narr]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84:attack=5:release=80:level=disabled[aout]")
open(f"{S}/fc{K}.txt","w").write(";\n".join(fc))
json.dump(P,open(f"{S}/place{K}.json","w"),indent=1)
out=f"{S}/Singularity_Bolum{K}.mp4"
cmd=["ffmpeg","-nostdin","-hide_banner","-y","-i",V,"-i",A,"-filter_complex_script",f"{S}/fc{K}.txt",
 "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",out,
 "-map","[narrchk]","-c:a","pcm_s16le",f"{S}/chk_narr{K}.wav","-map","[bedchk]","-c:a","pcm_s16le",f"{S}/chk_bed{K}.wav"]
r=subprocess.run(cmd,capture_output=True,text=True)
print("part",K,"rc",r.returncode,"len",round(VID,1)); 
if r.returncode: print(r.stderr[-1500:])
