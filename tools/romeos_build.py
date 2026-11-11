import json, subprocess, wave, struct, math, sys
S="/tmp/w/o"
def nt(o): return (o-6.0)/1.5
# orig film-time destinations; group (14,15) shares segments
DEST={1:6,2:15,3:22,4:28,5:36,6:44,7:58,8:66,9:98,10:106,11:120,12:127,13:135,14:162,15:172,16:268,17:298,18:312,19:336,20:350}
al=json.load(open(f"{S}/align.json")); segs=al['segs']; words=al['words']
ls={}
for si,j0,j1 in al['al']:
    a,b=segs[si]
    for ln in {words[j]['line']+1 for j in range(j0,j1)}:
        ls.setdefault(ln,[a,b]); ls[ln][0]=min(ls[ln][0],a); ls[ln][1]=max(ls[ln][1],b)
P=[(f"L{ln}",ls[ln][0],ls[ln][1],round(nt(DEST[ln]),3)) for ln in sorted(DEST)]
VID=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"{S}/film_t.mp4"]))
iv=sorted([(d,d+(e-s),n) for n,s,e,d in P])
for (a1,b1,n1),(a2,b2,n2) in zip(iv,iv[1:]): assert b1<=a2-0.2,(n1,n2,round(b1,2),a2)
assert iv[-1][1]<VID-0.3,(iv[-1],VID)
w=wave.open(f"{S}/narr.wav"); sr=w.getframerate(); raw=w.readframes(w.getnframes()); x=struct.unpack('<%dh'%(len(raw)//2),raw)
def rms_db(s,e):
    seg=x[int(s*sr):int(e*sr)]; blk=int(0.03*sr); vals=[]
    for i in range(0,len(seg)-blk,blk):
        b=seg[i:i+blk]; r=math.sqrt(sum(v*v for v in b)/blk)/32768
        if r>10**(-45/20): vals.append(r*r)
    return 10*math.log10(sum(vals)/len(vals)) if vals else -60
n=len(P); fc=[f"[0:a]aresample=44100,asplit={n}"+"".join(f"[s{i}]" for i in range(n))]
for i,(name,s,e,d) in enumerate(P):
    g=max(-3.0,min(12.0,-14.0-rms_db(s,e))); dur=e-s; ms=int(round(d*1000))
    fc.append(f"[s{i}]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,volume={g:.2f}dB,afade=t=in:st=0:d=0.02,afade=t=out:st={dur-0.06:.3f}:d=0.06,adelay={ms}|{ms}[p{i}]")
fc.append("".join(f"[p{i}]" for i in range(n))+f"amix=inputs={n}:normalize=0:dropout_transition=0,alimiter=limit=0.80:attack=5:release=60:level=disabled,volume=-2dB,apad,atrim=end={VID:.3f},pan=stereo|c0=c0|c1=c0[aout]")
open(f"{S}/fc.txt","w").write(";\n".join(fc))
r=subprocess.run(["ffmpeg","-nostdin","-hide_banner","-y","-i",f"{S}/narr.wav","-i",f"{S}/film_t.mp4","-filter_complex_script",f"{S}/fc.txt","-map","1:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",f"{S}/Romeos_Turkce.mp4"],capture_output=True,text=True)
print("rc",r.returncode,"VID",VID); print(r.stderr[-800:] if r.returncode else "")
