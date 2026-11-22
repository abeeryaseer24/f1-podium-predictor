"""Formula 1 engines through the eras, for the Engine Room page and the Academy.

Figures are rounded, commonly published values (peak power varied by team, year and mode);
they are here to compare eras, not to settle arguments about any one engine.

The sound is synthesised in the visitor's browser from the engine's firing frequency:
    firing frequency (Hz) = rpm / 60 x cylinders / 2      (a four-stroke fires each cylinder every 2 turns)
A V10 at 18,000 rpm fires 1,500 times a second; a V6 at 11,000 rpm about 550. Turbochargers
and hybrid exhausts muffle the high harmonics, which is why the turbo eras sound deeper.
"""
import json

import numpy as np
import streamlit.components.v1 as components

ERAS = [
    {"name": "1.5 V6 turbo", "years": "1977–1988", "cylinders": 6, "litres": 1.5, "rpm_max": 12500, "rpm_idle": 4000,
     "power_hp": "about 900–1,300 in qualifying trim", "power_kw": 900, "turbo": True, "hybrid": False,
     "colour": "#e8b33a", "note": "The first turbo era: enormous boost in qualifying, fuel limits in the race."},
    {"name": "3.5 V12", "years": "1989–1994", "cylinders": 12, "litres": 3.5, "rpm_max": 15000, "rpm_idle": 5000,
     "power_hp": "about 700–800", "power_kw": 560, "turbo": False, "hybrid": False,
     "colour": "#c04dff", "note": "Turbos were banned; V12s, V10s and V8s raced side by side."},
    {"name": "3.0 V10", "years": "1995–2005", "cylinders": 10, "litres": 3.0, "rpm_max": 19000, "rpm_idle": 6000,
     "power_hp": "about 900–950 at the peak (2005)", "power_kw": 690, "turbo": False, "hybrid": False,
     "colour": "#e10600", "note": "The loudest and highest-revving era; from 2000 every team ran a V10."},
    {"name": "2.4 V8", "years": "2006–2013", "cylinders": 8, "litres": 2.4, "rpm_max": 18000, "rpm_idle": 6000,
     "power_hp": "about 750 (plus 80 hp KERS from 2009)", "power_kw": 560, "turbo": False, "hybrid": False,
     "colour": "#2b6cff", "note": "Rev limits (19,000 then 18,000) and an engine freeze to cut costs."},
    {"name": "1.6 V6 turbo hybrid", "years": "2014–2025", "cylinders": 6, "litres": 1.6, "rpm_max": 15000, "rpm_idle": 5000,
     "power_hp": "about 1,000 with the hybrid system", "power_kw": 750, "turbo": True, "hybrid": True,
     "colour": "#27f4d2", "note": "MGU-K and MGU-H; a fuel-flow limit made thermal efficiency the battleground."},
    {"name": "2026 V6 turbo hybrid", "years": "2026–", "cylinders": 6, "litres": 1.6, "rpm_max": 15000, "rpm_idle": 5000,
     "power_hp": "about 1,000 combined, roughly half electric", "power_kw": 750, "turbo": True, "hybrid": True,
     "colour": "#1fd6a0", "note": "No MGU-H, a 350 kW MGU-K, and 100 % sustainable fuel."},
]
TYPICAL_RPM = {"1.5 V6 turbo": 11500, "3.5 V12": 14000, "3.0 V10": 18500, "2.4 V8": 17800,
               "1.6 V6 turbo hybrid": 11500, "2026 V6 turbo hybrid": 11500}


def firing_hz(rpm, cylinders):
    return rpm / 60 * cylinders / 2


def lap_rpm(track_df, era):
    """An rpm trace for a real fastest lap, from its speed and gear, in this engine's rpm range.
    Each gear's top speed comes from the lap itself; rpm runs from about 70 % to the top of the
    engine's usual range within each gear."""
    speed = track_df["speed"].to_numpy(dtype=float)
    gear = track_df["n_gear"].clip(1, 8).to_numpy(dtype=int)
    t = track_df["s"].to_numpy(dtype=float)
    top = {g: max(speed[gear == g].max(), 1.0) if (gear == g).any() else 1.0 for g in range(1, 9)}
    hi = TYPICAL_RPM[era["name"]]
    rpm = np.array([hi * min(1.0, max(0.6, s / top[g])) for s, g in zip(speed, gear)])
    return t, rpm


def engine_sound(era, lap=None, height=170, dark=True):
    """Play button, rpm slider and a 'rev it' sweep, all synthesised in the browser."""
    data = {"era": era, "lap": lap, "dark": dark, "typical": TYPICAL_RPM[era["name"]]}
    components.html(SOUND.replace("__DATA__", json.dumps(data)), height=height)


