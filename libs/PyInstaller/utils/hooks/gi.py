# 010025.python.gi.line1.comment ----------------------------------------------------------------------------
# 010026.python.gi.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 010027.python.gi.line3.comment
# 010028.python.gi.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 010029.python.gi.line5.comment or later) with exception for distributing the bootloader.
# 010030.python.gi.line6.comment
# 010031.python.gi.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 010032.python.gi.line8.comment
# 010033.python.gi.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 010034.python.gi.line10.comment ----------------------------------------------------------------------------
import os
import pathlib
import shutil
import subprocess
import hashlib
import re

from PyInstaller.depend.utils import _resolveCtypesImports
from PyInstaller.utils.hooks import collect_submodules, collect_system_data_files, get_hook_config
from PyInstaller import isolated
from PyInstaller import log as logging
from PyInstaller import compat
from PyInstaller.depend.bindepend import findSystemLibrary

logger = logging.getLogger(__name__)


class GiModuleInfo:
    def __init__(self, module, version, hook_api=None):
        self.name = module
        self.version = version
        self.available = False
        self.sharedlibs = []
        self.typelib = None
        self.dependencies = []

        # 010035.python.gi.line37.comment If hook API is available, use it to override the version from hookconfig.
        if hook_api is not None:
            module_versions = get_hook_config(hook_api, 'gi', 'module-versions')
            if module_versions:
                self.version = module_versions.get(module, version)

        logger.debug("Gathering GI module info for %s %s", module, self.version)

        @isolated.decorate
        def _get_module_info(module, version):
            import gi

            # 010036.python.gi.line49.comment Ideally, we would use gi.Repository, which provides common abstraction for some of the functions we use in
            # 010037.python.gi.line50.comment this codepath (e.g., `require`, `get_typelib_path`, `get_immediate_dependencies`). However, it lacks the
            # 010038.python.gi.line51.comment `get_shared_library` function, which is why we are using "full" bindings via `gi.repository.GIRepository`.
            # 010039.python.gi.line52.comment
            # 010040.python.gi.line53.comment PyGObject 3.52.0 switched from girepository-1.0 to girepository-2.0, which means that GIRepository version
            # 010041.python.gi.line54.comment has changed from 2.0 to 3.0 and some of the API has changed.
            try:
                gi.require_version("GIRepository", "3.0")
                new_api = True
            except ValueError:
                gi.require_version("GIRepository", "2.0")
                new_api = False

            from gi.repository import GIRepository

            # 010042.python.gi.line64.comment The old API had `get_default` method to obtain global singleton object; it was removed in the new API,
            # 010043.python.gi.line65.comment which requires creation of separate GIRepository instances.
            if new_api:
                repo = GIRepository.Repository()
                try:
                    repo.require(module, version, GIRepository.RepositoryLoadFlags.LAZY)
                except ValueError:
                    return None  # Module not available

                # 010045.python.gi.line73.comment The new API returns the list of shared libraries.
                sharedlibs = repo.get_shared_libraries(module)
            else:
                repo = GIRepository.Repository.get_default()
                try:
                    repo.require(module, version, GIRepository.RepositoryLoadFlags.IREPOSITORY_LOAD_FLAG_LAZY)
                except ValueError:
                    return None  # Module not available

                # 010047.python.gi.line82.comment Shared library/libraries
                # 010048.python.gi.line83.comment Comma-separated list of paths to shared libraries, or None if none are associated. Convert to list.
                sharedlibs = repo.get_shared_library(module)
                sharedlibs = [lib.strip() for lib in sharedlibs.split(",")] if sharedlibs else []

            # 010049.python.gi.line87.comment Path to .typelib file
            typelib = repo.get_typelib_path(module)

            # 010050.python.gi.line90.comment Dependencies
            # 010051.python.gi.line91.comment GIRepository.Repository.get_immediate_dependencies is available from gobject-introspection v1.44 on
            if hasattr(repo, 'get_immediate_dependencies'):
                dependencies = repo.get_immediate_dependencies(module)
            else:
                dependencies = repo.get_dependencies(module)

            return {
                'sharedlibs': sharedlibs,
                'typelib': typelib,
                'dependencies': dependencies,
            }

        # 010052.python.gi.line103.comment Try to query information; if this fails, mark module as unavailable.
        try:
            info = _get_module_info(module, self.version)
            if info is None:
                logger.debug("GI module info %s %s not found.", module, self.version)
            else:
                logger.debug("GI module info %s %s found.", module, self.version)
                self.sharedlibs = info['sharedlibs']
                self.typelib = info['typelib']
                self.dependencies = info['dependencies']
                self.available = True
        except Exception as e:
            logger.warning("Failed to query GI module %s %s: %s", module, self.version, e)

    def get_libdir(self):
        """
        Return the path to shared library used by the module. If no libraries are associated with the typelib, None is
        returned. If multiple library names are associated with the typelib, the path to the first resolved shared
        library is returned. Raises exception if module is unavailable or none of the shared libraries could be
        resolved.
        """
        # 010053.python.gi.line124.comment Module unavailable
        if not self.available:
            raise ValueError(f"Module {self.name} {self.version} is unavailable!")
        # 010054.python.gi.line127.comment Module has no associated shared libraries
        if not self.sharedlibs:
            return None
        for lib in self.sharedlibs:
            path = findSystemLibrary(lib)
            if path:
                return os.path.normpath(os.path.dirname(path))
        raise ValueError(f"Could not resolve any shared library of {self.name} {self.version}: {self.sharedlibs}!")

    def collect_typelib_data(self):
        """
        Return a tuple of (binaries, datas, hiddenimports) to be used by PyGObject related hooks.
        """
        datas = []
        binaries = []
        hiddenimports = []

        logger.debug("Collecting module data for %s %s", self.name, self.version)

        # 010055.python.gi.line146.comment Module unavailable
        if not self.available:
            raise ValueError(f"Module {self.name} {self.version} is unavailable!")

        # 010056.python.gi.line150.comment Find shared libraries
        resolved_libs = _resolveCtypesImports(self.sharedlibs)
        for resolved_lib in resolved_libs:
            logger.debug("Collecting shared library %s at %s", resolved_lib[0], resolved_lib[1])
            binaries.append((resolved_lib[1], "."))

        # 010057.python.gi.line156.comment Find and collect .typelib file. Run it through the `gir_library_path_fix` to fix the library path, if
        # 010058.python.gi.line157.comment necessary.
        typelib_entry = gir_library_path_fix(self.typelib)
        if typelib_entry:
            logger.debug('Collecting gir typelib at %s', typelib_entry[0])
            datas.append(typelib_entry)

        # 010059.python.gi.line163.comment Overrides for the module
        hiddenimports += collect_submodules('gi.overrides', lambda name: name.endswith('.' + self.name))

        # 010060.python.gi.line166.comment Module dependencies
        for dep in self.dependencies:
            dep_module, _ = dep.rsplit('-', 1)
            hiddenimports += [f'gi.repository.{dep_module}']

        return binaries, datas, hiddenimports


