/* LAWYGO master navigation: workspace-first, journal omitted from public IA. */
(function(){
  const p=location.pathname;
  const on=(s)=>p===s||p.startsWith(s+'/')?'active':'';
  const menu=[
    {href:'/p/wiki',name:'법률백과'},
    {href:'/p/note',name:'AI 워크스페이스'},
    {href:'/pro',name:'송무 PRO'},
    {href:'/p/pan',name:'전문가 PAN'},
    {href:'/pricing',name:'서비스 안내'},
    {href:'/partnership',name:'파트너십'}
  ];
  const links=menu.map(x=>'<a class="'+on(x.href)+'" href="'+x.href+'">'+x.name+'</a>').join('');
  const header='<a class="skip-link" href="#main-content">본문으로 바로가기</a>'+
    '<div class="utility"><div class="wrap utility-inner"><span>LAWYGO / LEGAL INTELLIGENCE</span><span>KNOWLEDGE · WORKSPACE · PRACTICE</span><span class="utility-right">THE LEGAL OPERATING NETWORK</span></div></div>'+
    '<header class="header"><div class="wrap header-main">'+
    '<a href="/" class="logo"><img class="brand-logo-original" src="/static/logo.svg" width="38" height="38" alt="" aria-hidden="true"><span class="logo-word">LAWYGO<span class="logo-sub">LEGAL INTELLIGENCE</span></span></a>'+
    '<nav class="desktop-nav" aria-label="주 메뉴">'+links+'</nav>'+
    '<div class="header-actions"><a class="btn btn-outline btn-mini" href="/dashboard">관리자</a><a class="btn btn-gold btn-mini" href="/p/note">워크스페이스 열기 ↗</a>'+
    '<button class="menu-toggle" type="button" aria-label="메뉴 열기" aria-expanded="false" aria-controls="mobileNav">☰</button></div></div>'+
    '<nav class="wrap mobile-nav" id="mobileNav" aria-label="모바일 주 메뉴">'+links+'<a href="/dashboard">관리자 로그인</a></nav></header>';
  const footer='<footer class="footer"><div class="wrap"><div class="footer-top"><div>'+
    '<a href="/" class="footer-logo">LAWYGO<span>®</span></a><p>법률 지식을 실행 가능한 업무로 연결합니다.<br>공개 자료의 최신성과 출처는 원문에서 확인하세요.</p></div>'+
    '<div><span class="eyebrow">OUR PLATFORMS</span><p>WIKI / AI WORKSPACE / PRO / PAN</p><p>법률 AI 도구는 전문적인 법률 판단과 자문을 대신하지 않습니다.</p></div></div>'+
    '<nav class="footer-links" aria-label="하단 메뉴"><a href="/p/wiki">법률백과</a><a href="/p/note">AI 워크스페이스</a><a href="/pro">송무 PRO</a><a href="/p/pan">전문가 PAN</a><a href="/partnership">파트너십</a><a href="/dashboard">CMS</a></nav>'+
    '<div class="footer-bottom"><span>© 2026 LAWYGO. All rights reserved.</span><span>개별 사안의 법률·투자 자문을 제공하지 않습니다.</span></div></div></footer><div class="toast" role="status" aria-live="polite"></div>';
  document.querySelectorAll('[data-brand-shell="header"]').forEach(el=>el.innerHTML=header);
  document.querySelectorAll('[data-brand-shell="footer"]').forEach(el=>el.innerHTML=footer);
  // Shared visual system for existing detail pages.
  if(!document.querySelector('link[href*="lawygo-rebuild-20261108.css"]')){
    const link=document.createElement('link');link.rel='stylesheet';link.href='/static/lawygo-rebuild-20261108.css?v=20261108-workspace-first';
    link.dataset.lawygoRebuild='';document.head.append(link);
  }
  document.body.classList.add('legal-rebuild');
  const toggle=document.querySelector('.menu-toggle'),mobile=document.getElementById('mobileNav');
  const close=()=>{mobile?.classList.remove('open');toggle?.setAttribute('aria-expanded','false');toggle?.setAttribute('aria-label','메뉴 열기')};
  toggle?.addEventListener('click',()=>{let opened=mobile?.classList.toggle('open')===true;toggle.setAttribute('aria-expanded',String(opened));toggle.setAttribute('aria-label',opened?'메뉴 닫기':'메뉴 열기')});
  mobile?.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&mobile?.classList.contains('open')){close();toggle?.focus()}});
  document.addEventListener('click',e=>{if(mobile?.classList.contains('open')&&!e.target.closest('.header'))close()});
})();
