from pathlib import Path
from collections import Counter,defaultdict
from docx import Document
import json,re
root=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')
# Only user-facing prose and brand/product terminology. These strings preserve all technical identifiers/URLs.
changes = [
 ('국제 정보서비스의 인상을 흉내내는 대신 같은 수준의 검증 프로세스를 구축합니다.','국제 정보 서비스의 외형을 모방하기보다, 이에 걸맞은 검증 절차를 구축합니다.'),
 ('그 차이를 배달합니다.','그 차이를 설명합니다.'),
 ('그 경제를 움직이는 제도를 해석하는 것입니다.','그 경제를 움직이는 제도를 이해하는 데 있습니다.'),
 ('전문 정보 플랫폼을 지향합니다.','전문 정보 플랫폼을 지향합니다.'),
 ('제휴 법무법인은 자신의 전문성과 독립적인 판단을 유지하면서','제휴 법무법인은 전문성과 독립적인 판단을 유지하면서'),
 ('LAWYGO는 국내 법무법인과의 업무협약(MOU)을 통해','LAWYGO는 국내 법무법인과 업무협약(MOU)을 체결하여'),
 ('법률전문성과 기술의 혁신이 만나는 곳.','법률 전문성과 기술 혁신이 만나는 곳.'),
 ('변호사 스스로 승인한 전문지식·프로필 콘텐츠','변호사가 직접 승인한 전문지식·프로필 콘텐츠'),
 ('투자관련 이해상충과 유료 홍보 표시','투자 관련 이해상충과 유료 홍보 표시'),
 ('시장뉴스 분석','시장 뉴스 분석'),
 ('미국 기술 협력 구상: TerraBridge Capital LLC · 검증 전','미국 기술 협력 관련 사항: TerraBridge Capital LLC · 확인 필요'),
 ('담당자가 확인후','담당자가 확인한 후'),
 ('구독안내','구독 안내'),
 ('서식·버전관리','서식·버전 관리'),
 ('데이터 보호와 마케팅 관련 원칙','데이터 보호 및 마케팅 관련 원칙'),
 ('법률정보백과','법률 정보 백과'),
 ('법률정보사전','법률 정보 사전'),
 ('법률정보를','법률 정보를'),
 ('법률정보의','법률 정보의'),
 ('법률정보와','법률 정보와'),
 ('법률정보','법률 정보'),
 ('전문정보','전문 정보'),
 ('경제정보','경제 정보'),
 ('경제법률','경제·법률'),
 ('법률뉴스','법률 뉴스'),
 ('시장뉴스','시장 뉴스'),
 ('정책뉴스','정책 뉴스'),
 ('판례정보','판례 정보'),
 ('판례검색','판례 검색'),
 ('판례카드','판례 카드'),
 ('법률용어','법률 용어'),
 ('전문서식','전문 서식'),
 ('송무프로그램','송무 프로그램'),
 ('송무운영','송무 운영'),
 ('송무관리','송무 관리'),
 ('사건관리','사건 관리'),
 ('사건검색','사건 검색'),
 ('사건정보','사건 정보'),
 ('기일정보','기일 정보'),
 ('기일관리','기일 관리'),
 ('문서작성','문서 작성'),
 ('문서분석','문서 분석'),
 ('문서관리','문서 관리'),
 ('실무워크플로','실무 워크플로'),
 ('베타서비스','베타 서비스'),
 ('베타체험','베타 체험'),
 ('베타기간','베타 기간'),
 ('무료체험','무료 체험'),
 ('구글아이디','구글 아이디'),
 ('이메일주소','이메일 주소'),
 ('구독정보','구독 정보'),
 ('보호조치','보호 조치'),
 ('접근권한','접근 권한'),
 ('정식전환요금','정식 전환 요금'),
 ('전문업무','전문 업무'),
 ('전문성에 구독하다.','전문 지식에 투자하다.'),
 ('독립적으로 재생성한 경제·법률 인텔리전스 시각 자료','경제·법률 인텔리전스를 표현한 독자 제작 시각 자료'),
 ('LAWYGO는 단순한 법률 뉴스 모음이 아닙니다.','LAWYGO는 법률 뉴스만 모아 전달하는 서비스가 아닙니다.'),
 ('한국 자본시장 정책을 기업의 언어로 다시 읽다','한국 자본시장 정책을 기업의 관점에서 다시 읽다'),
 ('경제를 이해하는 가장 깊은 방법은,','경제를 깊이 이해하려면'),
 ('법률적 검증을 거친 경제 인텔리전스의 새로운 기준.','법률적 검증을 바탕으로 경제 정보를 해석하는 관점입니다.'),
 ('미국 증권규제 변화가','미국 증권 규제 변화가'),
 ('미국 증권규제의 변화','미국 증권 규제의 변화'),
 ('공시·지배구조·기업금융 정책','공시·지배구조·기업 금융 정책'),
 ('법률상 허용되지 않는 법률사무 제공','법률상 허용되지 않는 법률사무의 제공'),
 ('‘확인 가능한 사실’과 ‘LAWYGO의 전망/해석’','‘확인 가능한 사실’과 ‘LAWYGO의 전망·해석’'),
 ('매월 1일과 15일을 기본 발송일로 제안합니다.','매월 1일과 15일 발행을 기본 일정으로 제안합니다.'),
 ('국내 경제·증권제도','국내 경제·증권 제도'),
 ('미국 경제·증권제도','미국 경제·증권 제도'),
 ('단순 보도인가, 법적 구속력 있는 문서인가?','단순 보도인가, 법적 구속력이 있는 문서인가?'),
 ('로펌 전용 협업·보안 업무 인프라','법무법인용 협업·보안 업무 인프라'),
 ('정보저널','정보 저널'),
 ('구독기능','구독 기능'),
 ('구독관리','구독 관리'),
 ('준비서면','준비서면'),
 ('경제의 움직임을 법률로 읽다.','경제의 변화를 법률의 관점에서 읽다.'),
 ('전문적인 업무에 특화된','전문 업무에 특화된'),
]
# avoid replacing inside file system and API identifiers: only Hangul changes; multiple hits expected.
counts=Counter(); locations=defaultdict(list); corrected_files=0
extensions={'.html','.md','.json','.js','.py','.svg','.css'}
for f in root.rglob('*'):
 if not f.is_file() or f.suffix not in extensions:continue
 s=f.read_text(encoding='utf-8',errors='replace');t=s
 for a,b in changes:
  if a==b:continue
  n=t.count(a)
  if n:
   t=t.replace(a,b);counts[(a,b)]+=n;locations[(a,b)].append(str(f.relative_to(root)))
 if t!=s:
  f.write_text(t,encoding='utf-8');corrected_files+=1
