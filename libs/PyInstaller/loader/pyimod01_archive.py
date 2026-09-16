# 009308.python.pyimod01_archive.line1.comment -----------------------------------------------------------------------------
# 009309.python.pyimod01_archive.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 009310.python.pyimod01_archive.line3.comment
# 009311.python.pyimod01_archive.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 009312.python.pyimod01_archive.line5.comment or later) with exception for distributing the bootloader.
# 009313.python.pyimod01_archive.line6.comment
# 009314.python.pyimod01_archive.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009315.python.pyimod01_archive.line8.comment
# 009316.python.pyimod01_archive.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 009317.python.pyimod01_archive.line10.comment -----------------------------------------------------------------------------

# 009318.python.pyimod01_archive.line12.comment **NOTE** This module is used during bootstrap.
# 009319.python.pyimod01_archive.line13.comment Import *ONLY* builtin modules or modules that are collected into the base_library.zip archive.
# 009320.python.pyimod01_archive.line14.comment List of built-in modules: sys.builtin_module_names
# 009321.python.pyimod01_archive.line15.comment List of modules collected into base_library.zip: PyInstaller.compat.PY3_BASE_MODULES

import os
import struct
import marshal
import zlib

# 009322.python.pyimod01_archive.line22.comment In Python3, the MAGIC_NUMBER value is available in the importlib module. However, in the bootstrap phase we cannot use
# 009323.python.pyimod01_archive.line23.comment importlib directly, but rather its frozen variant.
import _frozen_importlib

PYTHON_MAGIC_NUMBER = _frozen_importlib._bootstrap_external.MAGIC_NUMBER

# 009324.python.pyimod01_archive.line28.comment Type codes for PYZ PYZ entries
PYZ_ITEM_MODULE = 0
PYZ_ITEM_PKG = 1
PYZ_ITEM_DATA = 2  # deprecated; PYZ does not contain any data entries anymore
PYZ_ITEM_NSPKG = 3  # PEP-420 namespace package


class ArchiveReadError(RuntimeError):
    pass


class ZlibArchiveReader:
    """
    Reader for PyInstaller's PYZ (ZlibArchive) archive. The archive is used to store collected byte-compiled Python
    modules, as individually-compressed entries.
    """
    _PYZ_MAGIC_PATTERN = b'PYZ\0'

    def __init__(self, filename, start_offset=None, check_pymagic=False):
        self._filename = filename
        self._start_offset = start_offset

        self.toc = {}

        # 009327.python.pyimod01_archive.line52.comment If no offset is given, try inferring it from filename
        if start_offset is None:
            self._filename, self._start_offset = self._parse_offset_from_filename(filename)

        # 009328.python.pyimod01_archive.line56.comment Parse header and load TOC. Standard header contains 12 bytes: PYZ magic pattern, python bytecode magic
        # 009329.python.pyimod01_archive.line57.comment pattern, and offset to TOC (32-bit integer). It might be followed by additional fields, depending on
        # 009330.python.pyimod01_archive.line58.comment implementation version.
        with open(self._filename, "rb") as fp:
            # 009331.python.pyimod01_archive.line60.comment Read PYZ magic pattern, located at the start of the file
            fp.seek(self._start_offset, os.SEEK_SET)

            magic = fp.read(len(self._PYZ_MAGIC_PATTERN))
            if magic != self._PYZ_MAGIC_PATTERN:
                raise ArchiveReadError("PYZ magic pattern mismatch!")

            # 009332.python.pyimod01_archive.line67.comment Read python magic/version number
            pymagic = fp.read(len(PYTHON_MAGIC_NUMBER))
            if check_pymagic and pymagic != PYTHON_MAGIC_NUMBER:
                raise ArchiveReadError("Python magic pattern mismatch!")

            # 009333.python.pyimod01_archive.line72.comment Read TOC offset
            toc_offset, *_ = struct.unpack('!i', fp.read(4))

            # 009334.python.pyimod01_archive.line75.comment Load TOC
            fp.seek(self._start_offset + toc_offset, os.SEEK_SET)
            self.toc = dict(marshal.load(fp))

    @staticmethod
    def _parse_offset_from_filename(filename):
        """
        Parse the numeric offset from filename, stored as: `/path/to/file?offset`.
        """
        offset = 0

        idx = filename.rfind('?')
        if idx == -1:
            return filename, offset

        try:
            offset = int(filename[idx + 1:])
            filename = filename[:idx]  # Remove the offset from filename
        except ValueError:
            # 009336.python.pyimod01_archive.line94.comment Ignore spurious "?" in the path (for example, like in Windows UNC \\?\<path>).
            pass

        return filename, offset

    def extract(self, name, raw=False):
        """
        Extract data from entry with the given name.

        If the entry belongs to a module or a package, the data is loaded (unmarshaled) into code object. To retrieve
        raw data, set `raw` flag to True.
        """
        # 009337.python.pyimod01_archive.line106.comment Look up entry
        entry = self.toc.get(name)
        if entry is None:
            raise KeyError(f"No entry named {name!r} found in the archive!")

        typecode, entry_offset, entry_length = entry

        # 009338.python.pyimod01_archive.line113.comment PEP-420 namespace package does not have a data blob.
        if typecode == PYZ_ITEM_NSPKG:
            return None

        # 009339.python.pyimod01_archive.line117.comment Read data blob
        try:
            with open(self._filename, "rb") as fp:
                fp.seek(self._start_offset + entry_offset)
                obj = fp.read(entry_length)
        except FileNotFoundError:
            # 009340.python.pyimod01_archive.line123.comment We open the archive file each time we need to read from it, to avoid locking the file by keeping it open.
            # 009341.python.pyimod01_archive.line124.comment This allows executable to be deleted or moved (renamed) while it is running, which is useful in certain
            # 009342.python.pyimod01_archive.line125.comment scenarios (e.g., automatic update that replaces the executable). The caveat is that once the executable is
            # 009343.python.pyimod01_archive.line126.comment renamed, we cannot read from its embedded PYZ archive anymore. In such case, exit with informative
            # 009344.python.pyimod01_archive.line127.comment message.
            raise SystemExit(
                f"ERROR: {self._filename} appears to have been moved or deleted since this application was launched. "
                "Continouation from this state is impossible. Exiting now."
            )

        try:
            obj = zlib.decompress(obj)
            if typecode in (PYZ_ITEM_MODULE, PYZ_ITEM_PKG) and not raw:
                obj = marshal.loads(obj)
        except EOFError as e:
            raise ImportError(f"Failed to unmarshal PYZ entry {name!r}!") from e

        return obj
