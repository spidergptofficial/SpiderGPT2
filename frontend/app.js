
const CONFIG = window.SPIDERGPT_CONFIG || {};
const API = (CONFIG.API_URL || "/api/v1").replace(/\/$/, "");
const SUPABASE_CLIENT = (window.supabase && CONFIG.SUPABASE_URL && CONFIG.SUPABASE_ANON_KEY)
  ? window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY) : null;

const ACCESS_KEY = "spidergpt_access_token";
const REFRESH_KEY = "spidergpt_refresh_token";
const MODE_KEY = "spidergpt_mode";
const THEME_KEY = "spidergpt_theme";
const ASSET = "/frontend/assets/";

const ALL_MODES = [
  {id:"Brain",icon:"◉",color:"#3B82F6",desc:"Clear, thoughtful answers."},
  {id:"Chill",icon:"☾",color:"#A855F7",desc:"Relaxed, conversational energy."},
  {id:"Chaos",icon:"✦",color:"#FACC15",desc:"Unpredictable creative energy."},
  {id:"Roast",icon:"⌁",color:"#FB7185",desc:"Playful, sharp and honest."},
  {id:"Create",icon:"✎",color:"#22C55E",desc:"Ideas, visuals and making things."},
  {id:"Focus",icon:"＋",color:"#06B6D4",desc:"Minimal distraction, maximum focus."}
];

const DEFAULT_PLANS = {
  FREE:{name:"Free",price:"Free",responses:"30/day",modes:3,features:["30 AI responses / day","3 of 6 modes","Limited Spider customization"]},
  PRO:{name:"Pro",price:"₹399/mo",responses:"150/day",modes:5,features:["150 AI responses / day","5 of 6 modes","5× Spider customization"]},
  PLUS:{name:"Plus",price:"₹999/mo",responses:"Unlimited",modes:6,features:["Unlimited daily messages","All 6 modes","Full Spider customization"]}
};

const state = {
  user:null, spider:null, usage:null, subscription:null, plans:[],
  messages:[], conversations:[], saved:[], conversationId:null,
  mode:localStorage.getItem(MODE_KEY) || "Brain", menu:false, toast:null,
  loading:false
};

function esc(value){return String(value ?? "").replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c];});}
function go(path){location.hash=path;}
function currentPath(){const raw=location.hash.slice(1)||"/";return raw.split("?")[0]||"/";}
function icon(src,cls,alt){return '<img class="'+(cls||"asset")+'" src="'+ASSET+src+'" alt="'+esc(alt||"SpiderGPT")+'">';}
function logoLockup(){return icon("brand-lockup.webp","brand-lockup","SpiderGPT");}
function wordmark(){return icon("wordmark.webp","wordmark","SpiderGPT");}
function spider(){return icon("spider.webp","spider-mark","Spider");}
function appIcon(){return icon("app-icon.webp","app-icon","SpiderGPT");}
function initials(name){return String(name||"SP").split(/\s+/).filter(Boolean).map(function(x){return x[0];}).join("").slice(0,2).toUpperCase()||"SP";}
function token(){return localStorage.getItem(ACCESS_KEY);}
function isAuthed(){return !!token();}
function toast(message,type){state.toast={message:String(message||""),type:type||"info"};render();window.clearTimeout(toast._t);toast._t=window.setTimeout(function(){state.toast=null;render();},3200);}
function planCode(){return String(state.usage?.plan||"FREE").toUpperCase();}
function planFor(code){return DEFAULT_PLANS[String(code||"FREE").toUpperCase()]||DEFAULT_PLANS.FREE;}
function allowedModes(){return state.usage?.features?.allowed_modes || ["Brain","Chill","Focus"];}
function canUseMode(id){return allowedModes().includes(id);}
function normalizeSpider(data){if(!data)return null;return Object.assign({},data,{name:data.spider_name});}
function normalizeMessage(m){return {id:m.id,role:m.role,content:m.content,conversation_id:m.conversation_id,created_at:m.created_at};}

async function rawApi(path,opt){
  opt=opt||{};
  const headers=new Headers(opt.headers||{});
  if(!headers.has("Content-Type") && !(opt.body instanceof FormData)) headers.set("Content-Type","application/json");
  const access=token();
  if(access) headers.set("Authorization","Bearer "+access);
  const response=await fetch(API+path,Object.assign({},opt,{headers:headers}));
  const data=await response.json().catch(function(){return {};});
  return {response,data};
}

async function refreshSession(){
  const refresh=localStorage.getItem(REFRESH);
  if(!refresh) return false;
  try{
    const result=await rawApi("/auth/refresh",{method:"POST",body:JSON.stringify({refresh_token:refresh})});
    if(!result.response.ok || !result.data.access_token) return false;
    localStorage.setItem(ACCESS_KEY,result.data.access_token);
    if(result.data.refresh_token) localStorage.setItem(REFRESH_KEY,result.data.refresh_token);
    return true;
  }catch(e){return false;}
}

