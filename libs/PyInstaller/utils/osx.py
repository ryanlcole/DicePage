# 010976.python.osx.line1.comment -----------------------------------------------------------------------------
# 010977.python.osx.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 010978.python.osx.line3.comment
# 010979.python.osx.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 010980.python.osx.line5.comment or later) with exception for distributing the bootloader.
# 010981.python.osx.line6.comment
# 010982.python.osx.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 010983.python.osx.line8.comment
# 010984.python.osx.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 010985.python.osx.line10.comment -----------------------------------------------------------------------------
"""
Utils for macOS platform.
"""

import math
import os
import pathlib
import subprocess
import shutil
import tempfile

from macholib.mach_o import (
    LC_BUILD_VERSION,
    LC_CODE_SIGNATURE,
    LC_ID_DYLIB,
    LC_LOAD_DYLIB,
    LC_LOAD_UPWARD_DYLIB,
    LC_LOAD_WEAK_DYLIB,
    LC_PREBOUND_DYLIB,
    LC_REEXPORT_DYLIB,
    LC_RPATH,
    LC_SEGMENT_64,
    LC_SYMTAB,
    LC_UUID,
    LC_VERSION_MIN_MACOSX,
)
from macholib.MachO import MachO
import macholib.util

import PyInstaller.log as logging
from PyInstaller import compat

logger = logging.getLogger(__name__)


def is_homebrew_env():
    """
    Check if Python interpreter was installed via Homebrew command 'brew'.

    :return: True if Homebrew else otherwise.
    """
    # 010986.python.osx.line52.comment Python path prefix should start with Homebrew prefix.
    env_prefix = get_homebrew_prefix()
    if env_prefix and compat.base_prefix.startswith(env_prefix):
        return True
    return False


def is_macports_env():
    """
    Check if Python interpreter was installed via Macports command 'port'.

    :return: True if Macports else otherwise.
    """
    # 010987.python.osx.line65.comment Python path prefix should start with Macports prefix.
    env_prefix = get_macports_prefix()
    if env_prefix and compat.base_prefix.startswith(env_prefix):
        return True
    return False


def get_homebrew_prefix():
    """
    :return: Root path of the Homebrew environment.
    """
    prefix = shutil.which('brew')
    # 010988.python.osx.line77.comment Conversion:  /usr/local/bin/brew -> /usr/local
    prefix = os.path.dirname(os.path.dirname(prefix))
    return prefix


def get_macports_prefix():
    """
    :return: Root path of the Macports environment.
    """
    prefix = shutil.which('port')
    # 010989.python.osx.line87.comment Conversion:  /usr/local/bin/port -> /usr/local
    prefix = os.path.dirname(os.path.dirname(prefix))
    return prefix


def _find_version_cmd(header):
    """
    Helper that finds the version command in the given MachO header.
    """
    # 010990.python.osx.line96.comment The SDK version is stored in LC_BUILD_VERSION command (used when targeting the latest versions of macOS) or in
    # 010991.python.osx.line97.comment older LC_VERSION_MIN_MACOSX command. Check for presence of either.
    version_cmd = [cmd for cmd in header.commands if cmd[0].cmd in {LC_BUILD_VERSION, LC_VERSION_MIN_MACOSX}]
    assert len(version_cmd) == 1, \
        f"Expected exactly one LC_BUILD_VERSION or LC_VERSION_MIN_MACOSX command, found {len(version_cmd)}!"
    return version_cmd[0]


def get_macos_sdk_version(filename):
    """
    Obtain the version of macOS SDK against which the given binary was built.

    NOTE: currently, version is retrieved only from the first arch slice in the binary.

    :return: (major, minor, revision) tuple
    """
    binary = MachO(filename)
    header = binary.headers[0]
    # 010992.python.osx.line114.comment Find version command using helper
    version_cmd = _find_version_cmd(header)
    return _hex_triplet(version_cmd[1].sdk)


def _hex_triplet(version):
    # 010993.python.osx.line120.comment Parse SDK version number
    major = (version & 0xFF0000) >> 16
    minor = (version & 0xFF00) >> 8
    revision = (version & 0xFF)
    return major, minor, revision


