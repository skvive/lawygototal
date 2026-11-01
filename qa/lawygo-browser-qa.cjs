// LAWYGO customer-delivery browser smoke and screenshot audit.
// Runs against a LOCAL FastAPI/SQLite copy; never writes to production.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:8018';
const OUT = process.env.QA_OUT_DIR || 'qa-output';
const ROUTES = ['/', '/journal', '/p/wiki', '/p/note', '/pro', '/p/pan', '/channel', '/pricing', '/partnership', '/payment', '/dashboard', '/strategy', '/p/channel'];
const SCREENS = [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}];
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
            brokenImages:imgs.filter(i=>!i.complete||!i.naturalWidth).map(i=>i.currentSrc.slice(0,160)),
            images:imgs.length,
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
  await browser.close();
  const critical=results.filter(x=>x.http!==200||x.error||x.overflow||x.pageErrors.length||x.brokenImages?.length||!x.main||x.h1<1||x.unlabeledFields?.length||(x.route==='/'&&(!x.homeHeroImage?.includes('hero-korea.jpg')||x.homeFirstContentGap>85||(x.view==='mobile'&&x.homeHeroHeight>540))));
  const report={base:BASE,at:new Date().toISOString(),count:results.length,critical:critical.length,results,interactions};
  fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(report,null,2));
  console.log('RESULT',JSON.stringify({pages:report.count,critical:critical.map(x=>({view:x.view,route:x.route,error:x.error,overflow:x.overflow,js:x.pageErrors,broken:x.brokenImages,main:x.main,h1:x.h1,unlabeled:x.unlabeledFields})),interactions}));
  if(critical.length||interactions.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
