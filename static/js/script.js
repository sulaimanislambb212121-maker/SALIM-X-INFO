'use strict';
const IMAGE_BASE = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/";

const PREFIX_MAP = {
  "902":"Avatar","214":"Facepaint","101":"Female Skill","102":"Male Skill",
  "103":"Microchip","905":"Parachute","710":"Bundle","720":"Bundle",
  "203":"Top","204":"Bottom","205":"Shoes","211":"Head","901":"Banner",
  "131":"Pet","130":"Pet/Emote","903":"Loot Box","904":"Backpack",
  "906":"Skyboard","907":"Other","908":"Vehicle","909":"Emote",
  "911":"SkyWings","922":"Skill Skin","912":"Weapon Skin"
};
function getItemType(id){const s=String(id);return PREFIX_MAP[s.slice(0,3)]||PREFIX_MAP[s.slice(0,2)]||"Item";}

/* ======================================================
   HACKING CANVAS ANIMATION
   ====================================================== */
(function initHack(){
  const canvas = document.getElementById('hackCanvas');
  const ctx    = canvas.getContext('2d');
  const chars  = 'アイウエオカキクケコ01アイウエオ10ABCDEF0123456789</>{}[];:#$%^&*|\\KAWSARFFINFO'.split('');
  let cols, drops, fontSize = 13;

  function resize(){
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    cols  = Math.floor(canvas.width / fontSize);
    drops = Array(cols).fill(1);
  }
  resize();
  window.addEventListener('resize', resize);

  function getColor(){
    return getComputedStyle(document.documentElement).getPropertyValue('--ac').trim() || '#00ffff';
  }

  setInterval(()=>{
    ctx.fillStyle = 'rgba(6,6,16,0.08)';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = getColor();
    ctx.font = fontSize+'px "Share Tech Mono",monospace';
    for(let i=0;i<drops.length;i++){
      const c = chars[Math.floor(Math.random()*chars.length)];
      ctx.fillText(c, i*fontSize, drops[i]*fontSize);
      if(drops[i]*fontSize > canvas.height && Math.random()>0.975) drops[i]=0;
      drops[i]++;
    }
  }, 45);
})();

/* ======================================================
   THEME COLOR SWITCHER
   ====================================================== */
function hexToRgba(hex, alpha){
  const r=parseInt(hex.slice(1,3),16);
  const g=parseInt(hex.slice(3,5),16);
  const b=parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}
function setThemeColor(hex, btn){
  const root = document.documentElement;
  root.style.setProperty('--ac', hex);
  // darken for ac2
  root.style.setProperty('--ac2', hex);
  root.style.setProperty('--ac-glow', hexToRgba(hex, 0.22));
  root.style.setProperty('--border', hexToRgba(hex, 0.2));
  // update active swatch
  document.querySelectorAll('.swatch').forEach(s=>s.classList.remove('active'));
  if(btn) btn.classList.add('active');
  // save
  try{localStorage.setItem('ff_theme_color', hex);}catch(e){}
}
// Load saved color
try{
  const saved = localStorage.getItem('ff_theme_color');
  if(saved){
    setThemeColor(saved);
    document.querySelectorAll('.swatch').forEach(s=>{
      if(s.dataset.color===saved) s.classList.add('active');
      else s.classList.remove('active');
    });
  }
}catch(e){}

/* ======================================================
   BANNER
   ====================================================== */
function closeBanner(){
  const b=document.getElementById('welcomeBanner');
  b.classList.add('hide');
  setTimeout(()=>{b.style.display='none';document.getElementById('mainSite').style.display='block';},800);
}

/* ======================================================
   GUIDE
   ====================================================== */
function toggleGuide(){
  const g=document.getElementById('guideBox');
  g.style.display=g.style.display==='none'?'block':'none';
}

/* ======================================================
   FORMAT HELPERS
   ====================================================== */
