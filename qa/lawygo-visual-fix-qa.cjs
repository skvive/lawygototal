/* LAWYGO 2026-11-21 responsive reference and module navigation checks */
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const width of [360,390,412,768]){
   const page=await browser.newPage({viewport:{width,height:850}});
   for(const route of ['/journal','/p/wiki','/p/pan','/pro']){
    const response=await page.goto('http://127.0.0.1:8018'+route,{waitUntil:'domcontentloaded',timeout:25000});
    await page.waitForTimeout(350);
    const m=await page.evaluate(()=>{
     return {overflow:document.documentElement.scrollWidth>innerWidth+3,
      modules:document.querySelectorAll('.lp8-module').length,
      brand:document.querySelector('.lp8-wordmark')?.textContent?.trim(),
      journalEditorial:!!document.querySelector('.front-grid #journal-lead'),
      wikiText:!!document.querySelector('.wref-searchbox #wikiHomeQuery'),
      hasMain:!!document.querySelector('main')};
    });
    if(response.status()!==200||m.overflow||m.modules!==5||!m.hasMain||m.brand!=='LAWYGO JOURNAL'||
      (route==='/journal'&&!m.journalEditorial)||(route==='/p/wiki'&&!m.wikiText))throw Error(JSON.stringify({width,route,...m,http:response.status()}));
   }
   await page.close();
  }
  console.log('PASS: 360/390/412/768px, portal nav and restored journal newspaper and wiki reference page');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
