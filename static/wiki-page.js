// LAWYGO WIKI: public research and accessible record reader.
// Publicly published posts only. No unsafe API HTML injection.
const pick = (id) => document.getElementById(id);
function node(tag, content, className) {
  const el = document.createElement(tag);
  if (content !== undefined && content !== null) el.textContent = String(content);
  if (className) el.className = className;
  return el;
}
let reader;
function ensureReader(){
  if(reader) return reader;
  reader = document.createElement('dialog');
  reader.id='wikiReader';
  reader.className='delivery-reader';
  reader.setAttribute('aria-labelledby','wikiReaderTitle');
  const shell=node('div',undefined,'delivery-reader-shell');
  const top=node('div',undefined,'delivery-reader-top');
  const tag=node('span','LAWYGO WIKI / 공개 자료','eyebrow');
  const close=node('button','닫기 ×','delivery-reader-close');
  close.type='button';
  close.addEventListener('click',()=>reader.close());
  top.append(tag,close);
  const title=node('h2','','');
  title.id='wikiReaderTitle';
  const meta=node('p','','delivery-reader-meta');
  meta.id='wikiReaderMeta';
  const body=node('div','','delivery-reader-content');
  body.id='wikiReaderBody';
  const external=node('div','','delivery-reader-external');
  external.id='wikiReaderExternal';
  const notice=node('p','법령·판례의 최신성은 반드시 원문에서 확인하세요. 개별 사안에 대한 법률 자문이 아닙니다.','delivery-reader-disclaimer');
  shell.append(top,title,meta,body,external,notice);
  reader.append(shell);
  reader.addEventListener('click',e=>{if(e.target===reader)reader.close()});
  document.body.append(reader);
  return reader;
}
async function json(url) {
  const res=await fetch(url,{credentials:'same-origin'});
  if(!res.ok) throw new Error('자료를 불러오지 못했습니다 (HTTP '+res.status+')');
  return res.json();
}
async function openPost(id) {
  const modal=ensureReader();
  pick('wikiReaderTitle').textContent='게시글을 불러오는 중…';
  pick('wikiReaderBody').textContent='';
  pick('wikiReaderMeta').textContent='';
  pick('wikiReaderExternal').replaceChildren();
  if(!modal.open)modal.showModal();
  try {
    const item=await json('/api/posts/'+encodeURIComponent(id));
    pick('wikiReaderTitle').textContent=item.title||'법률 자료';
    pick('wikiReaderMeta').textContent=[item.kind,item.updated_at?.slice(0,10)].filter(Boolean).join(' · ');
    pick('wikiReaderBody').textContent=item.body||item.summary||'본문을 확인할 수 없습니다.';
    if(item.external_url) {
      try {
        const u=new URL(item.external_url);
        if(['https:','http:'].includes(u.protocol)) {
          const a=node('a','공식 원문·출처 보기 ↗','btn btn-navy');
          a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';
          pick('wikiReaderExternal').append(a);
        }
      }catch(_){}
    }
  }catch(e){pick('wikiReaderTitle').textContent='자료를 열 수 없습니다';pick('wikiReaderBody').textContent=e.message||'오류가 발생했습니다.'}
}
function resultCard(item) {
  const card=node('article',undefined,'result-card');
  card.append(node('span',item.kind||'WIKI','delivery-mini-label'),node('h3',item.title||'제목 없음'),node('p',item.summary||''),node('small',item.source||'LAWYGO WIKI'));
  if(item.id){
    const btn=node('button','상세 내용 읽기 ↗','delivery-textlink');
    btn.type='button';btn.addEventListener('click',()=>openPost(item.id));card.append(btn)
  }
  return card;
}
async function searchWiki(q){
  const root=pick('wiki-results'),count=pick('wiki-count');
  root.replaceChildren();
  const term=String(q||'').trim();
  if(term.length<2){count.textContent='0건';root.append(node('p','검색어는 2자 이상 입력하세요.','no-results'));return}
  root.append(node('p','검색 중…','no-results'));
  try{
    const data=await json('/api/wiki/search?q='+encodeURIComponent(term));
    root.replaceChildren();
    const items=Array.isArray(data.items)?data.items:[];
    count.textContent=items.length+'건';
    if(!items.length)root.append(node('p','검색 결과가 없습니다. 다른 검색어를 입력해 보세요.','no-results'));
    items.forEach(it=>root.append(resultCard(it)));
  }catch(e){count.textContent='조회 실패';root.replaceChildren(node('p',e.message,'no-results'))}
}
const form=pick('wiki-search-form');
form?.addEventListener('submit',e=>{e.preventDefault();searchWiki(pick('wikiq').value)});
async function loadFeed(){
  const root=pick('wiki-feed');if(!root)return;
  try{
    const data=await json('/api/posts?product=wiki&limit=12');
    root.replaceChildren();
    const items=Array.isArray(data.items)?data.items:[];
    const imgs=['/static/img/design/ai-wiki-visual.svg','/static/img/editorial/journal-lead.jpg','/static/img/editorial/journal-side.jpg'];
    items.forEach((post,i)=>{
      const card=node('article',undefined,'article-card delivery-feed-card');
      const pic=document.createElement('img');pic.src=imgs[i%imgs.length];pic.alt='';pic.loading='lazy';pic.className='card-img';
      const copy=node('div',undefined,'article-copy');
      copy.append(node('span',post.kind||'WIKI','eyebrow'),node('h3',post.title||'제목 없음'),node('p',post.summary||''));
      const btn=node('button','자료 읽기 ↗','delivery-textlink');btn.type='button';
      btn.addEventListener('click',()=>openPost(post.id));copy.append(btn);card.append(pic,copy);root.append(card);
    });
    if(!items.length)root.append(node('p','현재 공개된 위키 글이 없습니다. 새로운 자료를 준비 중입니다.','no-results'));
  }catch(e){root.replaceChildren(node('p','공개 자료를 불러오지 못했습니다. 잠시 후 다시 확인해 주세요.','no-results'))}
}
const preset=new URLSearchParams(location.search).get('q');
if(preset&&pick('wikiq')){pick('wikiq').value=preset;searchWiki(preset)}else searchWiki('공시');
loadFeed();
