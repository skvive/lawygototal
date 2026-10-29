const imgs = [
  "/static/img/editorial/journal-lead.jpg",
  "/static/img/editorial/journal-side.jpg",
  "/static/img/journal/hero-markets.jpg",
  "/static/img/journal/hero-korea.jpg",
];
const el = (t, txt, cls) => {
  const e = document.createElement(t);
  if (txt) e.textContent = txt;
  if (cls) e.className = cls;
  return e;
};

document.getElementById("journal-edition").textContent =
  new Date().toISOString().slice(0, 10) + " — LIVE EDITION";

function showIssue(item) {
  const view = document.getElementById("journal-issue-view");
  view.classList.remove("hidden");
  view.scrollIntoView({ behavior: "smooth" });
  document.getElementById("issue-kicker").textContent =
    (item.desk || "ARTICLE") + " · " + item.source;
  document.getElementById("issue-stamp").innerHTML =
    "ISSUE <span>" + (item.published || "") + "</span>";
  document.getElementById("issue-title").textContent = item.title;
  document.getElementById("issue-body").textContent = item.summary || item.title;
  const src = document.getElementById("issue-source");
  if (item.url && item.url.startsWith("http")) {
    src.href = item.url;
    src.style.display = "inline-flex";
    src.textContent = "원문 ↗";
  } else if (item.post_id) {
    src.href = "/p/channel";
    src.textContent = "편집국 글 보기 ↗";
    src.style.display = "inline-flex";
  } else src.style.display = "none";
}

document.getElementById("journal-issue-back").onclick = () => {
  document.getElementById("journal-issue-view").classList.add("hidden");
};

function wireRow(item, i) {
  const row = el("div", "", "issue-row");
  const left = el("div");
  left.innerHTML = `<b>VOL. ${String(i + 1).padStart(2, "0")}</b><h3>${item.title}</h3><p>${item.source} · ${item.published || ""}</p>`;
  const btn = el("button", "기사 보기 ↗", "btn btn-navy");
  btn.type = "button";
  btn.onclick = () => showIssue(item);
  row.append(left, btn);
  return row;
}

function topCard(item, img) {
  const a = el("article", "", "article-card");
  a.innerHTML = `<img class="card-img" src="${img}" alt=""><div class="article-copy"><span class="eyebrow">${item.source}</span><h3>${item.title}</h3><p>${item.summary || ""}</p><span class="readmore">자세히 읽기 ↗</span></div>`;
  a.onclick = () => showIssue(item);
  return a;
}

async function boot() {
  const res = await fetch("/api/journal/feed");
  const data = await res.json();
  const top = document.getElementById("journal-top-grid");
  top.replaceChildren();
  const lead = data.lead || data.us?.[0] || data.kr?.[0];
  const second = data.kr?.[0] || data.us?.[1];
  if (lead) top.append(topCard(lead, imgs[0]));
  if (second) top.append(topCard(second, imgs[1]));
  document.getElementById("desk-us-count").textContent = `미국·글로벌 ${(data.us || []).length}건`;
  document.getElementById("desk-kr-count").textContent = `국내 ${(data.kr || []).length}건`;

  const krList = document.getElementById("journal-kr-list");
  krList.replaceChildren();
  (data.kr || []).slice(0, 6).forEach((it, i) => krList.append(wireRow(it, i)));

  const usList = document.getElementById("journal-us-list");
  usList.replaceChildren();
  (data.us || []).slice(0, 6).forEach((it, i) => usList.append(wireRow(it, i + 6)));

  const issues = document.getElementById("journal-issues");
  issues.replaceChildren();
  [...(data.editorial || []), ...(data.kr || []).slice(0, 2)].forEach((it, i) =>
    issues.append(wireRow(it, i)),
  );

  document.getElementById("journal-disclaimer").textContent = data.disclaimer || "";
}

boot().catch(console.error);
