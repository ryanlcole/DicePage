"""distutils._msvccompiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
for Microsoft Visual Studio 2015.

This module requires VS 2015 or later.
"""

# 040204.python.msvc.line9.comment Written by Perry Stoll
# 040205.python.msvc.line10.comment hacked by Robin Becker and Thomas Heller to do a better job of
# 040206.python.msvc.line11.comment finding DevStudio (through the registry)
# 040207.python.msvc.line12.comment ported to VS 2005 and VS 2008 by Christian Heimes
# 040208.python.msvc.line13.comment ported to VS 2015 by Steve Dower
from __future__ import annotations

import contextlib
import os
import subprocess
import unittest.mock as mock
import warnings
from collections.abc import Iterable

with contextlib.suppress(ImportError):
    import winreg

from itertools import count

from ..._log import log
from ...errors import (
    DistutilsExecError,
    DistutilsPlatformError,
)
from ...util import get_host_platform, get_platform
from . import base
from .base import gen_lib_options
from .errors import (
    CompileError,
    LibError,
    LinkError,
)


def _find_vc2015():
    try:
        key = winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\VisualStudio\SxS\VC7",
            access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
        )
    except OSError:
        log.debug("Visual C++ is not registered")
        return None, None

    best_version = 0
    best_dir = None
    with key:
        for i in count():
            try:
                v, vc_dir, vt = winreg.EnumValue(key, i)
            except OSError:
                break
            if v and vt == winreg.REG_SZ and os.path.isdir(vc_dir):
                try:
                    version = int(float(v))
                except (ValueError, TypeError):
                    continue
                if version >= 14 and version > best_version:
                    best_version, best_dir = version, vc_dir
    return best_version, best_dir


def _find_vc2017():
    """Returns "15, path" based on the result of invoking vswhere.exe
    If no install is found, returns "None, None"

    The version is returned to avoid unnecessarily changing the function
    result. It may be ignored when the path is not None.

    If vswhere.exe is not available, by definition, VS 2017 is not
    installed.
    """
    root = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles")
    if not root:
        return None, None

    variant = 'arm64' if get_platform() == 'win-arm64' else 'x86.x64'
    suitable_components = (
        f"Microsoft.VisualStudio.Component.VC.Tools.{variant}",
        "Microsoft.VisualStudio.Workload.WDExpress",
    )

    for component in suitable_components:
        # 040209.python.msvc.line93.comment Workaround for `-requiresAny` (only available on VS 2017 > 15.6)
        with contextlib.suppress(
            subprocess.CalledProcessError, OSError, UnicodeDecodeError
        ):
            path = (
                subprocess.check_output([
                    os.path.join(
                        root, "Microsoft Visual Studio", "Installer", "vswhere.exe"
                    ),
                    "-latest",
                    "-prerelease",
                    "-requires",
                    component,
                    "-property",
                    "installationPath",
                    "-products",
                    "*",
                ])
                .decode(encoding="mbcs", errors="strict")
                .strip()
            )

            path = os.path.join(path, "VC", "Auxiliary", "Build")
            if os.path.isdir(path):
                return 15, path

    return None, None  # no suitable component found


PLAT_SPEC_TO_RUNTIME = {
    'x86': 'x86',
    'x86_amd64': 'x64',
    'x86_arm': 'arm',
    'x86_arm64': 'arm64',
}


def _find_vcvarsall(plat_spec):
    # 040211.python.msvc.line131.comment bpo-38597: Removed vcruntime return value
    _, best_dir = _find_vc2017()

    if not best_dir:
        best_version, best_dir = _find_vc2015()

    if not best_dir:
        log.debug("No suitable Visual C++ version found")
        return None, None

    vcvarsall = os.path.join(best_dir, "vcvarsall.bat")
    if not os.path.isfile(vcvarsall):
        log.debug("%s cannot be found", vcvarsall)
        return None, None

    return vcvarsall, None


