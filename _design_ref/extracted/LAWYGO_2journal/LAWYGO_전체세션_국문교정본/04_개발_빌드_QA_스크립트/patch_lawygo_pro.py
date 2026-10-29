from pathlib import Path
import re
p=Path('/mnt/data/build_lawygo.py')
s=p.read_text(encoding='utf-8')
s=s.replace("['journal','wiki','note','litigation','pan','legal','previews']", "['journal','wiki','note','pro','litigation','pan','legal','previews']")
s=s.replace("('송무 프로그램','litigation/index.html')", "('로이고 PRO','pro/index.html')")
s=s.replace('JOURNAL / WIKI / NOTE / LITIGATION / PAN','JOURNAL / WIKI / NOTE / PRO / PAN')
s=s.replace('LAWYGO LITIGATION','LAWYGO PRO')
s=s.replace('LAWYGO 송무 프로그램','LAWYGO PRO 전문 송무 관리')
s=s.replace('LAWYGO LITIGATION · 기업 계약','LAWYGO PRO · 법무법인 도입')
s=s.replace('JOURNAL · WIKI · NOTE · LITIGATION · PAN','JOURNAL · WIKI · NOTE · PRO · PAN')
s=s.replace('LITIGATION / EXISTING WEB PRICE', 'PRO / FREE BETA')
s=s.replace('송무가격은 기존 lawygo.com 공개 요금제 기준이며 사전 공지 없이 변경될 수 있습니다.', 'PRO는 현재 무료 베타 참여 안내를 우선하며, 기존 법인용 공개 요금과 베타 운영 조건은 별개입니다.')
s=s.replace("product(p,'04','LITIGATION','THE OPERATING SYSTEM','월 구독 · 송무 업무 전반','litigation/index.html','CASE / DEADLINE / WORKFLOW')", "product(p,'04','PRO','THE LEGAL OPERATING SYSTEM','구글 로그인 · 무료 베타','pro/index.html','DESK / CASE / FLOW / HUB')")
s=s.replace("p='litigation/index.html'", "p='pro/index.html'")
s=s.replace("p='litigation/dashboard.html'", "p='pro/dashboard.html'")
s=s.replace('litigation/dashboard.html', 'pro/dashboard.html')
s=s.replace('litigation/index.html', 'pro/index.html')
s=s.replace("'송무 프로그램',body)", "'로이고 PRO',body)")
s=s.replace("'송무 구독요금','btn-outline'", "'무료 베타 운영 안내','btn-outline'")
s=s.replace("'로이고 송무 대시보드 데모'", "'LAWYGO PRO DESK 송무 대시보드 데모'")
s=s.replace("'월 구독형 사건 관리, 기일, 전자결재, 회계와 문서 업무'", "'구글 계정으로 무료 베타 체험 가능한 사건 관리·기일·전자결재·법무법인 업무 프로그램'")
s=s.replace("'LAWYGO 월 구독 요금'", "'LAWYGO 제품별 구독 및 PRO 무료 베타'")
s=s.replace("'법률 정보·노트·송무·판의 월 구독 제안 요금'", "'저널 무료, 위키·노트 구독, LAWYGO PRO 송무 무료 베타 안내'")
# PRO hero lead name and accurate beta CTA
s=s.replace("'사건 관리부터 기일까지.<br><i>로펌의 업무를 하나로.</i>'", "'구글 계정으로 시작하는<br><i>전문 송무 관리.</i>'")
s=s.replace("'법률백과와 별도 제공되는 한국형 온라인 송무 운영 프로그램. 사건·고객·기일·결재·회계·문서의 흐름을 통합하도록 설계합니다.'", "'LAWYGO PRO(로이고 프로)는 사건·기일·결재·회계·문서·사내 협업을 통합한 법률 업무 프로그램입니다. 구글 계정으로 누구나 무료 베타 서비스 참여를 신청할 수 있습니다.'")
s=s.replace("button(p,'pro/dashboard.html','운영 대시보드 체험')+button(p,'pricing.html','무료 베타 운영 안내','btn-outline')", "button(p,'pro/beta.html','무료 베타 시작하기')+button(p,'pro/dashboard.html','PRO DESK 미리보기','btn-outline')")
# update pricing plan box: maintain original paid as historic not primary to avoid wrong marketing
s=s.replace('<span class="eyebrow">PRO / FREE BETA</span><h3>송무</h3><div class="price">₩300,000 <small>/ 월부터</small></div><p>기존 공개 사이트의 Core 시작 가격<br>실제 계약 조건 별도 확인</p><ul><li>사건·기일·문서</li><li>기존 사이트 Professional ₩750,000/월</li><li>Enterprise 별도 문의</li></ul>{button(p,\'pro/index.html\',\'상세 보기\',\'btn-navy\')}', '<span class="eyebrow">PRO / FREE BETA</span><h3>프로</h3><div class="price">₩0 <small>/ 베타 기간</small></div><p>구글 계정으로 무료 체험<br>3~6개월 예정 · 종료 1개월 전 안내</p><ul><li>사건·기일·문서·결재</li><li>법원 사건 검색 연결</li><li>정식 전환요금 사전 고지</li></ul>{button(p,\'pro/beta.html\',\'무료 베타 안내\',\'btn-navy\')}')
# Additional PRO content inserted before last safe by design band
anchor="body+=band(p,'SAFE BY DESIGN'"
addition='''body+=f'<section class="pro-beta-strip"><div class="wrap beta-in"><div><span class="eyebrow">OPEN BETA · GOOGLE ACCOUNT</span><h2>LAWYGO PRO 무료 베타 체험</h2><p>누구나 구글 계정으로 시작 · 무료 체험기간 3~6개월 예정 · 종료 1개월 전 별도 사전 안내</p><small>대법원 나의 사건 검색은 사건번호 외에 당사자명·보안코드·인증 등이 필요할 수 있습니다. 자동 동기화 제공 여부는 실제 계정·연동 상태에 따릅니다.</small></div>{button(p,'pro/beta.html','무료 베타 상세안내')}</div></section>'
body+=f'<section class="white"><div class="wrap">{section("PROFESSIONAL SUITE / MODULE NAMING","LAWYGO PRO, 여섯 개의 전문 업무 모듈.","실제 lawygo·lonexus 저장소의 개발 항목을 업무 흐름 중심으로 다시 정리한 고객용 네이밍입니다.")}<div class="pro-module-grid">'+''.join(f'<a class="pro-module" href="{link(p,\"pro/\"+slug+\".html\")}"><span>PRO / {code}</span><h3>LAWYGO {name}</h3><p>{desc}</p><b>모듈 상세 보기 ↗</b></a>' for code,name,slug,desc in [('01','DESK','desk','오늘의 대시보드 · 업무 상황판'),('02','CASE','case','사건번호 · 의뢰인 · 사건 기록'),('03','FLOW','flow','기일 · 결재 · 기한 관리'),('04','WORK','work','서류 · 담당자 · 업무 기록'),('05','HUB','hub','사내 메신저 · 메일 · 권한 · 협업'),('06','SMART','smart','AI 판례 · 법령 · 사건 정보 지원')])+'</div></div></section>'
'''
s=s.replace(anchor,addition+anchor)
# replace old pricing section description if still there: precise targeted
# insert module pages before PAN
modulecode='''# LAWYGO PRO product detailed module pages: names apply only to module categories, source systems remain as coded.
pro_modules=[
('desk','DESK','운영 대시보드','한눈에 읽는 로펌의 오늘','사건·기일·결재·고객 정보를 우선순위에 따라 정리하는 업무 관제 화면.','lawygo','dashboard, notices, deadlines, stats', [('기일 우선순위','오늘·다가오는 기일을 업무 성격별로 정렬'),('업무 카드','진행 사건·공지·결재 대기·할 일을 요약'),('팀별 요약','담당자 기준 분류 및 역할 기반 노출')]),
('case','CASE','사건 관리','사건번호 하나에서 시작하는 정돈된 업무','사건 등록, 의뢰인, 담당자, 단계별 메모와 문서를 하나의 사건 워크스페이스에서 확인하는 서비스.','lawygo','cases, clients, case timeline', [('사건번호 등록','법원·년도·사건구분·번호를 분리 입력'),('사건 진행 관리','담당자·상태·메모·상대방을 통합 관리'),('법원 정보 연결','공식 조회 또는 승인된 연동 경로로 사건 검색')]),
('flow','FLOW','송무 프로세스','기일에서 결재까지 이어지는 업무의 흐름','기일 캘린더, 재판 일정, 서류 기한, 전자결재, 알림을 하나의 워크플로로 조직합니다.','lawygo','calendar, deadlines, approval', [('기일 캘린더','월간·주간 기일과 주요 업무를 표시'),('전자결재','단계별 승인 요청과 변경 이력'),('알림·기한','D-day 및 할 일 우선순위')]),
('work','WORK','업무·문서 관리','사람과 서류를 연결하는 업무 플랫폼','송무 서류, 상담, 고객, 직원, 회계·수납 정보를 조직적으로 관리하는 실무 공간입니다.','lawygo','documents, staff, consultations, finance', [('서류 관리','사건별 파일·전문 서식·초안 기록'),('담당자 협업','인력·상담·업무 배정의 연결'),('회계·수납','수임료·미수금·업무 운영 현황')]),
('hub','HUB','로펌 협업·보안 ERP','조직의 대화를 안전한 업무로 연결','lonexus의 채팅·사내메일·캘린더·드라이브·권한·보안 모듈을 로펌 협업 영역으로 연계하는 설계입니다.','lonexus','chat, mail, web-drive, governance, security', [('사내 메신저','팀 채널 및 업무상 대화(연계 인프라 필요)'),('사내 메일','조직메일과 공지·의뢰인 소통의 업무 연결'),('보안·권한','접근 권한 분리, 로그, 보안정책 및 이력')]),
('smart','SMART','AI 송무 지원','근거를 찾고, 다음 행동을 제안하다','법률백과·판례 추천·법령 검색·문서요약을 사건 맥락에 연결하는 법률 AI 지원 모듈입니다.','lawygo','legal encyclopedia, precedent, ai search', [('판례·법령 검토','출처가 제시된 관련 자료 탐색'),('사건 정보 지원','사건번호로 조회 경로 및 기일 확인 지원'),('문서 AI 연계','로이고 노트와 연동할 수 있는 작성 흐름')])]
for slug,code,ko,title,lead,repo,module,feats in pro_modules:
 p=f'pro/{slug}.html'
 body=hero(f'LAWYGO PRO / {code}',title.replace('는','는')+'<br><i>'+ko+'</i>',lead,'hero-network.jpg' if slug in ('smart','hub') else 'hero-law.jpg',True,button(p,'pro/beta.html','무료 베타 안내')+button(p,'pro/index.html','PRO 전체 기능','btn-outline'),True)
 body+=f'<section class="white"><div class="wrap">{section("CORE CAPABILITIES / "+code,ko+"의 세 가지 핵심 기능","기존 GitHub 모듈을 기반으로 재구성한 고객용 설명입니다. 실제 제공 범위는 계정과 서비스 환경에 따라 다릅니다.")}<div class="four-grid">'+''.join(f'<div class="feature-card"><span>{i:02d} / PRO {code}</span><h3>{t}</h3><p>{d}</p></div>' for i,(t,d) in enumerate(feats,1))+'</div></div></section>'
 body+=f'<section class="cream"><div class="wrap split-grid"><div>{section("ENGINEERING SOURCE / MODULE MAP","이미 개발된 모듈에서 시작합니다.","기능의 원본 저장소와 공개 시안의 연결 구조를 구분합니다.")}<p><strong>원본 저장소:</strong> shinkangteam/{repo}</p><p><strong>검토 범위:</strong> {module}</p><p>제품 프런트엔드 시연을 위해 재구성한 정적 디자인입니다. 실제 기업 업무 데이터나 원본 앱의 API를 외부에 공개하지 않습니다.</p>{button(p,'pro/beta.html','베타 사용·인증 안내')}</div>{figure(p,'hero-network.jpg',code+' — AI 기술·법률 정보 이미지 콘셉트')}</div></section>'
 render(p,'LAWYGO PRO '+code+' — '+ko,lead,'로이고 PRO',body)
# free beta standalone: no fabricated login URL or claim that case lookup works with number alone
p='pro/beta.html'
body=hero('LAWYGO PRO / OPEN BETA','이제 시작하세요.<br><i>구글 계정만 준비하면.</i>','별도의 설치 없이 로이고 송무 프로그램을 체험하는 무료 베타 운영 정책을 안내합니다. 사건 등록부터 법원 조회 연결·기일 확인, 팀 협업까지.','hero-law.jpg',True,'<a class="btn btn-gold" href="https://www.lawygo.com/" target="_blank" rel="noopener">lawygo.com에서 시작하기 ↗</a>'+button(p,'pro/index.html','모든 기능 확인','btn-outline'))
body+=f'<section class="white"><div class="wrap">{section("BETA ACCESS / LAUNCH POLICY","무료 베타 서비스, 핵심만 명확하게.","운영정책은 요청하신 사업 계획에 따른 고지 문구 초안입니다.")}<div class="beta-steps"><div><span>01</span><h3>Google 계정</h3><p>Google 계정으로 LAWYGO에 접속해 로그인 또는 무료 체험을 시작하세요. 로그인 제공 상태는 서비스에서 확인합니다.</p></div><div><span>02</span><h3>사건 등록</h3><p>사건번호·법원 등 사건 기초정보를 입력하고 담당자와 메모를 등록합니다.</p></div><div><span>03</span><h3>법원 조회 연결</h3><p>대법원 나의 사건 검색 연결을 통해 기일 등 진행정보를 확인합니다. 법원 조회에 필요한 추가 정보와 인증은 이용자가 입력해야 할 수 있습니다.</p></div><div><span>04</span><h3>업무 관리</h3><p>기일 캘린더, 사건목록, 전자결재, 고객·사내업무 등 계정에 제공되는 모듈을 활용합니다.</p></div></div></div></section>'
body+=f'<section class="cream"><div class="wrap">{section("IMPORTANT BETA TERMS","무료 이용기간과 종료 고지") }<div class="reference-table light-table"><div><b>베타 대상</b><span>Google 계정 이용자 누구나 체험 신청 가능. 실제 이용 가능 여부는 가입·운영환경에 따릅니다.</span></div><div><b>이용 요금</b><span>베타 제공기간 무료. 차후 정식 구독요금은 별도 사전 공지.</span></div><div><b>운영기간</b><span>3개월~6개월 예상. 고정 종료일·시작일은 별도 공식 공지.</span></div><div><b>종료 안내</b><span>무료 베타 종료 1개월 전 별도 통지 예정.</span></div><div><b>대법원 조회</b><span>사건번호 외 당사자명·법원명·인증정보가 필요한 경우가 있음. 공식 API 또는 조회 링크 방식; 자동 동기화 일률 보장 없음.</span></div><div><b>데이터와 안전</b><span>베타 종료 시 데이터 백업·다운로드, 개인정보 보유·삭제·전환 정책을 별도 안내해야 합니다.</span></div></div><div class="article-warning space-top">현재 공개 웹사이트의 유료 요금표는 과거/별도 판매조건일 수 있습니다. 이 시안은 무료 베타를 우선 소개하며 실서비스의 약관·기간·과금 조건은 운영자가 확정해야 합니다.</div></div></section>'
body+=band(p,'PRO MODULES','PRO의 여섯 모듈을 살펴보세요.','DESK · CASE · FLOW · WORK · HUB · SMART. 이미 개발된 법률·업무 플랫폼 기능을 명료한 서비스 이름으로 소개합니다.','pro/index.html','기능 모두 보기')
render(p,'LAWYGO PRO 무료 베타 안내','Google 계정으로 시작하는 무료 송무 관리 베타 서비스와 3~6개월 운영 및 종료 1개월 전 통지 정책','로이고 PRO',body)
# Journal's data infrastructure detail page using wallpilotpro
p='journal/market-intelligence.html'
body=hero('LAWYGO JOURNAL / MARKET INTELLIGENCE','시장의 숫자를 넘어<br><i>제도의 변화를 읽습니다.</i>','WallPilot Pro의 DART 공시분석, 미국 시장 뉴스·증권 데이터, AI 리포트 인프라를 저널의 경제·증권정보 분석에 연결하는 편집 전략입니다.','hero-finance.jpg',True,button(p,'journal/index.html','저널 홈으로')+button(p,'journal/newsletter.html','무료 뉴스레터','btn-outline'))
body+=f'<section class="white"><div class="wrap">{section("DATA → REGULATION → INSIGHT","경제 데이터에 리걸 마인드를 더하다.","기존 wallpilotpro 저장소에서 확인한 뉴스수집·DART·재무 분석 코드를 재사용 대상으로 검토했습니다.")}<div class="four-grid"><div class="feature-card"><span>01 / OPEN DART</span><h3>한국 공시·재무</h3><p>기업 공시 자료, 재무지표, CPA 관점 분석. 최신 공시와 해당 시점의 법령을 함께 검증합니다.</p></div><div class="feature-card"><span>02 / US EQUITIES</span><h3>미국 증권 시장</h3><p>Alpha Vantage 뉴스·Yahoo 뉴스 폴백 등 기존 수집 로직을 보유. 라이선스·API 공급조건은 배포 전에 별도 확인합니다.</p></div><div class="feature-card"><span>03 / REGULATORY INTELLIGENCE</span><h3>정책·법규 검증</h3><p>SEC·연준·금융위원회 원문과 비교해 확정/제안/시행 상태를 구분합니다.</p></div><div class="feature-card"><span>04 / EDITORIAL</span><h3>리걸 인사이트</h3><p>경제 뉴스 한 건에 정책 영향, 적용 대상, 시행일, 기업 대응 체크포인트를 부착합니다.</p></div></div></div></section>'
body+=f'<section class="cream"><div class="wrap">{section("EDITORIAL FORMAT","뉴스 한 건의 완성형 분석 카드","실제 당일 증권 수치를 출력하지 않는 디자인 예시입니다.")}<div class="market-brief"><div class="brief-head"><span>LAWYGO EDITORIAL TEMPLATE</span><b>분석 예시 · 비실시간</b></div><h2>미국 증권정책의 변화는 국내 상장사 공시에 어떤 질문을 남기는가?</h2><div class="brief-grid"><div><b>01 사실 확인</b><p>발표 기관·원문·발표일·최종 시행여부를 확인</p></div><div><b>02 경제 맥락</b><p>자금조달·기업 비용·시장 심리에 미치는 통로</p></div><div><b>03 법률 분석</b><p>공시의무·지배구조·규제 범위·제재 가능성</p></div><div><b>04 행동 체크</b><p>담당부서별 확인사항 및 원문 인용</p></div></div></div></div></section>'
body+=band(p,'WALLPILOTPRO ENGINEERING','이미 만든 금융데이터 모듈을 콘텐츠 경쟁력으로.','이 페이지는 금융 정보·투자 자문을 제공하지 않으며, 실제 데이터 연동은 접근 권한·키·라이선스·배포 승인 후 진행합니다.','sources.html','기술·출처 확인')
render(p,'LAWYGO JOURNAL 미국·국내 경제 인텔리전스','WallPilot Pro와 연계하는 금융공시·증권뉴스·정책변화 법률저널 설계','저널',body)
# LAWYGO HUB integration and data security - Lonexus architecture
p='pro/enterprise.html'
body=hero('LAWYGO PRO / ENTERPRISE HUB','법무법인의 업무를<br><i>보안과 협업으로 완성하다.</i>','사건 정보만이 아니라 팀의 대화, 문서, 메일, 조직관리까지. lonexus의 내부 업무 모듈과 LAWYGO PRO의 송무 운영 기능을 고객 관점에서 연결합니다.','hero-network.jpg',True,button(p,'pro/hub.html','PRO HUB 상세')+button(p,'contact.html','기업 도입 문의','btn-outline'))
body+=f'<section class="white"><div class="wrap">{section("ENTERPRISE OPERATING LAYER","내부 시스템은 보호하고, 고객 경험은 통합합니다.")}<div class="four-grid">'+''.join(f'<div class="feature-card"><span>{i:02d} / ENTERPRISE</span><h3>{title}</h3><p>{desc}</p></div>' for i,(title,desc) in enumerate([('Secure Messaging','사내 업무 채팅과 사건별 협업. 다중 조직 간 권한 분리'),('Internal Mail','직원 메일·공지 및 관련 업무 연결(실제 메일서버 필요)'),('Company Drive','Google Drive 또는 자사 문서 저장소 기반 접근 권한·이력'),('Governance & DLP','본사 관리자·보안정책·감사로그·서버 접근을 별도 통제')],1))+'</div></div></section>'
body+=f'<section class="cream"><div class="wrap">{section("IMPLEMENTATION NOTE","고객에게 보여주는 통합, 내부에서는 분리된 권한.")}<div class="reference-table light-table"><div><b>법률 송무 데이터</b><span>lawygo: 사건·고객·기일·결재·수납 (조직/테넌트 분리 필수)</span></div><div><b>기업 업무 모듈</b><span>lonexus: 채팅·사내 메일·드라이브·캘린더·보안 거버넌스</span></div><div><b>접근 방법</b><span>SSO 및 서버 간 권한검사로 연결. 공유 인증·데이터베이스 직접접속 금지</span></div><div><b>확인사항</b><span>일부 모듈은 외부 서버/키가 필요한 개발 상태입니다. 모든 모듈의 현행 운영 여부는 배포 검증이 필요합니다.</span></div></div></div></section>'
render(p,'LAWYGO PRO 엔터프라이즈·보안 ERP','lonexus 모듈을 연계하는 로펌 메신저·메일·드라이브·보안 ERP 상세','로이고 PRO',body)
# backward compatible legacy folder; avoid stale old branding/paths
for old,new in [('litigation/index.html','pro/index.html'),('litigation/dashboard.html','pro/dashboard.html')]:
 path=ROOT/old
 destination=link(old,new)
 path.write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LAWYGO PRO로 이동</title><meta http-equiv="refresh" content="0;url='+destination+'"><p><a href="'+destination+'">LAWYGO PRO로 이동</a></p></html>',encoding='utf-8')
'''
s=s.replace('# PAN\n',modulecode+'# PAN\n',1)
# add extra routes on overall brand landing before newsletter section
s=s.replace("body+=f'<section class=\"newsletter-section\"", "body+=f'<section class=\"cream\"><div class=\"wrap\">{section(\"BEYOND THE PRODUCTS\",\"검증된 개발 자산을 통합된 경험으로.\",\"기술과 정보의 출처를 확인할 수 있는 별도 상세페이지.\")}<div class=\"editorial-grid\">{card(p,\"WALLPILOT / ECONOMIC INTELLIGENCE\",\"경제·증권·DART 정보의 법률적 분석\",\"공시와 시장 데이터를 제도 해석으로 연결하는 편집 엔진.\",\"journal/market-intelligence.html\",\"hero-finance.jpg\")}{card(p,\"LONEXUS / ENTERPRISE\",\"법무법인용 협업·보안 업무 인프라\",\"사내 메신저, 메일, 권한·보안 시스템을 송무와 연결합니다.\",\"pro/enterprise.html\",\"hero-network.jpg\")}</div></div></section>'\nbody+=f'<section class=\"newsletter-section\"",1)
# add links in journal to market page 
s=s.replace("button(p,'journal/newsletter.html','무료 뉴스레터 구독')+button(p,'journal/issue-01.html','최신호 미리보기','btn-outline')", "button(p,'journal/newsletter.html','무료 뉴스레터 구독')+button(p,'journal/market-intelligence.html','경제 인텔리전스','btn-outline')")
# tech company accuracy conflict: existing wallpilot doc identifies Capital Inc., elsewhere LLC; preserve evidence conflict
s=s.replace('델라웨어 LLC — 의뢰인 제공 정보, 정식 등록증 확인 전','델라웨어 LLC — 제공 정보. 주 정부 등록증·상호 및 WallPilot 문서의 Inc. 표기와 일치 여부 확인 필요')
s=s.replace('기술 협력 구상: TerraBridge Capital LLC','미국 기술 협력 관련 사항: TerraBridge Capital LLC · 확인 필요')
# add GitHub sources to references (links private repo; customer must have repo access)
s=s.replace("('SEC','https://www.sec.gov/'", "('GitHub · shinkangteam/lawygo (비공개)','https://github.com/shinkangteam/lawygo','송무·법률백과·AI 기능 소스 및 QA 확인'),('GitHub · shinkangteam/wallpilotpro (비공개)','https://github.com/shinkangteam/wallpilotpro','DART·미국 증권뉴스·시장분석 모듈 확인'),('GitHub · shinkangteam/lonexus (비공개)','https://github.com/shinkangteam/lonexus','사내메일·메신저·보안 ERP 모듈 확인'),('SEC','https://www.sec.gov/'")
# build outputs below after site map includes extra files yes
p.write_text(s,encoding='utf-8')
print('patched bytes',len(s))
