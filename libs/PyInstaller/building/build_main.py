# 000653.python.build_main.line1.comment -----------------------------------------------------------------------------
# 000654.python.build_main.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 000655.python.build_main.line3.comment
# 000656.python.build_main.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000657.python.build_main.line5.comment or later) with exception for distributing the bootloader.
# 000658.python.build_main.line6.comment
# 000659.python.build_main.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000660.python.build_main.line8.comment
# 000661.python.build_main.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000662.python.build_main.line10.comment -----------------------------------------------------------------------------
"""
Build packages using spec files.

NOTE: All global variables, classes and imported modules create API for .spec files.
"""

import glob
import os
import pathlib
import pprint
import shutil
import enum
import re
import sys

from PyInstaller import DEFAULT_DISTPATH, DEFAULT_WORKPATH, HOMEPATH, compat
from PyInstaller import log as logging
from PyInstaller.building.api import COLLECT, EXE, MERGE, PYZ
from PyInstaller.building.datastruct import (
    TOC, Target, Tree, _check_guts_eq, normalize_toc, normalize_pyz_toc, toc_process_symbolic_links
)
from PyInstaller.building.osx import BUNDLE
from PyInstaller.building.splash import Splash
from PyInstaller.building.utils import (
    _check_guts_toc, _check_guts_toc_mtime, _should_include_system_binary, format_binaries_and_datas, compile_pymodule,
    destination_name_for_extension, postprocess_binaries_toc_pywin32, postprocess_binaries_toc_pywin32_anaconda,
    create_base_library_zip
)
from PyInstaller.compat import is_win, is_conda, is_darwin, is_linux
from PyInstaller.depend import bindepend
from PyInstaller.depend.analysis import initialize_modgraph, HOOK_PRIORITY_USER_HOOKS
from PyInstaller.depend.utils import scan_code_for_ctypes
from PyInstaller import isolated
from PyInstaller.utils.misc import absnormpath, get_path_to_toplevel_modules, mtime
from PyInstaller.utils.hooks import get_package_paths
from PyInstaller.utils.hooks.gi import compile_glib_schema_files

if is_darwin:
    from PyInstaller.utils import osx as osxutils

logger = logging.getLogger(__name__)

STRINGTYPE = type('')
TUPLETYPE = type((None,))

rthooks = {}

# 000663.python.build_main.line58.comment Place where the loader modules and initialization scripts live.
_init_code_path = os.path.join(HOMEPATH, 'PyInstaller', 'loader')

IMPORT_TYPES = [
    'top-level', 'conditional', 'delayed', 'delayed, conditional', 'optional', 'conditional, optional',
    'delayed, optional', 'delayed, conditional, optional'
]

WARNFILE_HEADER = """\

This file lists modules PyInstaller was not able to find. This does not
necessarily mean this module is required for running your program. Python and
Python 3rd-party packages include a lot of conditional or optional modules. For
example the module 'ntpath' only exists on Windows, whereas the module
'posixpath' only exists on Posix systems.

Types if import:
* top-level: imported at the top-level - look at these first
* conditional: imported within an if-statement
* delayed: imported within a function
* optional: imported within a try-except-statement

IMPORTANT: Do NOT post this list to the issue-tracker. Use it as a basis for
            tracking down the missing module yourself. Thanks!

"""


@isolated.decorate
def discover_hook_directories():
    """
    Discover hook directories via pyinstaller40 entry points. Perform the discovery in an isolated subprocess
    to avoid importing the package(s) in the main process.

    :return: list of discovered hook directories.
    """

    from traceback import format_exception_only
    from PyInstaller.log import logger
    from PyInstaller.compat import importlib_metadata
    from PyInstaller.depend.analysis import HOOK_PRIORITY_CONTRIBUTED_HOOKS, HOOK_PRIORITY_UPSTREAM_HOOKS

    # 000664.python.build_main.line100.comment The “selectable” entry points (via group and name keyword args) were introduced in importlib_metadata 4.6 and
    # 000665.python.build_main.line101.comment Python 3.10. The compat module ensures we are using a compatible version.
    entry_points = importlib_metadata.entry_points(group='pyinstaller40', name='hook-dirs')

    # 000666.python.build_main.line104.comment Ensure that pyinstaller_hooks_contrib comes last so that hooks from packages providing their own take priority.
    # 000667.python.build_main.line105.comment In pyinstaller-hooks-contrib >= 2024.8, the entry-point module is `_pyinstaller_hooks_contrib`; in earlier
    # 000668.python.build_main.line106.comment versions, it was `_pyinstaller_hooks_contrib.hooks`.
    entry_points = sorted(entry_points, key=lambda x: x.module.startswith("_pyinstaller_hooks_contrib"))

    hook_directories = []
    for entry_point in entry_points:
        # 000669.python.build_main.line111.comment Query hook directory location(s) from entry point
        try:
            hook_directory_entries = entry_point.load()()
        except Exception as e:
            msg = "".join(format_exception_only(type(e), e)).strip()
            logger.warning("discover_hook_directories: Failed to process hook entry point '%s': %s", entry_point, msg)
            continue

        # 000670.python.build_main.line119.comment Determine location-based priority: upstream hooks vs. hooks from contributed hooks package.
        location_priority = (
            HOOK_PRIORITY_CONTRIBUTED_HOOKS
            if entry_point.module.startswith("_pyinstaller_hooks_contrib") else HOOK_PRIORITY_UPSTREAM_HOOKS
        )

        # 000671.python.build_main.line125.comment Append entries
        hook_directories.extend([(hook_directory_entry, location_priority)
                                 for hook_directory_entry in hook_directory_entries])

    logger.debug("discover_hook_directories: Hook directories: %s", hook_directories)

    return hook_directories


