const $=id=>document.getElementById(id);
const STORE={settings:"superai.settings",notes:"superai.notes",history:"superai.history"};
let history=JSON.parse(localStorage.getItem(STORE.history)||"[]");
let settings=JSON.parse(localStorage.getItem(STORE.settings)||"{}");
let activeView="chat";
function saveHistory(){localStorage.setItem(STORE.history,JSON.stringify(history.slice(-80)))}
function addMessage(role,content){const el=document.createElement("div");el.className="message "+role;const label=document.createElement("div");label.className="role";label.textContent=role==="user"?"شما":"SUPER AI";const body=document.createElement("div");body.textContent=content;el.append(label,body);$("messages").append(el);$("messages").scrollTop=$("messages").scrollHeight}
function renderHistory(){ $("messages").innerHTML="";history.forEach(m=>addMessage(m.role,m.content));$("welcome").classList.toggle("hidden",history.length>0)}
function provider(){return settings.providerType||"compatible"}
function setConnection(){const ready=provider()==="ollama"?!!(settings.apiBase&&settings.modelName):!!(settings.apiBase&&settings.modelName&&settings.apiKey);$("connectionLabel").textContent=ready?(provider()==="ollama"?"موتور محلی پیکربندی شده":"سرویس آنلاین پیکربندی شده"):"اتصال تنظیم نشده";$("modePill").textContent=ready?(provider()==="ollama"?"مدل محلی / Ollama":"مدل آنلاین"):"حالت محلی / بدون اتصال"}
function showView(name){activeView=name;document.querySelectorAll(".view").forEach(v=>v.classList.remove("active"));$("view-"+name).classList.add("active");document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.view===name));const titles={chat:"گفت‌وگو با هوش مصنوعی",creator:"استودیو تولید محتوا",files:"ابزار فایل‌ها",memory:"حافظه و یادداشت‌ها",settings:"تنظیمات اتصال"};$("pageTitle").textContent=titles[name];$("sidebar").classList.remove("open")}
async function askAI(messages){
 const kind=provider(),base=(settings.apiBase||"").replace(/\/+$/,""),model=settings.modelName;
 if(!base||!model||(kind==="compatible"&&!settings.apiKey)) return "موتور هوش مصنوعی هنوز تنظیم نشده است.\n\nبه بخش «تنظیمات اتصال» برو و Ollama محلی یا یک API سازگار را پیکربندی کن.\n\nیادداشت‌ها و تاریخچه محلی بدون اتصال هم در دسترس‌اند.";
 let response;
 if(kind==="ollama"){
  response=await fetch(base+"/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model,messages,stream:false,options:{temperature:0.7}})});
  if(!response.ok)throw new Error("Ollama: "+response.status+" "+(await response.text()).slice(0,220));
  const data=await response.json();return data.message?.content||"مدل پاسخی برنگرداند.";
 }
 response=await fetch(base+"/chat/completions",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+settings.apiKey},body:JSON.stringify({model,messages,temperature:.7})});
 if(!response.ok) throw new Error("خطای سرویس: "+response.status+" "+(await response.text()).slice(0,250));
 const data=await response.json();return data.choices?.[0]?.message?.content||"پاسخی از سرویس دریافت نشد.";
}
async function send(text){text=text.trim();if(!text)return;$("welcome").classList.add("hidden");history.push({role:"user",content:text});addMessage("user",text);saveHistory();$("prompt").value="";$("sendBtn").disabled=true;const waiting=document.createElement("div");waiting.className="message assistant";waiting.textContent="در حال پردازش…";$("messages").append(waiting);try{const reply=await askAI(history);waiting.remove();history.push({role:"assistant",content:reply});addMessage("assistant",reply);saveHistory()}catch(e){waiting.remove();const msg="ارتباط با سرویس برقرار نشد: "+e.message+"\nتنظیمات API و اتصال اینترنت را بررسی کن.";addMessage("assistant",msg);history.push({role:"assistant",content:msg});saveHistory()}finally{$("sendBtn").disabled=false}}
$("sendBtn").onclick=()=>send($("prompt").value);
$("prompt").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send($("prompt").value)}});
$("newChat").onclick=()=>{history=[];saveHistory();renderHistory();showView("chat")};
document.querySelectorAll(".nav-item").forEach(b=>b.onclick=()=>showView(b.dataset.view));
document.querySelectorAll(".suggestion").forEach(b=>b.onclick=()=>{$("prompt").value=b.dataset.prompt;$("prompt").focus()});
$("menuBtn").onclick=()=>$("sidebar").classList.toggle("open");
$("exportBtn").onclick=()=>{const blob=new Blob([history.map(m=>(m.role==="user"?"شما":"SUPER AI")+":\n"+m.content).join("\n\n")],{type:"text/plain;charset=utf-8"});download(blob,"super-ai-chat.txt")};
function download(blob,name){const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;a.click();URL.revokeObjectURL(a.href)}
function syncProviderUI(){const local=$("providerType").value==="ollama";$("apiKeyWrap").classList.toggle("hidden",local);$("providerHelp").textContent=local?"اتصال به Ollama؛ بدون کلید API. مدل باید قبلاً دانلود شده باشد.":"اتصال به یک سرویس آنلاین با قالب OpenAI Chat Completions.";$("apiBase").placeholder=local?"http://localhost:11434":"https://api.example.com/v1";$("securityWarning").textContent=local?"برای گوشی: localhost یعنی خود گوشی، نه رایانه. اگر Ollama روی رایانه است، از IP محلی رایانه مانند http://192.168.1.10:11434 استفاده کن. Ollama باید برای شبکه محلی/CORS پیکربندی شود. آن را بدون احراز هویت روی اینترنت عمومی قرار نده.":"هشدار امنیتی: این نسخه آزمایشی کلید را در حافظه محلی مرورگر نگه می‌دارد و مستقیم به سرویس وصل می‌شود. برای استفاده عمومی، کلید باید فقط روی Backend امن نگهداری شود."}
$("providerType").value=settings.providerType||"compatible";$("apiBase").value=settings.apiBase||"";$("modelName").value=settings.modelName||"";$("apiKey").value=settings.apiKey||"";syncProviderUI();$("providerType").onchange=syncProviderUI;setConnection();
$("saveSettings").onclick=()=>{settings={providerType:$("providerType").value,apiBase:$("apiBase").value.trim(),modelName:$("modelName").value.trim(),apiKey:$("apiKey").value.trim()};localStorage.setItem(STORE.settings,JSON.stringify(settings));setConnection();$("settingsStatus").textContent="تنظیمات موتور ذخیره شد."};
$("testConnection").onclick=async()=>{$("settingsStatus").textContent="در حال آزمایش اتصال…";const temp={providerType:$("providerType").value,apiBase:$("apiBase").value.trim(),modelName:$("modelName").value.trim(),apiKey:$("apiKey").value.trim()};const old=settings;settings=temp;try{const r=await askAI([{role:"user",content:"فقط بنویس: موتور SUPER AI آماده است."}]);$("settingsStatus").textContent="اتصال موفق؛ پاسخ مدل: "+r.slice(0,180)}catch(e){$("settingsStatus").textContent="اتصال ناموفق: "+e.message}finally{settings=old}};
$("generateContent").onclick=async()=>{const topic=$("contentTopic").value.trim();if(!topic)return alert("موضوع محتوا را وارد کن.");const p=`برای موضوع «${topic}» و پلتفرم ${$("contentPlatform").value} با سبک ${$("contentStyle").value} یک بسته کامل بساز: هوک ۳ ثانیه اول، سناریوی ۳۰ تا ۴۵ ثانیه‌ای با زمان‌بندی، پیشنهاد تصویر و تدوین، عنوان جذاب، کپشن و هشتگ. خروجی فارسی و کاربردی باشد.`;$("contentResult").textContent="در حال ساخت…";try{$("contentResult").textContent=await askAI([{role:"user",content:p}])}catch(e){$("contentResult").textContent=e.message}};
$("fileInput").onchange=async e=>{const f=e.target.files[0];if(!f)return;try{$("fileText").value=await f.text()}catch{$("fileText").value="خواندن این فایل ممکن نیست."}};
$("analyzeFile").onclick=()=>{const t=$("fileText").value.trim();if(!t)return alert("ابتدا یک فایل متنی انتخاب کن.");showView("chat");send("لطفاً متن زیر را خلاصه و تحلیل کن:\n\n"+t.slice(0,18000))};
function renderNotes(){const notes=JSON.parse(localStorage.getItem(STORE.notes)||"[]");$("notesList").innerHTML="";notes.forEach((n,i)=>{const d=document.createElement("div");d.className="note";d.textContent=n;const b=document.createElement("button");b.className="secondary";b.textContent="حذف";b.onclick=()=>{notes.splice(i,1);localStorage.setItem(STORE.notes,JSON.stringify(notes));renderNotes()};d.append(document.createElement("br"),b);$("notesList").append(d)})}
$("saveNote").onclick=()=>{const n=$("noteInput").value.trim();if(!n)return;const notes=JSON.parse(localStorage.getItem(STORE.notes)||"[]");notes.unshift(n);localStorage.setItem(STORE.notes,JSON.stringify(notes));$("noteInput").value="";renderNotes()};
renderNotes();renderHistory();
$("voiceBtn").onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert("تشخیص گفتار در این مرورگر پشتیبانی نمی‌شود.");return}const rec=new SR();rec.lang="fa-IR";rec.onresult=e=>$("prompt").value+=e.results[0][0].transcript;rec.start()};
if("serviceWorker" in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}));
