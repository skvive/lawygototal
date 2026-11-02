(()=>{
'use strict';
const $=id=>document.getElementById(id);
const csrf=()=>decodeURIComponent(document.cookie.split('; ').find(s=>s.startsWith('lawygo_cms_csrf='))?.split('=').slice(1).join('=')||'');
const cell=(row,value)=>{const x=document.createElement('td');x.textContent=String(value??'-');row.append(x);return x;};
const msg=v=>$('message').textContent=v;
const date=v=>v?String(v).replace('T',' ').slice(0,16):'-';
async function api(path,opts={}){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',...opts});const j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.detail||'요청 실패: '+r.status);return j}
const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf()},body:JSON.stringify(body)});
async function refresh(){
 try{
 const [s,q,stats]=await Promise.all([api('/api/growth/newsletter/admin/subscribers'),api('/api/growth/newsletter/admin/queue'),api('/api/growth/newsletter/admin/stats')]);
 const counts=stats.counts||{};
 const nums=[['총 주소록',Object.values(counts).reduce((t,n)=>t+Number(n),0)],['인증 완료',counts.active||0],['인증 대기',counts.pending||0],['발송 대기',q.counts.filter(x=>x.status==='queued').reduce((n,x)=>n+x.n,0)]];
 $('stats').replaceChildren();
 for(const [label,value] of nums){const d=document.createElement('div');d.className='stat';const a=document.createElement('small');a.textContent=label;const b=document.createElement('strong');b.textContent=value;d.append(a,b);$('stats').append(d)}
 $('subscribers').replaceChildren();
 for(const x of s.items){const tr=document.createElement('tr');cell(tr,x.email);cell(tr,({pending:'인증 대기',active:'수신 동의 완료',unsubscribed:'수신 거부'})[x.status]||x.status);cell(tr,date(x.consent_at));$('subscribers').append(tr)}
 $('jobs').replaceChildren();
 for(const x of q.jobs){const tr=document.createElement('tr');cell(tr,x.job_type==='confirmation'?'인증 메일':'뉴스레터');cell(tr,x.status);cell(tr,x.attempts);cell(tr,date(x.created_at));const td=document.createElement('td');if(x.status==='failed'){const b=document.createElement('button');b.className='subtle';b.textContent='재등록';b.addEventListener('click',async()=>{if(!confirm('중복 수신 가능성을 확인하고 재등록하시겠습니까?'))return;try{await post('/api/growth/newsletter/admin/requeue',{job_key:x.job_key});msg('실패 건을 다시 등록했습니다.');await refresh()}catch(e){msg(e.message)}});td.append(b)}tr.append(td);$('jobs').append(tr)}
 $('notice').textContent='SMTP: '+(q.smtp_configured?'설정됨':'미설정')+' · 뉴스레터 본문 발송: '+(q.issue_send_enabled?'승인 후 가능':'잠금 · 대기열 저장만 가능');
 }catch(e){msg(String(e.message))}
}
$('refresh').addEventListener('click',refresh);
$('dispatch').addEventListener('click',async e=>{const b=e.currentTarget;b.disabled=true;try{const x=await post('/api/growth/newsletter/admin/dispatch',{limit:20});msg('발송 '+x.sent+'건 · 실패 '+x.failed+'건 · 남은 대기 '+x.remaining+'건');await refresh()}catch(err){msg(err.message)}finally{b.disabled=false}});
$('compose').addEventListener('submit',async e=>{e.preventDefault();if(!confirm('이메일 원고와 대상 확인을 마치셨습니까? 발송 대기열에 추가합니다.'))return;const b=e.currentTarget.querySelector('button');b.disabled=true;try{const x=await post('/api/growth/newsletter/admin/queue-issue',{subject:$('subject').value,body:$('body').value,confirmed_preview:$('approved').checked});msg('승인된 원고 '+x.queued+'건을 발송 대기열에 등록했습니다. 아직 메일을 보내지 않았습니다.');e.currentTarget.reset();await refresh()}catch(err){msg(err.message)}finally{b.disabled=false}});
(async()=>{try{const u=await api('/api/me');if(u.role!=='admin')throw Error('관리자 권한이 필요합니다.');$('workspace').hidden=false;await refresh()}catch(e){$('notice').textContent='관리자 CMS 로그인 후 이용하세요. '+e.message+' ';const a=document.createElement('a');a.href='/dashboard';a.textContent='로그인 화면';$('notice').append(a)}})();
})();