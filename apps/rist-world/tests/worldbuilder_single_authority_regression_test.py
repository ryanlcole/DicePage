from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'wwwroot' / 'index.html'
KEYBOARD = ROOT / 'wwwroot' / 'worldbuilder-keyboard-authority-v2.js'
LIFECYCLE = ROOT / 'wwwroot' / 'worldbuilder-lifecycle-authority-v2.js'
RELOCATION = ROOT / 'wwwroot' / 'worldbuilder-mode-keyboard-relocation.js'
SHELL = ROOT / 'Components' / 'PublicAlphaShell.razor'


def test_worldbuilder_loads_only_consolidated_keyboard_and_lifecycle_authorities():
    html = INDEX.read_text(encoding='utf-8')
    assert 'worldbuilder-keyboard-authority-v2.js' in html
    assert 'worldbuilder-lifecycle-authority-v2.js' in html
    assert 'worldbuilder-shaelvien-keyboard-skin.js' not in html
    assert 'worldbuilder-keyboard-runtime-authority.js' not in html
    assert 'worldbuilder-final-keyboard-authority.js' not in html
    assert 'worldbuilder-keyboard-visual-accessibility.js' not in html
    assert 'worldbuilder-immersive-polish.js' not in html


def test_relocation_never_reinjects_retired_keyboard_runtime():
    source = RELOCATION.read_text(encoding='utf-8')
    assert 'worldbuilder-keyboard-runtime-authority.js' not in source
    assert 'ensureRuntime' not in source
    assert 'RistWorldBuilderKeyboardRuntime' not in source
    assert 'RistWorldBuilderKeyboardAuthority?.refresh' in source


def test_keyboard_authority_does_not_synthesize_touch_clicks():
    source = KEYBOARD.read_text(encoding='utf-8')
    assert "addEventListener('touchend'" not in source
    assert 'state.button.click()' not in source
    assert "addEventListener('pointerdown'" in source
    assert 'worldbuilder-keyboard-authority-v2' in source


def test_tiles_keyboard_does_not_reuse_unrelated_artwork():
    source = KEYBOARD.read_text(encoding='utf-8')
    tiles_map = source.split("tiles:{", 1)[1].split("},\n  sprites", 1)[0]
    assert "'Library':'library'" in tiles_map
    assert "'Tile Size':'tile_size'" in tiles_map
    assert "'Grid':'tile_size'" not in tiles_map
    assert "'Target':'move'" not in tiles_map
    assert "'Undo':'rotate'" not in tiles_map


def test_generic_keys_use_css_blank_once_instead_of_stacking_blank_art():
    source = KEYBOARD.read_text(encoding='utf-8')
    assert 'if(!id)' in source
    assert 'existing?.remove()' in source
    assert "setKeyClasses(button,false)" in source
    assert "img.src=id?" not in source
    assert "img.src=BLANK" not in source


def test_keyboard_art_preserves_authored_aspect_ratio():
    source = KEYBOARD.read_text(encoding='utf-8')
    assert 'object-fit:contain!important' in source
    assert 'width:96%!important' in source
    assert 'height:96%!important' in source


def test_worldbuilder_lifecycle_claims_remaining_viewport_and_widens_control_borders():
    source = LIFECYCLE.read_text(encoding='utf-8')
    assert '.alpha-world-stage.worldbuilder-stage' in source
    assert 'inset:20px 0 0 0!important' in source
    assert '.worldbuilder-studio>.studio-workbench{display:none!important}' in source
    assert 'inset:0 0 var(--wb-device-keyboard-h) 0!important' in source
    assert 'border:2px solid rgba(197,145,62,.94)!important' in source
    assert 'border-color:#38bfff!important' in source


def test_ios_worldbuilder_foreground_uses_persisted_active_marker_and_guarded_reload():
    source = LIFECYCLE.read_text(encoding='utf-8')
    assert "document.addEventListener('visibilitychange'" in source
    assert "window.addEventListener('pagehide',markBackground" in source
    assert 'wasActiveWorldbuilder()' in source
    assert "localStorage.setItem(WORKSPACE_KEY,'world')" in source
    assert 'location.reload()' in source
    assert 'guardedReload' in source
    assert '.site-copyright-notice' in source
    assert "document.body?.classList.toggle('wb-immersive-worldbuilder',active)" in source


def test_shell_returns_to_hub_after_authenticated_world_choice():
    source = SHELL.read_text(encoding='utf-8')
    assert '_workspaceOpen=false' in source
    assert '_worldGateOpen=false' in source
    assert 'await PersistWorkspaceAsync("hub")' in source
    assert 'RestorableWorkspaces.Contains(storedWorkspace)' not in source
    assert 'ApplyWorkspace(storedWorkspace)' not in source