def macosx_version_min(filename: str) -> tuple:
    """
    Get the -macosx-version-min used to compile a macOS binary.

    For fat binaries, the minimum version is selected.
    """
    versions = []
    for header in MachO(filename).headers:
        cmd = _find_version_cmd(header)
        if cmd[0].cmd == LC_VERSION_MIN_MACOSX:
            versions.append(cmd[1].version)
        else:
            # 010994.python.osx.line139.comment macOS >= 10.14 uses LC_BUILD_VERSION instead.
            versions.append(cmd[1].minos)

    return min(map(_hex_triplet, versions))


def set_macos_sdk_version(filename, major, minor, revision):
    """
    Overwrite the macOS SDK version declared in the given binary with the specified version.

    NOTE: currently, only version in the first arch slice is modified.
    """
    # 010995.python.osx.line151.comment Validate values
    assert 0 <= major <= 255, "Invalid major version value!"
    assert 0 <= minor <= 255, "Invalid minor version value!"
    assert 0 <= revision <= 255, "Invalid revision value!"
    # 010996.python.osx.line155.comment Open binary
    binary = MachO(filename)
    header = binary.headers[0]
    # 010997.python.osx.line158.comment Find version command using helper
    version_cmd = _find_version_cmd(header)
    # 010998.python.osx.line160.comment Write new SDK version number
    version_cmd[1].sdk = major << 16 | minor << 8 | revision
    # 010999.python.osx.line162.comment Write changes back.
    with open(binary.filename, 'rb+') as fp:
        binary.write(fp)


