const $ = (id) => document.getElementById(id);

function escapeHtml(value){
  return String(value || "").replace(/[&<>"']/g, (c) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

$("investigate").addEventListener("click", async () => {
  const claim = $("claim").value.trim();
  const media_url = $("url").value.trim() || null;
  if(!claim) return;

  $("result").classList.add("hidden");
  $("scanner").classList.remove("hidden");

  try{
    const response = await fetch("/api/verify", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({claim, media_url})
    });

    const data = await response.json();
    if(!response.ok) throw new Error(data.detail || "Verification failed");

    const score = data.score || {};
    const verdict = score.verdict || "UNVERIFIED";

    $("verdict").textContent = verdict;
    $("verdict").style.color =
      verdict === "SUPPORTED" ? "#34d399" :
      verdict === "LIKELY UNOFFICIAL" ? "#fb7185" : "#22d3ee";

    $("confidence").textContent =
      `Confidence ${Math.round((score.confidence || 0) * 100)}% · Support ${score.support_score || 0} · Contradiction ${score.contradiction_score || 0}`;

    $("summary").textContent =
      (data.analysis && data.analysis.summary) || "Investigation completed.";

    const questions = (data.plan && data.plan.verification_questions) || [];
    $("trace").innerHTML = questions.map((q,i) =>
      `<div class="trace-item"><div class="trace-num">0${i+1}</div><div>${escapeHtml(q)}</div></div>`
    ).join("");

    const evidence = data.evidence || [];
    $("evidence").innerHTML = evidence.map((e) =>
      `<div class="source">
        <a href="${encodeURI(e.url || "#")}" target="_blank" rel="noopener">${escapeHtml(e.title)}</a>
        <span class="pill">${escapeHtml((e.source_tier || "web").toUpperCase())}</span>
        <p>${escapeHtml((e.excerpt || "").slice(0,360))}</p>
      </div>`
    ).join("") || `<div style="color:#999">No evidence returned.</div>`;

    $("provenance").textContent =
      (data.analysis && data.analysis.provenance_summary) || "No provenance summary available.";

    $("result").classList.remove("hidden");
  }catch(err){
    alert(err.message);
  }finally{
    $("scanner").classList.add("hidden");
  }
});
