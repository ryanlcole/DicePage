# 002720.python.utils.line1.comment -----------------------------------------------------------------------------
# 002721.python.utils.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 002722.python.utils.line3.comment
# 002723.python.utils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 002724.python.utils.line5.comment or later) with exception for distributing the bootloader.
# 002725.python.utils.line6.comment
# 002726.python.utils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002727.python.utils.line8.comment
# 002728.python.utils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 002729.python.utils.line10.comment -----------------------------------------------------------------------------
"""
Utility functions related to analyzing/bundling dependencies.
"""

import ctypes.util
import os
import re
import shutil
from types import CodeType

from PyInstaller import compat
from PyInstaller import log as logging
from PyInstaller.depend import bytecode
from PyInstaller.depend.dylib import include_library
from PyInstaller.exceptions import ExecCommandFailed

logger = logging.getLogger(__name__)


def scan_code_for_ctypes(co):
    binaries = __recursively_scan_code_objects_for_ctypes(co)

    # 002730.python.utils.line33.comment If any of the libraries has been requested with anything else than the basename, drop that entry and warn the
    # 002731.python.utils.line34.comment user - PyInstaller would need to patch the compiled pyc file to make it work correctly!
    binaries = set(binaries)
    for binary in list(binaries):
        # 002732.python.utils.line37.comment 'binary' might be in some cases None. Some Python modules (e.g., PyObjC.objc._bridgesupport) might contain
        # 002733.python.utils.line38.comment code like this:
        # 002734.python.utils.line39.comment dll = ctypes.CDLL(None)
        if not binary:
            # 002735.python.utils.line41.comment None values have to be removed too.
            binaries.remove(binary)
        elif binary != os.path.basename(binary):
            # 002736.python.utils.line44.comment TODO make these warnings show up somewhere.
            try:
                filename = co.co_filename
            except Exception:
                filename = 'UNKNOWN'
            logger.warning(
                "Ignoring %s imported from %s - only basenames are supported with ctypes imports!", binary, filename
            )
            binaries.remove(binary)

    binaries = _resolveCtypesImports(binaries)
    return binaries


def __recursively_scan_code_objects_for_ctypes(code: CodeType):
    """
    Detects ctypes dependencies, using reasonable heuristics that should cover most common ctypes usages; returns a
    list containing names of binaries detected as dependencies.
    """
    from PyInstaller.depend.bytecode import any_alias, search_recursively

    binaries = []
    ctypes_dll_names = {
        *any_alias("ctypes.CDLL"),
        *any_alias("ctypes.cdll.LoadLibrary"),
        *any_alias("ctypes.WinDLL"),
        *any_alias("ctypes.windll.LoadLibrary"),
        *any_alias("ctypes.OleDLL"),
        *any_alias("ctypes.oledll.LoadLibrary"),
        *any_alias("ctypes.PyDLL"),
        *any_alias("ctypes.pydll.LoadLibrary"),
    }
    find_library_names = {
        *any_alias("ctypes.util.find_library"),
    }

    for calls in bytecode.recursive_function_calls(code).values():
        for (name, args) in calls:
            if not len(args) == 1 or not isinstance(args[0], str):
                continue
            if name in ctypes_dll_names:
                # 002737.python.utils.line85.comment ctypes.*DLL() or ctypes.*dll.LoadLibrary()
                binaries.append(*args)
            elif name in find_library_names:
                # 002738.python.utils.line88.comment ctypes.util.find_library() needs to be handled separately, because we need to resolve the library base
                # 002739.python.utils.line89.comment name given as the argument (without prefix and suffix, e.g. 'gs') into corresponding full name (e.g.,
                # 002740.python.utils.line90.comment 'libgs.so.9').
                libname = args[0]
                if libname:
                    try:  # this try was inserted due to the ctypes bug https://github.com/python/cpython/issues/93094
                        libname = ctypes.util.find_library(libname)
                    except FileNotFoundError:
                        libname = None
                        logger.warning(
                            'ctypes.util.find_library raised a FileNotFoundError. '
                            'Supressing and assuming no lib with the name "%s" was found.', args[0]
                        )
                    if libname:
                        # 002742.python.utils.line102.comment On Windows, `find_library` may return a full pathname. See issue #1934.
                        libname = os.path.basename(libname)
                        binaries.append(libname)

    # 002743.python.utils.line106.comment The above handles any flavour of function/class call. We still need to capture the (albeit rarely used) case of
    # 002744.python.utils.line107.comment loading libraries with ctypes.cdll's getattr.
    for i in search_recursively(_scan_code_for_ctypes_getattr, code).values():
        binaries.extend(i)

    return binaries


_ctypes_getattr_regex = bytecode.bytecode_regex(
    rb"""
    # Matches 'foo.bar' or 'foo.bar.whizz'.

    # Load the 'foo'.
    (
      (?:(?:""" + bytecode._OPCODES_EXTENDED_ARG + rb""").)*
      (?:""" + bytecode._OPCODES_FUNCTION_GLOBAL + rb""").
    )

    # Load the 'bar.whizz' (one opcode per name component, each possibly preceded by name reference extension).
    (
      (?:
        (?:(?:""" + bytecode._OPCODES_EXTENDED_ARG + rb""").)*
        (?:""" + bytecode._OPCODES_FUNCTION_LOAD + rb""").
      )+
    )
"""
)


