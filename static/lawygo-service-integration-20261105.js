/* LAWYGO source-aligned, public-data-only workspace integration.
 * Original private AI engines cannot be framed (X-Frame-Options: SAMEORIGIN;
 * CSP frame-ancestors 'self'). No credential sharing or private document upload. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const make = (tag, text, css) => {
    const el = document.createElement(tag);
    if (text !== undefined && text !== null) el.textContent = String(text);
    if (css) el.className = css;
    return el;
  };
  const LEGAL = /(법률|변호사|법무|법원|판례|법령|소송|민사|형사|계약|상속|이혼|손해배상|고소|재판|등기|조세|유언|양육권|특허|지식재산|\blegal\b|\blawyer\b|\battorney\b|\blitigation\b|\bcourt\b)/i;
  function safeLink(value) {
    try {
      const url = new URL(String(value || ''), location.origin);
      if (url.protocol === 'https:' || (url.protocol === 'http:' && url.origin === location.origin)) return url.href;
    } catch (_) {}
    return null;
  }
  async function api(path) {
    const response = await fetch(path, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('공개자료 요청 실패 (' + response.status + ')');
    return response.json();
  }
  function wikiStudio() {
    const form = $('lawygoWikiStudioForm');
    if (!form) return;
    const input = $('lawygoWikiStudioInput');
    const results = $('lawygoWikiStudioResults');
    const count = $('lawygoWikiStudioCount');
    const title = $('lawygoWikiStudioTitle');
    const text = $('lawygoWikiStudioBody');
    const source = $('lawygoWikiStudioSource');
    const copy = $('lawygoWikiStudioCopy');
    const send = $('lawygoWikiStudioSend');
    const status = $('lawygoWikiStudioStatus');
    let activePost = null;
    let nonce = 0;
    const show = (msg) => { status.textContent = msg; };
    const resetPreview = () => {
      activePost = null;
      title.textContent = '검색 결과를 선택하세요';
      text.textContent = '공개 검수된 법률자료만 이 화면에서 불러옵니다. 원본 AI 백과의 민감한 프로젝트 데이터와는 연결되지 않습니다.';
      source.hidden = true;
      source.removeAttribute('href');
      copy.disabled = true;
      send.disabled = true;
    };
    resetPreview();
    async function loadPost(item) {
      resetPreview();
      title.textContent = '자료 읽는 중…';
      try {
        const data = await api('/api/posts/' + encodeURIComponent(String(item.id)));
        activePost = {
          title: String(data.title || item.title || '법률 자료'),
          summary: String(data.summary || item.summary || ''),
          body: String(data.body || data.summary || '내용이 없습니다.'),
          source: String(data.source || item.source || 'LAWYGO WIKI'),
          url: safeLink(data.external_url) || location.origin + '/p/wiki?q=' + encodeURIComponent(input.value)
        };
        title.textContent = activePost.title;
        text.textContent = activePost.body;
        source.href = activePost.url;
        source.hidden = false;
        copy.disabled = false;
        send.disabled = false;
        show('공개자료를 불러왔습니다. 최신 법령·판례 원문을 별도로 확인하세요.');
      } catch (err) {
        title.textContent = '상세자료를 열 수 없습니다';
        text.textContent = String(err.message || err);
        show('공개자료 확인에 실패했습니다.');
      }
    }
    async function search(term) {
      const query = String(term || '').trim().slice(0, 100);
      input.value = query;
      results.replaceChildren();
      resetPreview();
      if (query.length < 2) {
        count.textContent = '0건';
        results.append(make('p', '검색어를 2자 이상 입력하세요.', 'lnw-caption'));
        return;
      }
      const seq = ++nonce;
      show('공개 백과 검색 중…');
      results.append(make('p', '승인된 자료를 검색하고 있습니다.', 'lnw-caption'));
      try {
        const data = await api('/api/wiki/search?q=' + encodeURIComponent(query));
        if (seq !== nonce) return;
        const items = Array.isArray(data.items) ? data.items : [];
        results.replaceChildren();
        count.textContent = items.length + '건';
        if (!items.length) results.append(make('p', '검색 조건에 맞는 공개 자료가 없습니다. 다른 키워드로 다시 검색해 주세요.', 'lnw-caption'));
        items.slice(0, 35).forEach((item) => {
          if (!item.id) return;
          const btn = make('button', null, 'lnw-result');
          btn.type = 'button';
          btn.append(make('strong', item.title || '법률 자료'), make('small', [item.kind, item.source].filter(Boolean).join(' · ')));
          btn.addEventListener('click', () => loadPost(item));
          results.append(btn);
        });
        show('검색 완료 · ' + items.length + '건 / 출처 및 최신성 확인 필요');
      } catch (err) {
        if (seq !== nonce) return;
        results.replaceChildren(make('p', '검색에 실패했습니다. 네트워크 상태를 확인해 주세요.', 'lnw-caption'));
        count.textContent = '조회 실패';
        show(String(err.message || err));
      }
    }
    form.addEventListener('submit', (e) => { e.preventDefault(); search(input.value); });
    document.querySelectorAll('[data-legal-workspace-topic]').forEach((b) => {
      b.addEventListener('click', () => search(b.dataset.legalWorkspaceTopic || ''));
    });
    copy?.addEventListener('click', async () => {
      if (!activePost) return;
      try {
        await navigator.clipboard.writeText([activePost.title, activePost.source, activePost.url, activePost.body].join('\n\n'));
        show('공개 법률자료를 복사했습니다.');
      } catch (_) { show('복사가 차단되었습니다. 브라우저 권한을 확인하세요.'); }
    });
    send?.addEventListener('click', () => {
      if (!activePost) return;
      // This transfers only a public citation selected by the user; no case/client data.
      sessionStorage.setItem('lawygo_public_research_v1', JSON.stringify({
        title: activePost.title, summary: activePost.summary, source: activePost.source, url: activePost.url
      }));
      location.href = '/p/note#note-native-workspace';
    });
    const fromUrl = new URLSearchParams(location.search).get('q');
    if (fromUrl && fromUrl.trim().length >= 2) search(fromUrl);
    else results.append(make('p', '법률 분야를 선택하거나 검색어를 입력하세요.', 'lnw-caption'));
  }
  function noteStudio() {
    const root = $('note-native-workspace');
    if (!root) return;
    const status = $('lawygoNoteIntegratedStatus');
    const importButton = $('lawygoNoteImportCitation');
    const availableTools = root.querySelectorAll('[data-note-start]');
    const draft = $('noteDraftContent');
    availableTools.forEach((btn) => btn.addEventListener('click', () => {
      const key = btn.dataset.noteStart || '';
      if (['blank', 'case', 'evidence', 'research'].includes(key)) {
        const original = document.querySelector('[data-note-template="' + key + '"]');
        original?.click();
        $('noteDraftTitle')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        status.textContent = '기존 NOTE 임시 편집기에서 ' + btn.textContent.trim() + ' 서식을 불러왔습니다.';
      }
    }));
    importButton?.addEventListener('click', () => {
      let citation;
      try { citation = JSON.parse(sessionStorage.getItem('lawygo_public_research_v1') || 'null'); }
      catch (_) { citation = null; }
      if (!citation?.title) {
        status.textContent = 'WIKI에서 공개 자료를 선택해 「NOTE로 보내기」를 눌러 주세요.';
        return;
      }
      const sourceText = [citation.title, citation.summary, citation.source, citation.url].filter(Boolean).join('\n');
      if (draft) {
        draft.value = (draft.value.trim() ? draft.value + '\n\n' : '') + '【WIKI 공개자료 참고】\n' + sourceText;
        draft.dispatchEvent(new Event('input', { bubbles: true }));
        draft.scrollIntoView({ behavior: 'smooth', block: 'center' });
        status.textContent = '공개 인용 정보를 임시 편집기로 불러왔습니다. 서버에는 자동 저장하지 않습니다.';
      }
      sessionStorage.removeItem('lawygo_public_research_v1');
    });
  }
  async function panLiveStudio() {
    const root = $('pan-legal-live-feed');
    if (!root) return;
    try {
      const data = await api('/api/pan/content?type=all&limit=25');
      const items = (Array.isArray(data.items) ? data.items : []).filter(
        (x) => LEGAL.test([x.title, x.summary].join(' '))
      );
      root.replaceChildren();
      if (!items.length) {
        root.append(make('p', '아직 연결된 공개 법률 영상·기사 피드가 없습니다. 승인된 소스가 등록되면 이곳에 표시됩니다.', 'pan-live-empty'));
        return;
      }
      items.slice(0, 5).forEach((item) => {
        const href = safeLink(item.url);
        if (!href) return;
        const a = make('a');
        a.href = href;
        if (new URL(href).origin !== location.origin) {
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
        }
        a.append(make('small', [item.content_type === 'shorts' ? 'SHORTS' : item.content_type === 'video' ? 'VIDEO' : 'ARTICLE', item.source || '공개 출처'].join(' · ')));
        a.append(make('strong', item.title || '법률 콘텐츠'));
        root.append(a);
      });
      if (!root.children.length) root.append(make('p', '표시할 수 있는 법률 원문 링크가 없습니다.', 'pan-live-empty'));
    } catch (_) {
      root.replaceChildren(make('p', '법률 피드를 불러오지 못했습니다. 기존 콘텐츠 영역에서 다시 조회할 수 있습니다.', 'pan-live-empty'));
    }
  }
  wikiStudio();
  noteStudio();
  panLiveStudio();
})();
