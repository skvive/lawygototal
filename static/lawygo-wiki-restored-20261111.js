/* LAWYGO WIKI — restored dashboard, real public endpoints, official statute reference.
 * Original authenticated legal engine remains on lawygo.com. This page does not fabricate user records. */
(() => {
'use strict';
const $=id=>document.getElementById(id);
const LEGAL_SOURCE='https://law.go.kr/LSW/lsInfoP.do?lsiSeq=246569';
const LEASE={
  key:'lease',title:'임대차(賃貸借)',kind:'민법',source:'국가법령정보센터 · 민법 제618조',
  summary:'민법 제618조는 임대차를 목적물의 사용·수익을 허용하는 약정과 그 대가인 차임 지급 약정이 결합된 계약으로 규정합니다.',
  body:'임대차는 임대인이 상대방에게 목적물을 사용하고 수익할 수 있도록 하는 대신, 임차인이 차임을 지급하기로 약속하는 계약입니다.\n\n계약의 목적물·대가·당사자의 권리와 의무를 검토할 때에는 민법 제618조뿐 아니라 관련 특별법과 개별 계약 조항을 함께 확인해야 합니다.',
  external_url:LEGAL_SOURCE,category:'민사 / 계약법 / 부동산',detail:'민법 제618조(임대차의 의의)'
};
let activeArticle=null;
const toast=message=>{const e=$('wikiToast');if(!e)return;e.textContent=message;e.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(()=>e.hidden=true,2800)};
function safeLocalGet(k){try{return JSON.parse(localStorage.getItem(k)||'[]')}catch{return []}}
function safeLocalSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(_){}}
function favorites(){const r=safeLocalGet('lawygoWikiFavoritesV1');return Array.isArray(r)?r:[]}
function historyTerms(){const r=safeLocalGet('lawygoWikiSearchHistoryV1');return Array.isArray(r)?r:[]}
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e}
function externalUrl(value){try{const url=new URL(String(value));return ['http:','https:'].includes(url.protocol)?url.href:null}catch{return null}}
function setView(view,opts={}){
 const chosen=['dashboard','search','article'].includes(view)?view:'dashboard';
 document.querySelectorAll('.wsection').forEach(e=>e.hidden=e.id!=='view-'+chosen);
 document.querySelectorAll('[data-view]').forEach(e=>{const isActive=e.dataset.view===chosen;e.classList.toggle('active',isActive);if(e.tagName==='BUTTON')e.setAttribute('aria-current',isActive?'page':'false')});
 if(opts.url)history.pushState({},'',opts.url);
 if(opts.scroll!==false)scrollTo({top:0,behavior:'instant'});
 if(chosen==='dashboard')renderStored();
}
async function getJSON(path){const r=await fetch(path,{credentials:'same-origin',headers:{Accept:'application/json'}});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}
function resultCard(item){const b=node('button',undefined,'wresult');b.type='button';
 b.append(node('b',String(item.title||'제목 없는 자료')));
 b.append(node('small',[item.kind,item.source,item.updated_at?.slice(0,10)].filter(Boolean).join(' · ')||'LAWYGO WIKI'));
 if(item.summary)b.append(node('p',String(item.summary).slice(0,180)));
 b.addEventListener('click',()=>openArticle(item));return b}
function officialCard(){const b=node('button',undefined,'wresult');b.type='button';
 b.append(node('b','임대차(賃貸借) · 민법 제618조'));
 b.append(node('small','국가법령정보센터 공식 법령 참고 · 공개 위키 게시글과 구분'));
 b.addEventListener('click',()=>openArticle(LEASE));return b}
