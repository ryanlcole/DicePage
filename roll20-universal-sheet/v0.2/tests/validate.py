"""Static audit. Actual Roll20 requires GM integration verification."""
import re, sys
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parent.parent
html=(root/'universal.html').read_text()
css=(root/'universal.css').read_text()
worker=(root/'worker.js').read_text()
soup=BeautifulSoup(html,'html.parser')
errors=[]
def check(cond,msg):
 if not cond: errors.append(msg)
 check_count=len(errors)
 return cond
assert not soup.find(['html','body','head','iframe','link']), 'Non-Roll20 root tags present'
check(len(soup.select('section.ucs-page'))==16,'Not all 16 sections exist')
keys=[x['value'] for x in soup.select('input.ucs-route-input')]
check(len(keys)==16 and len(set(keys))==16,'Bad tab radios')
for key in keys:
 check(f'.ucs-page--{key}' in css and f'.ucs-navitem--{key}' in css, f'Missing CSS route {key}')
reps=[x['class'][0] for x in soup.select('fieldset')]
check(all(re.fullmatch(r'repeating_[a-z0-9]+',x) for x in reps),'Invalid repeating names')
check(len(reps)==len(set(reps)),'Repeated fieldset names')
check('repeating_dicebag' in reps,'Missing repeating dice bag')
for t in soup.find_all(['input','textarea','select']):
 check(t.get('name','').startswith('attr_'),f'Missing attr_ on {t}')
for b in soup.find_all('button'):
 check(b.get('type')=='roll' and b.get('name','').startswith('roll_') and b.get('value'),f'Bad roll button {b}')
check(len(soup.select('button[type=roll]'))>=8,'Expected roll buttons in action sections')
check('type="text/worker"' in html,'Missing embedded worker')
check(worker in html,'Embedded worker not equal to source worker')
check('onclick=' not in html.lower(),'Inline DOM scripting not supported')
check(not re.search(r'<script(?! type="text/worker")',html),'Unexpected script tag')
check('legacy": false' in (root/'sheet.json').read_text(),'Not CSE metadata')
check('name="attr_recipe_command"' in html,'No generated dice macro field')
check('value="@{recipe_command}"' in html,'No working dice macro roll binding')
check('name="attr_display_name"' in html,'No persistent alias field')
if errors:
 print('FAILED',len(errors),'checks:')
 for x in errors[:30]:print(' -',x)
 sys.exit(1)
print('PASS: 16 CSS-routed tabs,',len(reps),'valid repeating collections,',len(soup.select('button[type=roll]')),'native roll buttons, valid Roll20 input naming and embedded worker')
