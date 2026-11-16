const canvas=document.getElementById('game'),ctx=canvas.getContext('2d');
const params=new URLSearchParams(location.search),isHost=params.has('host');
const host=location.hostname||'localhost';
document.getElementById('joinurl').textContent=`http://${host}:8000/?join=1`;
let ws,latest=null,keys={},touch={x:0,y:0,fire:false,special:false},comicPage=0,lastPhase='',myId=null,isCommander=false;
const stars=Array.from({length:190},()=>({x:Math.random()*900,y:Math.random()*650,z:Math.random()*2+.3,r:Math.random()*1.6+.3}));
const nebula=Array.from({length:13},(_,i)=>({x:Math.random()*900,y:Math.random()*650,r:90+Math.random()*150,h:i%2?195:285,a:.025+Math.random()*.035}));
const debris=Array.from({length:24},()=>({x:Math.random()*900,y:Math.random()*650,r:2+Math.random()*7,rot:Math.random()*6,spd:.2+Math.random()*.5}));
let shake=0,flash=0,bgTick=0;
let audioCtx=null,audioEnabled=false,musicTimer=null,lastKillCount=0,lastPickupCount=0,lastPhaseSound='';
function audioInit(){if(audioCtx)return;audioCtx=new (window.AudioContext||window.webkitAudioContext)()}
function tone(freq,duration=.12,type='sine',volume=.035,slide=0){if(!audioEnabled)return;audioInit();const o=audioCtx.createOscillator(),g=audioCtx.createGain();o.type=type;o.frequency.setValueAtTime(freq,audioCtx.currentTime);if(slide)o.frequency.exponentialRampToValueAtTime(Math.max(30,freq+slide),audioCtx.currentTime+duration);g.gain.setValueAtTime(volume,audioCtx.currentTime);g.gain.exponentialRampToValueAtTime(.0001,audioCtx.currentTime+duration);o.connect(g);g.connect(audioCtx.destination);o.start();o.stop(audioCtx.currentTime+duration)}
function sfx(name){if(!audioEnabled)return;({shoot:()=>tone(620,.055,'square',.012,-260),kill:()=>{tone(180,.18,'sawtooth',.035,-120);tone(510,.12,'triangle',.025,180)},pickup:()=>{tone(520,.11,'sine',.04,260);setTimeout(()=>tone(780,.16,'sine',.03,180),80)},hit:()=>tone(105,.22,'sawtooth',.045,-55),boss:()=>{tone(90,.5,'sawtooth',.045,35);setTimeout(()=>tone(150,.45,'triangle',.03,-70),180)},clear:()=>[440,554,659,880].forEach((n,i)=>setTimeout(()=>tone(n,.24,'triangle',.035,50),i*110))}[name]||(()=>{}))()}
function startMusic(){if(!audioEnabled||musicTimer)return;audioInit();let step=0;const notes=[55,65.4,73.4,82.4,73.4,65.4,49,61.7];musicTimer=setInterval(()=>{if(audioEnabled){const n=notes[step++%notes.length];tone(n,.42,'triangle',.012);if(step%2===0)tone(n*2,.16,'sine',.008)}},430)}
function setAudio(on){audioEnabled=on;const b=document.getElementById('audio-toggle');b.textContent=on?'♫ AUDIO: ON':'♫ AUDIO: OFF';b.classList.toggle('active',on);if(on){audioInit();audioCtx.resume();startMusic()}else if(musicTimer){clearInterval(musicTimer);musicTimer=null}}
document.getElementById('audio-toggle').addEventListener('click',()=>setAudio(!audioEnabled));
function connect(){ws=new WebSocket(`ws://${location.host}/ws`);ws.onopen=()=>{document.getElementById('netstatus').textContent='LINK ESTABLISHED';document.querySelector('.net').classList.add('online')};ws.onclose=()=>{document.getElementById('netstatus').textContent='LINK LOST - RECONNECTING';document.querySelector('.net').classList.remove('online');setTimeout(connect,1500)};ws.onmessage=e=>{const d=JSON.parse(e.data);if(d.type==='welcome'){myId=d.player_id;isCommander=!!d.is_host;if(isCommander){document.getElementById('mode-select').disabled=false;document.getElementById('start').style.display='block'}else{document.getElementById('mode-select').disabled=true;document.getElementById('start').style.display='none'}send({type:'profile',name:document.getElementById('callsign').value,ship:document.getElementById('ship-select').value})}else if(d.type==='state'){latest=d;updateUI(d)}else if(d.type==='error'){alert(d.message)}}}
connect();
function send(o){if(ws&&ws.readyState===1)ws.send(JSON.stringify(o))}
document.getElementById('start').onclick=()=>send({type:'start'});
document.getElementById('mode-select').onchange=e=>send({type:'mode',mode:e.target.value});
function profileChanged(){send({type:'profile',name:document.getElementById('callsign').value,ship:document.getElementById('ship-select').value})}
document.getElementById('callsign').addEventListener('change',profileChanged);document.getElementById('ship-select').addEventListener('change',profileChanged);
function updateUI(d){
 const kills=d.game.mission_kills||0;if(kills>lastKillCount)sfx('kill');if((d.pickups||[]).length<lastPickupCount)sfx('pickup');if(d.game.phase==='playing'&&lastPhaseSound!=='playing')sfx('boss');if(['stage_clear','campaign_complete'].includes(d.game.phase)&&lastPhaseSound!==d.game.phase)sfx('clear');if(d.game.phase==='defeat'&&lastPhaseSound!=='defeat')sfx('hit');lastKillCount=kills;lastPickupCount=(d.pickups||[]).length;lastPhaseSound=d.game.phase;
 const roster=document.getElementById('roster');roster.innerHTML='';Object.entries(d.players).forEach(([id,p],i)=>{const card=document.createElement('div');card.className='roster-pilot'+(id===d.room.host_id?' commander':'');card.innerHTML=`<span class="pilot-mark" style="--pilot:${p.color}">◆</span><span class="pilot-info"><b></b><small></small></span><span class="pilot-state">${p.alive?'LINKED':'DOWN'}</span>`;card.querySelector('b').textContent=p.name+(id===d.room.host_id?' // HOST':'');card.querySelector('small').textContent=p.ship+' CLASS';roster.appendChild(card)});
 document.getElementById('roster-count').textContent=`${Object.keys(d.players).length} / ${d.room.max_players} PILOTS`;document.getElementById('roomid').textContent=`ROOM ${d.room.id} // ${d.room.mode.toUpperCase()}`;
 isCommander=myId===d.room.host_id;document.getElementById('mode-select').disabled=!isCommander;document.getElementById('start').style.display=isCommander?'block':'none';document.getElementById('mode-select').value=d.room.mode;document.getElementById('start').disabled=!isCommander||Object.keys(d.players).length<d.room.min_players;
 const phase=d.game.phase;document.getElementById('lobby').classList.toggle('hidden',phase!=='lobby');document.getElementById('comic').classList.toggle('hidden',phase!=='comic');document.getElementById('gamewrap').classList.toggle('hidden',!['playing','defeat','stage_clear','campaign_complete'].includes(phase));document.getElementById('result').classList.toggle('hidden',!['defeat','stage_clear','campaign_complete'].includes(phase));
 if(phase==='comic'&&lastPhase!=='comic'){comicPage=0;renderComic(d)}if(['defeat','stage_clear','campaign_complete'].includes(phase)&&lastPhase!==phase)renderResult(d);if(phase==='playing'&&lastPhase!==phase)document.getElementById('result').classList.add('hidden');lastPhase=phase;
 const mi=d.mission_info;document.getElementById('mission-name').textContent=mi.name;document.getElementById('campaign-progress').textContent=`${String(d.game.mission).padStart(2,'0')} / ${mi.total_missions}`;document.getElementById('progress-fill').style.width=`${(d.game.mission/mi.total_missions)*100}%`;document.getElementById('mission-objective').textContent='OBJECTIVE: '+mi.objective;document.getElementById('wave').textContent=`WAVE ${String(d.game.wave).padStart(2,'0')}`;
 const all=Object.values(d.players),score=all.reduce((sum,p)=>sum+(p.score||0),0);document.getElementById('score').textContent='SCORE '+String(score).padStart(6,'0');
 const hud=document.getElementById('player-hud');hud.innerHTML='';all.forEach(p=>{const el=document.createElement('div');el.className='pilot-health';el.innerHTML=`<div class="pilot-health-top"><b></b><span></span></div><div class="health-track"><i></i></div>`;el.querySelector('b').textContent=p.name;el.querySelector('span').textContent=`${p.hp} HP // WPN ${p.weapon}`;el.querySelector('i').style.width=`${p.hp}%`;el.querySelector('i').style.background=p.color;hud.appendChild(el)});
 if(d.game.boss)document.getElementById('wave').textContent='BOSS: '+d.game.boss.name;
}
function renderComic(d){
 const pages=d.mission_info.comic||[];
 const p=pages[comicPage];if(!p)return;
 document.getElementById('comic-tag').textContent=p.tag;
 document.getElementById('comic-count').textContent=`PAGE ${String(comicPage+1).padStart(2,'0')} / ${String(pages.length).padStart(2,'0')}`;
 document.getElementById('comic-title').textContent=p.title;
 document.getElementById('comic-location').textContent=d.mission_info.location;
 document.getElementById('comic-text').textContent=p.text;
 document.getElementById('comic-speaker').textContent=p.speaker;
 const art=document.getElementById('comic-art');art.dataset.page=String(comicPage);
 document.getElementById('comic-prev').disabled=comicPage===0;
 document.getElementById('comic-next').textContent=comicPage===pages.length-1?'DEPLOY SQUADRON ▶':'NEXT PAGE ▶';
}
document.getElementById('comic-prev').onclick=()=>{if(comicPage>0){comicPage--;renderComic(latest)}};
document.getElementById('comic-next').onclick=()=>{let n=latest.mission_info.comic.length;if(comicPage<n-1){comicPage++;renderComic(latest)}else send({type:'deploy'})};