async function api(path,opt,allowRefresh){
  const result=await rawApi(path,opt);
  if(result.response.status===401 && allowRefresh!==false){
    const renewed=await refreshSession();
    if(renewed) return api(path,opt,false);
    localStorage.removeItem(ACCESS_KEY);localStorage.removeItem(REFRESH_KEY);
  }
  if(!result.response.ok){
    const detail=result.data?.detail || result.data?.error?.message || result.data?.message || "Request failed.";
    throw new Error(typeof detail==="string"?detail:"Request failed.");
  }
  return result.data;
}

function shell(title,subtitle,body){
  const path=currentPath();
  const nav=[
    ["/home","⌂","Home"],["/chat","◉","Chat"],["/history","◷","History"],
    ["/spider","✦","My Spider"],["/saved","♡","Saved"],["/themes","◈","Themes"],["/settings","⚙","Settings"]
  ];
  return '<div class="app-shell"><aside class="sidebar '+(state.menu?"open":"")+'"><div class="sidebar-brand" onclick="go(\\'/home\\')">'+logoLockup()+'</div>'+
    '<div class="side-section-label">WORKSPACE</div><nav class="nav">'+nav.map(function(n){
      return '<button class="nav-item '+(path===n[0] || (n[0]==="/spider"&&path.indexOf("/spider")===0)?"active":"")+'" onclick="go(\\''+n[0]+'\\')"><span class="nav-icon">'+n[1]+'</span><span>'+n[2]+'</span></button>';
    }).join("")+'</nav>'+
    '<div class="side-bottom"><div class="side-upgrade"><span>PRO / PLUS</span><b>Unlock more Spider.</b><button onclick="go(\\'/pricing\\')">View plans →</button></div>'+
    '<button class="profile-mini" onclick="go(\\'/profile\\')"><span class="avatar-sm">'+esc(initials(state.user?.display_name||state.user?.name))+'</span><span><b>'+esc(state.user?.display_name||"Your profile")+'</b><small>'+esc(planFor(planCode()).name)+'</small></span><span class="dots">•••</span></button></div></aside>'+
    '<div class="mobile-overlay '+(state.menu?"show":"")+'" onclick="closeMenu()"></div><main class="main"><header class="topbar"><button class="mobile-menu" onclick="openMenu()">☰</button><div><div class="page-kicker">SPIDERGPT</div><h1>'+esc(title)+'</h1><p>'+esc(subtitle||"")+'</p></div><button class="top-avatar" onclick="go(\\'/profile\\')">'+esc(initials(state.user?.display_name||state.user?.name))+'</button></header><div class="page-content">'+body+'</div></main>'+
    (state.toast?'<div class="toast '+esc(state.toast.type)+'">'+esc(state.toast.message)+'</div>':"")+'</div>';
}