def find_binary_dependencies(binaries, import_packages, symlink_suppression_patterns):
    """
    Find dynamic dependencies (linked shared libraries) for the provided list of binaries.

    On Windows, this function performs additional pre-processing in an isolated environment in an attempt to handle
    dynamic library search path modifications made by packages during their import. The packages from the given list
    of collected packages are imported one by one, while keeping track of modifications made by `os.add_dll_directory`
    calls and additions to the `PATH`  environment variable. The recorded additional search paths are then passed to
    the binary dependency analysis step.

    binaries
            List of binaries to scan for dynamic dependencies.
    import_packages
            List of packages to import prior to scanning binaries.
    symlink_suppression_patterns
            Set of paths and/or path patterns for which binary dependency analysis should not create symbolic links
            to the top-level application directory (when the discovered shared library's parent directory structure
            is preserved). When binary dependency analysis discovers a shared library, it matches its *source path*
            against all symlink suppression patterns (using `pathlib.PurePath.match`) to determine whether to create
            a symbolic link to top-level application directory or not.

    :return: expanded list of binaries and then dependencies.
    """

    # 000672.python.build_main.line158.comment Extra library search paths (used on Windows to resolve DLL paths).
    extra_libdirs = []
    if compat.is_win:
        # 000673.python.build_main.line161.comment Always search `sys.base_prefix`, and search it first. This ensures that we resolve the correct version of
        # 000674.python.build_main.line162.comment `python3X.dll` and `python3.dll` (a PEP-0384 stable ABI stub that forwards symbols to the fully versioned
        # 000675.python.build_main.line163.comment `python3X.dll`), regardless of other python installations that might be present in the PATH.
        extra_libdirs.append(compat.base_prefix)

        # 000676.python.build_main.line166.comment When using python built from source, `sys.base_prefix` does not point to the directory that contains python
        # 000677.python.build_main.line167.comment executable, `python3X.dll`, and `python3.dll`. To accommodate such case, also add the directory in which
        # 000678.python.build_main.line168.comment python executable is located to the extra search paths. On the off-chance that this is a combination of venv
        # 000679.python.build_main.line169.comment and python built from source, prefer `sys._base_executable` over `sys.executable`.
        extra_libdirs.append(os.path.dirname(getattr(sys, '_base_executable', sys.executable)))

        # 000680.python.build_main.line172.comment If `pywin32` is installed, resolve the path to the `pywin32_system32` directory. Most `pywin32` extensions
        # 000681.python.build_main.line173.comment reference the `pywintypes3X.dll` in there. Based on resolved `pywin32_system32` directory, also add other
        # 000682.python.build_main.line174.comment `pywin32` directory, in case extensions in different directories reference each other (the ones in the same
        # 000683.python.build_main.line175.comment directory should already be resolvable due to binary dependency analysis passing the analyzed binary's
        # 000684.python.build_main.line176.comment location to the `get_imports` function). This allows us to avoid searching all paths in `sys.path`, which
        # 000685.python.build_main.line177.comment may lead to other corner-case issues (e.g., #5560).
        pywin32_system32_dir = None
        try:
            # 000686.python.build_main.line180.comment Look up the directory by treating it as a namespace package.
            _, pywin32_system32_dir = get_package_paths('pywin32_system32')
        except Exception:
            pass

        if pywin32_system32_dir:
            pywin32_base_dir = os.path.dirname(pywin32_system32_dir)
            extra_libdirs += [
                pywin32_system32_dir,  # .../pywin32_system32
                # 000688.python.build_main.line189.comment based on pywin32.pth
                os.path.join(pywin32_base_dir, 'win32'),  # .../win32
                os.path.join(pywin32_base_dir, 'win32', 'lib'),  # .../win32/lib
                os.path.join(pywin32_base_dir, 'Pythonwin'),  # .../Pythonwin
            ]

    # 000692.python.build_main.line195.comment On Windows, packages' initialization code might register additional DLL search paths, either by modifying the
    # 000693.python.build_main.line196.comment `PATH` environment variable, or by calling `os.add_dll_directory`. Therefore, we import all collected packages,
    # 000694.python.build_main.line197.comment and track changes made to the environment.
    if compat.is_win:
        # 000695.python.build_main.line199.comment Helper functions to be executed in isolated environment.
        def setup(suppressed_imports):
            """
            Prepare environment for change tracking
            """
            import os
            import sys

            os._added_dll_directories = []
            os._original_path_env = os.environ.get('PATH', '')

            _original_add_dll_directory = os.add_dll_directory

            def _pyi_add_dll_directory(path):
                os._added_dll_directories.append(path)
                return _original_add_dll_directory(path)

            os.add_dll_directory = _pyi_add_dll_directory

            # 000696.python.build_main.line218.comment Suppress import of specified packages
            for name in suppressed_imports:
                sys.modules[name] = None

        def import_library(package):
            """
            Import collected package to set up environment.
            """
            try:
                __import__(package)
            except Exception:
                pass

        def process_search_paths():
            """
            Obtain lists of added search paths.
            """
            import os

            # 000697.python.build_main.line237.comment `os.add_dll_directory` might be called with a `pathlib.Path`, which cannot be marhsalled out of the helper
            # 000698.python.build_main.line238.comment process. So explicitly convert all entries to strings.
            dll_directories = [str(path) for path in os._added_dll_directories]

            orig_path = set(os._original_path_env.split(os.pathsep))
            modified_path = os.environ.get('PATH', '').split(os.pathsep)
            path_additions = [path for path in modified_path if path and path not in orig_path]

            return dll_directories, path_additions

        # 000699.python.build_main.line247.comment Pre-process the list of packages to import.
        # 000700.python.build_main.line248.comment Check for Qt bindings packages, and put them at the front of the packages list. This ensures that they are
        # 000701.python.build_main.line249.comment always imported first, which should prevent packages that support multiple bindings (`qtypy`, `pyqtgraph`,
        # 000702.python.build_main.line250.comment `matplotlib`, etc.) from trying to auto-select bindings.
        _QT_BINDINGS = ('PySide2', 'PyQt5', 'PySide6', 'PyQt6')

        qt_packages = []
        other_packages = []
        for package in import_packages:
            if package.startswith(_QT_BINDINGS):
                qt_packages.append(package)
            else:
                other_packages.append(package)
        import_packages = qt_packages + other_packages

        # 000703.python.build_main.line262.comment Just in case, explicitly suppress imports of Qt bindings that we are *not* collecting - if multiple bindings
        # 000704.python.build_main.line263.comment are available and some were excluded from our analysis, a package imported here might still try to import an
        # 000705.python.build_main.line264.comment excluded bindings package (and succeed at doing so).
        suppressed_imports = [package for package in _QT_BINDINGS if package not in qt_packages]

        # 000706.python.build_main.line267.comment If we suppressed PySide2 or PySide6, we must also suppress their corresponding shiboken package
        if "PySide2" in suppressed_imports:
            suppressed_imports += ["shiboken2"]
        if "PySide6" in suppressed_imports:
            suppressed_imports += ["shiboken6"]

        # 000707.python.build_main.line273.comment Suppress import of `pyqtgraph.canvas`, which is known to crash python interpreter. See #7452 and #8322, as
        # 000708.python.build_main.line274.comment well as https://github.com/pyqtgraph/pyqtgraph/issues/2838.
        suppressed_imports += ['pyqtgraph.canvas']

        # 000709.python.build_main.line277.comment PySimpleGUI 5.x displays a "first-run" dialog when imported for the first time, which blocks the loop below.
        # 000710.python.build_main.line278.comment This is a problem for building on CI, where the dialog cannot be closed, and where PySimpleGUI runs "for the
        # 000711.python.build_main.line279.comment first time" every time. See #8396.
        suppressed_imports += ['PySimpleGUI']

        # 000712.python.build_main.line282.comment Processing in isolated environment.
        with isolated.Python() as child:
            child.call(setup, suppressed_imports)
            for package in import_packages:
                try:
                    child.call(import_library, package)
                except isolated.SubprocessDiedError as e:
                    # 000713.python.build_main.line289.comment Re-raise as `isolated.SubprocessDiedError` again, to trigger error-handling codepath in
                    # 000714.python.build_main.line290.comment `isolated.Python.__exit__()`.
                    raise isolated.SubprocessDiedError(
                        f"Isolated subprocess crashed while importing package {package!r}! "
                        f"Package import list: {import_packages!r}"
                    ) from e
            added_dll_directories, added_path_directories = child.call(process_search_paths)

        # 000715.python.build_main.line297.comment Process extra search paths...
        logger.info("Extra DLL search directories (AddDllDirectory): %r", added_dll_directories)
        extra_libdirs += added_dll_directories

        logger.info("Extra DLL search directories (PATH): %r", added_path_directories)
        extra_libdirs += added_path_directories

    # 000716.python.build_main.line304.comment Deduplicate search paths
    # 000717.python.build_main.line305.comment NOTE: `list(set(extra_libdirs))` does not preserve the order of search paths (which matters here), so we need to
    # 000718.python.build_main.line306.comment de-duplicate using `list(dict.fromkeys(extra_libdirs).keys())` instead.
    extra_libdirs = list(dict.fromkeys(extra_libdirs).keys())

    # 000719.python.build_main.line309.comment Search for dependencies of the given binaries
    return bindepend.binary_dependency_analysis(
        binaries,
        search_paths=extra_libdirs,
        symlink_suppression_patterns=symlink_suppression_patterns,
    )


class _ModuleCollectionMode(enum.IntFlag):
    """
    Module collection mode flags.
    """
    PYZ = enum.auto()  # Collect byte-compiled .pyc into PYZ archive
    PYC = enum.auto()  # Collect byte-compiled .pyc as external data file
    PY = enum.auto()  # Collect source .py file as external data file


_MODULE_COLLECTION_MODES = {
    "pyz": _ModuleCollectionMode.PYZ,
    "pyc": _ModuleCollectionMode.PYC,
    "py": _ModuleCollectionMode.PY,
    "pyz+py": _ModuleCollectionMode.PYZ | _ModuleCollectionMode.PY,
    "py+pyz": _ModuleCollectionMode.PYZ | _ModuleCollectionMode.PY,
}


