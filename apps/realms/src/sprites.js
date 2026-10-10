/* Procedural pixel sprites. Each species is drawn from a body plan on a
   32x32 grid, mirrored for symmetry, then coloured with a 3-tone palette
   plus outline and shading. Details (spots, horns, crest size) come from a
   seeded RNG so every species looks fixed and distinct between loads.
   Not hand-drawn art; a deliberate, consistent pixel style instead. */

const SPR = 32;

function hashStr(s){ let h=2166136261; for(const c of s){ h^=c.charCodeAt(0); h=Math.imul(h,16777619); } return h>>>0; }
function rng(seed){ let a=seed>>>0; return ()=>{ a=(a+0x6D2B79F5)>>>0; let t=a; t=Math.imul(t^(t>>>15),t|1); t^=t+Math.imul(t^(t>>>7),t|61); return ((t^(t>>>14))>>>0)/4294967296; }; }

function hexToRgb(h){ const n=parseInt(h.slice(1),16); return [(n>>16)&255,(n>>8)&255,n&255]; }
function shade(h,f){ const [r,g,b]=hexToRgb(h); const k=v=>Math.max(0,Math.min(255,Math.round(v*f))); return `rgb(${k(r)},${k(g)},${k(b)})`; }

// mask helpers on a Uint8Array grid: value = layer (1 main, 2 belly, 3 accent)
function makeGrid(){ return new Uint8Array(SPR*SPR); }
function ell(g,cx,cy,rx,ry,v){ for(let y=0;y<SPR;y++)for(let x=0;x<SPR;x++){ const dx=(x+.5-cx)/rx, dy=(y+.5-cy)/ry; if(dx*dx+dy*dy<=1) g[y*SPR+x]=v; } }
function rect(g,x0,y0,w,h,v){ for(let y=y0;y<y0+h;y++)for(let x=x0;x<x0+w;x++) if(x>=0&&y>=0&&x<SPR&&y<SPR) g[y*SPR+x]=v; }
function mirror(g){ for(let y=0;y<SPR;y++)for(let x=0;x<SPR/2;x++){ const v=g[y*SPR+x]; g[y*SPR+(SPR-1-x)]=v; } }

