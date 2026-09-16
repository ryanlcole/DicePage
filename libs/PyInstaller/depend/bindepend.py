# 002107.python.bindepend.line1.comment -----------------------------------------------------------------------------
# 002108.python.bindepend.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 002109.python.bindepend.line3.comment
# 002110.python.bindepend.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 002111.python.bindepend.line5.comment or later) with exception for distributing the bootloader.
# 002112.python.bindepend.line6.comment
# 002113.python.bindepend.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002114.python.bindepend.line8.comment
# 002115.python.bindepend.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 002116.python.bindepend.line10.comment -----------------------------------------------------------------------------
"""
Find external dependencies of binary libraries.
"""

import ctypes.util
import functools
import os
import pathlib
import re
import sys
import sysconfig
import subprocess

from PyInstaller import compat
from PyInstaller import log as logging
from PyInstaller.depend import dylib, utils
from PyInstaller.utils.win32 import winutils

if compat.is_darwin:
    import PyInstaller.utils.osx as osxutils

logger = logging.getLogger(__name__)

_exe_machine_type = None
if compat.is_win:
    _exe_machine_type = winutils.get_pe_file_machine_type(compat.python_executable)

# 002117.python.bindepend.line38.comment - High-level binary dependency analysis


def _get_paths_for_parent_directory_preservation():
    """
    Return list of paths that serve as prefixes for parent-directory preservation of collected binaries and/or
    shared libraries. If a binary is collected from a location that starts with a path from this list, the relative
    directory structure is preserved within the frozen application bundle; otherwise, the binary is collected to the
    frozen application's top-level directory.
    """

    # 002118.python.bindepend.line49.comment Use only site-packages paths. We have no control over contents of `sys.path`, so using all paths from that may
    # 002119.python.bindepend.line50.comment lead to unintended behavior in corner cases. For example, if `sys.path` contained the drive root (see #7028),
    # 002120.python.bindepend.line51.comment all paths that do not match some other sub-path rooted in that drive will end up recognized as relative to the
    # 002121.python.bindepend.line52.comment drive root. In such case, any DLL collected from `c:\Windows\system32` will be collected into `Windows\system32`
    # 002122.python.bindepend.line53.comment sub-directory; ucrt DLLs collected from MSVC or Windows SDK installed in `c:\Program Files\...` will end up
    # 002123.python.bindepend.line54.comment collected into `Program Files\...` subdirectory; etc.
    # 002124.python.bindepend.line55.comment
    # 002125.python.bindepend.line56.comment On the other hand, the DLL parent directory preservation is primarily aimed at packages installed via PyPI
    # 002126.python.bindepend.line57.comment wheels, which are typically installed into site-packages. Therefore, limiting the directory preservation for
    # 002127.python.bindepend.line58.comment shared libraries collected from site-packages should do the trick, and should be reasonably safe.
    import site

    orig_paths = site.getsitepackages()
    orig_paths.append(site.getusersitepackages())

    # 002128.python.bindepend.line64.comment Explicitly excluded paths. `site.getsitepackages` seems to include `sys.prefix`, which we need to exclude, to
    # 002129.python.bindepend.line65.comment avoid issue swith DLLs in its sub-directories. We need both resolved and unresolved variant to handle cases
    # 002130.python.bindepend.line66.comment where `base_prefix` itself is a symbolic link (e.g., `scoop`-installed python on Windows, see #8023).
    excluded_paths = {
        pathlib.Path(sys.base_prefix),
        pathlib.Path(sys.base_prefix).resolve(),
        pathlib.Path(sys.prefix),
        pathlib.Path(sys.prefix).resolve(),
    }

    # 002131.python.bindepend.line74.comment For each path in orig_paths, append a resolved variant. This helps with linux venv where we need to consider
    # 002132.python.bindepend.line75.comment both `venv/lib/python3.11/site-packages` and `venv/lib/python3.11/site-packages` and `lib64` is a symlink
    # 002133.python.bindepend.line76.comment to `lib`.
    orig_paths += [pathlib.Path(path).resolve() for path in orig_paths]

    paths = set()
    for path in orig_paths:
        if not path:
            continue
        path = pathlib.Path(path)
        # 002134.python.bindepend.line84.comment Filter out non-directories (e.g., /path/to/python3x.zip) or non-existent paths
        if not path.is_dir():
            continue
        # 002135.python.bindepend.line87.comment Filter out explicitly excluded paths
        if path in excluded_paths:
            continue
        paths.add(path)

    # 002136.python.bindepend.line92.comment Sort by length (in term of path components) to ensure match against the longest common prefix (for example, match
    # 002137.python.bindepend.line93.comment /path/to/venv/lib/site-packages instead of /path/to/venv when both paths are in site paths).
    paths = sorted(paths, key=lambda x: len(x.parents), reverse=True)

    return paths


def _select_destination_directory(src_filename, parent_dir_preservation_paths):
    # 002138.python.bindepend.line100.comment Check parent directory preservation paths
    for parent_dir_preservation_path in parent_dir_preservation_paths:
        if parent_dir_preservation_path in src_filename.parents:
            # 002139.python.bindepend.line103.comment Collect into corresponding sub-directory.
            return src_filename.relative_to(parent_dir_preservation_path)

    # 002140.python.bindepend.line106.comment Collect into top-level directory.
    return src_filename.name


