"""distutils.cygwinccompiler

Provides the CygwinCCompiler class, a subclass of UnixCCompiler that
handles the Cygwin port of the GNU C compiler to Windows.  It also contains
the Mingw32CCompiler class which handles the mingw32 port of GCC (same as
cygwin in no-cygwin mode).
"""

import copy
import os
import pathlib
import shlex
import sys
import warnings
from subprocess import check_output

from ...errors import (
    DistutilsExecError,
    DistutilsPlatformError,
)
from ...file_util import write_file
from ...sysconfig import get_config_vars
from ...version import LooseVersion, suppress_known_deprecation
from . import unix
from .errors import (
    CompileError,
    Error,
)


def get_msvcr():
    """No longer needed, but kept for backward compatibility."""
    return []


_runtime_library_dirs_msg = (
    "Unable to set runtime library search path on Windows, "
    "usually indicated by `runtime_library_dirs` parameter to Extension"
)


class Compiler(unix.Compiler):
    """Handles the Cygwin port of the GNU C compiler to Windows."""

    compiler_type = 'cygwin'
    obj_extension = ".o"
    static_lib_extension = ".a"
    shared_lib_extension = ".dll.a"
    dylib_lib_extension = ".dll"
    static_lib_format = "lib%s%s"
    shared_lib_format = "lib%s%s"
    dylib_lib_format = "cyg%s%s"
    exe_extension = ".exe"

    def __init__(self, verbose=False, dry_run=False, force=False):
        super().__init__(verbose, dry_run, force)

        status, details = check_config_h()
        self.debug_print(f"Python's GCC status: {status} (details: {details})")
        if status is not CONFIG_H_OK:
            self.warn(
                "Python's pyconfig.h doesn't seem to support your compiler. "
                f"Reason: {details}. "
                "Compiling may fail because of undefined preprocessor macros."
            )

        self.cc, self.cxx = get_config_vars('CC', 'CXX')

        # 040156.python.cygwin.line69.comment Override 'CC' and 'CXX' environment variables for
        # 040157.python.cygwin.line70.comment building using MINGW compiler for MSVC python.
        self.cc = os.environ.get('CC', self.cc or 'gcc')
        self.cxx = os.environ.get('CXX', self.cxx or 'g++')

        self.linker_dll = self.cc
        self.linker_dll_cxx = self.cxx
        shared_option = "-shared"

        self.set_executables(
            compiler=f'{self.cc} -mcygwin -O -Wall',
            compiler_so=f'{self.cc} -mcygwin -mdll -O -Wall',
            compiler_cxx=f'{self.cxx} -mcygwin -O -Wall',
            compiler_so_cxx=f'{self.cxx} -mcygwin -mdll -O -Wall',
            linker_exe=f'{self.cc} -mcygwin',
            linker_so=f'{self.linker_dll} -mcygwin {shared_option}',
            linker_exe_cxx=f'{self.cxx} -mcygwin',
            linker_so_cxx=f'{self.linker_dll_cxx} -mcygwin {shared_option}',
        )

        self.dll_libraries = get_msvcr()

    @property
    def gcc_version(self):
        # 040158.python.cygwin.line93.comment Older numpy depended on this existing to check for ancient
        # 040159.python.cygwin.line94.comment gcc versions. This doesn't make much sense with clang etc so
        # 040160.python.cygwin.line95.comment just hardcode to something recent.
        # 040161.python.cygwin.line96.comment https://github.com/numpy/numpy/pull/20333
        warnings.warn(
            "gcc_version attribute of CygwinCCompiler is deprecated. "
            "Instead of returning actual gcc version a fixed value 11.2.0 is returned.",
            DeprecationWarning,
            stacklevel=2,
        )
        with suppress_known_deprecation():
            return LooseVersion("11.2.0")

    def _compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
        """Compiles the source by spawning GCC and windres if needed."""
        if ext in ('.rc', '.res'):
            # 040162.python.cygwin.line109.comment gcc needs '.res' and '.rc' compiled to object files !!!
            try:
                self.spawn(["windres", "-i", src, "-o", obj])
            except DistutilsExecError as msg:
                raise CompileError(msg)
        else:  # for other files use the C-compiler
            try:
                if self.detect_language(src) == 'c++':
                    self.spawn(
                        self.compiler_so_cxx
                        + cc_args
                        + [src, '-o', obj]
                        + extra_postargs
                    )
                else:
                    self.spawn(
                        self.compiler_so + cc_args + [src, '-o', obj] + extra_postargs
                    )
            except DistutilsExecError as msg:
                raise CompileError(msg)

    def link(
        self,
        target_desc,
        objects,
        output_filename,
        output_dir=None,
        libraries=None,
        library_dirs=None,
        runtime_library_dirs=None,
        export_symbols=None,
        debug=False,
        extra_preargs=None,
        extra_postargs=None,
        build_temp=None,
        target_lang=None,
    ):
        """Link the objects."""
        # 040164.python.cygwin.line147.comment use separate copies, so we can modify the lists
        extra_preargs = copy.copy(extra_preargs or [])
        libraries = copy.copy(libraries or [])
        objects = copy.copy(objects or [])

        if runtime_library_dirs:
            self.warn(_runtime_library_dirs_msg)

        # 040165.python.cygwin.line155.comment Additional libraries
        libraries.extend(self.dll_libraries)

        # 040166.python.cygwin.line158.comment handle export symbols by creating a def-file
        # 040167.python.cygwin.line159.comment with executables this only works with gcc/ld as linker
        if (export_symbols is not None) and (
            target_desc != self.EXECUTABLE or self.linker_dll == "gcc"
        ):
            # 040168.python.cygwin.line163.comment (The linker doesn't do anything if output is up-to-date.
            # 040169.python.cygwin.line164.comment So it would probably better to check if we really need this,
            # 040170.python.cygwin.line165.comment but for this we had to insert some unchanged parts of
            # 040171.python.cygwin.line166.comment UnixCCompiler, and this is not what we want.)

            # 040172.python.cygwin.line168.comment we want to put some files in the same directory as the
            # 040173.python.cygwin.line169.comment object files are, build_temp doesn't help much
            # 040174.python.cygwin.line170.comment where are the object files
            temp_dir = os.path.dirname(objects[0])
            # 040175.python.cygwin.line172.comment name of dll to give the helper files the same base name
            (dll_name, dll_extension) = os.path.splitext(
                os.path.basename(output_filename)
            )

            # 040176.python.cygwin.line177.comment generate the filenames for these files
            def_file = os.path.join(temp_dir, dll_name + ".def")

            # 040177.python.cygwin.line180.comment Generate .def file
            contents = [f"LIBRARY {os.path.basename(output_filename)}", "EXPORTS"]
            contents.extend(export_symbols)
            self.execute(write_file, (def_file, contents), f"writing {def_file}")

            # 040178.python.cygwin.line185.comment next add options for def-file

            # 040179.python.cygwin.line187.comment for gcc/ld the def-file is specified as any object files
            objects.append(def_file)

        # 040180.python.cygwin.line190.comment end: if ((export_symbols is not None) and
        # 040181.python.cygwin.line191.comment (target_desc != self.EXECUTABLE or self.linker_dll == "gcc")):

        # 040182.python.cygwin.line193.comment who wants symbols and a many times larger output file
        # 040183.python.cygwin.line194.comment should explicitly switch the debug mode on
        # 040184.python.cygwin.line195.comment otherwise we let ld strip the output file
        # 040185.python.cygwin.line196.comment (On my machine: 10KiB < stripped_file < ??100KiB
        # 040186.python.cygwin.line197.comment unstripped_file = stripped_file + XXX KiB
        # 040187.python.cygwin.line198.comment ( XXX=254 for a typical python extension))
        if not debug:
            extra_preargs.append("-s")

        super().link(
            target_desc,
            objects,
            output_filename,
            output_dir,
            libraries,
            library_dirs,
            runtime_library_dirs,
            None,  # export_symbols, we do this in our def-file
            debug,
            extra_preargs,
            extra_postargs,
            build_temp,
            target_lang,
        )

    def runtime_library_dir_option(self, dir):
        # 040189.python.cygwin.line219.comment cygwin doesn't support rpath. While in theory we could error
        # 040190.python.cygwin.line220.comment out like MSVC does, code might expect it to work like on Unix, so
        # 040191.python.cygwin.line221.comment just warn and hope for the best.
        self.warn(_runtime_library_dirs_msg)
        return []

    # 040192.python.cygwin.line225.comment -- Miscellaneous methods -----------------------------------------

    def _make_out_path(self, output_dir, strip_dir, src_name):
        # 040193.python.cygwin.line228.comment use normcase to make sure '.rc' is really '.rc' and not '.RC'
        norm_src_name = os.path.normcase(src_name)
        return super()._make_out_path(output_dir, strip_dir, norm_src_name)

    @property
    def out_extensions(self):
        """
        Add support for rc and res files.
        """
        return {
            **super().out_extensions,
            **{ext: ext + self.obj_extension for ext in ('.res', '.rc')},
        }


