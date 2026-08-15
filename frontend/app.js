let readings=[],timer=null,running=false,sessionId=null;
const $=x=>document.getElementById(x),canvas=$("chart"),ctx=canvas.getContext("2d");
function sim(){let r=Math.random();if(r<.12)return 45+Math.floor(Math.random()*14);if(r>.88)return 103+Math.floor(Math.random()*17);return 65+Math.floor(Math.random()*28)}
async function loadMe(){let d=await(await fetch("/api/auth/me")).json();if(!d.authenticated){location="/login";return}$("welcome").textContent="Welcome, "+d.user.name;$("uname").textContent=d.user.name;$("urole").textContent=d.user.role==="USER"?"Personal account":"Account"}
async function startSession(){if("Notification" in window && Notification.permission==="default"){try{await Notification.requestPermission()}catch(e){}}let d=await(await fetch("/api/session/start",{method:"POST"})).json();if(!d.session_id)return;sessionId=d.session_id;running=true;$("session").textContent="Active · "+sessionId;$("start").disabled=true;$("stop").disabled=false;add(sim());timer=setInterval(()=>add(sim()),2000)}
async function endSession(){running=false;clearInterval(timer);timer=null;if(sessionId)await fetch("/api/session/end",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:sessionId})});$("start").disabled=false;$("stop").disabled=true;$("session").textContent="Session ended"}
async function add(v){v=Math.round(v);readings.push(v);if(readings.length>60)readings.shift();$("bpm").innerHTML=v+' <i>BPM</i>';let avg=readings.reduce((a,b)=>a+b,0)/readings.length;$("avg").textContent=Math.round(avg);$("min").textContent=Math.min(...readings);$("max").textContent=Math.max(...readings);$("count").textContent=readings.length;$("gauge").style.width=Math.max(0,Math.min(100,(v-40)/85*100))+"%";draw();await predict()}
async function predict(){
  let r=await fetch("/api/predict",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({history:readings,session_id:sessionId})});
  let d=await r.json(); if(!r.ok)return;
  $("ai").textContent=d.ai_status==="NORMAL"?"Normal pattern":"Confirmed unusual pattern";
  $("risk").textContent=d.risk_score+"/100"; $("riskbar").style.width=d.risk_score+"%";
  $("conf").textContent=Math.round(d.confidence*100)+"%"; $("confbar").style.width=Math.round(d.confidence*100)+"%";
  $("why").textContent=d.explanation;
  await loadAlerts();
  if(d.alert && "Notification" in window && Notification.permission==="granted"){
    new Notification("PulseGuard AI Alert",{body:`BPM ${Math.round(d.bpm)} · ${d.rule_status.replace("NORMAL","")} ${d.ai_status.replace("_"," ")}`});
  }
}
function draw(){let w=canvas.width,h=canvas.height,p={l:35,r:15,t:20,b:25};ctx.clearRect(0,0,w,h);let y=v=>p.t+(125-v)/85*(h-p.t-p.b),x=i=>readings.length<2?p.l:p.l+i/(readings.length-1)*(w-p.l-p.r);[60,80,100,120].forEach(v=>{ctx.strokeStyle="#e5e7eb";ctx.beginPath();ctx.moveTo(p.l,y(v));ctx.lineTo(w-p.r,y(v));ctx.stroke();ctx.fillStyle="#94a3b8";ctx.fillText(v,8,y(v)+4)});if(!readings.length){ctx.fillStyle="#94a3b8";ctx.textAlign="center";ctx.fillText("Start monitoring to visualize your trend",w/2,h/2);ctx.textAlign="left";return}ctx.strokeStyle="#2563eb";ctx.lineWidth=3;ctx.beginPath();readings.forEach((v,i)=>i?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v)));ctx.stroke()}
async function metrics(){let d=await(await fetch("/api/metrics")).json();$("m1").textContent=Math.round(d.accuracy*100)+"%";$("m2").textContent=Math.round(d.precision*100)+"%";$("m3").textContent=Math.round(d.recall*100)+"%";$("m4").textContent=Math.round(d.f1*100)+"%"}