def binary_dependency_analysis(binaries, search_paths=None, symlink_suppression_patterns=None):
    """
    Perform binary dependency analysis on the given TOC list of collected binaries, by recursively scanning each binary
    for linked dependencies (shared library imports). Returns new TOC list that contains both original entries and their
    binary dependencies.

    Additional search paths for dependencies' full path resolution may be supplied via optional argument.
    """

    # 002141.python.bindepend.line119.comment Get all path prefixes for binaries' parent-directory preservation. For binaries collected from packages in (for
    # 002142.python.bindepend.line120.comment example) site-packages directory, we should try to preserve the parent directory structure.
    parent_dir_preservation_paths = _get_paths_for_parent_directory_preservation()

    # 002143.python.bindepend.line123.comment Keep track of processed binaries and processed dependencies.
    processed_binaries = set()
    processed_dependencies = set()

    # 002144.python.bindepend.line127.comment Keep track of unresolved dependencies, in order to defer the missing-library warnings until after everything has
    # 002145.python.bindepend.line128.comment been processed. This allows us to suppress warnings for dependencies that end up being collected anyway; for
    # 002146.python.bindepend.line129.comment details, see the end of this function.
    missing_dependencies = []

    # 002147.python.bindepend.line132.comment Populate output TOC with input binaries - this also serves as TODO list, as we iterate over it while appending
    # 002148.python.bindepend.line133.comment new entries at the end.
    output_toc = binaries[:]
    for dest_name, src_name, typecode in output_toc:
        # 002149.python.bindepend.line136.comment Do not process symbolic links (already present in input TOC list, or added during analysis below).
        if typecode == 'SYMLINK':
            continue

        # 002150.python.bindepend.line140.comment Keep track of processed binaries, to avoid unnecessarily repeating analysis of the same file. Use pathlib.Path
        # 002151.python.bindepend.line141.comment to avoid having to worry about case normalization.
        src_path = pathlib.Path(src_name)
        if src_path in processed_binaries:
            continue
        processed_binaries.add(src_path)

        logger.debug("Analyzing binary %r", src_name)

        # 002152.python.bindepend.line149.comment Analyze imports (linked dependencies)
        for dep_name, dep_src_path in get_imports(src_name, search_paths):
            logger.debug("Processing dependency, name: %r, resolved path: %r", dep_name, dep_src_path)

            # 002153.python.bindepend.line153.comment Skip unresolved dependencies. Defer the missing-library warnings until after binary dependency analysis
            # 002154.python.bindepend.line154.comment is complete.
            if not dep_src_path:
                missing_dependencies.append((dep_name, src_name))
                continue

            # 002155.python.bindepend.line159.comment Compare resolved dependency against global inclusion/exclusion rules.
            if not dylib.include_library(dep_src_path):
                logger.debug("Skipping dependency %r due to global exclusion rules.", dep_src_path)
                continue

            dep_src_path = pathlib.Path(dep_src_path)  # Turn into pathlib.Path for subsequent processing

            # 002157.python.bindepend.line166.comment Avoid processing this dependency if we have already processed it.
            if dep_src_path in processed_dependencies:
                logger.debug("Skipping dependency %r due to prior processing.", str(dep_src_path))
                continue
            processed_dependencies.add(dep_src_path)

            # 002158.python.bindepend.line172.comment Try to preserve parent directory structure, if applicable.
            # 002159.python.bindepend.line173.comment NOTE: do not resolve the source path, because on macOS and linux, it may be a versioned .so (e.g.,
            # 002160.python.bindepend.line174.comment libsomething.so.1, pointing at libsomething.so.1.2.3), and we need to collect it under original name!
            dep_dest_path = _select_destination_directory(dep_src_path, parent_dir_preservation_paths)
            dep_dest_path = pathlib.PurePath(dep_dest_path)  # Might be a str() if it is just a basename...

            # 002162.python.bindepend.line178.comment If we are collecting library into top-level directory on macOS, check whether it comes from a
            # 002163.python.bindepend.line179.comment .framework bundle. If it does, re-create the .framework bundle in the top-level directory
            # 002164.python.bindepend.line180.comment instead.
            if compat.is_darwin and dep_dest_path.parent == pathlib.PurePath('.'):
                if osxutils.is_framework_bundle_lib(dep_src_path):
                    # 002165.python.bindepend.line183.comment dst_src_path is parent_path/Name.framework/Versions/Current/Name
                    framework_parent_path = dep_src_path.parent.parent.parent.parent
                    dep_dest_path = pathlib.PurePath(dep_src_path.relative_to(framework_parent_path))

            logger.debug("Collecting dependency %r as %r.", str(dep_src_path), str(dep_dest_path))
            output_toc.append((str(dep_dest_path), str(dep_src_path), 'BINARY'))

            # 002166.python.bindepend.line190.comment On non-Windows, if we are not collecting the binary into application's top-level directory ('.'),
            # 002167.python.bindepend.line191.comment add a symbolic link from top-level directory to the actual location. This is to accommodate
            # 002168.python.bindepend.line192.comment LD_LIBRARY_PATH being set to the top-level application directory on linux (although library search
            # 002169.python.bindepend.line193.comment should be mostly done via rpaths, so this might be redundant) and to accommodate library path
            # 002170.python.bindepend.line194.comment rewriting on macOS, which assumes that the library was collected into top-level directory.
            if compat.is_win:
                # 002171.python.bindepend.line196.comment We do not use symlinks on Windows.
                pass
            elif dep_dest_path.parent == pathlib.PurePath('.'):
                # 002172.python.bindepend.line199.comment The shared library itself is being collected into top-level application directory.
                pass
            elif any(dep_src_path.match(pattern) for pattern in symlink_suppression_patterns):
                # 002173.python.bindepend.line202.comment Honor symlink suppression patterns specified by hooks.
                logger.debug(
                    "Skipping symbolic link from %r to top-level application directory due to source path matching one "
                    "of symlink suppression path patterns.", str(dep_dest_path)
                )
            else:
                logger.debug("Adding symbolic link from %r to top-level application directory.", str(dep_dest_path))
                output_toc.append((str(dep_dest_path.name), str(dep_dest_path), 'SYMLINK'))

    # 002174.python.bindepend.line211.comment Handle missing dependencies: display warnings, add missing symbolic links to top-level application directory, etc.
    seen_binaries = {
        os.path.normcase(os.path.basename(src_name)): (dest_name, src_name, typecode)
        for dest_name, src_name, typecode in output_toc if typecode != 'SYMLINK'
    }
    existing_symlinks = set([dest_name for dest_name, src_name, typecode in output_toc if typecode == 'SYMLINK'])

    for dependency_name, referring_binary in missing_dependencies:
        # 002175.python.bindepend.line219.comment Ignore libraries that we would not collect in the first place.
        if not dylib.include_library(dependency_name):
            continue

        # 002176.python.bindepend.line223.comment If the binary with a matching basename happens to be among the discovered binaries, suppress the message as
        # 002177.python.bindepend.line224.comment well. This might happen either because the library was collected by some other mechanism (for example, via
        # 002178.python.bindepend.line225.comment hook, or supplied by the user), or because it was discovered during the analysis of another binary (which,
        # 002179.python.bindepend.line226.comment for example, had properly set run-paths on Linux/macOS or was located next to that other analyzed binary on
        # 002180.python.bindepend.line227.comment Windows).
        # 002181.python.bindepend.line228.comment
        # 002182.python.bindepend.line229.comment On non-Windows, also check if symbolic link to the discovered binary already exists in the top-level
        # 002183.python.bindepend.line230.comment application directory, and if not, create it. This is important especially on macOS, where our library path
        # 002184.python.bindepend.line231.comment rewriting assumes that all dependent libraries are available in the top-level application directory, or
        # 002185.python.bindepend.line232.comment linked into it.
        dependency_basename = os.path.normcase(os.path.basename(dependency_name))
        dependency_toc_entry = seen_binaries.get(dependency_basename, None)
        if dependency_toc_entry is None:
            # 002186.python.bindepend.line236.comment Not found, emit a warning (subject to global warning suppression rules).
            if not dylib.warn_missing_lib(dependency_name):
                continue
            logger.warning(
                "Library not found: could not resolve %r, dependency of %r.", dependency_name, referring_binary
            )
        elif not compat.is_win:
            # 002187.python.bindepend.line243.comment Found; generate symbolic link if necessary.
            dependency_dest_path = pathlib.PurePath(dependency_toc_entry[0])
            dependency_src_path = pathlib.Path(dependency_toc_entry[1])

            if dependency_dest_path.parent == pathlib.PurePath('.'):
                # 002188.python.bindepend.line248.comment The binary is collected into top-level application directory.
                continue
            elif dependency_basename in existing_symlinks:
                # 002189.python.bindepend.line251.comment The symbolic link already exists.
                continue

            # 002190.python.bindepend.line254.comment Keep honoring symlink suppression patterns specified by hooks (same as in main binary dependency analysis
            # 002191.python.bindepend.line255.comment loop).
            if any(dependency_src_path.match(pattern) for pattern in symlink_suppression_patterns):
                logger.info(
                    "Missing dependency handling: skipping symbolic link from %r to top-level application directory "
                    "due to source path matching one of symlink suppression path patterns.", str(dependency_dest_path)
                )
                continue

            # 002192.python.bindepend.line263.comment Create the symbolic link
            logger.info(
                "Missing dependency handling: adding symbolic link from %r to top-level application directory.",
                str(dependency_dest_path)
            )
            output_toc.append((dependency_basename, str(dependency_dest_path), 'SYMLINK'))
            existing_symlinks.add(dependency_basename)

    return output_toc


