/* All game data. Every creature, name, and realm here is original to this
   project. The design principles are genre conventions, listed openly. */

const TYPES = ["Normal","Grass","Fire","Water","Bug","Rock","Ice","Electric","Flying","Ghost","Psychic","Dragon"];
const TYPE_COLOR = {Normal:"#b8b8a8",Grass:"#3ddc84",Fire:"#ff8a4c",Water:"#5ec8f2",Bug:"#b6d94c",Rock:"#c9a66b",
  Ice:"#a8e6f0",Electric:"#f5e04c",Flying:"#b9c7ff",Ghost:"#9b7bff",Psychic:"#ff7bd1",Dragon:"#7c6bff"};

// attacker -> defender -> multiplier (absent = 1). Our own chart; the type
// triangle and a few classic matchups are kept because players expect them.
const CHART = {
  Normal:{Rock:.5,Ghost:0},
  Grass:{Water:2,Rock:2,Fire:.5,Grass:.5,Bug:.5,Flying:.5,Dragon:.5},
  Fire:{Grass:2,Bug:2,Ice:2,Water:.5,Fire:.5,Rock:.5,Dragon:.5},
  Water:{Fire:2,Rock:2,Water:.5,Grass:.5,Dragon:.5},
  Bug:{Grass:2,Psychic:2,Fire:.5,Flying:.5,Ghost:.5},
  Rock:{Fire:2,Ice:2,Flying:2,Bug:2},
  Ice:{Grass:2,Flying:2,Dragon:2,Fire:.5,Water:.5,Ice:.5},
  Electric:{Water:2,Flying:2,Grass:.5,Electric:.5,Dragon:.5},
  Flying:{Grass:2,Bug:2,Rock:.5,Electric:.5},
  Ghost:{Ghost:2,Psychic:2,Normal:0},
  Psychic:{Rock:2,Psychic:.5,Ghost:.5},
  Dragon:{Dragon:2,Rock:.5},
};
function effectiveness(atk, defTypes){ return defTypes.reduce((m,t)=>m*((CHART[atk]||{})[t] ?? 1), 1); }

// pow 0 = status move. fx: {heal:0.5} or {stat:"atk"|"def", who:"self"|"foe", d:+1/-1}
const MOVES = {
  tackle:{n:"Tackle",t:"Normal",p:40,a:100}, scratch:{n:"Scratch",t:"Normal",p:40,a:100},
  slam:{n:"Slam",t:"Normal",p:70,a:90}, growl:{n:"Growl",t:"Normal",p:0,a:100,fx:{stat:"atk",who:"foe",d:-1}},
  harden:{n:"Harden",t:"Normal",p:0,a:100,fx:{stat:"def",who:"self",d:1}}, mend:{n:"Mend",t:"Normal",p:0,a:100,fx:{heal:.5}},
  leaflet:{n:"Leaflet",t:"Grass",p:40,a:100}, vinelash:{n:"Vine Lash",t:"Grass",p:60,a:100},
  petalstorm:{n:"Petal Storm",t:"Grass",p:90,a:90}, bloom:{n:"Bloom",t:"Grass",p:0,a:100,fx:{heal:.5}},
  ember:{n:"Ember",t:"Fire",p:40,a:100}, flamejet:{n:"Flame Jet",t:"Fire",p:65,a:100}, inferno:{n:"Inferno",t:"Fire",p:95,a:85},
  bubble:{n:"Bubble",t:"Water",p:40,a:100}, waterjet:{n:"Water Jet",t:"Water",p:65,a:100}, tidalcrash:{n:"Tidal Crash",t:"Water",p:95,a:85},
  nibble:{n:"Nibble",t:"Bug",p:35,a:100}, swarmbite:{n:"Swarm Bite",t:"Bug",p:60,a:100},
  pebble:{n:"Pebble",t:"Rock",p:40,a:100}, rockslam:{n:"Rock Slam",t:"Rock",p:75,a:90},
  frostnip:{n:"Frost Nip",t:"Ice",p:40,a:100}, icelance:{n:"Ice Lance",t:"Ice",p:70,a:100},
  spark:{n:"Spark",t:"Electric",p:40,a:100}, voltbolt:{n:"Volt Bolt",t:"Electric",p:75,a:100}, thunderclap:{n:"Thunderclap",t:"Electric",p:95,a:85},
  gust:{n:"Gust",t:"Flying",p:40,a:100}, wingcut:{n:"Wing Cut",t:"Flying",p:65,a:100},
  haunt:{n:"Haunt",t:"Ghost",p:45,a:100}, spectreclaw:{n:"Spectre Claw",t:"Ghost",p:75,a:100},
  mindjab:{n:"Mind Jab",t:"Psychic",p:45,a:100}, psywave:{n:"Psy Wave",t:"Psychic",p:75,a:100},
  dragonsnap:{n:"Dragon Snap",t:"Dragon",p:60,a:100}, dragonfury:{n:"Dragon Fury",t:"Dragon",p:95,a:85},
};

