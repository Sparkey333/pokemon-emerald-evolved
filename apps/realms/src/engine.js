/* Game rules. No DOM in here; ui.js renders what this produces. */

const DEFAULT_HACK = () => ({name:"Base game",sp:{},wildLv:1,catchX:1,xpX:1,builtin:true});
const HARD_HACK = () => ({name:"Hard Mode",sp:{},wildLv:1.25,catchX:.7,xpX:.9,builtin:true});

const store = {
  get(k,d){ try{ const v=localStorage.getItem(k); return v==null?d:JSON.parse(v);}catch(e){ return d; } },
  set(k,v){ try{ localStorage.setItem(k,JSON.stringify(v)); return true;}catch(e){ return false; } },
  del(k){ try{ localStorage.removeItem(k);}catch(e){} },
};

// ---------- hacks ----------
function loadHacks(){
  const h=store.get("realms.hacks",null);
  if(h && Array.isArray(h) && h.length) return h;
  return [DEFAULT_HACK(),HARD_HACK()];
}
let HACKS = loadHacks();
let ACTIVE_HACK = Math.min(store.get("realms.hack.active",0), HACKS.length-1);
function saveHacks(){ store.set("realms.hacks",HACKS); store.set("realms.hack.active",ACTIVE_HACK); }
function activeHack(){ return (G && G.hack) ? G.hack : HACKS[ACTIVE_HACK]; }

/** Species with the active hack's overrides applied. */
function getSpecies(id){
  const base=SPECIES_BY_ID[id]; const o=(activeHack().sp||{})[id];
  if(!o) return base;
  const s={...base};
  if(o.st) s.st=o.st.slice();
  if(o.t) s.t=o.t.slice();
  if(o.evo!==undefined) s.evo = o.evo===null ? undefined : {to:(base.evo||{}).to||o.evo.to, lv:o.evo.lv};
  return s;
}

// ---------- creatures ----------
function xpForLevel(lv){ return lv*lv*lv; }
function calcStats(mon){
  const sp=getSpecies(mon.sid), [bh,ba,bd,bs]=sp.st, L=mon.lv;
  return { hp:Math.floor(bh*2*L/100)+L+10, atk:Math.floor(ba*2*L/100)+5, def:Math.floor(bd*2*L/100)+5, spd:Math.floor(bs*2*L/100)+5 };
}
function movesAtLevel(sp, lv){ return sp.learn.filter(([l])=>l<=lv).map(([,m])=>m).filter((m,i,a)=>a.indexOf(m)===i).slice(-4); }
function makeMon(sid, lv){
  const sp=getSpecies(sid);
  const m={sid,lv,xp:xpForLevel(lv),moves:movesAtLevel(sp,lv),hp:0,uid:Math.random().toString(36).slice(2,9)};
  m.hp=calcStats(m).hp; return m;
}
function monName(m){ return getSpecies(m.sid).n; }

/** Apply xp; returns a list of events for the UI to narrate. */
function gainXp(m, amount){
  const ev=[]; m.xp+=amount;
  while(m.lv<100 && m.xp>=xpForLevel(m.lv+1)){
    const before=calcStats(m).hp; m.lv++; const after=calcStats(m).hp; m.hp=Math.min(after, m.hp+(after-before));
    ev.push({k:"level",lv:m.lv});
    const sp=getSpecies(m.sid);
    for(const [l,mv] of sp.learn) if(l===m.lv && !m.moves.includes(mv)){
      if(m.moves.length<4) m.moves.push(mv); else { m.moves.shift(); m.moves.push(mv); }
      ev.push({k:"learn",move:mv});
    }
    if(sp.evo && m.lv>=sp.evo.lv){
      const from=sp.n; m.sid=sp.evo.to; const nsp=getSpecies(m.sid);
      const hpNow=calcStats(m).hp; m.hp=Math.min(hpNow, m.hp+8);
      ev.push({k:"evolve",from,to:nsp.n});
      G.seen[m.sid]=1; G.caught[m.sid]=1;
    }
  }
  return ev;
}

// ---------- world ----------
let G=null;
function newGame(starterId){
  G={ realm:0, x:2, y:2, party:[makeMon(starterId,5)], box:[], orbs:8, tonics:3, seen:{}, caught:{}, steps:0,
      shrineDone:false, hack:JSON.parse(JSON.stringify(HACKS[ACTIVE_HACK])), started:Date.now() };
  G.seen[starterId]=1; G.caught[starterId]=1; STARTERS.forEach(s=>G.seen[s]=1);
  return G;
}
function tileAt(rx,x,y){ const r=REALMS[rx]; const row=r.map[y]; return row?row[x]:"T"; }
function walkable(rx,x,y){ const t=tileAt(rx,x,y); return !WALLS.has(t); }
function lead(){ return G.party.find(m=>m.hp>0) || G.party[0]; }
function allFainted(){ return G.party.every(m=>m.hp<=0); }

