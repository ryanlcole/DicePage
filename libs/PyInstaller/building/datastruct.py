# 000916.python.datastruct.line1.comment -----------------------------------------------------------------------------
# 000917.python.datastruct.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 000918.python.datastruct.line3.comment
# 000919.python.datastruct.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000920.python.datastruct.line5.comment or later) with exception for distributing the bootloader.
# 000921.python.datastruct.line6.comment
# 000922.python.datastruct.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000923.python.datastruct.line8.comment
# 000924.python.datastruct.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000925.python.datastruct.line10.comment -----------------------------------------------------------------------------

import os
import pathlib
import warnings

from PyInstaller import log as logging
from PyInstaller.building.utils import _check_guts_eq
from PyInstaller.utils import misc

logger = logging.getLogger(__name__)


def unique_name(entry):
    """
    Return the filename used to enforce uniqueness for the given TOC entry.

    Parameters
    ----------
    entry : tuple

    Returns
    -------
    unique_name: str
    """
    name, path, typecode = entry
    if typecode in ('BINARY', 'DATA', 'EXTENSION', 'DEPENDENCY'):
        name = os.path.normcase(name)

    return name


# 000926.python.datastruct.line42.comment This class is deprecated and has been replaced by plain lists with explicit normalization (de-duplication) via
# 000927.python.datastruct.line43.comment `normalize_toc` and `normalize_pyz_toc` helper functions.
class TOC(list):
    """
    TOC (Table of Contents) class is a list of tuples of the form (name, path, typecode).

    typecode    name                   path                        description
    --------------------------------------------------------------------------------------
    EXTENSION   Python internal name.  Full path name in build.    Extension module.
    PYSOURCE    Python internal name.  Full path name in build.    Script.
    PYMODULE    Python internal name.  Full path name in build.    Pure Python module (including __init__ modules).
    PYZ         Runtime name.          Full path name in build.    A .pyz archive (ZlibArchive data structure).
    PKG         Runtime name.          Full path name in build.    A .pkg archive (Carchive data structure).
    BINARY      Runtime name.          Full path name in build.    Shared library.
    DATA        Runtime name.          Full path name in build.    Arbitrary files.
    OPTION      The option.            Unused.                     Python runtime option (frozen into executable).

    A TOC contains various types of files. A TOC contains no duplicates and preserves order.
    PyInstaller uses TOC data type to collect necessary files bundle them into an executable.
    """
    def __init__(self, initlist=None):
        super().__init__()

        # 000928.python.datastruct.line65.comment Deprecation warning
        warnings.warn(
            "TOC class is deprecated. Use a plain list of 3-element tuples instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.filenames = set()
        if initlist:
            for entry in initlist:
                self.append(entry)

    def append(self, entry):
        if not isinstance(entry, tuple):
            logger.info("TOC found a %s, not a tuple", entry)
            raise TypeError("Expected tuple, not %s." % type(entry).__name__)

        unique = unique_name(entry)

        if unique not in self.filenames:
            self.filenames.add(unique)
            super().append(entry)

    def insert(self, pos, entry):
        if not isinstance(entry, tuple):
            logger.info("TOC found a %s, not a tuple", entry)
            raise TypeError("Expected tuple, not %s." % type(entry).__name__)
        unique = unique_name(entry)

        if unique not in self.filenames:
            self.filenames.add(unique)
            super().insert(pos, entry)

    def __add__(self, other):
        result = TOC(self)
        result.extend(other)
        return result

    def __radd__(self, other):
        result = TOC(other)
        result.extend(self)
        return result

    def __iadd__(self, other):
        for entry in other:
            self.append(entry)
        return self

    def extend(self, other):
        # 000929.python.datastruct.line114.comment TODO: look if this can be done more efficient with out the loop, e.g. by not using a list as base at all.
        for entry in other:
            self.append(entry)

    def __sub__(self, other):
        # 000930.python.datastruct.line119.comment Construct new TOC with entries not contained in the other TOC
        other = TOC(other)
        return TOC([entry for entry in self if unique_name(entry) not in other.filenames])

    def __rsub__(self, other):
        result = TOC(other)
        return result.__sub__(self)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key == slice(None, None, None):
                # 000931.python.datastruct.line130.comment special case: set the entire list
                self.filenames = set()
                self.clear()
                self.extend(value)
                return
            else:
                raise KeyError("TOC.__setitem__ doesn't handle slices")

        else:
            old_value = self[key]
            old_name = unique_name(old_value)
            self.filenames.remove(old_name)

            new_name = unique_name(value)
            if new_name not in self.filenames:
                self.filenames.add(new_name)
                super(TOC, self).__setitem__(key, value)


class Target:
    invcnum = 0

    def __init__(self):
        from PyInstaller.config import CONF

        # 000932.python.datastruct.line155.comment Get a (per class) unique number to avoid conflicts between toc objects
        self.invcnum = self.__class__.invcnum
        self.__class__.invcnum += 1
        self.tocfilename = os.path.join(CONF['workpath'], '%s-%02d.toc' % (self.__class__.__name__, self.invcnum))
        self.tocbasename = os.path.basename(self.tocfilename)
        self.dependencies = []

    def __postinit__(self):
        """
        Check if the target need to be rebuild and if so, re-assemble.

        `__postinit__` is to be called at the end of `__init__` of every subclass of Target. `__init__` is meant to
        setup the parameters and `__postinit__` is checking if rebuild is required and in case calls `assemble()`
        """
        logger.info("checking %s", self.__class__.__name__)
        data = None
        last_build = misc.mtime(self.tocfilename)
        if last_build == 0:
            logger.info("Building %s because %s is non existent", self.__class__.__name__, self.tocbasename)
        else:
            try:
                data = misc.load_py_data_struct(self.tocfilename)
            except Exception:
                logger.info("Building because %s is bad", self.tocbasename)
            else:
                # 000933.python.datastruct.line180.comment create a dict for easier access
                data = dict(zip((g[0] for g in self._GUTS), data))
        # 000934.python.datastruct.line182.comment assemble if previous data was not found or is outdated
        if not data or self._check_guts(data, last_build):
            self.assemble()
            self._save_guts()

    _GUTS = []

    def _check_guts(self, data, last_build):
        """
        Returns True if rebuild/assemble is required.
        """
        if len(data) != len(self._GUTS):
            logger.info("Building because %s is bad", self.tocbasename)
            return True
        for attr, func in self._GUTS:
            if func is None:
                # 000935.python.datastruct.line198.comment no check for this value
                continue
            if func(attr, data[attr], getattr(self, attr), last_build):
                return True
        return False

    def _save_guts(self):
        """
        Save the input parameters and the work-product of this run to maybe avoid regenerating it later.
        """
        data = tuple(getattr(self, g[0]) for g in self._GUTS)
        misc.save_py_data_struct(self.tocfilename, data)


class Tree(Target, list):
    """
    This class is a way of creating a TOC (Table of Contents) list that describes some or all of the files within a
    directory.
    """
    def __init__(self, root=None, prefix=None, excludes=None, typecode='DATA'):
        """
        root
                The root of the tree (on the build system).
        prefix
                Optional prefix to the names of the target system.
        excludes
                A list of names to exclude. Two forms are allowed:

                    name
                        Files with this basename will be excluded (do not include the path).
                    *.ext
                        Any file with the given extension will be excluded.
        typecode
                The typecode to be used for all files found in this tree. See the TOC class for for information about
                the typcodes.
        """
        Target.__init__(self)
        list.__init__(self)
        self.root = root
        self.prefix = prefix
        self.excludes = excludes
        self.typecode = typecode
        if excludes is None:
            self.excludes = []
        self.__postinit__()

    _GUTS = (  # input parameters
        ('root', _check_guts_eq),
        ('prefix', _check_guts_eq),
        ('excludes', _check_guts_eq),
        ('typecode', _check_guts_eq),
        ('data', None),  # tested below
        # 000938.python.datastruct.line250.comment no calculated/analysed values
    )

    def _check_guts(self, data, last_build):
        if Target._check_guts(self, data, last_build):
            return True
        # 000939.python.datastruct.line256.comment Walk the collected directories as check if they have been changed - which means files have been added or
        # 000940.python.datastruct.line257.comment removed. There is no need to check for the files, since `Tree` is only about the directory contents (which is
        # 000941.python.datastruct.line258.comment the list of files).
        stack = [data['root']]
        while stack:
            d = stack.pop()
            if misc.mtime(d) > last_build:
                logger.info("Building %s because directory %s changed", self.tocbasename, d)
                return True
            for nm in os.listdir(d):
                path = os.path.join(d, nm)
                if os.path.isdir(path):
                    stack.append(path)
        self[:] = data['data']  # collected files
        return False

    def _save_guts(self):
        # 000943.python.datastruct.line273.comment Use the attribute `data` to save the list
        self.data = self
        super()._save_guts()
        del self.data

    def assemble(self):
        logger.info("Building Tree %s", self.tocbasename)
        stack = [(self.root, self.prefix)]
        excludes = set()
        xexcludes = set()
        for name in self.excludes:
            if name.startswith('*'):
                xexcludes.add(name[1:])
            else:
                excludes.add(name)
        result = []
        while stack:
            dir, prefix = stack.pop()
            for filename in os.listdir(dir):
                if filename in excludes:
                    continue
                ext = os.path.splitext(filename)[1]
                if ext in xexcludes:
                    continue
                fullfilename = os.path.join(dir, filename)
                if prefix:
                    resfilename = os.path.join(prefix, filename)
                else:
                    resfilename = filename
                if os.path.isdir(fullfilename):
                    stack.append((fullfilename, resfilename))
                else:
                    result.append((resfilename, fullfilename, self.typecode))
        self[:] = result


def normalize_toc(toc):
    # 000944.python.datastruct.line310.comment Default priority: 0
    _TOC_TYPE_PRIORITIES = {
        # 000945.python.datastruct.line312.comment DEPENDENCY entries need to replace original entries, so they need the highest priority.
        'DEPENDENCY': 3,
        # 000946.python.datastruct.line314.comment SYMLINK entries have higher priority than other regular entries
        'SYMLINK': 2,
        # 000947.python.datastruct.line316.comment BINARY/EXTENSION entries undergo additional processing, so give them precedence over DATA and other entries.
        'BINARY': 1,
        'EXTENSION': 1,
    }

    def _type_case_normalization_fcn(typecode):
        # 000948.python.datastruct.line322.comment Case-normalize all entries except OPTION.
        return typecode not in {
            "OPTION",
        }

    return _normalize_toc(toc, _TOC_TYPE_PRIORITIES, _type_case_normalization_fcn)


def normalize_pyz_toc(toc):
    # 000949.python.datastruct.line331.comment Default priority: 0
    _TOC_TYPE_PRIORITIES = {
        # 000950.python.datastruct.line333.comment Ensure that entries with higher optimization level take precedence.
        'PYMODULE-2': 2,
        'PYMODULE-1': 1,
        'PYMODULE': 0,
    }

    return _normalize_toc(toc, _TOC_TYPE_PRIORITIES)


def _normalize_toc(toc, toc_type_priorities, type_case_normalization_fcn=lambda typecode: False):
    options_toc = []
    tmp_toc = dict()
    for dest_name, src_name, typecode in toc:
        # 000951.python.datastruct.line346.comment Exempt OPTION entries from de-duplication processing. Some options might allow being specified multiple times.
        if typecode == 'OPTION':
            options_toc.append(((dest_name, src_name, typecode)))
            continue

        # 000952.python.datastruct.line351.comment Always sanitize the dest_name with `os.path.normpath` to remove any local loops with parent directory path
        # 000953.python.datastruct.line352.comment components. `pathlib` does not seem to offer equivalent functionality.
        dest_name = os.path.normpath(dest_name)

        # 000954.python.datastruct.line355.comment Normalize the destination name for uniqueness. Use `pathlib.PurePath` to ensure that keys are both
        # 000955.python.datastruct.line356.comment case-normalized (on OSes where applicable) and directory-separator normalized (just in case).
        if type_case_normalization_fcn(typecode):
            entry_key = pathlib.PurePath(dest_name)
        else:
            entry_key = dest_name

        existing_entry = tmp_toc.get(entry_key)
        if existing_entry is None:
            # 000956.python.datastruct.line364.comment Entry does not exist - insert
            tmp_toc[entry_key] = (dest_name, src_name, typecode)
        else:
            # 000957.python.datastruct.line367.comment Entry already exists - replace if its typecode has higher priority
            _, _, existing_typecode = existing_entry
            if toc_type_priorities.get(typecode, 0) > toc_type_priorities.get(existing_typecode, 0):
                tmp_toc[entry_key] = (dest_name, src_name, typecode)

    # 000958.python.datastruct.line372.comment Return the items as list. The order matches the original order due to python dict maintaining the insertion order.
    # 000959.python.datastruct.line373.comment The exception are OPTION entries, which are now placed at the beginning of the TOC.
    return options_toc + list(tmp_toc.values())


def toc_process_symbolic_links(toc):
    """
    Process TOC entries and replace entries whose files are symbolic links with SYMLINK entries (provided original file
    is also being collected).
    """
    # 000960.python.datastruct.line382.comment Dictionary of all destination names, for a fast look-up.
    all_dest_files = set([dest_name for dest_name, src_name, typecode in toc])

    # 000961.python.datastruct.line385.comment Process the TOC to create SYMLINK entries
    new_toc = []
    for entry in toc:
        dest_name, src_name, typecode = entry

        # 000962.python.datastruct.line390.comment Skip entries that are already symbolic links
        if typecode == 'SYMLINK':
            new_toc.append(entry)
            continue

        # 000963.python.datastruct.line395.comment Skip entries without valid source name (e.g., OPTION)
        if not src_name:
            new_toc.append(entry)
            continue

        # 000964.python.datastruct.line400.comment Source path is not a symbolic link (i.e., it is a regular file or directory)
        if not os.path.islink(src_name):
            new_toc.append(entry)
            continue

        # 000965.python.datastruct.line405.comment Try preserving the symbolic link, under strict relative-relationship-preservation check
        symlink_entry = _try_preserving_symbolic_link(dest_name, src_name, all_dest_files)

        if symlink_entry:
            new_toc.append(symlink_entry)
        else:
            new_toc.append(entry)

    return new_toc


def _try_preserving_symbolic_link(dest_name, src_name, all_dest_files):
    seen_src_files = set()

    # 000966.python.datastruct.line419.comment Set initial values for the loop
    ref_src_file = src_name
    ref_dest_file = dest_name

    while True:
        # 000967.python.datastruct.line424.comment Guard against cyclic links...
        if ref_src_file in seen_src_files:
            break
        seen_src_files.add(ref_src_file)

        # 000968.python.datastruct.line429.comment Stop when referenced source file is not a symbolic link anymore.
        if not os.path.islink(ref_src_file):
            break

        # 000969.python.datastruct.line433.comment Read the symbolic link's target, but do not fully resolve it using os.path.realpath(), because there might be
        # 000970.python.datastruct.line434.comment other symbolic links involved as well (for example, /lib64 -> /usr/lib64 whereas we are processing
        # 000971.python.datastruct.line435.comment /lib64/liba.so -> /lib64/liba.so.1)
        symlink_target = os.readlink(ref_src_file)
        if os.path.isabs(symlink_target):
            break  # We support only relative symbolic links.

        ref_dest_file = os.path.join(os.path.dirname(ref_dest_file), symlink_target)
        ref_dest_file = os.path.normpath(ref_dest_file)  # remove any '..'

        ref_src_file = os.path.join(os.path.dirname(ref_src_file), symlink_target)
        ref_src_file = os.path.normpath(ref_src_file)  # remove any '..'

        # 000975.python.datastruct.line446.comment Check if referenced destination file is valid (i.e., we are collecting a file under referenced name).
        if ref_dest_file in all_dest_files:
            # 000976.python.datastruct.line448.comment Sanity check: original source name and current referenced source name must, after complete resolution,
            # 000977.python.datastruct.line449.comment point to the same file.
            if os.path.realpath(src_name) == os.path.realpath(ref_src_file):
                # 000978.python.datastruct.line451.comment Compute relative link for the destination file (might be modified, if we went over non-collected
                # 000979.python.datastruct.line452.comment intermediate links).
                rel_link = os.path.relpath(ref_dest_file, os.path.dirname(dest_name))
                return dest_name, rel_link, 'SYMLINK'

        # 000980.python.datastruct.line456.comment If referenced destination is not valid, do another iteration in case we are dealing with chained links and we
        # 000981.python.datastruct.line457.comment are not collecting an intermediate link...

    return None