async function analyticsPage(){
  let d=await (await fetch("/api/analytics")).json();
  if(!d || d.error) return;
  $("an-total").textContent=d.total_readings;
  $("an-avg").textContent=d.avg_bpm==null?"--":d.avg_bpm;
  $("an-abnormal").textContent=d.abnormal_count;
  $("an-ai").textContent=d.ai_unusual_count;
  $("an-range").textContent=d.min_bpm==null?"--":`${Math.round(d.min_bpm)}–${Math.round(d.max_bpm)} BPM`;
  $("an-risk").textContent=d.avg_risk==null?"--":`${d.avg_risk}/100`;
  $("an-conf").textContent=d.avg_confidence==null?"--":`${Math.round(d.avg_confidence*100)}%`;
  $("an-stability").textContent=d.stability==null?"--":`${d.stability}%`;
  drawInsight(d.timeline||[]);
}
function drawInsight(data){
  let c=$("insightChart"); if(!c)return;
  let x=c.getContext("2d"),w=c.width,h=c.height;
  x.clearRect(0,0,w,h);
  x.fillStyle="#64748b"; x.font="12px Segoe UI";
  if(!data.length){x.textAlign="center";x.fillText("Start monitoring to build your analytics timeline.",w/2,h/2);x.textAlign="left";return}
  let pad={l:40,r:20,t:20,b:30};
  let min=40,max=125;
  let px=i=>pad.l+i/(Math.max(1,data.length-1))*(w-pad.l-pad.r);
  let py=v=>pad.t+(max-v)/(max-min)*(h-pad.t-pad.b);
  [60,80,100,120].forEach(v=>{x.strokeStyle="#e5e7eb";x.beginPath();x.moveTo(pad.l,py(v));x.lineTo(w-pad.r,py(v));x.stroke();x.fillStyle="#94a3b8";x.fillText(v,8,py(v)+4)});
  x.strokeStyle="#2563eb";x.lineWidth=3;x.beginPath();
  data.forEach((d,i)=>i?x.lineTo(px(i),py(d.bpm)):x.moveTo(px(i),py(d.bpm)));x.stroke();
  data.forEach((d,i)=>{if(d.rule!=="NORMAL"||d.ai!=="NORMAL"){x.fillStyle="#ef4444";x.beginPath();x.arc(px(i),py(d.bpm),5,0,Math.PI*2);x.fill()}});
}

async function loadAlerts(){try{let r=await fetch("/api/notifications",{cache:"no-store"});if(!r.ok)return;let items=await r.json();let unread=items.filter(x=>!x.read).length;$("badge").textContent=unread;let list=$("alertslist");if(!list)return;list.innerHTML=items.map(x=>`<div class="alertitem ${x.read?"read":"unread"}"><div class="alerttop"><span class="alertsev ${x.severity.toLowerCase()}">${x.severity}</span><span>${x.timestamp.replace("T"," ")}</span></div><h3>${x.title}</h3><p>${x.message}</p><div class="alertmeta"><b>${Number(x.bpm).toFixed(0)} BPM</b><span>Risk ${Math.round(x.risk)}/100</span>${x.read?"<span>✓ Read</span>":`<button onclick="markRead(${x.id})">Mark as read</button>`}</div></div>`).join("")||`<div class="emptyalert"><div class="emptyicon">✓</div><h3>No alerts yet</h3><p>Start monitoring and try <b>High · 110</b> or <b>Low · 55</b> to generate a demonstration alert.</p></div>`;}catch(e){console.error("Alert loading failed",e)}}
async function markRead(id){await fetch(`/api/notifications/${id}/read`,{method:"POST"});await loadAlerts()}
async function requestNotifications(){if("Notification" in window && Notification.permission==="default")await Notification.requestPermission()}

