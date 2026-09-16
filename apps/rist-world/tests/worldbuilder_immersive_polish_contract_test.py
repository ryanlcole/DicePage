from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_immersive_polish_preserves_art_aspect_and_is_loaded_last():
    js = (ROOT / 'wwwroot' / 'worldbuilder-immersive-polish.js').read_text(encoding='utf-8')
    html = (ROOT / 'wwwroot' / 'index.html').read_text(encoding='utf-8')

    assert 'object-fit:contain' in js
    assert 'wb-final-key-art' in js
    assert 'wb-final-dpad-art' in js

    polish = html.index('worldbuilder-immersive-polish.js')
    visual_access = html.index('worldbuilder-keyboard-visual-accessibility.js')
    assert visual_access < polish


def test_worldbuilder_hides_only_immersive_footer_notice():
    js = (ROOT / 'wwwroot' / 'worldbuilder-immersive-polish.js').read_text(encoding='utf-8')

    assert 'wb-immersive-worldbuilder' in js
    assert '.site-copyright-notice' in js
    assert "classList.toggle('wb-immersive-worldbuilder',active)" in js


def test_ios_resume_has_recompose_and_guarded_recovery():
    js = (ROOT / 'wwwroot' / 'worldbuilder-immersive-polish.js').read_text(encoding='utf-8')

    assert "addEventListener('pageshow'" in js
    assert "addEventListener('pagehide'" in js
    assert "addEventListener('visibilitychange'" in js
    assert "mount.style.setProperty('display','none','important')" in js
    assert 'guardedReload' in js
    assert 'worldbuilderWasActive' in js
    assert 'location.reload()' in js
