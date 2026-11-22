const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const CATS = window.CATS, sel = {};

function toast(msg, err) { const t = $("#toast"); t.textContent = msg; t.className = "show" + (err ? " err" : ""); clearTimeout(t._h); t._h = setTimeout(() => t.className = "", 3200); }
async function api(url, body) {
  const r = await fetch(url, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const d = await r.json(); if (!r.ok) throw new Error(d.error || "Request failed"); return d;
}
async function busy(btn, fn) { btn.classList.add("loading"); btn.disabled = true; try { await fn(); } catch (e) { toast(e.message, true); } finally { btn.classList.remove("loading"); btn.disabled = false; } }

// tabs
$$(".tab").forEach(b => b.onclick = () => {
  $$(".tab").forEach(x => x.classList.toggle("active", x === b));
  $$(".panel").forEach(p => p.classList.toggle("active", p.id === "tab-" + b.dataset.tab));
  if (b.dataset.tab === "dataset") loadDataset();
});
// segmented controls
$$(".seg").forEach(seg => { sel[seg.dataset.name] = $("button.on", seg).dataset.v;
  seg.onclick = e => { const b = e.target.closest("button"); if (!b) return; $$("button", seg).forEach(x => x.classList.toggle("on", x === b)); sel[seg.dataset.name] = b.dataset.v; }; });
// sliders
[["count", "count-out", v => v], ["per", "per-out", v => v], ["ratio", "ratio-out", v => (+v).toFixed(1)], ["split", "split-out", v => v + "%"]]
  .forEach(([i, o, f]) => $("#" + i).oninput = e => $("#" + o).textContent = f(e.target.value));
const catDesc = () => $("#cat-desc").textContent = CATS[$("#category").value].desc;
$("#category").onchange = catDesc; catDesc();

// generate
function emailCard(e) {
  const legit = e.label === 0, d = document.createElement("article"); d.className = "email" + (legit ? " legit" : "");
  d.innerHTML = `<span class="badge">${legit ? "Legitimate" : "Phishing-style"} · ${esc(CATS[e.category].label)}</span>
    <button class="copy" title="Copy email" aria-label="Copy email"><i class="fa-regular fa-copy"></i></button>
    <h4>${esc(e.subject)}</h4><pre>${esc(e.body)}</pre>
    <div class="chips">${(e.indicators || "").toString().split("|").filter(Boolean).map(i => `<span class="chip">${esc(i)}</span>`).join("")}</div>`;
  $(".copy", d).onclick = async ev => { const b = ev.currentTarget; await navigator.clipboard.writeText(e.subject + "\n\n" + e.body); b.classList.add("done"); b.innerHTML = '<i class="fa-solid fa-check"></i>'; setTimeout(() => { b.classList.remove("done"); b.innerHTML = '<i class="fa-regular fa-copy"></i>'; }, 2000); };
  return d;
}
$("#gen-form").onsubmit = e => { e.preventDefault(); busy($("#gen-btn"), async () => {
  const d = await api("/generate", { category: $("#category").value, style: sel.style, difficulty: sel.difficulty, count: +$("#count").value, context: $("#context").value, save: $("#save").checked });
  const box = $("#emails"); box.innerHTML = ""; d.emails.forEach(x => box.appendChild(emailCard(x)));
  const n = $("#gen-notice"); n.hidden = !d.notice; n.textContent = d.notice;
  if ($("#save").checked) toast(`Saved ${d.saved} to dataset` + (d.skipped ? ` (${d.skipped} duplicates skipped)` : ""));
  box.scrollIntoView({ behavior: "smooth", block: "start" });
}); };

// dataset
function stat(v, l) { return `<div class="stat"><b>${v}</b><span>${l}</span></div>`; }
function renderSummary(s) {
  $("#ds-stats").innerHTML = stat(s.rows, "samples") + stat(s.phishing ?? 0, "phishing") + stat(s.legitimate ?? 0, "legitimate") + stat(s.exact_duplicates ?? 0, "exact duplicates") + stat(s.near_duplicates ?? 0, "near-duplicates") + stat(s.distinct_bigrams ?? "-", "word-pair variety");
  const n = $("#ds-suggest"); n.hidden = !s.rows; n.innerHTML = (s.suggestions || []).map(esc).join("<br>");
}
async function loadDataset() { const d = await api("/dataset"); renderSummary(d.summary);
  $("#ds-empty").hidden = d.preview.length > 0;
  $("#ds-table tbody").innerHTML = d.preview.map(r => `<tr><td><span class="tag ${r.label ? "p" : "l"}">${r.label ? "phishing" : "legit"}</span></td><td>${esc(CATS[r.category].label)}</td><td>${esc(r.difficulty)}</td><td>${esc(r.subject)}</td><td>${esc(r.source)}</td></tr>`).join(""); }
$("#build-btn").onclick = e => busy(e.currentTarget, async () => { const d = await api("/dataset/build", { per_category: +$("#per").value, legit_ratio: +$("#ratio").value, use_groq: $("#use-groq").checked });
  toast(`Added ${d.added} samples` + (d.skipped_duplicates ? ` (${d.skipped_duplicates} duplicates skipped)` : "")); await loadDataset(); });
$("#refine-btn").onclick = e => busy(e.currentTarget, async () => { const d = await api("/dataset/refine", {}); toast(`Removed ${d.removed} near-duplicates`); await loadDataset(); });
$("#clear-btn").onclick = async () => { if (confirm("Delete every sample in the dataset?")) { await api("/dataset/clear", {}); toast("Dataset cleared"); loadDataset(); } };

// train
const bars = (obj, el) => $(el).innerHTML = Object.keys(obj).length ? Object.entries(obj).map(([k, v]) => `<div class="bar"><span>${esc(CATS[k]?.label.split(" /")[0] || k)}</span><div class="t"><i class="${v < .8 ? "low" : ""}" style="width:${v * 100}%"></i></div><span>${Math.round(v * 100)}%</span></div>`).join("") : '<p class="hint">Not enough data.</p>';
$("#split").oninput = e => $("#split-out").textContent = e.target.value + "%";
$("#train-btn").onclick = e => busy(e.currentTarget, async () => {
  const { results: r } = await api("/train", { model: $("#model").value, test_size: $("#split").value / 100 });
  $("#results").hidden = false;
  $("#metrics").innerHTML = stat((r.accuracy * 100).toFixed(1) + "%", "accuracy") + stat(r.precision, "precision") + stat(r.recall, "recall") + stat(r.f1, "F1") + stat(`${r.cv_f1_mean} ± ${r.cv_f1_std}`, "5-fold F1");
  const [[tn, fp], [fn, tp]] = r.confusion_matrix;
  $("#cm").innerHTML = `<div class="cm"><div class="lbl2"></div><div class="lbl2">pred legit</div><div class="lbl2">pred phish</div><div class="lbl2">true legit</div><div class="${tn ? "hi" : ""}">${tn}</div><div>${fp}</div><div class="lbl2">true phish</div><div>${fn}</div><div class="hi">${tp}</div></div>`;
  bars(r.per_category_recall, "#bars-cat"); bars(r.heldout_category_recall, "#bars-gen");
  const f = r.top_features; $("#feat").innerHTML = f.important ? `<div class="chips">${f.important.map(x => `<span class="chip">${esc(x)}</span>`).join("")}</div>` :
    `<p class="hint">Points to phishing</p><div class="chips">${f.phishing.map(x => `<span class="chip">${esc(x)}</span>`).join("")}</div><p class="hint" style="margin-top:12px">Points to legitimate</p><div class="chips">${f.legitimate.map(x => `<span class="chip" style="background:rgba(74,222,128,.14);color:var(--green)">${esc(x)}</span>`).join("")}</div>`;
  $("#advice").innerHTML = r.suggestions.map(s => `<li>${esc(s)}</li>`).join("");
  $("#wrong").innerHTML = r.misclassified.length ? `<p class="hint" style="margin-top:12px">Mistakes to inspect:</p>` + r.misclassified.map(m => `<p>${esc(m.subject)} <span class="tag ${m.label ? "p" : "l"}">${m.label ? "phishing" : "legit"} → predicted ${m.pred ? "phishing" : "legit"}</span></p>`).join("") : "";
  $("#results").scrollIntoView({ behavior: "smooth" });
});
$("#probe-btn").onclick = e => busy(e.currentTarget, async () => { const d = await api("/predict", { text: $("#probe").value });
  const cues = Object.entries(d.cues).map(([k, v]) => `<div><b>${esc(k)}</b>: ${v.map(esc).join(", ")}</div>`).join("");
  $("#probe-out").innerHTML = `<p><b style="color:${d.label === "phishing" ? "var(--red)" : "var(--green)"}">${d.label}</b> · phishing probability ${Math.round(d.phishing_probability * 100)}%</p>${cues}`; });
$("#upload").onchange = async e => { const fd = new FormData(); fd.append("file", e.target.files[0]);
  try { const r = await fetch("/evaluate_upload", { method: "POST", body: fd }), d = await r.json(); if (!r.ok) throw new Error(d.error);
    $("#upload-out").innerHTML = `On ${d.rows} real emails: accuracy <b>${d.accuracy}</b>, precision ${d.precision}, recall ${d.recall}, F1 ${d.f1}`; } catch (x) { toast(x.message, true); } };
