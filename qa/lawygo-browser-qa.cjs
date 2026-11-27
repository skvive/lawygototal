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
      journalEditorial:!!document.querySelector('.front-grid #journal-lead'),
      wikiTextIndex:!!document.querySelector('body.wiki-reference-v12 .wref-searchbox'),
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
   body:JSON.stringify({kr:[{id:'qa-korean',region:'kr',title:'한국 지식재산 정책 개정',summary:'지식재산 및 법률 정책 안내',source:'공식 자료',
    published:'2026-11-21',url:'https://example.com/kr'}],us:[{id:'qa-english',region:'us',title:'Federal Markets Policy Update',summary:'Markets in 2026',
    source:'U.S. public source',published:'2026-11-20',url:'https://example.com/us'}],editorial:[]})}));
  const photo='https://www.newswire.co.kr/qa-source-photo.png';
  // Intercept only the allowed source hostname with a synthetic PNG. No upstream dependency.
  await page.route(photo,route=>route.fulfill({status:200,contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')}));
  
  await page.route('**/api/pan/content?**',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({items:[
    {id:'qa-lead',content_type:'newswire',title:'법률 정책 주요 보도자료',summary:'테스트 원문',source:'뉴스와이어',published:'2026-11-22',url:'https://example.com/lead',thumb_url:photo},
    {id:'qa-kr',content_type:'newswire',title:'한국 지식재산 정책 개정',summary:'테스트 원문',source:'뉴스와이어',published:'2026-11-21',url:'https://example.com/kr',thumb_url:photo},
    {id:'qa-no-photo',content_type:'newswire',title:'사진 없는 기사',source:'뉴스와이어',published:'2026-11-23',url:'https://example.com/no-photo'},
    {id:'qa-untrusted',content_type:'newswire',title:'허용되지 않은 이미지 기사',source:'뉴스와이어',published:'2026-11-24',url:'https://example.com/untrusted',thumb_url:'https://example.com/untrusted.jpg'}
  ]})}));
  await page.goto(BASE+'/journal',{waitUntil:'domcontentloaded'});
  const card=page.locator('#journal-front-left .side-story').first();
  await card.waitFor({timeout:12000});
  check('journal-newspaper-layout',await page.locator('.front-grid,#journal-lead,#journal-front-left,#journal-right').count()===4);
  check('journal-live-feed-restored',(await card.textContent()).includes('한국 지식재산 정책 개정'));
  check('journal-original-reader-link',(await card.getAttribute('href'))==='https://example.com/kr'&&(await card.getAttribute('target'))==='_blank'&&(await card.getAttribute('rel')).includes('noopener'));
  check('journal-no-fabricated-photo',!(await page.locator('.front-grid').textContent()).includes('사진 없는 기사'));
  check('journal-newsletter-preserved',await page.locator('#newsletterSignupJournal').count()===1);
  check('journal-untrusted-photo-rejected',!(await page.locator('.front-grid').textContent()).includes('허용되지 않은 이미지 기사'));
 }catch(e){check('journal-restoration-smoke',false,String(e).slice(0,250))}
 finally{
  await page.unroute('**/api/journal/feed');
  await page.unroute('**/api/pan/content?**');
  await page.unroute('https://www.newswire.co.kr/qa-source-photo.png');
 }
 try{
  await page.route('**/api/posts?product=wiki&limit=12',route=>route.fulfill({status:200,contentType:'application/json',
   body:JSON.stringify({total:1,items:[{id:'qa-law',kind:'encyclopedia',title:'임대차 법률 용어',summary:'민법 계약',source:'공개 위키',updated_at:'2026-11-21'}]})}));
  await page.route('**/api/wiki/search?**',route=>route.fulfill({status:200,contentType:'application/json',
   body:JSON.stringify({items:[{id:'qa-law',kind:'encyclopedia',title:'임대차 법률 용어',summary:'민법 계약',source:'공개 위키'}]})}));
  await page.route('**/api/posts/qa-law',route=>route.fulfill({status:200,contentType:'application/json',
   body:JSON.stringify({id:'qa-law',kind:'encyclopedia',title:'임대차 법률 용어',summary:'민법 임대차',body:'임대차 자료 본문',source:'공개 위키'})}));
  await page.goto(BASE+'/p/wiki',{waitUntil:'domcontentloaded'});
  await page.locator('#wikiLatestList .wresult').first().waitFor({timeout:11000});
  check('wiki-text-first-layout',await page.locator('.wref-searchbox,.wref-topic-index').count()===2);
  check('wiki-real-public-index',(await page.locator('#wikiLatestList').textContent()).includes('임대차 법률 용어'));
  await page.locator('#wikiHomeQuery').fill('임대차');
  await page.locator('#wiki-home-search button[type="submit"]').click();
  await page.locator('#wikiResults .wresult').first().waitFor({timeout:11000});
  check('wiki-search-still-functional',await page.locator('#view-search').isVisible());
  await page.locator('#wikiResults .wresult').first().click();
  await page.locator('#wikiArticleTitle').getByText('임대차 법률 용어').waitFor({timeout:11000});
  check('wiki-article-reader-preserved',(await page.locator('#wikiArticleBody').textContent()).includes('임대차 자료 본문'));
  check('wiki-source-section-preserved',await page.locator('#wikiArticleSourceLabel').count()===1);
 }catch(e){check('wiki-reference-qa',false,String(e).slice(0,260))}
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
  check('pan-korean-navigation',(await page.locator('.pan-side-nav').first().textContent()).includes('법률 콘텐츠 홈'));
  check('pan-korean-hero',await page.locator('.pan-video-hero h1').innerText()==='법률 영상·전문가 콘텐츠');
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
  check('note-korean-text-heading',(await page.locator('#lnw-chat-welcome h1').innerText()).includes('법률자료 검색과 문서 정리'));
  check('note-visible-korean-send',(await page.locator('#lnw-chat-send').innerText()).trim()==='실행');
  check('note-editor-order',await page.evaluate(()=>document.getElementById('note-chat-workspace').compareDocumentPosition(document.getElementById('note-editor')) & Node.DOCUMENT_POSITION_FOLLOWING));
  await page.locator('[data-lnw-example]').first().click();
  check('note-quick-prompt-fills',((await page.locator('#lnw-chat-input').inputValue()).includes('개인정보')));
  await page.locator('[data-note-template="case"]').click();
  check('note-case-template-action',(await page.locator('#noteDraftTitle').inputValue())==='사건 검토 메모');
 }catch(e){check('note-smoke',false,String(e).slice(0,250))}
 try{
  const fixture=id=>({revision:{id,title:'합성 검수 문서 '+id,status:'draft',legal_as_of:'2026-11-27',body_markdown:'합성 검수 본문',digest:'a'.repeat(64)},citations:[],candidates:[],self_review_blocked:id===2});
  let release;const gate=new Promise(resolve=>{release=resolve});let submitted=null;
  await page.route('**/api/wiki/v2/revisions/*/review',async route=>{
   const id=Number(new URL(route.request().url()).pathname.split('/').at(-2));
   if(route.request().method()==='POST'){
    submitted={id,body:route.request().postDataJSON(),url:route.request().url()};
    await gate;return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({revision_id:id,decision:'revise',published:false})});
   }
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(fixture(id))});
  });
  await page.goto(BASE+'/static/legal-wiki-review.html',{waitUntil:'domcontentloaded'});
  await page.locator('#rid').fill('1');await page.locator('#open').click();await page.locator('#detail').waitFor();
  await page.locator('#notes').fill('합성 검수 의견');
  await page.locator('#reviewed').check();
  page.once('dialog',d=>d.accept());
  await page.locator('#revise').click();
  await page.waitForFunction(()=>document.getElementById('open').disabled&&document.getElementById('rid').disabled);
  check('wiki-review-mutation-lock',await page.locator('#approve').isDisabled()&&await page.locator('#rid').isDisabled());
  release();
  await page.locator('#notice').getByText('검수 결정 저장 완료').waitFor();
  check('wiki-review-private-notes-body',submitted?.id===1&&submitted.body.notes==='합성 검수 의견'&&!new URL(submitted.url).search);
  await page.locator('#rid').fill('2');await page.locator('#open').click();await page.locator('#title').getByText('합성 검수 문서 2').waitFor();
  check('wiki-review-self-approval-disabled',await page.locator('#approve').isDisabled()&&await page.locator('#revise').isDisabled()&&await page.locator('#reject').isDisabled());
  await page.unroute('**/api/wiki/v2/revisions/*/review');
 }catch(e){check('wiki-review-browser-fixture',false,String(e).slice(0,250))}
 try{
  let requested=0,payload;
  await page.route('**/api/me',r=>r.fulfill({json:{id:'fixture-user',role:'editor'}}));
  await page.route('**/api/posts?product=note&limit=100',r=>r.fulfill({json:{items:[{id:'own',product:'note',visibility:'private',author_id:'fixture-user',title:'합성 개인 노트'},{id:'other',product:'note',visibility:'private',author_id:'other',title:'다른 사용자 노트'}]}}));
  await page.route('**/api/note/own/ai-analyze',r=>{requested++;payload=r.request().postDataJSON();return r.fulfill({json:{result:{summary:'합성 분석 결과',issues:[{issue:'합성 쟁점',source_ids:['source-note']}],evidence_gaps:[],questions:[]},sources:[{id:'source-note',title:'합성 개인 노트',included_chars:30}]}})});
  await page.goto(BASE+'/static/legal-wiki-note-analysis.html',{waitUntil:'domcontentloaded'});
  await page.locator('#panel').waitFor();
  check('note-ai-owner-list',await page.locator('#notes option').count()===2);
  await page.locator('#notes').selectOption('own');
  check('note-ai-consent-gate',await page.locator('#run').isDisabled()&&requested===0);
  await page.locator('#consent').check();page.once('dialog',d=>d.accept());await page.locator('#run').click();
  await page.locator('#result').waitFor();
  check('note-ai-explicit-consent',requested===1&&payload.consent===true&&payload.wiki_query===null);
  check('note-ai-source-render',(await page.locator('#sources').textContent()).includes('source-note')&&!(await page.locator('#consent').isChecked()));
  await page.unroute('**/api/me');await page.unroute('**/api/posts?product=note&limit=100');await page.unroute('**/api/note/own/ai-analyze');
 }catch(e){check('note-ai-browser-fixture',false,String(e).slice(0,250))}
 try{
  const digest='a'.repeat(64);
  let sent=0,decision=null;
  await page.route('**/api/wiki/v2/source-review-queue',r=>r.fulfill({json:{items:[{payload_id:7,kind:'precedent',external_id:'fixture'}]}}));
  await page.route('**/api/wiki/v2/source-reviews/7',r=>{if(r.request().method()==='POST'){sent++;decision=r.request().postDataJSON();return r.fulfill({json:{verified:true}})}return r.fulfill({json:{payload_id:7,canonical_id:9,digest,verified:false,source_url:'https://www.law.go.kr/fixture',notice:'합성 테스트 자료',data:{kind:'precedent',external_id:'fixture',case_number:'합성 검수 판례',court:'합성 법원',decided_on:'2020-01-01',original_text:'합성 원문입니다'}}})});
  await page.goto(BASE+'/static/legal-wiki-source-review.html',{waitUntil:'domcontentloaded'});
  await page.locator('#load').click();await page.locator('#queue button').first().click();await page.locator('#detail').waitFor();
  check('source-review-confirmation-gate',await page.locator('#approve').isDisabled()&&sent===0);
  await page.locator('#notes').fill('합성 원문과 날짜를 대조한 검수 기록입니다.');
  await page.locator('#confirm').check();page.once('dialog',d=>d.accept());await page.locator('#approve').click();
  await page.locator('#status').getByText('원문 검증 등록 완료.',{exact:false}).waitFor();
  check('source-review-digest-bound',sent===1&&decision.expected_digest===digest&&decision.confirmed===true);
  check('source-review-after-verification-lock',await page.locator('#approve').isDisabled());
  await page.unroute('**/api/wiki/v2/source-review-queue');await page.unroute('**/api/wiki/v2/source-reviews/7');
 }catch(e){check('source-review-browser-fixture',false,String(e).slice(0,250))}
 await testContext.close();await browser.close();
 const critical=results.filter(r=>r.error||r.http!==200||r.pageErrors.length||r.overflow||r.brokenImages?.length||
  !r.main||!r.headerVisible||r.moduleCount!==5||
  (r.route==='/journal'&&!r.journalEditorial)||
  (r.route==='/p/wiki'&&!r.wikiTextIndex)||
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