function fmtTime(ts){
  if(!ts||ts==='0') return '—';
  try{return new Date(parseInt(ts)*1000).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});}
  catch{return ts;}
}
function fmtNum(n){if(!n||n==='0') return '0'; return parseInt(n).toLocaleString();}

/* ======================================================
   BUILD HORIZONTAL INFO ROW LIST
   ====================================================== */
function buildRows(containerId, rows){
  const c = document.getElementById(containerId);
  c.innerHTML='';
  rows.forEach(([key,val,hl])=>{
    const d=document.createElement('div');
    d.className='info-row';
    d.innerHTML=`<span class="info-key">${key}</span><span class="info-val${hl?' hl':''}">${val||'—'}</span>`;
    c.appendChild(d);
  });
}

/* ======================================================
   BUILD ITEM GRID (outfit, weapons)
   ====================================================== */
function buildItemGrid(containerId, ids, emptyMsg){
  const c=document.getElementById(containerId);
  c.innerHTML='';
  const arr=Array.isArray(ids)?ids:[];
  if(!arr.length){c.innerHTML=`<div class="empty-msg">${emptyMsg}</div>`;return;}
  arr.forEach(id=>{
    const sid=String(id);
    const type=getItemType(sid);
    const card=document.createElement('div');
    card.className='item-card';
    card.innerHTML=`
      <img class="item-img" src="${IMAGE_BASE}${sid}.png" alt="${sid}" loading="lazy"
           onerror="this.style.opacity='0.25';this.src='${IMAGE_BASE}902001.png'"/>
      <div class="item-type">${type}</div>`;
    c.appendChild(card);
  });
}

/* ======================================================
   BUILD SKILL LIST (plain text — no PNG)
   ====================================================== */
function buildSkillList(containerId, skills, emptyMsg){
  const c=document.getElementById(containerId);
  c.innerHTML='';
  const arr=Array.isArray(skills)?skills:[];
  if(!arr.length){c.innerHTML=`<div class="empty-msg">${emptyMsg}</div>`;return;}
  arr.forEach((s,i)=>{
    const item=document.createElement('div');
    item.className='skill-item';
    // s can be object {skillId, skillLevel} or plain number
    if(typeof s==='object' && s!==null){
      const sid  = s.skillId   || s.skill_id   || s.id || '—';
      const slvl = s.skillLevel|| s.skill_level || s.level || '—';
      item.innerHTML=`
        <span class="skill-name">Skill ${i+1}</span>
        <span class="skill-id">ID: ${sid}</span>
        <span class="skill-lvl">Level: ${slvl}</span>`;
    } else {
      item.innerHTML=`
        <span class="skill-name">Skill ${i+1}</span>
        <span class="skill-id">ID: ${s}</span>`;
    }
    c.appendChild(item);
  });
}

/* ======================================================
   RENDER FULL RESULT
   ====================================================== */