function renderResult(d){
 const phase=d.game.phase,mi=d.mission_info;
 const score=Object.values(d.players).reduce((sum,p)=>sum+(p.score||0),0);
 const progress=phase==='campaign_complete'?100:Math.round(((d.game.mission-1)/mi.total_missions)*100+(phase==='stage_clear'?100/mi.total_missions:0));
 document.getElementById('final-score').textContent=String(score).padStart(6,'0');
 document.getElementById('kill-count').textContent=String(d.game.mission_kills||0).padStart(2,'0');
 document.getElementById('story-progress').textContent=progress+'%';
 const title=document.getElementById('result-title'),sub=document.getElementById('result-subtitle'),ey=document.getElementById('result-eyebrow'),story=document.getElementById('result-story'),actions=document.getElementById('result-actions');
 actions.innerHTML='';
 if(phase==='defeat'){
  title.textContent='MISSION FAILED';title.classList.add('danger-title');ey.textContent='AFTER ACTION REPORT // SQUADRON LOST';
  sub.textContent='The squadron has been disabled. The operation can still be attempted again.';
  story.textContent=`${mi.name}: ${mi.objective} Campaign story reached: mission ${d.game.mission} of ${mi.total_missions}. Retry this mission to continue the operation.`;
  addAction(actions,'RETRY MISSION',()=>send({type:'retry'}));
  addAction(actions,'RETURN TO LOBBY',()=>send({type:'back_lobby'}),'secondary');
 }else if(phase==='stage_clear'){
  title.textContent='MISSION COMPLETE';title.classList.remove('danger-title');ey.textContent='AFTER ACTION REPORT // TARGET ELIMINATED';
  sub.textContent=`${mi.boss} destroyed. The squadron advances.`;
  story.textContent=`You completed ${mi.name}. Campaign progress: mission ${d.game.mission} of ${mi.total_missions}. The next chapter of the operation is ready.`;
  addAction(actions,'NEXT CHAPTER ▶',()=>send({type:'next'}));
  addAction(actions,'RETURN TO LOBBY',()=>send({type:'back_lobby'}),'secondary');
 }else{
  title.textContent='CAMPAIGN COMPLETE';title.classList.remove('danger-title');ey.textContent='OPERATION ECLIPSE // FINAL DEBRIEF';
  sub.textContent='The Eclipse Array is silent. The Helios Colony is safe.';
  story.textContent='All three operations are complete. Your squadron prevented the activation of the planetary weapon and ended the enemy command network.';
  addAction(actions,'PLAY CAMPAIGN AGAIN',()=>send({type:'replay'}));
  addAction(actions,'RETURN TO LOBBY',()=>send({type:'back_lobby'}),'secondary');
 }
}
function addAction(parent,label,fn,cls=''){
 let b=document.createElement('button');
 b.textContent=label;
 if(cls)b.className=cls;
 b.onclick=fn;
 if(!isCommander){b.disabled=true;b.title='Only the room commander controls campaign progression';}
 parent.appendChild(b);
}

