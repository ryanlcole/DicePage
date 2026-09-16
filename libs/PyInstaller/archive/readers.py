# 000198.python.readers.line1.comment -----------------------------------------------------------------------------
# 000199.python.readers.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 000200.python.readers.line3.comment
# 000201.python.readers.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000202.python.readers.line5.comment or later) with exception for distributing the bootloader.
# 000203.python.readers.line6.comment
# 000204.python.readers.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000205.python.readers.line8.comment
# 000206.python.readers.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000207.python.readers.line10.comment -----------------------------------------------------------------------------
"""
Python-based CArchive (PKG) reader implementation. Used only in the archive_viewer utility.
"""

import os
import struct

from PyInstaller.loader.pyimod01_archive import ZlibArchiveReader, ArchiveReadError


class NotAnArchiveError(TypeError):
    pass


# 000208.python.readers.line25.comment Type codes for CArchive TOC entries
PKG_ITEM_BINARY = 'b'  # binary
PKG_ITEM_DEPENDENCY = 'd'  # runtime option
PKG_ITEM_PYZ = 'z'  # zlib (pyz) - frozen Python code
PKG_ITEM_ZIPFILE = 'Z'  # zlib (pyz) - frozen Python code
PKG_ITEM_PYPACKAGE = 'M'  # Python package (__init__.py)
PKG_ITEM_PYMODULE = 'm'  # Python module
PKG_ITEM_PYSOURCE = 's'  # Python script (v3)
PKG_ITEM_DATA = 'x'  # data
PKG_ITEM_RUNTIME_OPTION = 'o'  # runtime option
PKG_ITEM_SPLASH = 'l'  # splash resources


