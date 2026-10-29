from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION/site')
nav=[('lawyers.html','변호사 찾기'),('categories.html','전문 분야'),('content-feed.html','콘텐츠'),('shorts-feed.html','쇼츠'),('blogger-feed.html','블로그'),('lawfirms.html','법무법인'),('pricing.html','요금제'),('partnership.html','파트너십')]
for p in ROOT.glob('*.html'):
 if p.name=='marketing-email-preview.html':continue
 s=BeautifulSoup(p.read_text(),'html.parser')
 primary=s.select_one('.nav')
 if primary:
  primary.clear()
  for href,text in nav:
   a=s.new_tag('a',href=href);a.string=text
   if text=='콘텐츠':a['data-i18n']='법률 콘텐츠'
   if text=='쇼츠':a['data-i18n']='쇼츠'
   primary.append(a)
  top=s.select_one('.actions a.btn.primary')
  if top:
   top['href']='free-signup.html';top.string='무료 회원가입'
 if p.name in ['index.html','content-feed.html','creator-channels.html']:
  imgs=s.select('.pn-story img')
  for i,img in enumerate(imgs):
   img['src']='assets/'+['legal-consultant.webp','male-attorney.webp','hero-attorney.webp','lawyer-video.webp','hero-attorney.webp','male-attorney.webp'][i%6]
   img['alt']='가상 변호사 프로필 이미지(디자인 시연용)'
 p.write_text(str(s))
print('updated',len(list(ROOT.glob('*.html'))))
