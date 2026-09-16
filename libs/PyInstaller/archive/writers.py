# 000262.python.writers.line1.comment -----------------------------------------------------------------------------
# 000263.python.writers.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 000264.python.writers.line3.comment
# 000265.python.writers.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000266.python.writers.line5.comment or later) with exception for distributing the bootloader.
# 000267.python.writers.line6.comment
# 000268.python.writers.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000269.python.writers.line8.comment
# 000270.python.writers.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000271.python.writers.line10.comment -----------------------------------------------------------------------------
"""
Utilities to create data structures for embedding Python modules and additional files into the executable.
"""

import marshal
import os
import shutil
import struct
import sys
import zlib

from PyInstaller.building.utils import get_code_object, replace_filename_in_code_object
from PyInstaller.compat import BYTECODE_MAGIC, is_win, strict_collect_mode
from PyInstaller.loader.pyimod01_archive import PYZ_ITEM_MODULE, PYZ_ITEM_NSPKG, PYZ_ITEM_PKG


class ZlibArchiveWriter:
    """
    Writer for PyInstaller's PYZ (ZlibArchive) archive. The archive is used to store collected byte-compiled Python
    modules, as individually-compressed entries.
    """
    _PYZ_MAGIC_PATTERN = b'PYZ\0'
    _HEADER_LENGTH = 12 + 5
    _COMPRESSION_LEVEL = 6  # zlib compression level

    def __init__(self, filename, entries, code_dict=None):
        """
        filename
            Target filename of the archive.
        entries
            An iterable containing entries in the form of tuples: (name, src_path, typecode), where `name` is the name
            under which the resource is stored (e.g., python module name, without suffix), `src_path` is name of the
            file from which the resource is read, and `typecode` is the Analysis-level TOC typecode (`PYMODULE`).
        code_dict
            Optional code dictionary containing code objects for analyzed/collected python modules.
        """
        code_dict = code_dict or {}

        with open(filename, "wb") as fp:
            # 000273.python.writers.line50.comment Reserve space for the header.
            fp.write(b'\0' * self._HEADER_LENGTH)

            # 000274.python.writers.line53.comment Write entries' data and collect TOC entries
            toc = []
            for entry in entries:
                toc_entry = self._write_entry(fp, entry, code_dict)
                toc.append(toc_entry)

            # 000275.python.writers.line59.comment Write TOC
            toc_offset = fp.tell()
            toc_data = marshal.dumps(toc)
            fp.write(toc_data)

            # 000276.python.writers.line64.comment Write header:
            # 000277.python.writers.line65.comment - PYZ magic pattern (4 bytes)
            # 000278.python.writers.line66.comment - python bytecode magic pattern (4 bytes)
            # 000279.python.writers.line67.comment - TOC offset (32-bit int, 4 bytes)
            # 000280.python.writers.line68.comment - 4 unused bytes
            fp.seek(0, os.SEEK_SET)

            fp.write(self._PYZ_MAGIC_PATTERN)
            fp.write(BYTECODE_MAGIC)
            fp.write(struct.pack('!i', toc_offset))

    @classmethod
    def _write_entry(cls, fp, entry, code_dict):
        name, src_path, typecode = entry
        assert typecode in {'PYMODULE', 'PYMODULE-1', 'PYMODULE-2'}

        if src_path in {'-', None}:
            # 000281.python.writers.line81.comment PEP-420 namespace package; these do not have code objects, but we still need an entry in PYZ to inform our
            # 000282.python.writers.line82.comment run-time module finder/loader of the package's existence. So create a TOC entry for 0-byte data blob,
            # 000283.python.writers.line83.comment and write no data.
            return (name, (PYZ_ITEM_NSPKG, fp.tell(), 0))

        code_object = code_dict[name]

        src_basename, _ = os.path.splitext(os.path.basename(src_path))
        if src_basename == '__init__':
            typecode = PYZ_ITEM_PKG
            co_filename = os.path.join(*name.split('.'), '__init__.py')
        else:
            typecode = PYZ_ITEM_MODULE
            co_filename = os.path.join(*name.split('.')) + '.py'

        # 000284.python.writers.line96.comment Replace co_filename on code object with anonymized version without absolute path to the module.
        code_object = replace_filename_in_code_object(code_object, co_filename)

        # 000285.python.writers.line99.comment Serialize
        data = marshal.dumps(code_object)

        # 000286.python.writers.line102.comment First compress, then encrypt.
        obj = zlib.compress(data, cls._COMPRESSION_LEVEL)

        # 000287.python.writers.line105.comment Create TOC entry
        toc_entry = (name, (typecode, fp.tell(), len(obj)))

        # 000288.python.writers.line108.comment Write data blob
        fp.write(obj)

        return toc_entry


