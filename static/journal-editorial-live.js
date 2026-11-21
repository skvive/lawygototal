/* LAWYGO public reference catalog — Korean-first, source-linked, no synthetic article counts */
(()=>{
'use strict';
const get=id=>document.getElementById(id);
const input=get('reference-query'),list=get('reference-items'),status=get('reference-status'),count=get('reference-count');
if(!input||!list)return;
const topics=document.querySelectorAll('[data-reference-topic]');
const validUrl=raw=>{try{const u=new URL(String(raw||''),location.origin);return ['http:','https:'].includes(u.protocol)?u.href:null}catch{return null}};
const label=str=>String(str??'').trim().slice(0,250);
const translateLink=url=>'https://translate.google.com/translate?sl=auto&tl=ko&u='+encodeURIComponent(url);
let entries=[],active='all',loaded=false;
const law=/법률|법령|판례|법원|소송|민법|형사|law|legal|court|judicial|lawsuit/i;
const policy=/정책|규제|시행|지침|규칙|policy|regulat|enforcement|guidance|act\b|rule/i;
const classify=(item,section)=>{
 const text=[item.title,item.summary,item.desk,item.source].map(label).join(' ');
 const tags=new Set([section]);
 if(law.test(text))tags.add('law');
 if(policy.test(text))tags.add('policy');
 if(section==='kr')tags.add('kr');
 if(section==='us')tags.add('us');
 return tags;
};
const classifyText={kr:'한국 경제',us:'미국·국제',law:'법률·판례',policy:'정책·규제',editorial:'편집 자료'};
const englishOnly=str=>/[a-zA-Z]{4}/.test(str)&&!/[가-힣]/.test(str);
const textNode=(tag,text,cls)=>{const el=document.createElement(tag);if(cls)el.className=cls;el.textContent=label(text);return el};
const render=()=>{
 const query=input.value.trim().toLocaleLowerCase();
 const visible=entries.filter(item=>{
  if(active!=='all'&&!item.tags.has(active))return false;
  if(!query)return true;
  return [item.title,item.summary,item.source,item.desk].some(v=>label(v).toLocaleLowerCase().includes(query));
 });
 count.textContent=loaded?visible.length.toLocaleString('ko-KR')+'건':'불러오는 중';
 list.replaceChildren();
 get('reference-empty').hidden=visible.length>0||!loaded;
 const wiki=get('reference-wiki-search');if(wiki)wiki.href='/p/wiki?view=search&q='+encodeURIComponent(input.value.trim());
 for(const item of visible.slice(0,100)){
  const article=document.createElement('article');article.className='reference-item';
  const meta=textNode('div', (classifyText[item.section]||'경제·법률')+' · '+(item.source||'공개 원문')+(item.published?' · '+item.published:''),'reference-item-meta');
  article.append(meta);
  const link=item.url?document.createElement('a'):document.createElement('div');
  link.className='reference-item-title';
  if(item.url){link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';}
  else if(item.id&&/^[a-f0-9]{32}$/.test(item.id)){link.href='/journal/articles/'+item.id;}
  const heading=textNode('h3',item.title);if(englishOnly(item.title))heading.lang='en';
  link.append(heading);article.append(link);
  if(item.summary)article.append(textNode('p',item.summary.slice(0,190),'reference-item-summary'));
  const actions=document.createElement('div');actions.className='reference-item-actions';
  if(item.url){
    const original=document.createElement('a');original.href=item.url;original.target='_blank';original.rel='noopener noreferrer';original.textContent='원문 확인 ↗';actions.append(original);
    if(englishOnly(item.title)){const translated=document.createElement('a');translated.href=translateLink(item.url);translated.target='_blank';translated.rel='noopener noreferrer';translated.textContent='외부 자동번역 ↗';translated.setAttribute('aria-label','외부 번역 서비스에서 원문 한국어로 보기');actions.append(translated);}
  }
  if(actions.childElementCount)article.append(actions);
  list.append(article);
 }
 status.textContent=loaded?'분야와 검색어에 따라 실제 공개된 자료만 표시합니다.':'공개 자료를 확인하고 있습니다.';
};
const attach=(raw,section)=>{
 for(const item of raw){
  if(!item||!label(item.title))continue;
  const tags=classify(item,section);
  entries.push({title:label(item.title),summary:label(item.summary),source:label(item.source),published:label(item.published),desk:label(item.desk),id:label(item.id),url:validUrl(item.url),section,tags});
 }
};
const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),9000);
fetch('/api/journal/feed',{headers:{Accept:'application/json'},signal:controller.signal})
.then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
.then(data=>{
  if(!data||typeof data!=='object')throw Error('Invalid feed');
  attach(Array.isArray(data.editorial)?data.editorial:[],'editorial');
  attach(Array.isArray(data.kr)?data.kr:[],'kr');
  attach(Array.isArray(data.us)?data.us:[],'us');
  if(data.lead)attach([data.lead],data.lead.region==='kr'?'kr':'us');
  const seen=new Set();entries=entries.filter(i=>{const key=i.url||i.title;if(seen.has(key))return false;seen.add(key);return true});
  loaded=true;render();
  const disclaimer=get('journal-disclaimer');if(disclaimer)disclaimer.textContent=label(data.disclaimer);
})
.catch(()=>{loaded=true;render();status.textContent='현재 공개 자료 연결을 확인할 수 없습니다. 법률백과 또는 전문가 콘텐츠를 이용해 주세요.';})
.finally(()=>clearTimeout(timeout));
get('reference-search-form').addEventListener('submit',event=>{event.preventDefault();render();get('reference-results').scrollIntoView({behavior:'smooth',block:'start'})});
input.addEventListener('input',render);
topics.forEach(button=>button.addEventListener('click',()=>{
 active=button.dataset.referenceTopic;
 topics.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
 render();
 if(window.matchMedia('(max-width:760px)').matches)get('reference-results').scrollIntoView({behavior:'smooth'});
}));
const newsletter=get('newsletterSignupJournal');
newsletter?.addEventListener('submit',async event=>{
 event.preventDefault();
 const result=get('journal-nl-status');result.textContent='신청 처리 중…';
 try{
  const response=await fetch('/api/growth/newsletter/request',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({email:get('journal-nl-email').value,consent:get('journal-nl-consent').checked})});
  const payload=await response.json();if(!response.ok)throw Error(typeof payload.detail==='string'?payload.detail:'구독 요청 실패');
  result.textContent=payload.message||'신청이 접수되었습니다. 이메일을 확인하세요.';newsletter.reset();
 }catch(error){result.textContent=String(error.message||'요청을 처리하지 못했습니다.')}
});
})();