def _get_module_collection_mode(mode_dict, name, noarchive=False):
    """
    Determine the module/package collection mode for the given module name, based on the provided collection
    mode settings dictionary.
    """
    # 000723.python.build_main.line340.comment Default mode: collect into PYZ, unless noarchive is enabled. In that case, collect as pyc.
    mode_flags = _ModuleCollectionMode.PYC if noarchive else _ModuleCollectionMode.PYZ

    # 000724.python.build_main.line343.comment If we have no collection mode settings, end here and now.
    if not mode_dict:
        return mode_flags

    # 000725.python.build_main.line347.comment Search the parent modules/packages in top-down fashion, and take the last given setting. This ensures that
    # 000726.python.build_main.line348.comment a setting given for the top-level package is recursively propagated to all its subpackages and submodules,
    # 000727.python.build_main.line349.comment but also allows individual sub-modules to override the setting again.
    mode = 'pyz'

    name_parts = name.split('.')
    for i in range(len(name_parts)):
        modlevel = ".".join(name_parts[:i + 1])
        modlevel_mode = mode_dict.get(modlevel, None)
        if modlevel_mode is not None:
            mode = modlevel_mode

    # 000728.python.build_main.line359.comment Convert mode string to _ModuleCollectionMode flags
    try:
        mode_flags = _MODULE_COLLECTION_MODES[mode]
    except KeyError:
        raise ValueError(f"Unknown module collection mode for {name!r}: {mode!r}!")

    # 000729.python.build_main.line365.comment noarchive flag being set means that we need to change _ModuleCollectionMode.PYZ into _ModuleCollectionMode.PYC
    if noarchive and _ModuleCollectionMode.PYZ in mode_flags:
        mode_flags ^= _ModuleCollectionMode.PYZ
        mode_flags |= _ModuleCollectionMode.PYC

    return mode_flags


