
/* LAWYGO public-only WIKI dashboard. Original authenticated AI remains at lawygo.vercel.app. */
(() => {
  "use strict";
  const root = document.getElementById("lawygo-wiki-dashboard");
  if (!root) return;
  const el = id => document.getElementById(id);
  const layout=el("lw26-layout");
  const input=el("lw26-keyword");
  const zero=el("lw26-zero"),results=el("lw26-results"),reader=el("lw26-reader");
  const status=el("lw26-status");
  const aiTarget="https://lawygo.vercel.app/board/ai/legal_encyclopedia";
  const kinds=["전체","판례","법령","서식","기타자료","관련법률문서"];
  let all=[],activeKind="전체",selected=null,requestSeq=0,query="";
  const kindLabel = value => {
    const k=String(value||"").trim().toLowerCase();
    if (["precedent","판례"].includes(k)) return "판례";
    if (["statute","law","법령"].includes(k)) return "법령";
    if (["form","template","서식"].includes(k)) return "서식";
    if (["document","legal_document","관련법률문서"].includes(k)) return "관련법률문서";
    return "기타자료";
  };
  const element=(tag,contents,cls)=>{
    const n=document.createElement(tag);
    if(contents!==null&&contents!==undefined)n.textContent=String(contents);
    if(cls)n.className=cls;
    return n;
  };
  const notify=msg=>{status.textContent=msg};
  const switchPanel=key=>{
    if(!["categories","document","answer","vector","proof"].includes(key))return;
    layout.dataset.activePanel=key;
    document.querySelectorAll("[data-lw26-tab]").forEach(btn=>{
      const on=btn.dataset.lw26Tab===key;
      btn.classList.toggle("is-current",on);btn.setAttribute("aria-pressed",String(on));
    });
  };
  const visible=()=>activeKind==="전체"?all:all.filter(x=>kindLabel(x.kind||x.category)===activeKind);
  const syncMeta=()=>{
    const count=visible().length;
    el("lw26-total").textContent=String(count);
    el("lw26-counter").textContent=query?count+"건":"WIKI";
    el("lw26-vector-count").textContent=query?count+"건":"—";
    el("lw26-vector-kind").textContent=activeKind;
    el("lw26-vector-state").textContent=query?query+" · "+count+"건":"검색을 시작해 보세요";
  };
  const updateAi=()=>{
    if(selected){
      el("lw26-ai-preview-title").textContent=selected.title||"법률 자료";
      el("lw26-ai-preview").textContent=(selected.summary||selected.body||"공개 자료의 원문 출처를 검토하세요.").slice(0,220);
      el("lw26-vector-description").textContent="선택된 공개자료: "+(selected.title||"법률 자료")+" · "+(selected.kind||"WIKI");
    }else{
      el("lw26-ai-preview-title").textContent=query?"검색 결과를 선택하세요":"법률 자료를 선택하세요";
      el("lw26-ai-preview").textContent="이 영역은 공개자료 미리보기이며, AI가 생성한 모범답안이 아닙니다. 고급 AI 분석은 원본 인증 엔진에서 수행합니다.";
      el("lw26-vector-description").textContent="이 패널에는 공개자료의 제목·종류·검색 건수만 표시합니다. 비공개 벡터DB 데이터는 표시하지 않습니다.";
    }
    const url=new URL(aiTarget);
    if(query)url.searchParams.set("keyword",query);
    el("lw26-ai-launch").href=url.href;
  };
  const displayResults=()=>{
    const filtered=visible();
    zero.hidden=true;reader.hidden=true;results.hidden=false;results.replaceChildren();
    const h=element("h3",query?"“"+query+"” 공개자료 검색":"공개 법률자료");
    results.append(h);
    if(!filtered.length){
      const msg=all.length?"선택한 자료 유형에 해당하는 공개 결과가 없습니다.":"공개 검수된 검색 결과가 없습니다. 다른 키워드로 검색해 주세요.";
      results.append(element("p",msg,"lw26-empty-result"));
    }else filtered.forEach((item)=>{
      if(!item.id)return;
      const btn=element("button",null,"lw26-result");
      btn.type="button";
      const cat=kindLabel(item.kind||item.category);
      btn.append(element("span",cat+" · 공개자료"));
      btn.append(element("strong",item.title||"제목 없음"));
      btn.append(element("p",(item.summary||"").slice(0,180)));
      btn.append(element("small",[item.source||"LAWYGO WIKI",item.updated_at?String(item.updated_at).slice(0,10):""].filter(Boolean).join(" · ")));
      btn.addEventListener("click",()=>{loadItem(item)});
      results.append(btn);
    });
    syncMeta();updateAi();
    notify("공개 법률자료 "+filtered.length+"건 · 원문 출처와 최신성을 확인하세요.");
  };
  const api=async url=>{
    const res=await fetch(url,{credentials:"same-origin",headers:{Accept:"application/json"}});
    if(!res.ok)throw new Error("공개자료 요청 실패 ("+res.status+")");
    return res.json();
  };
  const search=async value=>{
    const kw=String(value||"").trim().slice(0,100);
    if(kw.length<2){notify("검색어를 두 글자 이상 입력해 주세요.");input.focus();return}
    query=kw;selected=null;input.value=kw;switchPanel("document");
    const seq=++requestSeq;
    zero.hidden=true;reader.hidden=true;results.hidden=false;
    results.replaceChildren(element("p","공개자료를 검색하고 있습니다…","lw26-empty-result"));
    notify("공개자료 검색 중…");
    try{
      const data=await api("/api/wiki/search?q="+encodeURIComponent(kw)+"&limit=50");
      if(seq!==requestSeq)return;
      all=Array.isArray(data.items)?data.items.filter(x=>x&&x.id):[];
      displayResults();
    }catch(err){
      if(seq!==requestSeq)return;
      all=[];syncMeta();updateAi();
      results.replaceChildren(element("p","공개자료 검색에 실패했습니다. 네트워크 상태를 확인하세요.","lw26-empty-result"));
      notify(err.message||"검색 실패");
    }
  };
  const safeUrl=input=>{
    try{const u=new URL(String(input||""));return ["https:","http:"].includes(u.protocol)?u.href:null}catch{return null}
  };
  async function loadItem(item){
    selected={title:item.title||"법률 자료",summary:item.summary||"",kind:item.kind||"공개자료"};
    results.hidden=true;zero.hidden=true;reader.hidden=false;
    el("lw26-reader-title").textContent="공개자료 불러오는 중…";
    el("lw26-reader-content").textContent="";
    el("lw26-source").hidden=true;el("lw26-source").removeAttribute("href");
    updateAi();switchPanel("document");
    try{
      const data=await api("/api/posts/"+encodeURIComponent(String(item.id)));
      selected={...data,title:data.title||item.title||"법률 자료",summary:data.summary||item.summary||"",kind:data.kind||item.kind};
      el("lw26-reader-title").textContent=selected.title;
      el("lw26-reader-label").textContent=kindLabel(selected.kind).toUpperCase()+" · PUBLIC SOURCE";
      el("lw26-reader-meta").textContent=[selected.kind,selected.source,selected.updated_at?String(selected.updated_at).slice(0,10):""].filter(Boolean).join(" · ");
      el("lw26-reader-summary").textContent=selected.summary||"공개자료입니다. 원문에서 최신성을 확인하세요.";
      el("lw26-reader-content").textContent=selected.body||selected.summary||"본문이 제공되지 않았습니다.";
      const source=safeUrl(selected.external_url);
      if(source){el("lw26-source").href=source;el("lw26-source").hidden=false}
      updateAi();notify("본문을 불러왔습니다. 법률 검토에 앞서 출처를 확인하세요.");
    }catch(err){el("lw26-reader-title").textContent="본문을 열 수 없습니다";el("lw26-reader-content").textContent=err.message||"공개자료 요청에 실패했습니다.";notify("본문 열기 실패")}
  }
  const setFilter=kind=>{
    if(!kinds.includes(kind))return;
    activeKind=kind;
    document.querySelectorAll("[data-lw26-filter]").forEach(btn=>{
      const on=btn.dataset.lw26Filter===kind;
      btn.classList.toggle("is-active",on);btn.setAttribute("aria-pressed",String(on));
    });
    document.querySelectorAll("[data-lw26-kind]").forEach(btn=>btn.classList.toggle("is-active",btn.dataset.lw26Kind===kind));
    if(query)displayResults();else syncMeta();
    switchPanel(query?"document":"categories");
  };
  el("lw26-searchform")?.addEventListener("submit",e=>{e.preventDefault();search(input.value)});
  document.querySelectorAll("[data-lw26-query]").forEach(btn=>btn.addEventListener("click",()=>search(btn.dataset.lw26Query)));
  document.querySelectorAll("[data-lw26-filter]").forEach(btn=>btn.addEventListener("click",()=>setFilter(btn.dataset.lw26Filter)));
  document.querySelectorAll("[data-lw26-kind]").forEach(btn=>btn.addEventListener("click",()=>setFilter(btn.dataset.lw26Kind)));
  document.querySelectorAll("[data-lw26-tab]").forEach(btn=>btn.addEventListener("click",()=>switchPanel(btn.dataset.lw26Tab)));
  document.querySelectorAll("[data-lw26-jump]").forEach(btn=>btn.addEventListener("click",()=>switchPanel(btn.dataset.lw26Jump)));
  el("lw26-back-results")?.addEventListener("click",()=>{reader.hidden=true;displayResults()});
  el("lw26-copy")?.addEventListener("click",async()=>{
    const content=[selected?.title,selected?.source,selected?.body].filter(Boolean).join("\n\n");
    try{await navigator.clipboard.writeText(content);notify("공개자료를 복사했습니다.")}
    catch{notify("브라우저 복사 권한을 확인해 주세요.")}
  });
  el("lw26-memo-copy")?.addEventListener("click",async()=>{
    const memo=el("lw26-memo").value;
    if(!memo.trim()){notify("복사할 메모를 입력해 주세요.");return}
    try{await navigator.clipboard.writeText(memo);notify("임시 메모를 복사했습니다.")}
    catch{notify("브라우저 복사가 차단되었습니다.")}
  });
  el("lw26-ui-toggle")?.addEventListener("click",()=>{
    const pressed=el("lw26-ui-toggle").getAttribute("aria-pressed")==="true";
    el("lw26-ui-toggle").setAttribute("aria-pressed",String(!pressed));
    root.classList.toggle("lw26-compact",!pressed);
    notify(!pressed?"패널 탐색 모드로 변경했습니다.":"기본 패널 보기로 변경했습니다.");
  });
  const qs=new URLSearchParams(location.search).get("q");
  if(qs)search(qs);else{syncMeta();updateAi()}
})();
