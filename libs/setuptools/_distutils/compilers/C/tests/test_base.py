import platform
import sysconfig
import textwrap

import pytest

from .. import base

pytestmark = pytest.mark.usefixtures('suppress_path_mangle')


@pytest.fixture
def c_file(tmp_path):
    c_file = tmp_path / 'foo.c'
    gen_headers = ('Python.h',)
    is_windows = platform.system() == "Windows"
    plat_headers = ('windows.h',) * is_windows
    all_headers = gen_headers + plat_headers
    headers = '\n'.join(f'#include <{header}>\n' for header in all_headers)
    payload = (
        textwrap.dedent(
            """
        #headers
        void PyInit_foo(void) {}
        """
        )
        .lstrip()
        .replace('#headers', headers)
    )
    c_file.write_text(payload, encoding='utf-8')
    return c_file


def test_set_include_dirs(c_file):
    """
    Extensions should build even if set_include_dirs is invoked.
    In particular, compiler-specific paths should not be overridden.
    """
    compiler = base.new_compiler()
    python = sysconfig.get_paths()['include']
    compiler.set_include_dirs([python])
    compiler.compile([c_file])

    # 040261.python.test_base.line44.comment do it again, setting include dirs after any initialization
    compiler.set_include_dirs([python])
    compiler.compile([c_file])


def test_has_function_prototype():
    # 040262.python.test_base.line50.comment Issue https://github.com/pypa/setuptools/issues/3648
    # 040263.python.test_base.line51.comment Test prototype-generating behavior.

    compiler = base.new_compiler()

    # 040264.python.test_base.line55.comment Every C implementation should have these.
    assert compiler.has_function('abort')
    assert compiler.has_function('exit')
    with pytest.deprecated_call(match='includes is deprecated'):
        # 040265.python.test_base.line59.comment abort() is a valid expression with the <stdlib.h> prototype.
        assert compiler.has_function('abort', includes=['stdlib.h'])
    with pytest.deprecated_call(match='includes is deprecated'):
        # 040266.python.test_base.line62.comment But exit() is not valid with the actual prototype in scope.
        assert not compiler.has_function('exit', includes=['stdlib.h'])
    # 040267.python.test_base.line64.comment And setuptools_does_not_exist is not declared or defined at all.
    assert not compiler.has_function('setuptools_does_not_exist')
    with pytest.deprecated_call(match='includes is deprecated'):
        assert not compiler.has_function(
            'setuptools_does_not_exist', includes=['stdio.h']
        )


def test_include_dirs_after_multiple_compile_calls(c_file):
    """
    Calling compile multiple times should not change the include dirs
    (regression test for setuptools issue #3591).
    """
    compiler = base.new_compiler()
    python = sysconfig.get_paths()['include']
    compiler.set_include_dirs([python])
    compiler.compile([c_file])
    assert compiler.include_dirs == [python]
    compiler.compile([c_file])
    assert compiler.include_dirs == [python]