document.addEventListener('keydown',e=>{keys[e.key.toLowerCase()]=true;if([' ','arrowup','arrowdown','arrowleft','arrowright'].includes(e.key.toLowerCase()))e.preventDefault()});
document.addEventListener('keyup',e=>keys[e.key.toLowerCase()]=false);
function bindHold(id,prop){let el=document.getElementById(id);el.addEventListener('pointerdown',e=>{e.preventDefault();touch[prop]=true;el.setPointerCapture(e.pointerId)});['pointerup','pointercancel','lostpointercapture'].forEach(ev=>el.addEventListener(ev,()=>touch[prop]=false))}
bindHold('fire','fire');bindHold('special','special');
let stick=document.getElementById('stick'),knob=document.getElementById('knob'),stickOn=false;stick.addEventListener('pointerdown',e=>{stickOn=true;stick.setPointerCapture(e.pointerId);moveStick(e)});stick.addEventListener('pointermove',e=>{if(stickOn)moveStick(e)});
function moveStick(e){let r=stick.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2,dx=e.clientX-cx,dy=e.clientY-cy,m=Math.max(1,Math.hypot(dx,dy)),lim=35;dx=dx/m*Math.min(m,lim);dy=dy/m*Math.min(m,lim);touch.x=dx/lim;touch.y=dy/lim;knob.style.transform=`translate(${dx}px,${dy}px)`}
function releaseStick(){stickOn=false;touch.x=touch.y=0;knob.style.transform=''}['pointerup','pointercancel','lostpointercapture'].forEach(ev=>stick.addEventListener(ev,releaseStick));
setInterval(()=>{let x=(keys.d||keys.arrowright?1:0)-(keys.a||keys.arrowleft?1:0),y=(keys.s||keys.arrowdown?1:0)-(keys.w||keys.arrowup?1:0);if(Math.abs(touch.x)+Math.abs(touch.y)>0){x=touch.x;y=touch.y}const firing=!!keys[' ']||!!keys.j||touch.fire;if(firing&&bgTick%5===0)sfx('shoot');send({type:'input',x,y,fire:firing,special:!!keys.k||touch.special})},33);