def fix_exe_for_code_signing(filename):
    """
    Fixes the Mach-O headers to make code signing possible.

    Code signing on macOS does not work out of the box with embedding .pkg archive into the executable.

    The fix is done this way:
    - Make the embedded .pkg archive part of the Mach-O 'String Table'. 'String Table' is at end of the macOS exe file,
      so just change the size of the table to cover the end of the file.
    - Fix the size of the __LINKEDIT segment.

    Note: the above fix works only if the single-arch thin executable or the last arch slice in a multi-arch fat
    executable is not signed, because LC_CODE_SIGNATURE comes after LC_SYMTAB, and because modification of headers
    invalidates the code signature. On modern arm64 macOS, code signature is mandatory, and therefore compilers
    create a dummy signature when executable is built. In such cases, that signature needs to be removed before this
    function is called.

    Mach-O format specification: http://developer.apple.com/documentation/Darwin/Reference/ManPages/man5/Mach-O.5.html
    """
    # 011000.python.osx.line186.comment Estimate the file size after data was appended
    file_size = os.path.getsize(filename)

    # 011001.python.osx.line189.comment Take the last available header. A single-arch thin binary contains a single slice, while a multi-arch fat binary
    # 011002.python.osx.line190.comment contains multiple, and we need to modify the last one, which is adjacent to the appended data.
    executable = MachO(filename)
    header = executable.headers[-1]

    # 011003.python.osx.line194.comment Sanity check: ensure the executable slice is not signed (otherwise signature's section comes last in the
    # 011004.python.osx.line195.comment __LINKEDIT segment).
    sign_sec = [cmd for cmd in header.commands if cmd[0].cmd == LC_CODE_SIGNATURE]
    assert len(sign_sec) == 0, "Executable contains code signature!"

    # 011005.python.osx.line199.comment Find __LINKEDIT segment by name (16-byte zero padded string)
    __LINKEDIT_NAME = b'__LINKEDIT\x00\x00\x00\x00\x00\x00'
    linkedit_seg = [cmd for cmd in header.commands if cmd[0].cmd == LC_SEGMENT_64 and cmd[1].segname == __LINKEDIT_NAME]
    assert len(linkedit_seg) == 1, "Expected exactly one __LINKEDIT segment!"
    linkedit_seg = linkedit_seg[0][1]  # Take the segment command entry
    # 011007.python.osx.line204.comment Find SYMTAB section
    symtab_sec = [cmd for cmd in header.commands if cmd[0].cmd == LC_SYMTAB]
    assert len(symtab_sec) == 1, "Expected exactly one SYMTAB section!"
    symtab_sec = symtab_sec[0][1]  # Take the symtab command entry

    # 011009.python.osx.line209.comment The string table is located at the end of the SYMTAB section, which in turn is the last section in the __LINKEDIT
    # 011010.python.osx.line210.comment segment. Therefore, the end of SYMTAB section should be aligned with the end of __LINKEDIT segment, and in turn
    # 011011.python.osx.line211.comment both should be aligned with the end of the file (as we are in the last or the only arch slice).
    # 011012.python.osx.line212.comment
    # 011013.python.osx.line213.comment However, when removing the signature from the executable using codesign under macOS 10.13, the codesign utility
    # 011014.python.osx.line214.comment may produce an invalid file, with the declared length of the __LINKEDIT segment (linkedit_seg.filesize) pointing
    # 011015.python.osx.line215.comment beyond the end of file, as reported in issue #6167.
    # 011016.python.osx.line216.comment
    # 011017.python.osx.line217.comment We can compensate for that by not using the declared sizes anywhere, and simply recompute them. In the final
    # 011018.python.osx.line218.comment binary, the __LINKEDIT segment and the SYMTAB section MUST end at the end of the file (otherwise, we have bigger
    # 011019.python.osx.line219.comment issues...). So simply recompute the declared sizes as difference between the final file length and the
    # 011020.python.osx.line220.comment corresponding start offset (NOTE: the offset is relative to start of the slice, which is stored in header.offset.
    # 011021.python.osx.line221.comment In thin binaries, header.offset is zero and start offset is relative to the start of file, but with fat binaries,
    # 011022.python.osx.line222.comment header.offset is non-zero)
    symtab_sec.strsize = file_size - (header.offset + symtab_sec.stroff)
    linkedit_seg.filesize = file_size - (header.offset + linkedit_seg.fileoff)

    # 011023.python.osx.line226.comment Compute new vmsize by rounding filesize up to full page size.
    page_size = (0x4000 if _get_arch_string(header.header).startswith('arm64') else 0x1000)
    linkedit_seg.vmsize = math.ceil(linkedit_seg.filesize / page_size) * page_size

    # 011024.python.osx.line230.comment NOTE: according to spec, segments need to be aligned to page boundaries: 0x4000 (16 kB) for arm64, 0x1000 (4 kB)
    # 011025.python.osx.line231.comment for other arches. But it seems we can get away without rounding and padding the segment file size - perhaps
    # 011026.python.osx.line232.comment because it is the last one?

    # 011027.python.osx.line234.comment Write changes
    with open(filename, 'rb+') as fp:
        executable.write(fp)

    # 011028.python.osx.line238.comment In fat binaries, we also need to adjust the fat header. macholib as of version 1.14 does not support this, so we
    # 011029.python.osx.line239.comment need to do it ourselves...
    if executable.fat:
        from macholib.mach_o import (FAT_MAGIC, FAT_MAGIC_64, fat_arch, fat_arch64, fat_header)
        with open(filename, 'rb+') as fp:
            # 011030.python.osx.line243.comment Taken from MachO.load_fat() implementation. The fat header's signature has already been validated when we
            # 011031.python.osx.line244.comment loaded the file for the first time.
            fat = fat_header.from_fileobj(fp)
            if fat.magic == FAT_MAGIC:
                archs = [fat_arch.from_fileobj(fp) for i in range(fat.nfat_arch)]
            elif fat.magic == FAT_MAGIC_64:
                archs = [fat_arch64.from_fileobj(fp) for i in range(fat.nfat_arch)]
            # 011032.python.osx.line250.comment Adjust the size in the fat header for the last slice.
            arch = archs[-1]
            arch.size = file_size - arch.offset
            # 011033.python.osx.line253.comment Now write the fat headers back to the file.
            fp.seek(0)
            fat.to_fileobj(fp)
            for arch in archs:
                arch.to_fileobj(fp)


