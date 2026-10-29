from pathlib import Path
from html import escape
from weasyprint import HTML
from pypdf import PdfReader
from datetime import date
import json
ROOT=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION');OUT=ROOT/'books';OUT.mkdir(exist_ok=True)
URLS={
'Google AI search':'https://developers.google.com/search/docs/appearance/ai-features',
'Google 콘텐츠 정책':'https://developers.google.com/search/docs/fundamentals/using-gen-ai-content',
'Google 다국어 검색':'https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites',
'네이버 검색 순위':'https://help.naver.com/service/5626/contents/8022?osType=COMMONOS',
'네이버 AI 브리핑':'https://www.navercorp.com/media/pressReleasesDetail?seq=32374',
'대한변협 회원현황':'https://www.koreanbar.or.kr/pages/introduce/stat.asp',
'변호사 광고 규정':'https://www.koreanbar.or.kr/pages/board/law_view.asp?category=&page=1&searchstr=&searchtype=&seq=14402&teamcode=&types=6',
'KISA 스팸 가이드':'https://www.kisa.kr/401/form?postSeq=3608',
'KISA 정보통신망법 요약':'https://spam.kisa.or.kr/spam/cm/cntnts/cntntsView.do?cntntsId=1086&mi=1061',
'Blogger API':'https://developers.google.com/blogger/docs/3.0/reference/posts/list',
'YouTube API':'https://developers.google.com/youtube/v3/docs/videos/list',
'IAB 2025 광고시장':'https://www.iab.com/insights/internet-advertising-revenue-report-full-year-2025/',
'로톡 서비스':'https://www.lawtalk.co.kr/'
}
# Each page has distinct claims, application guidelines and sources; all forecast values are scenario assumptions, not history.
slides=[
('Executive Summary','광고비 중심의 유입에서 전문 콘텐츠 자산으로','로판은 변호사의 이름·전문 분야·콘텐츠·상담을 하나의 발견 경험으로 묶는 법률 크리에이터 플랫폼입니다.','무료 프로필과 Google Blogger·YouTube URL 등록으로 초기 공급을 낮은 진입장벽에서 확보|유료 후원 콘텐츠·브랜드 관리·분석을 명확한 고지 아래 수익화|고객은 변호사를 먼저 검색하기도 하고, 관심 주제의 글·쇼츠에서 출발하기도 합니다.','2026년 하반기','변호사 광고 규정'),
('Vision','모든 전문가는 자신만의 지식 채널을 가질 수 있다','LAWYGO JOURNAL·WIKI·NOTE·PRO·PAN을 연결해 정보 소비에서 상담·업무까지 경험을 확장합니다.','JOURNAL은 경제·제도 변화의 맥락을 설명합니다|WIKI는 법률 지식과 판례 탐색을 지원합니다|NOTE·PRO는 전문 워크플로를, PAN은 개인 전문가의 공개 채널을 담당합니다.','브랜드 아키텍처','Google AI search'),
('Problem 01','새로운 변호사에게 검색 노출은 어렵다','경쟁이 높은 키워드에서 광고와 개별 홈페이지 운영만으로 차별화하기는 쉽지 않습니다.','단일 키워드 중심 광고는 캠페인이 끝나면 재방문 자산이 적습니다|사무소가 독립 채널을 운영할 자원과 시간이 부족할 수 있습니다|전문성을 보여주는 원문·영상·프로필이 플랫폼별로 흩어져 있습니다.','고객 인터뷰 필요','네이버 검색 순위'),
('Problem 02','고객은 “누가 좋은가”보다 “내 문제를 이해하나”를 묻는다','법률 콘텐츠의 실용성, 작성자 신뢰, 연락 과정의 투명성은 전문가 탐색의 핵심입니다.','전문 분야·지역 필터만으로 실제 경험을 설명하기 어렵습니다|내용 없는 랭킹·평점은 오인을 줄 수 있습니다|잘 정리된 원문·쇼츠는 상담 전 기초 이해를 도울 수 있습니다.','프로토타입 인사이트','로톡 서비스'),
('Why Now','AI 검색은 새로운 발견 경로다','Google은 AI 검색에서도 기존 검색의 색인 가능성, 콘텐츠 품질과 신뢰성이 기본이라고 설명합니다.','독립 URL·메타데이터·내부 링크·유익한 원문은 기본입니다|특정 서비스가 반드시 AI에 인용된다는 보장은 없습니다|콘텐츠 품질과 법률적 정확성을 기반으로 접근해야 합니다.','기술변화','Google AI search'),
('Truth Check','네이버 블로그 “완전 차단·무용지물”이라는 단정은 피한다','네이버는 자체 AI 브리핑을 운영하고 있으며 검색 결과의 순위도 고정이 아니라고 안내합니다.','플랫폼마다 외부 크롤러 허용 범위가 다를 수 있습니다|Google Blogger는 독립적인 원문 채널을 추가하는 전략입니다|특정 채널을 비방하는 대신 다채널 위험 분산을 제안합니다.','신뢰 정책','네이버 AI 브리핑'),
('Customer 01','개업·소형 로펌의 무료 시작','초기 마케팅 예산이 적은 개업 변호사도 공개 전문 채널의 기초를 마련할 수 있습니다.','무료 프로필과 공식 전문 분야 등록|구글블로그와 공개 YouTube 영상 원문 연결|전화번호·이메일 비공개 상담 요청 처리.','우선 공급자','변호사 광고 규정'),
('Customer 02','중형 법무법인의 팀 콘텐츠 운영','복수 변호사와 전문 분야를 팀 채널로 노출해 각자 콘텐츠로 탐색을 확장합니다.','기관 소개와 소속 변호사 공개 정보 연결|분야별 콘텐츠 승인·검수 워크플로|팀 관리 권한과 캠페인 분석을 분리합니다.','기관 고객','로톡 서비스'),
('Customer 03','개인 고객은 문제 해결의 첫 단서를 찾는다','처음부터 전화 상담을 요청하지 않아도 주제별 요약·쇼츠를 통해 핵심 문제를 알아봅니다.','쇼츠에서 관련 구글블로그 원문으로 이동|원문 아래 해당 변호사 공개 프로필 연결|상담 신청은 개인정보 동의 후 진행합니다.','수요 측면','로톡 서비스'),
('Market Signal','공식 변호사 회원 통계는 공급 측 지표다','대한변협 2026-10-21 공시에서 서울 개업 변호사는 24,512명으로 표시됩니다. 전국 시장 규모와 매출을 동일시하지 않습니다.','가입 가능한 변호사 수는 공급 시장의 참고치입니다|유료 가입율·광고비 수준은 별도 실증이 필요합니다|지역별 공급 변화를 정기적으로 추적합니다.','서울 24,512명 · 공식 공시','대한변협 회원현황'),
('Ad Market Context','광고 시장 성장률과 법률시장 TAM은 다르다','IAB/PwC는 미국 인터넷광고 매출 2025년 2,946억 달러와 전년 대비 13.9% 증가를 발표했습니다.','미국 전체 인터넷 광고 수치를 한국 법률시장 규모로 오용하지 않습니다|광고 예산은 실제 고객 예산 조사로 바텀업 추정합니다|콘텐츠 기반 브랜드 상품의 성장 배경으로만 활용합니다.','미국 전체 광고시장 참고','IAB 2025 광고시장'),
('Product Experience','로판의 4단계 사용 흐름','관심 주제를 발견하고, 콘텐츠를 읽고, 전문가를 검토하고, 문의하는 구조입니다.','1 발견: 주제·쇼츠·후원/자연 추천 지면|2 이해: 블로그 원문·영상 설명·법률 지식 탐색|3 선택: 실명·전문 분야·소속·주소 공개 프로필|4 연결: 전화 연결 요청·비공개 이메일 문의.','서비스 흐름','로톡 서비스'),
('Product · Free','무료 계정과 무료 공개 프로필','초기 네트워크의 공급 확대를 위해 등록 자체에 과금을 두지 않습니다.','이메일 인증 후 가입 완료|변호사 자격·소속은 운영자가 별도 검증합니다|전문 글·영상 등록은 승인형 큐레이션으로 게시합니다.','무료 진입 모델','변호사 광고 규정'),
('Product · Blogger','Google Blogger 원문 연결','게시물 출처와 저작권을 보존하면서 전문 글의 발견 가능성을 높입니다.','등록 URL을 서버에서 허용 도메인으로 검증합니다|원문 링크와 작성자 정보가 서로 일치하는지 확인합니다|공개 Blogger 게시물은 공식 API에서 조회할 수 있습니다.','Blogger v3','Blogger API'),
('Product · YouTube','YouTube 쇼츠를 법률정보 지면에','전문가는 기존 공개 영상을 재활용하고 방문자는 주제별로 탐색합니다.','본인 영상 URL 제출 및 검수|썸네일·영상 제목은 공식 API와 유튜브 정책에 맞춰 갱신|단순 썸네일을 실제 동영상 재생으로 가장하지 않습니다.','Shorts','YouTube API'),
('Product · Profile','공개와 비공개의 경계가 명확한 프로필','전문가 공개 정보와 내부 연락처를 분리하는 것은 신뢰를 위한 필수 조건입니다.','공개: 이름·사무소명·소재지·전문 분야·자격 확인 상태|비공개: 직통 전화·개인 이메일·계정 메일·문의 원문|문의는 플랫폼이 인증된 비공개 채널로만 전달합니다.','Privacy by design','KISA 스팸 가이드'),
('Product · Global','영문 소개 페이지는 해외 고객 접점','영문은 단순 버튼 번역을 넘어 전문용어 검수가 이뤄진 공개 페이지로 제공해야 합니다.','영문 독립 URL과 hreflang 설계를 권고합니다|해외 면허·법률 서비스 제공 지역을 과장하지 않습니다|기계 번역 결과는 법률 전문가가 최종 감수합니다.','Cross-border discovery','Google 다국어 검색'),
('Ranking','자연 추천은 관련성과 출처 품질에 의해','유료 광고비가 자연 추천 점수에 혼입되지 않도록 분리합니다.','관련성·출처 검증·콘텐츠 품질·다양성을 가중치로 제안|반복 콘텐츠·불법 광고·과장 표현은 감점 또는 제외|알고리즘 가중치는 실제 데이터로 검증 전까지 초안입니다.','예시 가중치 40/25/20/15','변호사 광고 규정'),
('Ads','후원 콘텐츠는 광고임을 눈에 띄게 표시','투명하게 표시한 스폰서 카드는 별도 지면에서 제공하고 검수 후 게시합니다.','광고 라벨과 관련성 설명|노출·클릭 계측의 정의 고지|보장형 순위·허위 사례·경력과 성과 과장 금지.','후원 카드','변호사 광고 규정'),
('Growth Loop','양질의 공개 콘텐츠가 새로운 이용자 접점을 만든다','매번 신규 광고를 집행하는 것만으로는 충분하지 않습니다.','변호사 콘텐츠 발행 → 플랫폼 큐레이션 → 검색과 추천 접근|프로필 방문 → 상담 의향 → 필요한 경우 실제 상담|상담 경험은 개인정보 동의 범위 내에서만 개선 신호에 활용합니다.','선순환 가설','Google AI search'),
('Trust & Safety','법률광고는 엄격한 기준 아래 검토','전문가 인증과 사전 광고 검수, 허위·과장 표현 차단을 운영 우선순위로 둡니다.','대한변협 변호사 광고에 관한 규정 준수 여부를 검토합니다|실제 의뢰인 사례는 동의·익명화·재식별 위험 평가 필요|고객 후기·별점은 위조하거나 임의로 생성하지 않습니다.','운영 필수','변호사 광고 규정'),
('Email Marketing','광고성 이메일은 사전 동의한 구독자만','KISA 2026년 3월 지침은 동의 안내 시 모호한 표현 사용을 피할 것을 강조합니다.','마케팅 동의는 회원가입 필수항목과 분리합니다|모든 캠페인에 광고 표기·발신자·무료 수신거부가 필요합니다|수신거부 처리 시 즉시 재발송 대상에서 제외합니다.','Opt-in only','KISA 스팸 가이드'),
('Differentiation','로톡의 상담 발견 구조와 다른 축','로톡은 변호사 찾기 및 온라인 상담을 제공하며, 로판은 콘텐츠 채널화와 Blogger·YouTube 연결에 집중합니다.','복제 디자인보다 로이고 고유의 법률×경제 지식 브랜드 사용|개인 블로그가 플랫폼의 자산인 동시에 변호사 소유 자산|기관·기업 고객에게 경제·법률 인사이트를 연결합니다.','Positioning','로톡 서비스'),
('Ecosystem','로이고 5개 서비스의 교차 활용','PAN의 수요와 전문가 생태계를 JOURNAL·WIKI·NOTE·PRO와 연결하는 장기 구상입니다.','JOURNAL에서 경제제도 이슈 읽기|WIKI·NOTE에서 전문 리서치 보조|PRO에서 사건·업무 관리로 확장.','Cross-product','Google AI search'),
('Membership','무료→콘텐츠 전문가→유료 마케팅 전환','무료 등록자를 억지로 유료화하기보다 실질적인 콘텐츠 운영 가치가 확인될 때 전환합니다.','무료: 공개 프로필·URL 등록 요청|Pro: 캠페인 분석·브랜드 도구|Business: 다계정·법무법인 워크플로·운영 지원.','가치 검증 후 유료화','변호사 광고 규정'),
('Proposed Pricing','제안 가격은 매출 실적이 아니다','요금은 운영 승인 전 시뮬레이션 기준이며 실제 청구를 시작하지 않았습니다.','Free 0원: 기본 소개와 검수형 콘텐츠 등록|Pro 49,000원/월: 캠페인 분석 및 브랜드 지면 기능(가정)|Business 179,000원/월: 기관·팀 계정과 운영 지원(가정).','가격 미확정','KISA 스팸 가이드'),
('Revenue Streams','가입비보다 반복 사용가치 기반 수익','구독과 명시적 후원 콘텐츠 판매의 조합이 핵심입니다.','월 구독: 편집 도구·통계·팀 기능|후원 지면: 심사 통과한 광고성 콘텐츠의 게재|B2B: 법무법인 교육·운영·콘텐츠 연동 서비스.','수익 가설','IAB 2025 광고시장'),
('Unit Economics','단위경제성은 초기 베타에서 검증해야 한다','성장 전에 인증·검수·고객지원 비용과 광고 운영의 단위비용을 계측합니다.','CAC = 신규 유료회원 획득 비용 / 신규 유료회원 수|기여이익 = 매출 – 결제수수료 – 콘텐츠 검수 – 호스팅 변동비|LTV 산정은 실제 유지율이 확보되기 전까지 투자 가정입니다.','측정 체계','Google AI search'),
('Pilot Design','첫 90일은 핵심 퍼널을 검증','시범 법무법인·변호사 참여를 통해 실제 콘텐츠 공급과 탐색 행동을 확인합니다.','1~30일: 인증·등록·저작권·정책 흐름 검증|31~60일: 카테고리·추천·검색 효용 테스트|61~90일: 상담 유입 및 유료 지면 수용성 조사.','90일 파일럿 가정','변호사 광고 규정'),
('Metrics','북극성 지표: 검증된 콘텐츠 기반 상담 연결','유료 클릭 수보다 신뢰를 잃지 않는 상담 연결을 우선 평가합니다.','활성 변호사: 공개 프로필 자격검증 완료 수|콘텐츠: 검수 완료된 원문·영상 수|상담: 접수 완료와 부적합 요청 비율을 분리 측정.','신뢰·성장 동시','KISA 스팸 가이드'),
('Illustrative Funnel','예시 퍼널 — 실적이 아닌 모델 가정','아래 수치는 시연 목적으로 작성한 월간 운영 시나리오입니다.','월 30,000 콘텐츠 노출 → 2,400 유효 클릭(CTR 8% 가정)|프로필 방문 1,200 → 상담 신청 48(4% 가정)|개인정보 동의 및 적합성 검수 후 유효 연결 30건(가정).','가정 · 8% / 4%','Google AI search'),
('Revenue Scenario A','보수적 시나리오: 유료 50개 계정','유료 Pro 40명, Business 10곳이 유지된다는 단순 모델입니다.','Pro: 40 × 49,000원 = 196만원/월|Business: 10 × 179,000원 = 179만원/월|월 반복매출(MRR) 375만원. 광고수익·세금·비용은 제외한 가정입니다.','가정 MRR 375만원','IAB 2025 광고시장'),
('Revenue Scenario B','기준 시나리오: 유료 200개 계정','유료 Pro 160명, Business 40곳으로 확대될 경우의 예시입니다.','Pro: 160 × 49,000원 = 784만원/월|Business: 40 × 179,000원 = 716만원/월|MRR 1,500만원. 이익이 아니며 달성 가능성은 검증되지 않았습니다.','가정 MRR 1,500만원','IAB 2025 광고시장'),
('Revenue Scenario C','확장 시나리오: 유료 600개 계정','유료 Pro 480명, Business 120곳이 유지되는 이상적 모델입니다.','Pro: 480 × 49,000원 = 2,352만원/월|Business: 120 × 179,000원 = 2,148만원/월|MRR 4,500만원. 판매 예측치가 아닌 민감도 분석입니다.','가정 MRR 4,500만원','IAB 2025 광고시장'),
('Cost Model','비용구조의 중심은 신뢰 운영','오픈 플랫폼은 인프라뿐 아니라 신원 검증·법률광고 검수·고객지원이 필요합니다.','고정비: 제품개발·보안·고객지원·콘텐츠 운영 인건비|변동비: 이메일·스토리지·트래픽·결제수수료·신원확인|비용 최적화보다 규정 위반 리스크와 개인정보 보호를 우선합니다.','예산 추정 필요','변호사 광고 규정'),
('Platform Architecture','법률 콘텐츠 데이터와 개인정보 저장소 분리','공개 페이지와 개인정보·상담 내역을 서로 다른 접근권한·테이블로 분리합니다.','공개 캐시: 콘텐츠 메타데이터·프로필 표시정보|개인정보 DB: 이메일·연락처·상담 요청·마케팅 동의|관리자: 인증·검수·승인·감사로그로 모든 변경 기록.','개념설계','KISA 스팸 가이드'),
('Security','안전한 초기 MVP의 최소 요구조건','보안은 광고 플랫폼 신뢰의 기본입니다.','HTTPS·비밀키·세션 보안·CSRF·Rate limiting·입력 검증|DB 백업·복구훈련·개인정보 파기 기한·접근 통제|외부 URL을 서버에서 임의로 가져오지 않는 SSRF 방어.','보안 체계','KISA 스팸 가이드'),
('International','국제 고객 연결은 번역 품질에서 시작','영문 콘텐츠와 해외 문의는 번역 정확도와 관할 범위를 명확히 해야 합니다.','영문 소개·분야·대표글은 전문 검수를 거쳐 발행|외국인 고객에게 한국 변호사의 업무 범위를 정확히 설명|운영 시 영문 별도 URL과 hreflang 설정.','전문가 감수 필수','Google 다국어 검색'),
('Partnership','법무법인 업무협약을 통한 생태계 확장','로판은 광고만 파는 서비스가 아니라 공동 콘텐츠·교육·정보 제공 네트워크를 제안합니다.','공동 칼럼·숏폼 제작과 법률정보 큐레이션|법무법인 전문 분야별 공동 웨비나|MOU 체결 전 권리·개인정보·광고 규정을 개별 검토합니다.','MOU 제안 단계','변호사 광고 규정'),
('Go to Market','변호사가 사용하는 언어로 제품을 설명','고객에게는 검색과 상담의 편리함, 변호사에게는 콘텐츠 자산을 중심으로 소개합니다.','무료 가입 → 프로필 정리 → 첫 블로그 등록 → 첫 쇼츠 등록|대상: 신규 개업, 지역 전문, 콘텐츠 제작 경험 있는 변호사|우선 측정: 콘텐츠 게시율과 활성 프로필, 상담 문의 적합성.','4-step onboarding','로톡 서비스'),
('Risks','핵심 위험과 완화 조치','수익 이전에 법률광고·개인정보·신뢰 문제를 통제해야 합니다.','과장 성과·랭킹: 광고 심사와 광고 표기 의무|허위 프로필: 자격 및 소속 검증, 운영자 승인|저작권·상담정보: 저작권 신고·민감정보 비공개·기록 삭제 체계.','컴플라이언스','변호사 광고 규정'),
('Funding Use','투자 재원 사용 계획 — 제안 비율','총 투자금 규모는 확정되지 않았으며, 아래 구성은 우선순위 예시입니다.','개발·제품 40%: 등록·검증·콘텐츠·대시보드|보안·규정 검수 25%: 법률 검토, 개인정보 대응|고객 획득 25%, 예비비 10%; 실제 투자 승인에 따라 조정.','가정 · 투자금 미정','KISA 스팸 가이드'),
('Milestones','12개월 로드맵 — 단계별 검증 게이트','검증 없이 광고 집행을 늘리지 않고 법적·기술적 준비 상태를 평가합니다.','Q1: 비공개 베타, 정회원 인증, 검수 기준 정립|Q2: 공개 콘텐츠·쇼츠 연동과 가입 퍼널|Q3: 제한적 유료 캠페인 테스트, 통계 품질 개선|Q4: 법무법인 팀 상품과 영문 채널 확대.','로드맵 제안','Google AI search'),
('Investment Thesis','투자자가 확인해야 할 것은 실제 반복 이용이다','검색 자산을 브랜드와 플랫폼의 장기 가치를 묶는 수단으로 활용합니다.','공개 콘텐츠의 공급과 갱신률이 안정적인지 확인|상담 연결이 과장 없이 실제 운영되는지 확인|광고 수익보다 규정 준수와 반복 이용 지표를 검증.','실사 요청','IAB 2025 광고시장'),
('Closing','법률 전문지식의 발견과 신뢰를 연결한다','LAWYGO PAN은 변호사의 전문 콘텐츠와 고객의 탐색을 연결하는 브랜드 플랫폼으로 성장하는 것을 목표로 합니다.','도입 논의: 무료 전문 계정 + Blogger·YouTube 콘텐츠 등록|법무법인 MOU: 공동 콘텐츠와 마케팅 운영|투자 미팅: 재무 모델, 규제 리스크와 제품 실사.','Contact · sk@terrabridge.us','변호사 광고 규정')]
assert len(slides)>=40,len(slides)