def _get_vc_env(plat_spec):
    if os.getenv("DISTUTILS_USE_SDK"):
        return {key.lower(): value for key, value in os.environ.items()}

    vcvarsall, _ = _find_vcvarsall(plat_spec)
    if not vcvarsall:
        raise DistutilsPlatformError(
            'Microsoft Visual C++ 14.0 or greater is required. '
            'Get it with "Microsoft C++ Build Tools": '
            'https://visualstudio.microsoft.com/visual-cpp-build-tools/'
        )

    try:
        out = subprocess.check_output(
            f'cmd /u /c "{vcvarsall}" {plat_spec} && set',
            stderr=subprocess.STDOUT,
        ).decode('utf-16le', errors='replace')
    except subprocess.CalledProcessError as exc:
        log.error(exc.output)
        raise DistutilsPlatformError(f"Error executing {exc.cmd}")

    env = {
        key.lower(): value
        for key, _, value in (line.partition('=') for line in out.splitlines())
        if key and value
    }

    return env


def _find_exe(exe, paths=None):
    """Return path to an MSVC executable program.

    Tries to find the program in several places: first, one of the
    MSVC program search paths from the registry; next, the directories
    in the PATH environment variable.  If any of those work, return an
    absolute path that is known to exist.  If none of them work, just
    return the original program name, 'exe'.
    """
    if not paths:
        paths = os.getenv('path').split(os.pathsep)
    for p in paths:
        fn = os.path.join(os.path.abspath(p), exe)
        if os.path.isfile(fn):
            return fn
    return exe


_vcvars_names = {
    'win32': 'x86',
    'win-amd64': 'amd64',
    'win-arm32': 'arm',
    'win-arm64': 'arm64',
}


def _get_vcvars_spec(host_platform, platform):
    """
    Given a host platform and platform, determine the spec for vcvarsall.

    Uses the native MSVC host if the host platform would need expensive
    emulation for x86.

    >>> _get_vcvars_spec('win-arm64', 'win32')
    'arm64_x86'
    >>> _get_vcvars_spec('win-arm64', 'win-amd64')
    'arm64_amd64'

    Otherwise, always cross-compile from x86 to work with the
    lighter-weight MSVC installs that do not include native 64-bit tools.

    >>> _get_vcvars_spec('win32', 'win32')
    'x86'
    >>> _get_vcvars_spec('win-arm32', 'win-arm32')
    'x86_arm'
    >>> _get_vcvars_spec('win-amd64', 'win-arm64')
    'x86_arm64'
    """
    if host_platform != 'win-arm64':
        host_platform = 'win32'
    vc_hp = _vcvars_names[host_platform]
    vc_plat = _vcvars_names[platform]
    return vc_hp if vc_hp == vc_plat else f'{vc_hp}_{vc_plat}'


