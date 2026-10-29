async function load() {
  const root = document.getElementById("note-feed");
  const data = await fetch("/api/posts?product=note&limit=20", { credentials: "same-origin" }).then(
    (r) => r.json(),
  );
  root.replaceChildren();
  if (!(data.items || []).length) {
    root.innerHTML =
      '<p class="demo-note">공개 노트가 없습니다. <a href="/dashboard">로그인</a> 후 개인 노트를 작성하세요. (Atlas note/index 워크플로)</p>';
    return;
  }
  for (const post of data.items) {
    const row = document.createElement("div");
    row.className = "issue-row";
    row.innerHTML = `<div><b>${post.kind}</b><h3>${post.title}</h3><p>${post.updated_at?.slice(0, 10) || ""}</p></div>`;
    root.append(row);
  }
}

load();
