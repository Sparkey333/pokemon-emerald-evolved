/* Screens, input, rendering, boot. */
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const el={ map:$("#map"), log:$("#world-log"), blog:$("#battle-log"), bmenu:$("#battle-menu") };
let toastT=null;
function toast(msg){ const t=$("#toast"); t.textContent=msg; t.hidden=false; clearTimeout(toastT); toastT=setTimeout(()=>t.hidden=true,2200); }
function confirmBox(text){ return new Promise(res=>{ const m=$("#modal"); $("#modal-text").textContent=text; m.hidden=false;
  const done=v=>{ m.hidden=true; $("#modal-yes").onclick=null; $("#modal-no").onclick=null; res(v); };
  $("#modal-yes").onclick=()=>done(true); $("#modal-no").onclick=()=>done(false); }); }
function typeChips(types){ return types.map(t=>`<span class="type" style="--t:${TYPE_COLOR[t]}">${t}</span>`).join(""); }
function hpClass(m){ const r=m.hp/calcStats(m).hp; return r<.25?"low":r<.5?"mid":""; }

// ---------- tabs & screens ----------
function showTab(id){
  $$(".tabs button").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.tab===id)));
  $$(".panel").forEach(p=>p.hidden=(p.id!=="tab-"+id));
  if(id==="party") renderParty(); if(id==="codex") renderCodex(); if(id==="hacks") renderHacks(); if(id==="saves") renderSlots();
  if(location.hash!=="#"+id) history.replaceState(null,"","#"+id);
}
function showScreen(id){ $$("#tab-play .screen").forEach(s=>s.hidden=(s.id!=="screen-"+id)); }

// ---------- title / starter ----------
function renderTitle(){
  const any=[1,2,3].some(n=>slotInfo(n));
  $("#btn-continue").hidden=!any;
  $("#title-hint").textContent = any ? "Continue loads your most recent slot. Slots, copies and transfers are under Saves." : "Saves live in this browser. Copy a save's text under Saves to keep it anywhere.";
}
function renderStarters(){
  const box=$("#starters"); box.innerHTML="";
  for(const id of STARTERS){ const sp=getSpecies(id); const b=document.createElement("button"); b.className="starter";
    b.innerHTML=`<canvas width="96" height="96"></canvas><div class="n">${sp.n}</div><div class="t">${typeChips(sp.t)}</div>`;
    drawSprite(b.querySelector("canvas"),sp,"front");
    b.onclick=()=>{ newGame(id); toast(`${sp.n} joins you.`); enterWorld(`You and ${sp.n} set out into the ${REALMS[0].n}.`); };
    box.appendChild(b); }
}

