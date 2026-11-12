# usage: python3 sfx.py out.wav  -- soft pad + beat + sfx; event times match scene_tab.html timeline (edit EVENTS for new scenes)
import sys, numpy as np, wave
sr=44100; T=15.0; n=int(sr*T); out=np.zeros(n); rng=np.random.default_rng(1)
def add(sig,at,g=1.0):
    i=int(at*sr); j=min(n,i+len(sig)); out[i:j]+=sig[:j-i]*g
chords=[[261.6,329.6,392.0],[220.0,261.6,329.6],[174.6,220.0,261.6],[196.0,246.9,293.7]]
for k in range(8):
    c=chords[k%4]; d=1.875; tt=np.arange(int(d*sr))/sr
    s=sum(np.sin(2*np.pi*f*tt)+0.3*np.sin(4*np.pi*f*tt) for f in c)/6
    add(s*np.minimum(1,tt/0.3)*np.minimum(1,(d-tt)/0.3),k*d,0.10)
for b in np.arange(0,15,0.46875):
    tt=np.arange(int(0.25*sr))/sr; f=55+90*np.exp(-tt*30); add(np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-tt*14),b,0.32)
    h=rng.standard_normal(int(0.04*sr))*np.exp(-np.linspace(0,8,int(0.04*sr))); add(np.diff(h,prepend=0),b+0.234,0.06)
def whoosh(d=0.6):
    m=int(d*sr); x=np.convolve(rng.standard_normal(m),np.ones(30)/30,'same'); return x*np.sin(np.pi*np.linspace(0,1,m))**2
def click(): m=int(0.05*sr); return rng.standard_normal(m)*np.exp(-np.linspace(0,10,m))
def pop(f=880): tt=np.arange(int(0.18*sr))/sr; return np.sin(2*np.pi*(f+600*np.exp(-tt*25))*tt)*np.exp(-tt*22)
def chime(): tt=np.arange(int(1.2*sr))/sr; return sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*(3+i)) for i,f in enumerate([1046,1318,1568,2093]))/3
def oops(): tt=np.arange(int(0.35*sr))/sr; return np.sin(2*np.pi*(420-220*tt/0.35)*tt)*np.exp(-tt*5)
EVENTS=[(whoosh(1.2),0.0,0.25),(click(),2.25,0.5),(oops(),2.6,0.35),(pop(700),2.7,0.35),(whoosh(0.7),4.1,0.35),(chime()[:int(0.5*sr)],4.9,0.25),
 (whoosh(0.5),6.8,0.25),(pop(600),7.05,0.45),(pop(800),7.95,0.45),(pop(1000),8.85,0.45),(click(),9.48,0.7),(click(),9.52,0.7),(click(),9.56,0.7),
 (chime(),10.05,0.5),(pop(990),11.0,0.3),(whoosh(0.8),13.15,0.3),(chime(),13.3,0.3)]
for s,a,g in EVENTS: add(s,a,g)
out[-int(0.8*sr):]*=np.linspace(1,0,int(0.8*sr)); out=out/np.max(np.abs(out))*0.8
st=np.stack([out,out],1); w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st*32767).astype('<i2').tobytes()); w.close()
