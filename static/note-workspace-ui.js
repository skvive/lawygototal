// Browser-only scratchpad. Does not persist legal text or call external APIs.
// Actual authenticated AI/encyclopedia actions live on original LAWYGO SaaS.
(() => {
 const setup=()=>{
  const title=document.getElementById('noteDraftTitle');
  const area=document.getElementById('noteDraftContent');
  const count=document.getElementById('noteEditorCount');
  const status=document.getElementById('noteEditorStatus');
  if(!title||!area||!count||!status)return;
  const templates={
    blank:{name:'새 법률 메모',body:''},
    case:{name:'사건 검토 메모',body:'[검토 목적]\n\n[확인된 사실]\n\n[쟁점]\n\n[관련 법령·판례]\n\n[검토 의견]\n\n[추가 확인사항]\n'},
    evidence:{name:'증거 정리표',body:'[증거 목록]\n1. 증거명:\n   입증 취지:\n   출처 및 수집일:\n   제출 여부:\n\n[원문 확인 및 보완]\n'},
    research:{name:'법률 리서치',body:'[리서치 질문]\n\n[관련 법령]\n\n[관련 판례]\n\n[법적 쟁점]\n\n[출처 URL / 확인일]\n\n[결론 — 검토 필요]\n'}
  };
  const update=()=>{count.textContent=area.value.length.toLocaleString('ko-KR')+'자';status.textContent='임시 편집 중 · 자동 저장 안 함'};
  const setTemplate=(key)=>{
    const t=templates[key];if(!t)return;
    if((area.value.trim()||title.value.trim()!=='새 법률 메모')&&!confirm('현재 임시 초안을 지우고 새 형식을 불러올까요?'))return;
    title.value=t.name;area.value=t.body;update();area.focus();
  };
  document.querySelectorAll('[data-note-template]').forEach(btn=>btn.addEventListener('click',()=>setTemplate(btn.dataset.noteTemplate)));
  area.addEventListener('input',update);title.addEventListener('input',()=>{status.textContent='임시 편집 중 · 자동 저장 안 함'});
  document.getElementById('noteCopyDraft')?.addEventListener('click',async()=>{
    const text=title.value.trim()+'\n\n'+area.value;
    try{await navigator.clipboard.writeText(text);status.textContent='클립보드에 복사했습니다'}
    catch{area.focus();area.select();status.textContent='자동 복사가 차단됐습니다. 텍스트를 선택해 복사하세요'}
  });
  document.getElementById('noteExportDraft')?.addEventListener('click',()=>{
    const clean=(title.value.trim()||'lawygo-note').replace(/[\\/:*?"<>|]/g,'_').slice(0,65);
    const text=(title.value||'법률 메모')+'\r\n\r\n'+area.value;
    const blob=new Blob(['\ufeff'+text],{type:'text/plain;charset=utf-8'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=clean+'.txt';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
    status.textContent='TXT 파일을 내보냈습니다. 서버에는 저장하지 않았습니다';
  });
  document.getElementById('noteClearDraft')?.addEventListener('click',()=>{
    if((title.value.trim()||area.value.trim())&&!confirm('작성 중인 임시 메모를 지울까요?'))return;
    title.value='새 법률 메모';area.value='';update();status.textContent='초안을 비웠습니다';
  });
  update();status.textContent='브라우저 임시 편집 · 자동 저장 안 함';
 };
 document.readyState==='loading'?document.addEventListener('DOMContentLoaded',setup,{once:true}):setup();
})();