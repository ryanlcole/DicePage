from setuptools import _scripts


class TestWindowsScriptWriter:
    def test_header(self):
        hdr = _scripts.WindowsScriptWriter.get_header('')
        assert hdr.startswith('#!')
        assert hdr.endswith('\n')
        hdr = hdr.lstrip('#!')
        hdr = hdr.rstrip('\n')
        # 045513.python.test_scripts.line11.comment header should not start with an escaped quote
        assert not hdr.startswith('\\"')