def _scan_code_for_ctypes_getattr(code: CodeType):
    """
    Detect uses of ``ctypes.cdll.library_name``, which implies that ``library_name.dll`` should be collected.
    """

    key_names = ("cdll", "oledll", "pydll", "windll")

    for match in bytecode.finditer(_ctypes_getattr_regex, code.co_code):
        name, attrs = match.groups()
        name = bytecode.load(name, code)
        attrs = bytecode.loads(attrs, code)

        if attrs and attrs[-1] == "LoadLibrary":
            continue

        # 002745.python.utils.line150.comment Capture `from ctypes import ole; ole.dll_name`.
        if len(attrs) == 1:
            if name in key_names:
                yield attrs[0] + ".dll"
        # 002746.python.utils.line154.comment Capture `import ctypes; ctypes.ole.dll_name`.
        if len(attrs) == 2:
            if name == "ctypes" and attrs[0] in key_names:
                yield attrs[1] + ".dll"


# 002747.python.utils.line160.comment TODO: reuse this code with modulegraph implementation.
def _resolveCtypesImports(cbinaries):
    """
    Completes ctypes BINARY entries for modules with their full path.

    Input is a list of c-binary-names (as found by `scan_code_instruction_for_ctypes`). Output is a list of tuples
    ready to be appended to the ``binaries`` of a modules.

    This function temporarily extents PATH, LD_LIBRARY_PATH or DYLD_LIBRARY_PATH (depending on the platform) by
    CONF['pathex'] so shared libs will be search there, too.

    Example:
    >>> _resolveCtypesImports(['libgs.so'])
    [(libgs.so', ''/usr/lib/libgs.so', 'BINARY')]
    """
    from ctypes.util import find_library

    from PyInstaller.config import CONF

    if compat.is_unix:
        envvar = "LD_LIBRARY_PATH"
    elif compat.is_darwin:
        envvar = "DYLD_LIBRARY_PATH"
    else:
        envvar = "PATH"

    def _setPaths():
        path = os.pathsep.join(CONF['pathex'])
        old = compat.getenv(envvar)
        if old is not None:
            path = os.pathsep.join((path, old))
        compat.setenv(envvar, path)
        return old

    def _restorePaths(old):
        if old is None:
            compat.unsetenv(envvar)
        else:
            compat.setenv(envvar, old)

    ret = []

    # 002748.python.utils.line202.comment Try to locate the shared library on the disk. This is done by calling ctypes.util.find_library with
    # 002749.python.utils.line203.comment ImportTracker's local paths temporarily prepended to the library search paths (and restored after the call).
    old = _setPaths()
    for cbin in cbinaries:
        try:
            # 002750.python.utils.line207.comment There is an issue with find_library() where it can run into errors trying to locate the library. See
            # 002751.python.utils.line208.comment #5734.
            cpath = find_library(os.path.splitext(cbin)[0])
        except FileNotFoundError:
            # 002752.python.utils.line211.comment In these cases, find_library() should return None.
            cpath = None
        if compat.is_unix or compat.is_cygwin:
            # 002753.python.utils.line214.comment CAVEAT: find_library() is not the correct function. ctype's documentation says that it is meant to resolve
            # 002754.python.utils.line215.comment only the filename (as a *compiler* does) not the full path. Anyway, it works well enough on Windows and
            # 002755.python.utils.line216.comment macOS. On Linux, we need to implement more code to find out the full path.
            if cpath is None:
                cpath = cbin
            # 002756.python.utils.line219.comment "man ld.so" says that we should first search LD_LIBRARY_PATH and then the ldcache.
            for d in compat.getenv(envvar, '').split(os.pathsep):
                if os.path.isfile(os.path.join(d, cpath)):
                    cpath = os.path.join(d, cpath)
                    break
            else:
                if LDCONFIG_CACHE is None:
                    load_ldconfig_cache()
                if cpath in LDCONFIG_CACHE:
                    cpath = LDCONFIG_CACHE[cpath]
                    assert os.path.isfile(cpath)
                else:
                    cpath = None
        if cpath is None:
            # 002757.python.utils.line233.comment Skip warning message if cbin (basename of library) is ignored. This prevents messages like:
            # 002758.python.utils.line234.comment 'W: library kernel32.dll required via ctypes not found'
            if not include_library(cbin):
                continue
            # 002759.python.utils.line237.comment On non-Windows, automatically ignore all ctypes-based referenes to DLL files. This complements the above
            # 002760.python.utils.line238.comment check, which might not match potential case variations (e.g., `KERNEL32.dll`, instead of `kernel32.dll`)
            # 002761.python.utils.line239.comment due to case-sensitivity of the matching that is in effect on non-Windows platforms.
            if (not compat.is_win and not compat.is_cygwin) and cbin.lower().endswith('.dll'):
                continue
            logger.warning("Library %s required via ctypes not found", cbin)
        else:
            if not include_library(cpath):
                continue
            ret.append((cbin, cpath, "BINARY"))
    _restorePaths(old)
    return ret


