/* LAWYGO JOURNAL front page: progressive, source-linked public headlines only. */
(()=>{
'use strict';
const target=document.querySelector('.v7-news-column .v7-editorial-items');
if(!target)return;
const controller=new AbortController();
const timeout=setTimeout(()=>controller.abort(),6500);
const trustworthyUrl=(raw)=>{
 try{const u=new URL(String(raw||''));return u.protocol==='https:'||u.protocol==='http:'?u.href:null;}catch{return null;}
};
const asText=(raw,limit)=>String(raw??'').trim().slice(0,limit);
const card=(article)=>{
 const title=asText(article?.title,150);
 if(!title)return null;
 const a=document.createElement('a');
 const href=trustworthyUrl(article?.url);
 a.href=href||'/journal';
 if(href){a.target='_blank';a.rel='noopener noreferrer';}
 const small=document.createElement('small');
 const source=asText(article?.source,60)||'LAWYGO JOURNAL';
 small.textContent=source;
 const strong=document.createElement('strong');strong.textContent=title;
 const detail=document.createElement('span');
 const published=asText(article?.published,32);
 detail.textContent=(published?published+' · ':'')+(href?'원문에서 상세 확인 ↗':'지면에서 읽기 ↗');
 a.append(small,strong,detail);
 return a;
};
fetch('/api/journal/feed',{signal:controller.signal,headers:{Accept:'application/json'}})
 .then(r=>{if(!r.ok)throw Error('Journal feed HTTP '+r.status);return r.json()})
 .then(data=>{
  const input=[data?.lead,...(Array.isArray(data?.editorial)?data.editorial:[]),
  ...(Array.isArray(data?.kr)?data.kr:[]),...(Array.isArray(data?.us)?data.us:[])];
  const seen=new Set();const list=[];
  for(const item of input){
   const title=asText(item?.title,150);if(!title||seen.has(title))continue;
   seen.add(title);const node=card(item);if(node)list.push(node);
   if(list.length===3)break;
  }
  if(list.length)target.replaceChildren(...list);
 })
 .catch(()=>{/* Preserve source-labelled editorial fallback and user navigation. */})
 .finally(()=>clearTimeout(timeout));
})();