// Species. st = [hp,atk,def,spd]. evo = {to,lv}. plan = sprite body plan.
// pal = [main, belly, accent]. pr = design-principle id (see PRINCIPLES).
const SPECIES = [
  // starters — the three DIY lines, now with original base forms and no Kanto ancestry
  {id:1,n:"Sproutle",t:["Grass"],st:[45,48,46,48],catch:45,xp:64,evo:{to:2,lv:16},plan:"quad",pal:["#4fcf7a","#d8f5a8","#ff7bd1"],realm:0,pr:"triangle",
    learn:[[1,"tackle"],[1,"growl"],[5,"leaflet"],[11,"vinelash"],[17,"bloom"]]},
  {id:2,n:"Florasaur",t:["Grass"],st:[60,62,63,60],catch:45,xp:142,evo:{to:3,lv:34},plan:"quad",pal:["#2fa85f","#cdeea0","#ff5cc1"],realm:0,pr:"triangle",
    learn:[[1,"tackle"],[1,"leaflet"],[11,"vinelash"],[17,"bloom"],[24,"slam"],[31,"petalstorm"]]},
  {id:3,n:"Verdantaur",t:["Grass"],st:[82,84,83,80],catch:45,xp:236,plan:"quad",pal:["#1f8a4b","#bde68e","#ff3fb0"],realm:0,pr:"triangle",
    learn:[[1,"vinelash"],[1,"bloom"],[24,"slam"],[31,"petalstorm"],[40,"harden"]]},
  {id:4,n:"Cindrake",t:["Fire"],st:[40,52,43,65],catch:45,xp:62,evo:{to:5,lv:16},plan:"biped",pal:["#ff8a4c","#ffe0a8","#ffd93d"],realm:0,pr:"triangle",
    learn:[[1,"scratch"],[1,"growl"],[5,"ember"],[12,"flamejet"],[18,"slam"]]},
  {id:5,n:"Charblaze",t:["Fire"],st:[58,64,58,80],catch:45,xp:142,evo:{to:6,lv:34},plan:"biped",pal:["#f46a2e","#ffd39a","#ffc400"],realm:0,pr:"triangle",
    learn:[[1,"scratch"],[1,"ember"],[12,"flamejet"],[18,"slam"],[26,"wingcut"],[33,"inferno"]]},
  {id:6,n:"Infernodrake",t:["Fire","Dragon"],st:[78,84,78,100],catch:45,xp:240,plan:"serpent",pal:["#d9441a","#ffc27a","#ffea00"],realm:0,pr:"triangle",
    learn:[[1,"flamejet"],[1,"wingcut"],[26,"dragonsnap"],[33,"inferno"],[42,"dragonfury"]]},
  {id:7,n:"Shellow",t:["Water"],st:[44,48,65,43],catch:45,xp:63,evo:{to:8,lv:16},plan:"turtle",pal:["#5ec8f2","#e4f6ff","#2d7fb3"],realm:0,pr:"triangle",
    learn:[[1,"tackle"],[1,"harden"],[5,"bubble"],[12,"waterjet"],[19,"slam"]]},
  {id:8,n:"Torrentoise",t:["Water"],st:[59,63,80,58],catch:45,xp:142,evo:{to:9,lv:34},plan:"turtle",pal:["#3aa9dc","#d6f0ff","#1d5f8a"],realm:0,pr:"triangle",
    learn:[[1,"tackle"],[1,"bubble"],[12,"waterjet"],[19,"slam"],[27,"icelance"],[35,"tidalcrash"]]},
  {id:9,n:"Tsunamoise",t:["Water"],st:[79,83,105,78],catch:45,xp:239,plan:"turtle",pal:["#2186b8","#c7ebff","#123f5e"],realm:0,pr:"triangle",
    learn:[[1,"waterjet"],[1,"harden"],[27,"icelance"],[35,"tidalcrash"],[44,"mend"]]},

  // Verdant Realm
  {id:10,n:"Mothling",t:["Bug"],st:[40,35,30,45],catch:255,xp:39,evo:{to:11,lv:14},plan:"bug",pal:["#b6d94c","#f0f7c8","#5a7f6a"],realm:0,pr:"earlybug",
    learn:[[1,"nibble"],[4,"harden"],[9,"leaflet"]]},
  {id:11,n:"Lumoth",t:["Bug","Grass"],st:[60,55,50,70],catch:120,xp:120,plan:"bug",pal:["#9ccc3c","#fdf6c3","#3ddc84"],realm:0,pr:"earlybug",
    learn:[[1,"nibble"],[1,"leaflet"],[14,"swarmbite"],[20,"vinelash"],[28,"gust"]]},
  {id:12,n:"Bramblit",t:["Normal"],st:[38,45,38,50],catch:255,xp:45,evo:{to:13,lv:18},plan:"quad",pal:["#c9a66b","#f1e2c3","#4fcf7a"],realm:0,pr:"pest",
    learn:[[1,"tackle"],[3,"growl"],[8,"scratch"],[14,"leaflet"]]},
  {id:13,n:"Thornhare",t:["Normal","Grass"],st:[66,72,58,78],catch:127,xp:140,plan:"quad",pal:["#a8824a","#ecd8ad","#2fa85f"],realm:0,pr:"pest",
    learn:[[1,"scratch"],[1,"leaflet"],[18,"vinelash"],[24,"slam"],[32,"petalstorm"]]},
  {id:14,n:"Pipwing",t:["Normal","Flying"],st:[40,42,36,60],catch:255,xp:48,evo:{to:15,lv:20},plan:"bird",pal:["#b9c7ff","#fff3d6","#f5b942"],realm:0,pr:"routebird",
    learn:[[1,"tackle"],[5,"gust"],[11,"growl"],[16,"wingcut"]]},
  {id:15,n:"Galewing",t:["Normal","Flying"],st:[68,70,56,95],catch:120,xp:148,plan:"bird",pal:["#8fa3ff","#fff0c8","#ff8a4c"],realm:0,pr:"routebird",
    learn:[[1,"gust"],[1,"wingcut"],[20,"slam"],[28,"wingcut"],[36,"dragonsnap"]]},
  {id:16,n:"Mossloaf",t:["Grass"],st:[90,45,80,20],catch:150,xp:110,plan:"blob",pal:["#5a9a4a","#9fd48a","#3b2a1a"],realm:0,pr:"bruiser",
    learn:[[1,"tackle"],[1,"harden"],[7,"leaflet"],[15,"bloom"],[23,"slam"],[31,"vinelash"]]},

  // Ember Realm
  {id:17,n:"Cindermite",t:["Fire","Bug"],st:[42,50,40,55],catch:200,xp:60,evo:{to:18,lv:22},plan:"bug",pal:["#ff8a4c","#ffd39a","#3b2a1a"],realm:1,pr:"earlybug",
    learn:[[1,"nibble"],[6,"ember"],[12,"swarmbite"],[18,"flamejet"]]},
  {id:18,n:"Pyroclast",t:["Fire","Rock"],st:[70,78,82,50],catch:90,xp:165,plan:"blob",pal:["#d9441a","#ffb347","#4a2a1a"],realm:1,pr:"mascot",
    learn:[[1,"ember"],[1,"pebble"],[22,"flamejet"],[28,"rockslam"],[36,"inferno"]]},
  {id:19,n:"Ashpup",t:["Fire"],st:[45,55,40,60],catch:190,xp:62,evo:{to:20,lv:24},plan:"quad",pal:["#8c8c8c","#ffd39a","#ff8a4c"],realm:1,pr:"pest",
    learn:[[1,"tackle"],[4,"growl"],[9,"ember"],[16,"flamejet"]]},
  {id:20,n:"Kilnhound",t:["Fire"],st:[72,85,60,85],catch:75,xp:170,plan:"quad",pal:["#5a5a5a","#ffc27a","#ff5a1a"],realm:1,pr:"pest",
    learn:[[1,"ember"],[1,"scratch"],[24,"flamejet"],[30,"slam"],[38,"inferno"]]},
  {id:21,n:"Rubblet",t:["Rock"],st:[50,52,70,30],catch:200,xp:60,evo:{to:22,lv:26},plan:"blob",pal:["#c9a66b","#e8d3a8","#5a4a3a"],realm:1,pr:"bruiser",
    learn:[[1,"tackle"],[5,"harden"],[10,"pebble"],[18,"slam"]]},
  {id:22,n:"Craglodon",t:["Rock"],st:[85,90,110,40],catch:70,xp:185,plan:"quad",pal:["#a0804a","#d8c398","#3a2a1a"],realm:1,pr:"bruiser",
    learn:[[1,"pebble"],[1,"harden"],[26,"rockslam"],[34,"slam"],[42,"dragonsnap"]]},

  // Tide Realm
  {id:23,n:"Finlet",t:["Water"],st:[42,48,40,62],catch:200,xp:58,evo:{to:24,lv:22},plan:"serpent",pal:["#5ec8f2","#e4f6ff","#ff6b6b"],realm:2,pr:"pest",
    learn:[[1,"tackle"],[5,"bubble"],[11,"growl"],[17,"waterjet"]]},
  {id:24,n:"Marlance",t:["Water"],st:[68,88,62,92],catch:80,xp:168,plan:"serpent",pal:["#2d7fb3","#c7ebff","#ff3f3f"],realm:2,pr:"mascot",
    learn:[[1,"bubble"],[1,"waterjet"],[22,"slam"],[30,"icelance"],[38,"tidalcrash"]]},
  {id:25,n:"Frostkit",t:["Ice"],st:[44,46,42,60],catch:180,xp:60,evo:{to:26,lv:28},plan:"quad",pal:["#a8e6f0","#ffffff","#5ec8f2"],realm:2,pr:"cute",
    learn:[[1,"scratch"],[5,"frostnip"],[12,"growl"],[20,"icelance"]]},
  {id:26,n:"Glacielle",t:["Ice","Water"],st:[72,74,80,78],catch:70,xp:175,plan:"quad",pal:["#7fd1e6","#ffffff","#2186b8"],realm:2,pr:"cute",
    learn:[[1,"frostnip"],[1,"bubble"],[28,"icelance"],[34,"waterjet"],[42,"tidalcrash"]]},
  {id:27,n:"Bubblob",t:["Water"],st:[95,40,70,25],catch:160,xp:105,plan:"blob",pal:["#78d2f0","#eafbff","#2d7fb3"],realm:2,pr:"bruiser",
    learn:[[1,"bubble"],[1,"harden"],[9,"tackle"],[17,"mend"],[25,"waterjet"],[33,"slam"]]},

  // Storm Realm
  {id:28,n:"Sparklet",t:["Electric"],st:[42,55,40,75],catch:170,xp:65,evo:{to:29,lv:26},plan:"bird",pal:["#f5e04c","#fffbd6","#5ec8f2"],realm:3,pr:"routebird",
    learn:[[1,"tackle"],[6,"spark"],[12,"gust"],[19,"voltbolt"]]},
  {id:29,n:"Voltern",t:["Electric","Flying"],st:[70,85,60,110],catch:70,xp:180,plan:"bird",pal:["#e6c400","#fff6b8","#2d7fb3"],realm:3,pr:"routebird",
    learn:[[1,"spark"],[1,"gust"],[26,"voltbolt"],[32,"wingcut"],[40,"thunderclap"]]},
  {id:30,n:"Zapmite",t:["Electric","Bug"],st:[55,70,50,88],catch:120,xp:130,plan:"bug",pal:["#d8e04c","#fff9c0","#7c6bff"],realm:3,pr:"earlybug",
    learn:[[1,"nibble"],[1,"spark"],[14,"swarmbite"],[22,"voltbolt"],[30,"harden"]]},
  {id:31,n:"Cloudrake",t:["Flying","Dragon"],st:[80,92,70,105],catch:35,xp:210,plan:"serpent",pal:["#dfe6ff","#ffffff","#7c6bff"],realm:3,pr:"latedragon",
    learn:[[1,"gust"],[1,"dragonsnap"],[24,"wingcut"],[32,"slam"],[40,"dragonfury"]]},

  // Dusk Realm
  {id:32,n:"Wispling",t:["Ghost"],st:[40,55,40,70],catch:140,xp:70,evo:{to:33,lv:30},plan:"ghost",pal:["#9b7bff","#e6ddff","#ff7bd1"],realm:4,pr:"ghostlate",
    learn:[[1,"haunt"],[8,"growl"],[16,"mindjab"],[24,"spectreclaw"]]},
  {id:33,n:"Phantasm",t:["Ghost"],st:[68,95,65,100],catch:60,xp:190,plan:"ghost",pal:["#6f4fe0","#d9ccff","#ff3fb0"],realm:4,pr:"ghostlate",
    learn:[[1,"haunt"],[1,"spectreclaw"],[30,"psywave"],[38,"slam"],[46,"dragonsnap"]]},
  {id:34,n:"Mindmote",t:["Psychic"],st:[45,60,45,65],catch:140,xp:72,evo:{to:35,lv:30},plan:"blob",pal:["#ff7bd1","#ffe1f4","#7c6bff"],realm:4,pr:"ghostlate",
    learn:[[1,"mindjab"],[8,"harden"],[16,"growl"],[24,"psywave"]]},
  {id:35,n:"Psylith",t:["Psychic","Rock"],st:[75,98,85,70],catch:60,xp:195,plan:"blob",pal:["#e05cb3","#ffd1ee","#4a2a5a"],realm:4,pr:"ghostlate",
    learn:[[1,"mindjab"],[1,"pebble"],[30,"psywave"],[36,"rockslam"],[44,"mend"]]},
  {id:36,n:"Aetherion",t:["Dragon","Psychic"],st:[110,120,100,110],catch:5,xp:320,plan:"serpent",pal:["#8f7bff","#f0ecff","#3ddc84"],realm:4,pr:"legend",
    learn:[[1,"dragonsnap"],[1,"psywave"],[1,"mend"],[50,"dragonfury"],[55,"thunderclap"]]},
];
const SPECIES_BY_ID = Object.fromEntries(SPECIES.map(s=>[s.id,s]));

