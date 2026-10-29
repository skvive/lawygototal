(() => {
  document.querySelectorAll("form[data-pan-api]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = form.querySelector(".pn-api-result");
      if (!form.reportValidity()) return;
      const payload = Object.fromEntries(new FormData(form).entries());
      for (const key of ["rights", "terms", "marketing"]) payload[key] = Boolean(new FormData(form).get(key));
      if (form.dataset.contentType) payload.content_type = form.dataset.contentType;
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      status.textContent = "요청을 확인하고 있습니다…";
      try {
        const response = await fetch(form.dataset.panApi, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          credentials: "same-origin",
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || data.message || "요청을 처리하지 못했습니다.");
        status.textContent = data.message || "접수되었습니다.";
        if (response.ok) form.reset();
      } catch (err) {
        status.textContent =
          err?.message ||
          "대시보드에서 Google Blogger·YouTube OAuth 연동(/api/google/connect) 후 동기화를 실행하세요.";
      } finally {
        button.disabled = false;
      }
    });
  });
})();

(() => {
  const target = document.querySelector("[data-approved-feed]");
  if (!target) return;
  const kind = target.dataset.approvedFeed || "all";
  fetch("/api/feed?kind=" + encodeURIComponent(kind), { credentials: "omit" })
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error("offline"))))
    .then((data) => {
      target.replaceChildren();
      if (!Array.isArray(data.contents) || !data.contents.length) {
        target.textContent =
          "공개 콘텐츠가 없습니다. Vercel에 LAWYGO_PAN_BLOGGER_SITES·LAWYGO_PAN_YOUTUBE_CHANNEL_IDS를 설정하거나 대시보드에서 OAuth 동기화 후 승인하세요.";
        return;
      }
      data.contents.slice(0, 6).forEach((x) => {
        const a = document.createElement("a");
        a.href = x.url;
        a.rel = "noopener noreferrer";
        a.target = "_blank";
        a.className = "pn-card";
        const img = document.createElement("img");
        img.alt = "";
        img.loading = "lazy";
        img.src =
          x.thumb_url ||
          (x.content_type === "video" || x.content_type === "shorts"
            ? "/static/img/editorial/pan-blog-2.png"
            : "/static/img/editorial/pan-blog-1.png");
        const body = document.createElement("div");
        body.className = "body";
        const tag = document.createElement("span");
        tag.className = "pn-tag";
        tag.textContent =
          (x.approved ? "CMS · 승인" : "RSS · ") +
          (x.content_type === "shorts" ? "SHORTS" : x.content_type === "video" ? "VIDEO" : "BLOG");
        const h3 = document.createElement("h3");
        h3.textContent = x.title;
        const p = document.createElement("p");
        p.textContent = x.summary || "원문 확인";
        body.append(tag, h3, p);
        a.append(img, body);
        target.appendChild(a);
      });
    })
    .catch(() => {
      target.textContent = "피드를 불러오지 못했습니다. 잠시 후 다시 시도하세요.";
    });
})();
