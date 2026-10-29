from pathlib import Path
from bs4 import BeautifulSoup
from shutil import copy2
import html, re
ROOT=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION');SITE=ROOT/'site';BOOK=ROOT/'books';AS=SITE/'assets'
(SITE/'books').mkdir(exist_ok=True)
for x in BOOK.glob('*'):
 if x.suffix in {'.pdf','.html'}:copy2(x,SITE/'books'/x.name)
for p in SITE.glob('*.html'):
 s=p.read_text();s=s.replace('../books/','books/')
 if p.name!='marketing-email-preview.html':
  s=s.replace('</body>','<div style="background:#102a43;color:#bbcbd9;text-align:center;font-size:11px;padding:12px">AI-generated imagery is used for illustration. · 일부 이미지는 AI로 생성한 시연 이미지입니다.</div></body>')
 p.write_text(s)
# Create standalone brochure/policy pages as actual site destinations.
sample=BeautifulSoup((SITE/'content-feed.html').read_text(),'html.parser')
items=[('investor-overview','투자제안서','투자 검토용 46쪽 사업제안서','investor-deck'),('company-intro','회사소개서','LAWYGO 통합 브랜드, 법률 지식과 콘텐츠 생태계','company-profile'),('member-guide','회원가입·콘텐츠 등록 매뉴얼','무료 가입부터 Google Blogger·YouTube 연결까지','user-manual'),('ad-policy-center','광고규정','광고 심사·후원 콘텐츠 표시·추천 알고리즘 분리','advertising-policy'),('privacy-center','개인정보보호지침','연락처 비공개·상담정보 보호·수신동의 및 수신거부','privacy-manual'),('security-center','사이트 보안규정','인증·권한·암호화·침해사고 대응 절차','security-manual')]
for slug,title,subtitle,name in items:
 s=BeautifulSoup(str(sample),'html.parser')
 main=s.select_one('main')
 body=f'''<section class="pn-hero"><div class="wrap"><div class="mini">LAWYGO PAN · CORPORATE DOCUMENTS</div><h1>{html.escape(title)}</h1><p class="subtitle">{html.escape(subtitle)}</p><div class="pn-action"><a href="books/{name}.html">HTML 책자 읽기 →</a><a class="alt" href="books/{name}.pdf">PDF 책자 열기 →</a></div></div></section><section class="pn-section"><div class="wrap"><h2>검토 범위와 주요 내용</h2><div class="pn-cards"><div class="pn-feature"><h3>실제 운영 범위</h3><p>모든 조항은 운영 시스템과 관련 법규를 확인한 뒤 최종 승인합니다.</p></div><div class="pn-feature"><h3>한국어 문구 검토</h3><p>용어·브랜드명·과장 표현을 정리하고 개인정보 공개 기준을 구분합니다.</p></div><div class="pn-feature"><h3>고객·투자자용 안내</h3><p>설명서의 예시 수치는 실적이 아닌 계획과 가정으로 표시합니다.</p></div></div><div class="pn-action"><a href="books/{name}.pdf">PDF 파일 확인</a><a href="books/{name}.html" class="alt" style="color:#102a43;border:1px solid #ccc">HTML 책자 보기</a></div></div></section>'''
 main.replace_with(BeautifulSoup('<main id="main">'+body+'</main>','html.parser'))
 s.title.string=title+' | LAWYGO PAN';s.select_one('link[rel="canonical"]')['href']=f'https://pan.lawygo.com/{slug}.html'
 (SITE/f'{slug}.html').write_text(str(s))
# Keep brand vocabulary consistent; replace a few known clumsy expressions in new pages only
for p in SITE.glob('*.html'):
 text=p.read_text()
 text=text.replace('구글블로그·유튜브 콘텐츠와 공개 프로필이 발견되는 공간','구글블로그·유튜브 콘텐츠와 공개 프로필을 발견할 수 있는 공간')
 text=text.replace('좋은 위치는 먼저 준비한','발견될 기회는 미리 준비한')
 text=text.replace('내 유튜브 영상의 공개 URL','내 유튜브 영상의 공개 주소')
 text=text.replace('마케팅 광고성 이메일 수신','광고성 정보 이메일 수신')
 p.write_text(text)
# Sitemap and robots
pages=sorted(f.name for f in SITE.glob('*.html') if f.name!='404.html')
xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>https://pan.lawygo.com/{f}</loc></url>' for f in pages)+'</urlset>'
(SITE/'sitemap.xml').write_text(xml)
(SITE/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /private-inquiry.html\nDisallow: /unsubscribe.html\nSitemap: https://pan.lawygo.com/sitemap.xml\n')
# Add docs links to shared footer for all pages
for p in SITE.glob('*.html'):
 if p.name=='marketing-email-preview.html':continue
 s=BeautifulSoup(p.read_text(),'html.parser');foot=s.select_one('.footer .foot-end')
 if foot:
  links=BeautifulSoup('<div style="margin-top:10px"><a style="color:#e7cea7;margin-right:10px" href="member-guide.html">회원 이용안내</a> <a style="color:#e7cea7;margin-right:10px" href="ad-policy-center.html">광고운영정책</a> <a style="color:#e7cea7;margin-right:10px" href="privacy-center.html">개인정보보호</a> <a style="color:#e7cea7;margin-right:10px" href="security-center.html">보안정책</a> <a style="color:#e7cea7" href="investor-overview.html">투자자료</a></div>','html.parser')
  foot.append(links)
 p.write_text(str(s))
print('final pages',len(pages)+1,'pdfs',len(list(BOOK.glob('*.pdf'))))