/** Move the player. Returns an event object or null. */
function stepPlayer(dir){
  const d={up:[0,-1],down:[0,1],left:[-1,0],right:[1,0]}[dir]; if(!d) return null;
  const nx=G.x+d[0], ny=G.y+d[1];
  if(!walkable(G.realm,nx,ny)) return {k:"bump"};
  G.x=nx; G.y=ny; G.steps++;
  const t=tileAt(G.realm,nx,ny);
  const realm=REALMS[G.realm];
  if(t==="H"){ G.party.forEach(m=>{ m.hp=calcStats(m).hp; }); return {k:"heal"}; }
  if(realm.gates[t]){ const g=realm.gates[t]; G.realm=g.to; G.x=g.ax; G.y=g.ay; return {k:"gate",realm:REALMS[g.to].n}; }
  if(t==="X" && !G.shrineDone){ return {k:"shrine"}; }
  if(t==="G" && Math.random()<0.14){ return {k:"encounter",foe:rollEncounter(realm)}; }
  return null;
}
function rollEncounter(realm){
  const tot=realm.enc.reduce((a,e)=>a+e[1],0); let r=Math.random()*tot;
  for(const [id,w,lo,hi] of realm.enc){ r-=w; if(r<=0){ const lv=Math.max(1,Math.round((lo+Math.random()*(hi-lo))*activeHack().wildLv)); G.seen[id]=1; return makeMon(id,lv); } }
  const [id,,lo]=realm.enc[0]; G.seen[id]=1; return makeMon(id,lo);
}

// ---------- battle ----------
let B=null;
function startBattle(foe, opts={}){
  B={foe, allyIdx:G.party.indexOf(lead()), st:{ally:{atk:0,def:0},foe:{atk:0,def:0}}, over:false, result:null, legend:!!opts.legend, log:[]};
  return B;
}
function ally(){ return G.party[B.allyIdx]; }
function stageMult(n){ return n>=0 ? (2+n)/2 : 2/(2-n); }
function dmg(att, def, move, attSt, defSt){
  const mv=MOVES[move]; if(!mv.p) return {d:0,eff:1,crit:false};
  const asp=getSpecies(att.sid), dsp=getSpecies(def.sid), as=calcStats(att), ds=calcStats(def);
  const A=as.atk*stageMult(attSt.atk), D=Math.max(1,ds.def*stageMult(defSt.def));
  const stab=asp.t.includes(mv.t)?1.5:1, eff=effectiveness(mv.t,dsp.t), crit=Math.random()<1/16;
  const base=((2*att.lv/5+2)*mv.p*A/D)/50+2;
  const d=Math.max(eff>0?1:0, Math.floor(base*stab*eff*(crit?1.5:1)*(0.85+Math.random()*0.15)));
  return {d,eff,crit};
}
function useMove(user, target, move, uSt, tSt, who){
  const mv=MOVES[move]; const lines=[`${monName(user)} used ${mv.n}!`];
  if(Math.random()*100>mv.a){ lines.push("It missed!"); return lines; }
  if(mv.p){
    const {d,eff,crit}=dmg(user,target,move,uSt,tSt); target.hp=Math.max(0,target.hp-d);
    if(eff===0) lines.push("It had no effect."); else if(eff>1) lines.push("It's super effective!"); else if(eff<1) lines.push("It's not very effective.");
    if(crit && eff>0) lines.push("A critical hit!");
  } else if(mv.fx){
    if(mv.fx.heal){ const mx=calcStats(user).hp; const h=Math.floor(mx*mv.fx.heal); user.hp=Math.min(mx,user.hp+h); lines.push(`${monName(user)} recovered ${h} HP.`); }
    if(mv.fx.stat){ const tgt=mv.fx.who==="self"?uSt:tSt; const name=mv.fx.who==="self"?monName(user):monName(target); tgt[mv.fx.stat]=Math.max(-4,Math.min(4,tgt[mv.fx.stat]+mv.fx.d)); lines.push(`${name}'s ${mv.fx.stat==="atk"?"attack":"defence"} ${mv.fx.d>0?"rose":"fell"}.`); }
  }
  return lines;
}
function foeMove(){ const f=B.foe; return f.moves[Math.floor(Math.random()*f.moves.length)]; }

