// Facet shortcuts for existing authenticated/public LAWYGO search.
// Calls only the existing site's public search form; not source repository APIs.
(() => {
  const setup=()=>{
    const input=document.getElementById('wikiq');
    const form=document.getElementById('wiki-search-form');
    document.querySelectorAll('[data-wiki-topic]').forEach(btn=>{
      btn.addEventListener('click',()=>{
        if(!input||!form)return;
        const word=btn.dataset.wikiTopic;
        if(!word)return;
        input.value=word;
        form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
        form.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth',block:'center'});
        input.focus({preventScroll:true});
        document.querySelectorAll('[data-wiki-topic]').forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));
      });
      btn.setAttribute('aria-pressed','false');
    });
  };
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',setup,{once:true}):setup();
})();