# 040194.python.cygwin.line243.comment the same as cygwin plus some additional parameters
class MinGW32Compiler(Compiler):
    """Handles the Mingw32 port of the GNU C compiler to Windows."""

    compiler_type = 'mingw32'

    def __init__(self, verbose=False, dry_run=False, force=False):
        super().__init__(verbose, dry_run, force)

        shared_option = "-shared"

        if is_cygwincc(self.cc):
            raise Error('Cygwin gcc cannot be used with --compiler=mingw32')

        self.set_executables(
            compiler=f'{self.cc} -O -Wall',
            compiler_so=f'{self.cc} -shared -O -Wall',
            compiler_so_cxx=f'{self.cxx} -shared -O -Wall',
            compiler_cxx=f'{self.cxx} -O -Wall',
            linker_exe=f'{self.cc}',
            linker_so=f'{self.linker_dll} {shared_option}',
            linker_exe_cxx=f'{self.cxx}',
            linker_so_cxx=f'{self.linker_dll_cxx} {shared_option}',
        )

    def runtime_library_dir_option(self, dir):
        raise DistutilsPlatformError(_runtime_library_dirs_msg)


# 040195.python.cygwin.line272.comment Because these compilers aren't configured in Python's pyconfig.h file by
# 040196.python.cygwin.line273.comment default, we should at least warn the user if he is using an unmodified
# 040197.python.cygwin.line274.comment version.