# 002193.python.bindepend.line274.comment - Low-level import analysis


def get_imports(filename, search_paths=None):
    """
    Analyze the given binary file (shared library or executable), and obtain the list of shared libraries it imports
    (i.e., link-time dependencies).

    Returns set of tuples (name, fullpath). The name component is the referenced name, and on macOS, may not be just
    a base name. If the library's full path cannot be resolved, fullpath element is None.

    Additional list of search paths may be specified via `search_paths`, to be used as a fall-back when the
    platform-specific resolution mechanism fails to resolve a library fullpath.
    """
    if compat.is_win:
        if str(filename).lower().endswith(".manifest"):
            return []
        return _get_imports_pefile(filename, search_paths)
    elif compat.is_darwin:
        return _get_imports_macholib(filename, search_paths)
    else:
        return _get_imports_ldd(filename, search_paths)


def _get_imports_pefile(filename, search_paths):
    """
    Windows-specific helper for `get_imports`, which uses the `pefile` library to walk through PE header.
    """
    import pefile

    output = set()

    # 002194.python.bindepend.line306.comment By default, pefile library parses all PE information. We are only interested in the list of dependent dlls.
    # 002195.python.bindepend.line307.comment Performance is improved by reading only needed information. https://code.google.com/p/pefile/wiki/UsageExamples
    pe = pefile.PE(filename, fast_load=True)
    pe.parse_data_directories(
        directories=[
            pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
            pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'],
        ],
        forwarded_exports_only=True,
        import_dllnames_only=True,
    )

    # 002196.python.bindepend.line318.comment If a library has no binary dependencies, pe.DIRECTORY_ENTRY_IMPORT does not exist.
    for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
        dll_str = entry.dll.decode('utf-8')
        output.add(dll_str)

    # 002197.python.bindepend.line323.comment We must also read the exports table to find forwarded symbols:
    # 002198.python.bindepend.line324.comment http://blogs.msdn.com/b/oldnewthing/archive/2006/07/19/671238.aspx
    exported_symbols = getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None)
    if exported_symbols:
        for symbol in exported_symbols.symbols:
            if symbol.forwarder is not None:
                # 002199.python.bindepend.line329.comment symbol.forwarder is a bytes object. Convert it to a string.
                forwarder = symbol.forwarder.decode('utf-8')
                # 002200.python.bindepend.line331.comment symbol.forwarder is for example 'KERNEL32.EnterCriticalSection'
                dll = forwarder.split('.')[0]
                output.add(dll + ".dll")

    pe.close()

    # 002201.python.bindepend.line337.comment Attempt to resolve full paths to referenced DLLs. Always add the input binary's parent directory to the search
    # 002202.python.bindepend.line338.comment paths.
    search_paths = [os.path.dirname(filename)] + (search_paths or [])
    output = {(lib, resolve_library_path(lib, search_paths)) for lib in output}

    return output


