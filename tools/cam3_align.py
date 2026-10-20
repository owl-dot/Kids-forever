import json, re, subprocess, sys
S="/tmp/claude-0/-home-claude/5cd46ef5-d7e0-5655-905e-b2411ffe9769/scratchpad/cam3"
LINES=[
"Karlı Patagonya'da soğuk bir kış sabahı. Küçük lama Koro çok acıkmıştı.",
"Buzun üstünde minik kırmızı bir çiçek görür ve hemen koşar. Ama kayar, kayar ve pat! Buzun üstüne yüzüstü yapışır.",
"Tam o sırada minik bir penguen, Oti, kayarak yanına gelir.",
"Hop! Çiçeği kapıp götürür. Koro bu işe çok bozulur.",
"Oti çiçeği alıp tren rayına kaçar.",
"Derken uzaktan çuf çuf bir tren gelir!",
"Koro çok korkar.",
"Tren gelir, gelir, gelir... Vuuuş! Tren bir anda geçer gider. Koro şaşkın şaşkın etrafına bakar.",
"Oti ise yine ortaya çıkar. Havada kırmızı bir meyve uçar. Koro dilini uzatıp yakalamaya çalışır.",
"Sonra ikisi karanlık bir madene düşer. Orada tepede sarkan kırmızı meyveleri görürler.",
"Küçük bir madenci arabasına binerler. Araba hızla iner, sallanır ve çat!",
"Dışarı fırlarlar. Meyveler de arabadadır, Koro çok sevinir.",
"Ama araba dağın kenarından fırlar ve Koro havada uçar, uçar, uçar. Bulutların arasından geçer.",
"Sonunda yumuşacık karın içine düşer. Pat! Oti de sırtındadır.",
"Sonra Oti sessizce uzaklaşır.",
"Koro yalnız kalır, düşünceli ve üzgündür.",
"Akşam olur. Deniz kenarında, fenerli bir uçurumda Koro tek başına oturur. Karnı da çok açtır.",
"Birden Oti çıkagelir! Kollarında kırmızı meyveler var. Arkasında bütün penguenler de meyve getiriyor!",
"Koro çok mutlu olur. Meyveler, balıklar, koca bir ziyafet! Birlikte yerler.",
"Fenerin ışığı da onlara gülümser. Ve böylece Koro'nun yeni bir arkadaşı olur.",
"Bir sonraki masalda görüşmek üzere!",
]
# silence segments
r=subprocess.run(["ffmpeg","-v","info","-i",f"{S}/narr.wav","-af","silencedetect=n=-38dB:d=0.15","-f","null","-"],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r"silence_start: ([\d.\-e]+)",r)]
en=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",r)]
DUR=115.2
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
        for L in range(1,22):
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
