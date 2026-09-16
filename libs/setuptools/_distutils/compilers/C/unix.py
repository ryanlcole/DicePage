"""distutils.unixccompiler

Contains the UnixCCompiler class, a subclass of CCompiler that handles
the "typical" Unix-style command-line C compiler:
  * macros defined with -Dname[=value]
  * macros undefined with -Uname
  * include search directories specified with -Idir
  * libraries specified with -lllib
  * library search directories specified with -Ldir
  * compile handled by 'cc' (or similar) executable with -c option:
    compiles .c to .o
  * link static library handled by 'ar' command (possibly with 'ranlib')
  * link shared library handled by 'cc -shared'
"""

from __future__ import annotations

import itertools
import os
import re
import shlex
import sys
from collections.abc import Iterable

from ... import sysconfig
from ..._log import log
from ..._macos_compat import compiler_fixup
from ..._modified import newer
from ...compat import consolidate_linker_args
from ...errors import DistutilsExecError
from . import base
from .base import _Macro, gen_lib_options, gen_preprocess_options
from .errors import (
    CompileError,
    LibError,
    LinkError,
)

# 040314.python.unix.line39.comment XXX Things not currently handled:
# 040315.python.unix.line40.comment * optimization/debug/warning flags; we just use whatever's in Python's
# 040316.python.unix.line41.comment Makefile and live with it.  Is this adequate?  If not, we might
# 040317.python.unix.line42.comment have to have a bunch of subclasses GNUCCompiler, SGICCompiler,
# 040318.python.unix.line43.comment SunCCompiler, and I suspect down that road lies madness.
# 040319.python.unix.line44.comment * even if we don't know a warning flag from an optimization flag,
# 040320.python.unix.line45.comment we need some way for outsiders to feed preprocessor/compiler/linker
# 040321.python.unix.line46.comment flags in to us -- eg. a sysadmin might want to mandate certain flags
# 040322.python.unix.line47.comment via a site config file, or a user might want to set something for
# 040323.python.unix.line48.comment compiling this module distribution only via the setup.py command
# 040324.python.unix.line49.comment line, whatever.  As long as these options come from something on the
# 040325.python.unix.line50.comment current system, they can be as system-dependent as they like, and we
# 040326.python.unix.line51.comment should just happily stuff them into the preprocessor/compiler/linker
# 040327.python.unix.line52.comment options and carry on.


def _split_env(cmd):
    """
    For macOS, split command into 'env' portion (if any)
    and the rest of the linker command.

    >>> _split_env(['a', 'b', 'c'])
    ([], ['a', 'b', 'c'])
    >>> _split_env(['/usr/bin/env', 'A=3', 'gcc'])
    (['/usr/bin/env', 'A=3'], ['gcc'])
    """
    pivot = 0
    if os.path.basename(cmd[0]) == "env":
        pivot = 1
        while '=' in cmd[pivot]:
            pivot += 1
    return cmd[:pivot], cmd[pivot:]


def _split_aix(cmd):
    """
    AIX platforms prefix the compiler with the ld_so_aix
    script, so split that from the linker command.

    >>> _split_aix(['a', 'b', 'c'])
    ([], ['a', 'b', 'c'])
    >>> _split_aix(['/bin/foo/ld_so_aix', 'gcc'])
    (['/bin/foo/ld_so_aix'], ['gcc'])
    """
    pivot = os.path.basename(cmd[0]) == 'ld_so_aix'
    return cmd[:pivot], cmd[pivot:]


def _linker_params(linker_cmd, compiler_cmd):
    """
    The linker command usually begins with the compiler
    command (possibly multiple elements), followed by zero or more
    params for shared library building.

    If the LDSHARED env variable overrides the linker command,
    however, the commands may not match.

    Return the best guess of the linker parameters by stripping
    the linker command. If the compiler command does not
    match the linker command, assume the linker command is
    just the first element.

    >>> _linker_params('gcc foo bar'.split(), ['gcc'])
    ['foo', 'bar']
    >>> _linker_params('gcc foo bar'.split(), ['other'])
    ['foo', 'bar']
    >>> _linker_params('ccache gcc foo bar'.split(), 'ccache gcc'.split())
    ['foo', 'bar']
    >>> _linker_params(['gcc'], ['gcc'])
    []
    """
    c_len = len(compiler_cmd)
    pivot = c_len if linker_cmd[:c_len] == compiler_cmd else 1
    return linker_cmd[pivot:]


