const product = location.pathname.split('/').pop() || 'channel';
const products = {
  channel: {
    word: 'JOURNAL',
    title: 'LAWYGO JOURNAL · 로이고 저널',
    desc: '미국·한국 경제와 증권·제도 변화를 법률로 읽는 편집국형 뉴스데스크.',
    help: '리드 기사와 보조 헤드라인, 호(issue) 목록 형식으로 표시됩니다.',
  },
  wiki: {
    word: 'WIKI',
    title: 'LAWYGO WIKI',
    desc: '법령·판례·법률백과 정보를 축적하는 지식 플랫폼',
    help: '판결문이나 법령의 원문을 함께 확인하세요.',
  },
  pan: {
    word: 'PAN',
    title: '변호사 블로그 · LAWYGO PAN',
    desc: '변호사 칼럼·구글 블로그 콘텐츠를 이미지 카드형으로 탐색합니다.',
    help: '광고 콘텐츠는 표시되며, 노출 순위는 수임 실적을 의미하지 않습니다.',
  },
  note: {
    word: 'NOTE',
    title: 'LAWYGO NOTE',
    desc: '업로드한 자료와 법률문서 초안을 비공개 관리하는 연구공간',
    help: '본인의 개인 노트는 로그인 후에만 확인할 수 있습니다.',
  },
};
const p = products[product] || products.channel;
document.body.classList.add('theme-' + product);
document.title = p.title + ' | LAWYGO';
document.getElementById('product-title').textContent = p.title;
document.getElementById('product-word').textContent = p.word;
document.getElementById('product-desc').textContent = p.desc;
document.getElementById('product-help').textContent = p.help;

const JOURNAL_IMGS = [
  '/static/img/editorial/journal-lead.jpg',
  '/static/img/editorial/journal-side.jpg',
  '/static/img/editorial/journal-lead.jpg',
];
const PAN_IMGS = [
  '/static/img/editorial/pan-blog-1.png',
  '/static/img/editorial/pan-blog-2.png',
  '/static/img/editorial/journal-side.jpg',
  '/static/img/editorial/journal-lead.jpg',
];

const api = async (url) => {
  const r = await fetch(url, { credentials: 'same-origin' });
  return r.json();
};
const el = (tag, text, cls) => {
  const e = document.createElement(tag);
  if (text) e.textContent = text;
  if (cls) e.className = cls;
  return e;
};

function boardLabel(slug) {
  const map = {
    news: '경제·법률 뉴스',
    clips: '영상·쇼츠',
    insight: '전문가 인사이트',
    lawyers: '변호사 브랜딩',
    blogs: '구글블로그 칼럼',
    shorts: '변호사 쇼츠',
    sponsored: '광고·프로모션',
  };
  return map[slug] || slug || '기사';
}

function injectChrome() {
  const chrome = document.getElementById('product-chrome');
  if (product === 'channel') {
    const today = new Date().toISOString().slice(0, 10);
    chrome.innerHTML = `
      <div class="journal-utility"><div class="wrap"><span>ECONOMY × LAW × INTELLIGENCE</span><span>로이고 저널 · LAWYGO JOURNAL</span></div></div>
      <div class="journal-masthead"><div class="wrap">
        <div class="kicker">THE EDITORIAL DESK · DIGITAL NEWSPAPER</div>
        <h1>LAWYGO JOURNAL</h1>
        <p class="muted" style="margin:0;font-size:14px">숫자 너머의 제도, 시장의 법률적 해석</p>
        <div class="dateline"><span>${today}</span><span>서울 · 워싱턴 데스크</span></div>
      </div></div>`;
    const help = document.getElementById('product-help');
    const desks = el('div', '', 'journal-desks');
    [
      ['01 / WASHINGTON', '미국 경제·증권', 'SEC·Fed 정책 단계별 정리'],
      ['02 / SEOUL', '한국 경제·제도', '금융위·금감원 발표 연결'],
      ['03 / CASE LAW', '판례와 해설', '시장·계약 논점'],
      ['04 / INSIGHT', '리걸마인드', '제도 배경 칼럼'],
    ].forEach(([a, b, c]) => {
      const d = el('div', '', 'journal-desk');
      d.innerHTML = `<span>${a}</span><strong>${b}</strong>${c}`;
      desks.append(d);
    });
    help.before(desks);
  } else if (product === 'pan') {
    chrome.innerHTML = `
      <section class="pan-hero"><div class="wrap">
        <div><div class="eyebrow">LAWYGO PAN</div><h1>변호사 블로그</h1>
        <p>쉽게 읽는 법률 정보와 변호사의 전문 콘텐츠를 한곳에서 만나보세요.</p></div>
        <img class="pan-hero-visual" src="/static/img/editorial/pan-blog-1.png" alt="LAWYGO PAN 블로그 허브">
      </div></section>`;
    const toolbar = document.querySelector('.toolbar');
    const chips = el('div', '', 'pan-chips');
    chips.innerHTML =
      '<button type="button" class="pan-chip active" data-kind="">전체</button>' +
      '<button type="button" class="pan-chip" data-kind="blog">칼럼</button>' +
      '<button type="button" class="pan-chip" data-kind="column">전문칼럼</button>' +
      '<button type="button" class="pan-chip" data-kind="profile">프로필</button>';
    toolbar.before(chips);
    chips.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.pan-chip');
      if (!btn) return;
      chips.querySelectorAll('.pan-chip').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      window.__panKindFilter = btn.dataset.kind || '';
      load();
    });
  }
}