def _get_imports_ldd(filename, search_paths):
    """
    Helper for `get_imports`, which uses `ldd` to analyze shared libraries. Used on Linux and other POSIX-like platforms
    (with exception of macOS).
    """

    output = set()

    # 002203.python.bindepend.line353.comment Output of ldd varies between platforms...
    if compat.is_aix:
        # 002204.python.bindepend.line355.comment Match libs of the form
        # 002205.python.bindepend.line356.comment 'archivelib.a(objectmember.so/.o)'
        # 002206.python.bindepend.line357.comment or
        # 002207.python.bindepend.line358.comment 'sharedlib.so'
        # 002208.python.bindepend.line359.comment Will not match the fake lib '/unix'
        LDD_PATTERN = re.compile(r"^\s*(((?P<libarchive>(.*\.a))(?P<objectmember>\(.*\)))|((?P<libshared>(.*\.so))))$")
    elif compat.is_hpux:
        # 002209.python.bindepend.line362.comment Match libs of the form
        # 002210.python.bindepend.line363.comment 'sharedlib.so => full-path-to-lib
        # 002211.python.bindepend.line364.comment e.g.
        # 002212.python.bindepend.line365.comment 'libpython2.7.so =>      /usr/local/lib/hpux32/libpython2.7.so'
        LDD_PATTERN = re.compile(r"^\s+(.*)\s+=>\s+(.*)$")
    elif compat.is_solar:
        # 002213.python.bindepend.line368.comment Match libs of the form
        # 002214.python.bindepend.line369.comment 'sharedlib.so => full-path-to-lib
        # 002215.python.bindepend.line370.comment e.g.
        # 002216.python.bindepend.line371.comment 'libpython2.7.so.1.0 => /usr/local/lib/libpython2.7.so.1.0'
        # 002217.python.bindepend.line372.comment Will not match the platform specific libs starting with '/platform'
        LDD_PATTERN = re.compile(r"^\s+(.*)\s+=>\s+(.*)$")
    elif compat.is_linux:
        # 002218.python.bindepend.line375.comment Match libs of the form
        # 002219.python.bindepend.line376.comment libpython3.13.so.1.0 => /home/brenainn/.pyenv/versions/3.13.0/lib/libpython3.13.so.1.0 (0x00007a9e15800000)
        # 002220.python.bindepend.line377.comment or
        # 002221.python.bindepend.line378.comment /tmp/python/install/bin/../lib/libpython3.13.so.1.0 (0x00007b9489c82000)
        LDD_PATTERN = re.compile(r"^\s*(?:(.*?)\s+=>\s+)?(.*?)\s+\(.*\)")
    else:
        LDD_PATTERN = re.compile(r"\s*(.*?)\s+=>\s+(.*?)\s+\(.*\)")

    # 002222.python.bindepend.line383.comment Resolve symlinks since GNU ldd contains a bug in processing a symlink to a binary
    # 002223.python.bindepend.line384.comment using $ORIGIN: https://sourceware.org/bugzilla/show_bug.cgi?id=25263
    p = subprocess.run(
        ['ldd', os.path.realpath(filename)],
        stdin=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding='utf-8',
    )

    ldd_warnings = []
    for line in p.stderr.splitlines():
        if not line:
            continue
        # 002224.python.bindepend.line397.comment Python extensions (including stdlib ones) are not linked against python.so but rely on Python's symbols having
        # 002225.python.bindepend.line398.comment already been loaded into symbol space at runtime. musl's ldd issues a series of harmless warnings to stderr
        # 002226.python.bindepend.line399.comment telling us that those symbols are unfindable. These should be suppressed.
        elif line.startswith("Error relocating ") and line.endswith(" symbol not found"):
            continue
        # 002227.python.bindepend.line402.comment Shared libraries should have the executable bits set; however, this is not the case for shared libraries
        # 002228.python.bindepend.line403.comment shipped in PyPI wheels, which cause ldd to emit `ldd: warning: you do not have execution permission for ...`
        # 002229.python.bindepend.line404.comment warnings. Suppress these.
        elif line.startswith("ldd: warning: you do not have execution permission for "):
            continue
        # 002230.python.bindepend.line407.comment When `ldd` is ran against a file that is not a dynamic binary (i.e., is not a binary at all, or is a static
        # 002231.python.bindepend.line408.comment binary), it emits a "not a dynamic executable" warning. Suppress it.
        elif "not a dynamic executable" in line:
            continue
        # 002232.python.bindepend.line411.comment Propagate any other warnings it might have.
        ldd_warnings.append(line)
    if ldd_warnings:
        logger.warning("ldd warnings for %r:\n%s", filename, "\n".join(ldd_warnings))

    for line in p.stdout.splitlines():
        name = None  # Referenced name
        lib = None  # Resolved library path

        m = LDD_PATTERN.search(line)
        if m:
            if compat.is_aix:
                libarchive = m.group('libarchive')
                if libarchive:
                    # 002235.python.bindepend.line425.comment We matched an archive lib with a request for a particular embedded shared object.
                    # 002236.python.bindepend.line426.comment 'archivelib.a(objectmember.so/.o)'
                    lib = libarchive
                    name = os.path.basename(lib) + m.group('objectmember')
                else:
                    # 002237.python.bindepend.line430.comment We matched a stand-alone shared library.
                    # 002238.python.bindepend.line431.comment 'sharedlib.so'
                    lib = m.group('libshared')
                    name = os.path.basename(lib)
            elif compat.is_hpux:
                name, lib = m.group(1), m.group(2)
            else:
                name, lib = m.group(1), m.group(2)
                name = name or os.path.basename(lib)
                if compat.is_linux:
                    # 002239.python.bindepend.line440.comment Skip all ld variants listed https://sourceware.org/glibc/wiki/ABIList
                    # 002240.python.bindepend.line441.comment plus musl's ld-musl-*.so.*.
                    if re.fullmatch(r"ld(64)?(-linux|-musl)?(-.+)?\.so(\..+)?", os.path.basename(lib)):
                        continue
            if name[:10] in ('linux-gate', 'linux-vdso'):
                # 002241.python.bindepend.line445.comment linux-gate is a fake library which does not exist and should be ignored. See also:
                # 002242.python.bindepend.line446.comment http://www.trilithium.com/johan/2005/08/linux-gate/
                continue

            if compat.is_cygwin:
                # 002243.python.bindepend.line450.comment exclude Windows system library
                if lib.lower().startswith('/cygdrive/c/windows/system'):
                    continue

            # 002244.python.bindepend.line454.comment Reset library path if it does not exist
            if not os.path.exists(lib):
                lib = None
        elif line.endswith("not found"):
            # 002245.python.bindepend.line458.comment On glibc-based linux distributions, missing libraries are marked with name.so => not found
            tokens = line.split('=>')
            if len(tokens) != 2:
                continue
            name = tokens[0].strip()
            lib = None
        else:
            # 002246.python.bindepend.line465.comment TODO: should we warn about unprocessed lines?
            continue

        # 002247.python.bindepend.line468.comment Fall back to searching the supplied search paths, if any.
        if not lib:
            lib = _resolve_library_path_in_search_paths(
                os.path.basename(name),  # Search for basename of the referenced name.
                search_paths,
            )

        # 002249.python.bindepend.line475.comment Normalize the resolved path, to remove any extraneous "../" elements.
        if lib:
            lib = os.path.normpath(lib)

        # 002250.python.bindepend.line479.comment Return referenced name as-is instead of computing a basename, to provide additional context when library
        # 002251.python.bindepend.line480.comment cannot be resolved.
        output.add((name, lib))

    return output


