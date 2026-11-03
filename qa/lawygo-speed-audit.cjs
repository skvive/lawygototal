// Non-mutating smoke timing probe from GitHub Actions, used before and after release.
// This measures edge HTTP response latency from the runner, not user's device LCP.
const fs = require('node:fs');
const {performance}=require('node:perf_hooks');

const origin=(process.env.PERF_BASE_URL||'https://lawygo.lexid.site').replace(/\/$/,'');
const paths=['/','/journal','/p/wiki','/p/pan','/api/journal/feed'];
const results=[];
const maxMs=16000;
async function measure(path,run){
  const url=origin+path+(path==='/api/journal/feed'?'':'');
  const start=performance.now();
  try{
    const res=await fetch(url,{
      method:'GET',
      redirect:'follow',
      headers:{'User-Agent':'LAWYGO-PERF-AUDIT/1.0','Accept':path.startsWith('/api/')?'application/json':'text/html'},
      signal:AbortSignal.timeout(maxMs)
    });
    const body=await res.arrayBuffer();
    return {path,run,status:res.status,ms:Math.round(performance.now()-start),
      bytes:body.byteLength,contentType:res.headers.get('content-type'),
      vercelCache:res.headers.get('x-vercel-cache')||'not-reported',
      vercelId:res.headers.get('x-vercel-id')?'present':'absent'};
  }catch(e){return {path,run,error:e.name||'request failed',ms:Math.round(performance.now()-start)}}
}
(async()=>{
 for(const path of paths){for(let i=1;i<=(path.startsWith('/api/')?1:3);i++)results.push(await measure(path,i));}
 fs.mkdirSync('qa-output',{recursive:true});
 const record={kind:'remote-edge-http',origin,recordedAt:new Date().toISOString(),results,
   note:'Runner-side HTTP timings; not actual end-user LCP and not proof of a cold start.'};
 fs.writeFileSync('qa-output/speed-audit.json',JSON.stringify(record,null,2));
 console.log(JSON.stringify(record,null,2));
})().catch(err=>{console.error(err);process.exitCode=1});
