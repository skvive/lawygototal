const el = (t, txt, cls) => {
  const e = document.createElement(t);
  if (txt) e.textContent = txt;
  if (cls) e.className = cls;
  return e;
};

document.getElementById("edition-date").textContent = new Date().toLocaleDateString("ko-KR", {
  weekday: "long",
  year: "numeric",
  month: "long",
  day: "numeric",
});

function openStory(item) {
  if (item.post_id) {
    window.location.href = "/p/channel#post-" + item.post_id;
    return;
  }
  if (item.url && item.url.startsWith("http")) {
    window.open(item.url, "_blank", "noopener,noreferrer");
  }
}

function storyNode(item) {
  const a = el("article", "", "journal-story");
  a.append(el("span", item.desk || item.source, "journal-kicker"));
  a.append(el("h3", item.title));
  a.append(el("p", item.summary || ""));
  a.append(el("div", `${item.source}${item.published ? " · " + item.published : ""}`, "src"));
  a.onclick = () => openStory(item);
  return a;
}

async function boot() {
  const main = document.getElementById("journal-main");
  const rail = document.getElementById("journal-rail");
  try {
    const res = await fetch("/api/journal/feed");
    const data = await res.json();
    main.replaceChildren();

    const lead = data.lead || data.us?.[0] || data.kr?.[0];
    if (lead) {
      const block = el("div", "", "journal-lead-block");
      const imgSrc =
        lead.region === "kr"
          ? "/static/img/journal/hero-korea.jpg"
          : "/static/img/journal/hero-markets.jpg";
      block.innerHTML = `
        <div class="journal-kicker">${lead.desk || "TOP STORY"} · ${lead.source}</div>
        <h1>${lead.title}</h1>
        <p>${lead.summary || ""}</p>
        <img class="journal-lead-img" src="${imgSrc}" alt="">
        <div class="journal-meta">${lead.source} · 원문 링크는 기사 클릭</div>`;
      block.querySelector("img").onclick = () => openStory(lead);
      block.querySelector("h1").style.cursor = "pointer";
      block.querySelector("h1").onclick = () => openStory(lead);
      main.append(block);
    }

    const cols = el("div", "", "journal-columns");
    const usCol = el("div");
    usCol.append(el("h2", "UNITED STATES", "journal-section-title"));
    (data.us || []).slice(0, 8).forEach((it) => usCol.append(storyNode(it)));
    const krCol = el("div");
    krCol.append(el("h2", "KOREA · 공인 통신", "journal-section-title"));
    (data.kr || []).slice(0, 8).forEach((it) => krCol.append(storyNode(it)));
    cols.append(usCol, krCol);
    main.append(cols);

    if ((data.editorial || []).length) {
      const ed = el("div");
      ed.style.marginTop = "28px";
      ed.append(el("h2", "LAWYGO 편집국", "journal-section-title"));
      data.editorial.slice(0, 6).forEach((it) => ed.append(storyNode(it)));
      main.append(ed);
    }

    rail.replaceChildren();
    const mkt = el("div", "", "journal-rail-card");
    mkt.append(el("h4", "Market snapshot"));
    const list = el("div", "", "journal-rail-list");
    [...(data.us || []).slice(0, 5), ...(data.kr || []).slice(0, 5)].forEach((it) => {
      const a = el("a", it.title);
      a.href = it.url?.startsWith("http") ? it.url : "#";
      if (it.url?.startsWith("http")) {
        a.target = "_blank";
        a.rel = "noopener noreferrer";
      } else a.onclick = (e) => {
        e.preventDefault();
        openStory(it);
      };
      list.append(a);
    });
    mkt.append(list);
    rail.append(mkt);
    const nl = el("div", "", "journal-rail-card");
    nl.append(el("h4", "Newsletter"));
    nl.append(el("p", "월 2회 무료 경제·법률 브리핑"));
    const btn = el("a", "구독 신청 →", "wsj-btn wsj-btn-admin");
    btn.href = "/#newsletter";
    btn.style.display = "inline-flex";
    btn.style.marginTop = "10px";
    nl.append(btn);
    rail.append(nl);

    document.getElementById("journal-disclaimer").textContent = data.disclaimer || "";
  } catch (e) {
    main.replaceChildren(el("p", "저널 피드를 불러오지 못했습니다.", "journal-meta"));
    console.error(e);
  }
}

boot();
