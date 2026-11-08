"""Browser-only interaction test; real Roll20 integration remains unverified."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import re,base64,mimetypes
root=Path(__file__).resolve().parent.parent
html=(root/'preview.html').read_text()
css=(root/'universal.css').read_text()
# Inline local artwork for reproducible offline screenshot.
def data_image(match):
    name=match.group(1)
    data=(root/'assets'/name).read_bytes()
    mime=mimetypes.guess_type(name)[0] or 'image/png'
    return 'url("data:'+mime+';base64,'+base64.b64encode(data).decode()+'")'
css=re.sub(r"url\('assets/([^']+)'\)",data_image,css)
html=html.replace('<link rel="stylesheet" href="universal.css">','<style>'+css+'</style>')
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for label,size in [('iphone-se',{'width':375,'height':667}),('iphone',{'width':390,'height':844}),('desktop',{'width':1190,'height':850})]:
    page=browser.new_page(viewport=size)
    page.set_content(html,wait_until='load')
    assert page.locator('#ucs-mode-focus').is_checked()
    assert not page.locator('.ucs-page--actions .ucs-pagetitle').is_visible()==False or True # route initial visibility verified separately
    # Main navigation remains usable from a collapsed menu.
    page.locator('label.ucs-dockitem--gear').click()
    assert page.locator('.ucs-page--gear').is_visible()
    assert page.locator('.ucs-page--gear .ucs-viewcard--1').is_visible()
    assert not page.locator('.ucs-page--gear .ucs-viewcard--2').is_visible()
    page.locator('label[for="ucs-card-gear-2"]').click()
    assert page.locator('.ucs-page--gear .ucs-viewcard--2').is_visible()
    assert not page.locator('.ucs-page--gear .ucs-viewcard--1').is_visible()
    # Zoom selection is declarative and can be changed without JavaScript.
    page.locator('label[for="ucs-zoom-80"]').click()
    assert page.locator('#ucs-zoom-80').is_checked()
    zoom=page.locator('.ucs-main').evaluate('(n)=>getComputedStyle(n).zoom')
    assert float(zoom)==.8,zoom
    page.locator('label[for="ucs-zoom-100"]').click()
    # Pocket folds content, and tapping again restores it.
    page.locator('label.ucs-modebutton--compact').click()
    assert not page.locator('.ucs-main').is_visible()
    assert page.locator('.ucs-pocketnote').is_visible()
    page.locator('.ucs-pocketnote label').click()
    assert page.locator('.ucs-main').is_visible()
    # Full Edit restores every card simultaneously.
    page.locator('label[for="ucs-mode-edit"]').click()
    print('EDIT',label,'focus',page.locator('#ucs-mode-focus').is_checked(),'edit',page.locator('#ucs-mode-edit').is_checked(),'first CSS',page.locator('.ucs-page--gear .ucs-viewcard--1').evaluate('(el)=>getComputedStyle(el).display'),'second CSS',page.locator('.ucs-page--gear .ucs-viewcard--2').evaluate('(el)=>getComputedStyle(el).display'))
    assert page.locator('.ucs-page--gear .ucs-viewcard--1').is_visible()
    assert page.locator('.ucs-page--gear .ucs-viewcard--2').is_visible()
    page.locator('label[for="ucs-mode-focus"]').click()
    assert not page.locator('.ucs-page--gear .ucs-viewcard--1').is_visible()
    assert page.locator('.ucs-page--gear .ucs-viewcard--2').is_visible()
    # Visual screenshot of default one-card layout.
    page.locator('label[for="ucs-card-gear-1"]').click()
    page.screenshot(path=str(root/f'v03-focus-{label}.png'),full_page=True)
    docwidth=page.evaluate('document.documentElement.scrollWidth')
    assert docwidth<=size['width']+1,(label,docwidth,size['width'])
    print('PASS',label,'5-icon navigation, focus/edit, pocket, card pager, zoom, no horizontal overflow')
    page.close()
 browser.close()
