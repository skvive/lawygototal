(()=>{
 document.querySelectorAll('[data-open-partner-popup]').forEach(a=>a.addEventListener('click',e=>{
  e.preventDefault(); const href=new URL(a.getAttribute('href'),location.href).toString();
  // Desktop: real popup. Mobile browsers commonly display as new tab.
  const win=window.open(href,'LAWYGO_Partnership','width=720,height=850,scrollbars=yes,resizable=yes');
  if(!win) location.href=href; else win.focus();
 }));
 document.querySelector('#closePop')?.addEventListener('click',()=>{if(window.opener)window.close();else location.href='partnership.html'});
 const f=document.querySelector('#partnerForm');if(!f)return;
 f.addEventListener('submit',e=>{
  e.preventDefault();if(!f.reportValidity())return;
  const d=new FormData(f);const email=String(d.get('email')||'').trim();
  const lines=["LAWYGO PARTNERSHIP 제휴 문의",'',`법무법인: ${d.get('firm')}`,`담당자: ${d.get('name')}`,`직책: ${d.get('title')||'-'}`,`연락처: ${d.get('phone')}`,`회신 이메일: ${email}`,`관심 협력 분야: ${d.getAll('topics').join(', ')||'협의 필요'}`,'','[문의 내용]',String(d.get('message')||''),'','개인정보 연락 목적 동의: 예'];
  const subject='[LAWYGO PARTNERSHIP] '+String(d.get('firm')||'법무법인')+' 제휴/MOU 문의';
  const url='mailto:sk@terrabridge.us?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(lines.join('\n'));
  document.querySelector('#result').textContent='기본 이메일 앱을 여는 중입니다. 앱에서 ‘보내기’를 눌러야 문의가 접수됩니다. 앱이 열리지 않으면 sk@terrabridge.us로 직접 보내주세요.';
  location.href=url;
 });
})();