/* LAWYGO website delivery QA: 13 public routes x 4 responsive viewports.
 * Runs only against localhost. Mocks API for interaction checks; no production data writes.
 */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:8018';
const OUT = process.env.QA_OUT_DIR || 'qa-output';
const ROUTES = ['/', '/journal', '/p/wiki', '/p/note', '/pro', '/p/pan', '/channel',
  '/pricing', '/partnership', '/payment', '/dashboard', '/strategy', '/p/channel'];
const SCREENS = [
 {name:'desktop',width:1440,height:900},
 {name:'tablet',width:768,height:1024},
 {name:'mobile',width:390,height:844},
 {name:'mobile-small',width:360,height:780}
];
const slug = route => route === '/' ? 'home' : route.replace(/^\/|\/$/g,'').replace(/\//g,'-');
const tasks = [];
(async()=>{
 fs.mkdirSync(path.join(OUT,'screens'),{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const results=[];
 for(const screen of SCREENS){
  const context=await browser.newContext({viewport:{width:screen.width,height:screen.height},
   isMobile:screen.name.startsWith('mobile'),hasTouch:screen.name.startsWith('mobile')});
  for(const route of ROUTES){
   const page=await context.newPage(),pageErrors=[];
   page.on('pageerror',error=>pageErrors.push(String(error.message).slice(0,180)));
   let http=0,error='',metrics={};
   try{
    const res=await page.goto(BASE+route,{waitUntil:'domcontentloaded',timeout:25000});
    http=res?.status()||0;
    await page.waitForTimeout(450);
    metrics=await page.evaluate(()=>{
     const w=window.innerWidth;
     const header=document.querySelector('.lp8-portal-top');
     const img=[...document.images].filter(x=>{
      try{const u=new URL(x.currentSrc||x.src);const r=x.getBoundingClientRect();
       return u.origin===location.origin&&r.top<innerHeight+150&&r.bottom>-150&&x.loading!=='lazy';
      }catch{return false;}
     });
     return {
      title:document.title,
      main:!!document.querySelector('main,[role="main"]'),
      headerVisible:!!header&&getComputedStyle(header).display!=='none',
      moduleCount:document.querySelectorAll('.lp8-module').length,
      overflow:document.documentElement.scrollWidth>w+3,
      documentWidth:document.documentElement.scrollWidth,
      brokenImages:img.filter(x=>x.complete&&!x.naturalWidth).map(x=>x.getAttribute('src')),
      journalSearch:!!document.getElementById('reference-search-form'),
      noteComposer:!!document.getElementById('lnw-chat-form'),
      panKorean:!!document.querySelector('body.pan-hub-page .pan-us-disclaimer'),
      proKorean:!!document.querySelector('.pro-ko-guide'),
      repeatedHomeNav:!!document.querySelector('.v7-fastbar,.v7-products')
     };
    });
    await page.screenshot({path:path.join(OUT,'screens',screen.name+'_'+slug(route)+'.jpg'),
      type:'jpeg',quality:68,fullPage:true,animations:'disabled',timeout:25000});
   }catch(e){error=String(e).slice(0,250);}
   results.push({screen:screen.name,route,http,error,pageErrors,...metrics});
   console.log(screen.name,route,http,error||metrics.overflow?'CHECK':'PASS');
   await page.close();
  }
  await context.close();
 }
 // Dedicated mocked interactions: real DOM and event handlers; no production writes.
 const testContext=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 const page=await testContext.newPage();
 const check=(name,pass,details)=>tasks.push({name,pass:!!pass,...(details?{details}: {})});
 try{
  await page.route('**/api/journal/feed',route=>route.fulfill({status:200,contentType:'application/json',
   body:JSON.stringify({kr:[{id:'qa-korean',title:'한국 지식재산 정책 개정',summary:'지식재산 및 법률 정책 안내',source:'공식 자료',
    published:'2026-11-21',url:'https://example.com/kr'}],us:[{id:'qa-english',title:'Federal Markets Policy Update',summary:'Markets in 2026',
    source:'U.S. public source',published:'2026-11-20',url:'https://example.com/us'}],editorial:[]})}));
  await page.goto(BASE+'/journal',{waitUntil:'domcontentloaded'});
  await page.locator('#reference-items .reference-item').first().waitFor({timeout:12000});
  check('library-real-source-list',await page.locator('.reference-item').count()===2);
  await page.locator('#reference-query').fill('지식재산');
  check('library-live-search',await page.locator('.reference-item').count()===1);
  await page.locator('#reference-query').fill('');
  await page.locator('[data-reference-topic="us"]').click();
  check('library-category-filter',await page.locator('.reference-item').count()===1);
  check('library-source-auto-translation-link',await page.locator('.reference-item-actions a[href^="https://translate.google.com/translate?"]').count()===1);
  check('library-no-decorative-hero',await page.locator('.front-grid,.lead-photo').count()===0);
  await page.unroute('**/api/journal/feed');
 }catch(e){check('library-interactions',false,String(e).slice(0,250))}
 try{
  await page.route('**/api/pan/content?**',route=>route.fulfill({status:200,contentType:'application/json',
   body:JSON.stringify({items:[{id:'qa-us-law',content_type:'us_legal',title:'U.S. Workplace Act',
    title_ko:'미국 근로자 보호 법률',title_original:'U.S. Workplace Act',summary:'Original summary',
    summary_ko:'한국어 편집 핵심 요약',translation_status:'editorial',source:'Law Firm',url:'https://example.com/law',
    published:'2026-11-21'}]})}));
  await page.goto(BASE+'/p/pan',{waitUntil:'domcontentloaded'});
  const card=page.locator('#pan-us-post-cards .pan-us-card').first();
  await card.waitFor({timeout:14000});
  check('pan-korean-editorial-title',(await card.textContent()).includes('미국 근로자 보호 법률'));
  await card.click();
  const detail=page.locator('#pan-post-detail');
  check('pan-source-translation-action',await detail.locator('a.pan-auto-translation-link').count()===1);
  check('pan-original-en-retained',(await detail.textContent()).includes('U.S. Workplace Act'));
  await page.unroute('**/api/pan/content?**');
 }catch(e){check('pan-korean-source-interaction',false,String(e).slice(0,250))}
 try{
  await page.goto(BASE+'/pro',{waitUntil:'domcontentloaded'});
  check('pro-korean-feature-guide',await page.locator('.pro-ko-guide-grid>div').count()===3);
  check('pro-official-product-link',(await page.locator('a.pro-launch').getAttribute('href')).startsWith('https://lawygo.com'));
 }catch(e){check('pro-korean-guide',false,String(e).slice(0,250))}
 try{
  await page.goto(BASE+'/p/note',{waitUntil:'domcontentloaded'});
  check('note-intact-composer',await page.locator('#lnw-chat-form').count()===1);
  check('note-decorative-mark-removed',await page.locator('.lawygo-ai-icon,.lawygo-ai-brand-mark').count()===0);
 }catch(e){check('note-smoke',false,String(e).slice(0,250))}
 await testContext.close();await browser.close();
 const critical=results.filter(r=>r.error||r.http!==200||r.pageErrors.length||r.overflow||r.brokenImages?.length||
  !r.main||!r.headerVisible||r.moduleCount!==5||
  (r.route==='/journal'&&!r.journalSearch)||
  (r.route==='/p/note'&&!r.noteComposer)||
  (r.route==='/pro'&&!r.proKorean)||
  (r.route==='/p/pan'&&!r.panKorean)||
  (r.route==='/'&&r.repeatedHomeNav));
 const report={at:new Date().toISOString(),base:BASE,total:results.length,critical:critical.length,results,tasks};
 fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(report,null,2));
 console.log('RESULT',JSON.stringify({screenshots:results.length,critical:critical.map(r=>({route:r.route,screen:r.screen,http:r.http,error:r.error,
    overflow:r.overflow,width:r.documentWidth,js:r.pageErrors,broken:r.brokenImages})),tasks}));
 if(critical.length||tasks.some(t=>!t.pass))process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1});