function authBackground(content,extra){return '<div class="auth-page"><div class="auth-bg"></div><div class="auth-top">'+wordmark()+'</div><div class="auth-center '+(extra||"")+'">'+content+'</div></div>';}
function pageSplash(){return '<div class="splash-page"><div class="splash-bg"></div><div class="splash-content"><div class="splash-logo">'+logoLockup()+'</div><p>Your AI Sidekick.</p><div class="loading-line"><span></span></div></div></div>';}
function pageWelcome(){return authBackground('<div class="auth-card welcome-card"><div class="auth-mark">'+appIcon()+'</div><div class="eyebrow">YOUR AI SIDEKICK</div><h1>Meet SpiderGPT.</h1><p class="auth-copy">Think faster. Create more. Research deeper. Your personal Spider is ready when you are.</p><button class="google-btn" onclick="googleLogin()"><span class="google-g">G</span><span>Continue with Google</span></button><div class="auth-note">Google sign-in · Secure Supabase Auth</div></div>',"welcome");}
function pageProfileSetup(){
  return authBackground('<div class="auth-card form-card"><div class="step">01 <span>/ 02</span></div><h1>Let’s get to know you.</h1><p class="auth-copy">A few details help your Spider feel personal.</p><label>NAME<input id="pname" class="input" autocomplete="name" value="'+esc(state.user?.display_name||state.user?.name||"")+'" placeholder="What should we call you?"></label><label>AGE<input id="page" class="input" type="number" min="13" max="120" value="'+esc(state.user?.age||"")+'" placeholder="18"></label><button class="primary wide" onclick="saveProfile()">Continue <span>→</span></button></div>',"form");
}
function pageCreateSpider(){
  return authBackground('<div class="auth-card spider-create-card"><div class="step">02 <span>/ 02</span></div><div class="create-preview">'+spider()+'</div><h1>Create your Spider.</h1><p class="auth-copy">Name your sidekick and choose its starting energy.</p><input id="sname" class="input" value="'+esc(state.spider?.name||"Nova")+'" maxlength="64" placeholder="Spider name"><div class="mode-grid compact">'+ALL_MODES.map(function(m){
    const locked=!canUseMode(m.id);
    return '<button class="mode-card '+(state.mode===m.id?"selected ":"")+(locked?"locked":"")+'" data-mode="'+m.id+'" onclick="selectCreateMode(\\''+m.id+'\\')"><span style="color:'+m.color+'">'+m.icon+'</span><b>'+m.id+'</b><small>'+esc(locked?"Upgrade to unlock":m.desc)+'</small></button>';
  }).join("")+'</div><button class="primary wide" onclick="createSpider()">Bring Spider to life <span>→</span></button></div>',"form");
}
function pageHome(){
  const p=planFor(planCode()), name=state.spider?.name||"Spider", remaining=state.usage?.responses_remaining;
  return shell("Good to see you, "+name+".","Your sidekick is ready.",
    '<section class="dashboard-hero"><div class="hero-copy"><div class="eyebrow">YOUR AI SIDEKICK</div><h2>What are we doing today?</h2><p>Ask, create, research, roast, or just talk. SpiderGPT adapts to you.</p><div class="hero-actions"><button class="primary" onclick="go(\\'/chat\\')">Start chatting <span>→</span></button><button class="ghost" onclick="go(\\'/personality\\')">Choose a mode</button></div></div><div class="hero-art">'+spider()+'<span class="hero-ring"></span></div></section>'+
    '<div class="section-head"><div><h3>Quick actions</h3><p>Jump straight into your next move.</p></div></div><div class="quick-grid"><button onclick="newConversation()"><span class="quick-icon blue">◉</span><b>New chat</b><small>Start fresh with Spider.</small><i>→</i></button><button onclick="go(\\'/personality\\')"><span class="quick-icon purple">◈</span><b>Switch personality</b><small>Change Spider’s energy.</small><i>→</i></button><button onclick="go(\\'/spider/customize\\')"><span class="quick-icon red">✦</span><b>Customize Spider</b><small>Make your sidekick yours.</small><i>→</i></button></div>'+
    '<div class="section-head"><div><h3>Your plan</h3><p>Current limits and access.</p></div><button class="link-btn" onclick="go(\\'/pricing\\')">Compare plans →</button></div><div class="plan-strip"><div><span class="plan-badge">'+p.name+'</span><strong>'+esc(remaining===-1?"Unlimited":String(remaining??0))+'</strong><small>responses remaining</small></div><div><strong>'+p.modes+'/6</strong><small>modes available</small></div><div><strong>'+esc(state.usage?.responses_used??0)+'</strong><small>used today</small></div></div>');
}
function pageChat(){
  const mode=ALL_MODES.find(function(m){return m.id===state.mode;})||ALL_MODES[0];
  return shell("Chat","Talk to your Spider.",
    '<div class="chat-page"><div class="chat-mode-bar">'+ALL_MODES.map(function(m){
      const locked=!canUseMode(m.id);
      return '<button class="'+(state.mode===m.id?"active ":"")+(locked?"locked":"")+'" style="--mode:'+m.color+'" onclick="setMode(\\''+m.id+'\\')"><span>'+m.icon+'</span>'+m.id+(locked?" 🔒":"")+'</button>';
    }).join("")+'</div><div class="chat-window"><div class="chat-toolbar"><span>Mode: <b style="color:'+mode.color+'">'+mode.id+'</b></span><span>'+esc(state.conversationId?"Conversation active":"New conversation")+'</span></div><div class="chat-messages" id="chatMessages">'+renderMessages()+'</div><form class="composer" onsubmit="sendChat(event)"><input id="chatInput" autocomplete="off" placeholder="Message SpiderGPT…"><button class="send">↑</button></form></div></div>');
}
function renderMessages(){
  if(!state.messages.length) return '<div class="chat-empty"><div class="chat-empty-art">'+spider()+'</div><h2>What’s on your mind?</h2><p>Ask me anything. I’m listening.</p><div class="suggestions"><button onclick="usePrompt(\\'Explain something to me simply.\\')">Explain something</button><button onclick="usePrompt(\\'Help me plan my day.\\')">Plan my day</button><button onclick="usePrompt(\\'Give me a creative idea.\\')">Get creative</button></div></div>';
  return state.messages.map(function(m){
    const saveButton=m.role==="assistant"&&m.id?'<button class="link-btn save-message" onclick="saveMessage(\\''+m.id+'\\')">♡ Save</button>':"";
    return '<div class="message-row '+esc(m.role)+'"><div class="message-avatar">'+(m.role==="user"?esc(initials(state.user?.display_name||state.user?.name)):spider())+'</div><div><div class="message-bubble">'+esc(m.content)+'</div>'+saveButton+'</div></div>';
  }).join("");
}
function pagePersonality(){
  const current=ALL_MODES.find(function(x){return x.id===state.mode;})||ALL_MODES[0];
  return shell("Personality","Choose how Spider talks and thinks.",'<div class="personality-layout"><div class="personality-intro card-dark"><div class="eyebrow">CURRENT MODE</div><div class="big-mode" style="--mode:'+current.color+'">'+current.icon+'</div><h2>'+current.id+'</h2><p>'+current.desc+'</p></div><div class="mode-list">'+ALL_MODES.map(function(m){const locked=!canUseMode(m.id);return '<button class="mode-list-item '+(state.mode===m.id?"selected ":"")+(locked?"locked":"")+'" onclick="setMode(\\''+m.id+'\\')"><span class="mode-dot" style="--mode:'+m.color+'">'+m.icon+'</span><span><b>'+m.id+(locked?" 🔒":"")+'</b><small>'+esc(locked?"Available on a higher plan":m.desc)+'</small></span><span class="check">'+(state.mode===m.id?"✓":"")+'</span></button>';}).join("")+'</div></div>');
}
function pageHistory(){
  const rows=state.conversations.length?state.conversations.map(function(c){return '<button class="history-item" onclick="openConversation(\\''+c.id+'\\')"><span class="history-icon">◉</span><span><b>'+esc(c.title)+'</b><small>'+esc(c.last_message||"No messages yet")+'</small></span><em>'+esc(new Date(c.updated_at).toLocaleDateString())+'</em></button>';}).join(""):'<div class="empty-state">'+spider()+'<h3>No conversations yet</h3><p>Your future chats will appear here.</p><button class="primary" onclick="newConversation()">Start a chat</button></div>';
  return shell("Chat history","Pick up where you left off.",'<div class="toolbar"><div class="searchbox">⌕<input id="historySearch" oninput="filterHistory()" placeholder="Search conversations"></div><button class="ghost" onclick="newConversation()">New chat</button></div><div class="history-list" id="historyList">'+rows+'</div>');
}
function pageProfile(){
  return shell("Profile","Your account and Spider identity.",'<div class="profile-grid"><div class="profile-card card-dark"><div class="profile-avatar">'+esc(initials(state.user?.display_name||state.user?.name))+'</div><div><div class="eyebrow">ACCOUNT</div><h2>'+esc(state.user?.display_name||state.user?.name||"Your profile")+'</h2><p class="muted">'+esc(state.user?.email||"Google account")+'</p><p class="muted">Age: '+esc(state.user?.age||"Not set")+'</p></div><button class="ghost" onclick="go(\\'/profile-setup\\')">Edit profile</button></div><div class="info-grid"><div class="info-card"><span>Spider</span><b>'+esc(state.spider?.name||"Not created")+'</b><button onclick="go(\\'/spider\\')">Open →</button></div><div class="info-card"><span>Plan</span><b>'+planFor(planCode()).name+'</b><button onclick="go(\\'/billing\\')">Manage →</button></div></div></div>');
}
function pageSpider(){
  return shell("My Spider","Your companion, your rules.",'<div class="spider-profile card-dark"><div class="spider-large">'+spider()+'</div><div><div class="eyebrow">YOUR SPIDER</div><h2>'+esc(state.spider?.name||"Nova")+'</h2><p class="muted">Mode: '+esc(state.mode)+'</p><div class="tag-row"><span>Personal AI</span><span>Adaptive</span><span>Private</span></div><div class="hero-actions"><button class="primary" onclick="go(\\'/spider/customize\\')">Customize Spider</button><button class="ghost" onclick="go(\\'/share\\')">Share preview</button></div></div></div>');
}
function pageSettings(){
  return shell("Settings","Control your account and app experience.",'<div class="settings-list"><div class="setting-group"><div class="setting-title">ACCOUNT</div><button class="setting-row" onclick="go(\\'/profile\\')"><span><b>Profile</b><small>Name, age and account identity.</small></span><span>→</span></button><button class="setting-row" onclick="go(\\'/billing\\')"><span><b>Billing & subscription</b><small>Plans, payments and cancellation.</small></span><span>→</span></button></div><div class="setting-group"><div class="setting-title">APP</div><button class="setting-row" onclick="go(\\'/themes\\')"><span><b>Theme</b><small>Choose the visual mood.</small></span><span>→</span></button><button class="setting-row" onclick="go(\\'/usage\\')"><span><b>Usage</b><small>See your daily limits.</small></span><span>→</span></button></div><div class="setting-group"><div class="setting-title">SESSION</div><button class="setting-row danger" onclick="logout()"><span><b>Sign out</b><small>End this session on this device.</small></span><span>↗</span></button></div></div>');
}
function pageCustomize(){
  const limits=state.usage?.monthly_customization_limits||{};
  const presets=[["preset_classic","Classic"],["preset_crimson","Crimson"],["preset_midnight","Midnight"],["preset_neon","Neon"]];
  return shell("Spider customization","Shape your sidekick within your plan.",'<div class="customize-layout"><div class="custom-preview card-dark"><div class="custom-spider">'+spider()+'</div><h2>'+esc(state.spider?.name||"Nova")+'</h2><p class="muted">Preview · '+esc(state.spider?.appearance_id||"preset_classic")+'</p></div><div class="custom-form card-dark"><div class="eyebrow">IDENTITY</div><label>SPIDER NAME<input id="newSpiderName" class="input" value="'+esc(state.spider?.name||"Nova")+'" maxlength="64"></label><button class="primary wide" onclick="saveSpiderName()">Save name</button><div class="eyebrow">APPEARANCE</div><div class="appearance-grid">'+presets.map(function(p){return '<button class="appearance '+(state.spider?.appearance_id===p[0]?"active":"")+'" onclick="saveAppearance(\\''+p[0]+'\\')">'+p[1]+'</button>';}).join("")+'</div><p class="form-hint">Name changes remaining: '+esc(limits.name_changes_remaining??"—")+' · Appearance changes remaining: '+esc(limits.appearance_changes_remaining??"—")+'</p></div></div>');
}
function pageThemes(){
  const themes=[["Obsidian","Deep black + red glow"],["Crimson Web","Red-lit web atmosphere"],["Midnight","Low-light blue-black mood"],["Minimal","Clean dark surfaces"]];
  const active=localStorage.getItem(THEME_KEY)||"0";
  return shell("Themes","Make SpiderGPT feel like yours.",'<div class="theme-grid">'+themes.map(function(t,i){return '<button class="theme-card '+(String(i)===active?"selected":"")+'" onclick="selectTheme('+i+')"><span class="theme-preview theme-'+i+'"></span><b>'+t[0]+'</b><small>'+t[1]+'</small><span class="theme-check">'+(String(i)===active?"✓":"")+'</span></button>';}).join("")+'</div>');
}
function pageSaved(){
  const body=state.saved.length?state.saved.map(function(s){return '<div class="history-item"><span class="history-icon">♡</span><span><b>'+esc(s.message_role||"Saved answer")+'</b><small>'+esc(s.message_content||"")+'</small></span><button class="link-btn" onclick="deleteSaved(\\''+s.id+'\\')">Remove</button></div>';}).join(""):'<div class="empty-state"><div class="empty-heart">♡</div><h3>Nothing saved yet.</h3><p>Save useful answers and ideas from your chats to find them here.</p><button class="primary" onclick="go(\\'/chat\\')">Go to chat</button></div>';
  return shell("Saved","Your favorite Spider moments.",'<div class="history-list">'+body+'</div>');
}
function pageShare(){
  return shell("Share preview","Preview your Spider identity before sharing.",'<div class="share-layout"><div class="share-card-preview"><div class="share-glow"></div><div class="share-brand">'+wordmark()+'</div><div class="share-spider">'+spider()+'</div><h2>'+esc(state.spider?.name||"Nova")+'</h2><p>Your AI Sidekick.</p><span class="share-mode">'+esc(state.mode)+' mode</span></div><div class="share-controls card-dark"><div class="eyebrow">PREVIEW</div><h2>Ready to share.</h2><p class="muted">This copies a preview URL for this SpiderGPT app. A public profile URL requires a dedicated sharing backend endpoint.</p><button class="primary wide" onclick="sharePreview()">Share preview</button></div></div>');
}
function pageUsage(){
  const used=Number(state.usage?.responses_used||0), limit=Number(state.usage?.daily_response_limit);
  const unlimited=limit===-1, label=unlimited?"Unlimited":String(limit), pct=unlimited?0:Math.min(100,used/Math.max(1,limit)*100);
  return shell("Usage","Know where you stand today.",'<div class="usage-hero card-dark"><div><div class="eyebrow">AI RESPONSES TODAY</div><h2>'+used+' <span>/ '+label+'</span></h2><p class="muted">'+(unlimited?"Unlimited daily responses on Plus.":Math.max(0,limit-used)+" responses remaining today.")+'</p></div><div class="progress-ring" style="--pct:'+pct+'%"><span>'+Math.round(pct)+'%</span></div></div><div class="usage-grid"><div class="usage-card"><span>Plan</span><b>'+planFor(planCode()).name+'</b></div><div class="usage-card"><span>Modes</span><b>'+allowedModes().length+' / 6</b></div><div class="usage-card"><span>Images today</span><b>'+esc(state.usage?.images_used??0)+' / '+esc(state.usage?.daily_image_limit??0)+'</b></div></div><button class="primary" onclick="go(\\'/pricing\\')">See plans →</button>');
}
function pagePricing(){
  const data=state.plans.length?state.plans:DEFAULT_PLANS;
  const entries=Array.isArray(data)?data.map(function(p){return [p.code,{name:p.name,price:p.monthly_price_inr?("₹"+p.monthly_price_inr+"/mo"):"Free",responses:p.daily_response_limit===-1?"Unlimited":p.daily_response_limit+"/day",modes:(p.allowed_modes||[]).length,features:[(p.daily_response_limit===-1?"Unlimited":p.daily_response_limit)+" AI responses / day",(p.allowed_modes||[]).length+" of 6 modes",p.custom_appearance_allowed?"Full Spider customization":"Limited Spider customization"]}];}):Object.entries(data);
  return shell("Plans","Choose how your Spider grows with you.",'<div class="pricing-intro"><div><div class="eyebrow">SIMPLE PLANS</div><h2>More Spider. More freedom.</h2><p class="muted">Upgrade when you need more messages, modes and customization.</p></div></div><div class="plans-grid">'+entries.map(function(pair){const code=pair[0],p=pair[1];return '<article class="pricing-card '+(code==="PRO"?"featured":"")+'"><div class="pricing-top"><span class="plan-badge">'+esc(p.name)+'</span>'+(code==="PRO"?'<span class="popular">POPULAR</span>':"")+'</div><div class="price">'+esc(p.price)+'</div><div class="price-note">'+(code==="FREE"?"No payment required":"Monthly subscription")+'</div><div class="feature-list">'+p.features.map(function(f){return '<span>✓ '+esc(f)+'</span>';}).join("")+'</div><button class="'+(code==="FREE"?"ghost":"primary")+' wide" onclick="'+(code==="FREE"?"go(\\'/home\\')":"go(\\'/checkout/"+code+"\\')")+'">'+(code==="FREE"?"Current plan":"Choose "+esc(p.name))+'</button></article>';}).join("")+'</div>');
}
function pageCheckout(plan){
  const p=planFor(plan);
  return shell("Checkout","Secure recurring subscription.",'<div class="checkout-layout"><div class="checkout-summary card-dark"><div class="eyebrow">YOU’RE CHOOSING</div><h2>'+p.name+'</h2><div class="checkout-price">'+p.price+'</div><div class="feature-list">'+p.features.map(function(f){return '<span>✓ '+esc(f)+'</span>';}).join("")+'</div></div><div class="payment-card card-dark"><div class="secure-pill">⌁ SECURE PAYMENT</div><h3>Continue to payment</h3><p class="muted">Choose monthly or yearly and continue to the configured provider checkout.</p><label>Billing period<select id="billingPeriod" class="input"><option value="monthly">Monthly</option><option value="yearly">Yearly</option></select></label><button class="primary wide" onclick="startCheckout(\\''+plan+'\\')">Continue securely <span>→</span></button><button class="link-btn wide" onclick="go(\\'/pricing\\')">Back to plans</button></div></div>');
}
function pageSuccess(){return shell("Payment success","Your subscription is being confirmed.",'<div class="success-card card-dark"><div class="success-icon">✓</div><h2>Welcome to your new plan.</h2><p class="muted">Provider confirmation and webhook processing determine the final subscription state.</p><button class="primary" onclick="refreshAccountAndGoHome()">Back home</button></div>');}
function pageBilling(){
  const s=state.subscription, p=planFor(planCode());
  if(!s) return shell("Billing & subscription","Manage your current subscription.",'<div class="empty-state">'+spider()+'<h3>Free plan</h3><p>No paid subscription is active.</p><button class="primary" onclick="go(\\'/pricing\\')">Compare plans</button></div>');
  return shell("Billing & subscription","Manage your current subscription.",'<div class="billing-card card-dark"><div><div class="eyebrow">CURRENT PLAN</div><h2>'+esc(s.plan_name||p.name)+'</h2><p class="muted">'+esc(s.billing_period)+' · '+esc(s.currency)+' · '+esc(s.status)+'</p></div><span class="status-pill">'+esc(s.cancel_at_period_end?"CANCELS AT PERIOD END":"ACTIVE")+'</span></div><div class="billing-actions"><button class="info-card" onclick="go(\\'/pricing\\')"><span>Change plan</span><b>Compare plans →</b></button><button class="info-card" onclick="cancelSubscription(false)"><span>Subscription</span><b>Cancel at period end →</b></button></div>');
}

