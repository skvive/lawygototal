/* LAWYGO public FAQ local retrieval: read-only, source URL attached. Never pass private legal records. */
const norm=s=>String(s??"").normalize("NFKC").toLowerCase().replace(/[^가-힣a-z0-9]+/g," ").trim();
const grams=s=>{const z=new Set();for(const w of norm(s).split(/\s+/).filter(w=>w.length>1)){z.add(w);for(let i=0;w.length>2&&i<w.length-1;i++)z.add(w.slice(i,i+2))}return z};
export function searchPublicLawygoFaq(db,query,{limit=3}={}){
 const q=norm(query);if(!q||!Array.isArray(db?.entries))return[];
 const tok=grams(q);if(!tok.size)return[];
 return db.entries.map(x=>{
  if(!x?.question||!x?.answer||!/^https:\/\/lawygo\.lexid\.site\//.test(x.source_url||""))return null;
  const a=grams(x.question),b=grams(x.answer);let score=norm(x.question).includes(q)?24:0;
  for(const t of tok)score+=a.has(t)?(t.length>2?4:2):b.has(t)?1:0;
  return score>=4?{id:x.id,question:x.question,answer:x.answer,citation_url:x.source_url,source_status:x.source_status,score}:null;
 }).filter(Boolean).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,Math.max(1,Math.min(Number(limit)||3,10)));
}
