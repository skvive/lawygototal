/* NOTE workspace navigation, retains existing editor and AI logic. */
(()=>{
  "use strict";
  if(document.body.dataset.product!=="note")return;
  const buttons=[...document.querySelectorAll("[data-ln26-view]")];
  const setMode=(mode)=>{
    const target=mode==="document"?"document":"ai";
    document.body.dataset.noteView=target;
    buttons.forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.ln26View===target)));
  };
  const fromHash=()=>{
    const hash=window.location.hash;
    if(["#note-native-workspace","#note-editor","#note-ai-tools"].includes(hash))setMode("document");
    else setMode("ai");
  };
  buttons.forEach(b=>b.addEventListener("click",()=>{
    setMode(b.dataset.ln26View);
    history.replaceState(null,"",b.dataset.ln26View==="document"?"#note-native-workspace":"#note-chat-workspace");
  }));
  document.addEventListener("click",e=>{
    const link=e.target.closest('a[href="#note-editor"],a[href="#note-native-workspace"]');
    if(link)setMode("document");
  });
  window.addEventListener("hashchange",fromHash);
  fromHash();
})();