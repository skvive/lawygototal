const {chromium}=require('playwright');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try{
 for(const width of [360,390,412,768,1440]){
  const page=await browser.newPage({viewport:{width,height:850}});
  for(const route of ['/','/p/wiki','/p/note']){
   const r=await page.goto('http://127.0.0.1:8018'+route,{waitUntil:'domcontentloaded'});
   const v=await page.evaluate(()=>{
    const e=document.querySelector('.lx-feature-grid');
    return {columns:e?getComputedStyle(e).gridTemplateColumns.trim().split(/\s+/).length:null,
      overflow:document.documentElement.scrollWidth>innerWidth+3,
      h1:document.querySelectorAll('h1').length,
      meta:document.querySelector('meta[name=lawygo-design-revision]')?.content,
      wiki:!!document.querySelector('#lawygoWikiStudioForm'),
      note:!!document.querySelector('#noteDraftContent'),
      journalNav:!!document.querySelector('header a[href="/journal"]')};
   });
   if(r.status()!==200||v.overflow||v.h1!==1||v.meta!=='20261108-workspace-first'||v.journalNav||
     (route==='/'&&v.columns!==(width<=720?1:2))||
     (route==='/p/wiki'&&!v.wiki)||(route==='/p/note'&&!v.note))throw Error(JSON.stringify({route,width,...v}));
  }
  await page.close();
 }
 console.log('PASS: mobile 360/390/412, tablet 768, desktop 1440, workspace first');
}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