class Compiler(base.Compiler):
    """Concrete class that implements an interface to Microsoft Visual C++,
    as defined by the CCompiler abstract class."""

    compiler_type = 'msvc'

    # 040212.python.msvc.line240.comment Just set this so CCompiler's constructor doesn't barf.  We currently
    # 040213.python.msvc.line241.comment don't use the 'set_executables()' bureaucracy provided by CCompiler,
    # 040214.python.msvc.line242.comment as it really isn't necessary for this sort of single-compiler class.
    # 040215.python.msvc.line243.comment Would be nice to have a consistent interface with UnixCCompiler,
    # 040216.python.msvc.line244.comment though, so it's worth thinking about.
    executables = {}

    # 040217.python.msvc.line247.comment Private class data (need to distinguish C from C++ source for compiler)
    _c_extensions = ['.c']
    _cpp_extensions = ['.cc', '.cpp', '.cxx']
    _rc_extensions = ['.rc']
    _mc_extensions = ['.mc']

    # 040218.python.msvc.line253.comment Needed for the filename generation methods provided by the
    # 040219.python.msvc.line254.comment base class, CCompiler.
    src_extensions = _c_extensions + _cpp_extensions + _rc_extensions + _mc_extensions
    res_extension = '.res'
    obj_extension = '.obj'
    static_lib_extension = '.lib'
    shared_lib_extension = '.dll'
    static_lib_format = shared_lib_format = '%s%s'
    exe_extension = '.exe'

    def __init__(self, verbose=False, dry_run=False, force=False) -> None:
        super().__init__(verbose, dry_run, force)
        # 040220.python.msvc.line265.comment target platform (.plat_name is consistent with 'bdist')
        self.plat_name = None
        self.initialized = False

    @classmethod
    def _configure(cls, vc_env):
        """
        Set class-level include/lib dirs.
        """
        cls.include_dirs = cls._parse_path(vc_env.get('include', ''))
        cls.library_dirs = cls._parse_path(vc_env.get('lib', ''))

    @staticmethod
    def _parse_path(val):
        return [dir.rstrip(os.sep) for dir in val.split(os.pathsep) if dir]

    def initialize(self, plat_name: str | None = None) -> None:
        # 040221.python.msvc.line282.comment multi-init means we would need to check platform same each time...
        assert not self.initialized, "don't init multiple times"
        if plat_name is None:
            plat_name = get_platform()
        # 040222.python.msvc.line286.comment sanity check for platforms to prevent obscure errors later.
        if plat_name not in _vcvars_names:
            raise DistutilsPlatformError(
                f"--plat-name must be one of {tuple(_vcvars_names)}"
            )

        plat_spec = _get_vcvars_spec(get_host_platform(), plat_name)

        vc_env = _get_vc_env(plat_spec)
        if not vc_env:
            raise DistutilsPlatformError(
                "Unable to find a compatible Visual Studio installation."
            )
        self._configure(vc_env)

        self._paths = vc_env.get('path', '')
        paths = self._paths.split(os.pathsep)
        self.cc = _find_exe("cl.exe", paths)
        self.linker = _find_exe("link.exe", paths)
        self.lib = _find_exe("lib.exe", paths)
        self.rc = _find_exe("rc.exe", paths)  # resource compiler
        self.mc = _find_exe("mc.exe", paths)  # message compiler
        self.mt = _find_exe("mt.exe", paths)  # message compiler

        self.preprocess_options = None
        # 040226.python.msvc.line311.comment bpo-38597: Always compile with dynamic linking
        # 040227.python.msvc.line312.comment Future releases of Python 3.x will include all past
        # 040228.python.msvc.line313.comment versions of vcruntime*.dll for compatibility.
        self.compile_options = ['/nologo', '/O2', '/W3', '/GL', '/DNDEBUG', '/MD']

        self.compile_options_debug = [
            '/nologo',
            '/Od',
            '/MDd',
            '/Zi',
            '/W3',
            '/D_DEBUG',
        ]

        ldflags = ['/nologo', '/INCREMENTAL:NO', '/LTCG']

        ldflags_debug = ['/nologo', '/INCREMENTAL:NO', '/LTCG', '/DEBUG:FULL']

        self.ldflags_exe = [*ldflags, '/MANIFEST:EMBED,ID=1']
        self.ldflags_exe_debug = [*ldflags_debug, '/MANIFEST:EMBED,ID=1']
        self.ldflags_shared = [
            *ldflags,
            '/DLL',
            '/MANIFEST:EMBED,ID=2',
            '/MANIFESTUAC:NO',
        ]
        self.ldflags_shared_debug = [
            *ldflags_debug,
            '/DLL',
            '/MANIFEST:EMBED,ID=2',
            '/MANIFESTUAC:NO',
        ]
        self.ldflags_static = [*ldflags]
        self.ldflags_static_debug = [*ldflags_debug]

        self._ldflags = {
            (base.Compiler.EXECUTABLE, None): self.ldflags_exe,
            (base.Compiler.EXECUTABLE, False): self.ldflags_exe,
            (base.Compiler.EXECUTABLE, True): self.ldflags_exe_debug,
            (base.Compiler.SHARED_OBJECT, None): self.ldflags_shared,
            (base.Compiler.SHARED_OBJECT, False): self.ldflags_shared,
            (base.Compiler.SHARED_OBJECT, True): self.ldflags_shared_debug,
            (base.Compiler.SHARED_LIBRARY, None): self.ldflags_static,
            (base.Compiler.SHARED_LIBRARY, False): self.ldflags_static,
            (base.Compiler.SHARED_LIBRARY, True): self.ldflags_static_debug,
        }

        self.initialized = True

    # 040229.python.msvc.line360.comment -- Worker methods ------------------------------------------------

    @property
    def out_extensions(self) -> dict[str, str]:
        return {
            **super().out_extensions,
            **{
                ext: self.res_extension
                for ext in self._rc_extensions + self._mc_extensions
            },
        }

    def compile(  # noqa: C901
        self,
        sources,
        output_dir=None,
        macros=None,
        include_dirs=None,
        debug=False,
        extra_preargs=None,
        extra_postargs=None,
        depends=None,
    ):
        if not self.initialized:
            self.initialize()
        compile_info = self._setup_compile(
            output_dir, macros, include_dirs, sources, depends, extra_postargs
        )
        macros, objects, extra_postargs, pp_opts, build = compile_info

        compile_opts = extra_preargs or []
        compile_opts.append('/c')
        if debug:
            compile_opts.extend(self.compile_options_debug)
        else:
            compile_opts.extend(self.compile_options)

        add_cpp_opts = False

        for obj in objects:
            try:
                src, ext = build[obj]
            except KeyError:
                continue
            if debug:
                # 040231.python.msvc.line405.comment pass the full pathname to MSVC in debug mode,
                # 040232.python.msvc.line406.comment this allows the debugger to find the source file
                # 040233.python.msvc.line407.comment without asking the user to browse for it
                src = os.path.abspath(src)

            if ext in self._c_extensions:
                input_opt = f"/Tc{src}"
            elif ext in self._cpp_extensions:
                input_opt = f"/Tp{src}"
                add_cpp_opts = True
            elif ext in self._rc_extensions:
                # 040234.python.msvc.line416.comment compile .RC to .RES file
                input_opt = src
                output_opt = "/fo" + obj
                try:
                    self.spawn([self.rc] + pp_opts + [output_opt, input_opt])
                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue
            elif ext in self._mc_extensions:
                # 040235.python.msvc.line425.comment Compile .MC to .RC file to .RES file.
                # 040236.python.msvc.line426.comment * '-h dir' specifies the directory for the
                # 040237.python.msvc.line427.comment generated include file
                # 040238.python.msvc.line428.comment * '-r dir' specifies the target directory of the
                # 040239.python.msvc.line429.comment generated RC file and the binary message resource
                # 040240.python.msvc.line430.comment it includes
                # 040241.python.msvc.line431.comment
                # 040242.python.msvc.line432.comment For now (since there are no options to change this),
                # 040243.python.msvc.line433.comment we use the source-directory for the include file and
                # 040244.python.msvc.line434.comment the build directory for the RC file and message
                # 040245.python.msvc.line435.comment resources. This works at least for win32all.
                h_dir = os.path.dirname(src)
                rc_dir = os.path.dirname(obj)
                try:
                    # 040246.python.msvc.line439.comment first compile .MC to .RC and .H file
                    self.spawn([self.mc, '-h', h_dir, '-r', rc_dir, src])
                    base, _ = os.path.splitext(os.path.basename(src))
                    rc_file = os.path.join(rc_dir, base + '.rc')
                    # 040247.python.msvc.line443.comment then compile .RC to .RES file
                    self.spawn([self.rc, "/fo" + obj, rc_file])

                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue
            else:
                # 040248.python.msvc.line450.comment how to handle this file?
                raise CompileError(f"Don't know how to compile {src} to {obj}")

            args = [self.cc] + compile_opts + pp_opts
            if add_cpp_opts:
                args.append('/EHsc')
            args.extend((input_opt, "/Fo" + obj))
            args.extend(extra_postargs)

            try:
                self.spawn(args)
            except DistutilsExecError as msg:
                raise CompileError(msg)

        return objects

    def create_static_lib(
        self,
        objects: list[str] | tuple[str, ...],
        output_libname: str,
        output_dir: str | None = None,
        debug: bool = False,
        target_lang: str | None = None,
    ) -> None:
        if not self.initialized:
            self.initialize()
        objects, output_dir = self._fix_object_args(objects, output_dir)
        output_filename = self.library_filename(output_libname, output_dir=output_dir)

        if self._need_link(objects, output_filename):
            lib_args = objects + ['/OUT:' + output_filename]
            if debug:
                pass  # XXX what goes here?
            try:
                log.debug('Executing "%s" %s', self.lib, ' '.join(lib_args))
                self.spawn([self.lib] + lib_args)
            except DistutilsExecError as msg:
                raise LibError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    def link(
        self,
        target_desc: str,
        objects: list[str] | tuple[str, ...],
        output_filename: str,
        output_dir: str | None = None,
        libraries: list[str] | tuple[str, ...] | None = None,
        library_dirs: list[str] | tuple[str, ...] | None = None,
        runtime_library_dirs: list[str] | tuple[str, ...] | None = None,
        export_symbols: Iterable[str] | None = None,
        debug: bool = False,
        extra_preargs: list[str] | None = None,
        extra_postargs: Iterable[str] | None = None,
        build_temp: str | os.PathLike[str] | None = None,
        target_lang: str | None = None,
    ) -> None:
        if not self.initialized:
            self.initialize()
        objects, output_dir = self._fix_object_args(objects, output_dir)
        fixed_args = self._fix_lib_args(libraries, library_dirs, runtime_library_dirs)
        libraries, library_dirs, runtime_library_dirs = fixed_args

        if runtime_library_dirs:
            self.warn(
                "I don't know what to do with 'runtime_library_dirs': "
                + str(runtime_library_dirs)
            )

        lib_opts = gen_lib_options(self, library_dirs, runtime_library_dirs, libraries)
        if output_dir is not None:
            output_filename = os.path.join(output_dir, output_filename)

        if self._need_link(objects, output_filename):
            ldflags = self._ldflags[target_desc, debug]

            export_opts = ["/EXPORT:" + sym for sym in (export_symbols or [])]

            ld_args = (
                ldflags + lib_opts + export_opts + objects + ['/OUT:' + output_filename]
            )

            # 040250.python.msvc.line532.comment The MSVC linker generates .lib and .exp files, which cannot be
            # 040251.python.msvc.line533.comment suppressed by any linker switches. The .lib files may even be
            # 040252.python.msvc.line534.comment needed! Make sure they are generated in the temporary build
            # 040253.python.msvc.line535.comment directory. Since they have different names for debug and release
            # 040254.python.msvc.line536.comment builds, they can go into the same directory.
            build_temp = os.path.dirname(objects[0])
            if export_symbols is not None:
                (dll_name, dll_ext) = os.path.splitext(
                    os.path.basename(output_filename)
                )
                implib_file = os.path.join(build_temp, self.library_filename(dll_name))
                ld_args.append('/IMPLIB:' + implib_file)

            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)

            output_dir = os.path.dirname(os.path.abspath(output_filename))
            self.mkpath(output_dir)
            try:
                log.debug('Executing "%s" %s', self.linker, ' '.join(ld_args))
                self.spawn([self.linker] + ld_args)
            except DistutilsExecError as msg:
                raise LinkError(msg)
        else:
            log.debug("skipping %s (up-to-date)", output_filename)

    def spawn(self, cmd):
        env = dict(os.environ, PATH=self._paths)
        with self._fallback_spawn(cmd, env) as fallback:
            return super().spawn(cmd, env=env)
        return fallback.value

    @contextlib.contextmanager
    def _fallback_spawn(self, cmd, env):
        """
        Discovered in pypa/distutils#15, some tools monkeypatch the compiler,
        so the 'env' kwarg causes a TypeError. Detect this condition and
        restore the legacy, unsafe behavior.
        """
        bag = type('Bag', (), {})()
        try:
            yield bag
        except TypeError as exc:
            if "unexpected keyword argument 'env'" not in str(exc):
                raise
        else:
            return
        warnings.warn("Fallback spawn triggered. Please update distutils monkeypatch.")
        with mock.patch.dict('os.environ', env):
            bag.value = super().spawn(cmd)

    # 040255.python.msvc.line585.comment -- Miscellaneous methods -----------------------------------------
    # 040256.python.msvc.line586.comment These are all used by the 'gen_lib_options() function, in
    # 040257.python.msvc.line587.comment ccompiler.py.

    def library_dir_option(self, dir):
        return "/LIBPATH:" + dir

    def runtime_library_dir_option(self, dir):
        raise DistutilsPlatformError(
            "don't know how to set runtime library search path for MSVC"
        )

    def library_option(self, lib):
        return self.library_filename(lib)

    def find_library_file(self, dirs, lib, debug=False):
        # 040258.python.msvc.line601.comment Prefer a debugging library if found (and requested), but deal
        # 040259.python.msvc.line602.comment with it if we don't have one.
        if debug:
            try_names = [lib + "_d", lib]
        else:
            try_names = [lib]
        for dir in dirs:
            for name in try_names:
                libfile = os.path.join(dir, self.library_filename(name))
                if os.path.isfile(libfile):
                    return libfile
        else:
            # 040260.python.msvc.line613.comment Oops, didn't find it in *any* of 'dirs'
            return None
