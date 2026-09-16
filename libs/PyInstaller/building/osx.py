# 001097.python.osx.line1.comment -----------------------------------------------------------------------------
# 001098.python.osx.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 001099.python.osx.line3.comment
# 001100.python.osx.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 001101.python.osx.line5.comment or later) with exception for distributing the bootloader.
# 001102.python.osx.line6.comment
# 001103.python.osx.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 001104.python.osx.line8.comment
# 001105.python.osx.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 001106.python.osx.line10.comment -----------------------------------------------------------------------------

import os
import pathlib
import plistlib
import shutil
import subprocess

from PyInstaller import log as logging
from PyInstaller.building.api import COLLECT, EXE
from PyInstaller.building.datastruct import Target, logger, normalize_toc
from PyInstaller.building.utils import _check_path_overlap, _rmtree, process_collected_binary
from PyInstaller.compat import is_darwin, strict_collect_mode
from PyInstaller.building.icon import normalize_icon_type
import PyInstaller.utils.misc as miscutils

if is_darwin:
    import PyInstaller.utils.osx as osxutils

# 001107.python.osx.line29.comment Character sequence used to replace dot (`.`) in names of directories that are created in `Contents/MacOS` or
# 001108.python.osx.line30.comment `Contents/Frameworks`, where only .framework bundle directories are allowed to have dot in name.
DOT_REPLACEMENT = '__dot__'

WINDOWED_ONEFILE_DEPRCATION = (
    "Onefile mode in combination with macOS .app bundles (windowed mode) don't make sense (a .app bundle can not be a "
    "single file) and clashes with macOS's security. Please migrate to onedir mode. This will become an error "
    "in v7.0."
)


