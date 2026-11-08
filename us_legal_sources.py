"""US law firm legal insight feed: verified originals, Korean editorial digests, official RSS."""
from __future__ import annotations
import asyncio,hashlib,re,xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlparse
import httpx

# Verified publisher URLs. Korean abstracts are concise original editorial summaries.
CURATED=[
("2026-11-04","BakerHostetler","New York DOL Issues Guidance on the Trapped at Work Act Ahead of December Effective Date","뉴욕주 노동부, ‘트랩트 앳 워크법’ 시행 전 고용주 지침 발표","12월 시행을 앞두고 퇴사 시 교육비·보너스·이주비 반환 약정에 관한 적용 범위와 예외를 설명했다. 고용주는 신규·변경 약정과 자발적 반환 약정을 구분해 점검할 필요가 있다.","https://www.bakerlaw.com/insights/new-york-dol-issues-guidance-on-the-trapped-at-work-act-ahead-of-december-effective-date/","노동·고용"),
("2026-11-04","Ogletree Deakins","A Narrower PWFA Rule Is on the Horizon, but the EEOC’s Pregnancy Accommodation Enforcement Is Not Slowing Down","임신근로자 보호 규칙 개정 예고… 미국 EEOC 집행은 지속","미국 EEOC가 임신근로자 공정법 시행규칙 범위를 좁히는 방안을 검토 중이지만, 합리적 편의 제공 의무와 현행 법 집행은 계속된다. 인사 담당자의 요청 처리 절차를 점검해야 한다.","https://ogletree.com/insights-resources/blog-posts/a-narrower-pwfa-rule-is-on-the-horizon-but-the-eeocs-pregnancy-accommodation-enforcement-is-not-slowing-down/","노동·고용"),
("2026-10-30","Ogletree Deakins","California’s ‘No Robo Bosses Act’: New Restrictions on Employers’ Use of AI","캘리포니아 ‘로보 상사 금지법’… AI 단독 해고·징계 제한","캘리포니아는 AI 도구만으로 징계·해고를 결정하는 행위를 제한하는 법을 도입했다. 사람이 결과를 검토하는 절차와 대상 근로자 통지 등 준수사항에 주목해야 한다.","https://ogletree.com/insights-resources/blog-posts/californias-no-robo-bosses-act-new-restrictions-on-employers-use-of-ai/","AI·고용"),
("2026-10-28","Hunton Andrews Kurth","California Expands Workplace AI Regulation: What Employers Need to Know About Four New Laws","캘리포니아 직장 내 AI 규제 확대… 새 법률 4건의 핵심","자동 고용결정과 근로자 감시, 기술 도입에 따른 인력 감축 관련 4개 법률의 주요 변화를 분석했다. 다수 의무가 2027년부터 시행될 예정이므로 기업별 영향 검토가 필요하다.","https://www.hunton.com/hunton-employment-labor-perspectives/california-expands-workplace-ai-regulation-what-employers-need-to-know-about-four-new-laws","AI·고용"),
("2026-10-28","BakerHostetler","DOJ Announces Record $1.6 Billion EKRA Prosecution in California Health Care Fraud Takedown","미 법무부, 약 16억 달러 규모 의료 리베이트 사건 기소","미 법무부가 의료보험 사기 단속에서 EKRA 위반 혐의를 적용한 사례를 분석했다. 환자 소개 수수료와 의료기관 보상구조를 운영하는 사업자에게 규제 준수 시사점이 있다.","https://www.bakerlaw.com/insights/doj-announces-record-1-6-billion-ekra-prosecution-in-california-health-care-fraud-takedown/","소송·규제"),
("2026-10-13","Ogletree Deakins","AI Smart Glasses in the Workplace: Seven Employment Law Risks to Consider","직장 내 AI 스마트 안경… 고용법상 위험 7가지","스마트 안경의 녹음·전사·AI 분석 기능이 개인정보·노동관계·영업비밀·장애인 편의제공 의무와 충돌할 수 있는 사례를 정리했다. 기업의 웨어러블 기기 정책을 점검할 필요가 있다.","https://ogletree.com/insights-resources/blog-posts/ai-smart-glasses-in-the-workplace-seven-employment-law-risks-to-consider/","개인정보·고용"),
("2026-10-01","Foley & Lardner","Foley at the Forefront: From AI Adoption to Execution","로펌의 AI 활용… 도구 도입보다 검증 가능한 업무 프로세스","법률 AI를 안전하게 활용하려면 업무 설계, 실행 권한, 결과 검증, 책임 주체가 명확해야 한다. 변호사 검토와 추적 가능한 작업 기록의 중요성을 강조한 분석이다.","https://www.foley.com/insights/publications/2026/10/foley-at-the-forefront-from-ai-adoption-to-execution/","법률 AI"),
("2026-09-10","Hunton Andrews Kurth","Delaware Expands State Privacy Law","델라웨어 개인정보보호법 확대… 적용 사업자 범위 넓어져","델라웨어주는 2027년부터 개인정보보호법 적용 기준을 낮추고 민감정보 보호와 자동화된 프로파일링 관련 권리를 확대한다. 개인정보 처리업체의 준수 범위가 넓어진다.","https://www.hunton.com/privacy-and-cybersecurity-law-blog/delaware-expands-state-privacy-law","개인정보·규제"),
("2026-11-04","Ogletree Deakins","Pennsylvania Court Confirms Workers Must Sue Within Three Years to Recover Unpaid Wages","펜실베이니아 미지급 임금 청구 소송 시효는 3년","펜실베이니아 항소법원은 미지급 초과근무 수당 청구의 소멸시효를 6년이 아닌 3년으로 보았다. 미지급 임금 관련 기업의 잠재 소송 위험에 영향을 미치는 결정이다.","https://ogletree.com/insights-resources/blog-posts/pennsylvania-court-confirms-workers-must-sue-within-three-years-to-recover-unpaid-wages/","노동·고용"),
("2026-11-04","Ogletree Deakins","New York Department of Labor Guidance Answers Questions About Trapped at Work Act","뉴욕주 ‘퇴사 시 비용반환 약정’ 제한법 시행 지침","뉴욕 노동부가 근로자의 조기 퇴사 시 비용을 반환하게 하는 ‘스테이 오어 페이’ 약정의 예외를 구체화했다. 기업은 12월 시행 전에 임금·교육비 반환 정책을 점검할 필요가 있다.","https://ogletree.com/insights-resources/blog-posts/new-york-department-of-labor-guidance-answers-questions-about-trapped-at-work-act/","노동·고용"),
("2026-11-02","BakerHostetler","Reading the Tea Leaves: As Hearings End, Enforcement is at the Forefront of the Agenda","텍사스 규제·예산정책, 감독과 집행 강화 가능성 분석","텍사스의 예산 심의와 위원회 청문회에서 규제 감독·집행 역량 확대가 강조되고 있다. 기업은 향후 법안과 예산의 변화를 함께 관찰해야 한다는 분석이다.","https://www.bakerlaw.com/insights/reading-the-tea-leaves-as-hearings-end-enforcement-is-at-the-forefront-of-the-agenda/","규제·행정"),
("2026-10-30","Ogletree Deakins","EEOC Rescinds Criminal Background Check Guidance","미국 EEOC, 채용 전과조회에 관한 2012년 지침 철회","미국 EEOC가 고용 과정의 체포·유죄판결 기록 활용에 관한 2012년 가이드라인을 철회했다. 다만 민권법 제7편과 별도 연방법·주법에 따른 차별금지 의무는 여전히 적용된다.","https://ogletree.com/insights-resources/blog-posts/eeoc-rescinds-criminal-background-check-guidance/","노동·고용"),
("2026-10-06","Hunton Andrews Kurth","California Enacts New Restrictions on AI-Based Employee Monitoring","캘리포니아, AI로 직원 감정·신경정보 추정하는 감시 제한","캘리포니아 AB 1883은 기업의 특정 AI 기반 직장 감시를 제한한다. 근로자의 감정상태 추정과 신경 데이터 수집에 대한 제한이 2027년부터 적용될 예정이다.","https://www.hunton.com/privacy-and-cybersecurity-law-blog/california-enacts-new-restrictions-on-ai-based-employee-monitoring","개인정보·AI"),
]
RSS=(("Hunton Andrews Kurth","https://www.huntonprivacyblog.com/feed/","huntonprivacyblog.com"),)
TOPICS=(
(re.compile(r"AI|artificial intelligence|automated|algorithm|robot",re.I),"AI·규제","미국 로펌의 인공지능·자동화 규제 관련 공개 분석입니다. 구체적인 법률 내용은 원문을 확인하세요."),
(re.compile(r"privacy|cyber|data|tracking|breach",re.I),"개인정보·보안","미국 로펌의 개인정보 보호·데이터 보안 관련 공개 분석입니다. 구체적인 법률 내용은 원문을 확인하세요."),
(re.compile(r"employ|worker|workplace|labor|wage",re.I),"노동·고용","미국 로펌의 노동·고용법 관련 공개 분석입니다. 구체적인 법률 내용은 원문을 확인하세요.")
)
LEGAL=re.compile(r"law|legal|court|litigat|privacy|cyber|data|regulat|compliance|employ|workplace|artificial intelligence|AI|FTC|SEC|DOJ|GDPR|rights|settlement",re.I)