LDCONFIG_CACHE = None  # cache the output of `/sbin/ldconfig -p`


def load_ldconfig_cache():
    """
    Create a cache of the `ldconfig`-output to call it only once.
    It contains thousands of libraries and running it on every dylib is expensive.
    """
    global LDCONFIG_CACHE

    if LDCONFIG_CACHE is not None:
        return

    if compat.is_cygwin:
        # 002763.python.utils.line265.comment Not available under Cygwin; but we might be re-using general POSIX codepaths, and end up here. So exit early.
        LDCONFIG_CACHE = {}
        return

    if compat.is_musl:
        # 002764.python.utils.line270.comment Musl deliberately doesn't use ldconfig. The ldconfig executable either doesn't exist or it's a functionless
        # 002765.python.utils.line271.comment executable which, on calling with any arguments, simply tells you that those arguments are invalid.
        LDCONFIG_CACHE = {}
        return

    ldconfig = shutil.which('ldconfig')
    if ldconfig is None:
        # 002766.python.utils.line277.comment If `ldconfig` is not found in $PATH, search for it in some fixed directories. Simply use a second call instead
        # 002767.python.utils.line278.comment of fiddling around with checks for empty env-vars and string-concat.
        ldconfig = shutil.which('ldconfig', path='/usr/sbin:/sbin:/usr/bin:/bin')

        # 002768.python.utils.line281.comment If we still could not find the 'ldconfig' command...
        if ldconfig is None:
            LDCONFIG_CACHE = {}
            return

    if compat.is_freebsd or compat.is_openbsd:
        # 002769.python.utils.line287.comment This has a quite different format than other Unixes:
        # 002770.python.utils.line288.comment [vagrant@freebsd-10 ~]$ ldconfig -r
        # 002771.python.utils.line289.comment /var/run/ld-elf.so.hints:
        # 002772.python.utils.line290.comment search directories: /lib:/usr/lib:/usr/lib/compat:...
        # 002773.python.utils.line291.comment 0:-lgeom.5 => /lib/libgeom.so.5
        # 002774.python.utils.line292.comment 184:-lpython2.7.1 => /usr/local/lib/libpython2.7.so.1
        ldconfig_arg = '-r'
        splitlines_count = 2
        pattern = re.compile(r'^\s+\d+:-l(\S+)(\s.*)? => (\S+)')
    else:
        # 002775.python.utils.line297.comment Skip first line of the library list because it is just an informative line and might contain localized
        # 002776.python.utils.line298.comment characters. Example of first line with locale set to cs_CZ.UTF-8:
        # 002777.python.utils.line299.comment $ /sbin/ldconfig -p
        # 002778.python.utils.line300.comment V keši „/etc/ld.so.cache“ nalezeno knihoven: 2799
        # 002779.python.utils.line301.comment libzvbi.so.0 (libc6,x86-64) => /lib64/libzvbi.so.0
        # 002780.python.utils.line302.comment libzvbi-chains.so.0 (libc6,x86-64) => /lib64/libzvbi-chains.so.0
        ldconfig_arg = '-p'
        splitlines_count = 1
        pattern = re.compile(r'^\s+(\S+)(\s.*)? => (\S+)')

    try:
        text = compat.exec_command(ldconfig, ldconfig_arg)
    except ExecCommandFailed:
        logger.warning("Failed to execute ldconfig. Disabling LD cache.")
        LDCONFIG_CACHE = {}
        return

    text = text.strip().splitlines()[splitlines_count:]

    LDCONFIG_CACHE = {}
    for line in text:
        # 002781.python.utils.line318.comment :fixme: this assumes library names do not contain whitespace
        m = pattern.match(line)

        # 002782.python.utils.line321.comment Sanitize away any abnormal lines of output.
        if m is None:
            # 002783.python.utils.line323.comment Warn about it then skip the rest of this iteration.
            if re.search("Cache generated by:", line):
                # 002784.python.utils.line325.comment See #5540. This particular line is harmless.
                pass
            else:
                logger.warning("Unrecognised line of output %r from ldconfig", line)
            continue

        path = m.groups()[-1]
        if compat.is_freebsd or compat.is_openbsd:
            # 002785.python.utils.line333.comment Insert `.so` at the end of the lib's basename. soname and filename may have (different) trailing versions.
            # 002786.python.utils.line334.comment We assume the `.so` in the filename to mark the end of the lib's basename.
            bname = os.path.basename(path).split('.so', 1)[0]
            name = 'lib' + m.group(1)
            assert name.startswith(bname)
            name = bname + '.so' + name[len(bname):]
        else:
            name = m.group(1)
        # 002787.python.utils.line341.comment ldconfig may know about several versions of the same lib, e.g., different arch, different libc, etc.
        # 002788.python.utils.line342.comment Use the first entry.
        if name not in LDCONFIG_CACHE:
            LDCONFIG_CACHE[name] = path
