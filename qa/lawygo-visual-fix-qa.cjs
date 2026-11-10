const {chromium}=require('playwright');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try{
 for(const width of [360,390,412,768]){
  const page=await browser.newPage({viewport:{width,height:850}});
  for(const route of ['/','/p/wiki']){
   const r=await page.goto('http://127.0.0.1:8018'+route,{waitUntil:'domcontentloaded'});
   const v=await page.evaluate(()=>{
    const cols=(s)=>{const e=document.querySelector(s);return e?getComputedStyle(e).gridTemplateColumns.trim().split(' ').filter(Boolean).length:0};
    return {catalog:cols('.ly-catalog'),serviceCount:document.querySelectorAll('.ly-catalog > a').length,duplicateServiceBlocks:document.querySelectorAll('.product-grid,.home-bridge').length,wikiImage:!!document.querySelector('#lw26-zero img[src="/static/img/design/lawygo-wiki-study-20261110.svg"]'), wikiLink:!!document.querySelector('#lw26-edit-toggle')&&!!document.querySelector('#lawygoPlatformSwitcher'),rev:document.querySelector('meta[name="lawygo-design-revision"]')?.content,overflow:document.documentElement.scrollWidth>innerWidth+3};
   });
   if(r.status()!==200||v.overflow||v.rev!=='20261105-designrefresh3'||(route==='/'&&(v.duplicateServiceBlocks!==0||v.serviceCount!==5||(width<=412&&v.catalog!==1)))||(route==='/p/wiki'&&(!v.wikiImage||!v.wikiLink)))throw Error(JSON.stringify({route,width,...v}));
  }
  await page.close();
 }
 console.log('Design release viewport checks passed');
}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
