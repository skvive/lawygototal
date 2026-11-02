// Auth-gated personal note feed: never interpolate stored titles as HTML.
async function loadNotes(){
 const root=document.getElementById('note-feed');
 if(!root)return;
 const empty=(message,showLogin=true)=>{
  root.replaceChildren();
  const div=document.createElement('div');div.className='demo-note';
  const p=document.createElement('p');p.textContent=message;div.append(p);
  if(showLogin){const a=document.createElement('a');a.href='/dashboard';a.textContent='로그인 후 노트 관리 ↗';div.append(a)}
  root.append(div);
 };
 try{
  const response=await fetch('/api/posts?product=note&limit=20',{credentials:'same-origin'});
  if(response.status===401||response.status===403){empty('개인 노트는 로그인한 본인에게만 표시됩니다.');return}
  if(!response.ok)throw new Error('HTTP '+response.status);
  const data=await response.json();
  const items=Array.isArray(data.items)?data.items:[];
  root.replaceChildren();
  if(!items.length){empty('현재 볼 수 있는 개인 노트가 없습니다. 로그인 후 대시보드에서 노트를 작성할 수 있습니다.');return}
  for(const post of items){
   const row=document.createElement('article');row.className='issue-row';
   const block=document.createElement('div');
   const badge=document.createElement('b');badge.textContent=post.kind||'NOTE';
   const title=document.createElement('h3');title.textContent=post.title||'제목 없음';
   const date=document.createElement('p');date.textContent=String(post.updated_at||'').slice(0,10);
   block.append(badge,title,date);row.append(block);root.append(row);
  }
 }catch(e){empty('노트 목록을 불러오지 못했습니다. 로그인 상태와 네트워크 연결을 확인해 주세요.')}
}
loadNotes();