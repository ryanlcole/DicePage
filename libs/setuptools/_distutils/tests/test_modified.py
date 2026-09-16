"""Tests for distutils._modified."""

import os
import types
from distutils._modified import newer, newer_group, newer_pairwise, newer_pairwise_group
from distutils.errors import DistutilsFileError
from distutils.tests import support

import pytest


class TestDepUtil(support.TempdirManager):
    def test_newer(self):
        tmpdir = self.mkdtemp()
        new_file = os.path.join(tmpdir, 'new')
        old_file = os.path.abspath(__file__)

        # 041150.python.test_modified.line18.comment Raise DistutilsFileError if 'new_file' does not exist.
        with pytest.raises(DistutilsFileError):
            newer(new_file, old_file)

        # 041151.python.test_modified.line22.comment Return true if 'new_file' exists and is more recently modified than
        # 041152.python.test_modified.line23.comment 'old_file', or if 'new_file' exists and 'old_file' doesn't.
        self.write_file(new_file)
        assert newer(new_file, 'I_dont_exist')
        assert newer(new_file, old_file)

        # 041153.python.test_modified.line28.comment Return false if both exist and 'old_file' is the same age or younger
        # 041154.python.test_modified.line29.comment than 'new_file'.
        assert not newer(old_file, new_file)

    def _setup_1234(self):
        tmpdir = self.mkdtemp()
        sources = os.path.join(tmpdir, 'sources')
        targets = os.path.join(tmpdir, 'targets')
        os.mkdir(sources)
        os.mkdir(targets)
        one = os.path.join(sources, 'one')
        two = os.path.join(sources, 'two')
        three = os.path.abspath(__file__)  # I am the old file
        four = os.path.join(targets, 'four')
        self.write_file(one)
        self.write_file(two)
        self.write_file(four)
        return one, two, three, four

    def test_newer_pairwise(self):
        one, two, three, four = self._setup_1234()

        assert newer_pairwise([one, two], [three, four]) == ([one], [three])

    def test_newer_pairwise_mismatch(self):
        one, two, three, four = self._setup_1234()

        with pytest.raises(ValueError):
            newer_pairwise([one], [three, four])

        with pytest.raises(ValueError):
            newer_pairwise([one, two], [three])

    def test_newer_pairwise_empty(self):
        assert newer_pairwise([], []) == ([], [])

    def test_newer_pairwise_fresh(self):
        one, two, three, four = self._setup_1234()

        assert newer_pairwise([one, three], [two, four]) == ([], [])

    def test_newer_group(self):
        tmpdir = self.mkdtemp()
        sources = os.path.join(tmpdir, 'sources')
        os.mkdir(sources)
        one = os.path.join(sources, 'one')
        two = os.path.join(sources, 'two')
        three = os.path.join(sources, 'three')
        old_file = os.path.abspath(__file__)

        # 041156.python.test_modified.line78.comment return true if 'old_file' is out-of-date with respect to any file
        # 041157.python.test_modified.line79.comment listed in 'sources'.
        self.write_file(one)
        self.write_file(two)
        self.write_file(three)
        assert newer_group([one, two, three], old_file)
        assert not newer_group([one, two, old_file], three)

        # 041158.python.test_modified.line86.comment missing handling
        os.remove(one)
        with pytest.raises(OSError):
            newer_group([one, two, old_file], three)

        assert not newer_group([one, two, old_file], three, missing='ignore')

        assert newer_group([one, two, old_file], three, missing='newer')


@pytest.fixture
def groups_target(tmp_path):
    """
    Set up some older sources, a target, and newer sources.

    Returns a simple namespace with these values.
    """
    filenames = ['older.c', 'older.h', 'target.o', 'newer.c', 'newer.h']
    paths = [tmp_path / name for name in filenames]

    for mtime, path in enumerate(paths):
        path.write_text('', encoding='utf-8')

        # 041159.python.test_modified.line109.comment make sure modification times are sequential
        os.utime(path, (mtime, mtime))

    return types.SimpleNamespace(older=paths[:2], target=paths[2], newer=paths[3:])


def test_newer_pairwise_group(groups_target):
    older = newer_pairwise_group([groups_target.older], [groups_target.target])
    newer = newer_pairwise_group([groups_target.newer], [groups_target.target])
    assert older == ([], [])
    assert newer == ([groups_target.newer], [groups_target.target])


def test_newer_group_no_sources_no_target(tmp_path):
    """
    Consider no sources and no target "newer".
    """
    assert newer_group([], str(tmp_path / 'does-not-exist'))