# 010061.python.gi.line174.comment The old function, provided for backwards compatibility in 3rd party hooks.
def get_gi_libdir(module, version):
    module_info = GiModuleInfo(module, version)
    return module_info.get_libdir()


# 010062.python.gi.line180.comment The old function, provided for backwards compatibility in 3rd party hooks.
def get_gi_typelibs(module, version):
    """
    Return a tuple of (binaries, datas, hiddenimports) to be used by PyGObject related hooks. Searches for and adds
    dependencies recursively.

    :param module: GI module name, as passed to 'gi.require_version()'
    :param version: GI module version, as passed to 'gi.require_version()'
    """
    module_info = GiModuleInfo(module, version)
    return module_info.collect_typelib_data()


def gir_library_path_fix(path):
    import subprocess

    # 010063.python.gi.line196.comment 'PyInstaller.config' cannot be imported as other top-level modules.
    from PyInstaller.config import CONF

    path = os.path.abspath(path)

    # 010064.python.gi.line201.comment On macOS we need to recompile the GIR files to reference the loader path,
    # 010065.python.gi.line202.comment but this is not necessary on other platforms.
    if compat.is_darwin:

        # 010066.python.gi.line205.comment If using a virtualenv, the base prefix and the path of the typelib
        # 010067.python.gi.line206.comment have really nothing to do with each other, so try to detect that.
        common_path = os.path.commonprefix([compat.base_prefix, path])
        if common_path == '/':
            logger.debug("virtualenv detected? fixing the gir path...")
            common_path = os.path.abspath(os.path.join(path, '..', '..', '..'))

        gir_path = os.path.join(common_path, 'share', 'gir-1.0')

        typelib_name = os.path.basename(path)
        gir_name = os.path.splitext(typelib_name)[0] + '.gir'

        gir_file = os.path.join(gir_path, gir_name)

        if not os.path.exists(gir_path):
            logger.error(
                "Unable to find gir directory: %s.\nTry installing your platform's gobject-introspection package.",
                gir_path
            )
            return None
        if not os.path.exists(gir_file):
            logger.error(
                "Unable to find gir file: %s.\nTry installing your platform's gobject-introspection package.", gir_file
            )
            return None

        with open(gir_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # 010068.python.gi.line233.comment GIR files are `XML encoded <https://developer.gnome.org/gi/stable/gi-gir-reference.html>`_,
        # 010069.python.gi.line234.comment which means they are by definition encoded using UTF-8.
        with open(os.path.join(CONF['workpath'], gir_name), 'w', encoding='utf-8') as f:
            for line in lines:
                if 'shared-library' in line:
                    split = re.split('(=)', line)
                    files = re.split('(["|,])', split[2])
                    for count, item in enumerate(files):
                        if 'lib' in item:
                            files[count] = '@loader_path/' + os.path.basename(item)
                    line = ''.join(split[0:2]) + ''.join(files)
                f.write(line)

        # 010070.python.gi.line246.comment g-ir-compiler expects a file so we cannot just pipe the fixed file to it.
        command = subprocess.Popen((
            'g-ir-compiler', os.path.join(CONF['workpath'], gir_name),
            '-o', os.path.join(CONF['workpath'], typelib_name)
        ))  # yapf: disable
        command.wait()

        return os.path.join(CONF['workpath'], typelib_name), 'gi_typelibs'
    else:
        return path, 'gi_typelibs'


@isolated.decorate
def get_glib_system_data_dirs():
    import gi
    gi.require_version('GLib', '2.0')
    from gi.repository import GLib
    return GLib.get_system_data_dirs()


def get_glib_sysconf_dirs():
    """
    Try to return the sysconf directories (e.g., /etc).
    """
    if compat.is_win:
        # 010072.python.gi.line271.comment On Windows, if you look at gtkwin32.c, sysconfdir is actually relative to the location of the GTK DLL. Since
        # 010073.python.gi.line272.comment that is what we are actually interested in (not the user path), we have to do that the hard way...
        return [os.path.join(get_gi_libdir('GLib', '2.0'), 'etc')]

    @isolated.call
    def data_dirs():
        import gi
        gi.require_version('GLib', '2.0')
        from gi.repository import GLib
        return GLib.get_system_config_dirs()

    return data_dirs


def collect_glib_share_files(*path):
    """
    Path is relative to the system data directory (e.g., /usr/share).
    """
    glib_data_dirs = get_glib_system_data_dirs()
    if glib_data_dirs is None:
        return []

    destdir = os.path.join('share', *path)

    # 010074.python.gi.line295.comment TODO: will this return too much?
    collected = []
    for data_dir in glib_data_dirs:
        p = os.path.join(data_dir, *path)
        collected += collect_system_data_files(p, destdir=destdir, include_py_files=False)

    return collected


def collect_glib_etc_files(*path):
    """
    Path is relative to the system config directory (e.g., /etc).
    """
    glib_config_dirs = get_glib_sysconf_dirs()
    if glib_config_dirs is None:
        return []

    destdir = os.path.join('etc', *path)

    # 010075.python.gi.line314.comment TODO: will this return too much?
    collected = []
    for config_dir in glib_config_dirs:
        p = os.path.join(config_dir, *path)
        collected += collect_system_data_files(p, destdir=destdir, include_py_files=False)

    return collected


_glib_translations = None


def collect_glib_translations(prog, lang_list=None):
    """
    Return a list of translations in the system locale directory whose names equal prog.mo.
    """
    global _glib_translations
    if _glib_translations is None:
        if lang_list is not None:
            trans = []
            for lang in lang_list:
                trans += collect_glib_share_files(os.path.join("locale", lang))
            _glib_translations = trans
        else:
            _glib_translations = collect_glib_share_files('locale')

    names = [os.sep + prog + '.mo', os.sep + prog + '.po']
    namelen = len(names[0])

    return [(src, dst) for src, dst in _glib_translations if src[-namelen:] in names]


# 010076.python.gi.line346.comment Not a hook utility function per-se (used by main Analysis class), but kept here to have all GLib/GObject functions
# 010077.python.gi.line347.comment in one place...
def compile_glib_schema_files(datas_toc, workdir, collect_source_files=False):
    """
    Compile collected GLib schema files. Extracts the list of GLib schema files from the given input datas TOC, copies
    them to temporary working directory, and compiles them. The resulting `gschemas.compiled` file is added to the
    output TOC, replacing any existing entry with that name. If `collect_source_files` flag is set, the source XML
    schema files are also (re)added to the output TOC; by default, they are not. This function is no-op (returns the
    original TOC) if no GLib schemas are found in TOC or if `glib-compile-schemas` executable is not found in `PATH`.
    """
    SCHEMA_DEST_DIR = pathlib.PurePath("share/glib-2.0/schemas")
    workdir = pathlib.Path(workdir)

    schema_files = []
    output_toc = []
    for toc_entry in datas_toc:
        dest_name, src_name, typecode = toc_entry
        dest_name = pathlib.PurePath(dest_name)
        src_name = pathlib.PurePath(src_name)

        # 010078.python.gi.line366.comment Pass-through for non-schema files, identified based on the destination directory.
        if dest_name.parent != SCHEMA_DEST_DIR:
            output_toc.append(toc_entry)
            continue

        # 010079.python.gi.line371.comment It seems schemas directory contains different files with different suffices:
        # 010080.python.gi.line372.comment - .gschema.xml
        # 010081.python.gi.line373.comment - .schema.override
        # 010082.python.gi.line374.comment - .enums.xml
        # 010083.python.gi.line375.comment To avoid omitting anything, simply collect everything into temporary directory.
        # 010084.python.gi.line376.comment Exemptions are gschema.dtd (which should be unnecessary) and gschemas.compiled (which we will generate
        # 010085.python.gi.line377.comment ourselves in this function).
        if src_name.name in {"gschema.dtd", "gschemas.compiled"}:
            continue

        schema_files.append(src_name)

    # 010086.python.gi.line383.comment If there are no schema files available, simply return the input datas TOC.
    if not schema_files:
        return datas_toc

    # 010087.python.gi.line387.comment Ensure that `glib-compile-schemas` executable is in PATH, just in case...
    schema_compiler_exe = shutil.which('glib-compile-schemas')
    if not schema_compiler_exe:
        logger.warning("GLib schema compiler (glib-compile-schemas) not found! Skipping GLib schema recompilation...")
        return datas_toc

    # 010088.python.gi.line393.comment If `gschemas.compiled` file already exists in the temporary working directory, record its modification time and
    # 010089.python.gi.line394.comment hash. This will allow us to restore the modification time on the newly-compiled copy, if the latter turns out
    # 010090.python.gi.line395.comment to be identical to the existing old one. Just in case, if the file becomes subject to timestamp-based caching
    # 010091.python.gi.line396.comment mechanism.
    compiled_file = workdir / "gschemas.compiled"
    old_compiled_file_hash = None
    old_compiled_file_stat = None

    if compiled_file.is_file():
        # 010092.python.gi.line402.comment Record creation/modification time
        old_compiled_file_stat = compiled_file.stat()
        # 010093.python.gi.line404.comment Compute SHA1 hash; since compiled schema files are relatively small, do it in single step.
        old_compiled_file_hash = hashlib.sha1(compiled_file.read_bytes()).digest()

    # 010094.python.gi.line407.comment Ensure that temporary working directory exists, and is empty.
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(exist_ok=True)

    # 010095.python.gi.line412.comment Copy schema (source) files to temporary working directory
    for schema_file in schema_files:
        shutil.copy(schema_file, workdir)

    # 010096.python.gi.line416.comment Compile. The glib-compile-schema might produce warnings on its own (e.g., schemas using deprecated paths, or
    # 010097.python.gi.line417.comment overrides for non-existent keys). Since these are non-actionable, capture and display them only as a DEBUG
    # 010098.python.gi.line418.comment message, or as a WARNING one if the command fails.
    logger.info("Compiling collected GLib schema files in %r...", str(workdir))
    try:
        cmd_args = [schema_compiler_exe, str(workdir), '--targetdir', str(workdir)]
        p = subprocess.run(
            cmd_args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            errors='ignore',
            encoding='utf-8',
        )
        logger.debug("Output from glib-compile-schemas:\n%s", p.stdout)
    except subprocess.CalledProcessError as e:
        # 010099.python.gi.line433.comment The called glib-compile-schema returned error. Display stdout/stderr, and return original datas TOC to
        # 010100.python.gi.line434.comment minimize damage.
        logger.warning("Failed to recompile GLib schemas! Returning collected files as-is!", exc_info=True)
        logger.warning("Output from glib-compile-schemas:\n%s", e.stdout)
        return datas_toc
    except Exception:
        # 010101.python.gi.line439.comment Compilation failed for whatever reason. Return original datas TOC to minimize damage.
        logger.warning("Failed to recompile GLib schemas! Returning collected files as-is!", exc_info=True)
        return datas_toc

    # 010102.python.gi.line443.comment Compute the checksum of the new compiled file, and if it matches the old checksum, restore the modification time.
    if old_compiled_file_hash is not None:
        new_compiled_file_hash = hashlib.sha1(compiled_file.read_bytes()).digest()
        if new_compiled_file_hash == old_compiled_file_hash:
            os.utime(compiled_file, ns=(old_compiled_file_stat.st_atime_ns, old_compiled_file_stat.st_mtime_ns))

    # 010103.python.gi.line449.comment Add the resulting gschemas.compiled file to the output TOC
    output_toc.append((str(SCHEMA_DEST_DIR / compiled_file.name), str(compiled_file), "DATA"))

    # 010104.python.gi.line452.comment Include source schema files in the output TOC (optional)
    if collect_source_files:
        for schema_file in schema_files:
            output_toc.append((str(SCHEMA_DEST_DIR / schema_file.name), str(schema_file), "DATA"))

    return output_toc