async function googleLogin(){
  if(!SUPABASE_CLIENT){toast("Configure the frontend public Supabase URL and anon key.","error");return;}
  const result=await SUPABASE_CLIENT.auth.signInWithOAuth({provider:"google",options:{redirectTo:location.origin+location.pathname}});
  if(result.error) toast(result.error.message,"error");
}
async function syncSession(){
  if(!SUPABASE_CLIENT) return;
  const session=await SUPABASE_CLIENT.auth.getSession();
  const supabaseToken=session.data?.session?.access_token;
  if(!supabaseToken) return;
  try{
    const result=await api("/auth/google",{method:"POST",body:JSON.stringify({access_token:supabaseToken})},false);
    localStorage.setItem(ACCESS_KEY,result.access_token);
    localStorage.setItem(REFRESH_KEY,result.refresh_token);
  }catch(e){console.error(e);}
}
async function loadAccount(){
  if(!isAuthed()) return;
  const values=await Promise.all([
    api("/auth/me"),api("/profile/me"),api("/usage"),api("/spider/me"),
    api("/subscriptions/me").catch(function(){return null;}),api("/subscriptions/plans").catch(function(){return []})
  ]);
  state.user=values[0]||values[1]; state.usage=values[2]; state.spider=normalizeSpider(values[3]); state.subscription=values[4]; state.plans=values[5]||[];
  if(state.spider?.personality_mode && canUseMode(state.spider.personality_mode)) state.mode=state.spider.personality_mode;
  if(!canUseMode(state.mode)) state.mode=allowedModes()[0]||"Brain";
  localStorage.setItem(MODE_KEY,state.mode);
}
async function loadHistory(){
  state.conversations=await api("/conversations");
}
async function loadSaved(){
  state.saved=await api("/saved");
}
async function loadConversation(id){
  const detail=await api("/conversations/"+encodeURIComponent(id));
  state.conversationId=detail.id;state.messages=(detail.messages||[]).map(normalizeMessage);
}
async function saveProfile(){
  const name=document.querySelector("#pname")?.value.trim(), age=Number(document.querySelector("#page")?.value);
  if(!name||!age||age<13||age>120){toast("Please enter a valid name and age (13–120).","error");return;}
  try{state.user=await api("/profile/me",{method:"PUT",body:JSON.stringify({display_name:name,age:age})});go(state.spider?"/home":"/create-spider");}
  catch(e){toast(e.message,"error");}
}
function selectCreateMode(id){if(!canUseMode(id)){toast("That mode is not available on your current plan.","error");go("/pricing");return;}state.mode=id;localStorage.setItem(MODE_KEY,id);render();}
async function createSpider(){
  const name=document.querySelector("#sname")?.value.trim()||"Nova";
  if(!canUseMode(state.mode)){toast("Choose an available mode.","error");return;}
  try{state.spider=normalizeSpider(await api("/spider",{method:"POST",body:JSON.stringify({spider_name:name,personality_mode:state.mode,appearance_id:"preset_classic",custom_appearance_data:{}})}));state.usage=await api("/usage");go("/home");}
  catch(e){toast(e.message,"error");}
}
async function setMode(id){
  if(!canUseMode(id)){toast("That mode is not available on your current plan.","error");go("/pricing");return;}
  state.mode=id;localStorage.setItem(MODE_KEY,id);
  try{if(state.spider) state.spider=normalizeSpider(await api("/spider/personality",{method:"PATCH",body:JSON.stringify({personality_mode:id})}));}
  catch(e){toast(e.message,"error");return;}
  render();
}
function usePrompt(value){const input=document.querySelector("#chatInput");if(input){input.value=value;input.focus();}}
function newConversation(){state.conversationId=null;state.messages=[];go("/chat");}
async function sendChat(event){
  event.preventDefault();
  const input=document.querySelector("#chatInput"), message=input?.value.trim();
  if(!message||state.loading)return;
  if(!canUseMode(state.mode)){toast("That mode is not available on your current plan.","error");return;}
  state.loading=true; input.value=""; state.messages.push({role:"user",content:message});
  render();
  try{
    const result=await api("/chat",{method:"POST",body:JSON.stringify({conversation_id:state.conversationId,message:message,mode:state.mode,stream:false,web_search:false})});
    state.conversationId=result.conversation_id;
    state.messages=state.messages.concat([normalizeMessage(result.message)]);
    state.usage=await api("/usage");
  }catch(e){
    state.messages.pop();toast(e.message,"error");
  }finally{state.loading=false;render();}
}
async function openConversation(id){try{await loadConversation(id);go("/chat");}catch(e){toast(e.message,"error");}}
async function saveMessage(messageId){
  if(!state.conversationId){toast("Open the conversation first.","error");return;}
  try{await api("/saved",{method:"POST",body:JSON.stringify({message_id:messageId,conversation_id:state.conversationId})});toast("Saved.","success");}
  catch(e){toast(e.message,"error");}
}
async function deleteSaved(id){try{await api("/saved/"+encodeURIComponent(id),{method:"DELETE"});await loadSaved();render();}catch(e){toast(e.message,"error");}}
async function saveSpiderName(){
  const name=document.querySelector("#newSpiderName")?.value.trim();if(!name)return;
  try{state.spider=normalizeSpider(await api("/spider/name",{method:"PATCH",body:JSON.stringify({spider_name:name})}));state.usage=await api("/usage");toast("Spider name updated.","success");render();}
  catch(e){toast(e.message,"error");}
}
async function saveAppearance(id){
  try{state.spider=normalizeSpider(await api("/spider/appearance",{method:"PATCH",body:JSON.stringify({appearance_type:"PRESET",appearance_id:id,custom_appearance_data:{}})}));state.usage=await api("/usage");toast("Spider appearance updated.","success");render();}
  catch(e){toast(e.message,"error");}
}
function selectTheme(index){localStorage.setItem(THEME_KEY,String(index));applyTheme();toast("Theme selected.","success");}
function applyTheme(){document.documentElement.dataset.theme=localStorage.getItem(THEME_KEY)||"0";}
async function startCheckout(plan){
  const period=document.querySelector("#billingPeriod")?.value||"monthly";
  try{
    const result=await api("/payments/checkout",{method:"POST",body:JSON.stringify({plan_code:plan,billing_period:period,currency:"INR"})});
    if(result.checkout_url){location.href=result.checkout_url;return;}
    if(result.provider==="razorpay" && window.Razorpay){
      const options={
        key:result.key_id,
        subscription_id:result.provider_subscription_id||result.order_id,
        name:"SpiderGPT",
        description:"SpiderGPT "+plan+" subscription",
        prefill:{name:state.user?.display_name||state.user?.name||"",email:state.user?.email||""},
        theme:{color:"#FF3B30"},
        handler:async function(response){
          try{
            const verification=await api("/payments/verify",{method:"POST",body:JSON.stringify({
              provider:"razorpay",
              order_id:result.order_id,
              payment_id:response.razorpay_payment_id,
              signature:response.razorpay_signature
            })});
            if(verification.success){go("/payment-success");await loadAccount();render();}
            else toast("Payment could not be verified.","error");
          }catch(e){toast(e.message,"error");}
        }
      };
      const checkout=new window.Razorpay(options);
      checkout.on("payment.failed",function(){toast("Payment failed or was cancelled.","error");});
      checkout.open();
      return;
    }
    toast("Payment provider did not return a usable checkout session.","error");
  }catch(e){toast(e.message,"error");}
}
async function cancelSubscription(immediate){
  if(!confirm(immediate?"Cancel the subscription immediately?":"Cancel the subscription at the end of the current billing period?"))return;
  try{await api("/subscriptions/cancel",{method:"POST",body:JSON.stringify({cancel_immediately:!!immediate})});state.subscription=await api("/subscriptions/me");toast("Subscription cancellation updated.","success");render();}
  catch(e){toast(e.message,"error");}
}
async function sharePreview(){
  const url=location.origin+location.pathname+"#share";
  if(navigator.share){try{await navigator.share({title:"My SpiderGPT",text:"Meet my SpiderGPT sidekick.",url:url});return;}catch(e){}}
  try{await navigator.clipboard.writeText(url);toast("Preview link copied.","success");}catch(e){toast("Copy failed. Use your browser share menu.","error");}
}
async function refreshAccountAndGoHome(){try{await loadAccount();go("/home");}catch(e){go("/home");}}
function filterHistory(){
  const q=(document.querySelector("#historySearch")?.value||"").toLowerCase();
  document.querySelectorAll("#historyList .history-item").forEach(function(el){el.style.display=el.textContent.toLowerCase().includes(q)?"":"none";});
}
async function logout(){
  try{await api("/auth/logout",{method:"POST"},false);}catch(e){}
  try{if(SUPABASE_CLIENT)await SUPABASE_CLIENT.auth.signOut();}catch(e){}
  localStorage.removeItem(ACCESS_KEY);localStorage.removeItem(REFRESH_KEY);state.user=null;state.spider=null;state.usage=null;state.subscription=null;state.messages=[];state.conversations=[];state.saved=[];state.conversationId=null;go("/welcome");
}
function openMenu(){state.menu=true;render();}
function closeMenu(){state.menu=false;render();}

