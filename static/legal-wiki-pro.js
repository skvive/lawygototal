"use strict";
const form=document.getElementById("search"), statusEl=document.getElementById("status"), items=document.getElementById("items");
let seq=0;
form.addEventListener("submit",async e=>{
 e.preventDefault();const token=++seq,q=document.getElementById("q").value.trim(),mode=document.getElementById("mode").value;items.replaceChildren();statusEl.textContent="검색 중";
 if(q.length<2){statusEl.textContent="검색어는 두 글자 이상 입력하세요.";return;}
 const url="/api/wiki/v2/"+(mode==="precedents"?"precedents":"search")+"?"+new URLSearchParams({q,...(mode==="beta"?{beta:"true"}:{})});
 try {const res=await fetch(url,{credentials:"same-origin",cache:"no-store"});if(token!==seq)return;
 if(!res.ok){statusEl.textContent=res.status===401?"로그인이 필요합니다.":res.status===403?"내부 검수 권한이 필요합니다.":"전문 법률위키 준비 중입니다.";return;}
 const data=await res.json();if(token!==seq)return;
 statusEl.textContent=(data.notice||"검증 판례 · 키워드 검색")+" / "+data.items.length+"건";
 for(const r of data.items){const card=document.createElement("article"),title=document.createElement("h2"),body=document.createElement("p"),meta=document.createElement("small");title.textContent=r.title||r.case_number||"";body.textContent=r.summary||r.holding||"";meta.textContent=[r.category,r.court,r.legal_as_of||r.decided_on,r.review_notice].filter(Boolean).join(" · ");card.append(title,body,meta);if(r.source_url){try{const u=new URL(r.source_url);if(u.protocol==="https:"&&["law.go.kr","www.law.go.kr","lx.scourt.go.kr","www.scourt.go.kr"].includes(u.hostname)){const a=document.createElement("a");a.href=u.href;a.textContent=" 공식 원문";a.target="_blank";a.rel="noopener noreferrer";card.append(a)}}catch{}}items.append(card);}
 }catch{if(token===seq)statusEl.textContent="검색 연결 오류. 다시 시도하세요.";}
});
