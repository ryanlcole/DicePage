"""Tests for distutils.file_util."""

import errno
import os
import unittest.mock as mock
from distutils.errors import DistutilsFileError
from distutils.file_util import copy_file, move_file

import jaraco.path
import pytest


@pytest.fixture(autouse=True)
def stuff(request, tmp_path):
    self = request.instance
    self.source = tmp_path / 'f1'
    self.target = tmp_path / 'f2'
    self.target_dir = tmp_path / 'd1'


class TestFileUtil:
    def test_move_file_verbosity(self, caplog):
        jaraco.path.build({self.source: 'some content'})

        move_file(self.source, self.target, verbose=False)
        assert not caplog.messages

        # 041072.python.test_file_util.line28.comment back to original state
        move_file(self.target, self.source, verbose=False)

        move_file(self.source, self.target, verbose=True)
        wanted = [f'moving {self.source} -> {self.target}']
        assert caplog.messages == wanted

        # 041073.python.test_file_util.line35.comment back to original state
        move_file(self.target, self.source, verbose=False)

        caplog.clear()
        # 041074.python.test_file_util.line39.comment now the target is a dir
        os.mkdir(self.target_dir)
        move_file(self.source, self.target_dir, verbose=True)
        wanted = [f'moving {self.source} -> {self.target_dir}']
        assert caplog.messages == wanted

    def test_move_file_exception_unpacking_rename(self):
        # 041075.python.test_file_util.line46.comment see issue 22182
        with (
            mock.patch("os.rename", side_effect=OSError("wrong", 1)),
            pytest.raises(DistutilsFileError),
        ):
            jaraco.path.build({self.source: 'spam eggs'})
            move_file(self.source, self.target, verbose=False)

    def test_move_file_exception_unpacking_unlink(self):
        # 041076.python.test_file_util.line55.comment see issue 22182
        with (
            mock.patch("os.rename", side_effect=OSError(errno.EXDEV, "wrong")),
            mock.patch("os.unlink", side_effect=OSError("wrong", 1)),
            pytest.raises(DistutilsFileError),
        ):
            jaraco.path.build({self.source: 'spam eggs'})
            move_file(self.source, self.target, verbose=False)

    def test_copy_file_hard_link(self):
        jaraco.path.build({self.source: 'some content'})
        # 041077.python.test_file_util.line66.comment Check first that copy_file() will not fall back on copying the file
        # 041078.python.test_file_util.line67.comment instead of creating the hard link.
        try:
            os.link(self.source, self.target)
        except OSError as e:
            self.skipTest(f'os.link: {e}')
        else:
            self.target.unlink()
        st = os.stat(self.source)
        copy_file(self.source, self.target, link='hard')
        st2 = os.stat(self.source)
        st3 = os.stat(self.target)
        assert os.path.samestat(st, st2), (st, st2)
        assert os.path.samestat(st2, st3), (st2, st3)
        assert self.source.read_text(encoding='utf-8') == 'some content'

    def test_copy_file_hard_link_failure(self):
        # 041079.python.test_file_util.line83.comment If hard linking fails, copy_file() falls back on copying file
        # 041080.python.test_file_util.line84.comment (some special filesystems don't support hard linking even under
        # 041081.python.test_file_util.line85.comment Unix, see issue #8876).
        jaraco.path.build({self.source: 'some content'})
        st = os.stat(self.source)
        with mock.patch("os.link", side_effect=OSError(0, "linking unsupported")):
            copy_file(self.source, self.target, link='hard')
        st2 = os.stat(self.source)
        st3 = os.stat(self.target)
        assert os.path.samestat(st, st2), (st, st2)
        assert not os.path.samestat(st2, st3), (st2, st3)
        for fn in (self.source, self.target):
            assert fn.read_text(encoding='utf-8') == 'some content'