def _get_imports_macholib(filename, search_paths):
    """
    macOS-specific helper for `get_imports`, which uses `macholib` to analyze library load commands in Mach-O headers.
    """
    from macholib.dyld import dyld_find
    from macholib.mach_o import LC_RPATH
    from macholib.MachO import MachO

    try:
        from macholib.dyld import _dyld_shared_cache_contains_path
    except ImportError:
        _dyld_shared_cache_contains_path = None

    output = set()

    # 002252.python.bindepend.line501.comment Parent directory of the input binary and parent directory of python executable, used to substitute @loader_path
    # 002253.python.bindepend.line502.comment and @executable_path. The macOS dylib loader (dyld) fully resolves the symbolic links when using @loader_path
    # 002254.python.bindepend.line503.comment and @executable_path references, so we need to do the same using `os.path.realpath`.
    bin_path = os.path.dirname(os.path.realpath(filename))
    python_bin = os.path.realpath(sys.executable)
    python_bin_path = os.path.dirname(python_bin)

    def _get_referenced_libs(m):
        # 002255.python.bindepend.line509.comment Collect referenced libraries from MachO object.
        referenced_libs = set()
        for header in m.headers:
            for idx, name, lib in header.walkRelocatables():
                referenced_libs.add(lib)
        return referenced_libs

    def _get_run_paths(m):
        # 002256.python.bindepend.line517.comment Find LC_RPATH commands to collect rpaths from MachO object.
        # 002257.python.bindepend.line518.comment macholib does not handle @rpath, so we need to handle run paths ourselves.
        run_paths = []
        for header in m.headers:
            for command in header.commands:
                # 002258.python.bindepend.line522.comment A command is a tuple like:
                # 002259.python.bindepend.line523.comment (<macholib.mach_o.load_command object at 0x>,
                # 002260.python.bindepend.line524.comment <macholib.mach_o.rpath_command object at 0x>,
                # 002261.python.bindepend.line525.comment '../lib\x00\x00')
                cmd_type = command[0].cmd
                if cmd_type == LC_RPATH:
                    rpath = command[2].decode('utf-8')
                    # 002262.python.bindepend.line529.comment Remove trailing '\x00' characters. E.g., '../lib\x00\x00'
                    rpath = rpath.rstrip('\x00')
                    # 002263.python.bindepend.line531.comment If run path starts with @, ensure it starts with either @loader_path or @executable_path.
                    # 002264.python.bindepend.line532.comment We cannot process anything else.
                    if rpath.startswith("@") and not rpath.startswith(("@executable_path", "@loader_path")):
                        logger.warning("Unsupported rpath format %r found in binary %r - ignoring...", rpath, filename)
                        continue
                    run_paths.append(rpath)
        return run_paths

    @functools.lru_cache
    def get_run_paths_and_referenced_libs(filename):
        # 002265.python.bindepend.line541.comment Walk through Mach-O headers, and collect all referenced libraries and run paths.
        m = MachO(filename)
        return _get_referenced_libs(m), _get_run_paths(m)

    @functools.lru_cache
    def get_run_paths(filename):
        # 002266.python.bindepend.line547.comment Walk through Mach-O headers, and collect only run paths.
        return _get_run_paths(MachO(filename))

    # 002267.python.bindepend.line550.comment Collect referenced libraries and run paths from the input binary.
    referenced_libs, run_paths = get_run_paths_and_referenced_libs(filename)

    # 002268.python.bindepend.line553.comment On macOS, run paths (rpaths) are inherited from the executable that loads the given shared library (or from the
    # 002269.python.bindepend.line554.comment shared library that loads the given shared library). This means that shared libraries and python binary extensions
    # 002270.python.bindepend.line555.comment can reference other shared libraries using @rpath without having set any run paths themselves.
    # 002271.python.bindepend.line556.comment
    # 002272.python.bindepend.line557.comment In order to simulate the run path inheritance that happens in unfrozen python programs, we need to augment the
    # 002273.python.bindepend.line558.comment run paths from the given binary with those set by the python interpreter executable (`sys.executable`). Anaconda
    # 002274.python.bindepend.line559.comment python, for example, sets the run path on the python executable to `@loader_path/../lib`, which allows python
    # 002275.python.bindepend.line560.comment extensions to reference shared libraries in the Anaconda environment's `lib` directory via only `@rpath`
    # 002276.python.bindepend.line561.comment (for example, the `_ssl` extension can reference the OpenSSL library as `@rpath/libssl.3.dylib`). In another
    # 002277.python.bindepend.line562.comment example, python executable has its run path set to the top-level directory of its .framework bundle; in this
    # 002278.python.bindepend.line563.comment case the `ssl` extension references the OpenSSL library as `@rpath/Versions/3.10/lib/libssl.1.1.dylib`.
    run_paths += get_run_paths(python_bin)

    # 002279.python.bindepend.line566.comment This fallback should be fully superseded by the above recovery of run paths from python executable; but for now,
    # 002280.python.bindepend.line567.comment keep it around in case of unforeseen corner cases.
    run_paths.append(os.path.join(compat.base_prefix, 'lib'))

    # 002281.python.bindepend.line570.comment De-duplicate run_paths while preserving their order.
    run_paths = list(dict.fromkeys(run_paths))

    def _resolve_using_path(lib):
        # 002282.python.bindepend.line574.comment Absolute paths should not be resolved; we should just check whether the library exists or not. This used to
        # 002283.python.bindepend.line575.comment be done using macholib's dyld_find() as well (as it properly handles system libraries that are hidden on
        # 002284.python.bindepend.line576.comment Big Sur and later), but it turns out that even if given an absolute path, it gives precedence to search paths
        # 002285.python.bindepend.line577.comment from DYLD_LIBRARY_PATH. This leads to confusing errors when directory in DYLD_LIBRARY_PATH contains a file
        # 002286.python.bindepend.line578.comment (shared library or data file) that happens to have the same name as a library from a system framework.
        if os.path.isabs(lib):
            if _dyld_shared_cache_contains_path is not None and _dyld_shared_cache_contains_path(lib):
                return lib
            if os.path.isfile(lib):
                return lib
            return None

        try:
            return dyld_find(lib)
        except ValueError:
            return None

    def _resolve_using_loader_path(lib, bin_path, python_bin_path):
        # 002287.python.bindepend.line592.comment Strictly speaking, @loader_path should be anchored to parent directory of analyzed binary (`bin_path`), while
        # 002288.python.bindepend.line593.comment @executable_path should be anchored to the parent directory of the process' executable. Typically, this would
        # 002289.python.bindepend.line594.comment be python executable (`python_bin_path`). Unless we are analyzing a collected 3rd party executable; in that
        # 002290.python.bindepend.line595.comment case, `bin_path` is correct option. So we first try resolving using `bin_path`, and then fall back to
        # 002291.python.bindepend.line596.comment `python_bin_path`. This does not account for transitive run paths of higher-order dependencies, but there is
        # 002292.python.bindepend.line597.comment only so much we can do here...
        # 002293.python.bindepend.line598.comment
        # 002294.python.bindepend.line599.comment NOTE: do not use macholib's `dyld_find`, because its fallback search locations might end up resolving wrong
        # 002295.python.bindepend.line600.comment instance of the library! For example, if our `bin_path` and `python_bin_path` are anchored in an Anaconda
        # 002296.python.bindepend.line601.comment python environment and the candidate library path does not exit (because we are calling this function when
        # 002297.python.bindepend.line602.comment trying to resolve @rpath with multiple candidate run paths), we do not want to fall back to eponymous library
        # 002298.python.bindepend.line603.comment that happens to be present in the Homebrew python environment...
        if lib.startswith('@loader_path/'):
            lib = lib[len('@loader_path/'):]
        elif lib.startswith('@executable_path/'):
            lib = lib[len('@executable_path/'):]

        # 002299.python.bindepend.line609.comment Try resolving with binary's path first...
        resolved_lib = _resolve_using_path(os.path.join(bin_path, lib))
        if resolved_lib is not None:
            return resolved_lib

        # 002300.python.bindepend.line614.comment ... and fall-back to resolving with python executable's path
        return _resolve_using_path(os.path.join(python_bin_path, lib))

    # 002301.python.bindepend.line617.comment Try to resolve full path of the referenced libraries.
    for referenced_lib in referenced_libs:
        resolved_lib = None

        # 002302.python.bindepend.line621.comment If path starts with @rpath, we have to handle it ourselves.
        if referenced_lib.startswith('@rpath'):
            lib = os.path.join(*referenced_lib.split(os.sep)[1:])  # Remove the @rpath/ prefix

            # 002304.python.bindepend.line625.comment Try all run paths.
            for run_path in run_paths:
                # 002305.python.bindepend.line627.comment Join the path.
                lib_path = os.path.join(run_path, lib)

                if lib_path.startswith(("@executable_path", "@loader_path")):
                    # 002306.python.bindepend.line631.comment Run path starts with @executable_path or @loader_path.
                    lib_path = _resolve_using_loader_path(lib_path, bin_path, python_bin_path)
                else:
                    # 002307.python.bindepend.line634.comment If run path was relative, anchor it to binary's location.
                    if not os.path.isabs(lib_path):
                        os.path.join(bin_path, lib_path)
                    lib_path = _resolve_using_path(lib_path)

                if lib_path and os.path.exists(lib_path):
                    resolved_lib = lib_path
                    break
        else:
            if referenced_lib.startswith(("@executable_path", "@loader_path")):
                resolved_lib = _resolve_using_loader_path(referenced_lib, bin_path, python_bin_path)
            else:
                resolved_lib = _resolve_using_path(referenced_lib)

        # 002308.python.bindepend.line648.comment Fall back to searching the supplied search paths, if any.
        if not resolved_lib:
            resolved_lib = _resolve_library_path_in_search_paths(
                os.path.basename(referenced_lib),  # Search for basename of the referenced name.
                search_paths,
            )

        # 002310.python.bindepend.line655.comment Normalize the resolved path, to remove any extraneous "../" elements.
        if resolved_lib:
            resolved_lib = os.path.normpath(resolved_lib)

        # 002311.python.bindepend.line659.comment Return referenced library name as-is instead of computing a basename. Full referenced name carries additional
        # 002312.python.bindepend.line660.comment information that might be useful for the caller to determine how to deal with unresolved library (e.g., ignore
        # 002313.python.bindepend.line661.comment unresolved libraries that are supposed to be located in system-wide directories).
        output.add((referenced_lib, resolved_lib))

    return output