class CArchiveWriter:
    """
    Writer for PyInstaller's CArchive (PKG) archive.

    This archive contains all files that are bundled within an executable; a PYZ (ZlibArchive), DLLs, Python C
    extensions, and other data files that are bundled in onefile mode.

    The archive can be read from either C (bootloader code at application's run-time) or Python (for debug purposes).
    """
    _COOKIE_MAGIC_PATTERN = b'MEI\014\013\012\013\016'

    # 000289.python.writers.line125.comment For cookie and TOC entry structure, see `PyInstaller.archive.readers.CArchiveReader`.
    _COOKIE_FORMAT = '!8sIIII64s'
    _COOKIE_LENGTH = struct.calcsize(_COOKIE_FORMAT)

    _TOC_ENTRY_FORMAT = '!IIIIBc'
    _TOC_ENTRY_LENGTH = struct.calcsize(_TOC_ENTRY_FORMAT)

    _COMPRESSION_LEVEL = 9  # zlib compression level

    def __init__(self, filename, entries, pylib_name):
        """
        filename
            Target filename of the archive.
        entries
            An iterable containing entries in the form of tuples: (dest_name, src_name, compress, typecode), where
            `dest_name` is the name under which the resource is stored in the archive (and name under which it is
            extracted at runtime), `src_name` is name of the file from which the resouce is read, `compress` is a
            boolean compression flag, and `typecode` is the Analysis-level TOC typecode.
        pylib_name
            Name of the python shared library.
        """
        self._collected_names = set()  # Track collected names for strict package mode.

        with open(filename, "wb") as fp:
            # 000292.python.writers.line149.comment Write entries' data and collect TOC entries
            toc = []
            for entry in entries:
                toc_entry = self._write_entry(fp, entry)
                toc.append(toc_entry)

            # 000293.python.writers.line155.comment Write TOC
            toc_offset = fp.tell()
            toc_data = self._serialize_toc(toc)
            toc_length = len(toc_data)

            fp.write(toc_data)

            # 000294.python.writers.line162.comment Write cookie
            archive_length = toc_offset + toc_length + self._COOKIE_LENGTH
            pyvers = sys.version_info[0] * 100 + sys.version_info[1]
            cookie_data = struct.pack(
                self._COOKIE_FORMAT,
                self._COOKIE_MAGIC_PATTERN,
                archive_length,
                toc_offset,
                toc_length,
                pyvers,
                pylib_name.encode('ascii'),
            )

            fp.write(cookie_data)

    def _write_entry(self, fp, entry):
        dest_name, src_name, compress, typecode = entry

        # 000295.python.writers.line180.comment Write OPTION entries as-is, without normalizing them. This also exempts them from duplication check,
        # 000296.python.writers.line181.comment allowing them to be specified multiple times.
        if typecode == 'o':
            return self._write_blob(fp, b"", dest_name, typecode)

        # 000297.python.writers.line185.comment Ensure forward slashes in paths are on Windows converted to back slashes '\\', as on Windows the bootloader
        # 000298.python.writers.line186.comment works only with back slashes.
        dest_name = os.path.normpath(dest_name)
        if is_win and os.path.sep == '/':
            # 000299.python.writers.line189.comment When building under MSYS, the above path normalization uses Unix-style separators, so replace them
            # 000300.python.writers.line190.comment manually.
            dest_name = dest_name.replace(os.path.sep, '\\')

            # 000301.python.writers.line193.comment For symbolic link entries, also ensure that the symlink target path (stored in src_name) is using
            # 000302.python.writers.line194.comment Windows-style back slash separators.
            if typecode == 'n':
                src_name = src_name.replace(os.path.sep, '\\')

        # 000303.python.writers.line198.comment Strict pack/collect mode: keep track of the destination names, and raise an error if we try to add a duplicate
        # 000304.python.writers.line199.comment (a file with same destination name, subject to OS case normalization rules).
        if strict_collect_mode:
            normalized_dest = None
            if typecode in {'s', 's1', 's2', 'm', 'M'}:
                # 000305.python.writers.line203.comment Exempt python source scripts and modules from the check.
                pass
            else:
                # 000306.python.writers.line206.comment Everything else; normalize the case
                normalized_dest = os.path.normcase(dest_name)
            # 000307.python.writers.line208.comment Check for existing entry, if applicable
            if normalized_dest:
                if normalized_dest in self._collected_names:
                    raise ValueError(
                        f"Attempting to collect a duplicated file into CArchive: {normalized_dest} (type: {typecode})"
                    )
                self._collected_names.add(normalized_dest)

        if typecode == 'd':
            # 000308.python.writers.line217.comment Dependency; merge src_name (= reference path prefix) and dest_name (= name) into single-string format that
            # 000309.python.writers.line218.comment is parsed by bootloader.
            return self._write_blob(fp, b"", f"{src_name}:{dest_name}", typecode)
        elif typecode in {'s', 's1', 's2'}:
            # 000310.python.writers.line221.comment If it is a source code file, compile it to a code object and marshal the object, so it can be unmarshalled
            # 000311.python.writers.line222.comment by the bootloader. For that, we need to know target optimization level, which is stored in typecode.
            optim_level = {'s': 0, 's1': 1, 's2': 2}[typecode]
            code = get_code_object(dest_name, src_name, optimize=optim_level)
            co_filename = dest_name + os.path.splitext(src_name)[1]  # Use dest name with suffix from source filename.
            code = replace_filename_in_code_object(code, co_filename)
            return self._write_blob(fp, marshal.dumps(code), dest_name, 's', compress=compress)
        elif typecode in ('m', 'M'):
            # 000313.python.writers.line229.comment Read the PYC file. We do not perform compilation here (in contrast to script files in the above branch),
            # 000314.python.writers.line230.comment so typecode does not contain optimization level information.
            with open(src_name, "rb") as in_fp:
                data = in_fp.read()
            assert data[:4] == BYTECODE_MAGIC
            # 000315.python.writers.line234.comment Skip the PYC header, load the code object.
            code = marshal.loads(data[16:])
            co_filename = dest_name + '.py'  # Use dest name with added .py suffix.
            code = replace_filename_in_code_object(code, co_filename)
            # 000317.python.writers.line238.comment These module entries are loaded and executed within the bootloader, which requires only the code
            # 000318.python.writers.line239.comment object, without the PYC header.
            return self._write_blob(fp, marshal.dumps(code), dest_name, typecode, compress=compress)
        elif typecode == 'n':
            # 000319.python.writers.line242.comment Symbolic link; store target name (as NULL-terminated string)
            data = src_name.encode('utf-8') + b'\x00'
            return self._write_blob(fp, data, dest_name, typecode, compress=compress)
        else:
            return self._write_file(fp, src_name, dest_name, typecode, compress=compress)

    def _write_blob(self, out_fp, blob: bytes, dest_name, typecode, compress=False):
        """
        Write the binary contents (**blob**) of a small file to the archive and return the corresponding CArchive TOC
        entry.
        """
        data_offset = out_fp.tell()
        data_length = len(blob)
        if compress:
            blob = zlib.compress(blob, level=self._COMPRESSION_LEVEL)
        out_fp.write(blob)

        return (data_offset, len(blob), data_length, int(compress), typecode, dest_name)

    def _write_file(self, out_fp, src_name, dest_name, typecode, compress=False):
        """
        Stream copy a large file into the archive and return the corresponding CArchive TOC entry.
        """
        data_offset = out_fp.tell()
        data_length = os.stat(src_name).st_size
        with open(src_name, 'rb') as in_fp:
            if compress:
                tmp_buffer = bytearray(16 * 1024)
                compressor = zlib.compressobj(self._COMPRESSION_LEVEL)
                while True:
                    num_read = in_fp.readinto(tmp_buffer)
                    if not num_read:
                        break
                    out_fp.write(compressor.compress(tmp_buffer[:num_read]))
                out_fp.write(compressor.flush())
            else:
                shutil.copyfileobj(in_fp, out_fp)

        return (data_offset, out_fp.tell() - data_offset, data_length, int(compress), typecode, dest_name)

    @classmethod
    def _serialize_toc(cls, toc):
        serialized_toc = []
        for toc_entry in toc:
            data_offset, compressed_length, data_length, compress, typecode, name = toc_entry

            # 000320.python.writers.line288.comment Encode names as UTF-8. This should be safe as standard python modules only contain ASCII-characters (and
            # 000321.python.writers.line289.comment standard shared libraries should have the same), and thus the C-code still can handle this correctly.
            name = name.encode('utf-8')
            name_length = len(name) + 1  # Add 1 for string-terminating zero byte.

            # 000323.python.writers.line293.comment Ensure TOC entries are aligned on 16-byte boundary, so they can be read by bootloader (C code) on
            # 000324.python.writers.line294.comment platforms with strict data alignment requirements (for example linux on `armhf`/`armv7`, such as 32-bit
            # 000325.python.writers.line295.comment Debian Buster on Raspberry Pi).
            entry_length = cls._TOC_ENTRY_LENGTH + name_length
            if entry_length % 16 != 0:
                padding_length = 16 - (entry_length % 16)
                name_length += padding_length

            # 000326.python.writers.line301.comment Serialize
            serialized_entry = struct.pack(
                cls._TOC_ENTRY_FORMAT + f"{name_length}s",  # "Ns" format automatically pads the string with zero bytes.
                cls._TOC_ENTRY_LENGTH + name_length,
                data_offset,
                compressed_length,
                data_length,
                compress,
                typecode.encode('ascii'),
                name,
            )
            serialized_toc.append(serialized_entry)

        return b''.join(serialized_toc)