// ---------- world ----------
const TILE=32;
function enterWorld(msg){ showScreen("world"); drawMap(); $("#realm-name").textContent=REALMS[G.realm].n; if(msg) el.log.textContent=msg; }
function drawMap(){
  const ctx=el.map.getContext("2d"); const r=REALMS[G.realm];
  ctx.fillStyle=r.bg; ctx.fillRect(0,0,el.map.width,el.map.height);
  for(let y=0;y<r.map.length;y++)for(let x=0;x<16;x++){
    const t=r.map[y][x]; const px=x*TILE, py=y*TILE;
    if(WALLS.has(t)){ ctx.fillStyle=r.wall; ctx.fillRect(px,py,TILE,TILE); ctx.fillStyle="rgba(0,0,0,.25)"; ctx.fillRect(px+4,py+4,TILE-8,TILE-8); }
    else if(t==="G"){ ctx.fillStyle=r.grass; ctx.fillRect(px,py,TILE,TILE); ctx.fillStyle=r.grass2; for(let i=0;i<4;i++){ ctx.fillRect(px+4+(i%2)*14,py+6+Math.floor(i/2)*12,4,8); } }
    else { ctx.fillStyle=r.path; ctx.fillRect(px,py,TILE,TILE); }
    if(t==="H"){ ctx.fillStyle="#3ddc84"; ctx.fillRect(px+8,py+8,16,16); ctx.fillStyle="#e6f2ea"; ctx.fillRect(px+14,py+6,4,20); ctx.fillRect(px+6,py+14,20,4); }
    if(r.gates[t]){ ctx.fillStyle="#f5b942"; ctx.fillRect(px+6,py+6,20,20); ctx.fillStyle=r.bg; ctx.fillRect(px+11,py+11,10,10); }
    if(t==="X"){ ctx.fillStyle=G.shrineDone?"#5a7f6a":"#9b7bff"; ctx.beginPath(); ctx.moveTo(px+16,py+4); ctx.lineTo(px+28,py+28); ctx.lineTo(px+4,py+28); ctx.closePath(); ctx.fill(); }
  }
  // player
  const px=G.x*TILE, py=G.y*TILE; ctx.fillStyle="#04150c"; ctx.fillRect(px+9,py+5,14,22);
  ctx.fillStyle="#3ddc84"; ctx.fillRect(px+10,py+6,12,20); ctx.fillStyle="#f5b942"; ctx.fillRect(px+10,py+6,12,7); ctx.fillStyle="#04150c"; ctx.fillRect(px+13,py+9,2,2); ctx.fillRect(px+17,py+9,2,2);
}
function handleMove(dir){
  if(B&&!B.over) return; if(!G) return;
  const ev=stepPlayer(dir); drawMap();
  if(!ev) return;
  if(ev.k==="heal"){ el.log.textContent="The shrine restores your party."; toast("Party healed"); }
  else if(ev.k==="gate"){ $("#realm-name").textContent=ev.realm; el.log.textContent=`You step through into the ${ev.realm}.`; toast(ev.realm); }
  else if(ev.k==="shrine"){ el.log.textContent="Something ancient stirs at the shrine..."; beginBattle(makeMon(36,50),{legend:true}); }
  else if(ev.k==="encounter"){ beginBattle(ev.foe); }
}
function bindInput(){
  document.addEventListener("keydown",e=>{
    const k={ArrowUp:"up",ArrowDown:"down",ArrowLeft:"left",ArrowRight:"right",w:"up",s:"down",a:"left",d:"right",W:"up",S:"down",A:"left",D:"right"}[e.key];
    if(k && !$("#screen-world").hidden && !$("#tab-play").hidden){ e.preventDefault(); handleMove(k); }
  });
  $$(".dpad button").forEach(b=>b.addEventListener("click",()=>handleMove(b.dataset.dir)));
}