manuals={
'company-profile':('회사소개서','LAWYGO PAN과 LAWYGO 서비스 생태계',[
('회사 개요','LAWYGO는 법률·경제 정보와 전문 업무 흐름을 연결하는 브랜드입니다.','JOURNAL은 미국·국내 경제제도와 법률적 해설을 제공|WIKI는 법률백과와 판례 정보 탐색|NOTE는 AI 기반 전문 문서 작업 지원|PRO는 송무 관리, PAN은 전문가 콘텐츠·마케팅 채널'),
('LAWYGO PAN의 목적','검색 친화적 공개 콘텐츠와 투명한 전문가 프로필을 연결합니다.','변호사의 개인 브랜드 구축 지원|이용자에게 원문 중심의 정보 접근 제공|실제 상담의 질이나 결과는 보증하지 않음'),
('브랜드 디자인','진한 네이비, 따뜻한 아이보리, 차분한 골드로 신뢰감을 표현합니다.','L 심벌과 내부 작은 사각형 유지|데스크톱·모바일 반응형 적용|이미지: AI 생성 시연용임을 고지'),
('플랫폼 차별화','법률 콘텐츠의 직접 소유권과 전문 출처를 중요하게 다룹니다.','검색·영상·블로그를 별개의 방문 경로로 운영|후원 콘텐츠와 자연 추천 지면을 명확히 분리|회원이 자신의 채널 주소를 재사용'),
('법무법인 제휴','파트너십은 영업 대행이 아니라 상호 협력의 기회를 제안합니다.','공동 콘텐츠 제작 및 정보 교류|전문가 인증·브랜드 가이드 수립|업무협약의 구체 조건은 서면 합의 후 확정'),
('기업 정보·검증','미국 법인과 국내 제휴 창구의 지위는 별도로 설명합니다.','미국법인 표기: TerraBridge Capital LLC - 공식 서류 확인 후 표기 확정|국내 제휴 창구: 대한에이전트협회(영업소 안내)|한국 사무소: 서울 서초구 서초중앙로22길 47, INS-154'),
('운영 책임','법률서비스 제공은 각 자격을 가진 변호사에게 있습니다.','상담 문의 중개 플랫폼과 실제 법률대리를 구분|광고성 콘텐츠 심사 및 신고 절차 운영|사용자 개인정보 처리 목적과 범위 고지'),
('연락 창구','파트너십 제안 및 운영 협의를 위한 안내입니다.','파트너십: sk@terrabridge.us|국내 창구: shinkang888@gmail.com|전화 0505-248-2468 · 팩스 0505-284-2468'),
]),
'user-manual':('회원가입·콘텐츠 등록 사용자 매뉴얼','변호사를 위한 LAWYGO PAN 사용 가이드',[
('이용 전 안내','서비스 시안의 샘플 변호사·콘텐츠는 실제 계정이 아닙니다.','온라인 API가 설정되어야 실제 등록·인증이 진행됩니다|로그인 없이 공개 콘텐츠는 열람 가능|법률 정보는 일반적 안내이며 변호사 자문을 대체하지 않습니다'),
('STEP 1 무료 가입','pan.lawygo.com/free-signup.html 에서 본인 이메일과 표시할 정보를 입력합니다.','이메일은 인증 링크를 수신하기 위한 내부 정보입니다|이름·소속·지역·전문 분야는 공개 후보 정보입니다|마케팅 수신동의는 선택이고 미선택해도 가입할 수 있습니다'),
('STEP 2 이메일 인증','등록 완료 메일에 포함된 고유 링크를 24시간 내에 확인합니다.','인증 메일이 안 오면 스팸함과 SMTP 설정 확인|로그인 세션은 쿠키에 안전하게 보관|변호사 자격 검증은 이메일 인증과 별개의 과정입니다'),
('STEP 3 변호사 자격 승인','운영팀이 변호사 자격·소속을 검증한 뒤 공개 노출을 승인합니다.','자격 미확인 계정은 검증 완료로 표시하지 않습니다|전문 분야는 객관적으로 설명해야 합니다|사례 수와 만족도를 임의로 기재하지 않습니다'),
('STEP 4 Blogger 글 등록','내 Google Blogger 공개 글 URL과 제목을 제출합니다.','본인 소유의 글 또는 적법한 사용권 필요|비공개 글·타인의 글은 승인되지 않습니다|관리자 승인 전까지 공개 피드에 반영되지 않습니다'),
('STEP 5 YouTube 쇼츠 등록','내 공개 YouTube 영상 URL을 입력합니다.','YouTube URL인지 사전 검증|오해를 부르는 썸네일·상담 보장형 제목 금지|공개 영상 정보는 유튜브 API 연결 후 자동 갱신 가능'),
('STEP 6 내 프로필 공개','법률사무소·주소·전문 분야와 공개 콘텐츠를 확인합니다.','연락처는 직통 공개하지 않습니다|전화 연결은 향후 안심전화 번호로 대체 가능|이메일 문의는 공개 주소가 아닌 버튼으로 처리'),
('STEP 7 상담 요청 처리','고객은 상담 목적과 필수 연락정보를 입력합니다.','민감한 사건 사실을 공개 댓글로 받지 않습니다|연락 목적·보관 기간을 안내합니다|계약 체결과 실제 수임은 당사자 간 별도 과정입니다'),
('STEP 8 광고 검토','후원 지면 신청은 광고 유형과 콘텐츠 원문을 제출합니다.','광고임을 별도로 표시합니다|사전 승인 전에는 게시·결제를 하지 않습니다|조회·클릭 수와 상담 성과는 서로 다른 지표입니다'),
('STEP 9 대시보드 확인','콘텐츠 노출·유효 클릭·상담 요청을 구분해서 봅니다.','샘플 수치를 실제 성과로 오인하지 않습니다|집계 방식과 봇 필터링 정책 점검|개인정보는 통계 집계 전 최소화합니다'),
('영문 페이지 안내','영문 서비스는 번역 참고 기능부터 제공하고 공식 영문 콘텐츠는 검수합니다.','번역된 법률 용어는 전문가 확인 필요|해외 사건 수임 자격을 추정하지 않습니다|다국어 검색의 최선 관행에 맞춰 언어별 URL 검토'),
('문제 해결 및 수신거부','콘텐츠 오류 신고·광고성 이메일 철회를 지원합니다.','개별 이메일 하단 수신거부 링크 사용|이용자 콘텐츠 삭제 요청 접수|문의: sk@terrabridge.us'),
]),
'advertising-policy':('사이트 광고규정·심사 매뉴얼','법률광고의 신뢰와 유료 노출의 투명성',[
('광고 정책의 목적','LAWYGO PAN은 법률광고와 일반정보의 경계를 명확히 합니다.','유료 광고 여부 고지|광고와 자연 노출의 알고리즘 분리|공식 대한변협 규정과 상충 시 해당 규정 우선'),
('허용되는 광고 형태','주제별 후원 카드·검수된 쇼츠 홍보·전문가 프로필 연결입니다.','원문 링크 필수|작성자·광고주 식별|정확한 전문 분야·소속 정보만 표시'),
('금지되는 표현','승소 보장·절대 1위·무조건 환급·성과 보증을 금지합니다.','실제 자격을 과장하는 인증 표장 금지|타 변호사 비방 및 허위 비교 금지|의뢰인 식별이 가능한 사건 정보 게시 금지'),
('심사 절차','광고 URL 제출 후 사전 승인 전에는 게시·청구가 시작되지 않습니다.','1 기초 정보·권리 확인|2 대한변협 광고 규정 적합성 검토|3 소재·문구 수정 요청 및 최종 승인'),
('광고 라벨','후원 콘텐츠는 눈에 잘 띄는 위치에 광고라고 표시합니다.','[광고] 라벨 고정|모바일 첫 화면에서도 시인성 유지|추천 전문가와 후원 변호사 구분'),
('추천 알고리즘','자연 추천 점수에 광고비 또는 구매 이력을 반영하지 않습니다.','주제 관련성·출처 검증·품질·다양성|같은 전문 계정의 도배 방지|순위 보장형 광고 상품 판매 금지'),
('광고 지표','노출·클릭·상담 요청은 서로 다른 의미를 갖습니다.','봇 의심 클릭 제외|유효 노출 기준 고지|부정 트래픽·비정상 패턴 사후 모니터링'),
('광고 이의신청','광고 거절·삭제 사유를 구체적으로 안내합니다.','운영자 재심 신청|필요한 경우 협회 규정 재검토|악용 계정은 이용제한·기록 보존'),
('광고성 이메일','이메일은 명시적 사전동의가 확인된 수신자에게만 발송합니다.','제목에 [광고] 표기|발신자·문의처 및 무료 수신거부 제공|수신거부 즉시 차단 및 처리 이력 관리'),
('정기 검토','정책과 관련 법령이 변경되면 최신 기준으로 개정합니다.','2025 대한변협 광고 규정 참조|2026 KISA 스팸안내서 참조|법률 전문가의 최종 검수 필요'),
]),
'privacy-manual':('개인정보보호지침·운영 매뉴얼','원칙: 최소 수집, 분리 보관, 목적 외 사용 금지',[
('수집 목적','이메일 인증·전문가 자격 확인·상담 연결에 필요한 정보만 수집합니다.','회원 가입: 이메일·이름, 선택 소속·지역·전문 분야|문의 접수: 신청자가 직접 제공한 연락처·상담 내용|광고 동의: 동의 여부·확인 일시·수신거부 상태'),
('공개 범위','전화번호·개인 이메일을 공개 페이지의 HTML에 기재하지 않습니다.','공개 후보: 이름·상호·업무 주소·전문 분야|비공개: 로그인 이메일·직통번호·상담 요청|공개 전 전문가의 검토·승인 필수'),
('동의 구분','서비스 제공 동의와 광고성 정보 수신동의를 분리합니다.','마케팅 선택 동의 기본값 해제|사전 동의 없는 마케팅 발송 금지|수신거부 상태를 우선 적용'),
('보관과 파기','개인정보는 목적 달성 이후 지체 없이 파기합니다.','보관 기간은 실제 운영법무 검토 후 확정|삭제 요청 수신과 처리 이력 기록|백업 데이터 파기·복원 정책 연계'),
('제3자 제공','변호사에게 문의 내용을 전달할 때 목적·항목·수신자를 안내합니다.','필요한 최소 정보만 제공|사용자 동의 없는 광고주 공유 금지|해외 이전이 있으면 법정 고지 검토'),
('접근 통제','개인정보 DB와 공개 콘텐츠 데이터는 분리합니다.','관리자 최소 권한과 다중요소 인증|직원 계정 입퇴사 관리|개인정보 조회 감사 로그'),
('이용자 권리','열람·정정·삭제·동의 철회 요청 경로를 제공합니다.','고객센터 이메일을 안내|정정 후 공개 프로필 캐시 갱신|과도한 본인확인 요구 금지'),
('침해 대응','침해 의심 즉시 계정·토큰을 회수하고 영향을 평가합니다.','증거 보전과 보안 사고 기록|법정 신고·통지 의무 해당 여부 검토|재발 방지 조치 보고'),
('법률·표시사항','사업자·개인정보 보호책임자·문의처는 실제 운영 법인 기준으로 확정해야 합니다.','문서 자체는 운영 검토용 초안|한국·미국 사업주체의 역할 분리|최종 정책은 법률 검토 후 공개'),
]),
'security-manual':('사이트 보안규정·보안운영 매뉴얼','LAWYGO PAN 안전한 데이터·콘텐츠 운영 기준',[
('보안 책임 구분','제품 운영·외부 전문 변호사·광고주 권한을 분리합니다.','최소권한 원칙|권한 변경은 승인 기록 필요|개인정보 열람 권한의 정기 점검'),
('인증·세션','이메일 인증과 변호사 자격증명 검증을 별개로 취급합니다.','이메일 인증 토큰 만료 및 일회성 사용|보안 쿠키 HttpOnly·Secure·SameSite|운영자 계정은 강력한 MFA 필수'),
('API 보안','공개 폼을 통한 취약점과 남용을 방어합니다.','입력 길이·형식·허용 도메인 검증|속도 제한·서버 측 권한 검사|CSRF와 CORS·보안 헤더 검토'),
('외부 콘텐츠','Blogger·YouTube URL을 무조건 서버에서 가져오지 않습니다.','화이트리스트 검증|서버 SSRF 방어|스크립트·HTML 임베드 안전화'),
('비밀키·배포','SMTP 비밀번호·서명키·DB 주소를 저장소에 커밋하지 않습니다.','환경변수 또는 Secret Manager 사용|배포별 키 분리|유출 감지 시 즉시 회전'),
('전송·저장 암호화','실제 운영은 HTTPS·TLS, 암호화 저장소를 기본으로 합니다.','백업 저장소 접근통제|클라이언트 코드에 연락처 원문 포함 금지|동의 없이 상담 원문을 AI 모델에 전송 금지'),
('로그·관측','개인정보를 기록하지 않는 운영 로그가 필요합니다.','인증 실패·접근 거부·검수 승인 로깅|사고 탐지·이상 트래픽 경보|법정 보존 기간과 최소 보관 원칙 병행'),
('광고 사기 방어','유료 노출은 이상 클릭·중복 노출을 감시합니다.','상세 분석 데이터 익명화|광고 고객 실적 과장 방지|검수 승인 이력 변경 불가 로그'),
('백업과 재해복구','유실·랜섬웨어에 대비한 독립 백업과 복구 훈련을 실시합니다.','일일 백업과 별도 지역 보관(제안)|주기적 복구 테스트|RTO/RPO는 운영 목표에 따라 설정'),
('보안 테스트','침투시험·종속성 스캔·웹훅 재전송 테스트를 계획합니다.','OWASP Top 10 중심 점검|외부 라이브러리 취약점 알림|배포 전 개인·회원권한 접근 점검'),
('법적 사고 대응','취약점 발견·침해 신고·정보주체 통지 책임을 문서화합니다.','사고 발생 시간과 조치 책임자 기록|규제 기관 신고 해당 여부 판단|구독자·개인정보 삭제 요청을 추적'),
('운영 전 점검표','프런트엔드 시안과 백엔드 예제를 상용 배포와 혼동하지 않습니다.','테스트 SMTP·DB를 운영 인프라로 교체|법무 책임자 정책 승인·모의 사고훈련|정기 접근권한 검토 후 출시'),
])
}