def _get_arch_string(header):
    """
    Converts cputype and cpusubtype from mach_o.mach_header_64 into arch string comparible with lipo/codesign.
    The list of supported architectures can be found in man(1) arch.
    """
    # 011034.python.osx.line265.comment NOTE: the constants below are taken from macholib.mach_o
    cputype = header.cputype
    cpusubtype = header.cpusubtype & 0x0FFFFFFF
    if cputype == 0x01000000 | 7:
        if cpusubtype == 8:
            return 'x86_64h'  # 64-bit intel (haswell)
        else:
            return 'x86_64'  # 64-bit intel
    elif cputype == 0x01000000 | 12:
        if cpusubtype == 2:
            return 'arm64e'
        else:
            return 'arm64'
    elif cputype == 7:
        return 'i386'  # 32-bit intel
    assert False, 'Unhandled architecture!'


def update_exe_identifier(filename, pkg_filename):
    """
    Modifies the Mach-O image UUID stored in the LC_UUID command (if present) in order to ensure that different
    frozen applications have different identifiers. See TN3178 for details on why this is required:
    https://developer.apple.com/documentation/technotes/tn3178-checking-for-and-resolving-build-uuid-problems
    """

    # 011038.python.osx.line290.comment Compute hash of the PKG
    import hashlib
    pkg_hash = hashlib.sha1()
    with open(pkg_filename, 'rb') as fp:
        for chunk in iter(lambda: fp.read(8192), b""):
            pkg_hash.update(chunk)

    # 011039.python.osx.line297.comment Modify UUID in all arch slices of the executable.
    executable = MachO(filename)
    for header in executable.headers:
        # 011040.python.osx.line300.comment Find LC_UUID command
        uuid_cmd = [cmd for cmd in header.commands if cmd[0].cmd == LC_UUID]
        if not uuid_cmd:
            continue
        uuid_cmd = uuid_cmd[0]

        # 011041.python.osx.line306.comment Read the existing UUID (which is based on bootloader executable itself).
        original_uuid = uuid_cmd[1].uuid

        # 011042.python.osx.line309.comment Add original UUID to the hash; this is similar to what UUID v3/v5 do with namespace + name, except
        # 011043.python.osx.line310.comment that in our case, the prefix UUID (namespace) is added at the end, so that PKG hash needs to be
        # 011044.python.osx.line311.comment (pre)computed only once.
        combined_hash = pkg_hash.copy()
        combined_hash.update(original_uuid)

        new_uuid = combined_hash.digest()[:16]  # Same as uuid.uuid3() / uuid.uuid5().
        assert len(new_uuid) == 16

        uuid_cmd[1].uuid = new_uuid

    # 011046.python.osx.line320.comment Write changes
    with open(filename, 'rb+') as fp:
        executable.write(fp)


class InvalidBinaryError(Exception):
    """
    Exception raised by `get_binary_architectures` when it is passed an invalid binary.
    """
    pass


class IncompatibleBinaryArchError(Exception):
    """
    Exception raised by `binary_to_target_arch` when the passed binary fails the strict architecture check.
    """
    def __init__(self, message):
        url = "https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support"
        super().__init__(f"{message} For details about this error message, see: {url}")


def get_binary_architectures(filename):
    """
    Inspects the given binary and returns tuple (is_fat, archs), where is_fat is boolean indicating fat/thin binary,
    and arch is list of architectures with lipo/codesign compatible names.
    """
    try:
        executable = MachO(filename)
    except ValueError as e:
        raise InvalidBinaryError("Invalid Mach-O binary!") from e
    return bool(executable.fat), [_get_arch_string(hdr.header) for hdr in executable.headers]


def convert_binary_to_thin_arch(filename, thin_arch, output_filename=None):
    """
    Convert the given fat binary into thin one with the specified target architecture.
    """
    output_filename = output_filename or filename
    cmd_args = ['lipo', '-thin', thin_arch, filename, '-output', output_filename]
    p = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    if p.returncode:
        raise SystemError(f"lipo command ({cmd_args}) failed with error code {p.returncode}!\noutput: {p.stdout}")


def merge_into_fat_binary(output_filename, *slice_filenames):
    """
    Merge the given single-arch thin binary files into a fat binary.
    """
    cmd_args = ['lipo', '-create', '-output', output_filename, *slice_filenames]
    p = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    if p.returncode:
        raise SystemError(f"lipo command ({cmd_args}) failed with error code {p.returncode}!\noutput: {p.stdout}")