# 002314.python.bindepend.line667.comment - Library full path resolution


def resolve_library_path(name, search_paths=None):
    """
    Given a library name, attempt to resolve full path to that library. The search for library is done via
    platform-specific mechanism and fall back to optionally-provided list of search paths. Returns None if library
    cannot be resolved. If give library name is already an absolute path, the given path is returned without any
    processing.
    """
    # 002315.python.bindepend.line677.comment No-op if path is already absolute.
    if os.path.isabs(name):
        return name

    if compat.is_unix:
        # 002316.python.bindepend.line682.comment Use platform-specific helper.
        fullpath = _resolve_library_path_unix(name)
        if fullpath:
            return fullpath
        # 002317.python.bindepend.line686.comment Fall back to searching the supplied search paths, if any
        return _resolve_library_path_in_search_paths(name, search_paths)
    elif compat.is_win:
        # 002318.python.bindepend.line689.comment Try the caller-supplied search paths, if any.
        fullpath = _resolve_library_path_in_search_paths(name, search_paths)
        if fullpath:
            return fullpath

        # 002319.python.bindepend.line694.comment Fall back to default Windows search paths, using the PATH environment variable (which should also include
        # 002320.python.bindepend.line695.comment the system paths, such as c:\windows and c:\windows\system32)
        win_search_paths = [path for path in compat.getenv('PATH', '').split(os.pathsep) if path]
        return _resolve_library_path_in_search_paths(name, win_search_paths)
    else:
        return ctypes.util.find_library(name)

    return None


# 002321.python.bindepend.line704.comment Compatibility aliases for hooks from contributed hooks repository. All of these now point to the high-level
# 002322.python.bindepend.line705.comment `resolve_library_path`.
findLibrary = resolve_library_path
findSystemLibrary = resolve_library_path


def _resolve_library_path_in_search_paths(name, search_paths=None):
    """
    Low-level helper for resolving given library name to full path in given list of search paths.
    """
    for search_path in search_paths or []:
        fullpath = os.path.join(search_path, name)
        if not os.path.isfile(fullpath):
            continue

        # 002323.python.bindepend.line719.comment On Windows, ensure that architecture matches that of running python interpreter.
        if compat.is_win:
            try:
                dll_machine_type = winutils.get_pe_file_machine_type(fullpath)
            except Exception:
                # 002324.python.bindepend.line724.comment A search path might contain a DLL that we cannot analyze; for example, a stub file. Skip over.
                continue
            if dll_machine_type != _exe_machine_type:
                continue

        return os.path.normpath(fullpath)

    return None


def _resolve_library_path_unix(name):
    """
    UNIX-specific helper for resolving library path.

    Emulates the algorithm used by dlopen. `name` must include the prefix, e.g., ``libpython2.4.so``.
    """
    assert compat.is_unix, "Current implementation for Unix only (Linux, Solaris, AIX, FreeBSD)"

    if name.endswith('.so') or '.so.' in name:
        # 002325.python.bindepend.line743.comment We have been given full library name that includes suffix. Use `_resolve_library_path_in_search_paths` to find
        # 002326.python.bindepend.line744.comment the exact match.
        lib_search_func = _resolve_library_path_in_search_paths
    else:
        # 002327.python.bindepend.line747.comment We have been given a library name without suffix. Use `_which_library` as search function, which will try to
        # 002328.python.bindepend.line748.comment find library with matching basename.
        lib_search_func = _which_library

    # 002329.python.bindepend.line751.comment Look in the LD_LIBRARY_PATH according to platform.
    if compat.is_aix:
        lp = compat.getenv('LIBPATH', '')
    elif compat.is_darwin:
        lp = compat.getenv('DYLD_LIBRARY_PATH', '')
    else:
        lp = compat.getenv('LD_LIBRARY_PATH', '')
    lib = lib_search_func(name, filter(None, lp.split(os.pathsep)))

    # 002330.python.bindepend.line760.comment Look in /etc/ld.so.cache
    # 002331.python.bindepend.line761.comment Solaris does not have /sbin/ldconfig. Just check if this file exists.
    if lib is None:
        utils.load_ldconfig_cache()
        lib = utils.LDCONFIG_CACHE.get(name)
        if lib:
            assert os.path.isfile(lib)

    # 002332.python.bindepend.line768.comment Look in the known safe paths.
    if lib is None:
        # 002333.python.bindepend.line770.comment Architecture independent locations.
        paths = ['/lib', '/usr/lib']
        # 002334.python.bindepend.line772.comment Architecture dependent locations.
        if compat.architecture == '32bit':
            paths.extend(['/lib32', '/usr/lib32'])
        else:
            paths.extend(['/lib64', '/usr/lib64'])
        # 002335.python.bindepend.line777.comment Machine dependent locations.
        if compat.machine == 'intel':
            if compat.architecture == '32bit':
                paths.extend(['/usr/lib/i386-linux-gnu'])
            else:
                paths.extend(['/usr/lib/x86_64-linux-gnu'])

        # 002336.python.bindepend.line784.comment On Debian/Ubuntu /usr/bin/python is linked statically with libpython. Newer Debian/Ubuntu with multiarch
        # 002337.python.bindepend.line785.comment support puts the libpythonX.Y.so in paths like /usr/lib/i386-linux-gnu/. Try to query the arch-specific
        # 002338.python.bindepend.line786.comment sub-directory, if available.
        arch_subdir = sysconfig.get_config_var('multiarchsubdir')
        if arch_subdir:
            arch_subdir = os.path.basename(arch_subdir)
            paths.append(os.path.join('/usr/lib', arch_subdir))
        else:
            logger.debug('Multiarch directory not detected.')

        # 002339.python.bindepend.line794.comment Termux (a Ubuntu like subsystem for Android) has an additional libraries directory.
        if os.path.isdir('/data/data/com.termux/files/usr/lib'):
            paths.append('/data/data/com.termux/files/usr/lib')

        if compat.is_aix:
            paths.append('/opt/freeware/lib')
        elif compat.is_hpux:
            if compat.architecture == '32bit':
                paths.append('/usr/local/lib/hpux32')
            else:
                paths.append('/usr/local/lib/hpux64')
        elif compat.is_freebsd or compat.is_openbsd:
            paths.append('/usr/local/lib')
        lib = lib_search_func(name, paths)

    return lib


