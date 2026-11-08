/* LAWYGO PAN V2 - verified original source posts, accessible detail reader */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('pan-featured-cards')) return;
  const labels = {video:'YOUTUBE',shorts:'SHORTS',blog:'BLOGGER',newswire:'뉴스와이어 · 보도자료',us_legal:'미국 로펌 · 법률 리포트'};
  const all = [];
  let active = 'all';
  let visibleCount = 16;
  let activeDetail = null;
  const pictureFallback = '/static/img/design/ly-pan-scene.svg';
  const safeUrl = (raw, allowRelative = false) => {
    try {
      const u = new URL(String(raw || ''), location.origin);
      if (u.protocol !== 'https:' && !(u.origin === location.origin && allowRelative)) return '';
      return u.href;
    } catch (_) { return ''; }
  };
  const safeThumb = (item) => {
    const u = safeUrl(item.thumb_url, true);
    if (!u) return pictureFallback;
    const host = new URL(u).hostname.toLowerCase();
    return (u.startsWith(location.origin+'/static/') ||
      host === 'img.youtube.com' || host === 'i.ytimg.com' ||
      host.endsWith('.googleusercontent.com') || host.endsWith('.blogspot.com') ||
      host.endsWith('.newswire.co.kr'))
      ? u : pictureFallback;
  };
  const displayDate = str => {
    if (!str) return '발행일 미표기';
    const d = new Date(str);
    if (!Number.isNaN(d.getTime())) return d.toLocaleDateString('ko-KR', {year:'numeric',month:'2-digit',day:'2-digit'});
    return String(str).slice(0, 16);
  };
  const node = (tag, className, txt) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (txt != null) el.textContent = String(txt);
    return el;
  };
  const image = (item) => {
    const img = node('img');
    img.alt = item.title ? item.title + ' 썸네일' : '법률 콘텐츠';
    img.loading = 'lazy';
    img.referrerPolicy = 'no-referrer';
    img.src = safeThumb(item);
    img.addEventListener('error', () => {
      if (img.getAttribute('src') !== pictureFallback) img.src = pictureFallback;
    });
    return img;
  };
  const cardLink = item => {
    const link = node('a');
    link.href = '/p/pan?post=' + encodeURIComponent(item.id);
    link.addEventListener('click', event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      showDetail(item, true);
    });
    return link;
  };
  const playIcon = () => node('span','pan-play-icon','▶');
  const mediaCard = item => {
    const a = cardLink(item);
    a.className = 'pan-featured-card';
    a.append(image(item),playIcon());
    const bottom = node('div','pan-card-bottom');
    bottom.append(node('span','pan-card-type',labels[item.content_type] || 'PUBLIC POST'),
      node('h3',null,item.title));
    a.append(bottom);
    return a;
  };
  const miniCard = item => {
    const a = cardLink(item);
    a.className = 'pan-mini-card';
    const thumb = node('div','pan-mini-card-img');
    thumb.append(image(item),node('span',null,'▶'));
    a.append(thumb,node('h3',null,item.title),
      node('small',null,item.source || '공개 법률 콘텐츠'));
    return a;
  };
  const newsCard = item => {
    const a = cardLink(item);
    a.className = 'pan-news-card';
    a.append(node('strong',null,item.title),
      node('span',null,displayDate(item.published)+' · 뉴스와이어 보도자료'));
    return a;
  };
  const standardCard = item => {
    const a = cardLink(item);
    a.className = 'pan-post-card';
    a.append(image(item));
    const body = node('div','pan-post-card-main');
    body.append(node('small',null,labels[item.content_type] || '법률 게시물'),
      node('h3',null,item.title_ko||item.title),
      node('p',null,(item.source || '공개 원문')+' · '+displayDate(item.published)));
    a.append(body);
    return a;
  };
  const empty = (msg,href,label) => {
    const b = node('div','pan-media-empty');
    b.append(node('p',null,msg));
    if (href) { const a=node('a',null,label||'원문 탐색 ↗');a.href=href;b.append(a); }
    return b;
  };
  const setItems = (id,items,creator,msg) => {
    const root=$(id); if (!root) return;
    root.replaceChildren();
    if (!items.length) {
      root.append(empty(msg || '연결된 실제 게시물이 없습니다.','/dashboard','공개 소스 연결 관리 ↗'));
      return;
    }
    items.forEach(item => root.append(creator(item)));
  };
  const sortByDate = (a,b) => {
    const da = new Date(a.published || '').getTime() || 0;
    const db = new Date(b.published || '').getTime() || 0;
    return (b.content_type==='us_legal')-(a.content_type==='us_legal') || db-da;
  };
  const usCard = (item) => {
    const a = cardLink(item);a.className='pan-us-card';
    a.append(node('span','pan-us-card-overline','U.S. LEGAL INSIGHT · '+(item.category_ko||'미국 법률 동향')));
    const h=node('h3',null,item.title_ko||item.title);a.append(h);
    if(item.title_original)a.append(node('span','pan-us-original',item.title_original));
    const abstract=node('p',null,item.summary_ko||item.summary||'원문에서 구체적인 내용을 확인해 주세요.');
    a.append(abstract);
    const foot=node('div','pan-us-foot');
    foot.append(node('strong',null,item.source||'미국 법률 발행사'),
      node('small',null,item.translation_status==='editorial'?'한글 편집 요약':'영문 원문 · 한국어 주제 안내'));
    a.append(foot);return a;
  };
  const render = () => {
    const us = all.filter(x=>x.content_type==='us_legal');
    setItems('pan-us-post-cards',us.slice(0,8),usCard,'미국 로펌 공개 게시물 연결을 확인해 주세요.');
    const videos = all.filter(x => ['video','shorts'].includes(x.content_type));
    const shorts = all.filter(x => x.content_type==='shorts');
    const news = all.filter(x => x.content_type==='newswire');
    setItems('pan-featured-cards',videos.slice(0,8),mediaCard,'게시된 법률 영상이 없습니다.');
    setItems('pan-channel-cards',videos.filter(x=>x.content_type==='video').slice(0,3),miniCard,'공개 전문가 영상이 없습니다.');
    setItems('pan-shorts-cards',shorts.slice(0,2),miniCard,'등록된 법률 쇼츠가 없습니다.');
    setItems('pan-wire-cards',news.slice(0,4),newsCard,'등록된 뉴스와이어 법률 보도자료가 없습니다.');
    renderList();
  };
  const renderList = () => {
    const filtered = active==='all'?all:all.filter(x=>x.content_type===active);
    const root=$('pan-real-post-grid');
    if (!root) return;
    root.replaceChildren();
    if (!filtered.length) root.append(empty('이 출처에 해당하는 법률 게시물이 없습니다.','/dashboard','소스 관리 ↗'));
    else filtered.slice(0,visibleCount).forEach(item=>root.append(standardCard(item)));
    const old=$('pan-more-button');old?.remove();
    if (filtered.length>visibleCount) {
      const btn=node('button','pan-more-button','게시물 더 보기 ('+Math.min(16,filtered.length-visibleCount)+'개) ↓');
      btn.id='pan-more-button';btn.type='button';
      btn.style.cssText='display:block;margin:22px auto 0;background:#192d43;color:#fff;border:0;border-radius:10px;min-height:44px;padding:10px 23px;font-weight:800';
      btn.addEventListener('click',()=>{visibleCount+=16;renderList();});
      root.after(btn);
    }
    const count=$('pan-real-post-count');
    if (count) count.textContent=filtered.length.toLocaleString('ko-KR')+'개 실제 원문';
  };
  const youtubeId = item => {
    try {
      const u = new URL(item.url);
      const host = u.hostname.toLowerCase();
      if (!['www.youtube.com','youtube.com','m.youtube.com','youtu.be'].includes(host)) return '';
      const id=host==='youtu.be'?u.pathname.slice(1):
        u.pathname.startsWith('/shorts/')?u.pathname.split('/')[2]:u.searchParams.get('v');
      return /^[a-zA-Z0-9_-]{11}$/.test(id||'')?id:'';
    } catch (_) {return '';}
  };
  const clearDetailUrl = () => {
    const u = new URL(location.href);
    if (u.searchParams.has('post')) {u.searchParams.delete('post');history.replaceState({},'',u.pathname+u.search+u.hash);}
  };
  const closeDetail = (updateUrl = true) => {
    const dia=$('pan-post-detail');
    if (dia?.open) dia.close();
    activeDetail=null;
    if (updateUrl) clearDetailUrl();
  };
  const showDetail = async (item,updateUrl) => {
    const dialog=$('pan-post-detail'),root=$('pan-detail-body');
    if (!dialog || !root) return;
    activeDetail=item;
    root.replaceChildren();
    const section=node('article','pan-detail-layout');
    const meta=node('div','pan-detail-meta',
      (labels[item.content_type]||'법률 게시물')+' · '+(item.source||'공개 원문')+' · '+displayDate(item.published));
    section.append(meta,node('h2',null,item.title_ko||item.title));
    if(item.title_original && item.title_original!==item.title_ko) {
      const original=node('p',null,'EN / '+item.title_original);
      original.style.cssText='font-size:12px;color:#6f7c8c;margin-top:-6px';
      section.append(original);
    }
    if(item.content_type==='us_legal'){
      section.append(node('p',null,item.translation_status==='editorial'?
        '아래 내용은 로이고가 독립 작성한 한국어 핵심 요약입니다. 영어 원문 전체 번역이 아닙니다.':
        '영어 원문입니다. 아래 한국어 문장은 주제를 분류한 안내이며 제목 전문의 번역은 아닙니다.'));
    }
    const description=(item.summary||'').trim();
    if (description) section.append(node('p',null,description));
    const wrapper=node('div','pan-detail-media');
    wrapper.append(image(item));
    const vid=youtubeId(item);
    if (vid) {
      const button=node('button',null,'▶ 원본 YouTube 영상 재생');
      button.type='button';
      button.addEventListener('click',()=>{
        const frame=node('iframe');
        frame.src='https://www.youtube-nocookie.com/embed/'+vid+'?rel=0';
        frame.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        frame.allowFullscreen=true;
        frame.title=item.title+' · YouTube 영상';
        frame.referrerPolicy='strict-origin-when-cross-origin';
        wrapper.replaceChildren(frame);
      });
      wrapper.append(button);
    }
    section.append(wrapper);
    const source=safeUrl(item.url,true);
    const actions=node('div','pan-detail-links');
    if (source) {
      const link=node('a',null,item.content_type==='newswire'?'뉴스와이어 원문 보기 ↗':
        item.content_type==='blog'?'구글 블로그 원문 보기 ↗':item.content_type==='us_legal'?'미국 로펌 원문 확인 ↗':'원본 영상·게시글 열기 ↗');
      link.href=source;link.target='_blank';link.rel='noopener noreferrer';
      actions.append(link);
    }
    const back=node('a',null,'전체 게시물로 돌아가기');
    back.href='#pan-more-posts';back.addEventListener('click',()=>closeDetail());
    actions.append(back);section.append(actions);
    section.append(node('p','pan-detail-disclaimer',
      '본문 및 영상의 저작권은 각 원 발행자에게 있습니다. LAWYGO는 공개 출처와 요약만 표시하며 법률 상담을 제공하지 않습니다.'));
    root.append(section);
    if (updateUrl) {
      const u=new URL(location.href);u.searchParams.set('post',item.id);
      history.pushState({post:item.id},'',u.pathname+u.search+u.hash);
    }
    if (!dialog.open) dialog.showModal();
    // CMS-owned public article may have additional body; never render remote HTML.
    if (item.approved && item.id && /^[-a-zA-Z0-9_]{1,80}$/.test(item.id)) {
      try {
        const response=await fetch('/api/posts/'+encodeURIComponent(item.id),{credentials:'omit'});
        if (response.ok && activeDetail===item) {
          const post=await response.json();
          if (post.product==='pan' && post.status==='published' && post.visibility==='public' && post.body) {
            const text=node('p',null,post.body);text.style.whiteSpace='pre-wrap';
            section.insertBefore(text,wrapper);
          }
        }
      } catch (_) {}
    }
  };
  const fetchItems = async q => {
    const root=$('pan-featured-cards');
    // Keep verified real video cards visible during first uncached RSS request.
    if (root && !root.querySelector('.pan-featured-card')) root.replaceChildren(node('p','pan-media-loading','실제 게시물과 공식 소스를 확인하고 있습니다.'));
    try {
      const api='/api/pan/content?'+new URLSearchParams({type:'all',limit:'100',q:q||''});
      const response=await fetch(api,{cache:'no-store',credentials:'omit'});
      if (!response.ok) throw Error('source API '+response.status);
      const payload=await response.json();
      const seen=new Set();all.length=0;
      for (const item of payload.items||[]) {
        if (!item || !item.title || !item.url || !item.id) continue;
        const url=safeUrl(item.url,true);
        if (!url || seen.has(url) || !['video','shorts','blog','newswire','us_legal'].includes(item.content_type)) continue;
        seen.add(url);all.push({...item,url});
      }
      all.sort(sortByDate);
      render();
      const requested=new URLSearchParams(location.search).get('post');
      if (requested) {
        const found=all.find(x=>x.id===requested);
        if (found) showDetail(found,false);
      }
    } catch (e) {
      if (root) root.replaceChildren(empty('공개 원문 연결에 실패했습니다. 새로고침하여 다시 확인해 주세요.','/dashboard','소스 연결 상태 확인 ↗'));
      const count=$('pan-real-post-count');if (count) count.textContent='소스 연결 확인 필요';
      console.warn('PAN public metadata request error',String(e));
    }
  };
  $('pan-media-filters')?.addEventListener('click',e=>{
    const button=e.target.closest('[data-feed-kind]');
    if (!button) return;
    active=button.dataset.feedKind;
    visibleCount=16;
    $('pan-media-filters').querySelectorAll('[data-feed-kind]').forEach(b=>{
      b.classList.toggle('active',b===button);
      b.setAttribute('aria-pressed',b===button?'true':'false');
    });
    renderList();
  });
  $('pan-posts-reload')?.addEventListener('click',()=>fetchItems(new URLSearchParams(location.search).get('q')||''));
  $('pan-detail-close')?.addEventListener('click',()=>closeDetail());
  $('pan-post-detail')?.addEventListener('click',e=>{if(e.target===$('pan-post-detail'))closeDetail()});
  $('pan-post-detail')?.addEventListener('close',()=>{activeDetail=null;clearDetailUrl();});
  window.addEventListener('popstate',()=>{
    const id=new URLSearchParams(location.search).get('post');
    if (!id) closeDetail(false);
    else {const item=all.find(x=>x.id===id);if (item) showDetail(item,false);}
  });
  const syncSearch = form => form?.addEventListener('submit',()=>{
    const q=($('pan-hero-search')?.value || $('pan-hub-query')?.value || '').trim();
    fetchItems(q);
  });
  syncSearch($('pan-hero-search-form')); syncSearch($('pan-hub-search'));
  fetchItems(new URLSearchParams(location.search).get('q')||'');
})();