def binary_to_target_arch(filename, target_arch, display_name=None):
    """
    Check that the given binary contains required architecture slice(s) and convert the fat binary into thin one,
    if necessary.
    """
    if not display_name:
        display_name = filename  # Same as input file
    # 011048.python.osx.line381.comment Check the binary
    is_fat, archs = get_binary_architectures(filename)
    if target_arch == 'universal2':
        if not is_fat:
            raise IncompatibleBinaryArchError(f"{display_name} is not a fat binary!")
        # 011049.python.osx.line386.comment Assume fat binary is universal2; nothing to do
    else:
        if is_fat:
            if target_arch not in archs:
                raise IncompatibleBinaryArchError(f"{display_name} does not contain slice for {target_arch}!")
            # 011050.python.osx.line391.comment Convert to thin arch
            logger.debug("Converting fat binary %s (%s) to thin binary (%s)", filename, display_name, target_arch)
            convert_binary_to_thin_arch(filename, target_arch)
        else:
            if target_arch not in archs:
                raise IncompatibleBinaryArchError(
                    f"{display_name} is incompatible with target arch {target_arch} (has arch: {archs[0]})!"
                )
            # 011051.python.osx.line399.comment Binary has correct arch; nothing to do


def remove_signature_from_binary(filename):
    """
    Remove the signature from all architecture slices of the given binary file using the codesign utility.
    """
    logger.debug("Removing signature from file %r", filename)
    cmd_args = ['/usr/bin/codesign', '--remove', '--all-architectures', filename]
    p = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    if p.returncode:
        raise SystemError(f"codesign command ({cmd_args}) failed with error code {p.returncode}!\noutput: {p.stdout}")


def sign_binary(filename, identity=None, entitlements_file=None, deep=False):
    """
    Sign the binary using codesign utility. If no identity is provided, ad-hoc signing is performed.
    """
    extra_args = []
    if not identity:
        identity = '-'  # ad-hoc signing
    else:
        extra_args.append('--options=runtime')  # hardened runtime
    if entitlements_file:
        extra_args.append('--entitlements')
        extra_args.append(entitlements_file)
    if deep:
        extra_args.append('--deep')

    logger.debug("Signing file %r", filename)
    cmd_args = [
        '/usr/bin/codesign', '-s', identity, '--force', '--all-architectures', '--timestamp', *extra_args, filename
    ]
    p = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    if p.returncode:
        raise SystemError(f"codesign command ({cmd_args}) failed with error code {p.returncode}!\noutput: {p.stdout}")


def set_dylib_dependency_paths(filename, target_rpath):
    """
    Modify the given dylib's identity (in LC_ID_DYLIB command) and the paths to dependent dylibs (in LC_LOAD_DYLIB)
    commands into `@rpath/<basename>` format, remove any existing rpaths (LC_RPATH commands), and add a new rpath
    (LC_RPATH command) with the specified path.

    Uses `install-tool-name` utility to make the changes.

    The system libraries (e.g., the ones found in /usr/lib) are exempted from path rewrite.

    For multi-arch fat binaries, this function extracts each slice into temporary file, processes it separately,
    and then merges all processed slices back into fat binary. This is necessary because `install-tool-name` cannot
    modify rpaths in cases when an existing rpath is present only in one slice.
    """

    # 011054.python.osx.line452.comment Check if we are dealing with a fat binary; the `install-name-tool` seems to be unable to remove an rpath that is
    # 011055.python.osx.line453.comment present only in one slice, so we need to extract each slice, process it separately, and then stich processed
    # 011056.python.osx.line454.comment slices back into a fat binary.
    is_fat, archs = get_binary_architectures(filename)

    if is_fat:
        with tempfile.TemporaryDirectory() as tmpdir:
            slice_filenames = []
            for arch in archs:
                slice_filename = os.path.join(tmpdir, arch)
                convert_binary_to_thin_arch(filename, arch, output_filename=slice_filename)
                _set_dylib_dependency_paths(slice_filename, target_rpath)
                slice_filenames.append(slice_filename)
            merge_into_fat_binary(filename, *slice_filenames)
    else:
        # 011057.python.osx.line467.comment Thin binary - we can process it directly
        _set_dylib_dependency_paths(filename, target_rpath)


