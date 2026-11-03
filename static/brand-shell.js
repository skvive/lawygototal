/** Atlas-style brand chrome — live routes on lawygo.lexid.site */
(function () {
  const path = location.pathname;
  const on = (p) => (path === p || (p !== '/' && path.startsWith(p)) ? 'active' : '');
  const header = `
<a class="skip-link" href="#main-content">본문으로 바로가기</a>\r\n<div class="utility"><div class="wrap utility-inner"><span>ECONOMY × LAW × INTELLIGENCE</span><span>대한민국 · 미국을 잇는 제도적 통찰</span><span class="utility-right">U.S. &amp; KOREA · LEGAL INTELLIGENCE</span></div></div>
<header class="header"><div class="wrap header-main">
  <a href="/" class="logo"><img class="brand-logo-original" src="/static/logo.svg" width="38" height="38" alt="" aria-hidden="true"><span class="logo-word">LAWYGO<span class="logo-sub">LEGAL INTELLIGENCE</span></span></a>
  <nav class="desktop-nav" aria-label="주 메뉴">
    <a class="${on('/journal')}" href="/journal">저널</a>
    <a class="${on('/p/wiki')}" href="/p/wiki">위키</a>
    <a class="${on('/p/note')}" href="/p/note">노트</a>
    <a class="${on('/pro')}" href="/pro">로이고 PRO</a>
    <a class="${on('/p/pan')}" href="/p/pan">판</a>
    <a class="${on('/pricing')}" href="/pricing">구독 안내</a>
    <a class="${on('/partnership')}" href="/partnership">파트너십</a>
    <a class="${on('/strategy')}" href="/strategy">성장 전략</a>
  </nav>
  <div class="header-actions">
    <a class="btn btn-outline btn-mini" href="/#newsletter">무료 뉴스레터</a>
    <a class="btn btn-gold btn-mini" href="/payment">Payment</a>
    <button class="menu-toggle" type="button" aria-label="메뉴 열기" aria-expanded="false" aria-controls="mobileNav">☰</button>
  </div>
</div>
<div class="wrap mobile-nav" id="mobileNav" aria-label="모바일 주 메뉴">
  <a href="/journal">저널</a><a href="/p/wiki">위키</a><a href="/p/note">노트</a><a href="/pro">로이고 PRO</a><a href="/p/pan">판</a>
  <a href="/pricing">구독 안내</a><a href="/payment">Payment</a><a href="/partnership">파트너십</a><a href="/strategy">성장 전략</a><a href="/dashboard">관리자</a>
</div></header>`;
  const footer = `
<footer class="footer"><div class="wrap"><div class="footer-top"><div>
  <a href="/" class="footer-logo">LAWYGO<span>®</span></a>
  <p>경제를 읽는 법률, 제도를 해석하는 인텔리전스.<br>뉴스레터에서 전문 법률 정보·실무 도구까지.</p>
</div><div><span class="eyebrow">THE ECOSYSTEM</span><p>JOURNAL / WIKI / NOTE / PRO / PAN</p>
  <p>미국 기술 협력 관련 사항: TerraBridge Capital LLC · 확인 필요</p></div></div>
<div class="footer-links">
  <a href="/journal">저널</a><a href="/payment">Payment</a><a href="/partnership">파트너십</a><a href="/strategy">성장 전략</a><a href="/dashboard">CMS</a>
</div>
<div class="footer-bottom"><span>© 2026 LAWYGO. All rights reserved.</span>
  <span>웹사이트는 운영 중이며 유료 결제는 별도 승인 전까지 비활성 상태입니다. 개별 사안의 법률·투자 자문이 아닙니다.</span></div></div></footer>
<div class="toast" role="status" aria-live="polite"></div>`;
  document.querySelectorAll('[data-brand-shell="header"]').forEach((el) => { el.innerHTML = header; });
  document.querySelectorAll('[data-brand-shell="footer"]').forEach((el) => { el.innerHTML = footer; });
  const toggle = document.querySelector('.menu-toggle');
  const mobile = document.getElementById('mobileNav');
  const closeMobileMenu = () => {
    mobile?.classList.remove('open');
    toggle?.setAttribute('aria-expanded', 'false');
    toggle?.setAttribute('aria-label', '메뉴 열기');
  };
  toggle?.addEventListener('click', () => {
    const open = mobile?.classList.toggle('open') === true;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
  });
  mobile?.querySelectorAll('a').forEach((anchor) => {
    anchor.addEventListener('click', closeMobileMenu);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && mobile?.classList.contains('open')) {
      closeMobileMenu();
      toggle?.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (mobile?.classList.contains('open') && !event.target.closest('.header')) {
      closeMobileMenu();
    }
  });
})();

