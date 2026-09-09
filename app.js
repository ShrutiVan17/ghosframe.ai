const $=id=>document.getElementById(id);
const savedApi=localStorage.getItem("ghostframe_api")||"";
const state={api:/trycloudflare\.com|ngrok/i.test(savedApi)?"":savedApi};
if(!state.api && savedApi){localStorage.removeItem("ghostframe_api");}

function cleanApi(v){return (v||"").trim().replace(/\/$/,"")}
function esc(v){return String(v||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}

$("connection").onclick=()=>{$("backendUrl").value=state.api;$("modal").classList.remove("hidden")};
$("closeModal").onclick=()=>$("modal").classList.add("hidden");
async function verifyBackend(url){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),8000);
  try{
    const r=await fetch(cleanApi(url)+"/health",{signal:controller.signal,cache:"no-store"});
    clearTimeout(timer);
    if(!r.ok)return false;
    const d=await r.json();
    return d && d.status==="ok";
  }catch(e){clearTimeout(timer);return false}
}

$("saveBackend").onclick=async()=>{
 const candidate=cleanApi($("backendUrl").value);
 if(!candidate){state.api="";localStorage.removeItem("ghostframe_api");$("connection").textContent="CONNECT CLOUD BACKEND";$("modal").classList.add("hidden");return}
 $("saveBackend").textContent="TESTING CONNECTION...";
 const ok=await verifyBackend(candidate);
 $("saveBackend").textContent="SAVE CONNECTION";
 if(!ok){alert("Backend is not reachable. Use your permanent Cloud Run URL, not an expired Cloudflare/ngrok URL.");return}
 state.api=candidate;
 localStorage.setItem("ghostframe_api",state.api);
 $("modal").classList.add("hidden");
 $("connection").textContent="BACKEND CONNECTED";
};
if(state.api)$("connection").textContent="BACKEND CONNECTED";

const canvas=$("particles"),ctx=canvas.getContext("2d");let dots=[];
function resize(){canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio;ctx.scale(devicePixelRatio,devicePixelRatio);dots=Array.from({length:Math.min(75,Math.floor(innerWidth/18))},()=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,v:.12+Math.random()*.25,r:.4+Math.random()*1.3}))}
function animate(){ctx.clearRect(0,0,innerWidth,innerHeight);ctx.fillStyle="rgba(167,139,250,.38)";dots.forEach(d=>{d.y-=d.v;if(d.y<0)d.y=innerHeight;ctx.beginPath();ctx.arc(d.x,d.y,d.r,0,Math.PI*2);ctx.fill()});requestAnimationFrame(animate)}
addEventListener("resize",resize);resize();animate();

function animateSteps(){
 const steps=[...document.querySelectorAll(".step")];steps.forEach(s=>s.classList.remove("active"));
 steps.forEach((s,i)=>setTimeout(()=>s.classList.add("active"),i*700));
}
function graph(evidence){
 const g=$("graph");g.innerHTML='<div class="center-node">CLAIM</div>';
 const items=(evidence||[]).slice(0,8);const cx=g.clientWidth/2,cy=g.clientHeight/2;
 items.forEach((e,i)=>{
   const ang=(Math.PI*2/items.length)*i-.6,r=125+(i%2)*28;
   const x=cx+Math.cos(ang)*r,y=cy+Math.sin(ang)*r;
   const n=document.createElement("div");n.className="e-node "+(e.stance||"neutral");n.textContent=(e.source_tier||"WEB").toUpperCase();n.style.left=x+"px";n.style.top=y+"px";n.style.animationDelay=(i*.08)+"s";g.appendChild(n);
   const dx=x-cx,dy=y-cy,len=Math.sqrt(dx*dx+dy*dy),line=document.createElement("div");line.className="connector";line.style.left=cx+"px";line.style.top=cy+"px";line.style.width=len+"px";line.style.transform="rotate("+Math.atan2(dy,dx)+"rad)";g.insertBefore(line,n);
 });
}