CONFIG_H_OK = "ok"
CONFIG_H_NOTOK = "not ok"
CONFIG_H_UNCERTAIN = "uncertain"


def check_config_h():
    """Check if the current Python installation appears amenable to building
    extensions with GCC.

    Returns a tuple (status, details), where 'status' is one of the following
    constants:

    - CONFIG_H_OK: all is well, go ahead and compile
    - CONFIG_H_NOTOK: doesn't look good
    - CONFIG_H_UNCERTAIN: not sure -- unable to read pyconfig.h

    'details' is a human-readable string explaining the situation.

    Note there are two ways to conclude "OK": either 'sys.version' contains
    the string "GCC" (implying that this Python was built with GCC), or the
    installed "pyconfig.h" contains the string "__GNUC__".
    """

    # 040198.python.cygwin.line299.comment XXX since this function also checks sys.version, it's not strictly a
    # 040199.python.cygwin.line300.comment "pyconfig.h" check -- should probably be renamed...

    from distutils import sysconfig

    # 040200.python.cygwin.line304.comment if sys.version contains GCC then python was compiled with GCC, and the
    # 040201.python.cygwin.line305.comment pyconfig.h file should be OK
    if "GCC" in sys.version:
        return CONFIG_H_OK, "sys.version mentions 'GCC'"

    # 040202.python.cygwin.line309.comment Clang would also work
    if "Clang" in sys.version:
        return CONFIG_H_OK, "sys.version mentions 'Clang'"

    # 040203.python.cygwin.line313.comment let's see if __GNUC__ is mentioned in python.h
    fn = sysconfig.get_config_h_filename()
    try:
        config_h = pathlib.Path(fn).read_text(encoding='utf-8')
    except OSError as exc:
        return (CONFIG_H_UNCERTAIN, f"couldn't read '{fn}': {exc.strerror}")
    else:
        substring = '__GNUC__'
        if substring in config_h:
            code = CONFIG_H_OK
            mention_inflected = 'mentions'
        else:
            code = CONFIG_H_NOTOK
            mention_inflected = 'does not mention'
        return code, f"{fn!r} {mention_inflected} {substring!r}"


def is_cygwincc(cc):
    """Try to determine if the compiler that would be used is from cygwin."""
    out_string = check_output(shlex.split(cc) + ['-dumpmachine'])
    return out_string.strip().endswith(b'cygwin')


get_versions = None
"""
A stand-in for the previous get_versions() function to prevent failures
when monkeypatched. See pypa/setuptools#2969.
"""
