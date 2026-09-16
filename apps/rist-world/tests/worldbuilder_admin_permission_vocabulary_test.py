from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_permission_vocabulary_matches_recursive_authority():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    authority = (ROOT / 'RecursiveAuthority.cs').read_text(encoding='utf-8')
    for grant in ('View', 'Edit', 'Public', 'Deny'):
        assert grant in js
        assert grant in authority
    assert 'StopsInheritance' in authority
    assert 'stopsInheritance' in js