let liveTimer=null, liveData=[];
async function livePage(){
  await refreshLive();
  if(!liveTimer) liveTimer=setInterval(refreshLive,2500);
}
async function refreshLive(){
  try{
    let d=await (await fetch("/api/history")).json();
    if(!Array.isArray(d)) return;
    liveData=d.slice(-60).map(x=>({
      bpm:Number(x.bpm||0),
      rule:x.rule||"NORMAL",
      ai:x.ai||"NORMAL",
      confidence:Number(x.confidence||0),
      risk:Number(x.risk_score||0),
      timestamp:x.timestamp||""
    }));
    renderLive(liveData);
  }catch(e){}
}
function renderLive(data){
  let last=data[data.length-1];
  $("live-count").textContent=data.length;
  if(!last){
    $("live-bpm").textContent="--"; $("live-ai").textContent="--"; $("live-risk").textContent="--";
    $("live-state").textContent="Waiting for a session";
    return;
  }
  $("live-bpm").textContent=Math.round(last.bpm);
  $("live-state").textContent=last.rule==="NORMAL"?"Within demonstration range":"Threshold alert";
  $("live-ai").textContent=last.ai;
  $("live-confidence").textContent=`Model confidence ${Math.round(last.confidence*100)}%`;
  $("live-risk").textContent=Math.round(last.risk);
  $("live-rule").textContent=last.rule;
  $("live-ai2").textContent=last.ai;
  $("live-risk2").textContent=Math.round(last.risk)+"/100";
  $("live-title").textContent=last.ai==="NORMAL" && last.rule==="NORMAL"?"Pattern currently normal":"Attention required";
  $("live-explanation").textContent=`Latest reading: ${Math.round(last.bpm)} BPM. Rule=${last.rule}. AI=${last.ai}.`;
  $("live-session").textContent=`Latest event ${last.timestamp.replace("T"," ")}`;
  drawLiveChart(data);
  $("live-events").innerHTML=data.slice(-8).reverse().map(x=>`
    <div class="live-event ${x.rule!=="NORMAL"||x.ai!=="NORMAL"?"event-alert":""}">
      <b>${Math.round(x.bpm)} BPM</b><span>${x.rule}</span><span>${x.ai}</span><span>Risk ${Math.round(x.risk)}</span><small>${x.timestamp.replace("T"," ")}</small>
    </div>`).join("");
}
function drawLiveChart(data){
  let c=$("liveChart"); if(!c)return;
  let ctx=c.getContext("2d"),w=c.width,h=c.height;
  ctx.clearRect(0,0,w,h);
  let pad={l:42,r:18,t:18,b:30},min=40,max=125;
  const px=i=>pad.l+i/Math.max(1,data.length-1)*(w-pad.l-pad.r);
  const py=v=>pad.t+(max-v)/(max-min)*(h-pad.t-pad.b);
  ctx.font="12px Segoe UI";
  [60,80,100,120].forEach(v=>{
    ctx.strokeStyle="#e5e7eb";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(pad.l,py(v));ctx.lineTo(w-pad.r,py(v));ctx.stroke();
    ctx.fillStyle="#94a3b8";ctx.fillText(v,8,py(v)+4);
  });
  ctx.strokeStyle="#2563eb";ctx.lineWidth=3;ctx.beginPath();
  data.forEach((d,i)=>i?ctx.lineTo(px(i),py(d.bpm)):ctx.moveTo(px(i),py(d.bpm)));ctx.stroke();
  data.forEach((d,i)=>{
    if(d.rule!=="NORMAL"||d.ai!=="NORMAL"){
      ctx.fillStyle="#ef4444";ctx.beginPath();ctx.arc(px(i),py(d.bpm),5,0,Math.PI*2);ctx.fill();
    }
  });
}

async function history(){let d=await(await fetch("/api/history")).json();$("tbody").innerHTML=d.map(x=>`<tr><td>${x.timestamp.replace("T"," ")}</td><td><b>${x.bpm.toFixed(0)}</b></td><td>${x.rule}</td><td>${x.ai}</td><td>${Math.round(x.confidence*100)}%</td><td>${x.risk}</td><td>${x.explanation}</td></tr>`).join("")||"<tr><td colspan=7>No monitoring readings yet.</td></tr>"}
$("start").onclick=startSession;$("stop").onclick=endSession;$("bell").onclick=()=>{document.querySelector('nav button[data-page="alerts"]').click();loadAlerts()};$("readall").onclick=async()=>{await fetch("/api/notifications/read-all",{method:"POST"});await loadAlerts()};document.querySelectorAll(".demo button").forEach(b=>b.onclick=()=>add(+b.dataset.v));$("clear").onclick=()=>{readings=[];draw()};$("refresh").onclick=history;
$("logout").onclick=async()=>{await fetch("/api/auth/logout",{method:"POST"});location="/login"};
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll("nav button").forEach(x=>x.classList.remove("active"));b.classList.add("active");document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"));$(b.dataset.page).classList.add("active");if(b.dataset.page==="analytics")metrics();if(b.dataset.page==="history")history();if(b.dataset.page==="alerts")loadAlerts();if(b.dataset.page==="insights")analyticsPage();if(b.dataset.page==="live")livePage()});
$("tour").onclick=()=>$("modal").classList.add("show");$("close").onclick=$("gotit").onclick=()=>$("modal").classList.remove("show");
loadMe();metrics();loadAlerts();analyticsPage();draw();setInterval(loadAlerts,3000);