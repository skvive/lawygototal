// LAWYGO customer-delivery browser smoke and screenshot audit.
// Runs against a LOCAL FastAPI/SQLite copy; never writes to production.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:8018';
const OUT = process.env.QA_OUT_DIR || 'qa-output';
const ROUTES = ['/', '/journal', '/p/wiki', '/p/note', '/pro', '/p/pan', '/channel', '/pricing', '/partnership', '/payment', '/dashboard', '/strategy', '/p/channel'];
const SCREENS = [{name:'desktop',width:1440,height:900},{name:'tablet',width:768,height:1024},{name:'mobile',width:390,height:844},{name:'mobile-small',width:360,height:780}];
const slug = route => route === '/' ? 'home' : route.replace(/^\/|\/$/g,'').replace(/\//g,'-');
(async () => {
  fs.mkdirSync(path.join(OUT,'screens'),{recursive:true});
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  const results = []; const interactions = [];
  for (const screen of SCREENS) {
    const context = await browser.newContext({viewport:{width:screen.width,height:screen.height},isMobile:screen.name==='mobile',hasTouch:screen.name==='mobile'});
    for (const route of ROUTES) {
      const page = await context.newPage(); const pageErrors=[];
      page.on('pageerror',err=>pageErrors.push(err.message.slice(0,200)));
      let http=0,error='';
      try {const res=await page.goto(BASE+route,{waitUntil:'domcontentloaded',timeout:30000});http=res.status();await page.waitForTimeout(500)}
      catch(e){error=String(e).slice(0,200)}
      let metrics={};
      if(!error) {
        metrics=await page.evaluate(()=>{
          const w=window.innerWidth;const imgs=[...document.images];
          const fields=[...document.querySelectorAll('input:not([type=hidden]),select,textarea')];
          return {
            title:document.title,
            scrollWidth:document.documentElement.scrollWidth,
            overflow:document.documentElement.scrollWidth>w+3,
            overflowElements:[...document.querySelectorAll('body *')].filter(e=>{
              const rect=e.getBoundingClientRect();
              const style=getComputedStyle(e);
              return rect.right>w+3&&rect.left<w+3&&rect.width>0
                &&style.position!=='fixed'&&style.visibility!=='hidden';
            }).slice(0,12).map(e=>({tag:e.tagName,class:String(e.className||'').slice(0,80),
                id:e.id,right:Math.round(e.getBoundingClientRect().right),width:Math.round(e.getBoundingClientRect().width)})),
            brokenImages:imgs.filter(i=>{
              const r=i.getBoundingClientRect();
              const nearViewport=r.top<window.innerHeight+120&&r.bottom>-120;
              // Off-screen native lazy images are intentionally not fetched yet.
              return nearViewport&&(i.currentSrc||i.loading!=='lazy')&&(!i.complete||!i.naturalWidth);
            }).map(i=>(i.currentSrc||i.getAttribute('src')||'(missing-src)').slice(0,160)),
            images:imgs.length,
            platformButtons:document.querySelectorAll('#lawygoPlatformSwitcher .lawygo-switcher-link').length,
            wikiTopicButtons:document.body.dataset.product==='wiki'?document.querySelectorAll('[data-wiki-topic]').length:null,
            noteEditor:document.body.dataset.product==='note'?!!document.getElementById('noteDraftContent'):null,
            deliveryCards:document.querySelectorAll('.delivery-feature').length,
            tinyDeliveryMedia:[...document.querySelectorAll('.delivery-feature-media')].filter(e=>e.getBoundingClientRect().height<112).length,
            // Delivery-critical: ensure service imagery is compact and user-facing buttons are tappable.
            catalogMediaOversize:[...document.querySelectorAll('.ly-catalog>a>img')].filter(e=>e.getBoundingClientRect().height>(w<=480?130:w<=750?155:195)).length,
            catalogCardsOversize:[...document.querySelectorAll('.ly-catalog>a')].filter(e=>e.getBoundingClientRect().height>(w<=480?365:440)).length,
            premiereMediaOversize:[...document.querySelectorAll('.ly-premiere-panel>img')].filter(e=>e.getBoundingClientRect().height>(w<=480?190:w<=750?250:335)).length,
            tinyMarketingCTAs:[...document.querySelectorAll('.ly-premiere-actions a, .ly-feature-link, body[data-page=pro] .pro-login-btn')].filter(e=>e.getBoundingClientRect().height<42).length,
            stylesheetDelivery:[...document.styleSheets].some(sh=>String(sh.href||'').includes('lawygo-delivery-20261103.css')),

            primaryButtons:[...document.querySelectorAll('.hero-buttons .btn')].filter(e=>e.getBoundingClientRect().height<40).length,
            main:!!document.querySelector('main,[role=main]'),
            homeHeroImage:document.body.dataset.page==='home' ? getComputedStyle(document.querySelector('.hero-bg.hero-global')).backgroundImage : null,
            homeFirstContentGap:document.body.dataset.page==='home' ? Math.round(document.querySelector('.cream .sec-heading').getBoundingClientRect().top-document.querySelector('.cream').getBoundingClientRect().top) : null,
            homeHeroHeight:document.body.dataset.page==='home' ? Math.round(document.querySelector('.hero').getBoundingClientRect().height) : null,
            h1:document.querySelectorAll('h1').length,
            unlabeledFields:fields.filter(x=>!x.labels?.length&&!x.getAttribute('aria-label')&&!x.getAttribute('placeholder')).map(x=>x.outerHTML.slice(0,120))
          };
        });
        await page.screenshot({path:path.join(OUT,'screens',screen.name+'_'+slug(route)+'.jpg'),type:'jpeg',quality:70,fullPage:true,animations:'disabled',timeout:25000});
      }
      results.push({view:screen.name,route,http,error,pageErrors,...metrics});
      console.log(screen.name,route,http,metrics.overflow?'OVERFLOW':'OK',pageErrors.length);
      await page.close();
    }
    const p=await context.newPage();
    await p.goto(BASE+'/',{waitUntil:'domcontentloaded'});
    if(screen.name==='mobile'){
      const toggle=p.locator('.menu-toggle').first();
      if(await toggle.count()){const before=await toggle.getAttribute('aria-expanded');await toggle.click();const after=await toggle.getAttribute('aria-expanded');interactions.push({test:'mobile-menu-toggle',pass:before!==after})}
    }
    await p.locator('#newsletterEmail').fill('not-an-email');
    interactions.push({test:screen.name+'-newsletter-invalid-email',pass:!(await p.locator('#newsletterEmail').evaluate(e=>e.checkValidity()))});
    await p.goto(BASE+'/dashboard',{waitUntil:'domcontentloaded'});
    interactions.push({test:screen.name+'-login-empty-required',pass:!(await p.locator('#email').evaluate(e=>e.checkValidity()))});
    await p.close();await context.close();
  }
  // User-facing links and mocked public reader: no transactions or production writes.
  const w = await browser.newPage({viewport:{width:390,height:844}});
  await w.route('**/api/wiki/search**',async route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({items:[{id:'qa-reader-article',title:'공개 법률정보 테스트',summary:'검색 결과에서 상세내용을 열어야 합니다.',kind:'encyclopedia'}]})}));
  await w.route('**/api/posts/qa-reader-article',async route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'qa-reader-article',title:'공개 법률정보 테스트',body:'본문 열기 정상 검증',kind:'encyclopedia',updated_at:'2026-11-02'})}));
  await w.goto(BASE+'/p/wiki',{waitUntil:'domcontentloaded'});
  try {
    await w.locator('#wiki-results button.delivery-textlink').first().click({timeout:12000});
    const dlg=w.locator('#wikiReader');
    await w.waitForFunction(() => document.querySelector('#wikiReaderBody')?.textContent === '본문 열기 정상 검증',null,{timeout:8000});
    const readerBody=await dlg.locator('#wikiReaderBody').textContent();
    console.log('WIKI_READER_BODY',readerBody);
    interactions.push({test:'wiki-public-article-detail-dialog',pass:await dlg.isVisible()&&readerBody==='본문 열기 정상 검증'});
    await w.locator('.delivery-reader-close').click();
    interactions.push({test:'wiki-reader-close-button',pass:!(await dlg.isVisible())});
  }catch(e){interactions.push({test:'wiki-reader-click',pass:false,error:String(e).slice(0,250)})}
  try{
    await w.locator('[data-wiki-topic="민법"]').click();
    await w.waitForFunction(()=>document.getElementById('wikiq')?.value==='민법',null,{timeout:5000});
    interactions.push({test:'wiki-facet-shortcut-search',pass:await w.locator('#wikiq').inputValue()==='민법'});
    const destination=await w.locator('#lawygoPlatformSwitcher a[href="/p/note"]').getAttribute('href');
    interactions.push({test:'wiki-to-note-switcher',pass:destination==='/p/note'});
  }catch(e){interactions.push({test:'wiki-facet-nav',pass:false,error:String(e).slice(0,230)})}
  // Inline encyclopedia and public citation transfer: original AI secrets remain isolated.
  try {
    await w.locator('#lawygoWikiStudioInput').fill('민법');
    await w.locator('#lawygoWikiStudioForm button[type="submit"]').click();
    await w.locator('#lawygoWikiStudioResults button.lnw-result').first().click({timeout:8000});
    await w.waitForFunction(() => document.querySelector('#lawygoWikiStudioBody')?.textContent === '본문 열기 정상 검증',null,{timeout:8000});
    interactions.push({test:'wiki-native-encyclopedia-search',pass:(await w.locator('#lawygoWikiStudioTitle').textContent())==='공개 법률정보 테스트'});
    await w.locator('#lawygoWikiStudioSend').click();
    await w.waitForURL('**/p/note#note-native-workspace',{timeout:8000});
    await w.locator('#lawygoNoteImportCitation').click();
    const imported=await w.locator('#noteDraftContent').inputValue();
    interactions.push({test:'wiki-to-note-public-citation-only',pass:imported.includes('【WIKI 공개자료 참고】')&&imported.includes('공개 법률정보 테스트')});
  } catch(e) { interactions.push({test:'wiki-note-integrated-workspace',pass:false,error:String(e).slice(0,260)})}
  await w.goto(BASE+'/p/note',{waitUntil:'domcontentloaded'});
  try{
    await w.locator('[data-note-template="case"]').click();
    const content=await w.locator('#noteDraftContent').inputValue();
    interactions.push({test:'note-template-load',pass:content.includes('[확인된 사실]')});
    w.once('dialog',dialog=>dialog.accept());
    await w.locator('#noteClearDraft').click();
    interactions.push({test:'note-clear',pass:(await w.locator('#noteDraftContent').inputValue())===''});
    const link=await w.locator('.note-ai-rail a').first().getAttribute('href');
    interactions.push({test:'advanced-ai-workspace-link',pass:link==='https://lawygo.vercel.app/board/ai/case_search'});
  }catch(e){interactions.push({test:'note-workspace',pass:false,error:String(e).slice(0,250)})}
  await w.goto(BASE+'/p/pan',{waitUntil:'domcontentloaded'});
  try {
    const tabs=w.locator('#pan-content-tabs button');
    const target=tabs.filter({hasText:'블로그'}).first();
    if(await target.count()) {await target.click(); interactions.push({test:'pan-blog-tab-click',pass:await target.evaluate(e=>e.classList.contains('active'))})}
  }catch(e){interactions.push({test:'pan-blog-tab-click',pass:false,error:String(e).slice(0,250)})}
  // Live-format legal-only preview and source-aligned journal/PRO product pages.
  try {
    await w.route('**/api/pan/content?**', async route => route.fulfill({
      status:200,contentType:'application/json',
      body:JSON.stringify({items:[
        {id:'qa-legal',content_type:'video',title:'형사 변호사 판례 해설',summary:'법률 상담 주제',source:'공개 법률 영상',url:'https://www.youtube.com/watch?v=aq123456789'},
        {id:'qa-fashion',content_type:'video',title:'패션 신상품',summary:'쇼핑 할인',source:'쇼핑 채널',url:'https://www.youtube.com/watch?v=ab123456789'}
      ]})
    }));
    await w.goto(BASE+'/p/pan',{waitUntil:'domcontentloaded'});
    await w.waitForFunction(() => document.querySelector('#pan-legal-live-feed')?.textContent?.includes('형사 변호사 판례 해설'),null,{timeout:9000});
    const liveBody=await w.locator('#pan-legal-live-feed').textContent();
    interactions.push({test:'pan-native-legal-live-filter',pass:liveBody.includes('형사 변호사 판례 해설')&&!liveBody.includes('패션 신상품')});
    await w.locator('#pan-legal-live-feed a').first().click();
    const embed=await w.locator('#pan-legal-player-frame iframe').getAttribute('src');
    interactions.push({test:'pan-legal-video-embed',pass:embed==='https://www.youtube-nocookie.com/embed/aq123456789'});
    await w.locator('#pan-legal-player-close').click();
    interactions.push({test:'pan-legal-video-close',pass:await w.locator('#pan-legal-player').evaluate(el=>el.hidden)});
    await w.goto(BASE+'/pro',{waitUntil:'domcontentloaded'});
    interactions.push({test:'pro-official-site-home-mirror',pass:await w.locator('#pro-source-home').count()===1&&(await w.locator('#pro-source-title').textContent()).includes('대한민국 법원')});
    await w.goto(BASE+'/journal',{waitUntil:'domcontentloaded'});
    interactions.push({test:'weeklynews-logo-and-attribution',pass:await w.locator('.weeklynews-partner img[src="/static/img/weeklynews-w.svg"]').count()===1&&(await w.locator('.weeklynews-partner').textContent()).includes('위클리뉴스 제공 기사')});
  } catch(e) { interactions.push({test:'source-integration-browser-qa',pass:false,error:String(e).slice(0,260)})}
  await w.close();
  await browser.close();
  const critical=results.filter(x=>x.http!==200||x.error||x.overflow||x.pageErrors.length||x.brokenImages?.length||x.platformButtons!==5||(x.route==='/p/wiki'&&x.wikiTopicButtons!==6)||(x.route==='/p/note'&&!x.noteEditor)||x.tinyDeliveryMedia||x.catalogMediaOversize||x.catalogCardsOversize||x.premiereMediaOversize||x.tinyMarketingCTAs||(!x.stylesheetDelivery&&x.route!=='/dashboard')||x.primaryButtons||(['\/p\/wiki','\/p\/note','\/pro','\/channel'].includes(x.route)&&x.deliveryCards<3)||!x.main||x.h1<1||x.unlabeledFields?.length||(x.route==='/'&&(!x.homeHeroImage?.includes('hero-sunset-20261102.webp')||(x.view==='mobile'&&(x.homeFirstContentGap>85||x.homeHeroHeight>540)))));
  const report={base:BASE,at:new Date().toISOString(),count:results.length,critical:critical.length,results,interactions};
  fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(report,null,2));
  console.log('RESULT',JSON.stringify({pages:report.count,critical:critical.map(x=>({view:x.view,route:x.route,error:x.error,overflow:x.overflow,offenders:x.overflowElements,js:x.pageErrors,broken:x.brokenImages,catalogMedia:x.catalogMediaOversize,catalogCards:x.catalogCardsOversize,premiereMedia:x.premiereMediaOversize,tinyCTAs:x.tinyMarketingCTAs,style:x.stylesheetDelivery,main:x.main,h1:x.h1,unlabeled:x.unlabeledFields})),interactions}));
  if(critical.length||interactions.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});

