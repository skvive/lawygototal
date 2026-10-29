const PH = ["ph-finance", "ph-city", "ph-global", "ph-law"];
const el = (t, txt, cls) => {
  const e = document.createElement(t);
  if (txt != null && txt !== "") e.textContent = txt;
  if (cls) e.className = cls;
  return e;
};

function openIssue(item) {
  const overlay = document.getElementById("journal-issue-overlay");
  document.getElementById("issue-kicker").textContent =
    (item.desk || item.region?.toUpperCase() || "WIRE") + " · " + (item.source || "LAWYGO");
  document.getElementById("issue-title").textContent = item.title;
  document.getElementById("issue-meta").textContent = item.published || "";
  document.getElementById("issue-body").textContent = item.summary || item.title;
  const src = document.getElementById("issue-source");
  if (item.url && item.url.startsWith("http")) {
    src.href = item.url;
    src.style.display = "inline-flex";
    src.textContent = "원문 ↗";
  } else {
    src.style.display = "none";
  }
  overlay.classList.add("open");
  overlay.setAttribute("aria-hidden", "false");
}

document.getElementById("journal-issue-close")?.addEventListener("click", () => {
  const overlay = document.getElementById("journal-issue-overlay");
  overlay.classList.remove("open");
  overlay.setAttribute("aria-hidden", "true");
});

function sideStory(item, rubric) {
  const a = el("a", "", "side-story");
  a.style.display = "block";
  a.href = "#";
  a.addEventListener("click", (e) => {
    e.preventDefault();
    openIssue(item);
  });
  a.innerHTML = `<span class="rubric">${rubric}</span><h3>${item.title}</h3><p>${item.summary || item.source || ""}</p>`;
  return a;
}

function leadBlock(item) {
  const wrap = el("div");
  const rubric = item.region === "kr" ? "THE BIG STORY · KOREA" : "THE BIG STORY · U.S. MARKETS";
  const img = el("div", "", "lead-photo ph-finance");
  wrap.innerHTML = `<div class="rubric">${rubric}</div><h1 class="headline">${item.title}</h1><p class="deck">${item.summary || "제3자 RSS 헤드라인·요약입니다."}</p>`;
  wrap.append(img);
  const cap = el("p", item.source + " · " + (item.published || ""), "caption");
  const by = el("p", "LAWYGO JOURNAL · LIVE WIRE", "byline");
  wrap.append(cap, by);
  wrap.style.cursor = "pointer";
  wrap.addEventListener("click", () => openIssue(item));
  return wrap;
}

function tile(item, rubric, ph) {
  const a = el("a", "", "tile");
  a.href = "#";
  a.addEventListener("click", (e) => {
    e.preventDefault();
    openIssue(item);
  });
  const img = el("div", "", ph);
  img.classList.add("tile");
  a.innerHTML = `<div class="rubric">${rubric}</div>`;
  a.append(img);
  const h = el("h3", item.title);
  const p = el("p", item.summary || item.source || "");
  const b = el("span", item.source || "WIRE", "byline");
  a.append(h, p, b);
  return a;
}

function keyIssue(item, n) {
  const li = el("li");
  li.innerHTML = `<span class="num">${String(n).padStart(2, "0")}</span><div><h4>${item.title}</h4><p>${item.source}</p></div>`;
  li.addEventListener("click", () => openIssue(item));
  return li;
}

function wireItem(item) {
  const a = el("a", "", "wire-item");
  a.href = item.url && item.url.startsWith("http") ? item.url : "#";
  if (!item.url?.startsWith("http")) {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      openIssue(item);
    });
  } else {
    a.target = "_blank";
    a.rel = "noopener";
  }
  a.innerHTML = `<small>${item.source}</small><strong>${item.title}</strong>`;
  return a;
}

async function boot() {
  const res = await fetch("/api/journal/feed");
  const data = await res.json();
  const us = data.us || [];
  const kr = data.kr || [];
  const editorial = data.editorial || [];
  const merged = [...editorial, ...kr, ...us];

  document.getElementById("journal-edition-meta").textContent =
    new Date().toISOString().slice(0, 10) + " · LIVE EDITION";

  const lead = data.lead || us[0] || kr[0] || editorial[0];
  const left = document.getElementById("journal-front-left");
  left.replaceChildren();
  (kr.slice(0, 2).length ? kr : editorial).slice(0, 2).forEach((it, i) =>
    left.append(sideStory(it, i === 0 ? "KOREA ECONOMY" : "LEGAL INTELLIGENCE")),
  );

  const leadNode = document.getElementById("journal-lead");
  leadNode.replaceChildren();
  if (lead) leadNode.append(leadBlock(lead));

  const right = document.getElementById("journal-right");
  right.replaceChildren();
  const keyWrap = el("div", "", "key-issues");
  keyWrap.innerHTML = '<div class="rubric">TODAY\'S KEY ISSUES</div>';
  const ol = el("ol");
  merged.slice(0, 5).forEach((it, i) => ol.append(keyIssue(it, i + 1)));
  keyWrap.append(ol);
  right.append(keyWrap);
  us.slice(0, 2).forEach((it, i) =>
    right.append(sideStory(it, i === 0 ? "MARKET INTELLIGENCE" : "U.S. MARKETS")),
  );
  const promo = el("div", "", "sidebar-promo");
  promo.innerHTML =
    '<span class="rubric">FREE NEWSLETTER</span><h3>경제의 변화를 법률의 관점에서 읽다.</h3><p>매월 두 번, 미국·한국 제도 변화를 전달합니다.</p><a href="#newsletter">무료 뉴스레터 ↗</a>';
  right.append(promo);

  const wkr = document.getElementById("journal-wire-kr");
  wkr.replaceChildren();
  kr.slice(0, 8).forEach((it) => wkr.append(wireItem(it)));
  const wus = document.getElementById("journal-wire-us");
  wus.replaceChildren();
  us.slice(0, 8).forEach((it) => wus.append(wireItem(it)));

  const row1 = document.getElementById("journal-row-editors");
  row1.replaceChildren();
  [...us.slice(0, 2), ...kr.slice(0, 1)].forEach((it, i) =>
    row1.append(tile(it, ["U.S. MARKETS", "KOREA ECONOMY", "MARKET INTELLIGENCE"][i] || "WIRE", PH[i % PH.length])),
  );

  const row2 = document.getElementById("journal-row-law");
  row2.replaceChildren();
  [...editorial.slice(0, 2), ...kr.slice(1, 2)].forEach((it, i) =>
    row2.append(tile(it, i === 0 ? "LEGAL INTELLIGENCE" : "EDITORIAL", PH[(i + 2) % PH.length])),
  );

  document.getElementById("journal-disclaimer").textContent = data.disclaimer || "";
}

const nl = document.getElementById("newsletterSignupJournal");
nl?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("journal-nl-status");
  status.textContent = "처리 중…";
  try {
    const r = await fetch("/api/growth/newsletter/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("journal-nl-email").value,
        consent: document.getElementById("journal-nl-consent").checked,
      }),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : "실패");
    status.textContent = j.message;
    nl.reset();
  } catch (err) {
    status.textContent = err.message;
  }
});

boot().catch((err) => {
  console.error(err);
  document.getElementById("journal-disclaimer").textContent =
    "피드를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
});