// ---------- battle ----------
let battleBusy=false;
function beginBattle(foe,opts){
  startBattle(foe,opts); showScreen("battle");
  const fsp=getSpecies(foe.sid);
  el.blog.textContent = opts&&opts.legend ? `${fsp.n}, guardian of the realms, descends!` : `A wild ${fsp.n} appears!`;
  renderBattle(); renderBattleMenu("main");
}
function renderBattle(){
  const a=ally(), f=B.foe, asp=getSpecies(a.sid), fsp=getSpecies(f.sid);
  drawSprite($("#foe-sprite"),fsp,"front"); drawSprite($("#ally-sprite"),asp,"back");
  $("#foe-name").textContent=fsp.n; $("#foe-lv").textContent="Lv "+f.lv;
  $("#ally-name").textContent=asp.n; $("#ally-lv").textContent="Lv "+a.lv;
  const fh=$("#foe-hp"); fh.style.width=(100*f.hp/calcStats(f).hp)+"%"; fh.className="hp "+hpClass(f);
  const ah=$("#ally-hp"); const amx=calcStats(a).hp; ah.style.width=(100*a.hp/amx)+"%"; ah.className="hp "+hpClass(a);
  $("#ally-hptext").textContent=`${a.hp} / ${amx}`;
  const lo=xpForLevel(a.lv), hi=xpForLevel(a.lv+1); $("#ally-xp").style.width=(100*(a.xp-lo)/(hi-lo))+"%";
}
function renderBattleMenu(mode){
  const m=el.bmenu; m.innerHTML="";
  const add=(label,sub,fn,type)=>{ const b=document.createElement("button"); b.innerHTML=`${label}${sub?`<small>${sub}</small>`:""}`; if(type){ b.classList.add("t"); b.style.setProperty("--t",TYPE_COLOR[type]); } b.onclick=fn; m.appendChild(b); return b; };
  if(B.over){ add("Continue","back to the realm",endBattle); return; }
  if(mode==="main"){
    add("Fight","choose a move",()=>renderBattleMenu("fight"));
    add("Catch",`${G.orbs} orbs`,()=>act({k:"catch"}));
    add("Swap","switch creature",()=>renderBattleMenu("swap"));
    add("Tonic",`${G.tonics} left · heals half`,()=>act({k:"tonic"}));
    add("Run", B.legend?"not from a guardian":"leave the fight",()=>act({k:"run"}));
  } else if(mode==="fight"){
    for(const mv of ally().moves){ const d=MOVES[mv]; add(d.n,`${d.t} · ${d.p?d.p+" power":"status"} · ${d.a}%`,()=>act({k:"move",move:mv}),d.t); }
    add("Back","",()=>renderBattleMenu("main"));
  } else if(mode==="swap"){
    G.party.forEach((p,i)=>{ const sp=getSpecies(p.sid); const b=add(sp.n,`Lv ${p.lv} · ${p.hp}/${calcStats(p).hp} HP`,()=>act({k:"swap",idx:i})); if(p.hp<=0||i===B.allyIdx) b.disabled=true; });
    add("Back","",()=>renderBattleMenu("main"));
  }
}
async function act(action){
  if(battleBusy||B.over) return; battleBusy=true;
  const out=battleRound(action);
  for(const line of out.lines){ el.blog.textContent=line; renderBattle(); await sleep(520); }
  battleBusy=false;
  if(out.events.some(e=>e.k==="needswap")){ el.blog.textContent+=" Choose another."; renderBattleMenu("swap"); $$("#battle-menu button").pop().hidden=true; return; }
  if(B.over){ renderBattleMenu("main"); return; }
  renderBattleMenu("main");
}
function endBattle(){
  const res=B.result; B=null;
  if(res==="lost"){ wipeToShrine(); enterWorld("You wake at the shrine, party restored."); }
  else enterWorld(res==="caught"?"A new creature joins you.":res==="won"?"You won the fight.":"Back on the path.");
  if(G.shrineDone) drawMap();
}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

