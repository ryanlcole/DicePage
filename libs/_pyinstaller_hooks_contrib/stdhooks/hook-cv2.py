# 012707.python.hook-cv2.line1.comment ------------------------------------------------------------------
# 012708.python.hook-cv2.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012709.python.hook-cv2.line3.comment
# 012710.python.hook-cv2.line4.comment This file is distributed under the terms of the GNU General Public
# 012711.python.hook-cv2.line5.comment License (version 2.0 or later).
# 012712.python.hook-cv2.line6.comment
# 012713.python.hook-cv2.line7.comment The full license is available in LICENSE, distributed with
# 012714.python.hook-cv2.line8.comment this software.
# 012715.python.hook-cv2.line9.comment
# 012716.python.hook-cv2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012717.python.hook-cv2.line11.comment ------------------------------------------------------------------

import sys
import os
import glob
import pathlib

import PyInstaller.utils.hooks as hookutils
from PyInstaller import compat

hiddenimports = ['numpy']

# 012718.python.hook-cv2.line23.comment On Windows, make sure that opencv_videoio_ffmpeg*.dll is bundled
binaries = []
if compat.is_win:
    # 012719.python.hook-cv2.line26.comment If conda is active, look for the DLL in its library path
    if compat.is_conda:
        libdir = os.path.join(compat.base_prefix, 'Library', 'bin')
        pattern = os.path.join(libdir, 'opencv_videoio_ffmpeg*.dll')
        for f in glob.glob(pattern):

            binaries.append((f, '.'))

    # 012720.python.hook-cv2.line34.comment Include any DLLs from site-packages/cv2 (opencv_videoio_ffmpeg*.dll
    # 012721.python.hook-cv2.line35.comment can be found there in the PyPI version)
    binaries += hookutils.collect_dynamic_libs('cv2')

# 012722.python.hook-cv2.line38.comment Collect auxiliary sub-packages, such as `cv2.gapi`, `cv2.mat_wrapper`, `cv2.misc`, and `cv2.utils`. This also
# 012723.python.hook-cv2.line39.comment picks up submodules with valid module names, such as `cv2.config`, `cv2.load_config_py2`, and `cv2.load_config_py3`.
# 012724.python.hook-cv2.line40.comment Therefore, filter out `cv2.load_config_py2`.
hiddenimports += hookutils.collect_submodules('cv2', filter=lambda name: name != 'cv2.load_config_py2')

# 012725.python.hook-cv2.line43.comment We also need to explicitly exclude `cv2.load_config_py2` due to it being imported in `cv2.__init__`.
excludedimports = ['cv2.load_config_py2']

# 012726.python.hook-cv2.line46.comment OpenCV loader from 4.5.4.60 requires extra config files and modules.
# 012727.python.hook-cv2.line47.comment We need to collect `config.py`  and `load_config_py3`; to improve compatibility with PyInstaller < 5.2, where
# 012728.python.hook-cv2.line48.comment `module_collection_mode` (see below) is not implemented.
# 012729.python.hook-cv2.line49.comment We also need to collect `config-3.py` or `config-3.X.py`, whichever is available (the former is usually
# 012730.python.hook-cv2.line50.comment provided by PyPI wheels, while the latter seems to be used when user builds OpenCV from source).
datas = hookutils.collect_data_files(
    'cv2',
    include_py_files=True,
    includes=[
        'config.py',
        f'config-{sys.version_info[0]}.{sys.version_info[1]}.py',
        'config-3.py',
        'load_config_py3.py',
    ],
)


# 012731.python.hook-cv2.line63.comment The OpenCV versions that attempt to perform module substitution via sys.path manipulation (== 4.5.4.58, >= 4.6.0.66)
# 012732.python.hook-cv2.line64.comment do not directly import the cv2.cv2 extension anymore, so in order to ensure it is collected, we would need to add it
# 012733.python.hook-cv2.line65.comment to hidden imports. However, when OpenCV is built by user from source, the extension is not located in the package's
# 012734.python.hook-cv2.line66.comment root directory, but in python-3.X sub-directory, which precludes referencing via module name due to sub-directory
# 012735.python.hook-cv2.line67.comment not being a valid subpackage name. Hence, emulate the OpenCV's loader and execute `config-3.py` or `config-3.X.py`
# 012736.python.hook-cv2.line68.comment to obtain the search path.
def find_cv2_extension(config_file):
    # 012737.python.hook-cv2.line70.comment Prepare environment
    PYTHON_EXTENSIONS_PATHS = []
    LOADER_DIR = os.path.dirname(os.path.abspath(os.path.realpath(config_file)))

    global_vars = globals().copy()
    local_vars = locals().copy()

    # 012738.python.hook-cv2.line77.comment Exec the config file
    with open(config_file) as fp:
        code = compile(fp.read(), os.path.basename(config_file), 'exec')
    exec(code, global_vars, local_vars)

    # 012739.python.hook-cv2.line82.comment Read the modified PYTHON_EXTENSIONS_PATHS
    PYTHON_EXTENSIONS_PATHS = local_vars['PYTHON_EXTENSIONS_PATHS']
    if not PYTHON_EXTENSIONS_PATHS:
        return None

    # 012740.python.hook-cv2.line87.comment Search for extension file
    for extension_path in PYTHON_EXTENSIONS_PATHS:
        extension_path = pathlib.Path(extension_path)
        if compat.is_win:
            extension_files = list(extension_path.glob('cv2*.pyd'))
        else:
            extension_files = list(extension_path.glob('cv2*.so'))
        if extension_files:
            if len(extension_files) > 1:
                hookutils.logger.warning("Found multiple cv2 extension candidates: %s", extension_files)
            extension_file = extension_files[0]  # Take first (or hopefully the only one)

            hookutils.logger.debug("Found cv2 extension module: %s", extension_file)

            # 012742.python.hook-cv2.line101.comment Compute path relative to parent of config file (which should be the package's root)
            dest_dir = pathlib.Path("cv2") / extension_file.parent.relative_to(LOADER_DIR)
            return str(extension_file), str(dest_dir)

    hookutils.logger.warning(
        "Could not find cv2 extension module! Config file: %s, search paths: %s",
        config_file, PYTHON_EXTENSIONS_PATHS)

    return None