def _item(date,source,en_title,ko_title,ko_abstract,url,category,translation_status="editorial",en_abstract=""):
 return {"id":"us-"+hashlib.sha1(url.encode()).hexdigest()[:20],
 "content_type":"us_legal","title":ko_title or en_title,"title_original":en_title,
 "title_ko":ko_title,"summary":ko_abstract,"summary_ko":ko_abstract,
 "summary_original":en_abstract,"category_ko":category,
 "translation_status":translation_status,"source_region":"US",
 "source_kind":"us-lawfirm","url":url,"source":source,
 "published":date,"thumb_url":None,"approved":False,"live":False}

def verified_us_articles():
 return [_item(*entry) for entry in CURATED]

def _plain(html,limit=210):
 class Reader(HTMLParser):
  def __init__(self):super().__init__();self.parts=[]
  def handle_data(self,data):self.parts.append(data)
 p=Reader()
 try:p.feed(html or "")
 except (TypeError,ValueError):return ""
 s=" ".join(" ".join(p.parts).split())
 return s[:limit].rstrip()+"…" if len(s)>limit else s

def parse_us_rss(xml,source,host):
 root=ET.fromstring(xml)
 out=[]
 for node in (root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry"))[:30]:
  def f(*tags):
   for tag in tags:
    n=node.find(tag)
    if n is not None and n.text:return n.text.strip()
   return ""
  title=_plain(f("title","{http://www.w3.org/2005/Atom}title"),180)
  url=f("link")
  if not url:
   tag=node.find("{http://www.w3.org/2005/Atom}link")
   if tag is not None:url=tag.get("href","")
  if not title or not LEGAL.search(title):continue
  if not url.startswith("https://") or (urlparse(url).hostname or "").lower().removeprefix("www.")!=host:continue
  date=f("pubDate","{http://www.w3.org/2005/Atom}published")
  try:date=parsedate_to_datetime(date).date().isoformat()
  except (ValueError,TypeError,OverflowError):date=date[:10] if re.match(r"^\d{4}-",date) else ""
  category,summary="미국 법률 동향","미국 로펌이 발표한 공개 법률 동향입니다. 자세한 법령·사례는 원문에서 확인하세요."
  for rule,label,text in TOPICS:
   if rule.search(title):category,summary=label,text;break
  out.append(_item(date,source,title,"",summary,url,category,"source-en",
     _plain(f("description","{http://www.w3.org/2005/Atom}summary"),180)))
 return out

async def fetch_us_legal():
 async def load(source,url,host):
  try:
   async with httpx.AsyncClient(timeout=8,follow_redirects=True,
    headers={"User-Agent":"LAWYGO-PAN/2.1 (+https://lawygo.lexid.site)"}) as client:
    res=await client.get(url);res.raise_for_status()
    if len(res.content)>1_000_000:return []
    return parse_us_rss(res.text,source,host)
  except (httpx.HTTPError,ET.ParseError,ValueError):return []
 result=verified_us_articles()
 seen={x["url"] for x in result}
 for batch in await asyncio.gather(*(load(*a) for a in RSS)):
  for item in batch:
   if item["url"] not in seen:
    result.append(item);seen.add(item["url"])
 return result