def _set_dylib_dependency_paths(filename, target_rpath):
    """
    The actual implementation of set_dylib_dependency_paths functionality.

    Implicitly assumes that a single-arch thin binary is given.
    """

    # 011058.python.osx.line478.comment Relocatable commands that we should overwrite - same list as used by `macholib`.
    _RELOCATABLE = {
        LC_LOAD_DYLIB,
        LC_LOAD_UPWARD_DYLIB,
        LC_LOAD_WEAK_DYLIB,
        LC_PREBOUND_DYLIB,
        LC_REEXPORT_DYLIB,
    }

    # 011059.python.osx.line487.comment Parse dylib's header to extract the following commands:
    # 011060.python.osx.line488.comment - LC_LOAD_DYLIB (or any member of _RELOCATABLE list): dylib load commands (dependent libraries)
    # 011061.python.osx.line489.comment - LC_RPATH: rpath definitions
    # 011062.python.osx.line490.comment - LC_ID_DYLIB: dylib's identity
    binary = MachO(filename)

    dylib_id = None
    rpaths = set()
    linked_libs = set()

    for header in binary.headers:
        for cmd in header.commands:
            lc_type = cmd[0].cmd
            if lc_type not in _RELOCATABLE and lc_type not in {LC_RPATH, LC_ID_DYLIB}:
                continue

            # 011063.python.osx.line503.comment Decode path, strip trailing NULL characters
            path = cmd[2].decode('utf-8').rstrip('\x00')

            if lc_type in _RELOCATABLE:
                linked_libs.add(path)
            elif lc_type == LC_RPATH:
                rpaths.add(path)
            elif lc_type == LC_ID_DYLIB:
                dylib_id = path

    del binary

    # 011064.python.osx.line515.comment If dylib has identifier set, compute the normalized version, in form of `@rpath/basename`.
    normalized_dylib_id = None
    if dylib_id:
        normalized_dylib_id = str(pathlib.PurePath('@rpath') / pathlib.PurePath(dylib_id).name)

    # 011065.python.osx.line520.comment Find dependent libraries that should have their prefix path changed to `@rpath`. If any dependent libraries
    # 011066.python.osx.line521.comment end up using `@rpath` (originally or due to rewrite), set the `rpath_required` boolean to True, so we know
    # 011067.python.osx.line522.comment that we need to add our rpath.
    changed_lib_paths = []
    rpath_required = False
    for linked_lib in linked_libs:
        # 011068.python.osx.line526.comment Leave system dynamic libraries unchanged.
        if macholib.util.in_system_path(linked_lib):
            continue

        # 011069.python.osx.line530.comment The older python.org builds that use system Tcl/Tk framework have their _tkinter.cpython-*-darwin.so
        # 011070.python.osx.line531.comment library linked against /Library/Frameworks/Tcl.framework/Versions/8.5/Tcl and
        # 011071.python.osx.line532.comment /Library/Frameworks/Tk.framework/Versions/8.5/Tk, although the actual frameworks are located in
        # 011072.python.osx.line533.comment /System/Library/Frameworks. Therefore, they slip through the above in_system_path() check, and we need to
        # 011073.python.osx.line534.comment exempt them manually.
        _exemptions = [
            '/Library/Frameworks/Tcl.framework/',
            '/Library/Frameworks/Tk.framework/',
        ]
        if any([x in linked_lib for x in _exemptions]):
            continue

        # 011074.python.osx.line542.comment This linked library will end up using `@rpath`, whether modified or not...
        rpath_required = True

        new_path = str(pathlib.PurePath('@rpath') / pathlib.PurePath(linked_lib).name)
        if linked_lib == new_path:
            continue

        changed_lib_paths.append((linked_lib, new_path))

    # 011075.python.osx.line551.comment Gather arguments for `install-name-tool`
    install_name_tool_args = []

    # 011076.python.osx.line554.comment Modify the dylib identifier if necessary
    if normalized_dylib_id and normalized_dylib_id != dylib_id:
        install_name_tool_args += ["-id", normalized_dylib_id]

    # 011077.python.osx.line558.comment Changed libs
    for original_path, new_path in changed_lib_paths:
        install_name_tool_args += ["-change", original_path, new_path]

    # 011078.python.osx.line562.comment Remove all existing rpaths except for the target rpath (if it already exists). `install_name_tool` disallows using
    # 011079.python.osx.line563.comment `-delete_rpath` and `-add_rpath` with the same argument.
    for rpath in rpaths:
        if rpath == target_rpath:
            continue
        install_name_tool_args += [
            "-delete_rpath",
            rpath,
        ]

    # 011080.python.osx.line572.comment If any of linked libraries use @rpath now and our target rpath is not already added, add it.
    # 011081.python.osx.line573.comment NOTE: @rpath in the dylib identifier does not actually require the rpath to be set on the binary...
    if rpath_required and target_rpath not in rpaths:
        install_name_tool_args += [
            "-add_rpath",
            target_rpath,
        ]

    # 011082.python.osx.line580.comment If we have no arguments, finish immediately.
    if not install_name_tool_args:
        return

    # 011083.python.osx.line584.comment Run `install_name_tool`
    cmd_args = ["install_name_tool", *install_name_tool_args, filename]
    p = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    if p.returncode:
        raise SystemError(
            f"install_name_tool command ({cmd_args}) failed with error code {p.returncode}!\noutput: {p.stdout}"
        )


