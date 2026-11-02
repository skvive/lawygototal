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
  const init=()=>{
    if(document.getElementById('lawygoPlatformSwitcher'))return;
    const header=document.querySelector('header.header,header.mast,body > header');
    const shell=document.querySelector('[data-brand-shell="header"]');
    if(!header&&!shell)return;
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
      a.href=item.path;
      a.className='lawygo-switcher-link';
      a.setAttribute('data-platform',item.en.toLowerCase());
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