const PRINCIPLES = {
  triangle:["Type triangle starters","Three partners in a rock-paper-scissors loop, each a three-stage line that finishes just past the midgame."],
  earlybug:["Early bug, fast payoff","A weak insect in the first grass that evolves within a dozen levels, so the first evolution happens early."],
  pest:["The regional pest","A common Normal-type on every early route; unremarkable alone, surprisingly strong fully grown."],
  routebird:["The route bird","A Normal/Flying line found early, carried by many players to the end out of loyalty."],
  bruiser:["Slow pure-type bruiser","High HP and defence, low speed: a wall that teaches the value of stats over flash."],
  mascot:["Realm mascot","Each realm has one creature whose silhouette and typing say where you are."],
  cute:["Cute now, fierce later","A small, round first stage that grows into something sharp."],
  latedragon:["The rare late dragon","A scarce dual-type with a dragon half, hard to catch, worth the hunt."],
  ghostlate:["The dark realm gates late","Ghosts and psychics live where you arrive last, so the type chart has a final twist."],
  legend:["One legend at the end","A single guardian with the highest stats in the game, met once, at the furthest point."],
};

// Realm maps, 16x12. T/W/L/C/K walls, . path, G tall grass, H heal shrine,
// S start, a/b/c gates, X the guardian's shrine.
const REALMS = [
  {n:"Verdant Realm",bg:"#0b2a16",wall:"#143d1f",path:"#3b4a2a",grass:"#2f7a3a",grass2:"#3a9447",
   gates:{a:{to:1,ax:2,ay:7},b:{to:2,ax:2,ay:7}},
   enc:[[10,3,2,5],[12,3,2,5],[14,2,3,6],[16,1,4,7],[11,.3,8,10]],
   map:[
    "TTTTTTTTTTTTTTTT",
    "T..GGG....GGG..T",
    "T.S.GG..H..GG..T",
    "T....T....T....T",
    "T.GGGT.TT.TGGG.T",
    "T.GGG......GGG.T",
    "TWWW...TT...WWWT",
    "TWWW.GG..GG.WWWT",
    "T....GGGGGG....T",
    "T.T..........T.T",
    "Ta.....TT.....bT",
    "TTTTTTTTTTTTTTTT"]},
  {n:"Ember Realm",bg:"#2a0f0b",wall:"#4a1a12",path:"#5a3a2a",grass:"#7a3a1f",grass2:"#9a4a22",
   gates:{a:{to:0,ax:2,ay:10},b:{to:3,ax:2,ay:3}},
   enc:[[17,3,9,13],[19,3,9,13],[21,2,10,14],[18,.3,16,18]],
   map:[
    "TTTTTTTTTTTTTTTT",
    "TLL..GGG...LLLLT",
    "TL...GGG.H...LLT",
    "T..T......T....T",
    "T.GGG.LL.GGGG..T",
    "T.GGG.LL.GGGG..T",
    "T.....LL.......T",
    "Ta..GGG..GGG...T",
    "T...GGG..GGG.T.T",
    "TLL..........LLT",
    "TLLL....b...LLLT",
    "TTTTTTTTTTTTTTTT"]},
  {n:"Tide Realm",bg:"#07192a",wall:"#0f2e4a",path:"#2a3a4a",grass:"#1f6a7a",grass2:"#268a9a",
   gates:{a:{to:0,ax:13,ay:10},b:{to:3,ax:2,ay:7}},
   enc:[[23,3,9,13],[25,2,10,14],[27,2,9,13],[24,.3,16,18]],
   map:[
    "TTTTTTTTTTTTTTTT",
    "TWWWW.....WWWWWT",
    "TWW..GGG.H..WWWT",
    "TW...GGG.....WWT",
    "T..GG.....GG...T",
    "T..GG.WWW.GG...T",
    "T.....WWW......T",
    "Ta.GGG.....GGG.T",
    "T..GGG..T..GGG.T",
    "TWW.........WWWT",
    "TWWWW...b..WWWWT",
    "TTTTTTTTTTTTTTTT"]},
  {n:"Storm Realm",bg:"#15172a",wall:"#2a2e4a",path:"#3a3f5a",grass:"#5a5a2a",grass2:"#7a7a30",
   gates:{a:{to:1,ax:8,ay:9},b:{to:2,ax:8,ay:9},c:{to:4,ax:2,ay:7}},
   enc:[[28,3,16,21],[30,2,16,20],[31,.4,20,24],[29,.3,24,27]],
   map:[
    "TTTTTTTTTTTTTTTT",
    "TCCC..GG...CCCCT",
    "TC....GG.H...CCT",
    "Ta..GGG...GGG..T",
    "T...GGG...GGG..T",
    "TCC.....C......T",
    "T....CC...GG.C.T",
    "Tb..GGGG..GG...T",
    "T...GGGG.......T",
    "TC....CC....CCCT",
    "TCCC....c...CCCT",
    "TTTTTTTTTTTTTTTT"]},
  {n:"Dusk Realm",bg:"#120a1e",wall:"#241438",path:"#2e2440",grass:"#4a2a6a",grass2:"#5e3a82",
   gates:{a:{to:3,ax:8,ay:9}},
   enc:[[32,3,22,28],[34,3,22,28],[33,.5,30,33],[35,.5,30,33]],
   map:[
    "TTTTTTTTTTTTTTTT",
    "TKKK...GG...KKKT",
    "TK.....GG.H...KT",
    "T..GGG.....GGG.T",
    "T..GGG..K..GGG.T",
    "TK.....KKK.....T",
    "T..GG...K...GG.T",
    "Ta.GG.......GG.T",
    "T....GGGGGG....T",
    "TK....GGGG....KT",
    "TKKK....X...KKKT",
    "TTTTTTTTTTTTTTTT"]},
];
const WALLS = new Set(["T","W","L","C","K"]);
const STARTERS = [1,4,7];