CSS='''@page{size:A4 landscape;margin:0}html,body{margin:0;font-family:"NanumSquare","Noto Sans KR","UnDotum",sans-serif;color:#11283e;background:#f5f3ee}*{box-sizing:border-box}.page{width:297mm;height:210mm;padding:18mm 20mm;page-break-after:always;position:relative;overflow:hidden;background:#f9f7f1}.page:before{content:"";position:absolute;top:0;left:0;right:0;height:7px;background:#0d2b47}.cover{background:linear-gradient(125deg,#0b2943,#173b5a);color:white}.cover:before{background:#cda974}.eyebrow{font-size:12pt;letter-spacing:.2em;color:#ae854d;font-weight:700}.cover .eyebrow{color:#e1c693}.logo{font:700 22pt Georgia,serif;letter-spacing:.04em}.logo i{color:#c9a267;font-style:normal}.page h1{font-size:32pt;line-height:1.3;max-width:230mm;letter-spacing:-.04em;margin:14mm 0 5mm}.cover h1{font-size:40pt;margin-top:30mm}.page h2{font-size:24pt;margin:8mm 0 5mm;letter-spacing:-.03em}.intro{font-size:15pt;line-height:1.7;max-width:230mm;color:#52677b}.cover .intro{color:#dfebf1}.bullets{display:grid;grid-template-columns:1fr 1fr;gap:5mm;margin-top:9mm}.item{border:1px solid #dfded8;background:#fff;padding:5mm 7mm;min-height:24mm;border-left:4px solid #be9864;font-size:12.5pt;line-height:1.65}.page .item:nth-child(3){grid-column:span 2}.metric{font-size:17pt;color:#b58244;margin-top:9mm;font-weight:700}.ref{position:absolute;left:20mm;bottom:13mm;font-size:8.5pt;color:#687c8d;max-width:245mm}.counter{position:absolute;right:20mm;bottom:13mm;font-size:9pt;color:#a1865e}.cover-img{width:215mm;height:57mm;object-fit:cover;border-radius:7mm;margin-top:13mm}.bar{height:6mm;background:#e5e6e7;border-radius:7px;overflow:hidden;margin:8px 0}.bar em{display:block;height:100%;background:#ad8758}.num{font-size:13pt;color:#c8ab7c;letter-spacing:.1em}
a{color:#b8874f}#toc{list-style:none}#toc li{margin:3mm 0;font-size:11pt}
@media screen{body{padding:12px}.page{box-shadow:0 8px 25px #11283e12;margin:0 auto 15px}}
'''