// ---------- party / codex ----------
function monCard(m,i,where){
  const sp=getSpecies(m.sid); const b=document.createElement("button"); b.className="mon"+(where==="party"&&i===0?" lead":"");
  b.innerHTML=`<canvas width="48" height="48"></canvas><div><div class="n">${sp.n}</div><div class="d">Lv ${m.lv} · ${m.hp}/${calcStats(m).hp} HP</div><div class="d">${typeChips(sp.t)}</div></div>`;
  drawSprite(b.querySelector("canvas"),sp,"front");
  b.onclick=()=>{ if(where==="party"){ if(i>0){ const [x]=G.party.splice(i,1); G.party.unshift(x); toast(`${sp.n} leads.`); } }
    else { if(G.party.length<6){ const [x]=G.box.splice(i,1); G.party.push(x); toast(`${sp.n} joins the party.`); } else toast("Party is full. Send one to the box first."); }
    renderParty(); };
  return b;
}
function renderParty(){
  const pg=$("#party-grid"), bg=$("#box-grid"); pg.innerHTML=""; bg.innerHTML="";
  if(!G){ pg.innerHTML='<p class="muted">Start a journey first.</p>'; return; }
  G.party.forEach((m,i)=>{ const c=monCard(m,i,"party"); if(G.party.length>1){ const s=document.createElement("button"); s.className="btn"; s.textContent="→ box"; s.style.minHeight="32px"; s.style.padding=".2rem .5rem"; s.style.fontSize=".7rem"; s.onclick=e=>{ e.stopPropagation(); const [x]=G.party.splice(i,1); G.box.push(x); renderParty(); }; c.appendChild(s);} pg.appendChild(c); });
  G.box.forEach((m,i)=>bg.appendChild(monCard(m,i,"box")));
  if(!G.box.length) bg.innerHTML='<p class="muted">Empty.</p>';
}
function renderCodex(){
  const grid=$("#codex-grid"); grid.innerHTML="";
  const seen=G?G.seen:{}, caught=G?G.caught:{};
  let nS=0,nC=0;
  for(const base of SPECIES){ const sp=getSpecies(base.id); const known=!!seen[sp.id]; const got=!!caught[sp.id]; if(known)nS++; if(got)nC++;
    const d=document.createElement("div"); d.className="mon"+(known?"":" unknown");
    const pr=PRINCIPLES[sp.pr]||["",""];
    d.innerHTML=`<canvas width="48" height="48"></canvas><div><div class="n">#${String(sp.id).padStart(2,"0")} ${known?sp.n:"???"}</div><div class="d">${known?typeChips(sp.t):REALMS[sp.realm].n}</div><div class="d">${known?pr[0]:""}${got?" · caught":""}</div></div>`;
    if(known) drawSprite(d.querySelector("canvas"),sp,"front"); else { const c=d.querySelector("canvas"); const x=c.getContext("2d"); x.fillStyle="#1f4531"; x.fillRect(12,12,24,24); }
    grid.appendChild(d); }
  $("#codex-count").textContent=`${nS} of ${SPECIES.length} seen · ${nC} caught`;
  $("#principles").innerHTML=Object.values(PRINCIPLES).map(([h,b])=>`<li><b>${h}.</b> ${b}</li>`).join("");
}

