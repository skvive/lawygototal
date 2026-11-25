/* LAWYGO JOURNAL: original Newswire artwork only. No fabricated media or placeholder image. */
const el = (tag, text, className) => {
  const n = document.createElement(tag);
  if(text != null && text !== '') n.textContent = String(text);
  if(className) n.className = className;
  return n;
};
function safeJournalUrl(raw) {
  try {
    const u=new URL(String(raw||''), location.origin);
    return u.protocol==='https:' ? u.href : null;
  } catch {return null;}
}
function sourceImage(raw) {
  const url=safeJournalUrl(raw);
  if(!url) return null;
  const u=new URL(url);
  // Newswire feed occasionally reports an empty "/thumb/.jpg" path.
  if(!u.hostname.endsWith('.newswire.co.kr') &&
     u.hostname!=='newswire.co.kr') return null;
  if(!/\.(?:jpe?g|png|webp)$/i.test(u.pathname)) return null;
  if(/\/thumb\/\.(?:jpe?g|png|webp)$/i.test(u.pathname)) return null;
  return url;
}
const issueOverlay=document.getElementById('journal-issue-overlay');
function openIssue(item) {
  if(!issueOverlay) return;
  document.getElementById('issue-kicker').textContent=(item.desk||'뉴스와이어')+' · '+(item.source||'뉴스와이어');
  document.getElementById('issue-title').textContent=item.title;
  document.getElementById('issue-meta').textContent=item.published||'';
  document.getElementById('issue-body').textContent=item.summary||item.title;
  const link=document.getElementById('issue-source');
  const url=safeJournalUrl(item.url);
  if(url){link.href=url;link.style.display='inline-flex';link.textContent='원문 ↗'}
  else link.style.display='none';
  issueOverlay.classList.add('open');
  issueOverlay.setAttribute('aria-hidden','false');
}
document.getElementById('journal-issue-close')?.addEventListener('click',()=>{
  issueOverlay?.classList.remove('open');
  issueOverlay?.setAttribute('aria-hidden','true');
});
function sourcePhoto(item, className) {
  const img=el('img',null,className);
  img.src=item.image;
  img.alt=item.title+' · 뉴스와이어 원문 사진';
  img.loading='lazy';
  img.decoding='async';
  img.referrerPolicy='no-referrer';
  img.addEventListener('error',()=>{
    // On unavailable original images, remove the entire photo-card, never
    // swap in generic imagery. Keep heading/section visibility clean.
    const card=img.closest('[data-source-photo-card]');
    card?.remove();
    if(card?.parentElement?.children.length===0) card.parentElement.hidden=true;
  },{once:true});
  return img;
}
function articleCard(item, rubric, kind='tile') {
  const a=el('a',null,kind);
  a.href=safeJournalUrl(item.url)||'#journal-front-left';
  a.target='_blank';a.rel='noopener noreferrer';
  a.dataset.sourcePhotoCard='true';
  a.append(el('span',rubric||'NEWSWIRE · PRESS RELEASE','rubric'),sourcePhoto(item,kind==='tile'?'journal-source-photo':'journal-side-photo'),
    el('h3',item.title),
    el('p',item.summary||''),
    el('span',item.source||'뉴스와이어','byline'));
  return a;
}
function leadBlock(item) {
  const wrap=el('a',null,'journal-source-lead');
  wrap.href=safeJournalUrl(item.url)||'#journal-front-left';
  wrap.target='_blank';wrap.rel='noopener noreferrer';
  wrap.dataset.sourcePhotoCard='true';
  wrap.append(el('span','NEWSWIRE / PHOTO STORY','rubric'),
    el('h1',item.title,'headline'),
    el('p',item.summary||'','deck'),
    sourcePhoto(item,'lead-photo'),
    el('p',(item.source||'뉴스와이어')+' · '+(item.published||''),'caption'));
  return wrap;
}
function wireItem(item) {
  const a=el('a',null,'wire-item');
  a.href=safeJournalUrl(item.url)||'#journal-front-left';
  a.target='_blank';a.rel='noopener noreferrer';
  a.dataset.sourcePhotoCard='true';
  a.append(sourcePhoto(item,'journal-wire-photo'),el('small',item.source||'뉴스와이어'),el('strong',item.title));
  return a;
}
function showSourceSection(id,items,render) {
  const root=document.getElementById(id);
  if(!root) return;
  root.replaceChildren();
  if(!items.length){root.hidden=true;return}
  root.hidden=false;
  items.forEach((item,i)=>root.append(render(item,i)));
}
async function boot() {
  const [journal,pan]=await Promise.all([
    fetch('/api/journal/feed',{cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({})),
    fetch('/api/pan/content?type=all&limit=100',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('PAN media '+r.status);return r.json()})
  ]);
  const images=(Array.isArray(pan.items)?pan.items:[])
    .filter(x=>x && x.content_type==='newswire' && x.title && safeJournalUrl(x.url))
    .map(x=>({...x,image:sourceImage(x.thumb_url)}))
    .filter(x=>x.image);
  const unique=[];const seen=new Set();
  for(const item of images){if(seen.has(item.url))continue;seen.add(item.url);unique.push(item);}
  // Newswire articles with an actual source-provided image take exclusive
  // editorial priority. Image-less Fed/other RSS remain off the home page.
  unique.sort((a,b)=>(Date.parse(b.published)||0)-(Date.parse(a.published)||0));
  const lead=unique[0];
  const rest=unique.slice(1);
  document.getElementById('journal-edition-meta').textContent=
    new Date().toISOString().slice(0,10)+' · IMAGE-VERIFIED NEWSWIRE';
  showSourceSection('journal-front-left',rest.slice(0,2),(x)=>articleCard(x,'LATEST NEWSWIRE','side-story'));
  showSourceSection('journal-lead',lead?[lead]:[],leadBlock);
  const right=document.getElementById('journal-right');
  if(right) {
    right.replaceChildren();
    const headline=el('div',null,'key-issues');
    headline.append(el('div',"NEWSWIRE · EDITOR'S PICKS",'rubric'));
    const ol=el('ol');
    rest.slice(2,7).forEach((item,i)=>{
      const li=el('li');
      const link=el('a',item.title);
      link.href=safeJournalUrl(item.url);link.target='_blank';link.rel='noopener noreferrer';
      li.append(el('span',String(i+1).padStart(2,'0'),'num'),link);
      ol.append(li);
    });
    if(ol.children.length){headline.append(ol);right.append(headline);}
    right.hidden=!ol.children.length;
  }
  showSourceSection('journal-wire-kr',unique.slice(0,6),wireItem);
  showSourceSection('journal-wire-us',unique.slice(6,12),wireItem);
  showSourceSection('journal-row-editors',unique.slice(0,3),(x)=>articleCard(x,'NEWSWIRE · FEATURED'));
  showSourceSection('journal-row-law',unique.slice(3,6),(x)=>articleCard(x,'LAW & POLICY · NEWSWIRE'));
  // Empty section headings must not create long blank panels.
  ['journal-row-editors','journal-row-law'].forEach(id=>{
    const root=document.getElementById(id);
    if(root?.hidden) root.previousElementSibling?.setAttribute('hidden','');
  });
  const disclaimer=document.getElementById('journal-disclaimer');
  if(disclaimer) disclaimer.textContent=(journal.disclaimer||'')+
    ' · 홈의 사진은 뉴스와이어 원문에 연결된 실제 대표 이미지만 사용합니다.';
}
const nl = document.getElementById("newsletterSignupJournal");
nl?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("journal-nl-status");
  status.textContent = "처리 중…";
  try {
    const r = await fetch("/api/growth/newsletter/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("journal-nl-email").value,
        consent: document.getElementById("journal-nl-consent").checked,
      }),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : "실패");
    status.textContent = j.message;
    nl.reset();
  } catch (err) {
    status.textContent = err.message;
  }
});

boot().catch((err) => {
  console.error(err);
  document.getElementById("journal-disclaimer").textContent =
    "피드를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
});
