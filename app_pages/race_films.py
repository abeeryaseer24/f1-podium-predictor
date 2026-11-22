"""Race Films: the story of any race since 2023, written from its data and read aloud by your browser."""
import json

import streamlit as st
import streamlit.components.v1 as components

import race_film as RF
from app_data import get_prepared_races


@st.cache_data(ttl=86400, max_entries=60)
def film(folder):
    return RF.film(folder)


races = get_prepared_races()
seasons = sorted(races["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons, key="rf_season")
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get, key="rf_race")
data = film(folder)
dark = st.session_state.dark

PLAYER = r"""<!doctype html><html><head><meta charset="utf-8"><style>
 body{margin:0;font-family:Inter,system-ui,sans-serif;color:var(--t)}
 #top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
 h2{font:800 26px 'Saira Condensed',Inter,sans-serif;margin:0;flex:1;letter-spacing:.4px;color:var(--t)}
 button,select{font:600 12px Inter,system-ui,sans-serif;padding:9px 15px;border-radius:999px;cursor:pointer;border:1px solid var(--b);background:var(--p);color:var(--t)}
 #play{background:#e10600;border-color:#e10600;color:#fff}
 #bar{height:6px;border-radius:3px;background:var(--p2);margin-bottom:14px;overflow:hidden}
 #fill{height:100%;width:0;background:linear-gradient(90deg,#e10600,#ff7a1a);transition:width .6s}
 .scene{display:flex;gap:14px;padding:14px 16px;margin-bottom:10px;border-radius:14px;border:1px solid var(--b);background:var(--p);transition:all .3s;cursor:pointer}
 .scene.on{border-color:#e10600;box-shadow:0 0 0 1px #e10600 inset;transform:translateX(4px)}
 .lap{font:800 22px 'Saira Condensed',Inter,sans-serif;min-width:58px;color:#e10600;text-align:center}
 .lap small{display:block;font:600 10px Inter,sans-serif;color:var(--m);text-transform:uppercase;letter-spacing:.5px}
 .body b{display:block;font-size:15px;margin-bottom:4px;color:var(--t)}
 .body p{margin:0 0 8px;font-size:13.5px;line-height:1.5;color:var(--t)}
 .chips{display:flex;gap:6px;flex-wrap:wrap}
 .chip{font:700 11px Inter,sans-serif;padding:3px 8px;border-radius:999px;color:#fff}
 .kind{font:700 10px Inter,sans-serif;text-transform:uppercase;letter-spacing:.5px;color:var(--m);margin-left:6px}
 #note{font-size:11px;color:var(--m);margin-top:6px}
</style></head><body><div id="top"><h2 id="title"></h2><button id="play">▶ Play the film</button><button id="stop">Stop</button>
<select id="voice" aria-label="Voice"></select></div><div id="bar"><div id="fill"></div></div><div id="list"></div>
<div id="note">Narrated by your browser's built-in voice (free, nothing leaves your device). Tap a scene to hear it.</div>
<script>
const D=__DATA__, dark=__DARK__;
const T=dark?{p:"#15151e",p2:"#1e1e29",b:"#2c2c3a",t:"#f5f5f7",m:"#a3a3b2"}:{p:"#ffffff",p2:"#ececea",b:"#d9d9d4",t:"#15151e",m:"#55556a"};
for(const[k,v]of Object.entries(T))document.body.style.setProperty("--"+k,v);
document.getElementById("title").textContent=D.title;
const KIND={start:"Start",sc:"Neutralised",lead:"Lead change",pit:"Strategy",climb:"Charge",finish:"Finish"};
const list=document.getElementById("list");
const cards=D.scenes.map((s,i)=>{const el=document.createElement("div");el.className="scene";
  el.innerHTML=`<div class="lap">${s.lap}<small>lap</small></div><div class="body"><b>${s.title}<span class="kind">${KIND[s.kind]||""}</span></b>
  <p>${s.text}</p><div class="chips">${s.top.map(t=>`<span class="chip" style="background:${t.colour}">P${t.pos} ${t.code}</span>`).join("")}</div></div>`;
  el.onclick=()=>{stop();speak(i,false)};list.appendChild(el);return el});
const synth=window.speechSynthesis;let voices=[],playing=false;
function loadVoices(){voices=synth?synth.getVoices().filter(v=>v.lang.startsWith("en")):[];const sel=document.getElementById("voice");
  sel.innerHTML=voices.map((v,i)=>`<option value="${i}">${v.name}</option>`).join("")||"<option>Default voice</option>"}
if(synth){loadVoices();synth.onvoiceschanged=loadVoices}
function mark(i){cards.forEach((c,k)=>c.classList.toggle("on",k===i));if(i>=0)cards[i].scrollIntoView({block:"nearest",behavior:"smooth"});
  document.getElementById("fill").style.width=(i<0?0:100*D.scenes[i].lap/D.laps)+"%"}
function speak(i,chain){if(!synth){mark(i);return}mark(i);const u=new SpeechSynthesisUtterance(D.scenes[i].title+". "+D.scenes[i].text);
  const v=voices[+document.getElementById("voice").value];if(v)u.voice=v;u.rate=1.02;
  u.onend=()=>{if(chain&&playing&&i+1<D.scenes.length)setTimeout(()=>speak(i+1,true),350);else if(chain)playing=false};synth.speak(u)}
function stop(){playing=false;if(synth)synth.cancel()}
document.getElementById("play").onclick=()=>{stop();playing=true;speak(0,true)};
document.getElementById("stop").onclick=()=>{stop();mark(-1)};
</script></body></html>"""
height = 140 + 132 * len(data["scenes"])
components.html(PLAYER.replace("__DATA__", json.dumps(data)).replace("__DARK__", json.dumps(dark)), height=min(height, 1500),
                scrolling=height > 1500)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Every sentence comes from the race's data: lap times, positions, pit stops and race control.")
right.page_link("app_pages/pit_wall.py", label="Watch it on the Pit Wall in 3D", icon=":material/play_circle:")