def _which_library(name, dirs):
    """
    Search for a shared library in a list of directories.

    Args:
        name:
            The library name including the `lib` prefix but excluding any `.so` suffix.
        dirs:
            An iterable of folders to search in.
    Returns:
        The path to the library if found or None otherwise.

    """
    matcher = _library_matcher(name)
    for path in filter(os.path.exists, dirs):
        for _path in os.listdir(path):
            if matcher(_path):
                return os.path.join(path, _path)


def _library_matcher(name):
    """
    Create a callable that matches libraries if **name** is a valid library prefix for input library full names.
    """
    return re.compile(name + r"[0-9]*\.").match


# 002340.python.bindepend.line839.comment - Python shared library search


def get_python_library_path():
    """
    Find Python shared library that belongs to the current interpreter.

    Return  full path to Python dynamic library or None when not found.

    PyInstaller needs to collect the Python shared library, so that bootloader can load it, import Python C API
    symbols, and use them to set up the embedded Python interpreter.

    The name of the shared library is typically fixed (`python3.X.dll` on Windows, libpython3.X.so on Unix systems,
    and `libpython3.X.dylib` on macOS for shared library builds and `Python.framework/Python` for framework build).
    Its location can usually be inferred from the Python interpreter executable, when the latter is dynamically
    linked against the shared library.

    However, some situations require extra handling due to various quirks; for example, Debian-based linux
    distributions statically link the Python interpreter executable against the Python library, while also providing
    a shared library variant for external users.
    """

    # 002341.python.bindepend.line861.comment With Windows Python builds, this is pretty straight-forward: `sys.dllhandle` provides a handle to the loaded
    # 002342.python.bindepend.line862.comment Python DLL, and we can resolve its path using `GetModuleFileName()` from win32 API.
    # 002343.python.bindepend.line863.comment This is applicable to python.org Windows builds, Anaconda on Windows, and MSYS2 Python.
    if compat.is_win:
        import _winapi
        return _winapi.GetModuleFileName(sys.dllhandle)

    # 002344.python.bindepend.line868.comment On other (POSIX) platforms, the name of the Python shared library is available in the `INSTSONAME` variable
    # 002345.python.bindepend.line869.comment exposed by the `sysconfig` module. There is also the `LDLIBRARY` variable, which points to the unversioned .so
    # 002346.python.bindepend.line870.comment symbolic link for linking purposes; however, we are interested in the actual, fully-versioned soname.
    # 002347.python.bindepend.line871.comment This should cover all variations in the naming schemes across different platforms as well as different build
    # 002348.python.bindepend.line872.comment options (debug build, free-threaded build, etc.).

    # 002349.python.bindepend.line874.comment First, try to catch Python builds that were not made with shared library (or .framework bundle on macOS) enabled.
    # 002350.python.bindepend.line875.comment In such builds, `INSTSONAME` seems to point to the static library, which is of no use to us.
    is_shared = (
        # 002351.python.bindepend.line877.comment Builds made with `--enable-shared` have `Py_ENABLE_SHARED` set to 1. This is true even for Debian-packaged
        # 002352.python.bindepend.line878.comment Python, which has the `python` executable statically linked against the Python library.
        sysconfig.get_config_var("Py_ENABLE_SHARED") or
        # 002353.python.bindepend.line880.comment On macOS, builds made with `--enable-framework` have `Py_ENABLE_SHARED` set to 0, but have `PYTHONFRAMEWORK`
        # 002354.python.bindepend.line881.comment set to a non-empty string.
        (compat.is_darwin and sysconfig.get_config_var("PYTHONFRAMEWORK"))
    )

    if is_shared:
        expected_name = sysconfig.get_config_var('INSTSONAME')
    elif compat.is_conda:
        # 002355.python.bindepend.line888.comment While Anaconda provides Python shared library, the interpreter executable and shared library seem to be made
        # 002356.python.bindepend.line889.comment separately; therefore, the interpreter has `Py_ENABLE_SHARED` set to 0 and `INSTSONAME` points to a static
        # 002357.python.bindepend.line890.comment library. And so we need to fall back to the old guess-work.
        py_major, py_minor = sys.version_info[:2]
        py_suffix = "t" if compat.is_nogil else ""  # TODO: does Anaconda provide debug builds with "d" suffix?
        if compat.is_darwin:
            # 002359.python.bindepend.line894.comment macOS
            expected_name = f"libpython{py_major}.{py_minor}{py_suffix}.dylib"
        else:
            # 002360.python.bindepend.line897.comment Linux; assume any other potential POSIX builds use the same naming scheme.
            expected_name = f"libpython{py_major}.{py_minor}{py_suffix}.so.1.0"
    else:
        # 002361.python.bindepend.line900.comment Raise PythonLibraryNotFoundError
        from PyInstaller.exceptions import PythonLibraryNotFoundError
        option_str = (
            "either the `--enable-shared` or the `--enable-framework` option"
            if compat.is_darwin else "the `--enable-shared` option"
        )
        raise PythonLibraryNotFoundError(
            "Python was built without a shared library, which is required by PyInstaller. "
            f"If you built Python from source, rebuild it with {option_str}."
        )

    # 002362.python.bindepend.line911.comment In Cygwin builds (and also MSYS2 python, although that should be handled by Windows-specific codepath...),
    # 002363.python.bindepend.line912.comment INSTSONAME is available, but the name has a ".dll.a" suffix; remove that trailing ".a".
    if (compat.is_win or compat.is_cygwin) and os.path.normcase(expected_name).endswith('.dll.a'):
        expected_name = expected_name[:-2]

    # 002364.python.bindepend.line916.comment NOTE: on macOS with .framework bundle build, INSTSONAME contains full name of the .framework library, for example
    # 002365.python.bindepend.line917.comment `Python.framework/Versions/3.13/Python`. Pre-compute a basename for comparisons that are using only basename.
    expected_basename = os.path.normcase(os.path.basename(expected_name))

    # 002366.python.bindepend.line920.comment Try to find the expected name among the libraries against which the Python executable is linked. This assumes that
    # 002367.python.bindepend.line921.comment the Python executable was not statically linked against the library (as is the case with Debian-packaged Python,
    # 002368.python.bindepend.line922.comment or Anaconda Python).
    if is_shared:
        imported_libraries = get_imports(compat.python_executable)  # (name, fullpath) tuples
        for _, lib_path in imported_libraries:
            if lib_path is None:
                continue  # Skip unresolved imports
            if os.path.normcase(os.path.basename(lib_path)) == expected_basename:  # Basename comparison
                # 002372.python.bindepend.line929.comment Python library found. Return absolute path to it.
                return lib_path

    # 002373.python.bindepend.line932.comment As a fallback, try to find the library in several "standard" search locations...
    def _find_lib_in_libdirs(name, *libdirs):
        for libdir in libdirs:
            full_path = os.path.join(libdir, name)
            if not os.path.exists(full_path):
                continue
            # 002374.python.bindepend.line938.comment Resolve potential symbolic links to achieve consistent results with linker-based search; e.g., on
            # 002375.python.bindepend.line939.comment POSIX systems, linker resolves unversioned library names (python3.X.so) to versioned ones
            # 002376.python.bindepend.line940.comment (libpython3.X.so.1.0) due to former being symbolic linkes to the latter. See #6831.
            full_path = os.path.realpath(full_path)
            if not os.path.exists(full_path):
                continue
            return full_path
        return None

    # 002377.python.bindepend.line947.comment Search the `sys.base_prefix` and `lib` directory in `sys.base_prefix`.
    # 002378.python.bindepend.line948.comment This covers various Python installations in case we fail to infer the shared library location for whatever reason;
    # 002379.python.bindepend.line949.comment Anaconda Python, `uv` and `rye` Python, etc.
    python_libname = _find_lib_in_libdirs(
        expected_name,  # Full name
        compat.base_prefix,
        os.path.join(compat.base_prefix, 'lib'),
    )
    if python_libname:
        return python_libname

    # 002381.python.bindepend.line958.comment Perform search in the configured library search locations. This should be done after exhausting all other options;
    # 002382.python.bindepend.line959.comment it primarily caters to Debian-packaged Python, but we need to make sure that we do not collect shared library from
    # 002383.python.bindepend.line960.comment system-installed Python when the current interpreter is in fact some other Python build (for example, `uv` or
    # 002384.python.bindepend.line961.comment `rye` Python of the same version as system-installed Python).
    python_libname = resolve_library_path(expected_basename)  # Basename
    if python_libname:
        return python_libname

    # 002386.python.bindepend.line966.comment Not found. Raise a PythonLibraryNotFoundError with corresponding message.
    from PyInstaller.exceptions import PythonLibraryNotFoundError

    message = f"ERROR: Python shared library ({expected_name!r}) was not found!"
    if compat.is_linux and os.path.isfile('/etc/debian_version'):
        # 002387.python.bindepend.line971.comment The shared library is provided by `libpython3.x` package (i.e., no need to install full `python3-dev`).
        pkg_name = f"libpython3.{sys.version_info.minor}"
        message += (
            " If you are using system python on Debian/Ubuntu, you might need to install a separate package by running "
            f"`apt install {pkg_name}`."
        )

    raise PythonLibraryNotFoundError(message)


