"""Tests for distutils.command.check."""

import os
import textwrap
from distutils.command.check import check
from distutils.errors import DistutilsSetupError
from distutils.tests import support

import pytest

try:
    import pygments
except ImportError:
    pygments = None


HERE = os.path.dirname(__file__)


@support.combine_markers
class TestCheck(support.TempdirManager):
    def _run(self, metadata=None, cwd=None, **options):
        if metadata is None:
            metadata = {}
        if cwd is not None:
            old_dir = os.getcwd()
            os.chdir(cwd)
        pkg_info, dist = self.create_dist(**metadata)
        cmd = check(dist)
        cmd.initialize_options()
        for name, value in options.items():
            setattr(cmd, name, value)
        cmd.ensure_finalized()
        cmd.run()
        if cwd is not None:
            os.chdir(old_dir)
        return cmd

    def test_check_metadata(self):
        # 040991.python.test_check.line40.comment let's run the command with no metadata at all
        # 040992.python.test_check.line41.comment by default, check is checking the metadata
        # 040993.python.test_check.line42.comment should have some warnings
        cmd = self._run()
        assert cmd._warnings == 1

        # 040994.python.test_check.line46.comment now let's add the required fields
        # 040995.python.test_check.line47.comment and run it again, to make sure we don't get
        # 040996.python.test_check.line48.comment any warning anymore
        metadata = {
            'url': 'xxx',
            'author': 'xxx',
            'author_email': 'xxx',
            'name': 'xxx',
            'version': 'xxx',
        }
        cmd = self._run(metadata)
        assert cmd._warnings == 0

        # 040997.python.test_check.line59.comment now with the strict mode, we should
        # 040998.python.test_check.line60.comment get an error if there are missing metadata
        with pytest.raises(DistutilsSetupError):
            self._run({}, **{'strict': 1})

        # 040999.python.test_check.line64.comment and of course, no error when all metadata are present
        cmd = self._run(metadata, strict=True)
        assert cmd._warnings == 0

        # 041000.python.test_check.line68.comment now a test with non-ASCII characters
        metadata = {
            'url': 'xxx',
            'author': '\u00c9ric',
            'author_email': 'xxx',
            'name': 'xxx',
            'version': 'xxx',
            'description': 'Something about esszet \u00df',
            'long_description': 'More things about esszet \u00df',
        }
        cmd = self._run(metadata)
        assert cmd._warnings == 0

    def test_check_author_maintainer(self):
        for kind in ("author", "maintainer"):
            # 041001.python.test_check.line83.comment ensure no warning when author_email or maintainer_email is given
            # 041002.python.test_check.line84.comment (the spec allows these fields to take the form "Name <email>")
            metadata = {
                'url': 'xxx',
                kind + '_email': 'Name <name@email.com>',
                'name': 'xxx',
                'version': 'xxx',
            }
            cmd = self._run(metadata)
            assert cmd._warnings == 0

            # 041003.python.test_check.line94.comment the check should not warn if only email is given
            metadata[kind + '_email'] = 'name@email.com'
            cmd = self._run(metadata)
            assert cmd._warnings == 0

            # 041004.python.test_check.line99.comment the check should not warn if only the name is given
            metadata[kind] = "Name"
            del metadata[kind + '_email']
            cmd = self._run(metadata)
            assert cmd._warnings == 0

    def test_check_document(self):
        pytest.importorskip('docutils')
        pkg_info, dist = self.create_dist()
        cmd = check(dist)

        # 041005.python.test_check.line110.comment let's see if it detects broken rest
        broken_rest = 'title\n===\n\ntest'
        msgs = cmd._check_rst_data(broken_rest)
        assert len(msgs) == 1

        # 041006.python.test_check.line115.comment and non-broken rest
        rest = 'title\n=====\n\ntest'
        msgs = cmd._check_rst_data(rest)
        assert len(msgs) == 0

    def test_check_restructuredtext(self):
        pytest.importorskip('docutils')
        # 041007.python.test_check.line122.comment let's see if it detects broken rest in long_description
        broken_rest = 'title\n===\n\ntest'
        pkg_info, dist = self.create_dist(long_description=broken_rest)
        cmd = check(dist)
        cmd.check_restructuredtext()
        assert cmd._warnings == 1

        # 041008.python.test_check.line129.comment let's see if we have an error with strict=True
        metadata = {
            'url': 'xxx',
            'author': 'xxx',
            'author_email': 'xxx',
            'name': 'xxx',
            'version': 'xxx',
            'long_description': broken_rest,
        }
        with pytest.raises(DistutilsSetupError):
            self._run(metadata, **{'strict': 1, 'restructuredtext': 1})

        # 041009.python.test_check.line141.comment and non-broken rest, including a non-ASCII character to test #12114
        metadata['long_description'] = 'title\n=====\n\ntest \u00df'
        cmd = self._run(metadata, strict=True, restructuredtext=True)
        assert cmd._warnings == 0

        # 041010.python.test_check.line146.comment check that includes work to test #31292
        metadata['long_description'] = 'title\n=====\n\n.. include:: includetest.rst'
        cmd = self._run(metadata, cwd=HERE, strict=True, restructuredtext=True)
        assert cmd._warnings == 0

    def test_check_restructuredtext_with_syntax_highlight(self):
        pytest.importorskip('docutils')
        # 041011.python.test_check.line153.comment Don't fail if there is a `code` or `code-block` directive

        example_rst_docs = [
            textwrap.dedent(
                """\
            Here's some code:

            .. code:: python

                def foo():
                    pass
            """
            ),
            textwrap.dedent(
                """\
            Here's some code:

            .. code-block:: python

                def foo():
                    pass
            """
            ),
        ]

        for rest_with_code in example_rst_docs:
            pkg_info, dist = self.create_dist(long_description=rest_with_code)
            cmd = check(dist)
            cmd.check_restructuredtext()
            msgs = cmd._check_rst_data(rest_with_code)
            if pygments is not None:
                assert len(msgs) == 0
            else:
                assert len(msgs) == 1
                assert (
                    str(msgs[0][1])
                    == 'Cannot analyze code. Pygments package not found.'
                )

    def test_check_all(self):
        with pytest.raises(DistutilsSetupError):
            self._run({}, **{'strict': 1, 'restructuredtext': 1})