def cover(title,subtitle,series,number,total):
 img=(ROOT/'site'/'assets'/'pan-editorial-6.webp').resolve().as_uri()
 return f'<section class="page cover"><div class="logo">LAWYGO <i>PAN</i></div><div class="eyebrow" style="margin-top:22mm">{escape(series)} · 2026</div><h1>{escape(title)}</h1><p class="intro">{escape(subtitle)}</p><img class="cover-img" src="{img}"><div class="ref" style="color:#b4c6d7">PAN.LAWYGO.COM · 제공 목적: 사업 검토 및 제안 · 실제 실적 수치는 별도 명시</div><div class="counter">01 / {total:02d}</div></section>'

def page(title,label,summary,bullets,metric,index,total,source):
 b=''.join(f'<div class="item">{escape(x.strip())}</div>' for x in bullets.split('|') if x.strip())
 url=URLS.get(source,'')
 ref=f'출처·참고: <a href="{url}">{escape(source)}</a> · 자료는 사실과 가정을 구분해야 합니다.' if url else '운영 제안 및 시장 가정 · 검증 전 초안'
 return f'<section class="page"><div class="logo">LAWYGO <i>PAN</i></div><div class="eyebrow" style="margin-top:12mm">{escape(label.upper())}</div><h2>{escape(title)}</h2><p class="intro">{escape(summary)}</p><div class="bullets">{b}</div><div class="metric">{escape(metric)}</div><div class="ref">{ref}</div><div class="counter">{index:02d} / {total:02d}</div></section>'

