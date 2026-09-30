
const CONFIG = window.SPIDERGPT_CONFIG || {};
const API = localStorage.getItem("spidergpt_api") || CONFIG.API_URL || "http://localhost:8000/api/v1";
const SUPABASE_CLIENT = (window.supabase && CONFIG.SUPABASE_URL && CONFIG.SUPABASE_ANON_KEY)
  ? window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY) : null;

const KEY = "spidergpt_access_token";
const REFRESH = "spidergpt_refresh_token";
const ASSET = "/frontend/assets/";
const state = { user:null, spider:null, usage:null, messages:[], mode:"Brain", menu:false, toast:null };

const modes = [
  {id:"Brain",icon:"◉",color:"#3B82F6",desc:"Clear, thoughtful answers."},
  {id:"Chill",icon:"☾",color:"#A855F7",desc:"Relaxed, conversational energy."},
  {id:"Chaos",icon:"✦",color:"#FACC15",desc:"Unpredictable creative energy."},
  {id:"Roast",icon:"⌁",color:"#FB7185",desc:"Playful, sharp and honest."},
  {id:"Create",icon:"✎",color:"#22C55E",desc:"Ideas, visuals and making things."},
  {id:"Focus",icon:"＋",color:"#06B6D4",desc:"Minimal distraction, maximum focus."}
];

const plans = {
  FREE:{name:"Free",price:"Free",responses:"30/day",modes:3,features:["30 AI responses / day","3 of 6 modes","Limited Spider customization"]},
  PRO:{name:"Pro",price:"₹399/mo",responses:"150/day",modes:5,features:["150 AI responses / day","5 of 6 modes","5× Spider customization"]},
  PLUS:{name:"Plus",price:"₹999/mo",responses:"Unlimited",modes:6,features:["Unlimited daily messages","All 6 modes","Full Spider customization"]}
};

function esc(value){return String(value ?? "").replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]});}
function go(path){location.hash=path;}
function currentPath(){return location.hash.slice(1)||"/";}
function icon(src,cls,alt){return '<img class="'+(cls||"asset")+'" src="'+ASSET+src+'" alt="'+esc(alt||"SpiderGPT")+'">';}
function toast(message,type){state.toast={message,type:type||"info"};render();setTimeout(function(){state.toast=null;render();},2800);}
function getInitials(name){return String(name||"SP").split(" ").map(function(x){return x[0]}).join("").slice(0,2).toUpperCase();}
function isAuthed(){return !!localStorage.getItem(KEY);}
function planFor(code){return plans[code]||plans.FREE;}

async function api(path,opt){
  opt=opt||{};
  const headers=new Headers(opt.headers||{});
  if(!headers.has("Content-Type") && !(opt.body instanceof FormData)) headers.set("Content-Type","application/json");
  const token=localStorage.getItem(KEY);
  if(token) headers.set("Authorization","Bearer "+token);
  const response=await fetch(API+path,Object.assign({},opt,{headers:headers}));
  const data=await response.json().catch(function(){return {};});
  if(response.status===401){localStorage.removeItem(KEY);localStorage.removeItem(REFRESH);}
  if(!response.ok) throw new Error(data && (data.detail || data.error?.message) || "Request failed");
  return data;
}

function logoLockup(){return icon("brand-lockup.webp","brand-lockup","SpiderGPT");}
function wordmark(){return icon("wordmark.webp","wordmark","SpiderGPT");}
function spider(){return icon("spider.webp","spider-mark","Spider");}
function appIcon(){return icon("app-icon.webp","app-icon","SpiderGPT");}

