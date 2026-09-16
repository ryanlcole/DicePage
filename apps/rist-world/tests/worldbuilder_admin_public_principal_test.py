from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_permission_uses_everyone_principal_only_at_authority_handoff():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    authority = (ROOT / 'RecursiveAuthority.cs').read_text(encoding='utf-8')
    assert 'EveryonePrincipal = "*"' in authority
    assert "state.grant==='Public'?'*':principal" in js