class Analysis(Target):
    """
    Class that performs analysis of the user's main Python scripts.

    An Analysis contains multiple TOC (Table of Contents) lists, accessed as attributes of the analysis object.

    scripts
            The scripts you gave Analysis as input, with any runtime hook scripts prepended.
    pure
            The pure Python modules.
    binaries
            The extension modules and their dependencies.
    datas
            Data files collected from packages.
    zipfiles
            Deprecated - always empty.
    zipped_data
            Deprecated - always empty.
    """
    _old_scripts = {
        absnormpath(os.path.join(HOMEPATH, "support", "_mountzlib.py")),
        absnormpath(os.path.join(HOMEPATH, "support", "useUnicode.py")),
        absnormpath(os.path.join(HOMEPATH, "support", "useTK.py")),
        absnormpath(os.path.join(HOMEPATH, "support", "unpackTK.py")),
        absnormpath(os.path.join(HOMEPATH, "support", "removeTK.py"))
    }

    def __init__(
        self,
        scripts,
        pathex=None,
        binaries=None,
        datas=None,
        hiddenimports=None,
        hookspath=None,
        hooksconfig=None,
        excludes=None,
        runtime_hooks=None,
        cipher=None,
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        noarchive=False,
        module_collection_mode=None,
        optimize=-1,
        **_kwargs,
    ):
        """
        scripts
                A list of scripts specified as file names.
        pathex
                An optional list of paths to be searched before sys.path.
        binaries
                An optional list of additional binaries (dlls, etc.) to include.
        datas
                An optional list of additional data files to include.
        hiddenimport
                An optional list of additional (hidden) modules to include.
        hookspath
                An optional list of additional paths to search for hooks. (hook-modules).
        hooksconfig
                An optional dict of config settings for hooks. (hook-modules).
        excludes
                An optional list of module or package names (their Python names, not path names) that will be
                ignored (as though they were not found).
        runtime_hooks
                An optional list of scripts to use as users' runtime hooks. Specified as file names.
        cipher
                Deprecated. Raises an error if not None.
        win_no_prefer_redirects
                Deprecated. Raises an error if not False.
        win_private_assemblies
                Deprecated. Raises an error if not False.
        noarchive
                If True, do not place source files in a archive, but keep them as individual files.
        module_collection_mode
                An optional dict of package/module names and collection mode strings. Valid collection mode strings:
                'pyz' (default), 'pyc', 'py', 'pyz+py' (or 'py+pyz')
        optimize
                Optimization level for collected bytecode. If not specified or set to -1, it is set to the value of
                `sys.flags.optimize` of the running build process.
        """
        if cipher is not None:
            from PyInstaller.exceptions import RemovedCipherFeatureError
            raise RemovedCipherFeatureError(
                "Please remove the 'cipher' arguments to PYZ() and Analysis() in your spec file."
            )
        if win_no_prefer_redirects:
            from PyInstaller.exceptions import RemovedWinSideBySideSupportError
            raise RemovedWinSideBySideSupportError(
                "Please remove the 'win_no_prefer_redirects' argument to Analysis() in your spec file."
            )
        if win_private_assemblies:
            from PyInstaller.exceptions import RemovedWinSideBySideSupportError
            raise RemovedWinSideBySideSupportError(
                "Please remove the 'win_private_assemblies' argument to Analysis() in your spec file."
            )
        super().__init__()
        from PyInstaller.config import CONF

        self.inputs = []
        spec_dir = os.path.dirname(CONF['spec'])
        for script in scripts:
            # 000730.python.build_main.line475.comment If path is relative, it is relative to the location of .spec file.
            if not os.path.isabs(script):
                script = os.path.join(spec_dir, script)
            if absnormpath(script) in self._old_scripts:
                logger.warning('Ignoring obsolete auto-added script %s', script)
                continue
            # 000731.python.build_main.line481.comment Normalize script path.
            script = os.path.normpath(script)
            if not os.path.exists(script):
                raise SystemExit("ERROR: script '%s' not found" % script)
            self.inputs.append(script)

        # 000732.python.build_main.line487.comment Django hook requires this variable to find the script manage.py.
        CONF['main_script'] = self.inputs[0]

        site_packages_pathex = []
        for path in (pathex or []):
            if pathlib.Path(path).name == "site-packages":
                site_packages_pathex.append(str(path))
        if site_packages_pathex:
            logger.log(
                logging.DEPRECATION, "Foreign Python environment's site-packages paths added to --paths/pathex:\n%s\n"
                "This is ALWAYS the wrong thing to do. If your environment's site-packages is not in PyInstaller's "
                "module search path then you are running PyInstaller from a different environment to the one your "
                "packages are in. Run print(sys.prefix) without PyInstaller to get the environment you should be using "
                "then install and run PyInstaller from that environment instead of this one. This warning will become "
                "an error in PyInstaller 7.0.", pprint.pformat(site_packages_pathex)
            )

        self.pathex = self._extend_pathex(pathex, self.inputs)
        # 000733.python.build_main.line505.comment Set global config variable 'pathex' to make it available for PyInstaller.utils.hooks and import hooks. Path
        # 000734.python.build_main.line506.comment extensions for module search.
        CONF['pathex'] = self.pathex
        # 000735.python.build_main.line508.comment Extend sys.path so PyInstaller could find all necessary modules.
        sys.path.extend(self.pathex)
        logger.info('Module search paths (PYTHONPATH):\n' + pprint.pformat(sys.path))

        self.hiddenimports = hiddenimports or []
        # 000736.python.build_main.line513.comment Include hidden imports passed via CONF['hiddenimports']; these might be populated if user has a wrapper script
        # 000737.python.build_main.line514.comment that calls `build_main.main()` with custom `pyi_config` dictionary that contains `hiddenimports`.
        self.hiddenimports.extend(CONF.get('hiddenimports', []))

        for modnm in self.hiddenimports:
            if re.search(r"[\\/]", modnm):
                raise SystemExit(
                    f"ERROR: Invalid hiddenimport '{modnm}'. Hidden imports should be importable module names – not "
                    "file paths. i.e. use --hiddenimport=foo.bar instead of --hiddenimport=.../site-packages/foo/bar.py"
                )

        self.hookspath = []
        # 000738.python.build_main.line525.comment Prepend directories in `hookspath` (`--additional-hooks-dir`) to take precedence over those from the entry
        # 000739.python.build_main.line526.comment points. Expand starting tilde into user's home directory, as a work-around for tilde not being expanded by
        # 000740.python.build_main.line527.comment shell when using `--additional-hooks-dir=~/path/abc` instead of `--additional-hooks-dir ~/path/abc` (or when
        # 000741.python.build_main.line528.comment the path argument is quoted).
        if hookspath:
            self.hookspath.extend([(os.path.expanduser(path), HOOK_PRIORITY_USER_HOOKS) for path in hookspath])

        # 000742.python.build_main.line532.comment Add hook directories from PyInstaller entry points.
        self.hookspath += discover_hook_directories()

        self.hooksconfig = {}
        if hooksconfig:
            self.hooksconfig.update(hooksconfig)

        # 000743.python.build_main.line539.comment Custom runtime hook files that should be included and started before any existing PyInstaller runtime hooks.
        self.custom_runtime_hooks = runtime_hooks or []

        self._input_binaries = []
        self._input_datas = []

        self.excludes = excludes or []
        self.scripts = []
        self.pure = []
        self.binaries = []
        self.zipfiles = []
        self.zipped_data = []
        self.datas = []
        self.dependencies = []
        self._python_version = sys.version
        self.noarchive = noarchive
        self.module_collection_mode = module_collection_mode or {}
        self.optimize = sys.flags.optimize if optimize in {-1, None} else optimize

        self._modules_outside_pyz = []

        # 000744.python.build_main.line560.comment Validate the optimization level to avoid errors later on...
        if self.optimize not in {0, 1, 2}:
            raise ValueError(f"Unsupported bytecode optimization level: {self.optimize!r}")

        # 000745.python.build_main.line564.comment Expand the `binaries` and `datas` lists specified in the .spec file, and ensure that the lists are normalized
        # 000746.python.build_main.line565.comment and sorted before guts comparison.
        # 000747.python.build_main.line566.comment
        # 000748.python.build_main.line567.comment While we use these lists to initialize `Analysis.binaries` and `Analysis.datas`, at this point, we need to
        # 000749.python.build_main.line568.comment store them in separate variables, which undergo *full* guts comparison (`_check_guts_toc`) as opposed to
        # 000750.python.build_main.line569.comment just mtime-based comparison (`_check_guts_toc_mtime`). Changes to these initial list *must* trigger a rebuild
        # 000751.python.build_main.line570.comment (and due to the way things work, a re-analysis), otherwise user might end up with a cached build that fails to
        # 000752.python.build_main.line571.comment reflect the changes.
        if binaries:
            logger.info("Appending 'binaries' from .spec")
            self._input_binaries = [(dest_name, src_name, 'BINARY')
                                    for dest_name, src_name in format_binaries_and_datas(binaries, workingdir=spec_dir)]
            self._input_binaries = sorted(normalize_toc(self._input_binaries))

        if datas:
            logger.info("Appending 'datas' from .spec")
            self._input_datas = [(dest_name, src_name, 'DATA')
                                 for dest_name, src_name in format_binaries_and_datas(datas, workingdir=spec_dir)]
            self._input_datas = sorted(normalize_toc(self._input_datas))

        self.__postinit__()

    _GUTS = (  # input parameters
        ('inputs', _check_guts_eq),  # parameter `scripts`
        ('pathex', _check_guts_eq),
        ('hiddenimports', _check_guts_eq),
        ('hookspath', _check_guts_eq),
        ('hooksconfig', _check_guts_eq),
        ('excludes', _check_guts_eq),
        ('custom_runtime_hooks', _check_guts_eq),
        ('noarchive', _check_guts_eq),
        ('module_collection_mode', _check_guts_eq),
        ('optimize', _check_guts_eq),

        ('_input_binaries', _check_guts_toc),
        ('_input_datas', _check_guts_toc),

        # 000755.python.build_main.line601.comment calculated/analysed values
        ('_python_version', _check_guts_eq),
        ('scripts', _check_guts_toc_mtime),
        ('pure', _check_guts_toc_mtime),
        ('binaries', _check_guts_toc_mtime),
        ('zipfiles', _check_guts_toc_mtime),
        ('zipped_data', None),  # TODO check this, too
        ('datas', _check_guts_toc_mtime),
        # 000757.python.build_main.line609.comment TODO: Need to add "dependencies"?

        ('_modules_outside_pyz', _check_guts_toc_mtime),
    )

    def _extend_pathex(self, spec_pathex, scripts):
        """
        Normalize additional paths where PyInstaller will look for modules and add paths with scripts to the list of
        paths.

        :param spec_pathex: Additional paths defined defined in .spec file.
        :param scripts: Scripts to create executable from.
        :return: list of updated paths
        """
        # 000758.python.build_main.line623.comment Based on main supplied script - add top-level modules directory to PYTHONPATH.
        # 000759.python.build_main.line624.comment Sometimes the main app script is not top-level module but submodule like 'mymodule.mainscript.py'.
        # 000760.python.build_main.line625.comment In that case PyInstaller will not be able find modules in the directory containing 'mymodule'.
        # 000761.python.build_main.line626.comment Add this directory to PYTHONPATH so PyInstaller could find it.
        pathex = []
        # 000762.python.build_main.line628.comment Add scripts paths first.
        for script in scripts:
            logger.debug('script: %s' % script)
            script_toplevel_dir = get_path_to_toplevel_modules(script)
            if script_toplevel_dir:
                pathex.append(script_toplevel_dir)
        # 000763.python.build_main.line634.comment Append paths from .spec.
        if spec_pathex is not None:
            pathex.extend(spec_pathex)
        # 000764.python.build_main.line637.comment Normalize paths in pathex and make them absolute.
        return [absnormpath(p) for p in pathex]

    def _check_guts(self, data, last_build):
        if Target._check_guts(self, data, last_build):
            return True
        for filename in self.inputs:
            if mtime(filename) > last_build:
                logger.info("Building because %s changed", filename)
                return True
        # 000765.python.build_main.line647.comment Now we know that none of the input parameters and none of the input files has changed. So take the values
        # 000766.python.build_main.line648.comment that were calculated / analyzed in the last run and store them in `self`. These TOC lists should already
        # 000767.python.build_main.line649.comment be normalized.
        self.scripts = data['scripts']
        self.pure = data['pure']
        self.binaries = data['binaries']
        self.zipfiles = data['zipfiles']
        self.zipped_data = data['zipped_data']
        self.datas = data['datas']

        return False

    def assemble(self):
        """
        This method is the MAIN method for finding all necessary files to be bundled.
        """
        from PyInstaller.config import CONF

        # 000768.python.build_main.line665.comment Search for python shared library, which we need to collect into frozen application. Do this as the very
        # 000769.python.build_main.line666.comment first step, to minimize the amount of processing when the shared library cannot be found.
        logger.info('Looking for Python shared library...')
        python_lib = bindepend.get_python_library_path()  # Raises PythonLibraryNotFoundError
        logger.info('Using Python shared library: %s', python_lib)

        logger.info("Running Analysis %s", self.tocbasename)
        logger.info("Target bytecode optimization level: %d", self.optimize)

        for m in self.excludes:
            logger.debug("Excluding module '%s'" % m)
        self.graph = initialize_modgraph(excludes=self.excludes, user_hook_dirs=self.hookspath)

        # 000771.python.build_main.line678.comment Initialize `binaries` and `datas` with `_input_binaries` and `_input_datas`. Make sure to copy the lists
        # 000772.python.build_main.line679.comment to prevent modifications of original lists, which we need to store in original form for guts comparison.
        self.datas = [entry for entry in self._input_datas]
        self.binaries = [entry for entry in self._input_binaries]

        # 000773.python.build_main.line683.comment Expand sys.path of module graph. The attribute is the set of paths to use for imports: sys.path, plus our
        # 000774.python.build_main.line684.comment loader, plus other paths from e.g. --path option).
        self.graph.path = self.pathex + self.graph.path

        # 000775.python.build_main.line687.comment Scan for legacy namespace packages.
        self.graph.scan_legacy_namespace_packages()

        # 000776.python.build_main.line690.comment Add python shared library to `binaries`.
        if is_darwin and osxutils.is_framework_bundle_lib(python_lib):
            # 000777.python.build_main.line692.comment If python library is located in macOS .framework bundle, collect the bundle, and create symbolic link to
            # 000778.python.build_main.line693.comment top-level directory.
            src_path = pathlib.PurePath(python_lib)
            dst_path = pathlib.PurePath(src_path.relative_to(src_path.parent.parent.parent.parent))
            self.binaries.append((str(dst_path), str(src_path), 'BINARY'))
            self.binaries.append((os.path.basename(python_lib), str(dst_path), 'SYMLINK'))
        else:
            self.binaries.append((os.path.basename(python_lib), python_lib, 'BINARY'))

        # 000779.python.build_main.line701.comment -- Module graph. --
        # 000780.python.build_main.line702.comment
        # 000781.python.build_main.line703.comment Construct the module graph of import relationships between modules required by this user's application. For
        # 000782.python.build_main.line704.comment each entry point (top-level user-defined Python script), all imports originating from this entry point are
        # 000783.python.build_main.line705.comment recursively parsed into a subgraph of the module graph. This subgraph is then connected to this graph's root
        # 000784.python.build_main.line706.comment node, ensuring imported module nodes will be reachable from the root node -- which is is (arbitrarily) chosen
        # 000785.python.build_main.line707.comment to be the first entry point's node.

        # 000786.python.build_main.line709.comment List of graph nodes corresponding to program scripts.
        program_scripts = []

        # 000787.python.build_main.line712.comment Assume that if the script does not exist, Modulegraph will raise error. Save the graph nodes of each in
        # 000788.python.build_main.line713.comment sequence.
        for script in self.inputs:
            logger.info("Analyzing %s", script)
            program_scripts.append(self.graph.add_script(script))

        # 000789.python.build_main.line718.comment Analyze the script's hidden imports (named on the command line)
        self.graph.add_hiddenimports(self.hiddenimports)

        # 000790.python.build_main.line721.comment -- Post-graph hooks. --
        self.graph.process_post_graph_hooks(self)

        # 000791.python.build_main.line724.comment Update 'binaries' and 'datas' TOC lists with entries collected from hooks.
        self.binaries += self.graph.make_hook_binaries_toc()
        self.datas += self.graph.make_hook_datas_toc()

        # 000792.python.build_main.line728.comment We do not support zipped eggs anymore (PyInstaller v6.0), so `zipped_data` and `zipfiles` are always empty.
        self.zipped_data = []
        self.zipfiles = []

        # 000793.python.build_main.line732.comment -- Automatic binary vs. data reclassification. --
        # 000794.python.build_main.line733.comment
        # 000795.python.build_main.line734.comment At this point, `binaries` and `datas` contain  TOC entries supplied by user via input arguments, and by hooks
        # 000796.python.build_main.line735.comment that were ran during the analysis. Neither source can be fully trusted regarding the DATA vs BINARY
        # 000797.python.build_main.line736.comment classification (no thanks to our hookutils not being 100% reliable, either!). Therefore, inspect the files and
        # 000798.python.build_main.line737.comment automatically reclassify them as necessary.
        # 000799.python.build_main.line738.comment
        # 000800.python.build_main.line739.comment The proper classification is important especially for collected binaries - to ensure that they undergo binary
        # 000801.python.build_main.line740.comment dependency analysis and platform-specific binary processing. On macOS, the .app bundle generation code also
        # 000802.python.build_main.line741.comment depends on files to be properly classified.
        # 000803.python.build_main.line742.comment
        # 000804.python.build_main.line743.comment For entries added to `binaries` and `datas` after this point, we trust their typecodes due to the nature of
        # 000805.python.build_main.line744.comment their origin.
        combined_toc = normalize_toc(self.datas + self.binaries)

        logger.info('Performing binary vs. data reclassification (%d entries)', len(combined_toc))

        self.datas = []
        self.binaries = []

        for dest_name, src_name, typecode in combined_toc:
            # 000806.python.build_main.line753.comment Returns 'BINARY' or 'DATA', or None if file cannot be classified.
            detected_typecode = bindepend.classify_binary_vs_data(src_name)
            if detected_typecode is not None:
                if detected_typecode != typecode:
                    logger.debug(
                        "Reclassifying collected file %r from %s to %s...", src_name, typecode, detected_typecode
                    )
                typecode = detected_typecode

            # 000807.python.build_main.line762.comment Put back into corresponding TOC list.
            if typecode in {'BINARY', 'EXTENSION'}:
                self.binaries.append((dest_name, src_name, typecode))
            else:
                self.datas.append((dest_name, src_name, typecode))

        # 000808.python.build_main.line768.comment -- Look for dlls that are imported by Python 'ctypes' module. --
        # 000809.python.build_main.line769.comment First get code objects of all modules that import 'ctypes'.
        logger.info('Looking for ctypes DLLs')
        # 000810.python.build_main.line771.comment dict like: {'module1': code_obj, 'module2': code_obj}
        ctypes_code_objs = self.graph.get_code_using("ctypes")

        for name, co in ctypes_code_objs.items():
            # 000811.python.build_main.line775.comment Get dlls that might be needed by ctypes.
            logger.debug('Scanning %s for ctypes-based references to shared libraries', name)
            try:
                ctypes_binaries = scan_code_for_ctypes(co)
                # 000812.python.build_main.line779.comment As this scan happens after automatic binary-vs-data classification, we need to validate the binaries
                # 000813.python.build_main.line780.comment ourselves, just in case.
                for dest_name, src_name, typecode in set(ctypes_binaries):
                    # 000814.python.build_main.line782.comment Allow for `None` in case re-classification is not supported on the given platform.
                    if bindepend.classify_binary_vs_data(src_name) not in (None, 'BINARY'):
                        logger.warning("Ignoring %s found via ctypes - not a valid binary!", src_name)
                        continue
                    self.binaries.append((dest_name, src_name, typecode))
            except Exception as ex:
                raise RuntimeError(f"Failed to scan the module '{name}'. This is a bug. Please report it.") from ex

        self.datas.extend((dest, source, "DATA")
                          for (dest, source) in format_binaries_and_datas(self.graph.metadata_required()))

        # 000815.python.build_main.line793.comment Analyze run-time hooks.
        rhtook_scripts = self.graph.analyze_runtime_hooks(self.custom_runtime_hooks)

        # 000816.python.build_main.line796.comment -- Extract the nodes of the graph as TOCs for further processing. --

        # 000817.python.build_main.line798.comment Initialize the scripts list: run-time hooks (custom ones, followed by regular ones), followed by program
        # 000818.python.build_main.line799.comment script(s).

        # 000819.python.build_main.line801.comment We do not optimize bytecode of run-time hooks.
        rthook_toc = self.graph.nodes_to_toc(rhtook_scripts)

        # 000820.python.build_main.line804.comment Override the typecode of program script(s) to include bytecode optimization level.
        program_toc = self.graph.nodes_to_toc(program_scripts)
        optim_typecode = {0: 'PYSOURCE', 1: 'PYSOURCE-1', 2: 'PYSOURCE-2'}[self.optimize]
        program_toc = [(name, src_path, optim_typecode) for name, src_path, typecode in program_toc]

        self.scripts = rthook_toc + program_toc
        self.scripts = normalize_toc(self.scripts)  # Should not really contain duplicates, but just in case...

        # 000822.python.build_main.line812.comment Extend the binaries list with all the Extensions modulegraph has found.
        self.binaries += self.graph.make_binaries_toc()

        # 000823.python.build_main.line815.comment Convert extension module names into full filenames, and append suffix. Ensure that extensions that come from
        # 000824.python.build_main.line816.comment the lib-dynload are collected into _MEIPASS/python3.x/lib-dynload instead of directly into _MEIPASS.
        for idx, (dest, source, typecode) in enumerate(self.binaries):
            if typecode != 'EXTENSION':
                continue
            dest = destination_name_for_extension(dest, source, typecode)
            self.binaries[idx] = (dest, source, typecode)

        # 000825.python.build_main.line823.comment Perform initial normalization of `datas` and `binaries`
        self.datas = normalize_toc(self.datas)
        self.binaries = normalize_toc(self.binaries)

        # 000826.python.build_main.line827.comment Post-process GLib schemas
        self.datas = compile_glib_schema_files(self.datas, os.path.join(CONF['workpath'], "_pyi_gschema_compilation"))
        self.datas = normalize_toc(self.datas)

        # 000827.python.build_main.line831.comment Process the pure-python modules list. Depending on the collection mode, these entries end up either in "pure"
        # 000828.python.build_main.line832.comment list for collection into the PYZ archive, or in the "datas" list for collection as external data files.
        assert len(self.pure) == 0
        pure_pymodules_toc = self.graph.make_pure_toc()

        # 000829.python.build_main.line836.comment Merge package collection mode settings from .spec file. These are applied last, so they override the
        # 000830.python.build_main.line837.comment settings previously applied by hooks.
        self.graph._module_collection_mode.update(self.module_collection_mode)
        logger.debug("Module collection settings: %r", self.graph._module_collection_mode)

        # 000831.python.build_main.line841.comment If target bytecode optimization level matches the run-time bytecode optimization level (i.e., of the running
        # 000832.python.build_main.line842.comment build process), we can re-use the modulegraph's code-object cache.
        if self.optimize == sys.flags.optimize:
            logger.debug(
                "Target optimization level %d matches run-time optimization level %d - using modulegraph's code-object "
                "cache.",
                self.optimize,
                sys.flags.optimize,
            )
            code_cache = self.graph.get_code_objects()
        else:
            logger.debug(
                "Target optimization level %d differs from run-time optimization level %d - ignoring modulegraph's "
                "code-object cache.",
                self.optimize,
                sys.flags.optimize,
            )
            code_cache = None

        # 000833.python.build_main.line860.comment Construct a set for look-up of modules that should end up in base_library.zip. The list of corresponding
        # 000834.python.build_main.line861.comment modulegraph nodes is stored in `PyiModuleGraph._base_modules` (see `PyiModuleGraph._analyze_base_modules`).
        base_modules = set(node.identifier for node in self.graph._base_modules)
        base_modules_toc = []

        pycs_dir = os.path.join(CONF['workpath'], 'localpycs')
        optim_level = self.optimize  # We could extend this with per-module settings, similar to `collect_mode`.
        for name, src_path, typecode in pure_pymodules_toc:
            assert typecode == 'PYMODULE'
            collect_mode = _get_module_collection_mode(self.graph._module_collection_mode, name, self.noarchive)

            # 000836.python.build_main.line871.comment Collect byte-compiled .pyc into PYZ archive or base_library.zip. Embed optimization level into typecode.
            in_pyz = False
            if _ModuleCollectionMode.PYZ in collect_mode:
                optim_typecode = {0: 'PYMODULE', 1: 'PYMODULE-1', 2: 'PYMODULE-2'}[optim_level]
                toc_entry = (name, src_path, optim_typecode)
                if name in base_modules:
                    base_modules_toc.append(toc_entry)
                else:
                    self.pure.append(toc_entry)
                    in_pyz = True

            # 000837.python.build_main.line882.comment If module is not collected into PYZ archive (and is consequently not tracked in the `self.pure` TOC list),
            # 000838.python.build_main.line883.comment add it to the `self._modules_outside_pyz` TOC list, in order to be able to detect modifications in those
            # 000839.python.build_main.line884.comment modules.
            if not in_pyz:
                self._modules_outside_pyz.append((name, src_path, typecode))

            # 000840.python.build_main.line888.comment Pure namespace packages have no source path, and cannot be collected as external data file.
            if src_path in (None, '-'):
                continue

            # 000841.python.build_main.line892.comment Collect source .py file as external data file
            if _ModuleCollectionMode.PY in collect_mode:
                basename, ext = os.path.splitext(os.path.basename(src_path))
                # 000842.python.build_main.line895.comment If the module is available only as a byte-compiled .pyc, we cannot collect its source.
                if ext.lower() == '.pyc':
                    logger.warning(
                        'Cannot collect source .py file for module %r - module is available only as .pyc: %r',
                        name,
                        src_path,
                    )
                    continue
                dest_path = name.replace('.', os.sep)
                if basename == '__init__':
                    dest_path += os.sep + '__init__' + ext
                else:
                    dest_path += ext
                self.datas.append((dest_path, src_path, "DATA"))

            # 000843.python.build_main.line910.comment Collect byte-compiled .pyc file as external data file
            if _ModuleCollectionMode.PYC in collect_mode:
                basename, ext = os.path.splitext(os.path.basename(src_path))
                dest_path = name.replace('.', os.sep)
                if basename == '__init__':
                    dest_path += os.sep + '__init__'
                # 000844.python.build_main.line916.comment Append the extension for the compiled result. In python 3.5 (PEP-488) .pyo files were replaced by
                # 000845.python.build_main.line917.comment .opt-1.pyc and .opt-2.pyc. However, it seems that for bytecode-only module distribution, we always
                # 000846.python.build_main.line918.comment need to use the .pyc extension.
                dest_path += '.pyc'

                # 000847.python.build_main.line921.comment Compile - use optimization-level-specific sub-directory in local working directory.
                obj_path = compile_pymodule(
                    name,
                    src_path,
                    workpath=os.path.join(pycs_dir, str(optim_level)),
                    optimize=optim_level,
                    code_cache=code_cache,
                )

                self.datas.append((dest_path, obj_path, "DATA"))

        # 000848.python.build_main.line932.comment Construct base_library.zip, if applicable (the only scenario where it is not is if we are building with
        # 000849.python.build_main.line933.comment noarchive mode). Always remove the file before the build.
        base_library_zip = os.path.join(CONF['workpath'], 'base_library.zip')
        if os.path.exists(base_library_zip):
            os.remove(base_library_zip)
        if base_modules_toc:
            logger.info('Creating %s...', os.path.basename(base_library_zip))
            create_base_library_zip(base_library_zip, base_modules_toc, code_cache)
            self.datas.append((os.path.basename(base_library_zip), base_library_zip, 'DATA'))  # Bundle as data file.

        # 000851.python.build_main.line942.comment Normalize list of pure-python modules (these will end up in PYZ archive, so use specific normalization).
        self.pure = normalize_pyz_toc(self.pure)

        # 000852.python.build_main.line945.comment Associate the `pure` TOC list instance with code cache in the global `CONF`; this is used by `PYZ` writer
        # 000853.python.build_main.line946.comment to obtain modules' code from cache instead
        # 000854.python.build_main.line947.comment
        # 000855.python.build_main.line948.comment (NOTE: back when `pure` was an instance of `TOC` class, the code object was passed by adding an attribute
        # 000856.python.build_main.line949.comment to the `pure` itself; now that `pure` is plain `list`, we cannot do that anymore. But the association via
        # 000857.python.build_main.line950.comment object ID should have the same semantics as the added attribute).
        from PyInstaller.config import CONF
        global_code_cache_map = CONF['code_cache']
        global_code_cache_map[id(self.pure)] = code_cache

        # 000858.python.build_main.line955.comment Add remaining binary dependencies - analyze Python C-extensions and what DLLs they depend on.
        # 000859.python.build_main.line956.comment
        # 000860.python.build_main.line957.comment Up until this point, we did very best not to import the packages into the main process. However, a package
        # 000861.python.build_main.line958.comment may set up additional library search paths during its import (e.g., by modifying PATH or calling the
        # 000862.python.build_main.line959.comment add_dll_directory() function on Windows, or modifying LD_LIBRARY_PATH on Linux). In order to reliably
        # 000863.python.build_main.line960.comment discover dynamic libraries, we therefore require an environment with all packages imported. We achieve that
        # 000864.python.build_main.line961.comment by gathering list of all collected packages, and spawn an isolated process, in which we first import all
        # 000865.python.build_main.line962.comment the packages from the list, and then perform search for dynamic libraries.
        logger.info('Looking for dynamic libraries')

        collected_packages = self.graph.get_collected_packages()
        self.binaries.extend(
            find_binary_dependencies(self.binaries, collected_packages, self.graph._bindepend_symlink_suppression)
        )

        # 000866.python.build_main.line970.comment Apply work-around for (potential) binaries collected from `pywin32` package...
        if is_win:
            self.binaries = postprocess_binaries_toc_pywin32(self.binaries)
            # 000867.python.build_main.line973.comment With anaconda, we need additional work-around...
            if is_conda:
                self.binaries = postprocess_binaries_toc_pywin32_anaconda(self.binaries)

        # 000868.python.build_main.line977.comment On linux, check for HMAC files accompanying shared library files and, if available, collect them.
        # 000869.python.build_main.line978.comment These are present on Fedora and RHEL, and are used in FIPS-enabled configurations to ensure shared
        # 000870.python.build_main.line979.comment library's file integrity.
        if is_linux:
            for dest_name, src_name, typecode in self.binaries:
                if typecode not in {'BINARY', 'EXTENSION'}:
                    continue  # Skip symbolic links

                src_lib_path = pathlib.Path(src_name)

                # 000872.python.build_main.line987.comment Check for .name.hmac file next to the shared library.
                src_hmac_path = src_lib_path.with_name(f".{src_lib_path.name}.hmac")
                if src_hmac_path.is_file():
                    dest_hmac_path = pathlib.PurePath(dest_name).with_name(src_hmac_path.name)
                    self.datas.append((str(dest_hmac_path), str(src_hmac_path), 'DATA'))

                # 000873.python.build_main.line993.comment Alternatively, check the fipscheck directory: fipscheck/name.hmac
                src_hmac_path = src_lib_path.parent / "fipscheck" / f"{src_lib_path.name}.hmac"
                if src_hmac_path.is_file():
                    dest_hmac_path = pathlib.PurePath("fipscheck") / src_hmac_path.name
                    self.datas.append((str(dest_hmac_path), str(src_hmac_path), 'DATA'))

                # 000874.python.build_main.line999.comment Similarly, look for .chk files that are used by NSS libraries.
                src_chk_path = src_lib_path.with_suffix(".chk")
                if src_chk_path.is_file():
                    dest_chk_path = pathlib.PurePath(dest_name).with_name(src_chk_path.name)
                    self.datas.append((str(dest_chk_path), str(src_chk_path), 'DATA'))

        # 000875.python.build_main.line1005.comment Final normalization of `datas` and `binaries`:
        # 000876.python.build_main.line1006.comment - normalize both TOCs together (to avoid having duplicates across the lists)
        # 000877.python.build_main.line1007.comment - process the combined normalized TOC for symlinks
        # 000878.python.build_main.line1008.comment - split back into `binaries` (BINARY, EXTENSION) and `datas` (everything else)
        combined_toc = normalize_toc(self.datas + self.binaries)
        combined_toc = toc_process_symbolic_links(combined_toc)

        # 000879.python.build_main.line1012.comment On macOS, look for binaries collected from .framework bundles, and collect their Info.plist files.
        if is_darwin:
            combined_toc += osxutils.collect_files_from_framework_bundles(combined_toc)

        self.datas = []
        self.binaries = []
        for entry in combined_toc:
            dest_name, src_name, typecode = entry
            if typecode in {'BINARY', 'EXTENSION'}:
                self.binaries.append(entry)
            else:
                self.datas.append(entry)

        # 000880.python.build_main.line1025.comment On macOS, the Finder app seems to litter visited directories with `.DS_Store` files. These cause issues with
        # 000881.python.build_main.line1026.comment codesigning when placed in mixed-content directories, where our .app bundle generator cross-links data files
        # 000882.python.build_main.line1027.comment from `Resources` to `Frameworks` tree, and the `codesign` utility explicitly forbids a `.DS_Store` file to be
        # 000883.python.build_main.line1028.comment a symbolic link.
        # 000884.python.build_main.line1029.comment But there is no reason for `.DS_Store` files to be collected in the first place, so filter them out.
        if is_darwin:
            self.datas = [(dest_name, src_name, typecode) for dest_name, src_name, typecode in self.datas
                          if os.path.basename(src_name) != '.DS_Store']

        # 000885.python.build_main.line1034.comment Write warnings about missing modules.
        self._write_warnings()
        # 000886.python.build_main.line1036.comment Write debug information about the graph
        self._write_graph_debug()

        # 000887.python.build_main.line1039.comment On macOS, check the SDK version of the binaries to be collected, and warn when the SDK version is either
        # 000888.python.build_main.line1040.comment invalid or too low. Such binaries will likely refuse to be loaded when hardened runtime is enabled and
        # 000889.python.build_main.line1041.comment while we cannot do anything about it, we can at least warn the user about it.
        # 000890.python.build_main.line1042.comment See: https://developer.apple.com/forums/thread/132526
        if is_darwin:
            binaries_with_invalid_sdk = []
            for dest_name, src_name, typecode in self.binaries:
                try:
                    sdk_version = osxutils.get_macos_sdk_version(src_name)
                except Exception:
                    logger.warning("Failed to query macOS SDK version of %r!", src_name, exc_info=True)
                    binaries_with_invalid_sdk.append((dest_name, src_name, "unavailable"))
                    continue

                if sdk_version < (10, 9, 0):
                    binaries_with_invalid_sdk.append((dest_name, src_name, sdk_version))
            if binaries_with_invalid_sdk:
                logger.warning("Found one or more binaries with invalid or incompatible macOS SDK version:")
                for dest_name, src_name, sdk_version in binaries_with_invalid_sdk:
                    logger.warning(" * %r, collected as %r; version: %r", src_name, dest_name, sdk_version)
                logger.warning("These binaries will likely cause issues with code-signing and hardened runtime!")

    def _write_warnings(self):
        """
        Write warnings about missing modules. Get them from the graph and use the graph to figure out who tried to
        import them.
        """
        def dependency_description(name, dep_info):
            if not dep_info or dep_info == 'direct':
                imptype = 0
            else:
                imptype = (dep_info.conditional + 2 * dep_info.function + 4 * dep_info.tryexcept)
            return '%s (%s)' % (name, IMPORT_TYPES[imptype])

        from PyInstaller.config import CONF
        miss_toc = self.graph.make_missing_toc()
        with open(CONF['warnfile'], 'w', encoding='utf-8') as wf:
            wf.write(WARNFILE_HEADER)
            for (n, p, status) in miss_toc:
                importers = self.graph.get_importers(n)
                print(
                    status,
                    'module named',
                    n,
                    '- imported by',
                    ', '.join(dependency_description(name, data) for name, data in importers),
                    file=wf
                )
        logger.info("Warnings written to %s", CONF['warnfile'])

    def _write_graph_debug(self):
        """
        Write a xref (in html) and with `--log-level DEBUG` a dot-drawing of the graph.
        """
        from PyInstaller.config import CONF
        with open(CONF['xref-file'], 'w', encoding='utf-8') as fh:
            self.graph.create_xref(fh)
            logger.info("Graph cross-reference written to %s", CONF['xref-file'])
        if logger.getEffectiveLevel() > logging.DEBUG:
            return
        # 000891.python.build_main.line1099.comment The `DOT language's <https://www.graphviz.org/doc/info/lang.html>`_ default character encoding (see the end
        # 000892.python.build_main.line1100.comment of the linked page) is UTF-8.
        with open(CONF['dot-file'], 'w', encoding='utf-8') as fh:
            self.graph.graphreport(fh)
            logger.info("Graph drawing written to %s", CONF['dot-file'])

    def exclude_system_libraries(self, list_of_exceptions=None):
        """
        This method may be optionally called from the spec file to exclude any system libraries from the list of
        binaries other than those containing the shell-style wildcards in list_of_exceptions. Those that match
        '*python*' or are stored under 'lib-dynload' are always treated as exceptions and not excluded.
        """

        self.binaries = [
            entry for entry in self.binaries if _should_include_system_binary(entry, list_of_exceptions or [])
        ]


