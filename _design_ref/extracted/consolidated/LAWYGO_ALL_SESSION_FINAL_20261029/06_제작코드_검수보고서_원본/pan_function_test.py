from playwright.sync_api import sync_playwright
from pathlib import Path
exec(open('/mnt/data/pan_render_qa_inline.py').read().split('results=[]')[0])
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 def setup(name,mobile=False):
  page=b.new_page(viewport={'width':390 if mobile else 1365,'height':850});page.set_content(inline(root/name),wait_until='domcontentloaded');page.add_script_tag(content=js);return page
 out={}
 pg=setup('lawyers.html');out['lawyers_initial']=pg.locator('.lawyer-card:visible').count();pg.fill('#lawyer-q','김서현');out['lawyers_name_filter']=pg.locator('.lawyer-card:visible').count();pg.fill('#lawyer-q','');pg.locator('[data-filter-category="가사·상속"]').click();out['lawyers_category_filter']=pg.locator('.lawyer-card:visible').count();pg.close()
 pg=setup('blog.html');out['blog_initial']=pg.locator('[data-content-category]:visible').count();pg.locator('[data-content-filter="부동산"]').click();out['blog_filter']=pg.locator('[data-content-category]:visible').count();pg.close()
 pg=setup('index.html',True);pg.click('#menu-toggle');out['mobile_open']=pg.locator('#mobile-nav').get_attribute('class');pg.click('.lang');out['lang_after_click']=pg.locator('html').get_attribute('lang');out['lang_button']=pg.locator('.lang').inner_text();pg.close()
 pg=setup('join.html');pg.click('[data-open-contact]');out['contact_modal']=pg.locator('#contact-modal').get_attribute('class');pg.click('[data-close-modal]');out['contact_close']=pg.locator('#contact-modal').get_attribute('class');pg.close()
 b.close()
 print(out)
 (root/'docs'/'INTERACTION_QA.txt').write_text('\n'.join(f'{k}: {v}' for k,v in out.items()),encoding='utf-8')