async function loadDashboard(){
 const target=$('wikiLatestList');target.replaceChildren(node('p','공개 자료를 조회하는 중입니다.','wstatustext'));
 try{const d=await getJSON('/api/posts?product=wiki&limit=12');
   const items=Array.isArray(d.items)?d.items:[];const count=Number.isFinite(Number(d.total))?Number(d.total):items.length;
   $('wikiStatPublished').textContent=String(count);
   target.replaceChildren();
   if(items.length){items.slice(0,5).forEach(it=>target.append(resultCard(it)))}
   else{target.append(node('p','현재 공개 승인된 위키 게시글이 없습니다. 아래 공식 법령 예시를 열어볼 수 있습니다.','wblank'));target.append(officialCard())}
 }catch(e){$('wikiStatPublished').textContent='—';target.replaceChildren(node('p','현재 위키 게시글 서버를 불러올 수 없습니다. 공식 법령 자료는 확인할 수 있습니다.','wblank'),officialCard())}
}
function renderStored(){
 const history=historyTerms();const faves=favorites();
 $('wikiStatSearches').textContent=String(history.length);
 $('wikiStatFavorites').textContent=String(faves.length);
 const recent=$('wikiRecentSearches');recent.replaceChildren();
 if(!history.length)recent.append(node('div','이 브라우저에서 검색한 키워드가 여기에 표시됩니다.','wblank'));
 else history.slice(0,6).forEach(t=>{const b=node('button',t,'wresult');b.type='button';b.addEventListener('click',()=>search(t));recent.append(b)});
 const fav=$('wikiFavoriteList');fav.replaceChildren();
 if(!faves.length)fav.append(node('div','백과 문서의 ☆ 저장 버튼을 누르면 이 브라우저에 즐겨찾기됩니다.','wblank'));
 else faves.slice(0,8).forEach(f=>{const b=node('button',f.title||'저장한 자료','wresult');b.type='button';b.addEventListener('click',()=>f.key==='lease'?openArticle(LEASE):openArticleById(f.key));fav.append(b)});
}
function storeSearch(query){
 const terms=historyTerms();safeLocalSet('lawygoWikiSearchHistoryV1',[query,...terms.filter(v=>v!==query)].slice(0,25));renderStored();
}
function setSearchInput(query){document.querySelectorAll('.wiki-search-input').forEach(e=>e.value=query)}
async function search(raw){
 const query=String(raw||'').trim().slice(0,100);
 if(query.length<2){toast('검색어는 두 글자 이상 입력해 주세요.');return}
 storeSearch(query);setSearchInput(query);
 setView('search',{url:'/p/wiki?view=search&q='+encodeURIComponent(query)});
 const root=$('wikiResults'),status=$('wikiSearchStatus');root.replaceChildren(node('p','자료를 검색하고 있습니다.','wstatustext'));status.textContent='검색 중…';
 try{
   const d=await getJSON('/api/wiki/search?q='+encodeURIComponent(query));const items=Array.isArray(d.items)?d.items:[];
   root.replaceChildren();status.textContent='실제 공개 위키 검색 '+items.length+'건';
   if(items.length)items.forEach(item=>{if(item.id)root.append(resultCard(item))});
   else root.append(node('div','일치하는 공개 위키 게시글은 아직 없습니다. 공식 법령 원문 검색 또는 원본 인증 작업실을 이용해 주세요.','wblank'));
   if(/임대차|민법|계약/.test(query))root.append(officialCard());
 }catch(e){status.textContent='검색 서버 연결을 확인해 주세요.';root.replaceChildren(node('p','공개 자료를 불러오지 못했습니다. 기존 법률백과 로그인 또는 국가법령정보센터를 이용해 주세요.','wblank'))}
}
function articleKey(item){return String(item.key||item.id||'')}
function renderArticle(item){
 activeArticle=item;
 const isLease=articleKey(item)==='lease';
 const title=String(item.title||'법률자료'),kind=String(item.kind||'법률백과'),source=String(item.source||'LAWYGO WIKI');
 document.title=title+' | 로이고법률백과';
 $('wikiArticleTitle').textContent=title;
 $('wikiArticleBreadcrumb').textContent='로이고법률백과 › '+(isLease?'민사 › 계약법':'공개자료 › '+kind);
 $('wikiArticleSummary').textContent=String(item.summary||'선택한 공개 자료의 내용을 확인하세요.');
 $('wikiArticleBody').textContent=String(item.body||item.summary||'본문을 확인할 수 없습니다.');
 $('wikiArticleSourceLabel').textContent=source+(isLease?' · 민법 제618조':'');
 const badges=$('wikiArticleBadges');badges.replaceChildren();
 (isLease?['민사','계약법','부동산','공식 법령 참고']:[kind,source,'공개 승인 자료']).forEach(v=>badges.append(node('span',v)));
 const link=$('wikiArticleSource');const safe=externalUrl(item.external_url);
 if(safe){link.href=safe;link.hidden=false}else{link.hidden=true;link.removeAttribute('href')}
 const key=articleKey(item);const selected=favorites().some(f=>f.key===key);
 $('wikiArticleFavorite').textContent=selected?'★ 저장됨':'☆ 저장';
 $('wikiArticleFavorite').setAttribute('aria-pressed',String(selected));
 setView('article',{url:isLease?'/p/wiki?article=lease':'/p/wiki?id='+encodeURIComponent(key)});
}
function openArticle(item){
 if(!item)return;
 if(articleKey(item)==='lease'){renderArticle(LEASE);return}
 const key=articleKey(item);if(!key){toast('자료 식별자가 없습니다.');return}
 openArticleById(key);
}
async function openArticleById(id){
 setView('article',{url:'/p/wiki?id='+encodeURIComponent(String(id))});
 activeArticle=null;
 $('wikiArticleTitle').textContent='공개 자료를 불러오는 중…';
 $('wikiArticleSummary').textContent='공개 문서를 확인하고 있습니다.';
 $('wikiArticleBody').textContent='';
 $('wikiArticleSource').hidden=true;
 try{const it=await getJSON('/api/posts/'+encodeURIComponent(String(id)));renderArticle({...it,key:id})}
 catch(e){$('wikiArticleTitle').textContent='자료를 열 수 없습니다';$('wikiArticleSummary').textContent='문서를 찾을 수 없거나 현재 공개되지 않았습니다.';$('wikiArticleBody').textContent='원본 서버 응답: '+e.message;toast('상세 페이지를 조회하지 못했습니다.')}
}
document.querySelectorAll('.wiki-search-form').forEach(form=>form.addEventListener('submit',e=>{e.preventDefault();search(form.querySelector('.wiki-search-input')?.value)}));
document.querySelectorAll('[data-topic]').forEach(btn=>btn.addEventListener('click',()=>search(btn.dataset.topic)));
document.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>{
 if(btn.dataset.view==='article')openArticle(LEASE);else setView(btn.dataset.view,{url:btn.dataset.view==='search'?'/p/wiki?view=search':'/p/wiki'})
}));
document.querySelectorAll('[data-article]').forEach(btn=>{if(btn.dataset.view==='article')return;btn.addEventListener('click',()=>openArticle(LEASE))});
document.querySelectorAll('[data-view-link]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const v=a.dataset.viewLink;setView(v,{url:v==='search'?'/p/wiki?view=search':'/p/wiki'})}));
$('wikiArticleFavorite').addEventListener('click',()=>{
 if(!activeArticle){toast('저장할 자료를 먼저 선택해 주세요.');return}
 const key=articleKey(activeArticle),arr=favorites();const found=arr.some(f=>f.key===key);
 const next=found?arr.filter(f=>f.key!==key):[{key,title:String(activeArticle.title||'법률자료')},...arr].slice(0,60);
 safeLocalSet('lawygoWikiFavoritesV1',next);const now=!found;
 $('wikiArticleFavorite').textContent=now?'★ 저장됨':'☆ 저장';
 $('wikiArticleFavorite').setAttribute('aria-pressed',String(now));renderStored();toast(now?'이 브라우저에 즐겨찾기했습니다.':'즐겨찾기를 해제했습니다.');
});
$('wikiArticlePrint').addEventListener('click',()=>window.print());
$('wikiArticleShare').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);toast('문서 링크를 복사했습니다.')}catch{toast('주소 표시줄에서 문서 URL을 복사하세요.')}});
window.addEventListener('popstate',()=>initRoute());
function initRoute(){
 const p=new URLSearchParams(location.search);
 if(p.get('id')){openArticleById(p.get('id'));return}
 if(p.get('article')==='lease'){renderArticle(LEASE);return}
 if(p.get('view')==='search'){setView('search',{scroll:false});const q=p.get('q');if(q)search(q);return}
 setView('dashboard',{scroll:false});
}
loadDashboard();renderStored();initRoute();
})();