class Compiler(base.Compiler):
    compiler_type = 'unix'

    # 040328.python.unix.line118.comment These are used by CCompiler in two places: the constructor sets
    # 040329.python.unix.line119.comment instance attributes 'preprocessor', 'compiler', etc. from them, and
    # 040330.python.unix.line120.comment 'set_executable()' allows any of these to be set.  The defaults here
    # 040331.python.unix.line121.comment are pretty generic; they will probably have to be set by an outsider
    # 040332.python.unix.line122.comment (eg. using information discovered by the sysconfig about building
    # 040333.python.unix.line123.comment Python extensions).
    executables = {
        'preprocessor': None,
        'compiler': ["cc"],
        'compiler_so': ["cc"],
        'compiler_cxx': ["c++"],
        'compiler_so_cxx': ["c++"],
        'linker_so': ["cc", "-shared"],
        'linker_so_cxx': ["c++", "-shared"],
        'linker_exe': ["cc"],
        'linker_exe_cxx': ["c++", "-shared"],
        'archiver': ["ar", "-cr"],
        'ranlib': None,
    }

    if sys.platform[:6] == "darwin":
        executables['ranlib'] = ["ranlib"]

    # 040334.python.unix.line141.comment Needed for the filename generation methods provided by the base
    # 040335.python.unix.line142.comment class, CCompiler.  NB. whoever instantiates/uses a particular
    # 040336.python.unix.line143.comment UnixCCompiler instance should set 'shared_lib_ext' -- we set a
    # 040337.python.unix.line144.comment reasonable common default here, but it's not necessarily used on all
    # 040338.python.unix.line145.comment Unices!

    src_extensions = [".c", ".C", ".cc", ".cxx", ".cpp", ".m"]
    obj_extension = ".o"
    static_lib_extension = ".a"
    shared_lib_extension = ".so"
    dylib_lib_extension = ".dylib"
    xcode_stub_lib_extension = ".tbd"
    static_lib_format = shared_lib_format = dylib_lib_format = "lib%s%s"
    xcode_stub_lib_format = dylib_lib_format
    if sys.platform == "cygwin":
        exe_extension = ".exe"
        shared_lib_extension = ".dll.a"
        dylib_lib_extension = ".dll"
        dylib_lib_format = "cyg%s%s"

    def _fix_lib_args(self, libraries, library_dirs, runtime_library_dirs):
        """Remove standard library path from rpath"""
        libraries, library_dirs, runtime_library_dirs = super()._fix_lib_args(
            libraries, library_dirs, runtime_library_dirs
        )
        libdir = sysconfig.get_config_var('LIBDIR')
        if (
            runtime_library_dirs
            and libdir.startswith("/usr/lib")
            and (libdir in runtime_library_dirs)
        ):
            runtime_library_dirs.remove(libdir)
        return libraries, library_dirs, runtime_library_dirs

    def preprocess(
        self,
        source: str | os.PathLike[str],
        output_file: str | os.PathLike[str] | None = None,
        macros: list[_Macro] | None = None,
        include_dirs: list[str] | tuple[str, ...] | None = None,
        extra_preargs: list[str] | None = None,
        extra_postargs: Iterable[str] | None = None,
    ):
        fixed_args = self._fix_compile_args(None, macros, include_dirs)
        ignore, macros, include_dirs = fixed_args
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = self.preprocessor + pp_opts
        if output_file:
            pp_args.extend(['-o', output_file])
        if extra_preargs:
            pp_args[:0] = extra_preargs
        if extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # 040339.python.unix.line196.comment reasons to preprocess:
        # 040340.python.unix.line197.comment - force is indicated
        # 040341.python.unix.line198.comment - output is directed to stdout
        # 040342.python.unix.line199.comment - source file is newer than the target
        preprocess = self.force or output_file is None or newer(source, output_file)
        if not preprocess:
            return

        if output_file:
            self.mkpath(os.path.dirname(output_file))

        try:
            self.spawn(pp_args)
        except DistutilsExecError as msg:
            raise CompileError(msg)

    def _compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
        compiler_so = compiler_fixup(self.compiler_so, cc_args + extra_postargs)
        compiler_so_cxx = compiler_fixup(self.compiler_so_cxx, cc_args + extra_postargs)
        try:
            if self.detect_language(src) == 'c++':
                self.spawn(
                    compiler_so_cxx + cc_args + [src, '-o', obj] + extra_postargs
                )
            else:
                self.spawn(compiler_so + cc_args + [src, '-o', obj] + extra_postargs)
        except DistutilsExecError as msg:
            raise CompileError(msg)

    def create_static_lib(
        self, objects, output_libname, output_dir=None, debug=False, target_lang=None
    ):
        objects, output_dir = self._fix_object_args(objects, output_dir)

        output_filename = self.library_filename(output_libname, output_dir=output_dir)

        if self._need_link(objects, output_filename):
            self.mkpath(os.path.dirname(output_filename))
            self.spawn(self.archiver + [output_filename] + objects + self.objects)

            # 040343.python.unix.line236.comment Not many Unices required ranlib anymore -- SunOS 4.x is, I
            # 040344.python.unix.line237.comment think the only major Unix that does.  Maybe we need some
            # 040345.python.unix.line238.comment platform intelligence here to skip ranlib if it's not
            # 040346.python.unix.line239.comment needed -- or maybe Python's configure script took care of
            # 040347.python.unix.line240.comment it for us, hence the check for leading colon.
            if self.ranlib:
                try:
                    self.spawn(self.ranlib + [output_filename])
                except DistutilsExecError as msg:
                    raise LibError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    def link(
        self,
        target_desc,
        objects: list[str] | tuple[str, ...],
        output_filename,
        output_dir: str | None = None,
        libraries: list[str] | tuple[str, ...] | None = None,
        library_dirs: list[str] | tuple[str, ...] | None = None,
        runtime_library_dirs: list[str] | tuple[str, ...] | None = None,
        export_symbols=None,
        debug=False,
        extra_preargs=None,
        extra_postargs=None,
        build_temp=None,
        target_lang=None,
    ):
        objects, output_dir = self._fix_object_args(objects, output_dir)
        fixed_args = self._fix_lib_args(libraries, library_dirs, runtime_library_dirs)
        libraries, library_dirs, runtime_library_dirs = fixed_args

        lib_opts = gen_lib_options(self, library_dirs, runtime_library_dirs, libraries)
        if not isinstance(output_dir, (str, type(None))):
            raise TypeError("'output_dir' must be a string or None")
        if output_dir is not None:
            output_filename = os.path.join(output_dir, output_filename)

        if self._need_link(objects, output_filename):
            ld_args = objects + self.objects + lib_opts + ['-o', output_filename]
            if debug:
                ld_args[:0] = ['-g']
            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)
            self.mkpath(os.path.dirname(output_filename))
            try:
                # 040348.python.unix.line285.comment Select a linker based on context: linker_exe when
                # 040349.python.unix.line286.comment building an executable or linker_so (with shared options)
                # 040350.python.unix.line287.comment when building a shared library.
                building_exe = target_desc == base.Compiler.EXECUTABLE
                target_cxx = target_lang == "c++"
                linker = (
                    (self.linker_exe_cxx if target_cxx else self.linker_exe)
                    if building_exe
                    else (self.linker_so_cxx if target_cxx else self.linker_so)
                )[:]

                if target_cxx and self.compiler_cxx:
                    env, linker_ne = _split_env(linker)
                    aix, linker_na = _split_aix(linker_ne)
                    _, compiler_cxx_ne = _split_env(self.compiler_cxx)
                    _, linker_exe_ne = _split_env(self.linker_exe_cxx)

                    params = _linker_params(linker_na, linker_exe_ne)
                    linker = env + aix + compiler_cxx_ne + params

                linker = compiler_fixup(linker, ld_args)

                self.spawn(linker + ld_args)
            except DistutilsExecError as msg:
                raise LinkError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    # 040351.python.unix.line313.comment -- Miscellaneous methods -----------------------------------------
    # 040352.python.unix.line314.comment These are all used by the 'gen_lib_options() function, in
    # 040353.python.unix.line315.comment ccompiler.py.

    def library_dir_option(self, dir):
        return "-L" + dir

    def _is_gcc(self):
        cc_var = sysconfig.get_config_var("CC")
        compiler = os.path.basename(shlex.split(cc_var)[0])
        return "gcc" in compiler or "g++" in compiler

    def runtime_library_dir_option(self, dir: str) -> str | list[str]:  # type: ignore[override] # Fixed in pypa/distutils#339
        # 040355.python.unix.line326.comment XXX Hackish, at the very least.  See Python bug #445902:
        # 040356.python.unix.line327.comment https://bugs.python.org/issue445902
        # 040357.python.unix.line328.comment Linkers on different platforms need different options to
        # 040358.python.unix.line329.comment specify that directories need to be added to the list of
        # 040359.python.unix.line330.comment directories searched for dependencies when a dynamic library
        # 040360.python.unix.line331.comment is sought.  GCC on GNU systems (Linux, FreeBSD, ...) has to
        # 040361.python.unix.line332.comment be told to pass the -R option through to the linker, whereas
        # 040362.python.unix.line333.comment other compilers and gcc on other systems just know this.
        # 040363.python.unix.line334.comment Other compilers may need something slightly different.  At
        # 040364.python.unix.line335.comment this time, there's no way to determine this information from
        # 040365.python.unix.line336.comment the configuration data stored in the Python installation, so
        # 040366.python.unix.line337.comment we use this hack.
        if sys.platform[:6] == "darwin":
            from distutils.util import get_macosx_target_ver, split_version

            macosx_target_ver = get_macosx_target_ver()
            if macosx_target_ver and split_version(macosx_target_ver) >= [10, 5]:
                return "-Wl,-rpath," + dir
            else:  # no support for -rpath on earlier macOS versions
                return "-L" + dir
        elif sys.platform[:7] == "freebsd":
            return "-Wl,-rpath=" + dir
        elif sys.platform[:5] == "hp-ux":
            return [
                "-Wl,+s" if self._is_gcc() else "+s",
                "-L" + dir,
            ]

        # 040368.python.unix.line354.comment For all compilers, `-Wl` is the presumed way to pass a
        # 040369.python.unix.line355.comment compiler option to the linker
        if sysconfig.get_config_var("GNULD") == "yes":
            return consolidate_linker_args([
                # 040370.python.unix.line358.comment Force RUNPATH instead of RPATH
                "-Wl,--enable-new-dtags",
                "-Wl,-rpath," + dir,
            ])
        else:
            return "-Wl,-R" + dir

    def library_option(self, lib):
        return "-l" + lib

    @staticmethod
    def _library_root(dir):
        """
        macOS users can specify an alternate SDK using'-isysroot'.
        Calculate the SDK root if it is specified.

        Note that, as of Xcode 7, Apple SDKs may contain textual stub
        libraries with .tbd extensions rather than the normal .dylib
        shared libraries installed in /.  The Apple compiler tool
        chain handles this transparently but it can cause problems
        for programs that are being built with an SDK and searching
        for specific libraries.  Callers of find_library_file need to
        keep in mind that the base filename of the returned SDK library
        file might have a different extension from that of the library
        file installed on the running system, for example:
          /Applications/Xcode.app/Contents/Developer/Platforms/
              MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk/
              usr/lib/libedit.tbd
        vs
          /usr/lib/libedit.dylib
        """
        cflags = sysconfig.get_config_var('CFLAGS')
        match = re.search(r'-isysroot\s*(\S+)', cflags)

        apply_root = (
            sys.platform == 'darwin'
            and match
            and (
                dir.startswith('/System/')
                or (dir.startswith('/usr/') and not dir.startswith('/usr/local/'))
            )
        )

        return os.path.join(match.group(1), dir[1:]) if apply_root else dir

    def find_library_file(self, dirs, lib, debug=False):
        """
        Second-guess the linker with not much hard
        data to go on: GCC seems to prefer the shared library, so
        assume that *all* Unix C compilers do,
        ignoring even GCC's "-static" option.
        """
        lib_names = (
            self.library_filename(lib, lib_type=type)
            for type in 'dylib xcode_stub shared static'.split()
        )

        roots = map(self._library_root, dirs)

        searched = itertools.starmap(os.path.join, itertools.product(roots, lib_names))

        found = filter(os.path.exists, searched)

        # 040371.python.unix.line421.comment Return None if it could not be found in any dir.
        return next(found, None)