// ---------- hack lab ----------
function renderHacks(){
  const sel=$("#hack-active"); sel.innerHTML=HACKS.map((h,i)=>`<option value="${i}" ${i===ACTIVE_HACK?"selected":""}>${h.name}${h.builtin?" (built in)":""}</option>`).join("");
  sel.onchange=()=>{ ACTIVE_HACK=+sel.value; saveHacks(); renderHacks(); toast(`Active: ${HACKS[ACTIVE_HACK].name}`); };
  const h=HACKS[ACTIVE_HACK]; const ed=$("#hack-edit"); ed.innerHTML="";
  const ro=!!h.builtin;
  const top=document.createElement("div"); top.className="hrow";
  top.innerHTML=`<label>Name<input type="text" id="hk-name" value="${h.name.replace(/"/g,"&quot;")}" ${ro?"disabled":""}></label>
    <label>Wild level ×<input type="number" step="0.05" min="0.5" max="3" id="hk-wild" value="${h.wildLv}" ${ro?"disabled":""}></label>
    <label>Catch rate ×<input type="number" step="0.05" min="0.1" max="3" id="hk-catch" value="${h.catchX}" ${ro?"disabled":""}></label>
    <label>XP ×<input type="number" step="0.05" min="0.1" max="5" id="hk-xp" value="${h.xpX}" ${ro?"disabled":""}></label>`;
  ed.appendChild(top);
  if(ro){ const p=document.createElement("p"); p.className="muted"; p.textContent="Built-in hacks are read only. Duplicate one to make your own."; ed.appendChild(p); }
  const wrap=document.createElement("div"); wrap.className="tablewrap";
  const rows=SPECIES.map(b=>{ const o=(h.sp||{})[b.id]||{}; const st=o.st||b.st; const t=o.t||b.t; const evo=o.evo===null?null:(o.evo||b.evo);
    return `<tr data-id="${b.id}"><td>${b.n}</td>
      <td><input type="number" data-k="st0" value="${st[0]}" ${ro?"disabled":""}></td><td><input type="number" data-k="st1" value="${st[1]}" ${ro?"disabled":""}></td>
      <td><input type="number" data-k="st2" value="${st[2]}" ${ro?"disabled":""}></td><td><input type="number" data-k="st3" value="${st[3]}" ${ro?"disabled":""}></td>
      <td><select data-k="t0" ${ro?"disabled":""}>${TYPES.map(x=>`<option ${x===t[0]?"selected":""}>${x}</option>`).join("")}</select></td>
      <td><select data-k="t1" ${ro?"disabled":""}><option value="">—</option>${TYPES.map(x=>`<option ${x===t[1]?"selected":""}>${x}</option>`).join("")}</select></td>
      <td>${b.evo?`<input type="number" data-k="evo" min="2" max="99" value="${evo?evo.lv:""}" placeholder="never" ${ro?"disabled":""}>`:"—"}</td></tr>`; }).join("");
  wrap.innerHTML=`<table><thead><tr><th>Creature</th><th>HP</th><th>Atk</th><th>Def</th><th>Spd</th><th>Type 1</th><th>Type 2</th><th>Evolves at</th></tr></thead><tbody>${rows}</tbody></table>`;
  ed.appendChild(wrap);
  if(!ro){
    const commit=()=>{ h.name=$("#hk-name").value||"Untitled hack"; h.wildLv=+$("#hk-wild").value||1; h.catchX=+$("#hk-catch").value||1; h.xpX=+$("#hk-xp").value||1; h.sp={};
      wrap.querySelectorAll("tr[data-id]").forEach(tr=>{ const id=+tr.dataset.id, b=SPECIES_BY_ID[id]; const g=k=>tr.querySelector(`[data-k=${k}]`); const st=[+g("st0").value,+g("st1").value,+g("st2").value,+g("st3").value];
        const t=[g("t0").value, g("t1").value].filter(Boolean); const o={};
        if(st.some((v,i)=>v!==b.st[i])) o.st=st; if(t.join()!==b.t.join()) o.t=t;
        if(b.evo){ const v=g("evo").value; if(v===""){ o.evo=null; } else if(+v!==b.evo.lv){ o.evo={to:b.evo.to,lv:+v}; } }
        if(Object.keys(o).length) h.sp[id]=o; });
      saveHacks(); };
    ed.addEventListener("change",()=>{ commit(); sel.options[ACTIVE_HACK].textContent=h.name; });
  }
  $("#hack-text").value=JSON.stringify(h);
}
function bindHacks(){
  $("#hack-new").onclick=()=>{ HACKS.push({name:"My hack "+(HACKS.length-1),sp:{},wildLv:1,catchX:1,xpX:1}); ACTIVE_HACK=HACKS.length-1; saveHacks(); renderHacks(); };
  $("#hack-dup").onclick=()=>{ const c=JSON.parse(JSON.stringify(HACKS[ACTIVE_HACK])); delete c.builtin; c.name+=" copy"; HACKS.push(c); ACTIVE_HACK=HACKS.length-1; saveHacks(); renderHacks(); };
  $("#hack-del").onclick=async()=>{ const h=HACKS[ACTIVE_HACK]; if(h.builtin){ toast("Built-in hacks can't be deleted."); return; } if(await confirmBox(`Delete "${h.name}"?`)){ HACKS.splice(ACTIVE_HACK,1); ACTIVE_HACK=0; saveHacks(); renderHacks(); } };
  $("#hack-copy").onclick=()=>copyText($("#hack-text"),"Hack copied");
  $("#hack-paste").onclick=()=>{ try{ const h=JSON.parse($("#hack-text").value); if(!h||typeof h.name!=="string") throw 0; delete h.builtin; h.sp=h.sp||{}; HACKS.push(h); ACTIVE_HACK=HACKS.length-1; saveHacks(); renderHacks(); toast(`Loaded "${h.name}"`); }catch(e){ toast("That text isn't a hack."); } };
}
function copyText(ta,msg){ const t=ta.value; (navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(t):Promise.reject()).then(()=>toast(msg)).catch(()=>{ ta.focus(); ta.select(); toast("Select all and copy."); }); }