class SplashWriter:
    """
    Writer for the splash screen resources archive.

    The resulting archive is added as an entry into the CArchive with the typecode PKG_ITEM_SPLASH.
    """
    # 000328.python.writers.line323.comment This struct describes the splash resources as it will be in an buffer inside the bootloader. All necessary parts
    # 000329.python.writers.line324.comment are bundled, the *_len and *_offset fields describe the data beyond this header definition.
    # 000330.python.writers.line325.comment Whereas script and image fields are binary data, the requirements fields describe an array of strings. Each string
    # 000331.python.writers.line326.comment is null-terminated in order to easily iterate over this list from within C.
    # 000332.python.writers.line327.comment
    # 000333.python.writers.line328.comment typedef struct _splash_data_header
    # 000334.python.writers.line329.comment {
    # 000335.python.writers.line330.comment char tcl_libname[16];
    # 000336.python.writers.line331.comment char tk_libname[16];
    # 000337.python.writers.line332.comment char tk_lib[16];
    # 000338.python.writers.line333.comment
    # 000339.python.writers.line334.comment uint32_t script_len;
    # 000340.python.writers.line335.comment uint32_t script_offset;
    # 000341.python.writers.line336.comment
    # 000342.python.writers.line337.comment uint32_t image_len;
    # 000343.python.writers.line338.comment uint32_t image_offset;
    # 000344.python.writers.line339.comment
    # 000345.python.writers.line340.comment uint32_t requirements_len;
    # 000346.python.writers.line341.comment uint32_t requirements_offset;
    # 000347.python.writers.line342.comment } SPLASH_DATA_HEADER;
    # 000348.python.writers.line343.comment
    _HEADER_FORMAT = '!32s 32s 16s II II II'
    _HEADER_LENGTH = struct.calcsize(_HEADER_FORMAT)

    # 000349.python.writers.line347.comment The created archive is compressed by the CArchive, so no need to compress the data here.

    def __init__(self, filename, name_list, tcl_libname, tk_libname, tklib, image, script):
        """
        Writer for splash screen resources that are bundled into the CArchive as a single archive/entry.

        :param filename: The filename of the archive to create
        :param name_list: List of filenames for the requirements array
        :param str tcl_libname: Name of the tcl shared library file
        :param str tk_libname: Name of the tk shared library file
        :param str tklib: Root of tk library (e.g. tk/)
        :param Union[str, bytes] image: Image like object
        :param str script: The tcl/tk script to execute to create the screen.
        """

        # 000350.python.writers.line362.comment Ensure forward slashes in dependency names are on Windows converted to back slashes '\\', as on Windows the
        # 000351.python.writers.line363.comment bootloader works only with back slashes.
        def _normalize_filename(filename):
            filename = os.path.normpath(filename)
            if is_win and os.path.sep == '/':
                # 000352.python.writers.line367.comment When building under MSYS, the above path normalization uses Unix-style separators, so replace them
                # 000353.python.writers.line368.comment manually.
                filename = filename.replace(os.path.sep, '\\')
            return filename

        name_list = [_normalize_filename(name) for name in name_list]

        with open(filename, "wb") as fp:
            # 000354.python.writers.line375.comment Reserve space for the header.
            fp.write(b'\0' * self._HEADER_LENGTH)

            # 000355.python.writers.line378.comment Serialize the requirements list. This list (more an array) contains the names of all files the bootloader
            # 000356.python.writers.line379.comment needs to extract before the splash screen can be started. The implementation terminates every name with a
            # 000357.python.writers.line380.comment null-byte, that keeps the list short memory wise and makes it iterable from C.
            requirements_len = 0
            requirements_offset = fp.tell()
            for name in name_list:
                name = name.encode('utf-8') + b'\0'
                fp.write(name)
                requirements_len += len(name)

            # 000358.python.writers.line388.comment Write splash script
            script_offset = fp.tell()
            script_len = len(script)
            fp.write(script.encode("utf-8"))

            # 000359.python.writers.line393.comment Write splash image. If image is a bytes buffer, it is written directly into the archive. Otherwise, it
            # 000360.python.writers.line394.comment is assumed to be a path and the file is copied into the archive.
            image_offset = fp.tell()
            if isinstance(image, bytes):
                # 000361.python.writers.line397.comment Image was converted by PIL/Pillow and is already in buffer
                image_len = len(image)
                fp.write(image)
            else:
                # 000362.python.writers.line401.comment Read image into buffer
                with open(image, 'rb') as image_fp:
                    image_data = image_fp.read()
                image_len = len(image_data)
                fp.write(image_data)
                del image_data

            # 000363.python.writers.line408.comment The following strings are written to 16-character fields with zero-padding, which means that we need to
            # 000364.python.writers.line409.comment ensure that their length is strictly below 16 characters (if it were exactly 16, the field would have no
            # 000365.python.writers.line410.comment terminating NULL character!).
            def _encode_str(value, field_name, limit):
                enc_value = value.encode("utf-8")
                if len(enc_value) >= limit:
                    raise ValueError(
                        f"Length of the encoded field {field_name!r} ({len(enc_value)}) is greater or equal to the "
                        f"limit of {limit} characters!"
                    )

                return enc_value

            # 000366.python.writers.line421.comment Write header
            header_data = struct.pack(
                self._HEADER_FORMAT,
                _encode_str(tcl_libname, 'tcl_libname', 32),
                _encode_str(tk_libname, 'tk_libname', 32),
                _encode_str(tklib, 'tklib', 16),
                script_len,
                script_offset,
                image_len,
                image_offset,
                requirements_len,
                requirements_offset,
            )

            fp.seek(0, os.SEEK_SET)
            fp.write(header_data)
