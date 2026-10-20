import json, re, subprocess, sys
S="/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/cam1"
LINES=[
"Uzak, sessiz bir yolda küçük lama Koro yürüyormuş.",
"Yolun öbür yanına geçmek istiyormuş.",
"Bir sağa bakmış, bir sola bakmış.",
"\"Acaba geçebilir miyim?\" diye düşünmüş.",
"Cesaretini toplayıp minik toynağını yola uzatmış.",
"Ama içi titremiş, hemen geri çekmiş.",
"Derin bir nefes alıp yeniden denemeye karar vermiş.",
"Tam o sırada, vınnn! Bir araba çıkagelmiş.",
"Koro havalara uçmuş!",
"Hop, yuvarlanmış, pat diye yere düşmüş.",
"Başı aşağıda, ayakları havada kalakalmış.",
"Çok şaşırmış, değil mi çocuklar?",
"Sonra toparlanıp tozun içinden koşmaya başlamış.",
"Yola bir daha bakmış, biraz korkmuş ama pes etmemiş.",
"Bir sonraki masalda görüşmek üzere!",
]
# silence segments
r=subprocess.run(["ffmpeg","-v","info","-i",f"{S}/narr.wav","-af","silencedetect=n=-38dB:d=0.15","-f","null","-"],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r"silence_start: ([\d.\-e]+)",r)]
en=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",r)]
DUR=54.4
sil=[]
for i,s in enumerate(st):
    e=en[i] if i<len(en) else DUR
    sil.append((max(s,0),e))
segs=[]; prev=0.0
for s,e in sil:
    if s-prev>0.08: segs.append((prev,s))
    prev=e
if DUR-prev>0.1: segs.append((prev,DUR))
V=set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")
def syl(w):
    core=re.sub(r"[^\wçğıöşüâîûÇĞİÖŞÜÂÎÛ']","",w)
    n=sum(1 for c in core if c in V)
    return max(n,1)
words=[]; 
for li,l in enumerate(LINES):
    for t in l.split():
        end=0
        if re.search(r'(\.\.\.|[.!?])$',t): end=2
        elif re.search(r'[,:]$',t): end=1
        words.append(dict(t=t,line=li,syl=syl(t),end=end))
tot_speech=sum(b-a for a,b in segs); tot_syl=sum(w['syl'] for w in words); rate=tot_syl/tot_speech
print("segs",len(segs),"words",len(words),"syl",tot_syl,"speech",round(tot_speech,1),"rate",round(rate,2))
N=len(segs); M=len(words); INF=1e18
best=[[INF]*(M+1) for _ in range(N+1)]; back=[[None]*(M+1) for _ in range(N+1)]
best[0][0]=0
cum=[0]
for w in words: cum.append(cum[-1]+w['syl'])
for i in range(N):
    a,b=segs[i]; dur=b-a
    for j in range(M):
        if best[i][j]>=INF: continue
        for L in range(1,14):
            jj=j+L
            if jj>M: break
            sy=cum[jj]-cum[j]; e=sy/rate
            c=((dur-e)**2)/(0.04+0.06*e)
            c+=6.0*sum(1 for w in words[j:jj-1] if w['end']==2)
            le=words[jj-1]['end']
            if jj<M: c+= 0.0 if le==2 else (0.4 if le==1 else 1.6)
            v=best[i][j]+c
            if v<best[i+1][jj]: best[i+1][jj]=v; back[i+1][jj]=j
print("cost",round(best[N][M],2))
al=[]; i=N; j=M
while i>0:
    pj=back[i][j]; al.append((i-1,pj,j)); i-=1; j=pj
al.reverse()
for si,j0,j1 in al:
    a,b=segs[si]; sy=cum[j1]-cum[j0]
    print(f"{si:3d} {a:7.2f}-{b:7.2f} ({b-a:4.2f}s {sy/(b-a):4.1f}/s) L{words[j0]['line']+1:02d}-{words[j1-1]['line']+1:02d}: {' '.join(w['t'] for w in words[j0:j1])}")
json.dump(dict(al=al,segs=segs,words=words),open(f"{S}/align.json","w"),ensure_ascii=False)