def is_framework_bundle_lib(lib_path):
    """
    Check if the given shared library is part of a .framework bundle.
    """

    lib_path = pathlib.PurePath(lib_path)

    # 011084.python.osx.line600.comment For now, focus only on versioned layout, such as `QtCore.framework/Versions/5/QtCore`
    if lib_path.parent.parent.name != "Versions":
        return False
    if lib_path.parent.parent.parent.name != lib_path.name + ".framework":
        return False

    return True


def collect_files_from_framework_bundles(collected_files):
    """
    Scan the given TOC list of collected files for shared libraries that are collected from macOS .framework bundles,
    and collect the bundles' Info.plist files. Additionally, the following symbolic links:
      - `Versions/Current` pointing to the `Versions/<version>` directory containing the binary
      - `<name>` in the top-level .framework directory, pointing to `Versions/Current/<name>`
      - `Resources` in the top-level .framework directory, pointing to `Versions/Current/Resources`
      - additional directories in top-level .framework directory, pointing to their counterparts in `Versions/Current`
        directory.

    Returns TOC list for the discovered Info.plist files and generated symbolic links. The list does not contain
    duplicated entries.
    """
    invalid_framework_found = False

    framework_files = set()  # Additional entries for collected files. Use set for de-duplication.
    framework_paths = set()  # Registered framework paths for 2nd pass.

    # 011087.python.osx.line627.comment 1st pass: discover binaries from .framework bundles, and for each such binary:
    # 011088.python.osx.line628.comment - collect `Info.plist`
    # 011089.python.osx.line629.comment - create `Current` -> `<version>` symlink in `<name>.framework/Versions` directory.
    # 011090.python.osx.line630.comment - create `<name>.framework/<name>` -> `<name>.framework/Versions/Current/<name>` symlink.
    # 011091.python.osx.line631.comment - create `<name>.framework/Resources` -> `<name>.framework/Versions/Current/Resources` symlink.
    for dest_name, src_name, typecode in collected_files:
        if typecode != 'BINARY':
            continue

        src_path = pathlib.Path(src_name)  # /src/path/to/<name>.framework/Versions/<version>/<name>
        dest_path = pathlib.PurePath(dest_name)  # /dest/path/to/<name>.framework/Versions/<version>/<name>

        # 011094.python.osx.line639.comment Check whether binary originates from a .framework bundle
        if not is_framework_bundle_lib(src_path):
            continue

        # 011095.python.osx.line643.comment Check whether binary is also collected into a .framework bundle (i.e., the original layout is preserved)
        if not is_framework_bundle_lib(dest_path):
            continue

        # 011096.python.osx.line647.comment Assuming versioned layout, Info.plist should exist in Resources directory located next to the binary.
        info_plist_src = src_path.parent / "Resources" / "Info.plist"
        if not info_plist_src.is_file():
            # 011097.python.osx.line650.comment Alas, the .framework bundles shipped with PySide/PyQt might have Info.plist available only in the
            # 011098.python.osx.line651.comment top-level Resources directory. So accommodate this scenario as well, but collect the file into
            # 011099.python.osx.line652.comment versioned directory to appease the code-signing gods...
            info_plist_src_top = src_path.parent.parent.parent / "Resources" / "Info.plist"
            if not info_plist_src_top.is_file():
                # 011100.python.osx.line655.comment Strictly speaking, a .framework bundle without Info.plist is invalid. However, that did not prevent
                # 011101.python.osx.line656.comment PyQt from shipping such Qt .framework bundles up until v5.14.1. So by default, we just complain via
                # 011102.python.osx.line657.comment a warning message; if such binaries work in unfrozen python, they should also work in frozen
                # 011103.python.osx.line658.comment application. The codesign will refuse to sign the .app bundle (if we are generating one), but there
                # 011104.python.osx.line659.comment is nothing we can do about that.
                invalid_framework_found = True
                framework_dir = src_path.parent.parent.parent
                if compat.strict_collect_mode:
                    raise SystemError(f"Could not find Info.plist in {framework_dir}!")
                else:
                    logger.warning("Could not find Info.plist in %s!", framework_dir)
                    continue
            info_plist_src = info_plist_src_top
        info_plist_dest = dest_path.parent / "Resources" / "Info.plist"
        framework_files.add((str(info_plist_dest), str(info_plist_src), "DATA"))

        # 011105.python.osx.line671.comment Reconstruct the symlink Versions/Current -> Versions/<version>.
        # 011106.python.osx.line672.comment This one seems to be necessary for code signing, but might be absent from .framework bundles shipped with
        # 011107.python.osx.line673.comment python packages. So we always create it ourselves.
        framework_files.add((str(dest_path.parent.parent / "Current"), str(dest_path.parent.name), "SYMLINK"))

        dest_framework_path = dest_path.parent.parent.parent  # Top-level .framework directory path.

        # 011109.python.osx.line678.comment Symlink the binary in the `Current` directory to the top-level .framework directory.
        framework_files.add((
            str(dest_framework_path / dest_path.name),
            str(pathlib.PurePath("Versions/Current") / dest_path.name),
            "SYMLINK",
        ))

        # 011110.python.osx.line685.comment Ditto for the `Resources` directory.
        framework_files.add((
            str(dest_framework_path / "Resources"),
            "Versions/Current/Resources",
            "SYMLINK",
        ))

        # 011111.python.osx.line692.comment Register the framework parent path to use in additional directories scan in subsequent pass.
        framework_paths.add(dest_framework_path)

    # 011112.python.osx.line695.comment 2nd pass: scan for additional collected directories from .framework bundles, and create symlinks to the top-level
    # 011113.python.osx.line696.comment application directory. Make the outer loop go over the registered framework paths, so it becomes no-op if no
    # 011114.python.osx.line697.comment framework paths are registered.
    VALID_SUBDIRS = {'Helpers', 'Resources'}

    for dest_framework_path in framework_paths:
        for dest_name, src_name, typecode in collected_files:
            dest_path = pathlib.PurePath(dest_name)

            # 011115.python.osx.line704.comment Try matching against framework path
            try:
                remaining_path = dest_path.relative_to(dest_framework_path)
            except ValueError:  # dest_path is not subpath of dest_framework_path
                continue

            remaining_path_parts = remaining_path.parts

            # 011117.python.osx.line712.comment We are interested only in entries under Versions directory.
            if remaining_path_parts[0] != 'Versions':
                continue

            # 011118.python.osx.line716.comment If the entry name is among valid sub-directory names, create symlink.
            dir_name = remaining_path_parts[2]
            if dir_name not in VALID_SUBDIRS:
                continue

            framework_files.add((
                str(dest_framework_path / dir_name),
                str(pathlib.PurePath("Versions/Current") / dir_name),
                "SYMLINK",
            ))

    # 011119.python.osx.line727.comment If we encountered an invalid .framework bundle without Info.plist, warn the user that code-signing will most
    # 011120.python.osx.line728.comment likely fail.
    if invalid_framework_found:
        logger.warning(
            "One or more collected .framework bundles have missing Info.plist file. If you are building an .app "
            "bundle, you will most likely not be able to code-sign it."
        )

    return sorted(framework_files)