async function openReader(post) {
  const item = await api('/api/posts/' + post.id);
  if (item.detail) {
    alert(item.detail);
    return;
  }
  document.getElementById('readerKind').textContent =
    post.kind + (post.is_sponsored ? ' · 광고' : '');
  document.getElementById('readerTitle').textContent = item.title;
  document.getElementById('readerBody').textContent = item.body;
  const link = document.getElementById('readerLink');
  link.replaceChildren();
  if (item.external_url) {
    const a = el('a', '원본 콘텐츠 열기 ↗', 'btn');
    a.href = item.external_url;
    a.target = '_blank';
    a.rel = item.is_sponsored ? 'noopener noreferrer sponsored' : 'noopener noreferrer';
    link.append(a);
  }
  document.getElementById('reader').classList.add('open');
}

function renderChannel(posts, wrap) {
  wrap.className = 'journal-rack';
  const [lead, ...rest] = posts;
  const leadEl = el('article', '', 'journal-lead');
    leadEl.innerHTML = `<img src="${JOURNAL_IMGS[0]}" alt=""><div class="copy"><span class="section-label">${lead.is_sponsored ? '광고 · ' : ''}${boardLabel(lead.kind)}</span><h2>${lead.title}</h2><p>${lead.summary || lead.title}</p><span class="meta">${lead.updated_at.slice(0, 10)}</span></div>`;
  leadEl.onclick = () => openReader(lead);
  wrap.append(leadEl);
  rest.slice(0, 4).forEach((post, i) => {
    const brief = el('article', '', 'journal-brief');
    brief.innerHTML = `<img src="${JOURNAL_IMGS[(i + 1) % JOURNAL_IMGS.length]}" alt=""><div><h3>${post.title}</h3><p class="meta">${post.updated_at.slice(0, 10)} · ${post.kind}</p></div>`;
    brief.onclick = () => openReader(post);
    wrap.append(brief);
  });
  if (posts.length > 1) {
    const list = el('div', '', 'journal-issue-list');
    list.style.gridColumn = '1 / -1';
    posts.slice(0, 6).forEach((post, i) => {
      const row = el('div', '', 'journal-issue-row');
      row.innerHTML = `<div><b>VOL. ${String(i + 1).padStart(2, '0')}</b><h3>${post.title}</h3></div><button type="button" class="btn secondary small">기사 보기</button>`;
      row.querySelector('button').onclick = () => openReader(post);
      list.append(row);
    });
    wrap.append(list);
  }
}

function renderPan(posts, wrap) {
  wrap.className = 'pan-blog-grid';
  const kindFilter = window.__panKindFilter || '';
  const filtered = kindFilter
    ? posts.filter((x) => x.kind === kindFilter)
    : posts;
  if (!filtered.length) {
    wrap.append(el('div', '해당 분야의 공개 글이 없습니다.', 'empty'));
    return;
  }
  filtered.forEach((post, i) => {
    const card = el('article', '', 'pan-image-card' + (post.is_sponsored ? ' sponsored' : ''));
    const img = PAN_IMGS[i % PAN_IMGS.length];
    card.innerHTML = `<img src="${img}" alt=""><div class="body"><span class="meta">${post.is_sponsored ? '광고 · ' : ''}${post.kind}</span><h3>${post.title}</h3><p>${post.summary || post.title}</p><span class="readmore">자세히 보기 →</span></div>`;
    card.onclick = () => openReader(post);
    wrap.append(card);
  });
}

function renderDefault(posts, wrap) {
  wrap.className = 'items-grid';
  for (const post of posts) {
    const card = el('article', '', 'post');
    card.append(el('span', post.is_sponsored ? '광고 · ' + post.kind : post.kind, post.is_sponsored ? 'tag sponsor' : 'tag'));
    card.append(el('h3', post.title));
    card.append(el('p', post.summary || post.title));
    card.append(el('div', post.updated_at.slice(0, 10), 'meta'));
    const btn = el('button', '자세히 보기 →', 'btn secondary');
    btn.onclick = () => openReader(post);
    card.append(btn);
    wrap.append(card);
  }
}

async function loadBoards() {
  const o = await api('/api/boards?product=' + product);
  const sel = document.getElementById('board');
  for (const b of o.items || []) {
    const opt = el('option', b.name);
    opt.value = b.id;
    sel.append(opt);
  }
}

async function load() {
  const q = new URLSearchParams({
    product,
    q: document.getElementById('search').value,
    limit: 60,
  });
  const b = document.getElementById('board').value;
  if (b) q.set('board_id', b);
  const data = await api('/api/posts?' + q);
  const wrap = document.getElementById('results');
  wrap.replaceChildren();
  document.getElementById('result-count').textContent = `총 ${data.total ?? 0}건`;
  const items = data.items || [];
  if (!items.length) {
    wrap.className = product === 'channel' ? 'journal-rack' : 'items-grid';
    wrap.append(
      el(
        'div',
        product === 'note'
          ? '개인 노트는 로그인 후 작성·열람할 수 있습니다.'
          : '아직 공개된 콘텐츠가 없습니다. 관리자 대시보드에서 새 글을 작성해 보세요.',
        'empty',
      ),
    );
    return;
  }
  if (product === 'channel') renderChannel(items, wrap);
  else if (product === 'pan') renderPan(items, wrap);
  else renderDefault(items, wrap);
}

document.getElementById('searchBtn').onclick = load;
document.getElementById('search').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') load();
});
document.getElementById('readerClose').onclick = () =>
  document.getElementById('reader').classList.remove('open');
document.getElementById('reader').onclick = (e) => {
  if (e.target.id === 'reader') e.target.classList.remove('open');
};

injectChrome();
loadBoards().then(load).catch(console.error);
