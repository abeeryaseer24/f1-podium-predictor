"""Wind Tunnel: a real 2D fluid simulation running in the visitor's browser.

It's a lattice-Boltzmann solver (D2Q9), the method many research and industry CFD codes use: the air
is a grid of particle populations that stream to their neighbours and relax towards equilibrium every
step. Solid shapes bounce the populations back (no-slip walls), and the momentum they take from the
air is the force on the shape: drag (backwards) and downforce (downwards).

The tunnel's edges are held at the free-stream speed. At this resolution the air's boundary layers are
thick, so ground effect can't be shown honestly here; the Academy's ride-height demo covers it instead.

It's 2D and at a much lower Reynolds number than a real car, so the numbers are qualitative: use it to
see how flow turns, separates, stalls and forms a wake, not for real downforce figures.
"""
import json

import streamlit.components.v1 as components


def tunnel(dark=True, height=430):
    components.html(PAGE.replace("__DARK__", json.dumps(dark)), height=height)


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
 body{margin:0;font-family:Inter,system-ui,sans-serif}
 #app{display:flex;flex-direction:column;gap:10px;color:var(--t)}
 #stage{position:relative;border-radius:16px;overflow:hidden;border:1px solid var(--b);background:#000}
 canvas{display:block;width:100%;image-rendering:auto}
 #hud{position:absolute;left:12px;top:12px;display:flex;gap:8px;flex-wrap:wrap}
 .tile{background:var(--p);border:1px solid var(--b);border-radius:12px;padding:8px 12px;min-width:110px}
 .tile b{display:block;font:800 22px 'Saira Condensed',Inter,sans-serif;color:var(--t)}
 .tile small{color:var(--m);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.4px}
 .tile.red b{color:#e10600}
 #controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
 select,button{font:600 12px Inter,system-ui,sans-serif;padding:9px 14px;border-radius:999px;cursor:pointer;border:1px solid var(--b);background:var(--p);color:var(--t)}
 button.on{background:#e10600;border-color:#e10600;color:#fff}
 label{font-size:12px;color:var(--m);display:flex;align-items:center;gap:8px}
 input[type=range]{accent-color:#e10600;width:150px}
 #legend{position:absolute;right:12px;bottom:10px;font-size:11px;color:#ddd;background:rgba(0,0,0,.45);padding:6px 10px;border-radius:10px}
</style></head><body><div id="app">
 <div id="stage"><canvas id="c"></canvas>
  <div id="hud">
   <div class="tile red"><small>Downforce</small><b id="down">–</b></div>
   <div class="tile"><small>Drag</small><b id="drag">–</b></div>
   <div class="tile"><small>Efficiency L/D</small><b id="ld">–</b></div>
  </div><div id="legend">Colour: air speed (blue slow → red fast)</div></div>
 <div id="controls">
  <select id="shape"><option value="wing" selected>Single wing</option><option value="slot">Wing with a flap (two elements)</option>
   <option value="car">Car silhouette</option><option value="plate">Flat plate</option></select>
  <label>Angle <input id="angle" type="range" min="-5" max="30" value="8"><span id="angv">8°</span></label>
  <select id="view"><option value="speed">Show air speed</option><option value="curl">Show swirl (vorticity)</option></select>
  <button id="pause">Pause</button><button id="reset">Reset air</button>
 </div></div>
<script>
const dark=__DARK__;
const T=dark?{p:"rgba(21,21,30,.9)",b:"#2c2c3a",t:"#f5f5f7",m:"#a3a3b2"}:{p:"rgba(255,255,255,.92)",b:"#d9d9d4",t:"#15151e",m:"#55556a"};
const app=document.getElementById("app");for(const[k,v]of Object.entries(T))app.style.setProperty("--"+k,v);

const xdim=300, ydim=110, N=xdim*ydim, u0=0.1, visc=0.0025, omega=1/(3*visc+0.5);
const four9=4/9, one9=1/9, one36=1/36;
const n0=new Float32Array(N),nN=new Float32Array(N),nS=new Float32Array(N),nE=new Float32Array(N),nW=new Float32Array(N),
      nNE=new Float32Array(N),nSE=new Float32Array(N),nNW=new Float32Array(N),nSW=new Float32Array(N);
const rho=new Float32Array(N),ux=new Float32Array(N),uy=new Float32Array(N),curl=new Float32Array(N);
const barrier=new Uint8Array(N);
let chord=60, fx=0, fy=0, avgX=0, avgY=0, steps=0, running=true;

function setEq(i,newux,newuy,newrho){
  const ux3=3*newux,uy3=3*newuy,ux2=newux*newux,uy2=newuy*newuy,uxuy2=2*newux*newuy,u2=ux2+uy2,u215=1.5*u2;
  n0[i]=four9*newrho*(1-u215);
  nE[i]=one9*newrho*(1+ux3+4.5*ux2-u215); nW[i]=one9*newrho*(1-ux3+4.5*ux2-u215);
  nN[i]=one9*newrho*(1+uy3+4.5*uy2-u215); nS[i]=one9*newrho*(1-uy3+4.5*uy2-u215);
  nNE[i]=one36*newrho*(1+ux3+uy3+4.5*(u2+uxuy2)-u215); nSE[i]=one36*newrho*(1+ux3-uy3+4.5*(u2-uxuy2)-u215);
  nNW[i]=one36*newrho*(1-ux3+uy3+4.5*(u2-uxuy2)-u215); nSW[i]=one36*newrho*(1-ux3-uy3+4.5*(u2+uxuy2)-u215);
  rho[i]=newrho; ux[i]=newux; uy[i]=newuy;
}
function initFluid(){for(let i=0;i<N;i++)setEq(i,u0,0,1);avgX=avgY=0;steps=0}

function collide(){
  for(let y=1;y<ydim-1;y++)for(let x=1;x<xdim-1;x++){
    const i=x+y*xdim;
    const r=n0[i]+nN[i]+nS[i]+nE[i]+nW[i]+nNW[i]+nNE[i]+nSW[i]+nSE[i];
    const vx=(nE[i]+nNE[i]+nSE[i]-nW[i]-nNW[i]-nSW[i])/r, vy=(nN[i]+nNE[i]+nNW[i]-nS[i]-nSE[i]-nSW[i])/r;
    rho[i]=r;ux[i]=vx;uy[i]=vy;
    const o9=one9*r,o36=one36*r,vx3=3*vx,vy3=3*vy,vx2=vx*vx,vy2=vy*vy,vxy2=2*vx*vy,v2=vx2+vy2,v215=1.5*v2;
    n0[i]+=omega*(four9*r*(1-v215)-n0[i]);
    nE[i]+=omega*(o9*(1+vx3+4.5*vx2-v215)-nE[i]); nW[i]+=omega*(o9*(1-vx3+4.5*vx2-v215)-nW[i]);
    nN[i]+=omega*(o9*(1+vy3+4.5*vy2-v215)-nN[i]); nS[i]+=omega*(o9*(1-vy3+4.5*vy2-v215)-nS[i]);
    nNE[i]+=omega*(o36*(1+vx3+vy3+4.5*(v2+vxy2)-v215)-nNE[i]); nSE[i]+=omega*(o36*(1+vx3-vy3+4.5*(v2-vxy2)-v215)-nSE[i]);
    nNW[i]+=omega*(o36*(1-vx3+vy3+4.5*(v2-vxy2)-v215)-nNW[i]); nSW[i]+=omega*(o36*(1-vx3-vy3+4.5*(v2+vxy2)-v215)-nSW[i]);
  }
  // outflow on the right: copy the next column in, so the wake leaves cleanly
  for(let y=1;y<ydim-1;y++){const a=xdim-1+y*xdim,b=a-1;nW[a]=nW[b];nNW[a]=nNW[b];nSW[a]=nSW[b]}
}
function stream(){
  for(let y=ydim-2;y>0;y--)for(let x=1;x<xdim-1;x++){nN[x+y*xdim]=nN[x+(y-1)*xdim];nNW[x+y*xdim]=nNW[x+1+(y-1)*xdim]}
  for(let y=ydim-2;y>0;y--)for(let x=xdim-2;x>0;x--){nE[x+y*xdim]=nE[x-1+y*xdim];nNE[x+y*xdim]=nNE[x-1+(y-1)*xdim]}
  for(let y=1;y<ydim-1;y++)for(let x=xdim-2;x>0;x--){nS[x+y*xdim]=nS[x+(y+1)*xdim];nSE[x+y*xdim]=nSE[x-1+(y+1)*xdim]}
  for(let y=1;y<ydim-1;y++)for(let x=1;x<xdim-1;x++){nW[x+y*xdim]=nW[x+1+y*xdim];nSW[x+y*xdim]=nSW[x+1+(y+1)*xdim]}
  fx=0;fy=0;
  for(let y=1;y<ydim-1;y++)for(let x=1;x<xdim-1;x++){
    const i=x+y*xdim;if(!barrier[i])continue;
    nE[i+1]=nW[i];nW[i-1]=nE[i];nN[i+xdim]=nS[i];nS[i-xdim]=nN[i];
    nNE[i+xdim+1]=nSW[i];nNW[i+xdim-1]=nSE[i];nSE[i-xdim+1]=nNW[i];nSW[i-xdim-1]=nNE[i];
    fx+=nE[i]+nNE[i]+nSE[i]-nW[i]-nNW[i]-nSW[i];
    fy+=nN[i]+nNE[i]+nNW[i]-nS[i]-nSE[i]-nSW[i];
  }
  // inflow (left), top and the moving floor (bottom) held at the free-stream: a rolling road
  for(let x=0;x<xdim;x++){setEq(x,u0,0,1);setEq(x+(ydim-1)*xdim,u0,0,1)}
  for(let y=1;y<ydim-1;y++)setEq(y*xdim,u0,0,1);
}

// ---------- shapes (y up) ----------
function naca(m,p,t,n){            // NACA 4-digit: returns upper+lower surface points, chord 1
  const pts=[];
  for(let k=0;k<=n;k++){const b=Math.PI*k/n,x=(1-Math.cos(b))/2;
    const yt=5*t*(0.2969*Math.sqrt(x)-0.126*x-0.3516*x*x+0.2843*x**3-0.1036*x**4);
    const yc=x<p?m/p/p*(2*p*x-x*x):m/(1-p)/(1-p)*((1-2*p)+2*p*x-x*x);
    pts.push([x,yc+yt])}
  for(let k=n;k>=0;k--){const b=Math.PI*k/n,x=(1-Math.cos(b))/2;
    const yt=5*t*(0.2969*Math.sqrt(x)-0.126*x-0.3516*x*x+0.2843*x**3-0.1036*x**4);
    const yc=x<p?m/p/p*(2*p*x-x*x):m/(1-p)/(1-p)*((1-2*p)+2*p*x-x*x);
    pts.push([x,yc-yt])}
  return pts}
function inside(px,py,poly){let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const[xi,yi]=poly[i],[xj,yj]=poly[j];
  if(((yi>py)!=(yj>py))&&(px<(xj-xi)*(py-yi)/(yj-yi)+xi))c=!c}return c}
function fill(poly){let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;for(const[x,y]of poly){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
  for(let y=Math.max(1,Math.floor(y0));y<=Math.min(ydim-2,Math.ceil(y1));y++)for(let x=Math.max(1,Math.floor(x0));x<=Math.min(xdim-2,Math.ceil(x1));x++)
    if(inside(x+.5,y+.5,poly))barrier[x+y*xdim]=1}
function wing(cx,cy,c,deg,camber){   // inverted (downforce) wing: camber downward, trailing edge raised by deg
  const a=deg*Math.PI/180;return naca(camber,0.4,0.12,40).map(([x,y])=>{const X=x*c,Y=-y*c;
    return[cx+X*Math.cos(a)-Y*Math.sin(a), cy+X*Math.sin(a)+Y*Math.cos(a)]})}
function buildShape(){
  barrier.fill(0);
  const s=document.getElementById("shape").value,deg=+document.getElementById("angle").value;
  document.getElementById("angv").textContent=deg+"°";
  if(s==="wing"){chord=60;fill(wing(70,55,chord,deg,0.06))}
  else if(s==="slot"){chord=60;const c1=42,a=deg*Math.PI/180,tx=70+c1*Math.cos(a),ty=55+c1*Math.sin(a);
    fill(wing(70,55,c1,deg,0.06));fill(wing(tx-4,ty+3,20,deg+22,0.06))}   // flap just above and behind: a slot between them
  else if(s==="plate"){chord=50;const a=deg*Math.PI/180,cx=75,cy=58,poly=[[0,-1.5],[chord,-1.5],[chord,1.5],[0,1.5]].map(([x,y])=>[cx+x*Math.cos(a)-y*Math.sin(a),cy+x*Math.sin(a)+y*Math.cos(a)]);fill(poly)}
  else{chord=170;                     // a simple car: floor, body, front wing and a rear wing set to the angle
    fill([[40,10],[200,10],[212,16],[210,26],[150,30],[120,40],[95,38],[70,26],[45,20]]);
    fill(wing(18,9,26,6,0.06));
    fill(wing(205,48,24,deg,0.08));fill([[214,24],[217,24],[217,46],[214,46]])}
  avgX=avgY=0;steps=0}

// ---------- drawing ----------
const canvas=document.getElementById("c");canvas.width=xdim;canvas.height=ydim;
const g=canvas.getContext("2d"),img=g.createImageData(xdim,ydim);
function colour(v){v=Math.max(0,Math.min(1,v));const st=[[43,108,255],[25,195,166],[255,210,63],[255,59,47]];
  const s=v*3,k=Math.min(2,Math.floor(s)),f=s-k,a=st[k],b=st[k+1];return[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f]}
function draw(){
  const mode=document.getElementById("view").value;
  if(mode==="curl")for(let y=1;y<ydim-1;y++)for(let x=1;x<xdim-1;x++){const i=x+y*xdim;curl[i]=uy[i+1]-uy[i-1]-ux[i+xdim]+ux[i-xdim]}
  for(let y=0;y<ydim;y++)for(let x=0;x<xdim;x++){
    const i=x+y*xdim,p=4*(x+(ydim-1-y)*xdim);
    let c;
    if(barrier[i])c=dark?[235,235,240]:[30,30,40];
    else if(mode==="curl"){const v=curl[i]*8;c=v>0?[255,59+Math.max(0,150-v*900),47]:[43,108+Math.max(0,100+v*900),255];
      const m=Math.min(1,Math.abs(v)*12);c=[c[0]*m+12*(1-m),c[1]*m+12*(1-m),c[2]*m+18*(1-m)]}
    else c=colour(Math.sqrt(ux[i]*ux[i]+uy[i]*uy[i])/(u0*1.8));
    img.data[p]=c[0];img.data[p+1]=c[1];img.data[p+2]=c[2];img.data[p+3]=255}
  g.putImageData(img,0,0);
  if(steps>300){
    const q=0.5*u0*u0*chord;               // per unit span, lattice units
    const down=-avgY/q, drag=avgX/q;
    document.getElementById("down").textContent=down.toFixed(2);
    document.getElementById("drag").textContent=drag.toFixed(2);
    document.getElementById("ld").textContent=drag>0.01?(down/drag).toFixed(1):"–";
  }else{["down","drag","ld"].forEach(k=>document.getElementById(k).textContent="…")}
}
function frame(){
  if(running){for(let s=0;s<10;s++){collide();stream();steps++;
    if(steps>200){avgX+=(fx-avgX)*0.004;avgY+=(fy-avgY)*0.004}}}
  draw();requestAnimationFrame(frame)}
document.getElementById("view").addEventListener("input",e=>{document.getElementById("legend").textContent=
  e.target.value==="curl"?"Colour: swirl (red clockwise, blue anticlockwise)":"Colour: air speed (blue slow → red fast)"});
["shape","angle"].forEach(id=>document.getElementById(id).addEventListener("input",buildShape));
document.getElementById("pause").onclick=e=>{running=!running;e.target.textContent=running?"Pause":"Run";e.target.classList.toggle("on",!running)};
document.getElementById("reset").onclick=()=>{initFluid()};
initFluid();buildShape();frame();
</script></body></html>"""