# 002388.python.bindepend.line981.comment - Binary vs data (re)classification


def classify_binary_vs_data(filename):
    """
    Classify the given file as either BINARY or a DATA, using appropriate platform-specific method. Returns 'BINARY'
    or 'DATA' string depending on the determined file type, or None if classification cannot be performed (non-existing
    file, missing tool, and other errors during classification).
    """

    # 002389.python.bindepend.line991.comment We cannot classify non-existent files.
    if not os.path.isfile(filename):
        return None

    # 002390.python.bindepend.line995.comment Use platform-specific implementation.
    return _classify_binary_vs_data(filename)


if compat.is_linux:

    def _classify_binary_vs_data(filename):
        # 002391.python.bindepend.line1002.comment First check for ELF signature, in order to avoid calling `objdump` on every data file, which can be costly.
        try:
            with open(filename, 'rb') as fp:
                sig = fp.read(4)
        except Exception:
            return None

        if sig != b"\x7FELF":
            return "DATA"

        # 002392.python.bindepend.line1012.comment Verify the binary by checking if `objdump` recognizes the file. The preceding ELF signature check should
        # 002393.python.bindepend.line1013.comment ensure that this is an ELF file, while this check should ensure that it is a valid ELF file. In the future,
        # 002394.python.bindepend.line1014.comment we could try checking that the architecture matches the running platform.
        cmd_args = ['objdump', '-a', filename]
        try:
            p = subprocess.run(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                encoding='utf8',
            )
        except Exception:
            return None  # Failed to run `objdump` or `objdump` unavailable.

        return 'BINARY' if p.returncode == 0 else 'DATA'

elif compat.is_win:

    def _classify_binary_vs_data(filename):
        import pefile

        # 002396.python.bindepend.line1034.comment First check for MZ signature, which should allow us to quickly classify the majority of data files.
        try:
            with open(filename, 'rb') as fp:
                sig = fp.read(2)
        except Exception:
            return None

        if sig != b"MZ":
            return "DATA"

        # 002397.python.bindepend.line1044.comment Check if the file can be opened using `pefile`.
        try:
            with pefile.PE(filename, fast_load=True) as pe:  # noqa: F841
                pass
            return 'BINARY'
        except pefile.PEFormatError:
            return 'DATA'
        except Exception:
            pass

        return None

elif compat.is_darwin:

    def _classify_binary_vs_data(filename):
        # 002399.python.bindepend.line1059.comment See if the file can be opened using `macholib`.
        import macholib.MachO

        try:
            macho = macholib.MachO.MachO(filename)  # noqa: F841
            return 'BINARY'
        except Exception:
            # 002401.python.bindepend.line1066.comment TODO: catch only `ValueError`?
            pass

        return 'DATA'

else:

    def _classify_binary_vs_data(filename):
        # 002402.python.bindepend.line1074.comment Classification not implemented for the platform.
        return None