class BUNDLE(Target):
    def __init__(self, *args, **kwargs):
        from PyInstaller.config import CONF

        for item in args:
            if isinstance(item, EXE) and not item.exclude_binaries:
                logger.log(logging.DEPRECATION, WINDOWED_ONEFILE_DEPRCATION)

        # 001109.python.osx.line48.comment BUNDLE only has a sense under macOS, it is a noop on other platforms.
        if not is_darwin:
            return

        # 001110.python.osx.line52.comment Get a path to a .icns icon for the app bundle.
        self.icon = kwargs.get('icon')
        if not self.icon:
            # 001111.python.osx.line55.comment --icon not specified; use the default in the pyinstaller folder
            self.icon = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'bootloader', 'images', 'icon-windowed.icns'
            )
        else:
            # 001112.python.osx.line60.comment User gave an --icon=path. If it is relative, make it relative to the spec file location.
            if not os.path.isabs(self.icon):
                self.icon = os.path.join(CONF['specpath'], self.icon)

        super().__init__()

        # 001113.python.osx.line66.comment .app bundle is created in DISTPATH.
        self.name = kwargs.get('name', None)
        base_name = os.path.basename(self.name)
        self.name = os.path.join(CONF['distpath'], base_name)

        self.appname = os.path.splitext(base_name)[0]
        # 001114.python.osx.line72.comment Ensure version is a string, even if user accidentally passed an int or a float.
        # 001115.python.osx.line73.comment Having a `CFBundleShortVersionString` entry of non-string type in `Info.plist` causes the .app bundle to
        # 001116.python.osx.line74.comment crash at start (#4466).
        self.version = str(kwargs.get("version", "0.0.0"))
        self.toc = []
        self.strip = False
        self.upx = False
        self.console = True
        self.target_arch = None
        self.codesign_identity = None
        self.entitlements_file = None

        # 001117.python.osx.line84.comment .app bundle identifier for Code Signing
        self.bundle_identifier = kwargs.get('bundle_identifier')
        if not self.bundle_identifier:
            # 001118.python.osx.line87.comment Fallback to appname.
            self.bundle_identifier = self.appname

        self.info_plist = kwargs.get('info_plist', None)

        for arg in args:
            # 001119.python.osx.line93.comment Valid arguments: EXE object, COLLECT object, and TOC-like iterables
            if isinstance(arg, EXE):
                # 001120.python.osx.line95.comment Add EXE as an entry to the TOC, and merge its dependencies TOC
                self.toc.append((os.path.basename(arg.name), arg.name, 'EXECUTABLE'))
                self.toc.extend(arg.dependencies)
                # 001121.python.osx.line98.comment Inherit settings
                self.strip = arg.strip
                self.upx = arg.upx
                self.upx_exclude = arg.upx_exclude
                self.console = arg.console
                self.target_arch = arg.target_arch
                self.codesign_identity = arg.codesign_identity
                self.entitlements_file = arg.entitlements_file
            elif isinstance(arg, COLLECT):
                # 001122.python.osx.line107.comment Merge the TOC
                self.toc.extend(arg.toc)
                # 001123.python.osx.line109.comment Inherit settings
                self.strip = arg.strip_binaries
                self.upx = arg.upx_binaries
                self.upx_exclude = arg.upx_exclude
                self.console = arg.console
                self.target_arch = arg.target_arch
                self.codesign_identity = arg.codesign_identity
                self.entitlements_file = arg.entitlements_file
            elif miscutils.is_iterable(arg):
                # 001124.python.osx.line118.comment TOC-like iterable
                self.toc.extend(arg)
            else:
                raise TypeError(f"Invalid argument type for BUNDLE: {type(arg)!r}")

        # 001125.python.osx.line123.comment Infer the executable name from the first EXECUTABLE entry in the TOC; it might have come from the COLLECT
        # 001126.python.osx.line124.comment (as opposed to the stand-alone EXE).
        for dest_name, src_name, typecode in self.toc:
            if typecode == "EXECUTABLE":
                self.exename = src_name
                break
        else:
            raise ValueError("No EXECUTABLE entry found in the TOC!")

        # 001127.python.osx.line132.comment Normalize TOC
        self.toc = normalize_toc(self.toc)

        self.__postinit__()

    _GUTS = (
        # 001128.python.osx.line138.comment BUNDLE always builds, just want the toc to be written out
        ('toc', None),
    )

    def _check_guts(self, data, last_build):
        # 001129.python.osx.line143.comment BUNDLE always needs to be executed, in order to clean the output directory.
        return True

    # 001130.python.osx.line146.comment Helper for determining whether the given file belongs to a .framework bundle or not. If it does, it returns
    # 001131.python.osx.line147.comment the path to the top-level .framework bundle directory; otherwise, returns None. In case of nested .framework
    # 001132.python.osx.line148.comment bundles, the path to the top-most .framework bundle directory is returned.
    @staticmethod
    def _is_framework_file(dest_path):
        # 001133.python.osx.line151.comment NOTE: reverse the parents list because we are looking for the top-most .framework bundle directory!
        for parent in reversed(dest_path.parents):
            if parent.name.endswith('.framework'):
                return parent
        return None

    # 001134.python.osx.line157.comment Helper that computes relative cross-link path between link's location and target, assuming they are both
    # 001135.python.osx.line158.comment rooted in the `Contents` directory of a macOS .app bundle.
    @staticmethod
    def _compute_relative_crosslink(crosslink_location, crosslink_target):
        # 001136.python.osx.line161.comment We could take symlink_location and symlink_target as they are (relative to parent of the `Contents`
        # 001137.python.osx.line162.comment directory), but that would introduce an unnecessary `../Contents` part. So instead, we take both paths
        # 001138.python.osx.line163.comment relative to the `Contents` directory.
        return os.path.join(
            *['..' for level in pathlib.PurePath(crosslink_location).relative_to('Contents').parent.parts],
            pathlib.PurePath(crosslink_target).relative_to('Contents'),
        )

    # 001139.python.osx.line169.comment This method takes the original (input) TOC and processes it into final TOC, based on which the `assemble` method
    # 001140.python.osx.line170.comment performs its file collection. The TOC processing here represents the core of our efforts to generate an .app
    # 001141.python.osx.line171.comment bundle that is compatible with Apple's code-signing requirements.
    # 001142.python.osx.line172.comment
    # 001143.python.osx.line173.comment For in-depth details on the code-signing, see Apple's `Technical Note TN2206: macOS Code Signing In Depth` at
    # 001144.python.osx.line174.comment https://developer.apple.com/library/archive/technotes/tn2206/_index.html
    # 001145.python.osx.line175.comment
    # 001146.python.osx.line176.comment The requirements, framed from PyInstaller's perspective, can be summarized as follows:
    # 001147.python.osx.line177.comment
    # 001148.python.osx.line178.comment 1. The `Contents/MacOS` directory is expected to contain only the program executable and (binary) code (= dylibs
    # 001149.python.osx.line179.comment and nested .framework bundles). Alternatively, the dylibs and .framework bundles can be also placed into
    # 001150.python.osx.line180.comment `Contents/Frameworks` directory (where same rules apply as for `Contents/MacOS`, so the remainder of this
    # 001151.python.osx.line181.comment text refers to the two inter-changeably, unless explicitly noted otherwise). The code in `Contents/MacOS`
    # 001152.python.osx.line182.comment is expected to be signed, and the `codesign` utility will recursively sign all found code when using `--deep`
    # 001153.python.osx.line183.comment option to sign the .app bundle.
    # 001154.python.osx.line184.comment
    # 001155.python.osx.line185.comment 2. All non-code files should be be placed in `Contents/Resources`, so they become sealed (data) resources;
    # 001156.python.osx.line186.comment i.e., their signature data is recorded in `Contents/_CodeSignature/CodeResources`. (As a side note,
    # 001157.python.osx.line187.comment it seems that signature information for data/resources in `Contents/Resources` is kept nder `file` key in
    # 001158.python.osx.line188.comment the `CodeResources` file, while the information for contents in `Contents/MacOS` is kept under `file2` key).
    # 001159.python.osx.line189.comment
    # 001160.python.osx.line190.comment 3. The directories in `Contents/MacOS` may not contain dots (`.`) in their names, except for the nested
    # 001161.python.osx.line191.comment .framework bundle directories. The directories in `Contents/Resources` have no such restrictions.
    # 001162.python.osx.line192.comment
    # 001163.python.osx.line193.comment 4. There may not be any content in the top level of a bundle. In other words, if a bundle has a `Contents`
    # 001164.python.osx.line194.comment or a `Versions` directory at its top level, there may be no other files or directories alongside them. The
    # 001165.python.osx.line195.comment sole exception is that alongside `Versions`, there may be symlinks to files and directories in
    # 001166.python.osx.line196.comment `Versions/Current`. This rule is important for nested .framework bundles that we collect from python packages.
    # 001167.python.osx.line197.comment
    # 001168.python.osx.line198.comment Next, let us consider the consequences of violating each of the above requirements:
    # 001169.python.osx.line199.comment
    # 001170.python.osx.line200.comment 1. Code signing machinery can directly store signature only in Mach-O binaries and nested .framework bundles; if
    # 001171.python.osx.line201.comment a data file is placed in `Contents/MacOS`, the signature is stored in the file's extended attributes. If the
    # 001172.python.osx.line202.comment extended attributes are lost, the program's signature will be broken. Many file transfer techniques (e.g., a
    # 001173.python.osx.line203.comment zip file) do not preserve extended attributes, nor are they preserved when uploading to the Mac App Store.
    # 001174.python.osx.line204.comment
    # 001175.python.osx.line205.comment 2. Putting code (a dylib or a .framework bundle) into `Contents/Resources` causes it to be treated as a resource;
    # 001176.python.osx.line206.comment the outer signature (i.e., of the whole .app bundle) does not know that this nested content is actually a code.
    # 001177.python.osx.line207.comment Consequently, signing the bundle with `codesign --deep` will NOT sign binaries placed in the
    # 001178.python.osx.line208.comment `Contents/Resources`, which may result in missing signatures when .app bundle is verified for notarization.
    # 001179.python.osx.line209.comment This might be worked around by signing each binary separately, and then signing the whole bundle (without the
    # 001180.python.osx.line210.comment `--deep` option), but requires the user to keep track of the offending binaries.
    # 001181.python.osx.line211.comment
    # 001182.python.osx.line212.comment 3. If a directory in `Contents/MacOS` contains a dot in the name, code-signing the bundle fails with
    # 001183.python.osx.line213.comment `bundle format unrecognized, invalid, or unsuitable` due to code signing machinery treating directory as a
    # 001184.python.osx.line214.comment nested .framework bundle directory.
    # 001185.python.osx.line215.comment
    # 001186.python.osx.line216.comment 4. If nested .framework bundle is malformed, the signing of the .app bundle might succeed, but subsequent
    # 001187.python.osx.line217.comment verification will fail, for example with `embedded framework contains modified or invalid version` (as observed
    # 001188.python.osx.line218.comment with .framework bundles shipped by contemporary PyQt/PySide PyPI wheels).
    # 001189.python.osx.line219.comment
    # 001190.python.osx.line220.comment The above requirements are unfortunately often at odds with the structure of python packages:
    # 001191.python.osx.line221.comment
    # 001192.python.osx.line222.comment * In general, python packages are mixed-content directories, where binaries and data files may be expected to
    # 001193.python.osx.line223.comment be found next to each other.
    # 001194.python.osx.line224.comment
    # 001195.python.osx.line225.comment For example, `opencv-python` provides a custom loader script that requires the package to be collected in the
    # 001196.python.osx.line226.comment source-only form by PyInstaller (i.e., the python modules and scripts collected as source .py files). At the
    # 001197.python.osx.line227.comment same time, it expects the .py loader script to be able to find the binary extension next to itself.
    # 001198.python.osx.line228.comment
    # 001199.python.osx.line229.comment Another example of mixed-mode directories are Qt QML components' sub-directories, which contain both the
    # 001200.python.osx.line230.comment component's plugin (a binary) and associated meta files (data files).
    # 001201.python.osx.line231.comment
    # 001202.python.osx.line232.comment * In python world, the directories often contain dots in their names.
    # 001203.python.osx.line233.comment
    # 001204.python.osx.line234.comment Dots are often used for private directories containing binaries that are shipped with a package. For example,
    # 001205.python.osx.line235.comment `numpy/.dylibs`, `scipy/.dylibs`, etc.
    # 001206.python.osx.line236.comment
    # 001207.python.osx.line237.comment Qt QML components may also contain a dot in their name; couple of examples from `PySide2` package:
    # 001208.python.osx.line238.comment `PySide2/Qt/qml/QtQuick.2`, `PySide2/Qt/qml/QtQuick/Controls.2`, `PySide2/Qt/qml/QtQuick/Particles.2`, etc.
    # 001209.python.osx.line239.comment
    # 001210.python.osx.line240.comment The packages' metadata directories also invariably contain dots in the name due to version (for example,
    # 001211.python.osx.line241.comment `numpy-1.24.3.dist-info`).
    # 001212.python.osx.line242.comment
    # 001213.python.osx.line243.comment In the light of all above, PyInstaller attempts to strictly place all files to their mandated location
    # 001214.python.osx.line244.comment (`Contents/MacOS` or `Contents/Frameworks` vs `Contents/Resources`). To preserve the illusion of mixed-content
    # 001215.python.osx.line245.comment directories, the content is cross-linked from one directory to the other. Specifically:
    # 001216.python.osx.line246.comment
    # 001217.python.osx.line247.comment * All entries with DATA typecode are assumed to be data files, and are always placed in corresponding directory
    # 001218.python.osx.line248.comment structure rooted in `Contents/Resources`.
    # 001219.python.osx.line249.comment
    # 001220.python.osx.line250.comment * All entries with BINARY or EXTENSION typecode are always placed in corresponding directory structure rooted in
    # 001221.python.osx.line251.comment `Contents/Frameworks`.
    # 001222.python.osx.line252.comment
    # 001223.python.osx.line253.comment * All entries with EXECUTABLE are placed in `Contents/MacOS` directory.
    # 001224.python.osx.line254.comment
    # 001225.python.osx.line255.comment * For the purposes of relocation, nested .framework bundles are treated as a single BINARY entity; i.e., the
    # 001226.python.osx.line256.comment whole .bundle directory is placed in corresponding directory structure rooted in `Contents/Frameworks` (even
    # 001227.python.osx.line257.comment though some of its contents, such as `Info.plist` file, are actually data files).
    # 001228.python.osx.line258.comment
    # 001229.python.osx.line259.comment * Top-level data files and binaries are always cross-linked to the other directory. For example, given a data file
    # 001230.python.osx.line260.comment `data_file.txt` that was collected into `Contents/Resources`, we create a symbolic link called
    # 001231.python.osx.line261.comment `Contents/MacOS/data_file.txt` that points to `../Resources/data_file.txt`.
    # 001232.python.osx.line262.comment
    # 001233.python.osx.line263.comment * The executable itself, while placed in `Contents/MacOS`, are cross-linked into both `Contents/Framworks` and
    # 001234.python.osx.line264.comment `Contents/Resources`.
    # 001235.python.osx.line265.comment
    # 001236.python.osx.line266.comment * The stand-alone PKG entries (used with onefile builds that side-load the PKG archive) are treated as data files
    # 001237.python.osx.line267.comment and collected into `Contents/Resources`, but cross-linked only into `Contents/MacOS` directory (because they
    # 001238.python.osx.line268.comment must appear to be next to the program executable). This is the only entry type that is cross-linked into the
    # 001239.python.osx.line269.comment `Contents/MacOS` directory and also the only data-like entry type that is not cross-linked into the
    # 001240.python.osx.line270.comment `Contents/Frameworks` directory.
    # 001241.python.osx.line271.comment
    # 001242.python.osx.line272.comment * For files in sub-directories, the cross-linking behavior depends on the type of directory:
    # 001243.python.osx.line273.comment
    # 001244.python.osx.line274.comment * A data-only directory is created in directory structure rooted in `Contents/Resources`, and cross-linked
    # 001245.python.osx.line275.comment into directory structure rooted in `Contents/Frameworks` at directory level (i.e., we link the whole
    # 001246.python.osx.line276.comment directory instead of individual files).
    # 001247.python.osx.line277.comment
    # 001248.python.osx.line278.comment This largely saves us from having to deal with dots in the names of collected metadata directories, which
    # 001249.python.osx.line279.comment are examples of data-only directories.
    # 001250.python.osx.line280.comment
    # 001251.python.osx.line281.comment * A binary-only directory is created in directory structure rooted in `Contents/Frameworks`, and cross-linked
    # 001252.python.osx.line282.comment into `Contents/Resources` at directory level.
    # 001253.python.osx.line283.comment
    # 001254.python.osx.line284.comment * A mixed-content directory is created in both directory structures. Files are placed into corresponding
    # 001255.python.osx.line285.comment directory structure based on their type, and cross-linked into other directory structure at file level.
    # 001256.python.osx.line286.comment
    # 001257.python.osx.line287.comment * This rule is applied recursively; for example, a data-only sub-directory in a mixed-content directory is
    # 001258.python.osx.line288.comment cross-linked at directory level, while adjacent binary and data files are cross-linked at file level.
    # 001259.python.osx.line289.comment
    # 001260.python.osx.line290.comment * To work around the issue with dots in the names of directories in `Contents/Frameworks` (applicable to
    # 001261.python.osx.line291.comment binary-only or mixed-content directories), such directories are created with modified name (the dot replaced
    # 001262.python.osx.line292.comment with a pre-defined pattern). Next to the modified directory, a symbolic link with original name is created,
    # 001263.python.osx.line293.comment pointing to the directory with modified name. With mixed-content directories, this modification is performed
    # 001264.python.osx.line294.comment only on the `Contents/Frameworks` side; the corresponding directory in `Contents/Resources` can be created
    # 001265.python.osx.line295.comment directly, without name modification and symbolic link.
    # 001266.python.osx.line296.comment
    # 001267.python.osx.line297.comment * If a symbolic link needs to be created in a mixed-content directory due to a SYMLINK entry from the original
    # 001268.python.osx.line298.comment TOC (i.e., a "collected" symlink originating from analysis, as opposed to the cross-linking mechanism described
    # 001269.python.osx.line299.comment above), the link is created in both directory structures, each pointing to the resource in its corresponding
    # 001270.python.osx.line300.comment directory structure (with one such resource being an actual file, and the other being a cross-link to the file).
    # 001271.python.osx.line301.comment
    # 001272.python.osx.line302.comment Final remarks:
    # 001273.python.osx.line303.comment
    # 001274.python.osx.line304.comment NOTE: the relocation mechanism is codified by tests in `tests/functional/test_macos_bundle_structure.py`.
    # 001275.python.osx.line305.comment
    # 001276.python.osx.line306.comment NOTE: by placing binaries and nested .framework entries into `Contents/Frameworks` instead of `Contents/MacOS`,
    # 001277.python.osx.line307.comment we have effectively relocated the `sys._MEIPASS` directory from the `Contents/MacOS` (= the parent directory of
    # 001278.python.osx.line308.comment the program executable) into `Contents/Frameworks`. This requires the PyInstaller's bootloader to detect that it
    # 001279.python.osx.line309.comment is running in the app-bundle mode (e.g., by checking if program executable's parent directory is `Contents/NacOS`)
    # 001280.python.osx.line310.comment and adjust the path accordingly.
    # 001281.python.osx.line311.comment
    # 001282.python.osx.line312.comment NOTE: the implemented relocation mechanism depends on the input TOC containing properly classified entries
    # 001283.python.osx.line313.comment w.r.t. BINARY vs DATA. So hooks and .spec files triggering collection of binaries as datas (and vice versa) will
    # 001284.python.osx.line314.comment result in incorrect placement of those files in the generated .app bundle. However, this is *not* the proper place
    # 001285.python.osx.line315.comment to address such issues; if necessary, automatic (re)classification should be added to analysis process, to ensure
    # 001286.python.osx.line316.comment that BUNDLE (as well as other build targets) receive correctly classified TOC.
    # 001287.python.osx.line317.comment
    # 001288.python.osx.line318.comment NOTE: similar to the previous note, the relocation mechanism is also not the proper place to enforce compliant
    # 001289.python.osx.line319.comment structure of the nested .framework bundles. Instead, this is handled by the analysis process, using the
    # 001290.python.osx.line320.comment `PyInstaller.utils.osx.collect_files_from_framework_bundles` helper function. So the input TOC that BUNDLE
    # 001291.python.osx.line321.comment receives should already contain entries that reconstruct compliant nested .framework bundles.
    def _process_bundle_toc(self, toc):
        bundle_toc = []

        # 001292.python.osx.line325.comment Step 1: inspect the directory layout and classify the directories according to their contents.
        directory_types = dict()

        _MIXED_DIR_TYPE = 'MIXED-DIR'
        _DATA_DIR_TYPE = 'DATA-DIR'
        _BINARY_DIR_TYPE = 'BINARY-DIR'
        _FRAMEWORK_DIR_TYPE = 'FRAMEWORK-DIR'

        _TOP_LEVEL_DIR = pathlib.PurePath('.')

        for dest_name, src_name, typecode in toc:
            dest_path = pathlib.PurePath(dest_name)

            framework_dir = self._is_framework_file(dest_path)
            if framework_dir:
                # 001293.python.osx.line340.comment Mark the framework directory as FRAMEWORK-DIR.
                directory_types[framework_dir] = _FRAMEWORK_DIR_TYPE
                # 001294.python.osx.line342.comment Treat the framework directory as BINARY file when classifying parent directories.
                typecode = 'BINARY'
                parent_dirs = framework_dir.parents
            else:
                parent_dirs = dest_path.parents
                # 001295.python.osx.line347.comment Treat BINARY and EXTENSION as BINARY to simplify further processing.
                if typecode == 'EXTENSION':
                    typecode = 'BINARY'

            # 001296.python.osx.line351.comment (Re)classify parent directories
            for parent_dir in parent_dirs:
                # 001297.python.osx.line353.comment Skip the top-level `.` dir. This is also the only directory that can contain EXECUTABLE and PKG
                # 001298.python.osx.line354.comment entries, so we do not have to worry about.
                if parent_dir == _TOP_LEVEL_DIR:
                    continue

                directory_type = _BINARY_DIR_TYPE if typecode == 'BINARY' else _DATA_DIR_TYPE  # default
                directory_type = directory_types.get(parent_dir, directory_type)

                if directory_type == _DATA_DIR_TYPE and typecode == 'BINARY':
                    directory_type = _MIXED_DIR_TYPE
                if directory_type == _BINARY_DIR_TYPE and typecode == 'DATA':
                    directory_type = _MIXED_DIR_TYPE

                directory_types[parent_dir] = directory_type

        logger.debug("Directory classification: %r", directory_types)

        # 001300.python.osx.line370.comment Step 2: process the obtained directory structure and create symlink entries for directories that need to be
        # 001301.python.osx.line371.comment cross-linked. Such directories are data-only and binary-only directories (and framework directories) that are
        # 001302.python.osx.line372.comment located either in the top-level directory (have no parent) or in a mixed-content directory.
        for directory_path, directory_type in directory_types.items():
            # 001303.python.osx.line374.comment Cross-linking at directory level applies only to data-only and binary-only directories (as well as
            # 001304.python.osx.line375.comment framework directories).
            if directory_type == _MIXED_DIR_TYPE:
                continue

            # 001305.python.osx.line379.comment The parent needs to be either top-level directory or a mixed-content directory. Otherwise, the parent
            # 001306.python.osx.line380.comment (or one of its ancestors) will get cross-linked, and we do not need the link here.
            parent_dir = directory_path.parent
            requires_crosslink = parent_dir == _TOP_LEVEL_DIR or directory_types.get(parent_dir) == _MIXED_DIR_TYPE
            if not requires_crosslink:
                continue

            logger.debug("Cross-linking directory %r of type %r", directory_path, directory_type)

            # 001307.python.osx.line388.comment Data-only directories are created in `Contents/Resources`, needs to be cross-linked into `Contents/MacOS`.
            # 001308.python.osx.line389.comment Vice versa for binary-only or framework directories. The directory creation is handled implicitly, when we
            # 001309.python.osx.line390.comment create parent directory structure for collected files.
            if directory_type == _DATA_DIR_TYPE:
                symlink_src = os.path.join('Contents/Resources', directory_path)
                symlink_dest = os.path.join('Contents/Frameworks', directory_path)
            else:
                symlink_src = os.path.join('Contents/Frameworks', directory_path)
                symlink_dest = os.path.join('Contents/Resources', directory_path)
            symlink_ref = self._compute_relative_crosslink(symlink_dest, symlink_src)

            bundle_toc.append((symlink_dest, symlink_ref, 'SYMLINK'))

        # 001310.python.osx.line401.comment Step 3: first part of the work-around for directories that are located in `Contents/Frameworks` but contain a
        # 001311.python.osx.line402.comment dot in their name. As per `codesign` rules, the only directories in `Contents/Frameworks` that are allowed to
        # 001312.python.osx.line403.comment contain a dot in their name are .framework bundle directories. So we replace the dot with a custom character
        # 001313.python.osx.line404.comment sequence (stored in global `DOT_REPLACEMENT` variable), and create a symbolic with original name pointing to
        # 001314.python.osx.line405.comment the modified name. This is the best we can do with code-sign requirements vs. python community showing their
        # 001315.python.osx.line406.comment packages' dylibs into `.dylib` subdirectories, or Qt storing their Qml components in directories named
        # 001316.python.osx.line407.comment `QtQuick.2`, `QtQuick/Controls.2`, `QtQuick/Particles.2`, `QtQuick/Templates.2`, etc.
        # 001317.python.osx.line408.comment
        # 001318.python.osx.line409.comment In this step, we only prepare symlink entries that link the original directory name (with dot) to the modified
        # 001319.python.osx.line410.comment one (with dot replaced). The parent paths for collected files are modified in later step(s).
        for directory_path, directory_type in directory_types.items():
            # 001320.python.osx.line412.comment .framework bundle directories contain a dot in the name, but are allowed that.
            if directory_type == _FRAMEWORK_DIR_TYPE:
                continue

            # 001321.python.osx.line416.comment Data-only directories are fully located in `Contents/Resources` and cross-linked to `Contents/Frameworks`
            # 001322.python.osx.line417.comment at directory level, so they are also allowed a dot in their name.
            if directory_type == _DATA_DIR_TYPE:
                continue

            # 001323.python.osx.line421.comment Apply the work-around, if necessary...
            if '.' not in directory_path.name:
                continue

            logger.debug(
                "Creating symlink to work around the dot in the name of directory %r (%s)...", str(directory_path),
                directory_type
            )

            # 001324.python.osx.line430.comment Create a SYMLINK entry, but only for this level. In case of nested directories with dots in names, the
            # 001325.python.osx.line431.comment symlinks for ancestors will be created by corresponding loop iteration.
            bundle_toc.append((
                os.path.join('Contents/Frameworks', directory_path),
                directory_path.name.replace('.', DOT_REPLACEMENT),
                'SYMLINK',
            ))

        # 001326.python.osx.line438.comment Step 4: process the entries for collected files, and decide whether they should be placed into
        # 001327.python.osx.line439.comment `Contents/MacOS`, `Contents/Frameworks`, or `Contents/Resources`, and whether they should be cross-linked into
        # 001328.python.osx.line440.comment other directories.
        for orig_dest_name, src_name, typecode in toc:
            orig_dest_path = pathlib.PurePath(orig_dest_name)

            # 001329.python.osx.line444.comment Special handling for EXECUTABLE and PKG entries
            if typecode == 'EXECUTABLE':
                # 001330.python.osx.line446.comment Place into `Contents/MacOS`, ...
                file_dest = os.path.join('Contents/MacOS', orig_dest_name)
                bundle_toc.append((file_dest, src_name, typecode))
                # 001331.python.osx.line449.comment ... and do nothing else. We explicitly avoid cross-linking the executable to `Contents/Frameworks` and
                # 001332.python.osx.line450.comment `Contents/Resources`, because it should be not necessary (the executable's location should be
                # 001333.python.osx.line451.comment discovered via `sys.executable`) and to prevent issues when executable name collides with name of a
                # 001334.python.osx.line452.comment package from which we collect either binaries or data files (or both); see #7314.
                continue
            elif typecode == 'PKG':
                # 001335.python.osx.line455.comment Place into `Contents/Resources` ...
                file_dest = os.path.join('Contents/Resources', orig_dest_name)
                bundle_toc.append((file_dest, src_name, typecode))
                # 001336.python.osx.line458.comment ... and cross-link only into `Contents/MacOS`.
                # 001337.python.osx.line459.comment This is used only in `onefile` mode, where there is actually no other content to distribute among the
                # 001338.python.osx.line460.comment `Contents/Resources` and `Contents/Frameworks` directories, so cross-linking into the latter makes
                # 001339.python.osx.line461.comment little sense.
                symlink_dest = os.path.join('Contents/MacOS', orig_dest_name)
                symlink_ref = self._compute_relative_crosslink(symlink_dest, file_dest)
                bundle_toc.append((symlink_dest, symlink_ref, 'SYMLINK'))
                continue

            # 001340.python.osx.line467.comment Standard data vs binary processing...

            # 001341.python.osx.line469.comment Determine file location based on its type.
            if self._is_framework_file(orig_dest_path):
                # 001342.python.osx.line471.comment File from a framework bundle; put into `Contents/Frameworks`, but never cross-link the file itself.
                # 001343.python.osx.line472.comment The whole .framework bundle directory will be linked as necessary by the directory cross-linking
                # 001344.python.osx.line473.comment mechanism.
                file_base_dir = 'Contents/Frameworks'
                crosslink_base_dir = None
            elif typecode == 'DATA':
                # 001345.python.osx.line477.comment Data file; relocate to `Contents/Resources` and cross-link it back into `Contents/Frameworks`.
                file_base_dir = 'Contents/Resources'
                crosslink_base_dir = 'Contents/Frameworks'
            else:
                # 001346.python.osx.line481.comment Binary; put into `Contents/Frameworks` and cross-link it into `Contents/Resources`.
                file_base_dir = 'Contents/Frameworks'
                crosslink_base_dir = 'Contents/Resources'

            # 001347.python.osx.line485.comment Determine if we need to cross-link the file. We need to do this for top-level files (the ones without
            # 001348.python.osx.line486.comment parent directories), and for files whose parent directories are mixed-content directories.
            requires_crosslink = False
            if crosslink_base_dir is not None:
                parent_dir = orig_dest_path.parent
                requires_crosslink = parent_dir == _TOP_LEVEL_DIR or directory_types.get(parent_dir) == _MIXED_DIR_TYPE

            # 001349.python.osx.line492.comment Special handling for SYMLINK entries in original TOC; if we need to cross-link a symlink entry, we create
            # 001350.python.osx.line493.comment it in both locations, and have each point to the (relative) resource in the same directory (so one of the
            # 001351.python.osx.line494.comment targets will likely be a file, and the other will be a symlink due to cross-linking).
            if typecode == 'SYMLINK' and requires_crosslink:
                bundle_toc.append((os.path.join(file_base_dir, orig_dest_name), src_name, typecode))
                bundle_toc.append((os.path.join(crosslink_base_dir, orig_dest_name), src_name, typecode))
                continue

            # 001352.python.osx.line500.comment The file itself.
            file_dest = os.path.join(file_base_dir, orig_dest_name)
            bundle_toc.append((file_dest, src_name, typecode))

            # 001353.python.osx.line504.comment Symlink for cross-linking
            if requires_crosslink:
                symlink_dest = os.path.join(crosslink_base_dir, orig_dest_name)
                symlink_ref = self._compute_relative_crosslink(symlink_dest, file_dest)
                bundle_toc.append((symlink_dest, symlink_ref, 'SYMLINK'))

        # 001354.python.osx.line510.comment Step 5: sanitize all destination paths in the new TOC, to ensure that paths that are rooted in
        # 001355.python.osx.line511.comment `Contents/Frameworks` do not contain directories with dots in their names. Doing this as a post-processing
        # 001356.python.osx.line512.comment step keeps code simple and clean and ensures that this step is applied to files, symlinks that originate from
        # 001357.python.osx.line513.comment cross-linking files, and symlinks that originate from cross-linking directories. This in turn ensures that
        # 001358.python.osx.line514.comment all directory hierarchies created during the actual file collection have sanitized names, and that collection
        # 001359.python.osx.line515.comment outcome does not depend on the order of entries in the TOC.
        sanitized_toc = []
        for dest_name, src_name, typecode in bundle_toc:
            dest_path = pathlib.PurePath(dest_name)

            # 001360.python.osx.line520.comment Paths rooted in Contents/Resources do not require sanitizing.
            if dest_path.parts[0] == 'Contents' and dest_path.parts[1] == 'Resources':
                sanitized_toc.append((dest_name, src_name, typecode))
                continue

            # 001361.python.osx.line525.comment Special handling for files from .framework bundle directories; sanitize only parent path of the .framework
            # 001362.python.osx.line526.comment directory.
            framework_path = self._is_framework_file(dest_path)
            if framework_path:
                parent_path = framework_path.parent
                remaining_path = dest_path.relative_to(parent_path)
            else:
                parent_path = dest_path.parent
                remaining_path = dest_path.name

            sanitized_dest_path = pathlib.PurePath(
                *parent_path.parts[:2],  # Contents/Frameworks
                *[part.replace('.', DOT_REPLACEMENT) for part in parent_path.parts[2:]],
                remaining_path,
            )
            sanitized_dest_name = str(sanitized_dest_path)

            if sanitized_dest_path != dest_path:
                logger.debug("Sanitizing dest path: %r -> %r", dest_name, sanitized_dest_name)

            sanitized_toc.append((sanitized_dest_name, src_name, typecode))

        bundle_toc = sanitized_toc

        # 001364.python.osx.line549.comment Normalize and sort the TOC for easier inspection
        bundle_toc = sorted(normalize_toc(bundle_toc))

        return bundle_toc

    def assemble(self):
        from PyInstaller.config import CONF

        if _check_path_overlap(self.name) and os.path.isdir(self.name):
            _rmtree(self.name)

        logger.info("Building BUNDLE %s", self.tocbasename)

        # 001365.python.osx.line562.comment Create a minimal Mac bundle structure.
        os.makedirs(os.path.join(self.name, "Contents", "MacOS"))
        os.makedirs(os.path.join(self.name, "Contents", "Resources"))
        os.makedirs(os.path.join(self.name, "Contents", "Frameworks"))

        # 001366.python.osx.line567.comment Makes sure the icon exists and attempts to convert to the proper format if applicable
        self.icon = normalize_icon_type(self.icon, ("icns",), "icns", CONF["workpath"])

        # 001367.python.osx.line570.comment Ensure icon path is absolute
        self.icon = os.path.abspath(self.icon)

        # 001368.python.osx.line573.comment Copy icns icon to Resources directory.
        shutil.copyfile(self.icon, os.path.join(self.name, 'Contents', 'Resources', os.path.basename(self.icon)))

        # 001369.python.osx.line576.comment Key/values for a minimal Info.plist file
        info_plist_dict = {
            "CFBundleDisplayName": self.appname,
            "CFBundleName": self.appname,

            # 001370.python.osx.line581.comment Required by 'codesign' utility.
            # 001371.python.osx.line582.comment The value for CFBundleIdentifier is used as the default unique name of your program for Code Signing
            # 001372.python.osx.line583.comment purposes. It even identifies the APP for access to restricted macOS areas like Keychain.
            # 001373.python.osx.line584.comment
            # 001374.python.osx.line585.comment The identifier used for signing must be globally unique. The usual form for this identifier is a
            # 001375.python.osx.line586.comment hierarchical name in reverse DNS notation, starting with the toplevel domain, followed by the company
            # 001376.python.osx.line587.comment name, followed by the department within the company, and ending with the product name. Usually in the
            # 001377.python.osx.line588.comment form: com.mycompany.department.appname
            # 001378.python.osx.line589.comment CLI option --osx-bundle-identifier sets this value.
            "CFBundleIdentifier": self.bundle_identifier,
            "CFBundleExecutable": os.path.basename(self.exename),
            "CFBundleIconFile": os.path.basename(self.icon),
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": self.version,
        }

        # 001379.python.osx.line598.comment Set some default values. But they still can be overwritten by the user.
        if self.console:
            # 001380.python.osx.line600.comment Setting EXE console=True implies LSBackgroundOnly=True.
            info_plist_dict['LSBackgroundOnly'] = True
        else:
            # 001381.python.osx.line603.comment Let's use high resolution by default.
            info_plist_dict['NSHighResolutionCapable'] = True

        # 001382.python.osx.line606.comment Merge info_plist settings from spec file
        if isinstance(self.info_plist, dict) and self.info_plist:
            info_plist_dict.update(self.info_plist)

        plist_filename = os.path.join(self.name, "Contents", "Info.plist")
        with open(plist_filename, "wb") as plist_fh:
            plistlib.dump(info_plist_dict, plist_fh)

        # 001383.python.osx.line614.comment Pre-process the TOC into its final BUNDLE-compatible form.
        bundle_toc = self._process_bundle_toc(self.toc)

        # 001384.python.osx.line617.comment Perform the actual collection.
        CONTENTS_FRAMEWORKS_PATH = pathlib.PurePath('Contents/Frameworks')
        for dest_name, src_name, typecode in bundle_toc:
            # 001385.python.osx.line620.comment Create parent directory structure, if necessary
            dest_path = os.path.join(self.name, dest_name)  # Absolute destination path
            dest_dir = os.path.dirname(dest_path)
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except FileExistsError:
                raise SystemExit(
                    f"ERROR: Pyinstaller needs to create a directory at {dest_dir!r}, "
                    "but there already exists a file at that path!"
                )
            # 001387.python.osx.line630.comment Copy extensions and binaries from cache. This ensures that these files undergo additional binary
            # 001388.python.osx.line631.comment processing - have paths to linked libraries rewritten (relative to `@rpath`) and have rpath set to the
            # 001389.python.osx.line632.comment top-level directory (relative to `@loader_path`, i.e., the file's location). The "top-level" directory
            # 001390.python.osx.line633.comment in this case corresponds to `Contents/MacOS` (where `sys._MEIPASS` also points), so we need to pass
            # 001391.python.osx.line634.comment the cache retrieval function the *original* destination path (which is without preceding
            # 001392.python.osx.line635.comment `Contents/MacOS`).
            if typecode in ('EXTENSION', 'BINARY'):
                orig_dest_name = str(pathlib.PurePath(dest_name).relative_to(CONTENTS_FRAMEWORKS_PATH))
                src_name = process_collected_binary(
                    src_name,
                    orig_dest_name,
                    use_strip=self.strip,
                    use_upx=self.upx,
                    upx_exclude=self.upx_exclude,
                    target_arch=self.target_arch,
                    codesign_identity=self.codesign_identity,
                    entitlements_file=self.entitlements_file,
                    strict_arch_validation=(typecode == 'EXTENSION'),
                )
            if typecode == 'SYMLINK':
                os.symlink(src_name, dest_path)  # Create link at dest_path, pointing at (relative) src_name
            else:
                # 001394.python.osx.line652.comment BUNDLE does not support MERGE-based multipackage
                assert typecode != 'DEPENDENCY', "MERGE DEPENDENCY entries are not supported in BUNDLE!"

                # 001395.python.osx.line655.comment At this point, `src_name` should be a valid file.
                if not os.path.isfile(src_name):
                    raise ValueError(f"Resource {src_name!r} is not a valid file!")
                # 001396.python.osx.line658.comment If strict collection mode is enabled, the destination should not exist yet.
                if strict_collect_mode and os.path.exists(dest_path):
                    raise ValueError(
                        f"Attempting to collect a duplicated file into BUNDLE: {dest_name} (type: {typecode})"
                    )
                # 001397.python.osx.line663.comment Use `shutil.copyfile` to copy file with default permissions. We do not attempt to preserve original
                # 001398.python.osx.line664.comment permissions nor metadata, as they might be too restrictive and cause issues either during subsequent
                # 001399.python.osx.line665.comment re-build attempts or when trying to move the application bundle. For binaries (and data files with
                # 001400.python.osx.line666.comment executable bit set), we manually set the executable bits after copying the file.
                shutil.copyfile(src_name, dest_path)
            if (
                typecode in ('EXTENSION', 'BINARY', 'EXECUTABLE')
                or (typecode == 'DATA' and os.access(src_name, os.X_OK))
            ):
                os.chmod(dest_path, 0o755)

        # 001401.python.osx.line674.comment Sign the bundle
        logger.info('Signing the BUNDLE...')
        try:
            osxutils.sign_binary(self.name, self.codesign_identity, self.entitlements_file, deep=True)
        except Exception as e:
            # 001402.python.osx.line679.comment Display a warning or re-raise the error, depending on the environment-variable setting.
            if os.environ.get("PYINSTALLER_STRICT_BUNDLE_CODESIGN_ERROR", "0") == "0":
                logger.warning("Error while signing the bundle: %s", e)
                logger.warning("You will need to sign the bundle manually!")
            else:
                raise RuntimeError("Failed to codesign the bundle!") from e

        logger.info("Building BUNDLE %s completed successfully.", self.tocbasename)

        # 001403.python.osx.line688.comment Optionally verify bundle's signature. This is primarily intended for our CI.
        if os.environ.get("PYINSTALLER_VERIFY_BUNDLE_SIGNATURE", "0") != "0":
            logger.info("Verifying signature for BUNDLE %s...", self.name)
            self.verify_bundle_signature(self.name)
            logger.info("BUNDLE verification complete!")

    @staticmethod
    def verify_bundle_signature(bundle_dir):
        # 001404.python.osx.line696.comment First, verify the bundle signature using codesign.
        cmd_args = ['/usr/bin/codesign', '--verify', '--all-architectures', '--deep', '--strict', bundle_dir]
        p = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
        if p.returncode:
            raise SystemError(
                f"codesign command ({cmd_args}) failed with error code {p.returncode}!\noutput: {p.stdout}"
            )

        # 001405.python.osx.line704.comment Ensure that code-signing information is *NOT* embedded in the files' extended attributes.
        # 001406.python.osx.line705.comment
        # 001407.python.osx.line706.comment This happens when files other than binaries are present in `Contents/MacOS` or `Contents/Frameworks`
        # 001408.python.osx.line707.comment directory; as the signature cannot be embedded within the file itself (contrary to binaries with
        # 001409.python.osx.line708.comment `LC_CODE_SIGNATURE` section in their header), it ends up stores in the file's extended attributes. However,
        # 001410.python.osx.line709.comment if such bundle is transferred using a method that does not support extended attributes (for example, a zip
        # 001411.python.osx.line710.comment file), the signatures on these files are lost, and the signature of the bundle as a whole becomes invalid.
        # 001412.python.osx.line711.comment This is the primary reason why we need to relocate non-binaries into `Contents/Resources` - the signatures
        # 001413.python.osx.line712.comment for files in that directory end up stored in `Contents/_CodeSignature/CodeResources` file.
        # 001414.python.osx.line713.comment
        # 001415.python.osx.line714.comment This check therefore aims to ensure that all files have been properly relocated to their corresponding
        # 001416.python.osx.line715.comment locations w.r.t. the code-signing requirements.

        try:
            import xattr
        except ModuleNotFoundError:
            logger.info("xattr package not available; skipping verification of extended attributes!")
            return

        CODESIGN_ATTRS = (
            "com.apple.cs.CodeDirectory",
            "com.apple.cs.CodeRequirements",
            "com.apple.cs.CodeRequirements-1",
            "com.apple.cs.CodeSignature",
        )

        for entry in pathlib.Path(bundle_dir).rglob("*"):
            if not entry.is_file():
                continue

            file_attrs = xattr.listxattr(entry)
            if any([codesign_attr in file_attrs for codesign_attr in CODESIGN_ATTRS]):
                raise ValueError(f"Code-sign attributes found in extended attributes of {str(entry)!r}!")