function shell(title,subtitle,body,opts){
  opts=opts||{};
  const path=currentPath();
  const nav=[
    ["/home","⌂","Home"],
    ["/chat","◉","Chat"],
    ["/history","◷","History"],
    ["/spider","✦","My Spider"],
    ["/saved","♡","Saved"],
    ["/themes","◈","Themes"],
    ["/settings","⚙","Settings"]
  ];
  const active=function(p){return path===p || (p==="/spider"&&path.startsWith("/spider/"));};
  return '<div class="app-shell">'+
    '<aside class="sidebar '+(state.menu?"open":"")+'" id="sidebar">'+
      '<div class="sidebar-brand" onclick="go(\'/home\')">'+logoLockup()+'</div>'+
      '<div class="side-section-label">WORKSPACE</div>'+
      '<nav class="nav">'+nav.map(function(n){return '<button class="nav-item '+(active(n[0])?"active":"")+'" onclick="go(\''+n[0]+'\')"><span class="nav-icon">'+n[1]+'</span><span>'+n[2]+'</span></button>';}).join("")+'</nav>'+
      '<div class="side-bottom"><div class="side-upgrade"><span>PRO / PLUS</span><b>Unlock more Spider.</b><button onclick="go(\'/pricing\')">View plans →</button></div><button class="profile-mini" onclick="go(\'/profile\')">'+
        '<span class="avatar-sm">'+esc(getInitials(state.user?.display_name||state.spider?.name))+'</span><span><b>'+esc(state.user?.display_name||"Your profile")+'</b><small>Account</small></span><span class="dots">•••</span></button></div>'+
    '</aside>'+
    '<div class="mobile-overlay" onclick="closeMenu()"></div>'+
    '<main class="main">'+
      '<header class="topbar"><button class="mobile-menu" onclick="openMenu()">☰</button><div><div class="page-kicker">SPIDERGPT</div><h1>'+esc(title)+'</h1><p>'+esc(subtitle||"")+'</p></div><button class="top-avatar" onclick="go(\'/profile\')">'+esc(getInitials(state.user?.display_name||state.spider?.name))+'</button></header>'+
      '<div class="page-content">'+body+'</div>'+
    '</main>'+
    (state.toast?'<div class="toast '+esc(state.toast.type)+'">'+esc(state.toast.message)+'</div>':"")+
  '</div>';
}
function openMenu(){state.menu=true;render();}
function closeMenu(){state.menu=false;document.querySelector(".sidebar")?.classList.remove("open");document.querySelector(".mobile-overlay")?.classList.remove("show");}

function authBackground(content,extra){
  return '<div class="auth-page"><div class="auth-bg"></div><div class="auth-top">'+wordmark()+'</div><div class="auth-center '+(extra||"")+'">'+content+'</div></div>';
}

function pageSplash(){
  return '<div class="splash-page"><div class="splash-bg"></div><div class="splash-content">'+
    '<div class="splash-logo">'+logoLockup()+'</div><p>Your AI Sidekick.</p><div class="loading-line"><span></span></div>'+
  '</div></div>';
}

