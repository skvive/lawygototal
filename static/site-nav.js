/** Shared LAWYGO top navigation (Journal-first IA) */
(function () {
  const path = location.pathname;
  const active = (p) => (path === p || path.startsWith(p + '/') ? 'active' : '');
  const html = `
<header class="wsj-header">
  <div class="wsj-utility"><div class="wsj-wrap wsj-utility-inner">
    <span>LAWYGO LEGAL INTELLIGENCE</span>
    <span>${new Date().toISOString().slice(0, 10)} · 서울 · 뉴욕</span>
  </div></div>
  <div class="wsj-masthead"><div class="wsj-wrap wsj-masthead-inner">
    <a class="wsj-logo" href="/"><span class="wsj-logo-main">LAWYGO</span><span class="wsj-logo-sub">JOURNAL</span></a>
    <nav class="wsj-nav" aria-label="주 메뉴">
      <a class="${active('/journal')}" href="/journal">저널</a>
      <a class="${active('/channel')}" href="/channel">채널</a>
      <a class="${active('/p/wiki')}" href="/p/wiki">위키</a>
      <a class="${active('/p/pan')}" href="/p/pan">판</a>
      <a class="${active('/p/note')}" href="/p/note">노트</a>
      <a class="${active('/pro')}" href="/pro">PRO</a>
      <a class="${active('/pricing')}" href="/pricing">구독</a>
      <a class="${active('/partnership')}" href="/partnership">파트너십</a>
    </nav>
    <div class="wsj-actions">
      <a class="wsj-btn wsj-btn-ghost" href="/#newsletter">뉴스레터</a>
      <a class="wsj-btn wsj-btn-admin" href="/dashboard">관리자 로그인</a>
    </div>
  </div></div>
</header>`;
  document.querySelectorAll('[data-lawygo-nav]').forEach((el) => {
    el.innerHTML = html;
  });
})();
