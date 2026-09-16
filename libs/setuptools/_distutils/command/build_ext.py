"""distutils.command.build_ext

Implements the Distutils 'build_ext' command, for building extension
modules (currently limited to C extensions, should accommodate C++
extensions ASAP)."""

from __future__ import annotations

import contextlib
import os
import re
import sys
from collections.abc import Callable
from distutils._log import log
from site import USER_BASE
from typing import ClassVar

from .._modified import newer_group
from ..ccompiler import new_compiler, show_compilers
from ..core import Command
from ..errors import (
    CCompilerError,
    CompileError,
    DistutilsError,
    DistutilsOptionError,
    DistutilsPlatformError,
    DistutilsSetupError,
)
from ..extension import Extension
from ..sysconfig import customize_compiler, get_config_h_filename, get_python_version
from ..util import get_platform, is_freethreaded, is_mingw

# 039451.python.build_ext.line33.comment An extension name is just a dot-separated list of Python NAMEs (ie.
# 039452.python.build_ext.line34.comment the same as a fully-qualified module name).
extension_name_re = re.compile(r'^[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*$')


class build_ext(Command):
    description = "build C/C++ extensions (compile/link to build directory)"

    # 039453.python.build_ext.line41.comment XXX thoughts on how to deal with complex command-line options like
    # 039454.python.build_ext.line42.comment these, i.e. how to make it so fancy_getopt can suck them off the
    # 039455.python.build_ext.line43.comment command line and make it look like setup.py defined the appropriate
    # 039456.python.build_ext.line44.comment lists of tuples of what-have-you.
    # 039457.python.build_ext.line45.comment - each command needs a callback to process its command-line options
    # 039458.python.build_ext.line46.comment - Command.__init__() needs access to its share of the whole
    # 039459.python.build_ext.line47.comment command line (must ultimately come from
    # 039460.python.build_ext.line48.comment Distribution.parse_command_line())
    # 039461.python.build_ext.line49.comment - it then calls the current command class' option-parsing
    # 039462.python.build_ext.line50.comment callback to deal with weird options like -D, which have to
    # 039463.python.build_ext.line51.comment parse the option text and churn out some custom data
    # 039464.python.build_ext.line52.comment structure
    # 039465.python.build_ext.line53.comment - that data structure (in this case, a list of 2-tuples)
    # 039466.python.build_ext.line54.comment will then be present in the command object by the time
    # 039467.python.build_ext.line55.comment we get to finalize_options() (i.e. the constructor
    # 039468.python.build_ext.line56.comment takes care of both command-line and client options
    # 039469.python.build_ext.line57.comment in between initialize_options() and finalize_options())

    sep_by = f" (separated by '{os.pathsep}')"
    user_options = [
        ('build-lib=', 'b', "directory for compiled extension modules"),
        ('build-temp=', 't', "directory for temporary files (build by-products)"),
        (
            'plat-name=',
            'p',
            "platform name to cross-compile for, if supported "
            f"[default: {get_platform()}]",
        ),
        (
            'inplace',
            'i',
            "ignore build-lib and put compiled extensions into the source "
            "directory alongside your pure Python modules",
        ),
        (
            'include-dirs=',
            'I',
            "list of directories to search for header files" + sep_by,
        ),
        ('define=', 'D', "C preprocessor macros to define"),
        ('undef=', 'U', "C preprocessor macros to undefine"),
        ('libraries=', 'l', "external C libraries to link with"),
        (
            'library-dirs=',
            'L',
            "directories to search for external C libraries" + sep_by,
        ),
        ('rpath=', 'R', "directories to search for shared C libraries at runtime"),
        ('link-objects=', 'O', "extra explicit link objects to include in the link"),
        ('debug', 'g', "compile/link with debugging information"),
        ('force', 'f', "forcibly build everything (ignore file timestamps)"),
        ('compiler=', 'c', "specify the compiler type"),
        ('parallel=', 'j', "number of parallel build jobs"),
        ('swig-cpp', None, "make SWIG create C++ files (default is C)"),
        ('swig-opts=', None, "list of SWIG command line options"),
        ('swig=', None, "path to the SWIG executable"),
        ('user', None, "add user include, library and rpath"),
    ]

    boolean_options: ClassVar[list[str]] = [
        'inplace',
        'debug',
        'force',
        'swig-cpp',
        'user',
    ]

    help_options: ClassVar[list[tuple[str, str | None, str, Callable[[], object]]]] = [
        ('help-compiler', None, "list available compilers", show_compilers),
    ]

    def initialize_options(self):
        self.extensions = None
        self.build_lib = None
        self.plat_name = None
        self.build_temp = None
        self.inplace = False
        self.package = None

        self.include_dirs = None
        self.define = None
        self.undef = None
        self.libraries = None
        self.library_dirs = None
        self.rpath = None
        self.link_objects = None
        self.debug = None
        self.force = None
        self.compiler = None
        self.swig = None
        self.swig_cpp = None
        self.swig_opts = None
        self.user = None
        self.parallel = None

    @staticmethod
    def _python_lib_dir(sysconfig):
        """
        Resolve Python's library directory for building extensions
        that rely on a shared Python library.

        See python/cpython#44264 and python/cpython#48686
        """
        if not sysconfig.get_config_var('Py_ENABLE_SHARED'):
            return

        if sysconfig.python_build:
            yield '.'
            return

        if sys.platform == 'zos':
            # 039470.python.build_ext.line152.comment On z/OS, a user is not required to install Python to
            # 039471.python.build_ext.line153.comment a predetermined path, but can use Python portably
            installed_dir = sysconfig.get_config_var('base')
            lib_dir = sysconfig.get_config_var('platlibdir')
            yield os.path.join(installed_dir, lib_dir)
        else:
            # 039472.python.build_ext.line158.comment building third party extensions
            yield sysconfig.get_config_var('LIBDIR')

    def finalize_options(self) -> None:  # noqa: C901
        from distutils import sysconfig

        self.set_undefined_options(
            'build',
            ('build_lib', 'build_lib'),
            ('build_temp', 'build_temp'),
            ('compiler', 'compiler'),
            ('debug', 'debug'),
            ('force', 'force'),
            ('parallel', 'parallel'),
            ('plat_name', 'plat_name'),
        )

        if self.package is None:
            self.package = self.distribution.ext_package

        self.extensions = self.distribution.ext_modules

        # 039474.python.build_ext.line180.comment Make sure Python's include directories (for Python.h, pyconfig.h,
        # 039475.python.build_ext.line181.comment etc.) are in the include search path.
        py_include = sysconfig.get_python_inc()
        plat_py_include = sysconfig.get_python_inc(plat_specific=True)
        if self.include_dirs is None:
            self.include_dirs = self.distribution.include_dirs or []
        if isinstance(self.include_dirs, str):
            self.include_dirs = self.include_dirs.split(os.pathsep)

        # 039476.python.build_ext.line189.comment If in a virtualenv, add its include directory
        # 039477.python.build_ext.line190.comment Issue 16116
        if sys.exec_prefix != sys.base_exec_prefix:
            self.include_dirs.append(os.path.join(sys.exec_prefix, 'include'))

        # 039478.python.build_ext.line194.comment Put the Python "system" include dir at the end, so that
        # 039479.python.build_ext.line195.comment any local include dirs take precedence.
        self.include_dirs.extend(py_include.split(os.path.pathsep))
        if plat_py_include != py_include:
            self.include_dirs.extend(plat_py_include.split(os.path.pathsep))

        self.ensure_string_list('libraries')
        self.ensure_string_list('link_objects')

        # 039480.python.build_ext.line203.comment Life is easier if we're not forever checking for None, so
        # 039481.python.build_ext.line204.comment simplify these options to empty lists if unset
        if self.libraries is None:
            self.libraries = []
        if self.library_dirs is None:
            self.library_dirs = []
        elif isinstance(self.library_dirs, str):
            self.library_dirs = self.library_dirs.split(os.pathsep)

        if self.rpath is None:
            self.rpath = []
        elif isinstance(self.rpath, str):
            self.rpath = self.rpath.split(os.pathsep)

        # 039482.python.build_ext.line217.comment for extensions under windows use different directories
        # 039483.python.build_ext.line218.comment for Release and Debug builds.
        # 039484.python.build_ext.line219.comment also Python's library directory must be appended to library_dirs
        if os.name == 'nt' and not is_mingw():
            # 039485.python.build_ext.line221.comment the 'libs' directory is for binary installs - we assume that
            # 039486.python.build_ext.line222.comment must be the *native* platform.  But we don't really support
            # 039487.python.build_ext.line223.comment cross-compiling via a binary install anyway, so we let it go.
            self.library_dirs.append(os.path.join(sys.exec_prefix, 'libs'))
            if sys.base_exec_prefix != sys.prefix:  # Issue 16116
                self.library_dirs.append(os.path.join(sys.base_exec_prefix, 'libs'))
            if self.debug:
                self.build_temp = os.path.join(self.build_temp, "Debug")
            else:
                self.build_temp = os.path.join(self.build_temp, "Release")

            # 039489.python.build_ext.line232.comment Append the source distribution include and library directories,
            # 039490.python.build_ext.line233.comment this allows distutils on windows to work in the source tree
            self.include_dirs.append(os.path.dirname(get_config_h_filename()))
            self.library_dirs.append(sys.base_exec_prefix)

            # 039491.python.build_ext.line237.comment Use the .lib files for the correct architecture
            if self.plat_name == 'win32':
                suffix = 'win32'
            else:
                # 039492.python.build_ext.line241.comment win-amd64
                suffix = self.plat_name[4:]
            new_lib = os.path.join(sys.exec_prefix, 'PCbuild')
            if suffix:
                new_lib = os.path.join(new_lib, suffix)
            self.library_dirs.append(new_lib)

        # 039493.python.build_ext.line248.comment For extensions under Cygwin, Python's library directory must be
        # 039494.python.build_ext.line249.comment appended to library_dirs
        if sys.platform[:6] == 'cygwin':
            if not sysconfig.python_build:
                # 039495.python.build_ext.line252.comment building third party extensions
                self.library_dirs.append(
                    os.path.join(
                        sys.prefix, "lib", "python" + get_python_version(), "config"
                    )
                )
            else:
                # 039496.python.build_ext.line259.comment building python standard extensions
                self.library_dirs.append('.')

        self.library_dirs.extend(self._python_lib_dir(sysconfig))

        # 039497.python.build_ext.line264.comment The argument parsing will result in self.define being a string, but
        # 039498.python.build_ext.line265.comment it has to be a list of 2-tuples.  All the preprocessor symbols
        # 039499.python.build_ext.line266.comment specified by the 'define' option will be set to '1'.  Multiple
        # 039500.python.build_ext.line267.comment symbols can be separated with commas.

        if self.define:
            defines = self.define.split(',')
            self.define = [(symbol, '1') for symbol in defines]

        # 039501.python.build_ext.line273.comment The option for macros to undefine is also a string from the
        # 039502.python.build_ext.line274.comment option parsing, but has to be a list.  Multiple symbols can also
        # 039503.python.build_ext.line275.comment be separated with commas here.
        if self.undef:
            self.undef = self.undef.split(',')

        if self.swig_opts is None:
            self.swig_opts = []
        else:
            self.swig_opts = self.swig_opts.split(' ')

        # 039504.python.build_ext.line284.comment Finally add the user include and library directories if requested
        if self.user:
            user_include = os.path.join(USER_BASE, "include")
            user_lib = os.path.join(USER_BASE, "lib")
            if os.path.isdir(user_include):
                self.include_dirs.append(user_include)
            if os.path.isdir(user_lib):
                self.library_dirs.append(user_lib)
                self.rpath.append(user_lib)

        if isinstance(self.parallel, str):
            try:
                self.parallel = int(self.parallel)
            except ValueError:
                raise DistutilsOptionError("parallel should be an integer")

    def run(self) -> None:  # noqa: C901
        # 039506.python.build_ext.line301.comment 'self.extensions', as supplied by setup.py, is a list of
        # 039507.python.build_ext.line302.comment Extension instances.  See the documentation for Extension (in
        # 039508.python.build_ext.line303.comment distutils.extension) for details.
        # 039509.python.build_ext.line304.comment
        # 039510.python.build_ext.line305.comment For backwards compatibility with Distutils 0.8.2 and earlier, we
        # 039511.python.build_ext.line306.comment also allow the 'extensions' list to be a list of tuples:
        # 039512.python.build_ext.line307.comment (ext_name, build_info)
        # 039513.python.build_ext.line308.comment where build_info is a dictionary containing everything that
        # 039514.python.build_ext.line309.comment Extension instances do except the name, with a few things being
        # 039515.python.build_ext.line310.comment differently named.  We convert these 2-tuples to Extension
        # 039516.python.build_ext.line311.comment instances as needed.

        if not self.extensions:
            return

        # 039517.python.build_ext.line316.comment If we were asked to build any C/C++ libraries, make sure that the
        # 039518.python.build_ext.line317.comment directory where we put them is in the library search path for
        # 039519.python.build_ext.line318.comment linking extensions.
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.libraries.extend(build_clib.get_library_names() or [])
            self.library_dirs.append(build_clib.build_clib)

        # 039520.python.build_ext.line324.comment Setup the CCompiler object that we'll use to do all the
        # 039521.python.build_ext.line325.comment compiling and linking
        self.compiler = new_compiler(
            compiler=self.compiler,
            verbose=self.verbose,
            dry_run=self.dry_run,
            force=self.force,
        )
        customize_compiler(self.compiler)
        # 039522.python.build_ext.line333.comment If we are cross-compiling, init the compiler now (if we are not
        # 039523.python.build_ext.line334.comment cross-compiling, init would not hurt, but people may rely on
        # 039524.python.build_ext.line335.comment late initialization of compiler even if they shouldn't...)
        if os.name == 'nt' and self.plat_name != get_platform():
            self.compiler.initialize(self.plat_name)

        # 039525.python.build_ext.line339.comment The official Windows free threaded Python installer doesn't set
        # 039526.python.build_ext.line340.comment Py_GIL_DISABLED because its pyconfig.h is shared with the
        # 039527.python.build_ext.line341.comment default build, so define it here (pypa/setuptools#4662).
        if os.name == 'nt' and is_freethreaded():
            self.compiler.define_macro('Py_GIL_DISABLED', '1')

        # 039528.python.build_ext.line345.comment And make sure that any compile/link-related options (which might
        # 039529.python.build_ext.line346.comment come from the command-line or from the setup script) are set in
        # 039530.python.build_ext.line347.comment that CCompiler object -- that way, they automatically apply to
        # 039531.python.build_ext.line348.comment all compiling and linking done here.
        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 039532.python.build_ext.line352.comment 'define' option is a list of (name,value) tuples
            for name, value in self.define:
                self.compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                self.compiler.undefine_macro(macro)
        if self.libraries is not None:
            self.compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            self.compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            self.compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            self.compiler.set_link_objects(self.link_objects)

        # 039533.python.build_ext.line367.comment Now actually compile and link everything.
        self.build_extensions()

    def check_extensions_list(self, extensions) -> None:  # noqa: C901
        """Ensure that the list of extensions (presumably provided as a
        command option 'extensions') is valid, i.e. it is a list of
        Extension objects.  We also support the old-style list of 2-tuples,
        where the tuples are (ext_name, build_info), which are converted to
        Extension instances here.

        Raise DistutilsSetupError if the structure is invalid anywhere;
        just returns otherwise.
        """
        if not isinstance(extensions, list):
            raise DistutilsSetupError(
                "'ext_modules' option must be a list of Extension instances"
            )

        for i, ext in enumerate(extensions):
            if isinstance(ext, Extension):
                continue  # OK! (assume type-checking done
                # 039536.python.build_ext.line388.comment by Extension constructor)

            if not isinstance(ext, tuple) or len(ext) != 2:
                raise DistutilsSetupError(
                    "each element of 'ext_modules' option must be an "
                    "Extension instance or 2-tuple"
                )

            ext_name, build_info = ext

            log.warning(
                "old-style (ext_name, build_info) tuple found in "
                "ext_modules for extension '%s' "
                "-- please convert to Extension instance",
                ext_name,
            )

            if not (isinstance(ext_name, str) and extension_name_re.match(ext_name)):
                raise DistutilsSetupError(
                    "first element of each tuple in 'ext_modules' "
                    "must be the extension name (a string)"
                )

            if not isinstance(build_info, dict):
                raise DistutilsSetupError(
                    "second element of each tuple in 'ext_modules' "
                    "must be a dictionary (build info)"
                )

            # 039537.python.build_ext.line417.comment OK, the (ext_name, build_info) dict is type-safe: convert it
            # 039538.python.build_ext.line418.comment to an Extension instance.
            ext = Extension(ext_name, build_info['sources'])

            # 039539.python.build_ext.line421.comment Easy stuff: one-to-one mapping from dict elements to
            # 039540.python.build_ext.line422.comment instance attributes.
            for key in (
                'include_dirs',
                'library_dirs',
                'libraries',
                'extra_objects',
                'extra_compile_args',
                'extra_link_args',
            ):
                val = build_info.get(key)
                if val is not None:
                    setattr(ext, key, val)

            # 039541.python.build_ext.line435.comment Medium-easy stuff: same syntax/semantics, different names.
            ext.runtime_library_dirs = build_info.get('rpath')
            if 'def_file' in build_info:
                log.warning("'def_file' element of build info dict no longer supported")

            # 039542.python.build_ext.line440.comment Non-trivial stuff: 'macros' split into 'define_macros'
            # 039543.python.build_ext.line441.comment and 'undef_macros'.
            macros = build_info.get('macros')
            if macros:
                ext.define_macros = []
                ext.undef_macros = []
                for macro in macros:
                    if not (isinstance(macro, tuple) and len(macro) in (1, 2)):
                        raise DistutilsSetupError(
                            "'macros' element of build info dict must be 1- or 2-tuple"
                        )
                    if len(macro) == 1:
                        ext.undef_macros.append(macro[0])
                    elif len(macro) == 2:
                        ext.define_macros.append(macro)

            extensions[i] = ext

    def get_source_files(self):
        self.check_extensions_list(self.extensions)
        filenames = []

        # 039544.python.build_ext.line462.comment Wouldn't it be neat if we knew the names of header files too...
        for ext in self.extensions:
            filenames.extend(ext.sources)
        return filenames

    def get_outputs(self):
        # 039545.python.build_ext.line468.comment Sanity check the 'extensions' list -- can't assume this is being
        # 039546.python.build_ext.line469.comment done in the same run as a 'build_extensions()' call (in fact, we
        # 039547.python.build_ext.line470.comment can probably assume that it *isn't*!).
        self.check_extensions_list(self.extensions)

        # 039548.python.build_ext.line473.comment And build the list of output (built) filenames.  Note that this
        # 039549.python.build_ext.line474.comment ignores the 'inplace' flag, and assumes everything goes in the
        # 039550.python.build_ext.line475.comment "build" tree.
        return [self.get_ext_fullpath(ext.name) for ext in self.extensions]

    def build_extensions(self) -> None:
        # 039551.python.build_ext.line479.comment First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)
        if self.parallel:
            self._build_extensions_parallel()
        else:
            self._build_extensions_serial()

    def _build_extensions_parallel(self):
        workers = self.parallel
        if self.parallel is True:
            workers = os.cpu_count()  # may return None
        try:
            from concurrent.futures import ThreadPoolExecutor
        except ImportError:
            workers = None

        if workers is None:
            self._build_extensions_serial()
            return

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self.build_extension, ext) for ext in self.extensions
            ]
            for ext, fut in zip(self.extensions, futures):
                with self._filter_build_errors(ext):
                    fut.result()

    def _build_extensions_serial(self):
        for ext in self.extensions:
            with self._filter_build_errors(ext):
                self.build_extension(ext)

    @contextlib.contextmanager
    def _filter_build_errors(self, ext):
        try:
            yield
        except (CCompilerError, DistutilsError, CompileError) as e:
            if not ext.optional:
                raise
            self.warn(f'building extension "{ext.name}" failed: {e}')

    def build_extension(self, ext) -> None:
        sources = ext.sources
        if sources is None or not isinstance(sources, (list, tuple)):
            raise DistutilsSetupError(
                f"in 'ext_modules' option (extension '{ext.name}'), "
                "'sources' must be present and must be "
                "a list of source filenames"
            )
        # 039553.python.build_ext.line529.comment sort to make the resulting .so file build reproducible
        sources = sorted(sources)

        ext_path = self.get_ext_fullpath(ext.name)
        depends = sources + ext.depends
        if not (self.force or newer_group(depends, ext_path, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return
        else:
            log.info("building '%s' extension", ext.name)

        # 039554.python.build_ext.line540.comment First, scan the sources for SWIG definition files (.i), run
        # 039555.python.build_ext.line541.comment SWIG on 'em to create .c files, and modify the sources list
        # 039556.python.build_ext.line542.comment accordingly.
        sources = self.swig_sources(sources, ext)

        # 039557.python.build_ext.line545.comment Next, compile the source code to object files.

        # 039558.python.build_ext.line547.comment XXX not honouring 'define_macros' or 'undef_macros' -- the
        # 039559.python.build_ext.line548.comment CCompiler API needs to change to accommodate this, and I
        # 039560.python.build_ext.line549.comment want to do one thing at a time!

        # 039561.python.build_ext.line551.comment Two possible sources for extra compiler arguments:
        # 039562.python.build_ext.line552.comment - 'extra_compile_args' in Extension object
        # 039563.python.build_ext.line553.comment - CFLAGS environment variable (not particularly
        # 039564.python.build_ext.line554.comment elegant, but people seem to expect it and I
        # 039565.python.build_ext.line555.comment guess it's useful)
        # 039566.python.build_ext.line556.comment The environment variable should take precedence, and
        # 039567.python.build_ext.line557.comment any sensible compiler will give precedence to later
        # 039568.python.build_ext.line558.comment command line args.  Hence we combine them in order:
        extra_args = ext.extra_compile_args or []

        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        objects = self.compiler.compile(
            sources,
            output_dir=self.build_temp,
            macros=macros,
            include_dirs=ext.include_dirs,
            debug=self.debug,
            extra_postargs=extra_args,
            depends=ext.depends,
        )

        # 039569.python.build_ext.line575.comment XXX outdated variable, kept here in case third-part code
        # 039570.python.build_ext.line576.comment needs it.
        self._built_objects = objects[:]

        # 039571.python.build_ext.line579.comment Now link the object files together into a "shared object" --
        # 039572.python.build_ext.line580.comment of course, first we have to figure out all the other things
        # 039573.python.build_ext.line581.comment that go into the mix.
        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []

        # 039574.python.build_ext.line586.comment Detect target language, if not provided
        language = ext.language or self.compiler.detect_language(sources)

        self.compiler.link_shared_object(
            objects,
            ext_path,
            libraries=self.get_libraries(ext),
            library_dirs=ext.library_dirs,
            runtime_library_dirs=ext.runtime_library_dirs,
            extra_postargs=extra_args,
            export_symbols=self.get_export_symbols(ext),
            debug=self.debug,
            build_temp=self.build_temp,
            target_lang=language,
        )

    def swig_sources(self, sources, extension):
        """Walk the list of source files in 'sources', looking for SWIG
        interface (.i) files.  Run SWIG on all that are found, and
        return a modified 'sources' list with SWIG source files replaced
        by the generated C (or C++) files.
        """
        new_sources = []
        swig_sources = []
        swig_targets = {}

        # 039575.python.build_ext.line612.comment XXX this drops generated C/C++ files into the source tree, which
        # 039576.python.build_ext.line613.comment is fine for developers who want to distribute the generated
        # 039577.python.build_ext.line614.comment source -- but there should be an option to put SWIG output in
        # 039578.python.build_ext.line615.comment the temp dir.

        if self.swig_cpp:
            log.warning("--swig-cpp is deprecated - use --swig-opts=-c++")

        if (
            self.swig_cpp
            or ('-c++' in self.swig_opts)
            or ('-c++' in extension.swig_opts)
        ):
            target_ext = '.cpp'
        else:
            target_ext = '.c'

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == ".i":  # SWIG interface file
                new_sources.append(base + '_wrap' + target_ext)
                swig_sources.append(source)
                swig_targets[source] = new_sources[-1]
            else:
                new_sources.append(source)

        if not swig_sources:
            return new_sources

        swig = self.swig or self.find_swig()
        swig_cmd = [swig, "-python"]
        swig_cmd.extend(self.swig_opts)
        if self.swig_cpp:
            swig_cmd.append("-c++")

        # 039580.python.build_ext.line647.comment Do not override commandline arguments
        if not self.swig_opts:
            swig_cmd.extend(extension.swig_opts)

        for source in swig_sources:
            target = swig_targets[source]
            log.info("swigging %s to %s", source, target)
            self.spawn(swig_cmd + ["-o", target, source])

        return new_sources

    def find_swig(self):
        """Return the name of the SWIG executable.  On Unix, this is
        just "swig" -- it should be in the PATH.  Tries a bit harder on
        Windows.
        """
        if os.name == "posix":
            return "swig"
        elif os.name == "nt":
            # 039581.python.build_ext.line666.comment Look for SWIG in its standard installation directory on
            # 039582.python.build_ext.line667.comment Windows (or so I presume!).  If we find it there, great;
            # 039583.python.build_ext.line668.comment if not, act like Unix and assume it's in the PATH.
            for vers in ("1.3", "1.2", "1.1"):
                fn = os.path.join(f"c:\\swig{vers}", "swig.exe")
                if os.path.isfile(fn):
                    return fn
            else:
                return "swig.exe"
        else:
            raise DistutilsPlatformError(
                f"I don't know how to find (much less run) SWIG on platform '{os.name}'"
            )

    # 039584.python.build_ext.line680.comment -- Name generators -----------------------------------------------
    # 039585.python.build_ext.line681.comment (extension names, filenames, whatever)
    def get_ext_fullpath(self, ext_name: str) -> str:
        """Returns the path of the filename for a given extension.

        The file is located in `build_lib` or directly in the package
        (inplace option).
        """
        fullname = self.get_ext_fullname(ext_name)
        modpath = fullname.split('.')
        filename = self.get_ext_filename(modpath[-1])

        if not self.inplace:
            # 039586.python.build_ext.line693.comment no further work needed
            # 039587.python.build_ext.line694.comment returning :
            # 039588.python.build_ext.line695.comment build_dir/package/path/filename
            filename = os.path.join(*modpath[:-1] + [filename])
            return os.path.join(self.build_lib, filename)

        # 039589.python.build_ext.line699.comment the inplace option requires to find the package directory
        # 039590.python.build_ext.line700.comment using the build_py command for that
        package = '.'.join(modpath[0:-1])
        build_py = self.get_finalized_command('build_py')
        package_dir = os.path.abspath(build_py.get_package_dir(package))

        # 039591.python.build_ext.line705.comment returning
        # 039592.python.build_ext.line706.comment package_dir/filename
        return os.path.join(package_dir, filename)

    def get_ext_fullname(self, ext_name: str) -> str:
        """Returns the fullname of a given extension name.

        Adds the `package.` prefix"""
        if self.package is None:
            return ext_name
        else:
            return self.package + '.' + ext_name

    def get_ext_filename(self, ext_name: str) -> str:
        r"""Convert the name of an extension (eg. "foo.bar") into the name
        of the file from which it will be loaded (eg. "foo/bar.so", or
        "foo\bar.pyd").
        """
        from ..sysconfig import get_config_var

        ext_path = ext_name.split('.')
        ext_suffix = get_config_var('EXT_SUFFIX')
        return os.path.join(*ext_path) + ext_suffix

    def get_export_symbols(self, ext: Extension) -> list[str]:
        """Return the list of symbols that a shared extension has to
        export.  This either uses 'ext.export_symbols' or, if it's not
        provided, "PyInit_" + module_name.  Only relevant on Windows, where
        the .pyd file (DLL) must export the module "PyInit_" function.
        """
        name = self._get_module_name_for_symbol(ext)
        try:
            # 039593.python.build_ext.line737.comment Unicode module name support as defined in PEP-489
            # 039594.python.build_ext.line738.comment https://peps.python.org/pep-0489/#export-hook-name
            name.encode('ascii')
        except UnicodeEncodeError:
            suffix = 'U_' + name.encode('punycode').replace(b'-', b'_').decode('ascii')
        else:
            suffix = "_" + name

        initfunc_name = "PyInit" + suffix
        if initfunc_name not in ext.export_symbols:
            ext.export_symbols.append(initfunc_name)
        return ext.export_symbols

    def _get_module_name_for_symbol(self, ext):
        # 039595.python.build_ext.line751.comment Package name should be used for `__init__` modules
        # 039596.python.build_ext.line752.comment https://github.com/python/cpython/issues/80074
        # 039597.python.build_ext.line753.comment https://github.com/pypa/setuptools/issues/4826
        parts = ext.name.split(".")
        if parts[-1] == "__init__" and len(parts) >= 2:
            return parts[-2]
        return parts[-1]

    def get_libraries(self, ext: Extension) -> list[str]:  # noqa: C901
        """Return the list of libraries to link against when building a
        shared extension.  On most platforms, this is just 'ext.libraries';
        on Windows, we add the Python library (eg. python20.dll).
        """
        # 039599.python.build_ext.line764.comment The python library is always needed on Windows.  For MSVC, this
        # 039600.python.build_ext.line765.comment is redundant, since the library is mentioned in a pragma in
        # 039601.python.build_ext.line766.comment pyconfig.h that MSVC groks.  The other Windows compilers all seem
        # 039602.python.build_ext.line767.comment to need it mentioned explicitly, though, so that's what we do.
        # 039603.python.build_ext.line768.comment Append '_d' to the python import library on debug builds.
        if sys.platform == "win32" and not is_mingw():
            from .._msvccompiler import MSVCCompiler

            if not isinstance(self.compiler, MSVCCompiler):
                template = "python%d%d"
                if self.debug:
                    template = template + '_d'
                pythonlib = template % (
                    sys.hexversion >> 24,
                    (sys.hexversion >> 16) & 0xFF,
                )
                # 039604.python.build_ext.line780.comment don't extend ext.libraries, it may be shared with other
                # 039605.python.build_ext.line781.comment extensions, it is a reference to the original list
                return ext.libraries + [pythonlib]
        else:
            # 039606.python.build_ext.line784.comment On Android only the main executable and LD_PRELOADs are considered
            # 039607.python.build_ext.line785.comment to be RTLD_GLOBAL, all the dependencies of the main executable
            # 039608.python.build_ext.line786.comment remain RTLD_LOCAL and so the shared libraries must be linked with
            # 039609.python.build_ext.line787.comment libpython when python is built with a shared python library (issue
            # 039610.python.build_ext.line788.comment bpo-21536).
            # 039611.python.build_ext.line789.comment On Cygwin (and if required, other POSIX-like platforms based on
            # 039612.python.build_ext.line790.comment Windows like MinGW) it is simply necessary that all symbols in
            # 039613.python.build_ext.line791.comment shared libraries are resolved at link time.
            from ..sysconfig import get_config_var

            link_libpython = False
            if get_config_var('Py_ENABLE_SHARED'):
                # 039614.python.build_ext.line796.comment A native build on an Android device or on Cygwin
                if hasattr(sys, 'getandroidapilevel'):
                    link_libpython = True
                elif sys.platform == 'cygwin' or is_mingw():
                    link_libpython = True
                elif '_PYTHON_HOST_PLATFORM' in os.environ:
                    # 039615.python.build_ext.line802.comment We are cross-compiling for one of the relevant platforms
                    if get_config_var('ANDROID_API_LEVEL') != 0:
                        link_libpython = True
                    elif get_config_var('MACHDEP') == 'cygwin':
                        link_libpython = True

            if link_libpython:
                ldversion = get_config_var('LDVERSION')
                return ext.libraries + ['python' + ldversion]

        return ext.libraries
