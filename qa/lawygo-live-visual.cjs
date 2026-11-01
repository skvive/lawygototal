// Read-only production visual QA. Never submit forms, log in, or modify data.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const BASE = process.env.LIVE_BASE_URL || 'https://lawygo.lexid.site';
const OUT = process.env.QA_OUT_DIR || 'live-browser-qa';
const routes = ['/', '/journal', '/p/wiki', '/p/note', '/pro', '/p/pan', '/channel', '/pricing', '/partnership', '/payment', '/dashboard', '/strategy', '/p/channel'];
const screens = [{name:'desktop',width:1440,height:900},{name:'tablet',width:768,height:1024},{name:'mobile',width:390,height:844},{name:'mobile-360',width:360,height:780}];
const slug = s => s === '/' ? 'home' : s.slice(1).replaceAll('/','-');
(async () => {
  fs.mkdirSync(path.join(OUT,'screens'),{recursive:true});
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  const records=[]; const linkPaths=new Set();
  for(const viewport of screens){
    const context = await browser.newContext({viewport:{width:viewport.width,height:viewport.height},isMobile:viewport.name.startsWith('mobile'),hasTouch:viewport.name.startsWith('mobile')});
    // All HTTP methods except GET/HEAD are blocked, including analytics and newsletter.
    await context.route('**/*', async route => {
      const method=route.request().method();
      if(method!=='GET'&&method!=='HEAD') return route.abort('blockedbyclient');
      return route.continue();
    });
    for(const routePath of routes){
      const page=await context.newPage();const uncaught=[];
      page.on('pageerror',e=>uncaught.push(String(e).slice(0,220)));
      let status=0,error='';
      try {
        const response=await page.goto(BASE+routePath,{waitUntil:'domcontentloaded',timeout:40000});
        status=response?.status()||0;
        await page.waitForTimeout(700);
        // Analytics requests can prevent networkidle forever. Wait only for visible images.
        await page.evaluate(() => Promise.all([...document.images].map(img => img.complete
          ? Promise.resolve()
          : Promise.race([img.decode().catch(()=>{}),new Promise(resolve=>setTimeout(resolve,1600))]))));
      }catch(e){error=String(e).slice(0,250)}
      let info={};
      if(!error){
        info=await page.evaluate(()=>{
          const badImages=[...document.images].filter(x=>!x.complete||!x.naturalWidth).map(x=>x.currentSrc.slice(0,120));
          const width=document.documentElement.scrollWidth;
          const links=[...document.querySelectorAll('a[href^="/"]')].map(a=>a.getAttribute('href').split('#')[0].split('?')[0]).filter(Boolean);
          const cards=document.querySelectorAll('.delivery-feature').length;
          return {title:document.title,documentWidth:width,viewportWidth:innerWidth,overflow:width>innerWidth+3,brokenImages:badImages,main:!!document.querySelector('main,[role=main]'),h1:document.querySelectorAll('h1').length,cards,links};
        });
        if(viewport.name==='desktop')info.links.forEach(v=>linkPaths.add(v));
        try{await page.screenshot({path:path.join(OUT,'screens',viewport.name+'_'+slug(routePath)+'.jpg'),type:'jpeg',quality:73,fullPage:true,animations:'disabled',timeout:30000})}
        catch(e){error='screenshot: '+String(e).slice(0,150)}
      }
      const {links,...rest}=info;
      const record={viewport:viewport.name,route:routePath,status,error,uncaught,...rest};
      records.push(record);
      console.log(viewport.name,routePath,status,record.overflow?'OVERFLOW':'OK',error||'');
      await page.close();
    }
    await context.close();
  }
  // Read-only GET verification for all public site's internal navigation destinations.
  const linkChecks=[];
  const http=await browser.newContext();
  for(const href of [...linkPaths].filter(v=>v.startsWith('/')&&!v.startsWith('/api/')&&v!=='/favicon.ico').sort()){
    try{const r=await http.request.get(BASE+href,{timeout:12000});linkChecks.push({href,status:r.status()})}
    catch(e){linkChecks.push({href,error:String(e).slice(0,180)})}
  }
  await http.close();await browser.close();
  const failures=records.filter(x=>x.status!==200||x.error||x.overflow||x.uncaught?.length||x.brokenImages?.length||!x.main||x.h1<1||(['\/p\/wiki','\/p\/note','\/pro','\/channel'].includes(x.route)&&x.cards<3));
  const linkFailures=linkChecks.filter(x=>x.status!==200);
  const report={source:BASE,mode:'READ_ONLY_PRODUCTION',timestamp:new Date().toISOString(),viewports:screens,routeCount:routes.length,count:records.length,failures,linkFailures,linkChecks,records};
  fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(report,null,2));
  console.log('SUMMARY',JSON.stringify({screens:records.length,failures:failures.length,linkChecks:linkChecks.length,linkFailures:linkFailures.length}));
  if(failures.length||linkFailures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
