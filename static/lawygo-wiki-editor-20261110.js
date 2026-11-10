/* LAWYGO WIKI layout editor. Preserves original Encyclopedia layout editor behaviour in a self-contained public portal. */
(() => {
  "use strict";
  const root=document.getElementById("lawygo-wiki-dashboard");
  const grid=document.getElementById("lw26-layout");
  const editor=document.getElementById("lw26-editor");
  const bar=document.getElementById("lw26-editor-list");
  if(!root||!grid||!editor||!bar)return;
  const KEY="lawygo_total_wiki_layout_v2";
  const defaults=[
    {id:"categories",label:"종류",width:15,visible:true},
    {id:"document",label:"본문",width:34,visible:true},
    {id:"answer",label:"AI 모범답안",width:27,visible:true},
    {id:"vector",label:"요약·고정",width:11,visible:true},
    {id:"proof",label:"교정",width:13,visible:true}
  ];
  const el=id=>document.getElementById(id);
  const clone=value=>JSON.parse(JSON.stringify(value));
  const allowed=new Set(defaults.map(x=>x.id));
  const displayNodes=new Map(defaults.map(x=>[x.id,grid.querySelector('[data-lw26-panel="'+x.id+'"]')]));
  const tabs=new Map(defaults.map(x=>[x.id,root.querySelector('[data-lw26-tab="'+x.id+'"]')]));
  const localNotice=msg=>{if(el("lw26-status"))el("lw26-status").textContent=msg};
  const normalized=value=>{
    const raw=Array.isArray(value?.panels)?value.panels:[];
    const known=new Map(raw.filter(x=>x&&allowed.has(x.id)).map(x=>[x.id,x]));
    const panels=defaults.map((d,i)=>{
      const old=known.get(d.id)||{};
      return {id:d.id,label:d.label,visible:typeof old.visible==="boolean"?old.visible:true,
        width:Number.isFinite(+old.width)?Math.min(70,Math.max(8,+old.width)):d.width,
        order:Number.isFinite(+old.order)?Math.min(100,Math.max(0,+old.order)):i};
    }).sort((a,b)=>a.order-b.order).map((p,i)=>({...p,order:i}));
    if(!panels.some(p=>p.visible))panels[0].visible=true;
    return panels;
  };
  const load=()=>{
    try{const v=JSON.parse(localStorage.getItem(KEY)||"null");return normalized(v)}
    catch{return normalized(null)}
  };
  let saved=load(),current=clone(saved),editing=false,maximized=null;
  const minimized=new Set();
  const visible=()=>current.filter(x=>x.visible&&!minimized.has(x.id));
  const all=()=>[...current].sort((a,b)=>a.order-b.order);
  const persist=()=>{
    try{localStorage.setItem(KEY,JSON.stringify({version:1,panels:current.map(p=>({id:p.id,visible:p.visible,width:p.width,order:p.order}))}));return true}
    catch{return false}
  };
  const activeFallback=()=>{
    const id=grid.dataset.activePanel;
    if(!current.some(p=>p.id===id&&p.visible&&!minimized.has(id)))grid.dataset.activePanel=visible()[0]?.id||"document";
    tabs.forEach((btn,id)=>{
      if(!btn)return;
      const p=current.find(x=>x.id===id);
      btn.hidden=!p.visible||minimized.has(id);
      btn.classList.toggle("is-current",grid.dataset.activePanel===id);
      btn.setAttribute("aria-pressed",String(grid.dataset.activePanel===id));
    });
  };
  const clearHandles=()=>grid.querySelectorAll(".lw26-resizer").forEach(el=>el.remove());
  const positionHandles=()=>{
    const rect=grid.getBoundingClientRect();
    grid.querySelectorAll(".lw26-resizer").forEach(h=>{
      const node=displayNodes.get(h.dataset.left);
      if(!node||!node.offsetWidth)return;
      const b=node.getBoundingClientRect();
      h.style.left=(b.right-rect.left+1)+"px";
      h.style.height=Math.max(30,b.height-17)+"px";
    });
  };
  function buildHandles(){
    clearHandles();
    if(!editing||maximized||matchMedia("(max-width:1050px)").matches)return;
    const items=visible();
    items.slice(0,-1).forEach((p,i)=>{
      const adjacent=items[i+1];
      const h=document.createElement("div");
      h.className="lw26-resizer";h.role="separator";h.tabIndex=0;
      h.dataset.left=p.id;
      h.setAttribute("aria-label",p.label+"과 "+adjacent.label+" 너비 조절");
      h.setAttribute("aria-orientation","vertical");
      const move=delta=>{
        const left=current.find(x=>x.id===p.id),right=current.find(x=>x.id===adjacent.id);
        const total=left.width+right.width,old=left.width;
        left.width=Math.max(8,Math.min(total-8,Math.round((old+delta)*10)/10));
        right.width=Math.round((total-left.width)*10)/10;
        apply(false);
        syncControls();
      };
      h.addEventListener("keydown",e=>{
        if(e.key!=="ArrowRight"&&e.key!=="ArrowLeft")return;
        e.preventDefault();move(e.key==="ArrowRight"?2:-2);
      });
      h.addEventListener("pointerdown",e=>{
        if(e.button!==0)return;
        e.preventDefault();h.setPointerCapture(e.pointerId);
        const start=e.clientX,left=current.find(x=>x.id===p.id).width,right=current.find(x=>x.id===adjacent.id).width;
        const total=left+right;
        const usable=Math.max(grid.getBoundingClientRect().width-85,200);
        const onMove=ev=>{
          const change=(ev.clientX-start)/usable*100;
          const updated=Math.max(8,Math.min(total-8,Math.round((left+change)*10)/10));
          current.find(x=>x.id===p.id).width=updated;
          current.find(x=>x.id===adjacent.id).width=Math.round((total-updated)*10)/10;
          apply(false);syncControls();
        };
        const onEnd=()=>{
          h.removeEventListener("pointermove",onMove);h.removeEventListener("pointerup",onEnd);
          h.removeEventListener("pointercancel",onEnd);
          try{h.releasePointerCapture(e.pointerId)}catch{}
          localNotice("패널 폭 변경됨 · 저장 버튼을 누르세요.");
        };
        h.addEventListener("pointermove",onMove);
        h.addEventListener("pointerup",onEnd);
        h.addEventListener("pointercancel",onEnd);
      });
      grid.append(h);
    });
    requestAnimationFrame(positionHandles);
  }
  function apply(rebuild=true){
    const entries=visible();
    if(maximized&&!entries.some(x=>x.id===maximized))maximized=null;
    const desktop=matchMedia("(min-width:1051px)").matches;
    grid.classList.add("lw26-editor-grid");
    grid.classList.toggle("lw26-editing",editing);
    grid.classList.toggle("lw26-maximized",!!maximized);
    grid.style.gridTemplateAreas="none";
    grid.style.gridTemplateColumns=desktop?"56px "+entries.map(p=>Math.max(8,p.width)+"fr").join(" "):"";
    const rail=grid.querySelector(".lw26-rail");
    if(rail){rail.style.gridColumn=desktop?"1":"";rail.style.gridRow=desktop?"1":"";}
    current.forEach(p=>{
      const n=displayNodes.get(p.id);
      if(!n)return;
      n.hidden=!p.visible||minimized.has(p.id);
      n.classList.toggle("lw26-max-target",maximized===p.id);
      n.style.gridArea="auto";
      n.style.order=String(p.order);
      n.style.gridColumn=desktop?String(entries.findIndex(v=>v.id===p.id)+2):"";
      n.style.gridRow=desktop?"1":"";
    });
    tabs.forEach((node,id)=>{if(node)node.style.order=String(current.find(p=>p.id===id)?.order??0)});
    const tabsContainer=root.querySelector(".lw26-mobile-tabs");
    if(tabsContainer)all().forEach(p=>tabsContainer.append(tabs.get(p.id)));
    activeFallback();
    updateMinbar();
    if(rebuild)buildHandles();else requestAnimationFrame(positionHandles);
  }
  function updateMinbar(){
    const minbar=el("lw26-minbar");if(!minbar)return;
    minbar.replaceChildren();
    current.filter(p=>minimized.has(p.id)).forEach(p=>{
      const b=document.createElement("button");b.type="button";
      b.textContent="▢ "+p.label+" 복원";
      b.addEventListener("click",()=>{minimized.delete(p.id);apply();localNotice(p.label+" 패널을 복원했습니다.")});
      minbar.append(b);
    });
    minbar.hidden=!minimized.size;
  }
  const reorder=(id,delta)=>{
    const order=all(),idx=order.findIndex(p=>p.id===id),target=idx+delta;
    if(idx<0||target<0||target>=order.length)return;
    [order[idx],order[target]]=[order[target],order[idx]];
    order.forEach((p,i)=>p.order=i);
    current=order;
    apply();drawControls();localNotice("패널 순서 변경됨 · 저장 버튼을 누르세요.");
  };
  const setVisible=(id,on)=>{
    if(!on&&current.filter(p=>p.visible).length===1){localNotice("최소 한 개의 패널은 표시해야 합니다.");drawControls();return}
    const p=current.find(p=>p.id===id);if(!p)return;
    p.visible=on;
    if(!on){minimized.delete(id);if(maximized===id)maximized=null}
    apply();drawControls();
  };
  function syncControls(){
    current.forEach(p=>{
      const range=bar.querySelector('[data-lw26-width="'+p.id+'"]');
      const value=bar.querySelector('[data-lw26-width-label="'+p.id+'"]');
      if(range)range.value=p.width;
      if(value)value.textContent=Math.round(p.width)+"%";
    });
  }
  function drawControls(){
    bar.replaceChildren();
    all().forEach(p=>{
      const card=document.createElement("div");card.className="lw26-editor-item";card.draggable=true;card.dataset.panel=p.id;
      const drag=document.createElement("span");drag.className="lw26-editor-drag";drag.textContent="⠿";drag.title="드래그하여 순서 변경";
      const label=document.createElement("label");const check=document.createElement("input");check.type="checkbox";check.checked=p.visible;check.dataset.lw26Visible=p.id;
      label.append(check,document.createTextNode(p.label));
      check.addEventListener("change",()=>setVisible(p.id,check.checked));
      const prev=document.createElement("button");prev.type="button";prev.textContent="←";prev.title=p.label+" 왼쪽으로";prev.addEventListener("click",()=>reorder(p.id,-1));
      const next=document.createElement("button");next.type="button";next.textContent="→";next.title=p.label+" 오른쪽으로";next.addEventListener("click",()=>reorder(p.id,1));
      const range=document.createElement("input");range.type="range";range.min="8";range.max="70";range.step="1";range.value=String(p.width);range.dataset.lw26Width=p.id;range.setAttribute("aria-label",p.label+" 너비");
      range.addEventListener("input",()=>{current.find(x=>x.id===p.id).width=Number(range.value);apply(false);syncControls()});
      const size=document.createElement("span");size.dataset.lw26WidthLabel=p.id;size.textContent=Math.round(p.width)+"%";
      card.append(drag,label,prev,next,range,size);
      card.addEventListener("dragstart",e=>{e.dataTransfer.effectAllowed="move";e.dataTransfer.setData("text/plain",p.id);card.setAttribute("aria-grabbed","true")});
      card.addEventListener("dragend",()=>card.removeAttribute("aria-grabbed"));
      card.addEventListener("dragover",e=>e.preventDefault());
      card.addEventListener("drop",e=>{
        e.preventDefault();
        const dragId=e.dataTransfer.getData("text/plain");
        const from=all().findIndex(x=>x.id===dragId),to=all().findIndex(x=>x.id===p.id);
        if(from>=0&&to>=0)reorder(dragId,to-from);
      });
      bar.append(card);
    });
  }
  function toggleEditor(force){
    editing=typeof force==="boolean"?force:!editing;
    editor.hidden=!editing;
    const trigger=el("lw26-edit-toggle");
    trigger.setAttribute("aria-expanded",String(editing));
    trigger.textContent=editing?"✕ 편집 종료":"⚙ UI 편집";
    if(editing)drawControls();
    apply();
  }
  el("lw26-edit-toggle")?.addEventListener("click",()=>toggleEditor());
  el("lw26-editor-save")?.addEventListener("click",()=>{
    if(!persist()){localNotice("브라우저 저장이 차단되어 저장할 수 없습니다.");return}
    saved=clone(current);toggleEditor(false);localNotice("WIKI 패널 레이아웃을 이 브라우저에 저장했습니다.");
  });
  el("lw26-editor-reset")?.addEventListener("click",()=>{
    current=normalized(null);minimized.clear();maximized=null;
    if(!persist()){localNotice("설정 초기화 저장이 차단되었습니다.");return}
    saved=clone(current);apply();drawControls();localNotice("기본 패널 규격으로 초기화했습니다.");
  });
  el("lw26-editor-cancel")?.addEventListener("click",()=>{
    current=clone(saved);minimized.clear();maximized=null;toggleEditor(false);localNotice("미저장 편집을 취소했습니다.");
  });
  defaults.forEach(p=>{
    const panel=displayNodes.get(p.id);
    const head=panel?.querySelector(".lw26-panelhead");
    if(!head)return;
    const group=document.createElement("span");group.className="lw26-window-tools";
    const min=document.createElement("button");min.type="button";min.textContent="−";min.title=p.label+" 최소화";min.setAttribute("aria-label",p.label+" 최소화");
    min.addEventListener("click",()=>{minimized.add(p.id);if(maximized===p.id)maximized=null;apply();localNotice(p.label+" 패널을 최소화했습니다.")});
    const max=document.createElement("button");max.type="button";max.textContent="□";max.title=p.label+" 최대화/복원";max.setAttribute("aria-label",p.label+" 최대화 또는 복원");
    max.addEventListener("click",()=>{maximized=maximized===p.id?null:p.id;minimized.delete(p.id);apply();localNotice(maximized?p.label+" 패널 최대화":"전체 패널 보기")});
    group.append(min,max);head.append(group);
    head.draggable=true;
    head.addEventListener("dragstart",e=>{
      if(!editing){e.preventDefault();return}
      e.dataTransfer.setData("text/plain",p.id);e.dataTransfer.effectAllowed="move";
    });
    head.addEventListener("dragover",e=>{if(editing)e.preventDefault()});
    head.addEventListener("drop",e=>{
      if(!editing)return;
      e.preventDefault();const from=e.dataTransfer.getData("text/plain");
      const before=all().findIndex(x=>x.id===from),after=all().findIndex(x=>x.id===p.id);
      if(before>=0&&after>=0)reorder(from,after-before);
    });
  });
  root.querySelectorAll("[data-lw26-jump]").forEach(x=>x.addEventListener("dblclick",()=>{
    const id=x.dataset.lw26Jump;if(!allowed.has(id))return;
    maximized=maximized===id?null:id;apply();
  }));
  window.addEventListener("resize",()=>apply(),{passive:true});
  apply();
})();