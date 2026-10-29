const PAN_IMGS = [
  "/static/img/editorial/pan-blog-1.png",
  "/static/img/editorial/pan-blog-2.png",
  "/static/img/editorial/journal-lead.jpg",
  "/static/img/editorial/journal-side.jpg",
];
let kindFilter = "";

document.querySelectorAll("#pan-chips .chip").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll("#pan-chips .chip").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    kindFilter = btn.dataset.kind || "";
    load();
  };
});

async function openPost(id) {
  const item = await fetch("/api/posts/" + id, { credentials: "same-origin" }).then((r) => r.json());
  if (item.detail) {
    alert(item.detail);
    return;
  }
  document.getElementById("readerTitle").textContent = item.title;
  document.getElementById("readerBody").textContent = item.body;
  document.getElementById("reader").classList.add("open");
}

document.getElementById("readerClose").onclick = () =>
  document.getElementById("reader").classList.remove("open");

async function load() {
  const q = document.getElementById("pan-search").value;
  const params = new URLSearchParams({ product: "pan", limit: "48", q });
  const data = await fetch("/api/posts?" + params).then((r) => r.json());
  let items = data.items || [];
  if (kindFilter) items = items.filter((x) => x.kind === kindFilter);
  const root = document.getElementById("pan-feed");
  root.replaceChildren();
  document.getElementById("pan-empty").classList.toggle("hidden", items.length > 0);
  items.forEach((post, i) => {
    const wrap = document.createElement("div");
    const card = document.createElement("a");
    card.className = "image-card";
    card.href = "#";
    card.onclick = (e) => {
      e.preventDefault();
      openPost(post.id);
    };
    card.innerHTML = `<img alt="" loading="lazy" src="${PAN_IMGS[i % PAN_IMGS.length]}"><div class="body"><span class="meta">${post.kind}${post.is_sponsored ? " · 광고" : ""}</span><h3>${post.title}</h3><p>${post.summary || post.title}</p><span class="small" style="display:block;margin-top:16px;color:#a77b42;font-weight:750">자세히 보기 →</span></div>`;
    wrap.append(card);
    root.append(wrap);
  });
}

document.getElementById("pan-search").addEventListener("keydown", (e) => {
  if (e.key === "Enter") load();
});
load();
