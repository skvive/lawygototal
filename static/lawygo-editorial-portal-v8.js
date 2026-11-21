/* LAWYGO v8 editorial portal shell — one publisher, five distinct modules. */
(()=>{
'use strict';
const key='lawygo-editorial-portal-v8';
if(document.getElementById(key))return;
const path=location.pathname.replace(/\\/g,'/');
const modules=[
 {slug:'journal',ko:'경제·법률',en:'LIBRARY',url:'/journal',mark:'L',active:path==='/'||path==='/journal'},
 {slug:'wiki',ko:'위키',en:'WIKI',url:'/p/wiki',mark:'W',active:path==='/p/wiki'},
 {slug:'pan',ko:'판',en:'PAN',url:'/p/pan',mark:'P',active:path==='/p/pan'},
 {slug:'pro',ko:'프로',en:'PRO',url:'/pro',mark:'R',active:path==='/pro'},
 {slug:'note',ko:'노트',en:'NOTE',url:'/p/note',mark:'N',active:path==='/p/note'}
];
const target=document.querySelector('main')||document.querySelector('[role="main"]');
if(target&&!target.id)target.id='lp8-main';
const mast=document.createElement('div');
mast.id=key;
mast.className='lp8-portal-top';
mast.innerHTML='<a class="lp8-skip" href="#'+(target?.id||'lp8-main')+'">본문으로 바로가기</a>'+
 '<header class="lp8-mast"><div class="lp8-mast-inner">'+
 '<a class="lp8-logo" href="/journal" aria-label="LAWYGO 경제·법률 자료실">'+
 '<img src="/static/logo.svg" alt="" width="54" height="54" decoding="async">'+
 '<span class="lp8-wordmark">LAWYGO</span></a>'+
 '<div class="lp8-mast-detail"><strong>ECONOMY · LAW · INTELLIGENCE</strong>경제와 법률의 변화를 근거로 읽습니다.</div>'+
 '</div></header>';
const ribbon=document.createElement('nav');
ribbon.className='lp8-ribbon';
ribbon.setAttribute('aria-label','LAWYGO 서비스 모듈');
const inner=document.createElement('div');
inner.className='lp8-ribbon-inner';
for(const item of modules){
 const link=document.createElement('a');
 link.className='lp8-module';
 link.href=item.url;
 if(item.active)link.setAttribute('aria-current','page');
 const mark=document.createElement('span');mark.className='lp8-mark';mark.textContent=item.mark;mark.setAttribute('aria-hidden','true');
 const copy=document.createElement('span');copy.className='lp8-copy';
 const strong=document.createElement('strong');strong.textContent=item.ko;
 const small=document.createElement('small');small.textContent=item.en;
 copy.append(strong,small);link.append(mark,copy);inner.append(link);
}
const all=document.createElement('a');all.href='/#modules';all.className='lp8-all';all.textContent='전체 서비스 ↗';inner.append(all);ribbon.append(inner);mast.append(ribbon);
document.body.prepend(mast);document.body.classList.add('lp8-portal');
const measure=()=>document.documentElement.style.setProperty('--lp8-top-height',Math.ceil(mast.getBoundingClientRect().height)+'px');
measure();window.addEventListener('resize',measure,{passive:true});
})();