class CArchiveReader:
    """
    Reader for PyInstaller's CArchive (PKG) archive.
    """

    # 000219.python.readers.line43.comment Cookie - holds some information for the bootloader. C struct format definition. '!' at the beginning means network
    # 000220.python.readers.line44.comment byte order. C struct looks like:
    # 000221.python.readers.line45.comment
    # 000222.python.readers.line46.comment typedef struct _archive_cookie
    # 000223.python.readers.line47.comment {
    # 000224.python.readers.line48.comment char magic[8];
    # 000225.python.readers.line49.comment uint32_t pkg_length;
    # 000226.python.readers.line50.comment uint32_t toc_offset;
    # 000227.python.readers.line51.comment uint32_t toc_length;
    # 000228.python.readers.line52.comment uint32_t python_version;
    # 000229.python.readers.line53.comment char python_libname[64];
    # 000230.python.readers.line54.comment } ARCHIVE_COOKIE;
    # 000231.python.readers.line55.comment
    _COOKIE_MAGIC_PATTERN = b'MEI\014\013\012\013\016'

    _COOKIE_FORMAT = '!8sIIII64s'
    _COOKIE_LENGTH = struct.calcsize(_COOKIE_FORMAT)

    # 000232.python.readers.line61.comment TOC entry:
    # 000233.python.readers.line62.comment
    # 000234.python.readers.line63.comment typedef struct _toc_entry
    # 000235.python.readers.line64.comment {
    # 000236.python.readers.line65.comment uint32_t entry_length;
    # 000237.python.readers.line66.comment uint32_t offset;
    # 000238.python.readers.line67.comment uint32_t length;
    # 000239.python.readers.line68.comment uint32_t uncompressed_length;
    # 000240.python.readers.line69.comment unsigned char compression_flag;
    # 000241.python.readers.line70.comment char typecode;
    # 000242.python.readers.line71.comment char name[1]; /* Variable-length name, padded to multiple of 16 */
    # 000243.python.readers.line72.comment } TOC_ENTRY;
    # 000244.python.readers.line73.comment
    _TOC_ENTRY_FORMAT = '!IIIIBc'
    _TOC_ENTRY_LENGTH = struct.calcsize(_TOC_ENTRY_FORMAT)

    def __init__(self, filename):
        self._filename = filename
        self._start_offset = 0
        self._end_offset = 0
        self._toc_offset = 0
        self._toc_length = 0

        self.toc = {}
        self.options = []

        # 000245.python.readers.line87.comment Load TOC
        with open(self._filename, "rb") as fp:
            # 000246.python.readers.line89.comment Find cookie MAGIC pattern
            cookie_start_offset = self._find_magic_pattern(fp, self._COOKIE_MAGIC_PATTERN)
            if cookie_start_offset == -1:
                raise ArchiveReadError("Could not find COOKIE magic pattern!")

            # 000247.python.readers.line94.comment Read the whole cookie
            fp.seek(cookie_start_offset, os.SEEK_SET)
            cookie_data = fp.read(self._COOKIE_LENGTH)

            magic, archive_length, toc_offset, toc_length, pyvers, pylib_name = \
                struct.unpack(self._COOKIE_FORMAT, cookie_data)

            # 000248.python.readers.line101.comment Compute start and end offset of the the archive
            self._end_offset = cookie_start_offset + self._COOKIE_LENGTH
            self._start_offset = self._end_offset - archive_length

            # 000249.python.readers.line105.comment Verify that Python shared library name is set
            if not pylib_name:
                raise ArchiveReadError("Python shared library name not set in the archive!")

            # 000250.python.readers.line109.comment Read whole toc
            fp.seek(self._start_offset + toc_offset)
            toc_data = fp.read(toc_length)

            self.toc, self.options = self._parse_toc(toc_data)

    @staticmethod
    def _find_magic_pattern(fp, magic_pattern):
        # 000251.python.readers.line117.comment Start at the end of file, and scan back-to-start
        fp.seek(0, os.SEEK_END)
        end_pos = fp.tell()

        # 000252.python.readers.line121.comment Scan from back
        SEARCH_CHUNK_SIZE = 8192
        magic_offset = -1
        while end_pos >= len(magic_pattern):
            start_pos = max(end_pos - SEARCH_CHUNK_SIZE, 0)
            chunk_size = end_pos - start_pos
            # 000253.python.readers.line127.comment Is the remaining chunk large enough to hold the pattern?
            if chunk_size < len(magic_pattern):
                break
            # 000254.python.readers.line130.comment Read and scan the chunk
            fp.seek(start_pos, os.SEEK_SET)
            buf = fp.read(chunk_size)
            pos = buf.rfind(magic_pattern)
            if pos != -1:
                magic_offset = start_pos + pos
                break
            # 000255.python.readers.line137.comment Adjust search location for next chunk; ensure proper overlap
            end_pos = start_pos + len(magic_pattern) - 1

        return magic_offset

    @classmethod
    def _parse_toc(cls, data):
        options = []
        toc = {}
        cur_pos = 0
        while cur_pos < len(data):
            # 000256.python.readers.line148.comment Read and parse the fixed-size TOC entry header
            entry_length, entry_offset, data_length, uncompressed_length, compression_flag, typecode = \
                struct.unpack(cls._TOC_ENTRY_FORMAT, data[cur_pos:(cur_pos + cls._TOC_ENTRY_LENGTH)])
            cur_pos += cls._TOC_ENTRY_LENGTH
            # 000257.python.readers.line152.comment Read variable-length name
            name_length = entry_length - cls._TOC_ENTRY_LENGTH
            name, *_ = struct.unpack(f'{name_length}s', data[cur_pos:(cur_pos + name_length)])
            cur_pos += name_length
            # 000258.python.readers.line156.comment Name string may contain up to 15 bytes of padding
            name = name.rstrip(b'\0').decode('utf-8')

            typecode = typecode.decode('ascii')

            # 000259.python.readers.line161.comment The TOC should not contain duplicates, except for OPTION entries. Therefore, keep those
            # 000260.python.readers.line162.comment in a separate list. With options, the rest of the entries do not make sense, anyway.
            if typecode == 'o':
                options.append(name)
            else:
                toc[name] = (entry_offset, data_length, uncompressed_length, compression_flag, typecode)

        return toc, options

    def extract(self, name):
        """
        Extract data for the given entry name.
        """

        entry = self.toc.get(name)
        if entry is None:
            raise KeyError(f"No entry named {name!r} found in the archive!")

        entry_offset, data_length, uncompressed_length, compression_flag, typecode = entry
        with open(self._filename, "rb") as fp:
            fp.seek(self._start_offset + entry_offset, os.SEEK_SET)
            data = fp.read(data_length)

        if compression_flag:
            import zlib
            data = zlib.decompress(data)

        return data

    def raw_pkg_data(self):
        """
        Extract complete PKG/CArchive archive from the parent file (executable).
        """
        total_length = self._end_offset - self._start_offset
        with open(self._filename, "rb") as fp:
            fp.seek(self._start_offset, os.SEEK_SET)
            return fp.read(total_length)

    def open_embedded_archive(self, name):
        """
        Open new archive reader for the embedded archive.
        """

        entry = self.toc.get(name)
        if entry is None:
            raise KeyError(f"No entry named {name!r} found in the archive!")

        entry_offset, data_length, uncompressed_length, compression_flag, typecode = entry

        if typecode == PKG_ITEM_PYZ:
            # 000261.python.readers.line211.comment Open as embedded archive, without extraction.
            return ZlibArchiveReader(self._filename, self._start_offset + entry_offset)
        elif typecode == PKG_ITEM_ZIPFILE:
            raise NotAnArchiveError("Zipfile archives not supported yet!")
        else:
            raise NotAnArchiveError(f"Entry {name!r} is not a supported embedded archive!")


def pkg_archive_contents(filename, recursive=True):
    """
    List the contents of the PKG / CArchive. If `recursive` flag is set (the default), the contents of the embedded PYZ
    archive is included as well.

    Used by the tests.
    """

    contents = []

    pkg_archive = CArchiveReader(filename)
    for name, toc_entry in pkg_archive.toc.items():
        *_, typecode = toc_entry
        contents.append(name)
        if typecode == PKG_ITEM_PYZ and recursive:
            pyz_archive = pkg_archive.open_embedded_archive(name)
            for name in pyz_archive.toc.keys():
                contents.append(name)

    return contents