async function route(){
  const p=currentPath();
  if(p==="/") return pageSplash();
  if(p==="/welcome") return pageWelcome();
  if(!isAuthed()) return pageWelcome();
  if(p==="/profile-setup") return pageProfileSetup();
  if(p==="/create-spider") return pageCreateSpider();
  if(p==="/home") return pageHome();
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
  if(p==="/usage") return pageUsage();
  if(p==="/pricing") return pagePricing();
  if(p==="/payment-success") return pageSuccess();
  if(p==="/billing") return pageBilling();
  if(p.indexOf("/checkout/")===0) return pageCheckout(p.split("/")[2]?.toUpperCase()||"PRO");
  return pageHome();
}

let rendering=false;
async function render(){
  if(rendering)return;
  rendering=true;
  try{
    const root=document.querySelector("#app");
    if(!root)return;
    const p=currentPath();
    if(p==="/"){root.innerHTML=pageSplash();window.clearTimeout(render.splash);render.splash=window.setTimeout(function(){go(isAuthed()?"/home":"/welcome");},900);return;}
    root.innerHTML=await route();
    window.scrollTo(0,0);
  }catch(e){console.error(e);document.querySelector("#app").innerHTML=authBackground('<div class="auth-card"><h1>Something went wrong.</h1><p class="auth-copy">'+esc(e.message||"Please try again.")+'</p><button class="primary wide" onclick="location.reload()">Reload</button></div>');}
  finally{rendering=false;}
}

async function bootstrap(){
  applyTheme();
  await syncSession();
  if(isAuthed()){
    try{
      await loadAccount();
      if(!state.user?.onboarding_completed){go("/profile-setup");}
      else if(!state.spider){go("/create-spider");}
      else if(currentPath()==="/"||currentPath()==="/welcome"){go("/home");}
    }catch(e){
      console.error(e);
      localStorage.removeItem(ACCESS_KEY);localStorage.removeItem(REFRESH_KEY);
      if(currentPath()!=="/welcome")go("/welcome");
    }
  }else if(currentPath()!=="/") go("/welcome");
  await render();
}
window.addEventListener("hashchange",async function(){
  const p=currentPath();
  if(p==="/history"&&isAuthed())try{await loadHistory();}catch(e){}
  if(p==="/saved"&&isAuthed())try{await loadSaved();}catch(e){}
  render();
});
window.addEventListener("DOMContentLoaded",bootstrap);
if(document.readyState!=="loading")bootstrap();