# DOCX semantic correction: preserve original runs and font on text components; regenerate PDF afterward.
word_files=list(root.rglob('*.docx'))
word_log=[]
for file in word_files:
 doc=Document(file); n=0
 ps=list(doc.paragraphs)
 for tab in doc.tables:
  for row in tab.rows:
   for cell in row.cells: ps+=list(cell.paragraphs)
 for para in ps:
  for run in para.runs:
   text=run.text
   for a,b in changes:
    if a!=b and a in text:
     num=text.count(a);text=text.replace(a,b);n+=num
   if text!=run.text:run.text=text
 if n:doc.save(file)
 word_log.append({'file':str(file.relative_to(root)),'replacements':n})
# update archive-level readme
report={
 'scope':{'html_files':len(list(root.rglob('*.html'))),'docx_files':len(word_files),'other_text_files':len([f for f in root.rglob('*') if f.suffix in extensions and f.suffix!='.html'])},
 'files_changed':corrected_files,
 'replace_total':sum(counts.values()),
 'changes':[{'before':a,'after':b,'count':c,'sample_files':locations[(a,b)][:4]} for (a,b),c in sorted(counts.items(),key=lambda x:-x[1])],
 'word_changes':word_log
}
Path('/mnt/data/_lawygo_text_corrections.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files_changed':corrected_files,'replacements':sum(counts.values()),'unique_rules_hit':len(counts),'word_log':word_log,'top':report['changes'][:25]},ensure_ascii=False,indent=2))
