from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for name,viewport in [('desktop',{'width':1250,'height':900}),('mobile',{'width':390,'height':844})]:
        page=browser.new_page(viewport=viewport,device_scale_factor=1)
        html=(root/'preview.html').read_text().replace('<link rel="stylesheet" href="universal.css">','<style>'+ (root/'universal.css').read_text()+'</style>')
        page.set_content(html,wait_until='load')
        assert page.locator('.ucs-page--actions').is_visible(), 'Actions tab missing on initial load'
        # the route selectors must work without browser JavaScript; click a CSS label.
        if name=='mobile':
            page.locator('.ucs-navdetails').evaluate('(el) => el.open = true')
        page.locator('label.ucs-navitem--dicebag').click()
        assert page.locator('.ucs-page--dicebag').is_visible(), 'Dice Bag not shown after tab click'
        assert not page.locator('.ucs-page--actions').is_visible(), 'Previous tab not hidden'
        assert page.locator('fieldset.repeating_dicebag').count()==1
        w=page.evaluate('document.documentElement.scrollWidth')
        print(name,'page width',viewport['width'],'content width',w)
        assert w<=viewport['width']+1, f'Unexpected horizontal scroll in {name}'
        page.screenshot(path=str(root/f'preview-{name}.png'),full_page=True)
        # test navigation to Bio as well
        page.locator('label.ucs-navitem--bio').click()
        assert page.locator('.ucs-page--bio').is_visible()
        assert not page.locator('.ucs-page--dicebag').is_visible()
        print('PASS',name,'tab navigation and no horizontal scrolling')
        page.close()
    browser.close()
