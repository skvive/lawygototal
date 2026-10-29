from pathlib import Path
from PIL import Image,ImageEnhance
from bs4 import BeautifulSoup
root=Path('/mnt/data/LAWYGO_PAN_DELIVERY');assets=root/'assets'
# Distinct AI-generated fictional professional portrait from a separate generation.
src=Image.open('/mnt/data/a_polished_multi_panel_ui_website_showcase_image.png').convert('RGB')
print('mockup size',src.size)
# Main hero distinct woman (no lettered UI in crop): right middle of left hero area
W,H=src.size
crop=src.crop((int(W*.26),int(H*.055),int(W*.55),int(H*.41))).resize((1024,600),Image.Resampling.LANCZOS)
crop.save(assets/'portrait-female-2.webp','WEBP',quality=90)
# Crop of original generation with no legal text in main background
for name in ['lawyer-sujeong.html','lawyers.html','index.html']:
 p=root/name;s=p.read_text(encoding='utf-8')
 if name=='lawyer-sujeong.html':s=s.replace('assets/portrait-female.webp','assets/portrait-female-2.webp')
 elif name=='lawyers.html':
  # third profile image only
  s=s.replace('가상 최수정 변호사 프로필" loading="lazy"','가상 최수정 변호사 프로필" loading="lazy"')
  pos=s.find('href="lawyer-sujeong.html"');a=s[:pos];b=s[pos:];b=b.replace('assets/portrait-female.webp','assets/portrait-female-2.webp',1);s=a+b
 else:
  pos=s.find('href="lawyer-sujeong.html"');a=s[:pos];b=s[pos:];b=b.replace('assets/portrait-female.webp','assets/portrait-female-2.webp',1);s=a+b
  s=s.replace('data-en="Find legal expertise, &lt;em&gt;closer to you.&lt;/em&gt;"','data-en="Find legal expertise, closer to you."')
 p.write_text(s,encoding='utf-8')
# feedback enhancement to article discovery: live category/search filters
p=root/'contents.html';s=p.read_text(encoding='utf-8')
old='<div class="story-grid"><a class="story-card"'
new='''<div class="content-tools"><label for="contentQuery">검색 <input id="contentQuery" type="search" placeholder="글·영상·주제 검색"></label><div class="content-filter" role="group" aria-label="콘텐츠 유형"><button type="button" class="on" data-content-type="all">전체</button><button type="button" data-content-type="blog">블로그</button><button type="button" data-content-type="video">영상</button></div><span id="contentCount" aria-live="polite"></span></div><div class="story-grid"><a class="story-card"'''
assert old in s
s=s.replace(old,new,1)
# label content cards
s=s.replace('<div class="story-grid"><a class="story-card" href="article-business.html"','<div class="story-grid"><a class="story-card" data-feed-kind="blog" href="article-business.html"',1)
s=s.replace('<a class="story-card" href="article-lease.html"','<a class="story-card" data-feed-kind="blog" href="article-lease.html"',1)
s=s.replace('<a class="story-card" href="video-guide.html"','<a class="story-card" data-feed-kind="video" href="video-guide.html"',1)
s=s.replace('</div><div class="promo-band">','</div><p class="empty" id="contentEmpty" hidden>일치하는 글이나 영상이 없습니다.</p><div class="promo-band">')
p.write_text(s,encoding='utf-8')
# CSS
p=assets/'style.css';s=p.read_text(encoding='utf-8');s+='''\n.content-tools{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin:20px 0 24px}.content-tools label{font-weight:700;font-size:13px}.content-tools input{margin-left:10px;border:1px solid #d8dbdf;border-radius:8px;padding:10px;width:min(330px,72vw)}.content-filter{display:flex;gap:6px}.content-filter button{border:1px solid #d8dcdf;background:white;border-radius:25px;padding:8px 15px;font-size:12px;color:#647386}.content-filter button.on{background:var(--navy);color:white;border-color:var(--navy)}#contentCount{font-size:12px;color:#9a7b52}.story-card[hidden],.lawyer-card[hidden]{display:none!important}@media(max-width:660px){.content-tools{align-items:flex-start;flex-direction:column}}\n''';p.write_text(s,encoding='utf-8')
# JS content search filter integrated patterns from Linkr FeedNlSearch (not copying source)
p=assets/'app.js';s=p.read_text(encoding='utf-8');marker="const builder=$('#builderForm');"
search="""const contentQuery=$('#contentQuery');let activeKind='all';function filterContent(){const q=(contentQuery?.value||'').trim().toLowerCase();let n=0;$$('[data-feed-kind]').forEach(card=>{const ok=(activeKind==='all'||card.dataset.feedKind===activeKind)&&(!q||card.textContent.toLowerCase().includes(q));card.hidden=!ok;if(ok)n++;});if($('#contentCount'))$('#contentCount').textContent=n+'건';if($('#contentEmpty'))$('#contentEmpty').hidden=n>0;}contentQuery?.addEventListener('input',filterContent);$$('[data-content-type]').forEach(b=>b.addEventListener('click',()=>{activeKind=b.dataset.contentType;$$('[data-content-type]').forEach(v=>v.classList.toggle('on',v===b));filterContent();}));filterContent();
"""
assert marker in s;s=s.replace(marker,search+marker,1);p.write_text(s,encoding='utf-8')
# update image descriptions to avoid fake credentials
r=root/'DESIGN_QA.md';r.write_text(r.read_text(encoding='utf-8')+'\n## 2차 개선 결과\n- 서로 다른 생성 이미지로 가상 인물 프로필 중복 완화\n- 콘텐츠 분야별 검색/분류 필터 추가\n- 데스크톱/모바일 대표 상세페이지 캡처 및 JS 동작 재검증\n- 한국어·영어 메뉴와 Google Translate 선택 방식 구분\n',encoding='utf-8')
print('refined')
