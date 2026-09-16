# 015578.python.hook-pydicom.line1.comment ------------------------------------------------------------------
# 015579.python.hook-pydicom.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 015580.python.hook-pydicom.line3.comment
# 015581.python.hook-pydicom.line4.comment This file is distributed under the terms of the GNU General Public
# 015582.python.hook-pydicom.line5.comment License (version 2.0 or later).
# 015583.python.hook-pydicom.line6.comment
# 015584.python.hook-pydicom.line7.comment The full license is available in LICENSE, distributed with
# 015585.python.hook-pydicom.line8.comment this software.
# 015586.python.hook-pydicom.line9.comment
# 015587.python.hook-pydicom.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015588.python.hook-pydicom.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files

hiddenimports = []
datas = []

# 015589.python.hook-pydicom.line18.comment In pydicom 3.0.0, the `pydicom.encoders` plugins were renamed to `pydicom.pixels.encoders`, and
# 015590.python.hook-pydicom.line19.comment `pydicom.pixels.decoders` were also added. We need to collect them all, because they are loaded during
# 015591.python.hook-pydicom.line20.comment `pydicom` module initialization. We intentionally avoid using `collect_submodules` here, because that causes
# 015592.python.hook-pydicom.line21.comment import of `pydicom` with logging framework initialized, which results in error tracebacks being logged for all plugins
# 015593.python.hook-pydicom.line22.comment with missing libraries (see https://github.com/pydicom/pydicom/issues/2128).
if is_module_satisfies('pydicom >= 3.0.0'):
    hiddenimports += [
        "pydicom.pixels.decoders.gdcm",
        "pydicom.pixels.decoders.pylibjpeg",
        "pydicom.pixels.decoders.pillow",
        "pydicom.pixels.decoders.pyjpegls",
        "pydicom.pixels.decoders.rle",
        "pydicom.pixels.encoders.gdcm",
        "pydicom.pixels.encoders.pylibjpeg",
        "pydicom.pixels.encoders.native",
        "pydicom.pixels.encoders.pyjpegls",
    ]

    # 015594.python.hook-pydicom.line36.comment With pydicom 3.0.0, initialization of `pydicom` (unnecessarily) imports `pydicom.examples`, which attempts to set
    # 015595.python.hook-pydicom.line37.comment up several test datasets: https://github.com/pydicom/pydicom/blob/v3.0.0/src/pydicom/examples/__init__.py#L10-L24
    # 015596.python.hook-pydicom.line38.comment Some of those are bundled with the package itself, some are downloaded (into `.pydicom/data` directory in user's
    # 015597.python.hook-pydicom.line39.comment home directory) on he first `pydicom.examples` import.
    # 015598.python.hook-pydicom.line40.comment
    # 015599.python.hook-pydicom.line41.comment The download code requires `pydicom/data/urls.json` and `pydicom/data/hashes.json`; the lack of former results in
    # 015600.python.hook-pydicom.line42.comment run-time error, while the lack of latter results in warnings about dataset download failure.
    # 015601.python.hook-pydicom.line43.comment
    # 015602.python.hook-pydicom.line44.comment The test data files that are bundled with the package are not listed in `urls.json`, so if they are missing, there
    # 015603.python.hook-pydicom.line45.comment is not attempt to download them. Therefore, try to get away without collecting them here - if anyone actually
    # 015604.python.hook-pydicom.line46.comment requires them in the frozen application, let them explicitly collect them.
    additional_data_patterns = [
        'urls.json',
        'hashes.json',
    ]
else:
    hiddenimports += [
        "pydicom.encoders.gdcm",
        "pydicom.encoders.pylibjpeg",
        "pydicom.encoders.native",
    ]
    additional_data_patterns = []

# 015605.python.hook-pydicom.line59.comment Collect data files from `pydicom.data`; charset files and palettes might be needed during processing, so always
# 015606.python.hook-pydicom.line60.comment collect them. Some other data files became required in v3.0.0 - the corresponding patterns are set accordingly in
# 015607.python.hook-pydicom.line61.comment `additional_data_patterns` in the above if/else block.
datas += collect_data_files(
    'pydicom.data',
    includes=[
        'charset_files/*',
        'palettes/*',
        *additional_data_patterns,
    ],
)
