from pathlib import Path
from playwright.sync_api import sync_playwright
import mimetypes, re, base64
root=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files'])
 for kind,vp in [('mobile',{'width':390,'height':844}),('desktop',{'width':1200,'height':900})]:
  page=browser.new_page(viewport=vp,device_scale_factor=1)
  html=(root/'preview.html').read_text()
  css=(root/'universal.css').read_text()
  def inline_image(m):
   rel=m.group(1)
   f=root/rel
   mime=mimetypes.guess_type(str(f))[0] or 'image/png'
   return 'url("data:'+mime+';base64,'+base64.b64encode(f.read_bytes()).decode()+'")'
  css=re.sub(r'url\(\'((?:assets/)[^\']+)\'\)',inline_image,css)
  html=html.replace('<link rel="stylesheet" href="universal.css">','<style>'+css+'</style>')
  page.set_content(html,wait_until='load')
  assert page.locator('.ucs-bottomdock').count()==1
  assert page.locator('.ucs-dockitem').count()==5
  for item in page.locator('.ucs-dockart').all():
   url=item.evaluate('(el)=>getComputedStyle(el).backgroundImage');assert 'data:image' in url, url[:80]
  routes=['bio','base','spellbook','gear','knowledge']
  for route in routes:
   page.locator('label.ucs-dockitem--'+route).click()
   assert page.locator('.ucs-page--'+route).is_visible(),route
   assert page.locator('.ucs-bottomdock').count()==1,route
   assert page.locator('.ucs-dockitem').count()==5,route
   if route=='base':
    pop=page.locator('.ucs-page--base details.ucs-inlinebag').first
    assert pop.count()==1
    pop.locator('summary.ucs-inlinebag-trigger').click()
    assert pop.locator('.ucs-inlinebag-popover').is_visible()
    assert pop.locator('[name="attr_skill_roll_bonus"]').count()==1
    assert pop.locator('[name="attr_skill_roll_dc"]').count()==1
   if route=='gear':
    # viewport screenshot of art-backed nav and contextual bag
    page.screenshot(path=str(root/f'v02-{kind}-gear-viewport.png'))
  # Check that the SAME dock exists across all secondary sections, not merely the five destination pages.
  for route in ['artwork','bio','classes','base','flavor','gear','loot','actions','effects','spellbook','dicebag','knowledge','profession','journal','player','custom']:
   page.locator('#ucs-tab-'+route).evaluate('(el)=>{el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))}')
   assert page.locator('.ucs-page--'+route).is_visible(), route
   assert page.locator('.ucs-bottomdock').count()==1
   assert page.locator('.ucs-dockitem').count()==5
  w=page.evaluate('document.documentElement.scrollWidth'); assert w<=vp['width']+1,(kind,w)
  print('PASS',kind,'all 5 routes use same nav; sheet bag details accessible; width',w)
  page.close()
 browser.close()
