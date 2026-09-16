"""Tests for distutils.command.bdist."""

from distutils.command.bdist import bdist
from distutils.tests import support


class TestBuild(support.TempdirManager):
    def test_formats(self):
        # 040843.python.test_bdist.line9.comment let's create a command and make sure
        # 040844.python.test_bdist.line10.comment we can set the format
        dist = self.create_dist()[1]
        cmd = bdist(dist)
        cmd.formats = ['gztar']
        cmd.ensure_finalized()
        assert cmd.formats == ['gztar']

        # 040845.python.test_bdist.line17.comment what formats does bdist offer?
        formats = [
            'bztar',
            'gztar',
            'rpm',
            'tar',
            'xztar',
            'zip',
            'ztar',
        ]
        found = sorted(cmd.format_commands)
        assert found == formats

    def test_skip_build(self):
        # 040846.python.test_bdist.line31.comment bug #10946: bdist --skip-build should trickle down to subcommands
        dist = self.create_dist()[1]
        cmd = bdist(dist)
        cmd.skip_build = True
        cmd.ensure_finalized()
        dist.command_obj['bdist'] = cmd

        names = [
            'bdist_dumb',
        ]  # bdist_rpm does not support --skip-build

        for name in names:
            subcmd = cmd.get_finalized_command(name)
            if getattr(subcmd, '_unsupported', False):
                # 040848.python.test_bdist.line45.comment command is not supported on this build
                continue
            assert subcmd.skip_build, f'{name} should take --skip-build from bdist'
