"""Tests for distutils.command.install_headers."""

import os
from distutils.command.install_headers import install_headers
from distutils.tests import support

import pytest


@pytest.mark.usefixtures('save_env')
class TestInstallHeaders(
    support.TempdirManager,
):
    def test_simple_run(self):
        # 041139.python.test_install_headers.line15.comment we have two headers
        header_list = self.mkdtemp()
        header1 = os.path.join(header_list, 'header1')
        header2 = os.path.join(header_list, 'header2')
        self.write_file(header1)
        self.write_file(header2)
        headers = [header1, header2]

        pkg_dir, dist = self.create_dist(headers=headers)
        cmd = install_headers(dist)
        assert cmd.get_inputs() == headers

        # 041140.python.test_install_headers.line27.comment let's run the command
        cmd.install_dir = os.path.join(pkg_dir, 'inst')
        cmd.ensure_finalized()
        cmd.run()

        # 041141.python.test_install_headers.line32.comment let's check the results
        assert len(cmd.get_outputs()) == 2
