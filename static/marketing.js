/* LAWYGO public feed: lazy & parallel to keep first paint independent of slow Neon queries. */
const make=(tag,txt,cls='')=>{const e=document.createElement(tag);e.textContent=txt??'';if(cls)e.className=cls;return e};
const FEED_LABELS={pan:'변호사 브랜드 채널',channel:'법률·경제 인사이트',wiki:'법률 지식·위키'};
let publicFeedStarted=false;
async function getPublicFeed(product){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),6500);
  try{
    const res=await fetch('/api/growth/feed?product='+encodeURIComponent(product),{
      credentials:'omit',signal:controller.signal,headers:{'Accept':'application/json'}
    });
    if(!res.ok)throw Error('HTTP '+res.status);
    const data=await res.json();
    return Array.isArray(data.items)?data.items.slice(0,6):[];
  }finally{clearTimeout(timer)}
}
async function renderPublicFeed(){
  const node=document.querySelector('#livePublicFeed');
  if(!node||publicFeedStarted)return;
  publicFeedStarted=true;
  // Preserve useful, clickable fallback while data is loading.
  const products=['pan','channel','wiki'];
  const results=await Promise.allSettled(products.map(p=>getPublicFeed(p)));
  const output=document.createDocumentFragment();
  products.forEach((product,idx)=>{
    const section=make('section','','public-feed-section');
    section.append(make('h3',FEED_LABELS[product]));
    const cards=make('div','','public-feed-grid');
    const result=results[idx];
    const items=result.status==='fulfilled'?result.value:[];
    items.forEach(item=>{
      const card=make('article','','public-feed-card');
      card.append(make('span',item.placement==='광고'?'광고 · 후원 콘텐츠':'전문 콘텐츠',item.placement==='광고'?'tag sponsor':'tag'));
      card.append(make('h4',item.title||'제목 없음'));
      card.append(make('p',item.summary||'원문에서 전체 내용을 확인해 주세요.'));
      const btn=make('a','자세히 보기 ↗','textlink');btn.href='/p/'+product;card.append(btn);cards.append(card);
    });
    if(!items.length){
      const link=make('a',result.status==='rejected'?'콘텐츠 연결이 지연되고 있습니다. 서비스 바로가기 ↗':'새 공개 콘텐츠를 준비하고 있습니다. 서비스 둘러보기 ↗','feed-fallback-link');
      link.href=product==='channel'?'/channel':'/p/'+product;
      cards.append(link);
    }
    section.append(cards);output.append(section);
  });
  node.replaceChildren(output);
}
const feedNode=document.querySelector('#livePublicFeed');
if(feedNode){
  if('IntersectionObserver'in window){
    const observer=new IntersectionObserver(entries=>{
      if(entries.some(e=>e.isIntersecting)){observer.disconnect();renderPublicFeed();}
    },{rootMargin:'240px 0px'});
    observer.observe(feedNode);
  }else window.addEventListener('load',()=>setTimeout(renderPublicFeed,300),{once:true});
}
const newsForm=document.querySelector('#newsletterSignup');
if(newsForm)newsForm.addEventListener('submit',async e=>{
 e.preventDefault();const msg=document.querySelector('#newsletterResult');
 msg.textContent='구독 신청을 확인하고 있습니다.';
 const data={email:document.querySelector('#newsletterEmail').value,consent:document.querySelector('#newsletterConsent').checked};
 try{
   const r=await fetch('/api/growth/newsletter/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
   const j=await r.json();
   if(!r.ok)throw Error(typeof j.detail==='string'?j.detail:'신청을 완료할 수 없습니다.');
   msg.textContent=j.message;msg.className='micro';newsForm.reset();
 }catch(x){msg.textContent=x.message;msg.className='error'}
});