$("run").onclick=async()=>{
 if(!state.api){$("modal").classList.remove("hidden");return}
 const claim=$("claim").value.trim();if(!claim)return;
 $("results").classList.add("hidden");$("scanner").classList.remove("hidden");animateSteps();
 try{
   const r=await fetch(state.api+"/api/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({claim,media_url:$("mediaUrl").value.trim()||null})});
   const d=await r.json();if(!r.ok)throw new Error(d.detail||"Investigation failed");
   const s=d.score||{},v=s.verdict||"UNVERIFIED";$("verdict").textContent=v;
   $("verdict").style.color=v==="SUPPORTED"?"#34d399":v==="LIKELY UNOFFICIAL"?"#fb7185":"#22d3ee";
   $("confidence").textContent="CONFIDENCE "+Math.round((s.confidence||0)*100)+"%  ·  SUPPORT "+(s.support_score||0)+"  ·  CONTRADICTION "+(s.contradiction_score||0);
   $("summary").textContent=d.analysis?.summary||"Investigation complete.";
   $("trace").innerHTML=(d.plan?.verification_questions||[]).map((q,i)=>'<div class="trace-item" style="animation-delay:'+i*.08+'s"><b>0'+(i+1)+'</b><span>'+esc(q)+'</span></div>').join("");
   $("evidence").innerHTML=(d.evidence||[]).map((e,i)=>'<div class="source" style="animation-delay:'+i*.06+'s"><a target="_blank" rel="noopener" href="'+encodeURI(e.url||"#")+'">'+esc(e.title)+'</a><span class="pill">'+esc((e.source_tier||"web").toUpperCase())+'</span><p>'+esc((e.excerpt||"").slice(0,300))+'</p></div>').join("")||'<p>No evidence returned.</p>';
   $("provenance").textContent=d.analysis?.provenance_summary||"No provenance summary available.";
   graph(d.evidence||[]);$("scanner").classList.add("hidden");$("results").classList.remove("hidden");$("results").scrollIntoView({behavior:"smooth"});
 }catch(e){
   $("scanner").classList.add("hidden");
   if(String(e.message).includes("Failed to fetch") || e.name==="TypeError"){
     localStorage.removeItem("ghostframe_api");
     state.api="";
     $("connection").textContent="CONNECT CLOUD BACKEND";
     alert("Your saved backend URL is offline. GhostFrame cleared it. Connect a permanent Cloud Run URL and try again.");
   }else{
     alert(e.message);
   }
 }
};

const demoPayload={
  claim:"This is the official trailer for Avengers: Secret Wars.",
  plan:{
    verification_questions:[
      "Has Marvel Studios officially released a trailer for Avengers: Secret Wars?",
      "Do major entertainment outlets confirm an official trailer release?",
      "Are circulating videos labeled concept, fan-made, or unofficial?",
      "Does the claimed media trace back to an official studio source?"
    ]
  },
  score:{verdict:"LIKELY UNOFFICIAL",confidence:.94,support_score:1,contradiction_score:8},
  analysis:{
    summary:"The available provenance signals do not support this as an official studio trailer. The strongest evidence points to unofficial or concept-trailer circulation rather than an authenticated Marvel release.",
    provenance_summary:"Demo data: GhostFrame compares the claim against source authority, publication context, contradictory wording, and provenance signals. Connect the live Cloud Run backend for real-time verification."
  },
  evidence:[
    {title:"Marvel official channels",url:"https://www.marvel.com/",source_tier:"official",stance:"contradiction",excerpt:"No matching official trailer release is demonstrated in this demo dataset."},
    {title:"Major entertainment reporting",url:"https://variety.com/",source_tier:"reputable",stance:"neutral",excerpt:"Reputable coverage is used to confirm whether a trailer release was officially announced."},
    {title:"Concept / fan trailer signals",url:"#",source_tier:"web",stance:"contradiction",excerpt:"Circulating uploads may use labels such as concept trailer, fan-made, unofficial, or AI-generated."}
  ]
};

function renderResult(d){
  const s=d.score||{},v=s.verdict||"UNVERIFIED";$("verdict").textContent=v;
  $("verdict").style.color=v==="SUPPORTED"?"#34d399":v==="LIKELY UNOFFICIAL"?"#fb7185":"#22d3ee";
  $("confidence").textContent="CONFIDENCE "+Math.round((s.confidence||0)*100)+"%  ·  SUPPORT "+(s.support_score||0)+"  ·  CONTRADICTION "+(s.contradiction_score||0);
  $("summary").textContent=d.analysis?.summary||"Investigation complete.";
  $("trace").innerHTML=(d.plan?.verification_questions||[]).map((q,i)=>'<div class="trace-item" style="animation-delay:'+i*.08+'s"><b>0'+(i+1)+'</b><span>'+esc(q)+'</span></div>').join("");
  $("evidence").innerHTML=(d.evidence||[]).map((e,i)=>'<div class="source" style="animation-delay:'+i*.06+'s"><a target="_blank" rel="noopener" href="'+encodeURI(e.url||"#")+'">'+esc(e.title)+'</a><span class="pill">'+esc((e.source_tier||"web").toUpperCase())+'</span><p>'+esc((e.excerpt||"").slice(0,300))+'</p></div>').join("");
  $("provenance").textContent=d.analysis?.provenance_summary||"No provenance summary available.";
  graph(d.evidence||[]);$("scanner").classList.add("hidden");$("results").classList.remove("hidden");$("results").scrollIntoView({behavior:"smooth"});
}

$("demoRun").onclick=()=>{
  const btn=$("demoRun");
  btn.disabled=true;
  btn.textContent="ANALYZING DEMO...";
  $("results").classList.add("hidden");
  $("scanner").classList.remove("hidden");
  animateSteps();
  $("scanner").scrollIntoView({behavior:"smooth",block:"center"});
  setTimeout(()=>{
    renderResult(demoPayload);
    btn.disabled=false;
    btn.textContent="RUN DEMO MODE";
  },2900);
};