function glow(color,blur=15){ctx.shadowColor=color;ctx.shadowBlur=blur}
function drawBackground(t,mission){
 const palettes={1:['#071a2b','#102c40','#315c72'],2:['#100e25','#241c43','#6b487b'],3:['#08091e','#1c1740','#51408c']};
 const pal=palettes[mission]||palettes[1];
 let g=ctx.createRadialGradient(470,280,20,450,320,650);g.addColorStop(0,pal[2]);g.addColorStop(.45,pal[1]);g.addColorStop(1,'#01040d');ctx.fillStyle=g;ctx.fillRect(0,0,900,650);
 // Layered nebula clouds
 nebula.forEach((n,i)=>{let x=(n.x+Math.sin(t*.00012+i)*35+900)%900,y=(n.y+Math.cos(t*.0001+i)*28+650)%650;let rg=ctx.createRadialGradient(x,y,2,x,y,n.r);rg.addColorStop(0,`hsla(${n.h+(mission===2?35:0)},90%,65%,${n.a*2.2})`);rg.addColorStop(1,'transparent');ctx.fillStyle=rg;ctx.fillRect(x-n.r,y-n.r,n.r*2,n.r*2)});
 // Planet / moon in the distance
 ctx.save();let px=mission===2?720:mission===3?155:760,py=mission===2?140:mission===3?160:95,pr=mission===3?92:mission===2?75:58;
 let pg=ctx.createRadialGradient(px-pr*.35,py-pr*.4,4,px,py,pr);pg.addColorStop(0,mission===2?'#a88ac0':'#75b8d0');pg.addColorStop(.55,mission===2?'#49375f':'#244b67');pg.addColorStop(1,'#030916');ctx.fillStyle=pg;glow(mission===3?'#8d62ff':'#3bbfe8',28);ctx.beginPath();ctx.arc(px,py,pr,0,Math.PI*2);ctx.fill();ctx.globalAlpha=.23;ctx.strokeStyle='#9defff';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(px,py,pr*1.55,pr*.35,-.25,0,Math.PI*2);ctx.stroke();ctx.restore();ctx.globalAlpha=1;ctx.shadowBlur=0;
 // Starfield with parallax
 stars.forEach((s,i)=>{s.y=(s.y+s.z*(mission===3?1.3:1))%650;let tw=.45+Math.sin(t*.002+i)*.35;ctx.globalAlpha=tw;ctx.fillStyle=i%13===0?'#a6f4ff':'#b7d9ec';ctx.fillRect(s.x,s.y,s.r,s.r);if(s.z>1.8){ctx.fillRect(s.x,s.y,1,s.r*4)}});ctx.globalAlpha=1;
 // Distant debris and asteroid silhouettes
 debris.forEach((d,i)=>{d.y=(d.y+d.spd)%690;d.rot+=.002;ctx.save();ctx.translate(d.x,d.y);ctx.rotate(d.rot);ctx.fillStyle='#30485c';ctx.globalAlpha=.38;ctx.beginPath();ctx.moveTo(-d.r,-d.r*.4);ctx.lineTo(-d.r*.2,-d.r);ctx.lineTo(d.r,.1*d.r);ctx.lineTo(d.r*.4,d.r);ctx.lineTo(-d.r,d.r*.4);ctx.closePath();ctx.fill();ctx.restore()});ctx.globalAlpha=1;
 // Tactical scan grid and sector brackets
 ctx.strokeStyle=mission===3?'#8c6cff':'#4cdcf0';ctx.globalAlpha=.08;for(let x=0;x<900;x+=75){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,650);ctx.stroke()}for(let y=0;y<650;y+=75){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(900,y);ctx.stroke()}ctx.globalAlpha=1;
 ctx.strokeStyle='#63eaff66';ctx.lineWidth=1;ctx.strokeRect(12,12,876,626);
}
function ship(x,y,color,role,t,weapon=1,shield=0){
 ctx.save();ctx.translate(x,y);const flick=11+Math.sin(t*.03)*6;glow(color,24);
 for(const ex of [-10,10]){ctx.globalAlpha=.72;const flame=ctx.createLinearGradient(0,12,0,32+flick);flame.addColorStop(0,color);flame.addColorStop(1,'transparent');ctx.fillStyle=flame;ctx.beginPath();ctx.moveTo(ex-4,10);ctx.lineTo(ex,29+flick);ctx.lineTo(ex+4,10);ctx.fill()}ctx.globalAlpha=1;
 const body=ctx.createLinearGradient(-26,-24,24,20);body.addColorStop(0,'#f0fdff');body.addColorStop(.18,color);body.addColorStop(.68,'#17364e');body.addColorStop(1,'#050d1b');ctx.fillStyle=body;ctx.strokeStyle=color;ctx.lineWidth=1.8;ctx.beginPath();
 if(role==='TITAN'){ctx.moveTo(0,-25);ctx.lineTo(34,-3);ctx.lineTo(43,15);ctx.lineTo(13,10);ctx.lineTo(0,21);ctx.lineTo(-13,10);ctx.lineTo(-43,15);ctx.lineTo(-34,-3)}
 else if(role==='PHANTOM'){ctx.moveTo(0,-34);ctx.lineTo(17,4);ctx.lineTo(11,17);ctx.lineTo(0,11);ctx.lineTo(-11,17);ctx.lineTo(-17,4)}
 else if(role==='MEDIC'){ctx.moveTo(0,-28);ctx.lineTo(25,-3);ctx.lineTo(21,13);ctx.lineTo(8,17);ctx.lineTo(0,11);ctx.lineTo(-8,17);ctx.lineTo(-21,13);ctx.lineTo(-25,-3)}
 else{ctx.moveTo(0,-31);ctx.lineTo(23,8);ctx.lineTo(12,7);ctx.lineTo(7,20);ctx.lineTo(0,13);ctx.lineTo(-7,20);ctx.lineTo(-12,7);ctx.lineTo(-23,8)}
 ctx.closePath();ctx.fill();ctx.stroke();
 ctx.globalAlpha=.45;ctx.fillStyle='#eaffff';ctx.beginPath();ctx.moveTo(0,-25);ctx.lineTo(8,4);ctx.lineTo(0,0);ctx.lineTo(-8,4);ctx.closePath();ctx.fill();ctx.globalAlpha=1;
 const cockpit=ctx.createRadialGradient(-2,-12,1,0,-7,12);cockpit.addColorStop(0,'#ffffff');cockpit.addColorStop(.25,color);cockpit.addColorStop(1,'#10273a');ctx.fillStyle=cockpit;ctx.beginPath();ctx.ellipse(0,-7,5,12,0,0,Math.PI*2);ctx.fill();
 if(role==='MEDIC'){ctx.strokeStyle='#e7fff2';ctx.lineWidth=2;ctx.beginPath();ctx.arc(0,0,28+Math.sin(t*.01)*2,0,Math.PI*2);ctx.stroke()}
 if(weapon>1){ctx.fillStyle='#ffe38a';ctx.fillRect(-19,-3,4,12);ctx.fillRect(15,-3,4,12)}
 if(shield>0){ctx.globalAlpha=.25+.14*Math.sin(t*.02);ctx.strokeStyle='#72eaff';ctx.lineWidth=2.5;ctx.shadowBlur=20;ctx.beginPath();ctx.ellipse(0,0,37,45,0,0,Math.PI*2);ctx.stroke();ctx.globalAlpha=1}
 ctx.restore();ctx.shadowBlur=0}


