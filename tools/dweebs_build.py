import subprocess, wave, struct, math, json
S="/tmp/w/dw"; F="inbox/dweebs/film.mp4"
T0=2.7; END=50.6; VID=END-T0
# (line, seg_start, seg_end, film_time_orig)
P=[("L1",0.0,2.135,3.0),("L2",2.82,6.059,5.4),("L3",6.615,8.993,8.85),("L4",9.564,15.068,11.45),
   ("L5",15.43,18.456,17.25),("L6",18.71,20.336,20.5),("L7",20.69,25.026,24.0),("L8",25.61,29.931,32.0),
   ("L9",30.55,33.06,39.5),("L10",33.67,37.95,42.5)]
P=[(n,s,e,round(d-T0,3)) for n,s,e,d in P]
iv=sorted([(d,d+(e-s),n) for n,s,e,d in P])
for (a1,b1,n1),(a2,b2,n2) in zip(iv,iv[1:]): assert b1<=a2-0.2,(n1,n2,b1,a2)
assert iv[-1][1]<VID-0.3
w=wave.open(S+"/narr.wav"); sr=w.getframerate(); raw=w.readframes(w.getnframes()); x=struct.unpack('<%dh'%(len(raw)//2),raw)
def rms_db(s,e):
    seg=x[int(s*sr):int(e*sr)]; blk=int(0.03*sr); v=[]
    for i in range(0,len(seg)-blk,blk):
        b=seg[i:i+blk]; r=math.sqrt(sum(q*q for q in b)/blk)/32768
        if r>10**(-45/20): v.append(r*r)
    return 10*math.log10(sum(v)/len(v)) if v else -60
n=len(P); fc=[f"[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit={n}"+"".join(f"[s{i}]" for i in range(n))]
for i,(nm,s,e,d) in enumerate(P):
    g=max(-3,min(12,-16.3-rms_db(s,e))); ms=int(d*1000); du=e-s
    fc.append(f"[s{i}]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,volume={g:.2f}dB,afade=t=in:st=0:d=0.02,afade=t=out:st={du-0.06:.3f}:d=0.06,adelay={ms}|{ms}[p{i}]")
fc.append("".join(f"[p{i}]" for i in range(n))+f"amix=inputs={n}:normalize=0:dropout_transition=0,alimiter=limit=0.80:attack=5:release=60:level=disabled,apad,atrim=end={VID:.3f}[aout]")
open(S+"/fc.txt","w").write(";\n".join(fc))
cmd=["ffmpeg","-nostdin","-y","-loglevel","error","-ss",str(T0),"-t",f"{VID:.3f}","-i",F,"-i",S+"/narr.wav","-filter_complex_script",S+"/fc.txt",
 "-map","0:v","-map","[aout]","-c:v","libx264","-crf","24","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","out/Dweebs_Turkce.mp4"]
r=subprocess.run(cmd,capture_output=True,text=True); print(r.returncode,r.stderr[-800:])