// ---------- saves ----------
function renderSlots(){
  const box=$("#slots"); box.innerHTML="";
  for(const n of [1,2,3]){ const s=slotInfo(n); const d=document.createElement("div"); d.className="slot";
    d.innerHTML=s?`<div class="h">Slot ${n} · ${s.lead} Lv ${s.lv}</div><div class="d">${s.realm} · ${s.n} creatures · ${s.caught} caught · ${s.hack}<br>${new Date(s.saved).toLocaleString()}</div>`:`<div class="h">Slot ${n}</div><div class="d">Empty</div>`;
    const row=document.createElement("div"); row.className="btnrow";
    const mk=(l,fn,cls="")=>{ const b=document.createElement("button"); b.className="btn "+cls; b.textContent=l; b.onclick=fn; row.appendChild(b); return b; };
    mk("Save here",async()=>{ if(!G){ toast("Nothing to save yet."); return; } if(s && !(await confirmBox(`Overwrite slot ${n}?`))) return; saveSlot(n)?toast(`Saved to slot ${n}`):toast("Couldn't write to this browser's storage."); renderSlots(); },"primary");
    if(s){ mk("Load",async()=>{ if(G && !(await confirmBox("Load this slot? Unsaved progress is lost."))) return; try{ loadSlot(n); B=null; showTab("play"); enterWorld("Loaded."); toast(`Slot ${n} loaded`);}catch(e){ toast(e.message);} });
      mk("Copy text",()=>{ $("#save-text").value=s.txt; copyText($("#save-text"),"Save text copied"); });
      for(const o of [1,2,3]) if(o!==n) mk(`→ ${o}`,async()=>{ if(slotInfo(o) && !(await confirmBox(`Overwrite slot ${o} with slot ${n}?`))) return; copySlot(n,o); toast(`Copied to slot ${o}`); renderSlots(); });
      mk("Delete",async()=>{ if(await confirmBox(`Delete slot ${n}?`)){ deleteSlot(n); renderSlots(); } },"danger"); }
    d.appendChild(row); box.appendChild(d); }
}
function bindSaves(){
  $("#save-copy").onclick=()=>{ if(!G){ toast("Nothing to copy yet."); return; } $("#save-text").value=serialize(); copyText($("#save-text"),"Current game copied"); };
  for(const n of [1,2,3]) $("#save-load-"+n).onclick=()=>{ try{ const txt=$("#save-text").value.trim(); JSON.parse(txt); deserialize(txt); saveSlot(n); renderSlots(); toast(`Loaded into slot ${n}`); }catch(e){ toast("That text isn't a save."); } };
}

// ---------- boot ----------
function start(hot){
  $$(".tabs button").forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
  $("#btn-new").onclick=()=>{ showScreen("starter"); renderStarters(); };
  $("#btn-continue").onclick=()=>{ let best=null; for(const n of [1,2,3]){ const s=slotInfo(n); if(s&&(!best||s.saved>best.saved)) best={...s,n}; } if(best){ loadSlot(best.n); enterWorld("Welcome back."); } };
  bindInput(); bindHacks(); bindSaves();
  if(hot && hot.G){ G=hot.G; B=null; }
  renderTitle(); renderCodex();
  const tab=location.hash.replace("#",""); showTab(["play","party","codex","hacks","saves"].includes(tab)?tab:"play");
  if(G) enterWorld("Resumed."); else showScreen("title");
  if(window.claude && window.claude.hot && window.claude.hot.snapshot) window.claude.hot.snapshot(()=>({G}));
  window.addEventListener("hashchange",()=>{ const t=location.hash.replace("#",""); if(["play","party","codex","hacks","saves"].includes(t)) showTab(t); });
  // self-test hook for automated checks: ?selftest in the hash is not available, so use a global.
  window.__realms={newGame,makeMon,startBattle,battleRound,stepPlayer,serialize,deserialize,getSpecies,calcStats,gainXp,get G(){return G;},get B(){return B;}};
}
(window.claude && window.claude.hot && window.claude.hot.ready) ? window.claude.hot.ready(start) : start((window.claude&&window.claude.hot&&window.claude.hot.data)||{});
