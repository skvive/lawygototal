(() => {
  const replacements = {'콘텐츠 피드':'Content feed','쇼츠':'Shorts','창작자 스튜디오':'Creator studio','광고 안내':'Advertising','무료 회원가입':'Join for free','구글블로그':'Google Blogger','유튜브 영상':'YouTube videos','후원 콘텐츠':'Sponsored content','비공개 이메일 문의':'Private email inquiry','전화 연결 요청':'Request a call'};
  document.querySelectorAll('.nav a,#mobile-nav a').forEach(el=>{
    let ko = el.textContent.trim(); if(replacements[ko]) {el.dataset.i18n=ko;el.dataset.en=replacements[ko]}
  });
  document.querySelectorAll('form[data-pan-api]').forEach(form => {
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const status = form.querySelector('.pn-api-result');
      if(!form.reportValidity()) return;
      let payload=Object.fromEntries(new FormData(form).entries());
      for(const key of ['rights','terms','marketing'])payload[key]=Boolean(new FormData(form).get(key));
      if(form.dataset.contentType) payload.content_type=form.dataset.contentType;
      const button=form.querySelector('button[type=submit]');
      button.disabled=true;
      status.textContent='요청을 확인하고 있습니다…';
      try {
        const response=await fetch(form.dataset.panApi,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),credentials:'same-origin'});
        const data=await response.json();
        if(!response.ok) throw new Error(data.detail || data.message || '요청을 처리하지 못했습니다.');
        status.textContent=data.message||'접수되었습니다.';
        if(response.ok)form.reset();
      } catch(err) {
        if(location.protocol==='file:')status.textContent='이 페이지는 미리보기입니다. 실제 가입과 등록은 함께 제공된 API 서버를 실행해 주세요.';
        else status.textContent=err?.message||'현재 서비스를 연결할 수 없습니다.';
      } finally {button.disabled=false}
    });
  });
})();
// Approval-only live feed: no DOM HTML injection, no public account email.
(() => {
  const target=document.querySelector('[data-approved-feed]'); if(!target)return;
  const kind=target.dataset.approvedFeed||'all';
  fetch('/api/feed?kind='+encodeURIComponent(kind),{credentials:'omit'})
    .then(r=>r.ok?r.json():Promise.reject(new Error('offline')))
    .then(data=>{
      if(!Array.isArray(data.contents)||!data.contents.length){target.textContent='아직 승인된 공개 콘텐츠가 없습니다. 아래 시연용 콘텐츠를 확인하세요.';return}
      data.contents.forEach(x=>{
        const a=document.createElement('a');a.href=x.url;a.rel='noopener noreferrer';a.target='_blank';a.className='pn-feature';
        const title=document.createElement('h3');title.textContent=x.title;
        const p=document.createElement('p');p.textContent=x.summary||'원문 확인';
        const small=document.createElement('small');small.textContent=x.content_type==='video'?'YouTube 원문 ↗':'Google Blogger 원문 ↗';
        a.append(title,p,small);target.appendChild(a)
      });
    }).catch(()=>{target.textContent='실서비스 데이터가 연결되면 검증 완료된 콘텐츠가 여기에 표시됩니다.'});
})();
(() => {
 const form=document.querySelector('form[data-pan-api="/api/inquiry"]'); if(!form)return;
 const p=new URLSearchParams(location.search);const prof=p.get('profile');const method=p.get('method');
 if(prof&&Array.from(form.querySelector('[name="profile"]').options).some(o=>o.value===prof))form.querySelector('[name="profile"]').value=prof;
 if(['email','callback'].includes(method))form.querySelector('[name="method"]').value=method;
})();