SOUND = r"""<!doctype html><html><head><meta charset="utf-8"><style>
 body{margin:0;font-family:Inter,system-ui,sans-serif}
 #box{display:flex;flex-wrap:wrap;align-items:center;gap:12px;padding:14px;border-radius:16px;border:1px solid var(--b);background:var(--p);color:var(--t)}
 button{font:600 13px Inter,system-ui,sans-serif;padding:10px 16px;border-radius:999px;cursor:pointer;border:1px solid var(--b);background:var(--p2);color:var(--t)}
 button.on,#play{background:#e10600;border-color:#e10600;color:#fff}
 #rpm{flex:1;min-width:160px;accent-color:#e10600}
 #read{font:800 26px 'Saira Condensed',Inter,sans-serif;min-width:150px}
 #read small{display:block;font:600 11px Inter,sans-serif;color:var(--m)}
 #bar{height:8px;border-radius:4px;background:linear-gradient(90deg,#1fd6a0,#e8b33a,#e10600);width:0%;transition:width .05s}
 #barwrap{flex-basis:100%;height:8px;border-radius:4px;background:var(--p2)}
</style></head><body><div id="box">
 <button id="play">▶ Start engine</button><button id="rev">Rev it</button><span id="lapb"></span>
 <input id="rpm" type="range" min="0" max="1000" value="400" aria-label="Engine speed">
 <div id="read">0 rpm<small>firing 0 Hz</small></div><div id="barwrap"><div id="bar"></div></div>
</div><script>
const D=__DATA__, E=D.era;
const T=D.dark?{p:"#15151e",p2:"#1e1e29",b:"#2c2c3a",t:"#f5f5f7",m:"#a3a3b2"}:{p:"#ffffff",p2:"#ececea",b:"#d9d9d4",t:"#15151e",m:"#55556a"};
const box=document.getElementById("box");for(const[k,v]of Object.entries(T))box.style.setProperty("--"+k,v);
let ctx=null,nodes=null,rpm=E.rpm_idle,target=E.rpm_idle,lapT=null;
const slider=document.getElementById("rpm"),read=document.getElementById("read"),bar=document.getElementById("bar");
function fromSlider(){return E.rpm_idle+(E.rpm_max-E.rpm_idle)*slider.value/1000}
function build(){
  ctx=new (window.AudioContext||window.webkitAudioContext)();
  const out=ctx.createGain();out.gain.value=0.0;out.connect(ctx.destination);
  const lp=ctx.createBiquadFilter();lp.type="lowpass";lp.Q.value=0.9;lp.connect(out);
  const shaper=ctx.createWaveShaper();const c=new Float32Array(1024);for(let i=0;i<1024;i++){const x=i/512-1;c[i]=Math.tanh(2.2*x)}
  shaper.curve=c;shaper.connect(lp);
  const osc=[],gains=[];[1,2,0.5,3,4].forEach((h,i)=>{const o=ctx.createOscillator();o.type=i==0?"sawtooth":(i==2?"triangle":"square");
    const g=ctx.createGain();g.gain.value=[0.5,0.22,0.35,0.12,0.06][i];o.connect(g);g.connect(shaper);o.start();osc.push([o,h]);gains.push(g)});
  const n=ctx.createBufferSource(),buf=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate),d=buf.getChannelData(0);
  for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;n.buffer=buf;n.loop=true;const ng=ctx.createGain();ng.gain.value=E.turbo?0.05:0.025;
  const nf=ctx.createBiquadFilter();nf.type="bandpass";nf.frequency.value=E.turbo?2600:4000;n.connect(nf);nf.connect(ng);ng.connect(lp);n.start();
  nodes={out,lp,osc};out.gain.setTargetAtTime(0.28,ctx.currentTime,0.08);
}
function frame(){
  if(lapT){const L=D.lap,el=(performance.now()-lapT)/1000;if(el>=L.t[L.t.length-1]){lapT=null;document.getElementById("lapbtn").classList.remove("on")}
    else{let i=0;while(i<L.t.length-1&&L.t[i+1]<el)i++;target=L.rpm[i]}}
  else target=fromSlider();
  rpm+= (target-rpm)*0.18;
  const hz=rpm/60*E.cylinders/2;
  read.innerHTML=Math.round(rpm).toLocaleString()+" rpm<small>firing "+Math.round(hz)+" Hz</small>";
  bar.style.width=(100*(rpm-E.rpm_idle)/(E.rpm_max-E.rpm_idle))+"%";
  if(nodes){const now=ctx.currentTime;nodes.osc.forEach(([o,h])=>o.frequency.setTargetAtTime(hz*h*(1+0.004*Math.sin(now*37)),now,0.02));
    nodes.lp.frequency.setTargetAtTime((E.turbo?1.8:3.2)*hz+400,now,0.03)}
  requestAnimationFrame(frame)}
document.getElementById("play").onclick=e=>{if(!ctx){build();e.target.textContent="■ Stop";}else{ctx.close();ctx=null;nodes=null;e.target.textContent="▶ Start engine";}};
document.getElementById("rev").onclick=()=>{if(!ctx){build();document.getElementById("play").textContent="■ Stop";}
  slider.value=1000;setTimeout(()=>slider.value=150,900)};
if(D.lap){const b=document.createElement("button");b.id="lapbtn";b.textContent="Drive the lap";document.getElementById("lapb").appendChild(b);
  b.onclick=()=>{if(!ctx){build();document.getElementById("play").textContent="■ Stop";}lapT=performance.now();b.classList.add("on")}}
frame();
</script></body></html>"""
