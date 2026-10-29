async function searchWiki(q) {
  const res = await fetch("/api/wiki/search?q=" + encodeURIComponent(q));
  const data = await res.json();
  const root = document.getElementById("wiki-results");
  root.replaceChildren();
  document.getElementById("wiki-count").textContent = (data.items || []).length + "건";
  for (const it of data.items || []) {
    const a = document.createElement("a");
    a.className = "result-card";
    a.href = "#";
    a.innerHTML = `<span>${it.kind || "wiki"}</span><h3>${it.title}</h3><p>${it.summary || ""}</p><small>${it.source || "LAWYGO WIKI"}</small>`;
    root.append(a);
  }
  if (!(data.items || []).length) {
    root.innerHTML = '<p class="no-results">검색 결과가 없습니다. CMS에서 위키 글을 발행하세요.</p>';
  }
}

document.getElementById("wiki-search-form").onsubmit = (e) => {
  e.preventDefault();
  searchWiki(document.getElementById("wikiq").value);
};

async function loadFeed() {
  const data = await fetch("/api/posts?product=wiki&limit=12").then((r) => r.json());
  const root = document.getElementById("wiki-feed");
  root.replaceChildren();
  const imgs = ["/static/img/editorial/journal-lead.jpg", "/static/img/editorial/journal-side.jpg"];
  (data.items || []).forEach((post, i) => {
    const a = document.createElement("a");
    a.className = "article-card";
    a.href = "#";
    a.innerHTML = `<img class="card-img" src="${imgs[i % 2]}" alt=""><div class="article-copy"><span class="eyebrow">${post.kind}</span><h3>${post.title}</h3><p>${post.summary || ""}</p><span class="readmore">읽기 ↗</span></div>`;
    root.append(a);
  });
}

loadFeed();
searchWiki("공시");