function pageWelcome(){
  return authBackground('<div class="auth-card welcome-card">'+
    '<div class="auth-mark">'+appIcon()+'</div><div class="eyebrow">YOUR AI SIDEKICK</div>'+
    '<h1>Meet SpiderGPT.</h1><p class="auth-copy">Think faster. Create more. Research deeper. Your personal Spider is ready when you are.</p>'+
    '<button class="google-btn" onclick="googleLogin()"><span class="google-g">G</span><span>Continue with Google</span></button>'+
    '<div class="auth-note">Google sign-in · Secure Supabase Auth</div>'+
  '</div>','welcome');

function pageProfileSetup(){
  return authBackground('<div class="auth-card form-card">'+
    '<div class="step">01 <span>/ 02</span></div><h1>Let’s get to know you.</h1><p class="auth-copy">A few details help your Spider feel personal.</p>'+
    '<label>NAME<input id="pname" class="input" autocomplete="name" placeholder="What should we call you?"></label>'+
    '<label>AGE<input id="page" class="input" type="number" min="13" max="120" placeholder="18"></label>'+
    '<button class="primary wide" onclick="saveProfile()">Continue <span>→</span></button>'+
  '</div>','form');
}

function pageCreateSpider(){
  return authBackground('<div class="auth-card spider-create-card">'+
    '<div class="step">02 <span>/ 02</span></div><div class="create-preview">'+spider()+'</div>'+
    '<h1>Create your Spider.</h1><p class="auth-copy">Name your sidekick and choose the energy you want to start with.</p>'+
    '<input id="sname" class="input" value="Nova" maxlength="40" placeholder="Spider name">'+
    '<div class="mode-grid compact">'+modes.map(function(m){return '<button class="mode-card" data-mode="'+m.id+'" onclick="selectCreateMode(\''+m.id+'\')"><span style="color:'+m.color+'">'+m.icon+'</span><b>'+m.id+'</b><small>'+m.desc+'</small></button>';}).join("")+'</div>'+
    '<button class="primary wide" onclick="createSpider()">Bring Spider to life <span>→</span></button>'+
  '</div>','form');
}

function pageHome(){
  const p=planFor(state.usage?.plan_code);
  const name=state.spider?.name||"Spider";
  return shell("Good to see you, "+name+".","Your sidekick is ready.",'<section class="dashboard-hero">'+
    '<div class="hero-copy"><div class="eyebrow">YOUR AI SIDEKICK</div><h2>What are we doing today?</h2><p>Ask, create, research, roast, or just talk. SpiderGPT adapts to you.</p>'+
    '<div class="hero-actions"><button class="primary" onclick="go(\'/chat\')">Start chatting <span>→</span></button><button class="ghost" onclick="go(\'/personality\')">Choose a mode</button></div></div>'+
    '<div class="hero-art">'+spider()+'<span class="hero-ring"></span></div></section>'+
    '<div class="section-head"><div><h3>Quick actions</h3><p>Jump straight into your next move.</p></div></div>'+
    '<div class="quick-grid"><button onclick="go(\'/chat\')"><span class="quick-icon blue">◉</span><b>Chat with Spider</b><small>Get instant answers.</small><i>→</i></button>'+
    '<button onclick="go(\'/personality\')"><span class="quick-icon purple">◈</span><b>Switch personality</b><small>Change Spider’s energy.</small><i>→</i></button>'+
    '<button onclick="go(\'/spider/customize\')"><span class="quick-icon red">✦</span><b>Customize Spider</b><small>Make your sidekick yours.</small><i>→</i></button></div>'+
    '<div class="section-head"><div><h3>Your plan</h3><p>Current limits and access.</p></div><button class="link-btn" onclick="go(\'/pricing\')">Compare plans →</button></div>'+
    '<div class="plan-strip"><div><span class="plan-badge">'+p.name+'</span><strong>'+p.responses+'</strong><small>AI responses</small></div><div><strong>'+p.modes+'/6</strong><small>modes available</small></div><div><strong>'+((state.usage?.responses_used??0))+'</strong><small>used today</small></div></div>');
}

function pageChat(){
  return shell("Chat","Talk to your Spider.",'<div class="chat-page"><div class="chat-mode-bar">'+modes.map(function(m){return '<button class="'+(state.mode===m.id?"active":"")+'" style="--mode:'+m.color+'" onclick="setMode(\''+m.id+'\')"><span>'+m.icon+'</span>'+m.id+'</button>';}).join("")+'</div>'+
    '<div class="chat-window"><div class="chat-messages" id="chatMessages">'+
      (state.messages.length?state.messages.map(function(m){return '<div class="message-row '+m.role+'"><div class="message-avatar">'+(m.role==="user"?esc(getInitials(state.user?.display_name)) : spider())+'</div><div class="message-bubble">'+esc(m.content)+'</div></div>';}).join(""):'<div class="chat-empty"><div class="chat-empty-art">'+spider()+'</div><h2>What’s on your mind?</h2><p>Ask me anything. I’m listening.</p><div class="suggestions"><button onclick="usePrompt(\'Explain something to me simply.\')">Explain something</button><button onclick="usePrompt(\'Help me plan my day.\')">Plan my day</button><button onclick="usePrompt(\'Give me a creative idea.\')">Get creative</button></div></div>')+
    '</div><form class="composer" onsubmit="sendChat(event)"><input id="chatInput" autocomplete="off" placeholder="Message SpiderGPT…"><button class="send">↑</button></form></div></div>');
}

function pagePersonality(){
  return shell("Personality","Choose how Spider talks and thinks.",'<div class="personality-layout"><div class="personality-intro card-dark"><div class="eyebrow">CURRENT MODE</div><div class="big-mode" style="--mode:'+modes.find(function(x){return x.id===state.mode}).color+'">'+modes.find(function(x){return x.id===state.mode}).icon+'</div><h2>'+esc(state.mode)+'</h2><p>'+esc(modes.find(function(x){return x.id===state.mode}).desc)+'</p></div>'+
    '<div class="mode-list">'+modes.map(function(m){return '<button class="mode-list-item '+(state.mode===m.id?"selected":"")+'" onclick="setMode(\''+m.id+'\')"><span class="mode-dot" style="--mode:'+m.color+'">'+m.icon+'</span><span><b>'+m.id+'</b><small>'+m.desc+'</small></span><span class="check">'+(state.mode===m.id?"✓":"")+'</span></button>';}).join("")+'</div></div>');
}

function pageHistory(){
  return shell("Chat history","Pick up where you left off.",'<div class="toolbar"><div class="searchbox">⌕<input placeholder="Search conversations"></div><button class="ghost">Filter</button></div><div class="history-list">'+
    (state.messages.length?'<div class="history-item" onclick="go(\'/chat\')"><span class="history-icon">◉</span><span><b>Current conversation</b><small>'+esc(state.messages[state.messages.length-1].content.slice(0,70))+'</small></span><em>Now</em></div>':'<div class="empty-state">'+spider()+'<h3>No conversations yet</h3><p>Your future chats will appear here.</p><button class="primary" onclick="go(\'/chat\')">Start a chat</button></div>')+
  '</div>');
}

function pageProfile(){
  return shell("Profile","Your account and Spider identity.",'<div class="profile-grid"><div class="profile-card card-dark"><div class="profile-avatar">'+esc(getInitials(state.user?.display_name))+'</div><div><div class="eyebrow">ACCOUNT</div><h2>'+esc(state.user?.display_name||"Your profile")+'</h2><p class="muted">'+esc(state.user?.email||"Google account")+'</p></div><button class="ghost" onclick="go(\'/settings\')">Edit settings</button></div>'+
    '<div class="info-grid"><div class="info-card"><span>Spider</span><b>'+esc(state.spider?.name||"Not created")+'</b><button onclick="go(\'/spider\')">Open →</button></div><div class="info-card"><span>Plan</span><b>'+planFor(state.usage?.plan_code).name+'</b><button onclick="go(\'/billing\')">Manage →</button></div></div></div>');
}

function pageSpider(){
  return shell("My Spider","Your companion, your rules.",'<div class="spider-profile card-dark"><div class="spider-large">'+spider()+'</div><div><div class="eyebrow">YOUR SPIDER</div><h2>'+esc(state.spider?.name||"Nova")+'</h2><p class="muted">Mode: '+esc(state.mode)+'</p><div class="tag-row"><span>Personal AI</span><span>Adaptive</span><span>Private</span></div><div class="hero-actions"><button class="primary" onclick="go(\'/spider/customize\')">Customize Spider</button><button class="ghost" onclick="go(\'/share\')">Share preview</button></div></div></div>');
}

function pageSettings(){
  return shell("Settings","Control your account and app experience.",'<div class="settings-list"><div class="setting-group"><div class="setting-title">ACCOUNT</div><button class="setting-row" onclick="go(\'/profile\')"><span><b>Profile</b><small>Name, age and account identity.</small></span><span>→</span></button><button class="setting-row" onclick="go(\'/billing\')"><span><b>Billing & subscription</b><small>Plans, payments and cancellation.</small></span><span>→</span></button></div>'+
    '<div class="setting-group"><div class="setting-title">APP</div><button class="setting-row" onclick="go(\'/themes\')"><span><b>Theme</b><small>Choose the visual mood.</small></span><span>→</span></button><button class="setting-row" onclick="go(\'/usage\')"><span><b>Usage</b><small>See your daily limits.</small></span><span>→</span></button></div>'+
    '<div class="setting-group"><div class="setting-title">SESSION</div><button class="setting-row danger" onclick="logout()"><span><b>Sign out</b><small>End this session on this device.</small></span><span>↗</span></button></div></div>');
}

function pageCustomize(){
  return shell("Spider customization","Shape your sidekick within your plan.",'<div class="customize-layout"><div class="custom-preview card-dark"><div class="custom-spider">'+spider()+'</div><h2>'+esc(state.spider?.name||"Nova")+'</h2><p class="muted">Preview</p></div><div class="custom-form card-dark"><div class="eyebrow">IDENTITY</div><label>SPIDER NAME<input id="newSpiderName" class="input" value="'+esc(state.spider?.name||"Nova")+'"></label><div class="eyebrow">APPEARANCE</div><div class="appearance-grid"><button class="appearance active">Classic</button><button class="appearance">Crimson</button><button class="appearance">Midnight</button><button class="appearance">Neon</button></div><button class="primary wide" onclick="saveSpiderName()">Save changes</button><p class="form-hint">Customization limits are enforced by your backend plan entitlements.</p></div></div>');
}

function pageThemes(){
  const themes=[["Obsidian","Deep black + red glow"],["Crimson Web","Red-lit web atmosphere"],["Midnight","Low-light blue-black mood"],["Minimal","Clean dark surfaces"]];
  return shell("Themes","Make SpiderGPT feel like yours.",'<div class="theme-grid">'+themes.map(function(t,i){return '<button class="theme-card '+(i===0?"selected":"")+'" onclick="selectTheme(this)"><span class="theme-preview theme-'+i+'"></span><b>'+t[0]+'</b><small>'+t[1]+'</small><span class="theme-check">'+(i===0?"✓":"")+'</span></button>';}).join("")+'</div>');
}

function pageSaved(){
  return shell("Saved","Your favorite Spider moments.",'<div class="empty-state">'+
    '<div class="empty-heart">♡</div><h3>Nothing saved yet.</h3><p>Save useful answers and ideas from your chats to find them here.</p><button class="primary" onclick="go(\'/chat\')">Go to chat</button></div>');
}

function pageShare(){
  return shell("Share preview","Preview what your Spider profile looks like to others.",'<div class="share-layout"><div class="share-card-preview"><div class="share-glow"></div><div class="share-brand">'+wordmark()+'</div><div class="share-spider">'+spider()+'</div><h2>'+esc(state.spider?.name||"Nova")+'</h2><p>Your AI Sidekick.</p><span class="share-mode">'+esc(state.mode)+' mode</span></div><div class="share-controls card-dark"><div class="eyebrow">SHARE CARD</div><h2>Ready to share.</h2><p class="muted">This is the public preview of your Spider identity.</p><button class="primary wide" onclick="navigator.clipboard?.writeText(location.origin+location.pathname+\'#share\');toast(\'Share link copied\',\'success\')">Copy share link</button></div></div>');
}

function pageUsage(){
  const used=Number(state.usage?.responses_used||0); const limit=state.usage?.responses_limit;
  const label=limit===-1?"Unlimited":String(limit??30); const pct=limit===-1?8:Math.min(100,(used/Math.max(1,limit||30))*100);
  return shell("Usage","Know where you stand today.",'<div class="usage-hero card-dark"><div><div class="eyebrow">AI RESPONSES TODAY</div><h2>'+used+' <span>/ '+label+'</span></h2><p class="muted">'+(limit===-1?"Unlimited daily responses on Plus.":Math.max(0,(limit||30)-used)+" responses remaining today.")+'</p></div><div class="progress-ring" style="--pct:'+pct+'%"><span>'+Math.round(pct)+'%</span></div></div>'+
    '<div class="usage-grid"><div class="usage-card"><span>Plan</span><b>'+planFor(state.usage?.plan_code).name+'</b></div><div class="usage-card"><span>Modes</span><b>'+planFor(state.usage?.plan_code).modes+' / 6</b></div><div class="usage-card"><span>Spider changes</span><b>Plan based</b></div></div><button class="primary" onclick="go(\'/pricing\')">See upgrade options →</button>');
}

function pagePricing(){
  return shell("Plans","Choose how your Spider grows with you.",'<div class="pricing-intro"><div><div class="eyebrow">SIMPLE PLANS</div><h2>More Spider. More freedom.</h2><p class="muted">Upgrade when you need more messages, modes and customization.</p></div></div><div class="plans-grid">'+Object.keys(plans).map(function(code){const p=plans[code];return '<article class="pricing-card '+(code==="PRO"?"featured":"")+'"><div class="pricing-top"><span class="plan-badge">'+p.name+'</span>'+(code==="PRO"?'<span class="popular">POPULAR</span>':"")+'</div><div class="price">'+p.price+'</div><div class="price-note">'+(code==="FREE"?"No payment required":"Monthly subscription")+'</div><div class="feature-list">'+p.features.map(function(f){return '<span>✓ '+f+'</span>';}).join("")+'</div><button class="'+(code==="FREE"?"ghost":"primary")+' wide" onclick="'+(code==="FREE"?"go(\'/home\')":"go(\'/checkout/"+code+"\')")+'">'+(code==="FREE"?"Current plan":"Choose "+p.name)+'</button></article>';}).join("")+'</div>');
}

function pageCheckout(plan){
  const p=planFor(plan);
  return shell("Checkout","Secure recurring subscription.",'<div class="checkout-layout"><div class="checkout-summary card-dark"><div class="eyebrow">YOU’RE CHOOSING</div><h2>'+p.name+'</h2><div class="checkout-price">'+p.price+'</div><div class="feature-list">'+p.features.map(function(f){return '<span>✓ '+f+'</span>';}).join("")+'</div></div><div class="payment-card card-dark"><div class="secure-pill">⌁ SECURE PAYMENT</div><h3>Continue to payment</h3><p class="muted">You’ll be redirected to the configured Stripe or Razorpay checkout.</p><button class="primary wide" onclick="startCheckout(\''+plan+'\')">Continue securely <span>→</span></button><button class="link-btn wide" onclick="go(\'/pricing\')">Back to plans</button></div></div>');
}

function pageSuccess(){
  return shell("Payment success","Your subscription is being confirmed.",'<div class="success-card card-dark"><div class="success-icon">✓</div><h2>Welcome to your new plan.</h2><p class="muted">Your provider confirmation will update your account subscription.</p><button class="primary" onclick="go(\'/home\')">Back home</button></div>');
}

function pageBilling(){
  const p=planFor(state.usage?.plan_code);
  return shell("Billing & subscription","Manage your current subscription.",'<div class="billing-card card-dark"><div><div class="eyebrow">CURRENT PLAN</div><h2>'+p.name+'</h2><p class="muted">'+p.responses+' · '+p.modes+'/6 modes</p></div><span class="status-pill">ACTIVE</span></div><div class="billing-actions"><button class="info-card" onclick="go(\'/pricing\')"><span>Change plan</span><b>Compare plans →</b></button><button class="info-card" onclick="toast(\'Cancellation is handled by the payment provider.\',\'info\')"><span>Subscription</span><b>Manage cancellation →</b></button></div>');
}

async function googleLogin(){
  if(!SUPABASE_CLIENT){toast("Add your Supabase URL and anon key in frontend/config.js.","error");return;}
  const result=await SUPABASE_CLIENT.auth.signInWithOAuth({provider:"google",options:{redirectTo:location.origin+location.pathname}});
  if(result.error) toast(result.error.message,"error");
}
async function syncSession(){
  if(!SUPABASE_CLIENT || localStorage.getItem(KEY)) return;
  const session=await SUPABASE_CLIENT.auth.getSession();
  const token=session.data?.session?.access_token;
  if(!token) return;
  try{
    const result=await api("/auth/google",{method:"POST",body:JSON.stringify({access_token:token})});
    localStorage.setItem(KEY,result.access_token);
    if(result.refresh_token) localStorage.setItem(REFRESH,result.refresh_token);
    go(result.onboarding_completed?"/home":"/profile-setup");
  }catch(error){console.error(error);}
}
async function load(){
  try{
    const values=await Promise.all([api("/usage"),api("/spider/me")]);
    state.usage=values[0];state.spider=values[1];
  }catch(error){}
}
async function saveProfile(){
  const name=document.querySelector("#pname")?.value.trim(); const age=Number(document.querySelector("#page")?.value);
  if(!name || !age){toast("Please enter your name and age.","error");return;}
  try{await api("/profile/me",{method:"PUT",body:JSON.stringify({display_name:name,age:age})});go("/create-spider");}catch(e){toast(e.message,"error");}
}
function selectCreateMode(id){document.querySelectorAll(".mode-card").forEach(function(x){x.classList.toggle("selected",x.dataset.mode===id)});state.mode=id;}
async function createSpider(){
  const name=document.querySelector("#sname")?.value.trim()||"Nova";
  try{await api("/spider",{method:"POST",body:JSON.stringify({name:name,personality_mode:state.mode,appearance_id:"default"})});await load();go("/home");}catch(e){toast(e.message,"error");}
}
function setMode(id){state.mode=id;render();}
function usePrompt(text){const input=document.querySelector("#chatInput");if(input){input.value=text;input.focus();}}
async function sendChat(event){
  event.preventDefault();const input=document.querySelector("#chatInput");const message=input?.value.trim();if(!message)return;
  input.value="";state.messages.push({role:"user",content:message});render();
  try{const result=await api("/chat",{method:"POST",body:JSON.stringify({message:message,mode:state.mode})});state.messages.push({role:"assistant",content:result?.assistant_message?.content||result?.message||"Done."});}
  catch(e){state.messages.push({role:"assistant",content:e.message});}
  render();
}
async function saveSpiderName(){
  const name=document.querySelector("#newSpiderName")?.value.trim();if(!name)return;
  try{await api("/spider/me",{method:"PUT",body:JSON.stringify({name:name})});state.spider=Object.assign({},state.spider,{name:name});toast("Spider updated.","success");render();}
  catch(e){toast(e.message,"error");}
}
function selectTheme(el){document.querySelectorAll(".theme-card").forEach(function(x){x.classList.remove("selected");x.querySelector(".theme-check").textContent=""});el.classList.add("selected");el.querySelector(".theme-check").textContent="✓";toast("Theme selected.","success");}
async function startCheckout(plan){
  try{const result=await api("/payments/checkout",{method:"POST",body:JSON.stringify({plan_code:plan,billing_period:"monthly",currency:"INR"})});if(result.checkout_url)location.href=result.checkout_url;else go("/payment-success");}
  catch(e){toast(e.message,"error");}
}
async function logout(){
  try{if(SUPABASE_CLIENT)await SUPABASE_CLIENT.auth.signOut();}catch(e){}
  localStorage.removeItem(KEY);localStorage.removeItem(REFRESH);state.user=null;state.spider=null;state.usage=null;go("/welcome");
}

async function route(){
  const p=currentPath();
  if(p==="/") return pageSplash();
  if(p==="/welcome") return pageWelcome();
  if(p==="/profile-setup") return pageProfileSetup();
  if(p==="/create-spider") return pageCreateSpider();
  if(p==="/home"){await load();return pageHome();}
  if(p==="/chat") return pageChat();
  if(p==="/personality") return pagePersonality();
  if(p==="/history") return pageHistory();
  if(p==="/profile") return pageProfile();
  if(p==="/spider") return pageSpider();
  if(p==="/settings") return pageSettings();
  if(p==="/spider/customize") return pageCustomize();
  if(p==="/themes") return pageThemes();
  if(p==="/saved") return pageSaved();
  if(p==="/share") return pageShare();
  if(p==="/usage"){if(!state.usage)await load();return pageUsage();}
  if(p==="/pricing") return pagePricing();
  if(p==="/payment-success") return pageSuccess();
  if(p==="/billing"){if(!state.usage)await load();return pageBilling();}
  if(p.startsWith("/checkout/")) return pageCheckout(p.split("/")[2]?.toUpperCase()||"PRO");
  return pageSplash();
}

let splashTimer=null;
async function render(){
  clearTimeout(splashTimer);
  const p=currentPath();
  if(p==="/"){
    document.querySelector("#app").innerHTML=pageSplash();
    splashTimer=setTimeout(function(){go(isAuthed()?"/home":"/welcome")},1100);
    return;
  }
  const html=await route();
  document.querySelector("#app").innerHTML=html;
  if(state.menu){document.querySelector(".mobile-overlay")?.classList.add("show");document.querySelector(".sidebar")?.classList.add("open");}
  window.scrollTo(0,0);
}
window.addEventListener("hashchange",render);
window.addEventListener("DOMContentLoaded",function(){syncSession().finally(render);});
if(document.readyState!=="loading") syncSession().finally(render);
