/* NOTE public search & drafting console, grounded in original lawygo AI workspace routes. */
(() => {
 'use strict';
 const $=id=>document.getElementById(id),root=$('lnw-chat-messages'),form=$('lnw-chat-form'),input=$('lnw-chat-input');
 if(!root||!form||!input)return;
 const modes={research:'법률·판례 검색',case:'사건·판례 근거',draft:'법률문서 초안',extract:'문서 발췌 실험'};
 const originals={research:'ai_search',case:'case_search',draft:'doc_draft',extract:'doc_summary'};
 let mode='research',sources=[],transcript=[],draft='',running=false;
 const el=(tag,cls,txt)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(txt!=null)x.textContent=String(txt);return x};
 const setStatus=s=>{if($('lnw-chat-status'))$('lnw-chat-status').textContent=s};
 const safe=raw=>{try{const u=new URL(String(raw||''),location.origin);return u.protocol==='https:'||u.origin===location.origin?u.href:''}catch{return ''}};
 const origUrl=()=> 'https://lawygo.vercel.app/board/ai/'+originals[mode];
 function bubble(role,content){
  $('lnw-chat-welcome')?.remove();
  const box=el('article','lawygo-ai-message '+role);
  if(role==='assistant')box.append(el('strong',null,'LAWYGO · 공개자료 작업 결과'));
  box.append(el('div',null,content));
  if(role==='assistant'){
   const a=el('a',null,'실제 AI 프로그램에서 실행 ↗');
   a.href=origUrl();a.target='_blank';a.rel='noopener noreferrer';a.style.cssText='display:block;margin-top:10px;color:#a64e70;font-size:11px;font-weight:800';
   box.append(a);
  }
  root.append(box);root.scrollTop=root.scrollHeight;transcript.push({role,text:content});
 }
 function sourceList(rows){
  sources=rows.slice(0,12);const panel=$('lnw-chat-sources');if(!panel)return;
  panel.replaceChildren();
  if(!sources.length){panel.append(el('p','lawygo-ai-rail-empty','연결된 공개자료가 없습니다. 다른 법률 용어로 검색해 보세요.'));return}
  sources.forEach((s,i)=>{
   const card=el('article','lawygo-ai-source-card');
   card.append(el('small',null,'출처 '+(i+1)+' · '+s.source),el('strong',null,s.title));
   if(s.summary)card.append(el('small',null,s.summary.slice(0,115)));
   const url=safe(s.url);
   if(url){const link=el('a',null,'원문 열기 ↗');link.href=url;link.target='_blank';link.rel='noopener noreferrer';card.append(link)}
   panel.append(card);
  });
 }
 function putInEditor(value,title){
  const field=$('noteDraftContent'),name=$('noteDraftTitle');
  if(!field||!name){setStatus('NOTE 문서 편집기를 찾지 못했습니다.');return}
  if(field.value.trim()&&!confirm('기존 편집 내용 끝에 추가할까요?'))return;
  name.value=(title||'법률 리서치 메모').slice(0,120);
  field.value+=(field.value?'\n\n':'')+value;
  field.dispatchEvent(new Event('input',{bubbles:true}));
  $('note-editor')?.scrollIntoView({behavior:'smooth',block:'start'});
  setStatus('NOTE 초안 편집기에 반영했습니다. 복사 또는 TXT로 내보내세요.');
 }
 function makeDraft(query){
  return '[법률문서 구조화 초안 · 편집용]\n\n작성 목적: '+query.slice(0,350)+
   '\n\n[1. 사실관계]\n- 사실 및 자료 확인 필요\n\n[2. 쟁점]\n- 주요 법률적 쟁점 입력\n\n[3. 관련 법령·판례]\n- 원문·최신성 확인 필요\n\n[4. 검토 의견]\n- 담당 전문가 작성\n\n[5. 추가 확인사항]\n- 보완 자료 입력\n\n※ AI 법률판단이 아닌 편집 가능한 문서 템플릿입니다.';
 }
 function extract(text){
  const fragments=text.replace(/\r/g,'').split(/(?<=[.!?。])\s+|\n+/).map(s=>s.trim()).filter(s=>s.length>16).slice(0,5);
  return '원문 발췌 실험 · 법률 판단 아님\n원문 '+text.length+'자 / 발췌 '+fragments.length+
   '문장\n\n'+fragments.map((s,i)=>(i+1)+'. '+s.slice(0,330)).join('\n\n')+
   '\n\n※ 문장 일부를 원문에서 그대로 가져온 발췌입니다. 실제 AI/OCR 분석은 인증된 로이고에서 실행하세요.';
 }
 async function findPublic(query){
  const endpoints=[
   '/api/wiki/search?'+new URLSearchParams({q:query.slice(0,100),limit:'6'}),
   '/api/pan/content?'+new URLSearchParams({type:'all',q:query.slice(0,100),limit:'24'})
  ];
  const results=await Promise.allSettled(endpoints.map(url=>fetch(url,{credentials:'omit'})));
  const found=[],seen=new Set;
  for(let i=0;i<results.length;i++){
   const p=results[i];if(p.status!=='fulfilled'||!p.value.ok)continue;
   let obj;try{obj=await p.value.json()}catch{continue}
   for(const x of (obj.items||[])){
    const url=safe(x.url||x.external_url||(i===0?'/p/wiki?q='+encodeURIComponent(query):''));
    if(!url||seen.has(url))continue;
    seen.add(url);
    found.push({title:x.title_ko||x.title||'법률 자료',summary:x.summary_ko||x.summary||'',
      url,source:i===0?'LAWYGO 법률백과':x.source||'공개 법률자료'});
   }
  }
  return found.slice(0,12);
 }
 async function submit(){
  if(running)return;const q=input.value.trim();
  if(q.length<2){setStatus('최소 2자 이상 입력해 주세요.');return}
  running=true;$('lnw-chat-send').disabled=true;input.value='';
  bubble('user',q);setStatus(modes[mode]+' 처리 중…');
  try{
   if(mode==='draft'||mode==='extract'){
    sourceList([]);draft=mode==='draft'?makeDraft(q):extract(q);bubble('assistant',draft);
    setStatus('브라우저 안에서 처리했습니다. 서버로 문서 내용을 보내지 않았습니다.');
   }else{
    const rows=await findPublic(q);
    sourceList(rows);
    draft='[리서치 질문]\n'+q+'\n\n[원문 출처]\n'+rows.map((x,i)=>(i+1)+'. '+x.title+'\n'+x.url).join('\n')+
      '\n\n[담당 전문가의 법률 검토]\n';
    const content=rows.length?rows.length+'개의 공개자료를 찾았습니다.\n\n'+
      rows.slice(0,5).map((s,i)=>'[출처 '+(i+1)+'] '+s.title+'\n'+s.source).join('\n\n')+
      '\n\n오른쪽 원문 링크를 열어 법역·개정일을 확인하세요. 이는 검색 결과이지 AI 법률 의견이 아닙니다.':
      '해당 검색어로 공개 게시물을 찾지 못했습니다. 다른 키워드를 사용하거나 실제 AI 워크스페이스를 실행해 주세요.';
    bubble('assistant',content);setStatus('공개자료 '+rows.length+'건 검색 완료 / AI 판단 아님');
   }
  }catch(e){bubble('assistant','검색 중 연결 문제가 발생했습니다. 원본 인증형 AI 프로그램을 이용하거나 네트워크를 확인하세요.');setStatus('연결 오류')}
  finally{running=false;$('lnw-chat-send').disabled=false;input.focus()}
 }
 form.addEventListener('submit',e=>{e.preventDefault();submit()});
 input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();submit()}});
 document.querySelectorAll('[data-lnw-mode]').forEach(btn=>btn.addEventListener('click',()=>{
  mode=btn.dataset.lnwMode||'research';
  document.querySelectorAll('[data-lnw-mode]').forEach(x=>{x.classList.toggle('is-active',x===btn);x.setAttribute('aria-pressed',x===btn?'true':'false')});
  $('lnw-chat-mode-label').textContent=modes[mode]+(mode==='research'||mode==='case'?' · 공개 API':' · 로컬 편집');
  input.placeholder=mode==='extract'?'문장 발췌할 원문 텍스트를 입력하세요 (로컬 처리)':mode==='draft'?
   '작성 목적을 입력하면 법률문서 형식의 빈 편집 템플릿을 만듭니다.':'검색할 법률 쟁점이나 키워드를 입력하세요.';
  setStatus(modes[mode]+' 모드 선택');input.focus();
 }));
 document.querySelectorAll('[data-lnw-example]').forEach(b=>b.addEventListener('click',()=>{
  input.value=b.dataset.lnwExample||'';input.focus();setStatus('예시 입력 완료. 전송하여 직접 실험할 수 있습니다.');
 }));
 $('lnw-chat-new')?.addEventListener('click',()=>{
  if(transcript.length&&!confirm('현재 임시 대화와 검색 결과를 지울까요?'))return;
  transcript=[];draft='';root.replaceChildren();sourceList([]);bubble('assistant','새 작업을 시작했습니다. 질문이나 법률 자료를 입력하세요.');setStatus('새 임시 작업 · 자동 저장 없음');input.focus();
 });
 $('lnw-chat-to-draft')?.addEventListener('click',()=>{
  if(!draft){setStatus('먼저 작업을 실행해 주세요.');return}
  putInEditor(draft,mode==='draft'?'법률 검토 문서 초안':'법률 리서치 메모');
 });
 $('lnw-chat-copy')?.addEventListener('click',async()=>{
  const body=transcript.map(x=>(x.role==='user'?'[질문]':'[검색/편집 결과]')+'\n'+x.text).join('\n\n')+
  '\n\n[원문 출처]\n'+sources.map(x=>x.title+'\n'+x.url).join('\n');
  if(!body.trim()){setStatus('복사할 대화가 없습니다.');return}
  try{await navigator.clipboard.writeText(body);setStatus('대화와 출처를 클립보드에 복사했습니다.')}
  catch{setStatus('클립보드 복사가 차단됐습니다. 브라우저 권한을 확인하세요.')}
 });
})();
