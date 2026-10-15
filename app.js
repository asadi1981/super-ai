const $ = (id) => document.getElementById(id);
const STORE = {settings:'superai_settings_v2', chats:'superai_chats_v2', notes:'superai_notes_v2'};
let messages = JSON.parse(localStorage.getItem(STORE.chats) || '[]');
let busy = false;

function settings(){ return JSON.parse(localStorage.getItem(STORE.settings) || '{}'); }
function saveSettings(){
  const s={mode:$('providerType').value, endpoint:$('apiBase').value.trim(), model:$('modelName').value.trim()};
  localStorage.setItem(STORE.settings,JSON.stringify(s));
  $('settingsStatus').textContent='تنظیمات در همین مرورگر ذخیره شد.';
  updateStatus();
}
function updateStatus(){
  const s=settings(); const online=s.endpoint && s.mode==='online';
  $('modePill').textContent=online?'آنلاین':'آفلاین / محلی';
  $('connectionLabel').textContent=online?'درگاه آنلاین تنظیم شده':'حالت محلی فعال';
}
function addMessage(role,content){
  messages.push({role,content,at:Date.now()});
  localStorage.setItem(STORE.chats,JSON.stringify(messages.slice(-100)));
  renderMessages();
}
function renderMessages(){
  const box=$('messages'); box.innerHTML='';
  for(const m of messages){const el=document.createElement('article');el.className='message '+(m.role==='user'?'user':'assistant');const who=document.createElement('b');who.textContent=m.role==='user'?'شما':'SUPER AI';const body=document.createElement('div');body.textContent=m.content;el.append(who,body);box.append(el);}
  box.scrollTop=box.scrollHeight;
  $('welcome').style.display=messages.length?'none':'block';
}
async function send(){
  const text=$('prompt').value.trim(); if(!text||busy)return;
  $('prompt').value=''; addMessage('user',text); busy=true; $('sendBtn').disabled=true;
  const s=settings();
  try{
    if(s.mode!=='online'||!s.endpoint) throw new Error('NO_ONLINE_CONFIG');
    const base=s.endpoint.replace(/\/$/, '').replace(/\/api\/chat$/, '');
    const response=await fetch(base+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:messages.filter(m=>['user','assistant'].includes(m.role)&&typeof m.content==='string'&&m.content.trim()).slice(-19).map(m=>({role:m.role,content:m.content.trim()})),model:s.model||'openrouter/free'})});
    const data=await response.json(); if(!response.ok) throw new Error(data.error||('خطای سرور '+response.status));
    const answer=data.answer||data.choices?.[0]?.message?.content;
    if(!answer) throw new Error('پاسخ معتبری از مدل دریافت نشد.');
    addMessage('assistant',answer);
  }catch(e){
    const msg=e.message==='NO_ONLINE_CONFIG'?'موتور آنلاین هنوز تنظیم نشده است. وارد «تنظیمات اتصال» شو و نشانی Worker را وارد کن. تا آن زمان تاریخچه و یادداشت‌ها روی گوشی ذخیره می‌شوند، اما پاسخ هوشمند آفلاین هنوز فعال نیست.':e.message;
    addMessage('assistant','اتصال برقرار نشد: '+msg);
  }finally{busy=false;$('sendBtn').disabled=false;}
}
function switchView(name){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id==='view-'+name));document.querySelectorAll('.nav-item').forEach(v=>v.classList.toggle('active',v.dataset.view===name));const labels={chat:'گفت‌وگو با هوش مصنوعی',creator:'استودیو تولید محتوا',files:'ابزار فایل‌ها',memory:'حافظه و یادداشت‌ها',settings:'تنظیمات اتصال'};$('pageTitle').textContent=labels[name]||'SUPER AI';$('sidebar').classList.remove('open');}
function loadNotes(){const notes=JSON.parse(localStorage.getItem(STORE.notes)||'[]');const list=$('notesList');list.innerHTML='';notes.forEach((n,i)=>{const d=document.createElement('div');d.className='card note';d.textContent=n;const b=document.createElement('button');b.className='secondary';b.textContent='حذف';b.onclick=()=>{notes.splice(i,1);localStorage.setItem(STORE.notes,JSON.stringify(notes));loadNotes();};d.append(b);list.append(d);});}
function init(){
 const s=settings(); $('providerType').value=s.mode||'online'; $('apiBase').value=s.endpoint||'https://super-ai-engine.bita-bita1981-0001.workers.dev'; $('modelName').value=s.model||'openrouter/free';
 $('providerHelp').textContent='برای اتصال آنلاین، نشانی Worker امن خودت را وارد کن. کلید API فقط در تنظیمات سرور نگهداری می‌شود؛ آن را اینجا وارد نکن.';
 $('securityWarning').textContent='کلید API را هرگز در GitHub یا مرورگر ذخیره نکن. آن را به‌عنوان Secret در محیط Cloudflare Worker تنظیم کن.';
 $('providerType').onchange=()=>{$('providerHelp').textContent=$('providerType').value==='online'?'نشانی Cloudflare Worker را وارد کن.':'حالت آفلاین فعلاً حافظه محلی را نگه می‌دارد؛ پاسخ‌گویی با مدل محلی اندروید در مرحله بعد اضافه می‌شود.';};
 $('sendBtn').onclick=send; $('prompt').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
 $('saveSettings').onclick=saveSettings;
 $('testConnection').onclick=async()=>{saveSettings();const s=settings();if(s.mode!=='online'||!s.endpoint){$('settingsStatus').textContent='ابتدا حالت آنلاین و نشانی Worker را وارد کن.';return;}try{const base=s.endpoint.replace(/\/$/,'').replace(/\/api\/chat$/,'');const r=await fetch(base+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:[{role:'user',content:'فقط OK پاسخ بده'}],model:s.model||'openrouter/free'})});const d=await r.json();$('settingsStatus').textContent=r.ok&&d.choices?.[0]?.message?.content?'اتصال برقرار است. پاسخ موتور دریافت شد.':'خطا در پاسخ موتور: '+(d.error||r.status);}catch(e){$('settingsStatus').textContent='اتصال ناموفق: '+e.message;}};
 $('newChat').onclick=()=>{messages=[];localStorage.setItem(STORE.chats,'[]');renderMessages();switchView('chat');};
 document.querySelectorAll('.nav-item').forEach(b=>b.onclick=()=>switchView(b.dataset.view));
 document.querySelectorAll('.suggestion').forEach(b=>b.onclick=()=>{$('prompt').value=b.dataset.prompt;$('prompt').focus();});
 $('menuBtn').onclick=()=>$('sidebar').classList.toggle('open');
 $('saveNote').onclick=()=>{const v=$('noteInput').value.trim();if(!v)return;const n=JSON.parse(localStorage.getItem(STORE.notes)||'[]');n.unshift(v);localStorage.setItem(STORE.notes,JSON.stringify(n));$('noteInput').value='';loadNotes();};
 $('generateContent').onclick=()=>{$('prompt').value='برای موضوع زیر یک بسته محتوای کوتاه شامل قلاب ۳ ثانیه‌ای، سناریو، عنوان و کپشن بساز: '+$('contentTopic').value+'\nپلتفرم: '+$('contentPlatform').value+'؛ سبک: '+$('contentStyle').value;switchView('chat');};
 $('analyzeFile').onclick=()=>{$('prompt').value='این متن را تحلیل و خلاصه کن:\n'+$('fileText').value;switchView('chat');};
 $('fileInput').onchange=async e=>{const f=e.target.files[0];if(f)$('fileText').value=await f.text();};
 $('exportBtn').onclick=()=>{const blob=new Blob([messages.map(m=>(m.role==='user'?'شما':'SUPER AI')+': '+m.content).join('\n\n')],{type:'text/plain;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='super-ai-chat.txt';a.click();URL.revokeObjectURL(a.href);};
 $('voiceBtn').onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert('تشخیص گفتار در این مرورگر پشتیبانی نمی‌شود.');return;}const rec=new SR();rec.lang='fa-IR';rec.onresult=e=>$('prompt').value+=(e.results[0][0].transcript||'');rec.start();};
 updateStatus();renderMessages();loadNotes();
}
init();