function renderResult(data){
  const ai = data.AccountInfo       || {};
  const ap = data.AccountProfileInfo|| {};
  const gi = data.GuildInfo         || {};
  const pet= data.petInfo           || {};
  const cr = data.creditScoreInfo   || {};

  // Player header
  const avatarId = ai.AccountAvatarId||'902001';
  document.getElementById('playerAvatar').src = `${IMAGE_BASE}${avatarId}.png`;
  document.getElementById('playerName').textContent = ai.AccountName||'Unknown';
  document.getElementById('tagRegion').textContent  = ai.AccountRegion||'—';
  document.getElementById('tagLevel').textContent   = `LV ${ai.AccountLevel||'—'}`;
  document.getElementById('tagGuild').textContent   = gi.GuildName||'No Guild';
  document.getElementById('statLikes').textContent  = fmtNum(ai.AccountLikes);
  document.getElementById('statEXP').textContent    = fmtNum(ai.AccountEXP);
  document.getElementById('statBPBadge').textContent= fmtNum(ai.AccountBPBadges);

  // Account info rows (horizontal)
  buildRows('accountInfoList',[
    ['Name',         ai.AccountName,             true],
    ['UID',          data.socialinfo?.accountId||'—', true],
    ['Region',       ai.AccountRegion],
    ['Level',        ai.AccountLevel],
    ['Account Type', ai.AccountType],
    ['Season ID',    ai.AccountSeasonId],
    ['Created',      fmtTime(ai.AccountCreateTime)],
    ['Last Login',   fmtTime(ai.AccountLastLogin)],
    ['Version',      ai.ReleaseVersion],
    ['Credit Score', cr.creditScore||'—'],
  ]);

  // Guild info rows
  buildRows('guildInfoList',[
    ['Guild Name',  gi.GuildName,  true],
    ['Guild ID',    gi.GuildID],
    ['Level',       gi.GuildLevel],
    ['Members',     `${gi.GuildMember} / ${gi.GuildCapacity}`],
    ['Owner ID',    gi.GuildOwner],
  ]);

  // Rank info rows
  buildRows('rankInfoList',[
    ['BR Rank Points', fmtNum(ai.BrRankPoint), true],
    ['BR Max Rank',    ai.BrMaxRank],
    ['Show BR Rank',   ai.ShowBrRank==='1'?'✅ Yes':'❌ No'],
    ['CS Rank Points', fmtNum(ai.CsRankPoint), true],
    ['CS Max Rank',    ai.CsMaxRank],
    ['Show CS Rank',   ai.ShowCsRank==='1'?'✅ Yes':'❌ No'],
    ['BP ID',          ai.AccountBPID],
  ]);

  // Pet info rows
  buildRows('petInfoList',[
    ['Pet Name',   pet.name||'—',         true],
    ['Pet ID',     pet.id||'—'],
    ['Pet Level',  pet.level||'—'],
    ['Pet EXP',    fmtNum(pet.exp)],
    ['Selected',   pet.isSelected?'✅ Yes':pet.id?'❌ No':'—'],
    ['Skill ID',   pet.selectedSkillId||'—'],
  ]);

  // Equipped outfit → images
  buildItemGrid('outfitGrid',  ap.EquippedOutfit||[],  '👗 No outfit data');

  // Equipped weapons → images
  buildItemGrid('weaponGrid',  ai.EquippedWeapon||[],  '🔫 No weapon skin data');

  // Equipped skills → PLAIN TEXT (no PNG)
  buildSkillList('skillList',  ap.EquippedSkills||[],  '⚡ No skill data');
}

/* ======================================================
   SEARCH
   ====================================================== */
async function searchPlayer(){
  const uid    = document.getElementById('uidInput').value.trim();
  const region = document.getElementById('regionSelect').value;
  if(!uid){showError('Please enter a UID / UID দিন');return;}
  if(!/^\d{5,15}$/.test(uid)){showError('Invalid UID — numbers only / শুধু সংখ্যা দিন');return;}

  setLoading(true);
  hideError();
  document.getElementById('resultSection').style.display='none';

  try{
    let url=`/get?uid=${encodeURIComponent(uid)}`;
    if(region) url+=`&region=${encodeURIComponent(region)}`;
    const res  = await fetch(url);
    const data = await res.json();
    if(!res.ok||data.error){showError(data.error||'Player not found / প্লেয়ার পাওয়া যায়নি');return;}
    renderResult(data);
    document.getElementById('resultSection').style.display='block';
    document.getElementById('resultSection').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(err){
    showError('Network error / নেটওয়ার্ক সমস্যা');
    console.error(err);
  }finally{setLoading(false);}
}

function setLoading(on){
  document.getElementById('searchBtn').disabled=on;
  document.getElementById('btnText').style.display   =on?'none':'inline';
  document.getElementById('btnLoader').style.display =on?'inline-block':'none';
}
function showError(msg){
  document.getElementById('errorMsg').textContent=msg;
  document.getElementById('errorBox').style.display='flex';
}
function hideError(){document.getElementById('errorBox').style.display='none';}

document.getElementById('uidInput').addEventListener('keydown',e=>{if(e.key==='Enter')searchPlayer();});