function drawEnemy(e,t){
 const styles={SCOUT:['#ff5577','#672b49'],INTERCEPTOR:['#ff8a5b','#65354a'],GUNSHIP:['#ffb45f','#554052'],BOMBER:['#ff6d3d','#653b39'],PHANTOM:['#c18aff','#382e68'],ELITE:['#ff365f','#4c2547'],SNIPER:['#ffe16a','#554a35'],SWARMER:['#ff4c9a','#552341'],REPAIR_DRONE:['#68ffb4','#24594e']};
 const [c,fill]=styles[e.kind]||styles.SCOUT;ctx.save();ctx.translate(e.x,e.y);const pulse=1+Math.sin(t*.008+e.phase)*.06;ctx.scale(pulse,pulse);glow(c,e.kind==='ELITE'?24:15);ctx.fillStyle=fill;ctx.strokeStyle=c;ctx.lineWidth=e.kind==='ELITE'?2.8:1.8;
 ctx.beginPath();
 switch(e.kind){
 case 'GUNSHIP':case 'ELITE':ctx.moveTo(0,23);ctx.lineTo(31,5);ctx.lineTo(23,-15);ctx.lineTo(8,-9);ctx.lineTo(0,-20);ctx.lineTo(-8,-9);ctx.lineTo(-23,-15);ctx.lineTo(-31,5);break;
 case 'BOMBER':ctx.moveTo(0,24);ctx.lineTo(27,5);ctx.lineTo(18,-13);ctx.lineTo(0,-7);ctx.lineTo(-18,-13);ctx.lineTo(-27,5);break;
 case 'SNIPER':ctx.moveTo(0,-24);ctx.lineTo(12,-4);ctx.lineTo(7,18);ctx.lineTo(0,12);ctx.lineTo(-7,18);ctx.lineTo(-12,-4);break;
 case 'REPAIR_DRONE':for(let i=0;i<8;i++){let a=i*Math.PI/4;ctx.lineTo(Math.cos(a)*20,Math.sin(a)*20)}break;
 case 'SWARMER':ctx.moveTo(0,20);ctx.lineTo(10,-4);ctx.lineTo(0,-17);ctx.lineTo(-10,-4);break;
 case 'PHANTOM':ctx.moveTo(0,22);ctx.lineTo(25,-8);ctx.lineTo(8,-3);ctx.lineTo(0,-22);ctx.lineTo(-8,-3);ctx.lineTo(-25,-8);break;
 default:ctx.moveTo(0,20);ctx.lineTo(23,-9);ctx.lineTo(8,-5);ctx.lineTo(0,-20);ctx.lineTo(-8,-5);ctx.lineTo(-23,-9);
 }
 ctx.closePath();ctx.fill();ctx.stroke();
 // engine nacelles and cockpit glow
 ctx.fillStyle=c;ctx.shadowBlur=13;ctx.fillRect(-17,8,5,9);ctx.fillRect(12,8,5,9);ctx.fillStyle='#eaffff';ctx.beginPath();ctx.ellipse(0,-3,4,7,0,0,Math.PI*2);ctx.fill();
 if(e.kind==='ELITE'){ctx.strokeStyle='#fff0b0';ctx.lineWidth=1;ctx.beginPath();ctx.arc(0,0,29+Math.sin(t*.01)*3,0,Math.PI*2);ctx.stroke()}
 ctx.shadowBlur=0;ctx.fillStyle='#311b2c';ctx.fillRect(-15,-31,30,4);ctx.fillStyle=c;ctx.fillRect(-15,-31,30*Math.max(0,e.hp/e.maxhp),4);ctx.restore();
}
function drawPickup(item,t){const cfg={HEALTH:['#78ffb7','+'],WEAPON:['#63eaff','✦'],RAPID:['#ffd16d','»'],SHIELD:['#c49aff','⬡']}[item.kind]||['#fff','?'];ctx.save();ctx.translate(item.x,item.y+Math.sin(item.phase)*4);glow(cfg[0],22);ctx.rotate(t*.0015);ctx.strokeStyle=cfg[0];ctx.fillStyle='#071c2b';ctx.lineWidth=2;ctx.beginPath();ctx.rect(-12,-12,24,24);ctx.fill();ctx.stroke();ctx.rotate(-t*.0015);ctx.fillStyle=cfg[0];ctx.font='bold 17px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(cfg[1],0,1);ctx.restore();ctx.shadowBlur=0}
function drawBoss(b,t){ctx.save();ctx.translate(b.x,b.y);let type=b.type;
 if(type==='dreadnought'){glow('#ff4c68',30);ctx.fillStyle='#3b354b';ctx.strokeStyle='#ff7891';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(0,-72);ctx.lineTo(75,-35);ctx.lineTo(90,18);ctx.lineTo(48,37);ctx.lineTo(0,24);ctx.lineTo(-48,37);ctx.lineTo(-90,18);ctx.lineTo(-75,-35);ctx.closePath();ctx.fill();ctx.stroke();for(let x of [-55,55]){ctx.fillStyle='#ff5a78';ctx.fillRect(x-8,-5,16,24)}}
 else if(type==='carrier'){glow('#ff9a56',28);ctx.fillStyle='#514052';ctx.strokeStyle='#ffb36e';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(-110,-25);ctx.lineTo(-65,-58);ctx.lineTo(65,-58);ctx.lineTo(110,-25);ctx.lineTo(95,35);ctx.lineTo(35,48);ctx.lineTo(0,25);ctx.lineTo(-35,48);ctx.lineTo(-95,35);ctx.closePath();ctx.fill();ctx.stroke();ctx.fillStyle='#ff6d83';for(let x of [-60,-30,0,30,60])ctx.fillRect(x-5,-35,10,9)}
 else{ctx.rotate(t*.0006);glow('#a77bff',35);ctx.fillStyle='#30275a';ctx.strokeStyle='#a98aff';ctx.lineWidth=4;ctx.beginPath();for(let i=0;i<12;i++){let a=i*Math.PI/6,r=i%2?56:90;let x=Math.cos(a)*r,y=Math.sin(a)*r; if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}ctx.closePath();ctx.fill();ctx.stroke();ctx.fillStyle='#c4b0ff';ctx.beginPath();ctx.arc(0,0,26+Math.sin(t*.01)*5,0,Math.PI*2);ctx.fill();for(let a=0;a<6;a++){ctx.rotate(Math.PI/3);ctx.fillStyle='#ff537a';ctx.fillRect(0,-5,110,10)}}
 ctx.restore();ctx.shadowBlur=0;
 // Boss health bar
 ctx.fillStyle='#341c30';ctx.fillRect(250,22,400,8);ctx.fillStyle=type==='core'?'#a68aff':'#ff5577';ctx.fillRect(250,22,400*Math.max(0,b.hp/b.maxhp),8);
 ctx.fillStyle='#d8efff';ctx.font='11px Orbitron';ctx.textAlign='center';ctx.fillText(b.name,450,15)}
function draw(){
 requestAnimationFrame(draw);bgTick++;let t=performance.now();ctx.save();
 if(shake>0){ctx.translate((Math.random()-.5)*shake,(Math.random()-.5)*shake);shake*=.88;if(shake<.3)shake=0}
 drawBackground(t,latest?.game.mission||1);
 if(latest){
  let d=latest;
  d.particles.forEach(p=>{ctx.globalAlpha=Math.max(0,p.life/42);glow(p.color||'#ffad66',10);ctx.fillStyle=p.color||'#ffad66';ctx.beginPath();ctx.arc(p.x,p.y,p.size||2,0,Math.PI*2);ctx.fill()});ctx.globalAlpha=1;ctx.shadowBlur=0;
  d.enemies.forEach(e=>drawEnemy(e,t));
  (d.pickups||[]).forEach(item=>drawPickup(item,t));
  if(d.game.boss)drawBoss(d.game.boss,t);
  d.bullets.forEach(b=>{let owner=d.players[b.owner];let c=owner?.color||'#63efff';glow(c,17);ctx.strokeStyle=c;ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(b.x,b.y+8);ctx.lineTo(b.x,b.y-9);ctx.stroke()});
  d.enemy_shots.forEach(b=>{let c=b.kind==='core'?'#b48aff':b.kind==='sniper'?'#ffe16a':b.kind==='bomb'?'#ff874f':'#ff426c';glow(c,14);ctx.fillStyle=c;ctx.beginPath();ctx.arc(b.x,b.y,b.kind==='heavy'?5:3.5,0,Math.PI*2);ctx.fill()});
  Object.entries(d.players).forEach(([id,p])=>{if(p.alive){ship(p.x,p.y,p.color||'#54eaff',p.ship||'VANGUARD',t,p.weapon||1,p.shield||0);ctx.fillStyle='#c5e8f5';ctx.font='10px Orbitron';ctx.textAlign='center';ctx.fillText(p.name||'PILOT',p.x,p.y+40)}});
  ctx.shadowBlur=0;ctx.textAlign='left';ctx.fillStyle='#a9eaff';ctx.font='10px Orbitron';ctx.fillText(`SECTOR ${String(d.game.mission).padStart(2,'0')} // ${d.mission_info.location}`,26,35);
  if(d.game.phase==='playing'&&d.game.tick<100){ctx.globalAlpha=Math.max(0,1-d.game.tick/100);ctx.fillStyle='#e5faff';ctx.textAlign='center';ctx.font='bold 22px Orbitron';ctx.fillText(d.mission_info.subtitle,450,310);ctx.globalAlpha=1}
 }
 if(flash>0){ctx.fillStyle=`rgba(255,70,100,${flash})`;ctx.fillRect(0,0,900,650);flash*=.86}
 ctx.restore();
}
draw();
