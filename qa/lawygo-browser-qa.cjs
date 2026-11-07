// LAWYGO redesign smoke + 52 viewport screenshots. Runs on isolated test server.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path');
const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:8018';
const OUT=process.env.QA_OUT_DIR||'qa-output';
const ROUTES=['/','/p/wiki','/p/note','/pro','/p/pan','/pricing','/partnership','/payment','/dashboard','/strategy','/channel','/journal','/p/channel'];
const SIZES=[{name:'desktop',width:1440,height:900},{name:'tablet',width:768,height:1024},{name:'mobile',width:390,height:844},{name:'mobile-small',width:360,height:780}];
(async()=>{
 fs.mkdirSync(path.join(OUT,'screens'),{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const results=[],interactions=[];
 for(const size of SIZES){
  const context=await browser.newContext({viewport:{width:size.width,height:size.height},hasTouch:size.width<=390});
  for(const route of ROUTES){
   const page=await context.newPage();let error='',status=0;const errors=[];
   page.on('pageerror',e=>errors.push(String(e.message).slice(0,300)));
   try{const r=await page.goto(BASE+route,{waitUntil:'domcontentloaded',timeout:30000});status=r?.status()||0;await page.waitForTimeout(450)}catch(e){error=String(e)}
   let metrics={};
   if(!error){
    metrics=await page.evaluate(()=>{
     const w=innerWidth;const imgs=[...document.images];
     return {overflow:document.documentElement.scrollWidth>w+3,
      brokenImages:imgs.filter(i=>{const r=i.getBoundingClientRect();return r.top<innerHeight+120&&r.bottom>-120&&(i.currentSrc||i.loading!=='lazy')&&(!i.complete||!i.naturalWidth)}).map(i=>i.currentSrc||i.src),
      unlabeled:[...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(e=>!e.labels?.length&&!e.getAttribute('aria-label')&&!e.placeholder).map(e=>e.id),
      main:!!document.querySelector('main'),h1:document.querySelectorAll('h1').length,
      appNav:!!document.querySelector('header .desktop-nav a[href="/p/wiki"]'),
      overflowElements:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left<innerWidth+5&&r.right>innerWidth+3}).slice(0,9).map(e=>({tag:e.tagName,id:e.id,cls:String(e.className||'').slice(0,80),right:Math.round(e.getBoundingClientRect().right)})),
      unwantedJournalNav:!!document.querySelector('header a[href="/journal"]'),
      wiki:!!document.querySelector('#lawygoWikiStudioForm'),
      note:!!document.querySelector('#noteDraftContent'),
      products:document.querySelectorAll('.lx-feature').length};
    });
    await page.screenshot({path:path.join(OUT,'screens',size.name+'_'+(route==='/'?'home':route.slice(1).replaceAll('/','-'))+'.jpg'),type:'jpeg',quality:75,fullPage:true,animations:'disabled',timeout:25000});
   }
   results.push({size:size.name,route,status,error,errors,...metrics});
   await page.close();
  }
  await context.close();
 }
 const page=await browser.newPage({viewport:{width:390,height:844}});
 await page.route('**/api/wiki/search**',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({items:[{id:'qa-reader-article',title:'법률 상세 검증',summary:'법률자료',kind:'encyclopedia'}]})}));
 await page.route('**/api/posts/qa-reader-article',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'qa-reader-article',title:'법률 상세 검증',body:'원문 상세 정상',kind:'encyclopedia'})}));
 try{
  await page.goto(BASE+'/p/wiki');
  interactions.push({test:'wiki-inline-frame',pass:await page.locator('#lawygoWikiStudioForm').isVisible()});
  await page.locator('#lawygoWikiStudioInput').fill('민법');
  await page.locator('#lawygoWikiStudioForm button[type=submit]').click();
  await page.locator('#lawygoWikiStudioResults button.lnw-result').first().click({timeout:10000});
  await page.waitForFunction(()=>document.querySelector('#lawygoWikiStudioBody')?.textContent==='원문 상세 정상',null,{timeout:10000});
  interactions.push({test:'wiki-detail',pass:(await page.locator('#lawygoWikiStudioBody').textContent())==='원문 상세 정상'});
  interactions.push({test:'wiki-deep-link',pass:new URL(page.url()).searchParams.get('post')==='qa-reader-article'});
  await page.reload();
  await page.waitForFunction(()=>document.querySelector('#lawygoWikiStudioBody')?.textContent==='원문 상세 정상',null,{timeout:10000});
  interactions.push({test:'wiki-permalink-reload',pass:true});
  await page.locator('#lawygoWikiStudioSend').click();
  await page.waitForURL('**/p/note#note-native-workspace',{timeout:8000});
  await page.locator('#lawygoNoteImportCitation').click();
  interactions.push({test:'wiki-to-note-public-citation',pass:(await page.locator('#noteDraftContent').inputValue()).includes('법률 상세 검증')});
 }catch(e){interactions.push({test:'wiki-and-note-flow',pass:false,error:String(e).slice(0,300)})}
 try{
  await page.goto(BASE+'/p/note');
  await page.locator('[data-note-template="case"]').click();
  interactions.push({test:'note-template',pass:(await page.locator('#noteDraftContent').inputValue()).includes('[확인된 사실]')});
  interactions.push({test:'ai-backend-link',pass:(await page.locator('a[href="https://lawygo.vercel.app/board/ai/ai_search"]').count())>=1});
  page.once('dialog',d=>d.accept());
  await page.locator('#noteClearDraft').click();
  interactions.push({test:'note-clear',pass:(await page.locator('#noteDraftContent').inputValue())===''});
 }catch(e){interactions.push({test:'note-local-edit',pass:false,error:String(e).slice(0,300)})}
 try{
  await page.goto(BASE+'/');
  const btn=page.locator('.menu-toggle');await btn.click();
  interactions.push({test:'mobile-nav',pass:(await btn.getAttribute('aria-expanded'))==='true'});
  interactions.push({test:'four-platforms',pass:(await page.locator('.lx-feature').count())===4});
 }catch(e){interactions.push({test:'home-navigation',pass:false,error:String(e).slice(0,300)})}
 await page.close();await browser.close();
 const newProductRoutes=['/','/p/wiki','/p/note','/pro'];
 const legacyPages=['/journal','/p/channel','/dashboard'];
 const critical=results.filter(x=>x.status!==200||x.error||x.errors?.length||x.overflow||x.brokenImages?.length||x.unlabeled?.length||!x.main||(x.h1!==1&&!legacyPages.includes(x.route))||(newProductRoutes.includes(x.route)&&(!x.appNav||x.unwantedJournalNav))||(x.route==='/p/wiki'&&!x.wiki)||(x.route==='/p/note'&&!x.note)||(x.route==='/'&&x.products!==4));
 const report={pages:results.length,critical:critical.length,results,interactions};
 fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(report,null,2));
 console.log('RESULT',JSON.stringify({pages:results.length,critical:critical.slice(0,16),interactions}));
 if(critical.length||interactions.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
