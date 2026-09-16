"""distutils.command.build

Implements the Distutils 'build' command."""

from __future__ import annotations

import os
import sys
import sysconfig
from collections.abc import Callable
from typing import ClassVar

from ..ccompiler import show_compilers
from ..core import Command
from ..errors import DistutilsOptionError
from ..util import get_platform


class build(Command):
    description = "build everything needed to install"

    user_options = [
        ('build-base=', 'b', "base directory for build library"),
        ('build-purelib=', None, "build directory for platform-neutral distributions"),
        ('build-platlib=', None, "build directory for platform-specific distributions"),
        (
            'build-lib=',
            None,
            "build directory for all distribution (defaults to either build-purelib or build-platlib",
        ),
        ('build-scripts=', None, "build directory for scripts"),
        ('build-temp=', 't', "temporary build directory"),
        (
            'plat-name=',
            'p',
            f"platform name to build for, if supported [default: {get_platform()}]",
        ),
        ('compiler=', 'c', "specify the compiler type"),
        ('parallel=', 'j', "number of parallel build jobs"),
        ('debug', 'g', "compile extensions and libraries with debugging information"),
        ('force', 'f', "forcibly build everything (ignore file timestamps)"),
        ('executable=', 'e', "specify final destination interpreter path (build.py)"),
    ]

    boolean_options: ClassVar[list[str]] = ['debug', 'force']

    help_options: ClassVar[list[tuple[str, str | None, str, Callable[[], object]]]] = [
        ('help-compiler', None, "list available compilers", show_compilers),
    ]

    def initialize_options(self):
        self.build_base = 'build'
        # 039401.python.build.line53.comment these are decided only after 'build_base' has its final value
        # 039402.python.build.line54.comment (unless overridden by the user or client)
        self.build_purelib = None
        self.build_platlib = None
        self.build_lib = None
        self.build_temp = None
        self.build_scripts = None
        self.compiler = None
        self.plat_name = None
        self.debug = None
        self.force = False
        self.executable = None
        self.parallel = None

    def finalize_options(self) -> None:  # noqa: C901
        if self.plat_name is None:
            self.plat_name = get_platform()
        else:
            # 039404.python.build.line71.comment plat-name only supported for windows (other platforms are
            # 039405.python.build.line72.comment supported via ./configure flags, if at all).  Avoid misleading
            # 039406.python.build.line73.comment other platforms.
            if os.name != 'nt':
                raise DistutilsOptionError(
                    "--plat-name only supported on Windows (try "
                    "using './configure --help' on your platform)"
                )

        plat_specifier = f".{self.plat_name}-{sys.implementation.cache_tag}"

        # 039407.python.build.line82.comment Python 3.13+ with --disable-gil shouldn't share build directories
        if sysconfig.get_config_var('Py_GIL_DISABLED'):
            plat_specifier += 't'

        # 039408.python.build.line86.comment Make it so Python 2.x and Python 2.x with --with-pydebug don't
        # 039409.python.build.line87.comment share the same build directories. Doing so confuses the build
        # 039410.python.build.line88.comment process for C modules
        if hasattr(sys, 'gettotalrefcount'):
            plat_specifier += '-pydebug'

        # 039411.python.build.line92.comment 'build_purelib' and 'build_platlib' just default to 'lib' and
        # 039412.python.build.line93.comment 'lib.<plat>' under the base build directory.  We only use one of
        # 039413.python.build.line94.comment them for a given distribution, though --
        if self.build_purelib is None:
            self.build_purelib = os.path.join(self.build_base, 'lib')
        if self.build_platlib is None:
            self.build_platlib = os.path.join(self.build_base, 'lib' + plat_specifier)

        # 039414.python.build.line100.comment 'build_lib' is the actual directory that we will use for this
        # 039415.python.build.line101.comment particular module distribution -- if user didn't supply it, pick
        # 039416.python.build.line102.comment one of 'build_purelib' or 'build_platlib'.
        if self.build_lib is None:
            if self.distribution.has_ext_modules():
                self.build_lib = self.build_platlib
            else:
                self.build_lib = self.build_purelib

        # 039417.python.build.line109.comment 'build_temp' -- temporary directory for compiler turds,
        # 039418.python.build.line110.comment "build/temp.<plat>"
        if self.build_temp is None:
            self.build_temp = os.path.join(self.build_base, 'temp' + plat_specifier)
        if self.build_scripts is None:
            self.build_scripts = os.path.join(
                self.build_base,
                f'scripts-{sys.version_info.major}.{sys.version_info.minor}',
            )

        if self.executable is None and sys.executable:
            self.executable = os.path.normpath(sys.executable)

        if isinstance(self.parallel, str):
            try:
                self.parallel = int(self.parallel)
            except ValueError:
                raise DistutilsOptionError("parallel should be an integer")

    def run(self) -> None:
        # 039419.python.build.line129.comment Run all relevant sub-commands.  This will be some subset of:
        # 039420.python.build.line130.comment - build_py      - pure Python modules
        # 039421.python.build.line131.comment - build_clib    - standalone C libraries
        # 039422.python.build.line132.comment - build_ext     - Python extensions
        # 039423.python.build.line133.comment - build_scripts - (Python) scripts
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

    # 039424.python.build.line137.comment -- Predicates for the sub-command list ---------------------------

    def has_pure_modules(self):
        return self.distribution.has_pure_modules()

    def has_c_libraries(self):
        return self.distribution.has_c_libraries()

    def has_ext_modules(self):
        return self.distribution.has_ext_modules()

    def has_scripts(self):
        return self.distribution.has_scripts()

    sub_commands = [
        ('build_py', has_pure_modules),
        ('build_clib', has_c_libraries),
        ('build_ext', has_ext_modules),
        ('build_scripts', has_scripts),
    ]