def render(name,title,sub,rows,series):
 sections=[cover(title,sub,series,1,len(rows)+1)]
 for i,r in enumerate(rows,2):
  if len(r)==6: label,heading,summary,points,metric,source=r
  else:heading,summary,points=r;label=series;metric='운영 지침 · 검토용';source='변호사 광고 규정'
  sections.append(page(heading,label,summary,points,metric,i,len(rows)+1,source))
 body=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{escape(title)} | LAWYGO PAN</title><style>{CSS}</style></head><body>{''.join(sections)}</body></html>'''
 path=OUT/f'{name}.html';path.write_text(body)
 pdf=OUT/f'{name}.pdf';HTML(string=body,base_url=str(OUT)).write_pdf(pdf)
 n=len(PdfReader(pdf).pages)
 print(name,'html sections',len(rows)+1,'pdf pages',n, 'size',pdf.stat().st_size)
 return n

# Deck has a cover plus 43 unique narrative slides = 44 pages
assert len(slides)>=40
render('investor-deck','LAWYGO PAN 투자제안서','법률 콘텐츠·전문가 플랫폼 | 시장·제품·수익 모델·정책·리스크·투자 가정',slides,'INVESTMENT PROPOSAL')
for name,(title,sub,rows) in manuals.items():
 render(name,title,sub,rows,'POLICY & OPERATIONS')
(OUT/'RESEARCH_SOURCES.md').write_text('# 공개 근거자료와 검증 범위\n\n'+'\n'.join(f'- [{a}]({b})' for a,b in URLS.items())+'\n\n> 투자 시나리오 숫자와 서비스 제안 가격은 실제 매출 실적이 아닙니다. 확인된 서울 개업 변호사 24,512명은 전국 유료회원 수가 아닙니다.\n')
