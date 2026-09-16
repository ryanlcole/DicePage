from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_preview_draws_only_exposed_region_edges():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert 'selectedKeys' in js
    assert 'cellKey(col,row-1,n)' in js
    assert 'cellKey(col+1,row,n)' in js
    assert 'cellKey(col,row+1,n)' in js
    assert 'cellKey(col-1,row,n)' in js
    assert 'mark.style.borderTop=border' in js
    assert 'mark.style.borderRight=border' in js
    assert 'mark.style.borderBottom=border' in js
    assert 'mark.style.borderLeft=border' in js


def test_admin_preview_does_not_outline_every_cell_as_a_border():
    css = (ROOT / 'wwwroot' / 'css' / 'worldbuilder-admin-keyboard.css').read_text(encoding='utf-8')
    assert 'outline:0' in css
    assert 'outline:2px' not in css
    assert 'outline:4px' not in css