class ExecutableBuilder:
    """
    Class that constructs the executable.
    """
    # 000893.python.build_main.line1121.comment TODO wrap the 'main' and 'build' function into this class.


def build(spec, distpath, workpath, clean_build):
    """
    Build the executable according to the created SPEC file.
    """
    from PyInstaller.config import CONF

    # 000894.python.build_main.line1130.comment Ensure starting tilde in distpath / workpath is expanded into user's home directory. This is to work around for
    # 000895.python.build_main.line1131.comment tilde not being expanded when using `--workpath=~/path/abc` instead of `--workpath ~/path/abc` (or when the path
    # 000896.python.build_main.line1132.comment argument is quoted). See https://github.com/pyinstaller/pyinstaller/issues/696
    distpath = os.path.abspath(os.path.expanduser(distpath))
    workpath = os.path.abspath(os.path.expanduser(workpath))

    CONF['spec'] = os.path.abspath(spec)
    CONF['specpath'], CONF['specnm'] = os.path.split(CONF['spec'])
    CONF['specnm'] = os.path.splitext(CONF['specnm'])[0]

    # 000897.python.build_main.line1140.comment Add 'specname' to workpath and distpath if they point to PyInstaller homepath.
    if os.path.dirname(distpath) == HOMEPATH:
        distpath = os.path.join(HOMEPATH, CONF['specnm'], os.path.basename(distpath))
    CONF['distpath'] = distpath
    if os.path.dirname(workpath) == HOMEPATH:
        workpath = os.path.join(HOMEPATH, CONF['specnm'], os.path.basename(workpath), CONF['specnm'])
    else:
        workpath = os.path.join(workpath, CONF['specnm'])
    CONF['workpath'] = workpath

    CONF['warnfile'] = os.path.join(workpath, 'warn-%s.txt' % CONF['specnm'])
    CONF['dot-file'] = os.path.join(workpath, 'graph-%s.dot' % CONF['specnm'])
    CONF['xref-file'] = os.path.join(workpath, 'xref-%s.html' % CONF['specnm'])

    CONF['code_cache'] = dict()

    # 000898.python.build_main.line1156.comment Clean PyInstaller cache (CONF['cachedir']) and temporary files (workpath) to be able start a clean build.
    if clean_build:
        logger.info('Removing temporary files and cleaning cache in %s', CONF['cachedir'])
        for pth in (CONF['cachedir'], workpath):
            if os.path.exists(pth):
                # 000899.python.build_main.line1161.comment Remove all files in 'pth'.
                for f in glob.glob(pth + '/*'):
                    # 000900.python.build_main.line1163.comment Remove dirs recursively.
                    if os.path.isdir(f):
                        shutil.rmtree(f)
                    else:
                        os.remove(f)

    # 000901.python.build_main.line1169.comment Create DISTPATH and workpath if they does not exist.
    for pth in (CONF['distpath'], CONF['workpath']):
        os.makedirs(pth, exist_ok=True)

    # 000902.python.build_main.line1173.comment Construct NAMESPACE for running the Python code from .SPEC file.
    # 000903.python.build_main.line1174.comment NOTE: Passing NAMESPACE allows to avoid having global variables in this module and makes isolated environment for
    # 000904.python.build_main.line1175.comment running tests.
    # 000905.python.build_main.line1176.comment NOTE: Defining NAMESPACE allows to map any class to a apecific name for .SPEC.
    # 000906.python.build_main.line1177.comment FIXME: Some symbols might be missing. Add them if there are some failures.
    # 000907.python.build_main.line1178.comment TODO: What from this .spec API is deprecated and could be removed?
    spec_namespace = {
        # 000908.python.build_main.line1180.comment Set of global variables that can be used while processing .spec file. Some of them act as configuration
        # 000909.python.build_main.line1181.comment options.
        'DISTPATH': CONF['distpath'],
        'HOMEPATH': HOMEPATH,
        'SPEC': CONF['spec'],
        'specnm': CONF['specnm'],
        'SPECPATH': CONF['specpath'],
        'WARNFILE': CONF['warnfile'],
        'workpath': CONF['workpath'],
        # 000910.python.build_main.line1189.comment PyInstaller classes for .spec.
        'TOC': TOC,  # Kept for backward compatibility even though `TOC` class is deprecated.
        'Analysis': Analysis,
        'BUNDLE': BUNDLE,
        'COLLECT': COLLECT,
        'EXE': EXE,
        'MERGE': MERGE,
        'PYZ': PYZ,
        'Tree': Tree,
        'Splash': Splash,
        # 000912.python.build_main.line1199.comment Python modules available for .spec.
        'os': os,
    }

    # 000913.python.build_main.line1203.comment Execute the specfile. Read it as a binary file...
    try:
        with open(spec, 'rb') as f:
            # 000914.python.build_main.line1206.comment ... then let Python determine the encoding, since ``compile`` accepts byte strings.
            code = compile(f.read(), spec, 'exec')
    except FileNotFoundError:
        raise SystemExit(f'ERROR: Spec file "{spec}" not found!')
    exec(code, spec_namespace)

    logger.info("Build complete! The results are available in: %s", CONF['distpath'])