config_file = [
    src_path for src_path, _ in datas
    if os.path.basename(src_path) in (f'config-{sys.version_info[0]}.{sys.version_info[1]}.py', 'config-3.py')
]

if config_file:
    try:
        extension_info = find_cv2_extension(config_file[0])
        if extension_info:
            ext_src, ext_dst = extension_info
            # 012743.python.hook-cv2.line122.comment Due to bug in PyInstaller's TOC structure implementation (affecting PyInstaller up to latest version at
            # 012744.python.hook-cv2.line123.comment the time of writing, 5.9), we fail to properly resolve `cv2.cv2` EXTENSION entry's destination name if
            # 012745.python.hook-cv2.line124.comment we already have a BINARY entry with the same destination name. This results in verbatim `cv2.cv2` file
            # 012746.python.hook-cv2.line125.comment created in application directory in addition to the proper copy in the `cv2` sub-directoy.
            # 012747.python.hook-cv2.line126.comment Therefoe, if destination directory of the cv2 extension module is the top-level package directory, fall
            # 012748.python.hook-cv2.line127.comment back to using hiddenimports instead.
            if ext_dst == 'cv2':
                # 012749.python.hook-cv2.line129.comment Extension found in top-level package directory; likely a PyPI wheel.
                hiddenimports += ['cv2.cv2']
            else:
                # 012750.python.hook-cv2.line132.comment Extension found in sub-directory; use BINARY entry
                binaries += [extension_info]
    except Exception:
        hookutils.logger.warning("Failed to determine location of cv2 extension module!", exc_info=True)


# 012751.python.hook-cv2.line138.comment Mark the cv2 package to be collected in source form, bypassing PyInstaller's PYZ archive and FrozenImporter. This is
# 012752.python.hook-cv2.line139.comment necessary because recent versions of cv2 package attempt to perform module substritution via sys.path manipulation,
# 012753.python.hook-cv2.line140.comment which is incompatible with the way that FrozenImporter works. This requires pyinstaller/pyinstaller#6945, i.e.,
# 012754.python.hook-cv2.line141.comment PyInstaller >= 5.3. On earlier versions, the following statement does nothing, and problematic cv2 versions
# 012755.python.hook-cv2.line142.comment (== 4.5.4.58, >= 4.6.0.66) will not work.
# 012756.python.hook-cv2.line143.comment
# 012757.python.hook-cv2.line144.comment Note that the collect_data_files() above is still necessary, because some of the cv2 loader's config scripts are not
# 012758.python.hook-cv2.line145.comment valid module names (e.g., config-3.py). So the two collection approaches are complementary, and any overlap in files
# 012759.python.hook-cv2.line146.comment (e.g., __init__.py) is handled gracefully due to PyInstaller's uniqueness constraints on collected files.
module_collection_mode = 'py'

# 012760.python.hook-cv2.line149.comment In linux PyPI opencv-python wheels, the cv2 extension is linked against Qt, and the wheel bundles a basic subset of Qt
# 012761.python.hook-cv2.line150.comment shared libraries, plugins, and font files. This is not the case on other OSes (presumably native UI APIs are used by
# 012762.python.hook-cv2.line151.comment OpenCV HighGUI module), nor in the headless PyPI wheels (opencv-python-headless).
# 012763.python.hook-cv2.line152.comment The bundled Qt shared libraries should be picked up automatically due to binary dependency analysis, but we need to
# 012764.python.hook-cv2.line153.comment collect plugins and font files from the `qt` subdirectory.
if compat.is_linux:
    pkg_path = pathlib.Path(hookutils.get_module_file_attribute('cv2')).parent
    # 012765.python.hook-cv2.line156.comment Collect .ttf files fron fonts directory.
    # 012766.python.hook-cv2.line157.comment NOTE: since we are using glob, we can skip checks for (sub)directories' existence.
    qt_fonts_dir = pkg_path / 'qt' / 'fonts'
    datas += [
        (str(font_file), str(font_file.parent.relative_to(pkg_path.parent)))
        for font_file in qt_fonts_dir.rglob('*.ttf')
    ]
    # 012767.python.hook-cv2.line163.comment Collect .so files from plugins directory.
    qt_plugins_dir = pkg_path / 'qt' / 'plugins'
    binaries += [
        (str(plugin_file), str(plugin_file.parent.relative_to(pkg_path.parent)))
        for plugin_file in qt_plugins_dir.rglob('*.so')
    ]