const PLANS = {
  quad(g,r,s){ // body, head to the left, four legs, tail
    const bw=9+s*2, bh=6+s;
    ell(g,18,20,bw,bh,1); ell(g,9,15,5+s,5+s,1);            // body, head
    ell(g,18,21,bw-3,bh-3,2);                                 // belly
    for(const lx of [12,16,21,25]) rect(g,lx,24,3,5,1);       // legs
    rect(g,26,16,4,2,1); rect(g,29,13,2,4,1);                 // tail
    ell(g,7,13,1.3,1.3,3); if(r()>.4) ell(g,9,9,2+s*.5,2,3);  // eye, crest
    if(r()>.5) for(let i=0;i<3+s;i++) ell(g,14+i*3,18+(i%2)*2,1.2,1.2,3); // spots
  },
  biped(g,r,s){ // upright, big head, arms, tail
    ell(g,16,13,6+s,6+s,1); ell(g,16,22,6+s,7+s,1);           // head, body
    ell(g,16,24,4+s,4+s,2);                                   // belly
    rect(g,9-s,19,3,6,1); rect(g,20+s,19,3,6,1);              // arms
    rect(g,12,28,3,4,1); rect(g,17,28,3,4,1);                 // legs
    rect(g,22+s,25,5,2,1); rect(g,26+s,22,2,4,3);             // tail + flame tip
    ell(g,13,12,1.3,1.3,3); ell(g,19,12,1.3,1.3,3);           // eyes
    if(r()>.3){ rect(g,11,6-s,2,4,3); rect(g,19,6-s,2,4,3); } // horns
  },
  serpent(g,r,s){ // long body coiling, head raised, small wings
    for(let i=0;i<7;i++){ const x=26-i*3, y=24-Math.abs(i-3)*2; ell(g,x,y,3.5+s*.4,3.5+s*.4,1); }
    ell(g,8,10,5+s,4.5+s,1); ell(g,8,12,3,2,2);               // head, chin
    ell(g,6,9,1.2,1.2,3);                                     // eye
    rect(g,16,8-s,2,8,3); rect(g,20,9-s,2,7,3);               // wing/fin spikes
    for(let i=0;i<4;i++) ell(g,14+i*3,24,1.2,1.2,3);          // belly accents
  },
  bird(g,r,s){ // round body, wing, beak, tail feathers
    ell(g,15,18,8+s,7+s,1); ell(g,11,10,4.5+s*.5,4+s*.5,1);   // body, head
    ell(g,17,20,5+s,4,2);                                     // breast
    ell(g,20,17,5,3,3);                                       // wing
    rect(g,5,10,3,2,3);                                       // beak
    ell(g,10,9,1.1,1.1,3);                                    // eye
    rect(g,24,13,5,2,3); rect(g,26,10,2,4,3);                 // tail
    rect(g,12,25,2,4,3); rect(g,17,25,2,4,3);                 // legs
  },
  blob(g,r,s){ // dome with face, flat bottom
    ell(g,16,19,10+s,9+s,1); rect(g,6-s,19,20+2*s,8,1);
    ell(g,16,24,7+s,3,2);                                     // base shade
    ell(g,12,16,1.5,1.5,3); ell(g,20,16,1.5,1.5,3);           // eyes
    if(r()>.5) for(let i=0;i<4;i++) rect(g,8+i*5,10-(i%2)*2,2,3,3); // bumps
    if(r()>.5) ell(g,16,20,2,1,3);                            // mouth
  },
  bug(g,r,s){ // segmented body, legs, antennae
    ell(g,10,14,4+s*.5,4+s*.5,1); ell(g,17,17,5+s,5+s,1); ell(g,24,19,4+s,4+s,1);
    ell(g,17,18,3+s,3,2);
    for(let i=0;i<3;i++){ rect(g,12+i*5,22,2,5,1); }          // legs
    rect(g,7,9,1,4,3); rect(g,11,8,1,5,3);                    // antennae
    ell(g,8,13,1.1,1.1,3);
    if(s>0){ ell(g,17,11,6,3,3); }                            // wings
  },
  ghost(g,r,s){ // floating sheet with wavy bottom, no legs
    ell(g,16,14,8+s,9+s,1);
    for(let i=0;i<5;i++) ell(g,8+i*4,23,2.2,3,1);             // wavy hem
    ell(g,12,13,1.6,2,3); ell(g,20,13,1.6,2,3);               // eyes
    ell(g,16,17,2,1.2,2);                                     // mouth
    if(r()>.5){ rect(g,4,10,3,2,3); rect(g,25,10,3,2,3); }    // wisps
  },
  turtle(g,r,s){ // shell dome, head out, stubby legs
    ell(g,17,17,9+s,7+s,3);                                   // shell (accent)
    ell(g,17,17,7+s,5+s,1);                                   // shell pattern
    ell(g,7,15,4+s*.5,4,1); ell(g,7,16,2.5,2,2);              // head
    for(const lx of [11,22]) rect(g,lx,23,4,4,1);             // legs
    rect(g,27+s,19,3,2,1);                                    // tail
    ell(g,6,14,1.1,1.1,3);
    for(let i=0;i<3;i++) ell(g,13+i*4,16,1.5,1.5,2);          // shell scutes
  },
};

const spriteCache = new Map();
/** Render species to a canvas (96x96, pixelated). Cached per species+facing. */
function spriteFor(sp, facing="front"){
  const key=sp.id+":"+facing;
  if(spriteCache.has(key)) return spriteCache.get(key);
  const g=makeGrid();
  const r=rng(hashStr(sp.n));
  const stage=sp.evo?0:(SPECIES.some(o=>o.evo&&o.evo.to===sp.id)?1:0);
  const s=Math.min(2, stage + (sp.st.reduce((a,b)=>a+b,0)>300?1:0));
  (PLANS[sp.plan]||PLANS.blob)(g,r,s);
  mirror(g);

  const c=document.createElement("canvas"); c.width=c.height=96;
  const ctx=c.getContext("2d");
  const [main,belly,acc]=sp.pal;
  const cols={1:main,2:belly,3:acc};
  const dark=shade(main,.55), outline=shade(main,.3);
  const px=3;
  // shading: lower-right quadrant darker
  for(let y=0;y<SPR;y++)for(let x=0;x<SPR;x++){
    const v=g[y*SPR+x]; if(!v) continue;
    const edge=[[1,0],[-1,0],[0,1],[0,-1]].some(([dx,dy])=>{const nx=x+dx,ny=y+dy; return nx<0||ny<0||nx>=SPR||ny>=SPR||!g[ny*SPR+nx];});
    let col = edge ? outline : cols[v];
    if(!edge && v===1 && (x+y)>SPR+6) col=dark;
    ctx.fillStyle=col;
    const dx = facing==="back" ? (SPR-1-x) : x;
    ctx.fillRect(dx*px,y*px,px,px);
  }
  spriteCache.set(key,c);
  return c;
}
function drawSprite(canvas, sp, facing){
  const ctx=canvas.getContext("2d"); ctx.imageSmoothingEnabled=false;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(spriteFor(sp,facing),0,0,canvas.width,canvas.height);
}
