/* Public LAWYGO media feed. No fake metrics. All titles via textContent. */
const make=(tag,txt,cls='')=>{const e=document.createElement(tag);e.textContent=txt??'';if(cls)e.className=cls;return e};
async function renderPublicFeed(){
 const node=document.querySelector('#livePublicFeed');if(!node)return;
 for(const product of ['pan','channel','wiki']){
   const section=make('section','','public-feed-section');section.append(make('h3',({pan:'변호사 브랜드 채널',channel:'법률·경제 인사이트',wiki:'법률 지식·위키'})[product]));
   const cards=make('div','','public-feed-grid');
   try{const res=await fetch('/api/growth/feed?product='+product);if(!res.ok)throw Error('failed');const data=await res.json();
      for(const item of data.items.slice(0,6)){
        const card=make('article','','public-feed-card');card.append(make('span',item.placement==='광고'?'광고 · 후원 콘텐츠':'전문 콘텐츠',item.placement==='광고'?'tag sponsor':'tag'));
        card.append(make('h4',item.title));card.append(make('p',item.summary||'원문에서 전체 내용을 확인해 주세요.'));
        const btn=make('a','자세히 보기 ↗','textlink');btn.href='/p/'+product;card.append(btn);cards.append(card);
      }
      if(!data.items.length)cards.append(make('p','아직 공개된 콘텐츠가 없습니다. 검수 완료 후 등록됩니다.','empty'));
   }catch{cards.append(make('p','현재 콘텐츠를 불러올 수 없습니다.','empty'))}
   section.append(cards);node.append(section);
 }
}
const newsForm=document.querySelector('#newsletterSignup');if(newsForm)newsForm.addEventListener('submit',async e=>{
 e.preventDefault();const msg=document.querySelector('#newsletterResult');msg.textContent='구독 신청을 확인하고 있습니다.';
 const data={email:document.querySelector('#newsletterEmail').value,consent:document.querySelector('#newsletterConsent').checked};
 try{const r=await fetch('/api/growth/newsletter/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 const j=await r.json();if(!r.ok)throw Error(typeof j.detail==='string'?j.detail:'신청을 완료할 수 없습니다.');msg.textContent=j.message;newsForm.reset();
 }catch(x){msg.textContent=x.message;msg.className='error'}
});
renderPublicFeed();
