const FALLBACK_IMG = [
  "/static/img/editorial/pan-blog-1.png",
  "/static/img/editorial/pan-blog-2.png",
  "/static/img/editorial/journal-lead.jpg",
  "/static/img/editorial/journal-side.jpg",
];

let activeTab = "all";

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}

async function fetchContent(type, q) {
  const params = new URLSearchParams({ type, limit: "48" });
  if (q) params.set("q", q);
  const res = await fetch("/api/pan/content?" + params);
  if (!res.ok) throw new Error("콘텐츠 API 오류");
  return res.json();
}

async function fetchLawyers(q) {
  const params = new URLSearchParams({ limit: "8" });
  if (q) params.set("q", q);
  const res = await fetch("/api/pan/lawyers?" + params);
  if (!res.ok) throw new Error("변호사 API 오류");
  return res.json();
}

function renderLawyers(items) {
  const root = document.getElementById("pan-lawyers");
  if (!root) return;
  root.replaceChildren();
  if (!items.length) {
    root.innerHTML =
      '<p class="muted">등록된 공개 프로필이 없습니다. <a href="/dashboard">대시보드</a>에서 PAN · 변호사 프로필을 발행하세요.</p>';
    return;
  }
  items.forEach((L) => {
    const card = document.createElement("article");
    card.className = "lawyer-card shadow";
    card.innerHTML = `
      <img alt="" loading="lazy" src="${esc(L.photo)}">
      <div>
        <span class="tag demo">LAWYGO PAN</span>
        <h3>${esc(L.name)} <small class="muted">${esc(L.author || "")}</small></h3>
        <div><span class="tag">${esc(L.practice)}</span><span class="tag">${esc(L.region)}</span></div>
        <p>${esc(L.bio || L.practice)}</p>
      </div>
      <div class="end">
        <a class="btn outline" href="/api/posts/${esc(L.id)}" target="_blank" rel="noopener">프로필 ↗</a>
        <a class="btn primary" href="/dashboard">상담 연동</a>
      </div>`;
    root.append(card);
  });
}

function renderContentGrid(items, rootId, mode) {
  const root = document.getElementById(rootId);
  if (!root) return;
  root.replaceChildren();
  const filtered = items.filter((x) => {
    if (mode === "shorts") return x.content_type === "shorts";
    if (mode === "blog") return x.content_type === "blog";
    if (mode === "video") return x.content_type === "video";
    return true;
  });
  if (!filtered.length) {
    root.innerHTML = '<p class="empty" style="display:block">해당 유형 콘텐츠가 없습니다. RSS 환경변수 또는 OAuth 동기화를 확인하세요.</p>';
    return;
  }
  filtered.slice(0, mode === "shorts" ? 10 : 9).forEach((x, i) => {
    if (mode === "shorts") {
      const a = document.createElement("a");
      a.className = "pn-short";
      a.href = x.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML = `
        <img alt="" src="${esc(x.thumb_url || FALLBACK_IMG[i % FALLBACK_IMG.length])}">
        <span class="play">▶</span>
        <div class="overlay"><small>${esc(x.source)}</small><h3>${esc(x.title)}</h3></div>`;
      root.append(a);
      return;
    }
    const wrap = document.createElement("a");
    wrap.className = mode === "blog" ? "pn-card" : "image-card";
    wrap.href = x.url;
    wrap.target = "_blank";
    wrap.rel = "noopener noreferrer";
    const thumb = x.thumb_url || FALLBACK_IMG[i % FALLBACK_IMG.length];
    if (mode === "blog") {
      wrap.innerHTML = `<img alt="" loading="lazy" src="${esc(thumb)}"><div class="body"><span class="pn-tag">${
        x.approved ? "CMS" : "RSS"
      } · BLOG</span><h3>${esc(x.title)}</h3><p>${esc(x.summary)}</p><small>${esc(x.source)}</small></div>`;
    } else {
      wrap.innerHTML = `<img alt="" loading="lazy" src="${esc(thumb)}"><div class="body"><span class="meta">VIDEO</span><h3>${esc(
        x.title,
      )}</h3><p>${esc(x.summary)}</p></div>`;
    }
    root.append(wrap);
  });
}

function renderTabList(items) {
  const root = document.getElementById("pan-content-list");
  if (!root) return;
  root.replaceChildren();
  const filtered =
    activeTab === "all" ? items : items.filter((x) => x.content_type === activeTab || (activeTab === "video" && x.content_type === "video"));
  if (!filtered.length) {
    root.innerHTML = '<p class="empty" style="display:block;padding:24px">검색 결과가 없습니다.</p>';
    return;
  }
  filtered.slice(0, 12).forEach((x, i) => {
    const a = document.createElement("a");
    a.className = "image-card";
    a.href = x.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.innerHTML = `
      <img alt="" loading="lazy" src="${esc(x.thumb_url || FALLBACK_IMG[i % FALLBACK_IMG.length])}">
      <div class="body">
        <span class="meta">${esc(x.content_type.toUpperCase())}${x.approved ? "" : ' <span class="pan-wire-badge">RSS</span>'}</span>
        <h3>${esc(x.title)}</h3>
        <p>${esc(x.summary)}</p>
      </div>`;
    root.append(a);
  });
}

async function reloadAll() {
  const q =
    document.getElementById("pan-hero-search")?.value ||
    new URLSearchParams(location.search).get("q") ||
    "";
  try {
    const [{ items }, lawyers] = await Promise.all([fetchContent(activeTab === "all" ? "all" : activeTab, q), fetchLawyers(q)]);
    renderLawyers(lawyers.items || []);
    renderTabList(items || []);
    renderContentGrid(items || [], "pan-shorts-grid", "shorts");
    renderContentGrid(items || [], "pan-blog-grid", "blog");
    renderContentGrid(items || [], "pan-video-grid", "video");
    const stat = document.getElementById("pan-wire-stat");
    if (stat) stat.textContent = (items || []).length + "건 · CMS+Google RSS";
  } catch (e) {
    console.error(e);
  }
}

document.querySelectorAll("#pan-content-tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#pan-content-tabs button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeTab = btn.dataset.kind || "all";
    reloadAll();
  });
});

document.getElementById("pan-hero-search-form")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("pan-hero-search")?.value || "";
  history.replaceState(null, "", q ? "?q=" + encodeURIComponent(q) : "/p/pan");
  reloadAll();
});

document.getElementById("menu-toggle")?.addEventListener("click", () => {
  const nav = document.getElementById("mobile-nav");
  const open = nav?.classList.toggle("open");
  document.getElementById("menu-toggle")?.setAttribute("aria-expanded", open ? "true" : "false");
});

reloadAll();
