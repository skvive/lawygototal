const PH = ["ph-finance", "ph-city", "ph-global", "ph-law"];
const el = (t, txt, cls) => {
  const e = document.createElement(t);
  if (txt != null && txt !== "") e.textContent = txt;
  if (cls) e.className = cls;
  return e;
};

function safeJournalUrl(raw) {
  try {
    const url = new URL(String(raw || ""));
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch { return null; }
}

function journalEmpty(label, message, image, link, linkText) {
  const card = el("article", "", "lyd-feed-empty");
  const img = el("img");
  img.src = image || "/static/img/channel.webp";
  img.alt = "";
  img.loading = "lazy";
  img.width = 640;
  img.height = 360;
  const content = el("div", "", "lyd-feed-empty-copy");
  content.append(el("strong", label), el("p", message));
  const a = el("a", linkText || "LAWYGO 채널 보기 ↗");
  a.href = link || "/channel";
  content.append(a);
  card.append(img, content);
  return card;
}

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
  a.href = "#journal-front-left";
  a.addEventListener("click", (e) => { e.preventDefault(); openIssue(item); });
  a.append(el("span", rubric, "rubric"), el("h3", item.title), el("p", item.summary || item.source || ""));
  return a;
}

function leadBlock(item) {
  const wrap = el("div");
  const rubric = item.region === "kr" ? "THE BIG STORY · KOREA" : "THE BIG STORY · U.S. MARKETS";
  wrap.append(el("div", rubric, "rubric"),el("h1", item.title, "headline"),
    el("p", item.summary || "제3자 RSS 헤드라인·요약입니다.", "deck"));
  wrap.append(el("div", "", "lead-photo ph-finance"),
    el("p", (item.source || "") + " · " + (item.published || ""), "caption"),
    el("p", "LAWYGO JOURNAL · LIVE WIRE", "byline"));
  wrap.style.cursor = "pointer";
  wrap.addEventListener("click", () => openIssue(item));
  return wrap;
}

function tile(item, rubric, ph) {
  const a = el("a", "", "tile");
  a.href="#journal-row-editors";
  a.addEventListener("click",(e)=>{e.preventDefault();openIssue(item)});
  const img = el("div", "", ph); img.classList.add("tile");
  a.append(el("div", rubric, "rubric"),img,el("h3", item.title),
    el("p", item.summary || item.source || ""),el("span", item.source || "WIRE", "byline"));
  return a;
}

function keyIssue(item, n) {
  const li=el("li");
  const info=el("div");
  info.append(el("h4",item.title),el("p",item.source || ""));
  li.append(el("span",String(n).padStart(2,"0"),"num"),info);
  li.addEventListener("click",()=>openIssue(item));
  return li;
}

function wireItem(item) {
  const a=el("a","","wire-item");
  const url=safeJournalUrl(item.url);
  a.href=url || "#journal-front-left";
  if(url){a.target="_blank";a.rel="noopener noreferrer";}
  else a.addEventListener("click",(e)=>{e.preventDefault();openIssue(item)});
  a.append(el("small",item.source),el("strong",item.title));
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
  if (!left.children.length) left.append(journalEmpty(
    "EDITOR'S DESK", "오늘의 공개 기사 원문을 확인 중입니다. 승인된 자료만 자동으로 노출됩니다.",
    "/static/img/channel.webp", "/channel", "편집 채널 살펴보기 ↗"
  ));

  const leadNode = document.getElementById("journal-lead");
  leadNode.replaceChildren();
  if (lead) {
    leadNode.append(leadBlock(lead));
  } else {
    const placeholder = el('div', '', 'journal-empty-lead');
    const photo = el('img');
    photo.src='/static/img/channel.webp';
    photo.alt='경제·법률 편집 데스크를 표현한 일러스트';
    const heading=el('h2', '경제와 법률의 연결을 읽는 저널');
    const desc=el('p', '승인된 오늘의 헤드라인을 준비 중입니다. 공개 콘텐츠가 등록되면 이 영역에 업데이트됩니다.');
    placeholder.append(photo,heading,desc);
    leadNode.append(placeholder);
  }

  const right = document.getElementById("journal-right");
  right.replaceChildren();
  const keyWrap = el("div", "", "key-issues");
  keyWrap.innerHTML = '<div class="rubric">TODAY\'S KEY ISSUES</div>';
  const ol = el("ol");
  merged.slice(0, 5).forEach((it, i) => ol.append(keyIssue(it, i + 1)));
  if (!merged.length) {
    const item=el("li");
    item.append(el("strong","공개 편집 자료 확인 중"),
                el("p","정식 공개 자료만 등록되며, 콘텐츠 건수를 임의로 표시하지 않습니다."));
    ol.append(item);
  }
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
  if (!wkr.children.length) wkr.append(journalEmpty("KOREA WIRE","공개된 국내 정책·법률 제목을 확인 중입니다.","/static/img/channel.webp","/channel","채널에서 콘텐츠 확인 ↗"));
  const wus = document.getElementById("journal-wire-us");
  wus.replaceChildren();
  us.slice(0, 8).forEach((it) => wus.append(wireItem(it)));
  if (!wus.children.length) wus.append(journalEmpty("GLOBAL WIRE","공개된 미국·국제 경제 자료를 확인 중입니다.","/static/img/design/hero-sunset-20261102.webp","/channel","편집 채널 확인 ↗"));

  const row1 = document.getElementById("journal-row-editors");
  row1.replaceChildren();
  [...us.slice(0, 2), ...kr.slice(0, 1)].forEach((it, i) =>
    row1.append(tile(it, ["U.S. MARKETS", "KOREA ECONOMY", "MARKET INTELLIGENCE"][i] || "WIRE", PH[i % PH.length])),
  );
  if (!row1.children.length) row1.append(journalEmpty("EDITOR'S SELECTION","검수된 주요 기사를 준비 중입니다.","/static/img/design/editorial-library-20261102.webp","/p/wiki","WIKI 법률자료 보기 ↗"));

  const row2 = document.getElementById("journal-row-law");
  row2.replaceChildren();
  [...editorial.slice(0, 2), ...kr.slice(1, 2)].forEach((it, i) =>
    row2.append(tile(it, i === 0 ? "LEGAL INTELLIGENCE" : "EDITORIAL", PH[(i + 2) % PH.length])),
  );
  if (!row2.children.length) row2.append(journalEmpty("LAW & POLICY","승인된 제도·판례 리뷰가 등록되면 이곳에 노출됩니다.","/static/img/wiki.webp","/p/wiki","법률백과 살펴보기 ↗"));

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
