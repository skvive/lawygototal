/**
 * LAWYGO TOTAL universal platform switcher.
 * Reuses existing public routes. Never alters the canonical brand logo or login state.
 */
(() => {
  const items = [
    {label:'저널',en:'JOURNAL',path:'/journal',match:p=>p==='/journal'||p==='/channel'||p==='/p/channel',short:'J'},
    {label:'위키',en:'WIKI',path:'/p/wiki',match:p=>p==='/p/wiki',short:'W'},
    {label:'판',en:'PAN',path:'/p/pan',match:p=>p==='/p/pan',short:'P'},
    {label:'프로',en:'PRO',path:'/pro',match:p=>p==='/pro',short:'R'},
    {label:'노트',en:'NOTE',path:'/p/note',match:p=>p==='/p/note',short:'N'}
  ];
  const productPaths = new Set(['/p/wiki','/p/pan','/p/note','/pro']);
  const normalizePath = (anchor) => {
    let url;
    try { url = new URL(anchor.getAttribute('href'), location.href); }
    catch { return null; }
    const host = url.hostname.toLowerCase();
    const path = url.pathname.replace(/\/+$/, '') || '/';
    if ((host === 'lawygo.com' || host === 'www.lawygo.com') && path === '/') return '/pro';
    if (path === '/channel' || path === '/p/channel') return '/journal';
    return path;
  };
  const normalizeProductLink = (anchor) => {
    const path = normalizePath(anchor);
    if (!path || !productPaths.has(path)) return;
    if (path === '/p/wiki' && location.pathname.replace(/\/+$/, '') === '/p/wiki') {
      anchor.removeAttribute('target');
      anchor.removeAttribute('rel');
      return;
    }
    const current = new URL(anchor.getAttribute('href'), location.href);
    const href = path === '/pro'
      ? 'https://lawygo.com'
      : `https://lawygo.lexid.site${path}${current.search}${current.hash}`;
    if (anchor.getAttribute('href') !== href) anchor.setAttribute('href', href);
    anchor.setAttribute('target', '_blank');
    anchor.setAttribute('rel', 'noopener noreferrer');
  };
  const normalizeProductLinks = (root) => {
    if (root.nodeType === 1 && root.matches?.('a[href]')) normalizeProductLink(root);
    root.querySelectorAll?.('a[href]').forEach(normalizeProductLink);
  };
  let linkObserverStarted = false;
  const observeProductLinks = () => {
    if (linkObserverStarted || !document.documentElement) return;
    linkObserverStarted = true;
    new MutationObserver(records => {
      for (const record of records) {
        if (record.type === 'attributes') normalizeProductLink(record.target);
        else record.addedNodes.forEach(normalizeProductLinks);
      }
    }).observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['href']
    });
  };
  const hasCompleteProductMenu = () => Array.from(
    document.querySelectorAll('header nav, header .mobile-nav')
  ).some(nav => {
    const paths = new Set(Array.from(nav.querySelectorAll('a[href]'), normalizePath));
    return items.every(item => paths.has(item.path));
  });
  const init=()=>{
    normalizeProductLinks(document);
    observeProductLinks();
    if(document.getElementById('lawygoPlatformSwitcher'))return;
    const header=document.querySelector('header.header,header.mast,body > header');
    const shell=document.querySelector('[data-brand-shell="header"]');
    if(!header&&!shell)return;
    if(hasCompleteProductMenu()){
      document.body?.classList.add('lawygo-nav-consolidated');
      return;
    }
    const wrap=document.createElement('div');
    wrap.id='lawygoPlatformSwitcher';
    wrap.className='lawygo-switcher';
    const nav=document.createElement('nav');
    nav.className='lawygo-switcher-inner';
    nav.setAttribute('aria-label','LAWYGO 플랫폼 간 이동');
    const label=document.createElement('span');
    label.className='lawygo-switcher-label';
    label.textContent='PLATFORM';
    nav.append(label);
    for(const item of items){
      const a=document.createElement('a');
      a.href=item.path==='/pro'?'https://lawygo.com':item.path.startsWith('/p/')?`https://lawygo.lexid.site${item.path}`:item.path;
      a.className='lawygo-switcher-link';
      a.setAttribute('data-platform',item.en.toLowerCase());
      if(item.path!=='/journal'&&!(item.path==='/p/wiki'&&location.pathname.replace(/\/+$/,'')==='/p/wiki')){
        a.setAttribute('target','_blank');
        a.setAttribute('rel','noopener noreferrer');
      }
      if(item.match(location.pathname)){
        a.classList.add('is-current');
        a.setAttribute('aria-current','page');
      }
      const mark=document.createElement('span');
      mark.className='lawygo-switcher-monogram';
      mark.setAttribute('aria-hidden','true');
      mark.textContent=item.short;
      const copy=document.createElement('span');
      copy.className='lawygo-switcher-copy';
      const ko=document.createElement('strong');ko.textContent=item.label;
      const en=document.createElement('small');en.textContent=item.en;
      copy.append(ko,en);
      a.append(mark,copy);
      nav.append(a);
    }
    const home=document.createElement('a');
    home.href='/';
    home.className='lawygo-switcher-all';
    home.textContent='전체 서비스 ↗';
    nav.append(home);
    wrap.append(nav);
    if(header)header.insertAdjacentElement('afterend',wrap);
    else shell.insertAdjacentElement('afterend',wrap);
    normalizeProductLinks(wrap);
    const updateOffset=()=>{
      const h=document.querySelector('header.header');
      const sticky=h&&getComputedStyle(h).position==='sticky';
      wrap.style.setProperty('--lawygo-switcher-offset',sticky?Math.max(0,h.getBoundingClientRect().height)+'px':'0px');
    };
    updateOffset();
    window.addEventListener('resize',updateOffset,{passive:true});
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