/** One battle round. action: {k:"move",move}|{k:"catch"}|{k:"swap",idx}|{k:"run"}|{k:"tonic"} */
function battleRound(action){
  const out={lines:[],events:[]}; if(B.over) return out;
  const a=ally(), f=B.foe;
  let allyActs=true;
  if(action.k==="run"){
    if(B.legend){ out.lines.push("The guardian blocks the way out."); allyActs=false; }
    else if(Math.random()<0.7+ (calcStats(a).spd>calcStats(f).spd?0.25:0)){ out.lines.push("Got away safely."); B.over=true; B.result="ran"; return out; }
    else { out.lines.push("Couldn't escape!"); allyActs=false; }
  }
  if(action.k==="catch"){
    if(G.orbs<=0){ out.lines.push("No orbs left."); return out; }
    G.orbs--; const sp=getSpecies(f.sid); const mx=calcStats(f).hp;
    const p=Math.min(.95, (sp.catch/255)*(1-(f.hp/mx)*0.7)*activeHack().catchX*1.2 + 0.03);
    out.lines.push(`Threw an orb at ${sp.n}...`);
    if(Math.random()<p){ out.lines.push(`${sp.n} was caught!`); G.caught[f.sid]=1; f.hp=Math.max(1,f.hp); if(G.party.length<6) G.party.push(f); else G.box.push(f);
      B.over=true; B.result="caught"; out.events.push({k:"caught",where:G.party.includes(f)?"party":"box"}); return out; }
    out.lines.push("It broke free!"); allyActs=false;
  }
  if(action.k==="tonic"){
    if(G.tonics<=0){ out.lines.push("No tonics left."); return out; }
    G.tonics--; const mx=calcStats(a).hp; const h=Math.floor(mx*.5); a.hp=Math.min(mx,a.hp+h); out.lines.push(`${monName(a)} drank a tonic and recovered ${h} HP.`); allyActs=false;
  }
  if(action.k==="swap"){
    const m=G.party[action.idx]; if(!m||m.hp<=0||action.idx===B.allyIdx){ out.lines.push("That one can't fight right now."); return out; }
    B.allyIdx=action.idx; B.st.ally={atk:0,def:0}; out.lines.push(`Go, ${monName(m)}!`); allyActs=false;
  }
  const a2=ally();
  const first = allyActs && (calcStats(a2).spd>=calcStats(f).spd);
  const doAlly=()=>{ if(allyActs && action.k==="move") out.lines.push(...useMove(a2,f,action.move,B.st.ally,B.st.foe,"ally")); };
  const doFoe=()=>{ if(f.hp>0) out.lines.push(...useMove(f,a2,foeMove(),B.st.foe,B.st.ally,"foe")); };
  if(first){ doAlly(); if(f.hp>0) doFoe(); } else { doFoe(); if(a2.hp>0) doAlly(); }

  if(f.hp<=0){
    out.lines.push(`${monName(f)} fainted.`);
    const xp=Math.floor(getSpecies(f.sid).xp*f.lv/7*activeHack().xpX)+1;
    out.lines.push(`${monName(a2)} gained ${xp} XP.`);
    for(const e of gainXp(a2,xp)){
      if(e.k==="level") out.lines.push(`${monName(a2)} grew to level ${e.lv}!`);
      if(e.k==="learn") out.lines.push(`${monName(a2)} learned ${MOVES[e.move].n}!`);
      if(e.k==="evolve") out.lines.push(`${e.from} evolved into ${e.to}!`);
      out.events.push(e);
    }
    if(B.legend){ G.shrineDone=true; }
    B.over=true; B.result="won"; return out;
  }
  if(a2.hp<=0){
    out.lines.push(`${monName(a2)} fainted!`);
    if(allFainted()){ out.lines.push("Everyone is out. You hurry back to the shrine."); B.over=true; B.result="lost"; out.events.push({k:"wipe"}); }
    else { out.events.push({k:"needswap"}); }
  }
  return out;
}
function wipeToShrine(){
  const r=REALMS[G.realm]; for(let y=0;y<r.map.length;y++){ const x=r.map[y].indexOf("H"); if(x>=0){ G.x=x; G.y=y; break; } }
  G.party.forEach(m=>{ m.hp=calcStats(m).hp; });
}

// ---------- saves ----------
function serialize(){ return JSON.stringify({v:1,saved:Date.now(),G}); }
function deserialize(txt){
  const o=JSON.parse(txt); if(!o||o.v!==1||!o.G||!Array.isArray(o.G.party)) throw new Error("Not a valid Emerald Realms save.");
  G=o.G; if(!G.hack) G.hack=DEFAULT_HACK(); return G;
}
function slotKey(n){ return "realms.slot."+n; }
function saveSlot(n){ return store.set(slotKey(n), {saved:Date.now(),txt:serialize()}); }
function loadSlot(n){ const s=store.get(slotKey(n),null); if(!s) return null; return deserialize(s.txt); }
function slotInfo(n){ const s=store.get(slotKey(n),null); if(!s) return null; try{ const o=JSON.parse(s.txt); const g=o.G; return {saved:s.saved, realm:REALMS[g.realm].n, lead:monName(g.party[0]), lv:g.party[0].lv, n:g.party.length+g.box.length, caught:Object.keys(g.caught).length, hack:(g.hack||{}).name, txt:s.txt}; }catch(e){ return null; } }
function copySlot(a,b){ const s=store.get(slotKey(a),null); if(!s) return false; return store.set(slotKey(b),s); }
function deleteSlot(n){ store.del(slotKey(n)); }
