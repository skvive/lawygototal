(()=>{'use strict';
const $=id=>document.getElementById(id);
const csrf=()=>decodeURIComponent(document.cookie.split('; ').find(s=>s.startsWith('lawygo_cms_csrf='))?.slice('lawygo_cms_csrf='.length)||'');
let role='',previewHash='';
const msg=text=>$('message').textContent=text;
async function api(path,options={}){const r=await fetch(path,{cache:'no-store',credentials:'same-origin',...options});const x=await r.json().catch(()=>({}));if(!r.ok)throw Error(x.detail||'요청 오류 '+r.status);return x;}
const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf()},body:JSON.stringify(body)});
function todayKst(){return new Date(Date.now()+9*3600000).toISOString().slice(0,10);}
function nextKst(){return new Date(Date.now()+9*3600000+86400000).toISOString().slice(0,10);}
function safeUrl(raw){try{const u=new URL(raw);return u.protocol==='https:'?u.toString():''}catch{return ''}}
function card(section,values={}){
 const parent=$(section+'-list');if(parent.children.length>=5)throw Error('분야별 기사는 최대 5건입니다.');
 const div=document.createElement('article');div.className='story';div.innerHTML='<div class="item-head">EDITORIAL STORY</div><button type="button" class="remove" title="기사 제거" aria-label="기사 제거">×</button><label>기사 제목</label><input class="title" maxlength="160" minlength="8" placeholder="검증된 뉴스 제목" required><label>핵심 요약 및 영향</label><textarea class="summary" rows="3" maxlength="350" minlength="15" placeholder="사실·발표일·경제 또는 법률적 의미" required></textarea><div class="two"><div><label>언론사 / 기관</label><input class="source" maxlength="80" minlength="2" placeholder="공식 발표 기관" required></div><div><label>원문 URL (HTTPS)</label><input class="url" type="url" maxlength="600" placeholder="https://..." required></div></div>';
 for(const k of ['title','summary','source','url'])div.querySelector('.'+k).value=values[k]||'';
 div.querySelector('.remove').addEventListener('click',()=>{if(parent.children.length<=1){msg('분야별 최소 1건은 필요합니다.');return}div.remove();renumber(section);previewHash=''});
 div.addEventListener('input',()=>previewHash='');
 parent.append(div);renumber(section);
}
function renumber(section){[...$(section+'-list').children].forEach((x,i)=>x.querySelector('.item-head').textContent=(section==='us'?'US ECONOMY':'KOREA POLICY')+' / '+String(i+1).padStart(2,'0'))}
function stories(section){
 return [...$(section+'-list').children].map(el=>{
  const obj=Object.fromEntries(['title','summary','source','url'].map(key=>[key,el.querySelector('.'+key).value.trim()]));
  if(obj.title.length<8||obj.summary.length<15||obj.source.length<2||!safeUrl(obj.url))throw Error('기사 제목·15자 이상의 요약·출처·HTTPS 원문 주소를 확인하세요.');
  obj.url=safeUrl(obj.url);return obj;
 });
}
function payload(){
 const local=$('scheduled').value;
 if(!local)throw Error('예약발송 시각을 지정하세요.');
 const date=new Date(local+':00+09:00');
 if(isNaN(date.getTime()))throw Error('예약 발송일 형식을 확인하세요.');
 const result={issue_month:$('month').value,subject:$('subject').value.trim(),intro:$('intro').value.trim(),us:stories('us'),kr:stories('kr'),editorial_note:$('note').value.trim(),scheduled_at:date.toISOString()};
 if(!result.issue_month||result.subject.length<8||result.intro.length<30)throw Error('발행월·8자 이상의 제목·30자 이상의 서문을 입력하세요.');
 if(local.slice(0,7)!==result.issue_month)throw Error('예약 발송일과 발행월을 일치시켜 주세요.');
 if(date.getTime()<=Date.now())throw Error('예약발송은 현재 시각 이후여야 합니다.');
 return result;
}
function fill(d){
 $('month').value=d.issue_month||'';
 $('subject').value=d.subject||'';
 $('intro').value=d.intro||'';
 $('note').value=d.editorial_note||'';
 if(d.scheduled_at){const utc=new Date(d.scheduled_at).getTime()+9*3600000;$('scheduled').value=new Date(utc).toISOString().slice(0,16)}
 for(const section of ['us','kr']){$(section+'-list').replaceChildren();for(const item of (d[section]||[]).slice(0,5))card(section,item);if(!$(section+'-list').children.length)card(section)}
 previewHash='';
}
function busy(button,fn){button.disabled=true;return Promise.resolve().then(fn).catch(e=>msg(e.message)).finally(()=>button.disabled=false)}
async function loadStatus(){
 const [stats,queue,issues]=await Promise.all([api('/api/growth/newsletter/admin/stats'),api('/api/growth/newsletter/admin/queue'),api('/api/growth/newsletter/monthly/issues')]);
 $('count').textContent=(stats.counts&&stats.counts.active)||0;
 $('queue-count').textContent=(queue.counts||[]).filter(x=>x.job_type==='issue'&&x.status==='queued').reduce((n,x)=>n+x.n,0);
 const history=$('history');history.replaceChildren();
 for(const issue of issues.items||[]){const node=document.createElement('div');node.className='hist-item';node.textContent=issue.issue_month+' · '+issue.subject+' · 발송 '+issue.sent+' / 대기 '+issue.queued;history.append(node)}
 if(!history.children.length)history.textContent='발행된 뉴스레터가 없습니다.';
 $('issue-status').textContent=issues.items?.some(x=>x.issue_month===$('month').value)?'발행 등록됨':'편집 중';
 if(!queue.smtp_configured||!queue.issue_send_enabled)msg('현재 실제 발송 잠금 상태입니다. 원고 작업·미리보기·대기열 등록은 가능합니다.');
}
$('month').value=nextKst().slice(0,7);
$('scheduled').value=nextKst()+'T10:00';
$('subject').value='LAWYGO JOURNAL | '+$('month').value+' 미국 경제·한국 법률정책 브리핑';
card('us');card('kr');
for(const section of ['us','kr'])$(section+'-add').addEventListener('click',()=>{try{card(section);previewHash=''}catch(e){msg(e.message)}});
$('month').addEventListener('change',()=>{const current=$('scheduled').value;if(current)$('scheduled').value=$('month').value+current.slice(7);$('subject').value='LAWYGO JOURNAL | '+$('month').value+' 미국 경제·한국 법률정책 브리핑';previewHash='';loadStatus().catch(e=>msg(e.message))});
$('save').addEventListener('click',e=>busy(e.currentTarget,async()=>{const r=await post('/api/growth/newsletter/monthly/draft',payload());msg('편집 초안을 저장했습니다. '+r.saved_at)}));
$('preview').addEventListener('click',e=>busy(e.currentTarget,async()=>{const data=payload();const result=await post('/api/growth/newsletter/monthly/preview',data);$('email-preview').srcdoc=result.html;previewHash=JSON.stringify(data);msg('이메일 HTML 및 한국어 본문 미리보기를 생성했습니다. 제목·출처·링크를 검토하세요.');$('email-preview').scrollIntoView({block:'nearest',behavior:'smooth'});}));
$('queue').addEventListener('click',e=>busy(e.currentTarget,async()=>{
 if(role!=='admin')throw Error('최종 발송 승인에는 관리자 권한이 필요합니다.');
 const data=payload();
 if(previewHash!==JSON.stringify(data))throw Error('수정된 원고를 다시 미리보기한 후 승인하세요.');
 if(!$('approved').checked)throw Error('출처 검증 및 수신 대상 승인에 체크하세요.');
 if(!confirm(data.issue_month+' 월간호를 '+$('scheduled').value+' (KST)부터 발송하도록 승인·대기열에 등록할까요?'))return;
 const r=await post('/api/growth/newsletter/monthly/queue',{...data,confirmed_preview:true});
 msg('승인 완료: '+r.queued+'명의 인증 구독자를 예약 발송 대기열에 추가했습니다. 실제 발송은 이메일 서버 설정에 따릅니다.');
 await loadStatus();
}));
$('fetch-news').addEventListener('click',e=>busy(e.currentTarget,async()=>{
 const data=await api('/api/journal/feed');
 let added=0;
 for(const section of ['us','kr']){
  const list=(data[section]||[]).filter(x=>safeUrl(x.url)).slice(0,3);
  if(!list.length)continue;
  $(section+'-list').replaceChildren();
  for(const x of list){card(section,{title:String(x.title||'').slice(0,160),summary:String(x.summary||x.title||'').slice(0,350),source:String(x.source||'').slice(0,80),url:x.url});added++}
 }
 if(!added)throw Error('현재 외부 RSS 기사 목록을 불러올 수 없습니다. 직접 입력하세요.');
 msg(added+'건의 참고 뉴스가 입력됐습니다. 주제 적합성·실제 발표일·내용을 반드시 재검증하세요.');
}));
(async()=>{try{const me=await api('/api/me');role=me.role;if(!['admin','editor'].includes(role))throw Error('편집자 또는 관리자 권한이 필요합니다.');if(role!=='admin')$('queue').disabled=true;
 const saved=await api('/api/growth/newsletter/monthly/draft?month='+encodeURIComponent($('month').value));if(saved.draft)fill(saved.draft);
 await loadStatus();if(!saved.draft)msg('뉴스 수집 후 개별 기사 출처를 확인하고 월간호를 작성하세요.');
}catch(e){msg('로그인 또는 접근 권한을 확인하세요: '+e.message+' · 관리자 페이지 /dashboard')}})();
})();