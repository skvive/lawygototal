const FALLBACK_IMG = [
  "/static/img/editorial/pan-blog-1.png",
  "/static/img/editorial/pan-blog-2.png",
];

let activeTab = "all";

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}

function bindImg(img) {
  img.addEventListener("error", () => {
    img.classList.add("pan-img-ph");
    img.removeAttribute("src");
  });
}

function thumbUrl(x, i) {
  return x.thumb_url || FALLBACK_IMG[i % FALLBACK_IMG.length];
}

async function fetchContent(type, q) {
  const params = new URLSearchParams({ type, limit: "48" });
  if (q) params.set("q", q);
  const res = await fetch("/api/pan/content?" + params);
  if (!res.ok) throw new Error("콘텐츠 API 오류");
  return res.json();
}

async function fetchLawyers(q) {
  const params = new URLSearchParams({ limit: "12" });
  if (q) params.set("q", q);
  const res = await fetch("/api/pan/lawyers?" + params);
  if (!res.ok) throw new Error("변호사 API 오류");
  return res.json();
}

function renderLawyers(items) {
  const root = document.getElementById("pan-lawyers-grid");
  if (!root) return;
  root.replaceChildren();
  if (!items.length) {
    root.innerHTML =
      '<p class="muted">등록된 공개 프로필이 없습니다. <a href="/dashboard">대시보드</a>에서 PAN · 변호사 프로필을 발행하세요.</p>';
    return;
  }
  items.forEach((L, i) => {
    const card = document.createElement("article");
    card.className = "lawyer-card shadow";
    card.dataset.search = `${L.name} ${L.practice} ${L.region} ${L.bio || ""}`.toLowerCase();
    card.dataset.category = L.practice || "";
    card.dataset.region = L.region || "";
    const img = document.createElement("img");
    img.alt = L.name || "";
    img.loading = "lazy";
    img.src = L.photo || FALLBACK_IMG[i % FALLBACK_IMG.length];
    bindImg(img);
    card.append(img);
    const body = document.createElement("div");
    body.innerHTML = `<span class="tag demo">LAWYGO PAN</span>
      <h3>${esc(L.name)} <small class="muted">${esc(L.author || "")}</small></h3>
      <div><span class="tag">${esc(L.practice)}</span><span class="tag">${esc(L.region)}</span></div>
      <p>${esc(L.bio || L.practice)}</p>`;
    card.append(body);
    const end = document.createElement("div");
    end.className = "end";
    end.innerHTML = `<a class="btn outline" href="/dashboard">프로필 보기</a>
      <a class="btn primary" href="/dashboard">상담 신청</a>`;
    card.append(end);
    root.append(card);
  });
}

function renderStory(lawyers) {
  const root = document.getElementById("pan-story");
  if (!root) return;
  root.replaceChildren();
  const list = lawyers.length ? lawyers : [{ name: "등록 대기", practice: "CMS", photo: "" }];
  list.slice(0, 6).forEach((L, i) => {
    const a = document.createElement("a");
    a.href = "/dashboard";
    const img = document.createElement("img");
    img.alt = L.name || "";
    img.src = L.photo || FALLBACK_IMG[i % FALLBACK_IMG.length];
    bindImg(img);
    a.append(img);
    const span = document.createElement("span");
    span.innerHTML = `${esc(L.name)}<br><small>${esc(L.practice)}</small>`;
    a.append(span);
    root.append(a);
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
    root.innerHTML =
      '<p class="empty" style="display:block">해당 유형 콘텐츠가 없습니다. RSS 환경변수 또는 OAuth 동기화를 확인하세요.</p>';
    return;
  }
  filtered.slice(0, mode === "shorts" ? 10 : 6).forEach((x, i) => {
    if (mode === "shorts") {
      const a = document.createElement("a");
      a.className = "pn-short";
      a.href = x.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      const img = document.createElement("img");
      img.alt = "";
      img.src = thumbUrl(x, i);
      bindImg(img);
      const play = document.createElement("span");
      play.className = "play";
      play.textContent = "▶";
      const overlay = document.createElement("div");
      overlay.className = "overlay";
      overlay.innerHTML = `<small>${esc(x.source)}</small><h3>${esc(x.title)}</h3>`;
      a.append(img, play, overlay);
      root.append(a);
      return;
    }
    const wrap = document.createElement("a");
    wrap.className = "pn-card";
    wrap.href = x.url;
    wrap.target = "_blank";
    wrap.rel = "noopener noreferrer";
    const img = document.createElement("img");
    img.alt = "";
    img.loading = "lazy";
    img.src = thumbUrl(x, i);
    bindImg(img);
    wrap.append(img);
    const body = document.createElement("div");
    body.className = "body";
    body.innerHTML = `<span class="pn-tag">${x.approved ? "CMS" : "RSS"} · BLOG</span>
      <h3>${esc(x.title)}</h3><p>${esc(x.summary)}</p><small>${esc(x.source)}</small>`;
    wrap.append(body);
    root.append(wrap);
  });
}

function renderTabList(items) {
  const root = document.getElementById("pan-content-list");
  if (!root) return;
  root.replaceChildren();
  const filtered =
    activeTab === "all"
      ? items
      : items.filter((x) => x.content_type === activeTab || (activeTab === "video" && x.content_type === "video"));
  if (!filtered.length) {
    root.innerHTML = '<p class="empty" style="display:block;padding:24px">검색 결과가 없습니다.</p>';
    return;
  }
  filtered.slice(0, 9).forEach((x, i) => {
    const a = document.createElement("a");
    a.className = "image-card";
    a.href = x.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    const img = document.createElement("img");
    img.alt = "";
    img.loading = "lazy";
    img.src = thumbUrl(x, i);
    bindImg(img);
    a.append(img);
    const body = document.createElement("div");
    body.className = "body";
    body.innerHTML = `<span class="meta">${esc(x.content_type.toUpperCase())}${
      x.approved ? "" : ' · RSS'
    }</span><h3>${esc(x.title)}</h3><p>${esc(x.summary)}</p>
      <span class="small" style="display:block;margin-top:16px;color:#a77b42;font-weight:750">자세히 보기 →</span>`;
    a.append(body);
    root.append(a);
  });
}

async function reloadAll() {
  const q =
    document.getElementById("pan-hero-search")?.value ||
    new URLSearchParams(location.search).get("q") ||
    "";
  if (document.getElementById("pan-hero-search") && q) {
    document.getElementById("pan-hero-search").value = q;
  }
  try {
    const [{ items }, lawyers] = await Promise.all([
      fetchContent(activeTab === "all" ? "all" : activeTab, q),
      fetchLawyers(q),
    ]);
    const lawyerItems = lawyers.items || [];
    renderLawyers(lawyerItems);
    renderStory(lawyerItems);
    renderTabList(items || []);
    renderContentGrid(items || [], "pan-shorts-grid", "shorts");
    renderContentGrid(items || [], "pan-blog-grid", "blog");
    const stat = document.getElementById("pan-wire-stat");
    if (stat) stat.textContent = String((items || []).length);
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
  document.getElementById("pan-lawyers")?.scrollIntoView({ behavior: "smooth" });
});

document.getElementById("menu-toggle")?.addEventListener("click", () => {
  const nav = document.getElementById("mobile-nav");
  const open = nav?.classList.toggle("open");
  document.getElementById("menu-toggle")?.setAttribute("aria-expanded", open ? "true" : "false");
});

reloadAll();