def __add_options(parser):
    parser.add_argument(
        "--distpath",
        metavar="DIR",
        default=DEFAULT_DISTPATH,
        help="Where to put the bundled app (default: ./dist)",
    )
    parser.add_argument(
        '--workpath',
        default=DEFAULT_WORKPATH,
        help="Where to put all the temporary work files, .log, .pyz and etc. (default: ./build)",
    )
    parser.add_argument(
        '-y',
        '--noconfirm',
        action="store_true",
        default=False,
        help="Replace output directory (default: %s) without asking for confirmation" %
        os.path.join('SPECPATH', 'dist', 'SPECNAME'),
    )
    parser.add_argument(
        '--upx-dir',
        default=None,
        help="Path to UPX utility (default: search the execution path)",
    )
    parser.add_argument(
        '--clean',
        dest='clean_build',
        action='store_true',
        default=False,
        help="Clean PyInstaller cache and remove temporary files before building.",
    )


def main(
    pyi_config,
    specfile,
    noconfirm=False,
    distpath=DEFAULT_DISTPATH,
    workpath=DEFAULT_WORKPATH,
    upx_dir=None,
    clean_build=False,
    **kw
):
    from PyInstaller.config import CONF
    CONF['noconfirm'] = noconfirm

    # 000915.python.build_main.line1262.comment If configuration dict is supplied - skip configuration step.
    if pyi_config is None:
        import PyInstaller.configure as configure
        CONF.update(configure.get_config(upx_dir=upx_dir))
    else:
        CONF.update(pyi_config)

    CONF['ui_admin'] = kw.get('ui_admin', False)
    CONF['ui_access'] = kw.get('ui_uiaccess', False)

    build(specfile, distpath, workpath, clean_build)
