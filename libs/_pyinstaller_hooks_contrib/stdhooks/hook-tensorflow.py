# 017400.python.hook-tensorflow.line1.comment ------------------------------------------------------------------
# 017401.python.hook-tensorflow.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017402.python.hook-tensorflow.line3.comment
# 017403.python.hook-tensorflow.line4.comment This file is distributed under the terms of the GNU General Public
# 017404.python.hook-tensorflow.line5.comment License (version 2.0 or later).
# 017405.python.hook-tensorflow.line6.comment
# 017406.python.hook-tensorflow.line7.comment The full license is available in LICENSE, distributed with
# 017407.python.hook-tensorflow.line8.comment this software.
# 017408.python.hook-tensorflow.line9.comment
# 017409.python.hook-tensorflow.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017410.python.hook-tensorflow.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.compat import importlib_metadata
from packaging.version import Version

from PyInstaller.compat import is_linux
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    get_module_attribute,
    is_module_satisfies,
    logger,
)

# 017411.python.hook-tensorflow.line26.comment Determine the name of `tensorflow` dist; this is available under different names (releases vs. nightly, plus build
# 017412.python.hook-tensorflow.line27.comment variants). We need to determine the dist that we are dealing with, so we can query its version and metadata.
_CANDIDATE_DIST_NAMES = (
    "tensorflow",
    "tensorflow-cpu",
    "tensorflow-gpu",
    "tensorflow-intel",
    "tensorflow-rocm",
    "tensorflow-macos",
    "tensorflow-aarch64",
    "tensorflow-cpu-aws",
    "tf-nightly",
    "tf-nightly-cpu",
    "tf-nightly-gpu",
    "tf-nightly-rocm",
    "intel-tensorflow",
    "intel-tensorflow-avx512",
)
dist = None
for candidate_dist_name in _CANDIDATE_DIST_NAMES:
    try:
        dist = importlib_metadata.distribution(candidate_dist_name)
        break
    except importlib_metadata.PackageNotFoundError:
        continue

version = None
if dist is None:
    logger.warning(
        "hook-tensorflow: failed to determine tensorflow dist name! Reading version from tensorflow.__version__!"
    )
    try:
        version = get_module_attribute("tensorflow", "__version__")
    except Exception as e:
        raise Exception("Failed to read tensorflow.__version__") from e
else:
    logger.info("hook-tensorflow: tensorflow dist name: %s", dist.name)
    version = dist.version

# 017413.python.hook-tensorflow.line65.comment Parse version
logger.info("hook-tensorflow: tensorflow version: %s", version)
try:
    version = Version(version)
except Exception as e:
    raise Exception("Failed to parse tensorflow version!") from e

# 017414.python.hook-tensorflow.line72.comment Exclude from data collection:
# 017415.python.hook-tensorflow.line73.comment - development headers in include subdirectory
# 017416.python.hook-tensorflow.line74.comment - XLA AOT runtime sources
# 017417.python.hook-tensorflow.line75.comment - libtensorflow_framework and libtensorflow_cc (since TF 2.12) shared libraries (to avoid duplication)
# 017418.python.hook-tensorflow.line76.comment - import library (.lib) files (Windows-only)
data_excludes = [
    "include",
    "xla_aot_runtime_src",
    "libtensorflow_framework.*",
    "libtensorflow_cc.*",
    "**/*.lib",
]

# 017419.python.hook-tensorflow.line85.comment Under tensorflow 2.3.0 (the most recent version at the time of writing), _pywrap_tensorflow_internal extension module
# 017420.python.hook-tensorflow.line86.comment ends up duplicated; once as an extension, and once as a shared library. In addition to increasing program size, this
# 017421.python.hook-tensorflow.line87.comment also causes problems on macOS, so we try to prevent the extension module "variant" from being picked up.
# 017422.python.hook-tensorflow.line88.comment
# 017423.python.hook-tensorflow.line89.comment See pyinstaller/pyinstaller-hooks-contrib#49 for details.
# 017424.python.hook-tensorflow.line90.comment
# 017425.python.hook-tensorflow.line91.comment With PyInstaller >= 6.0, this issue is alleviated, because the binary dependency analysis (which picks up the
# 017426.python.hook-tensorflow.line92.comment extension in question as a shared library that other extensions are linked against) now preserves the parent directory
# 017427.python.hook-tensorflow.line93.comment layout, and creates a symbolic link to the top-level application directory.
if is_module_satisfies('PyInstaller >= 6.0'):
    excluded_submodules = []
else:
    excluded_submodules = ['tensorflow.python._pywrap_tensorflow_internal']


def _submodules_filter(x):
    return x not in excluded_submodules


if version < Version("1.15.0a0"):
    # 017428.python.hook-tensorflow.line105.comment 1.14.x and earlier: collect everything from tensorflow
    hiddenimports = collect_submodules('tensorflow', filter=_submodules_filter)
    datas = collect_data_files('tensorflow', excludes=data_excludes)
elif version >= Version("1.15.0a0") and version < Version("2.2.0a0"):
    # 017429.python.hook-tensorflow.line109.comment 1.15.x - 2.1.x: collect everything from tensorflow_core
    hiddenimports = collect_submodules('tensorflow_core', filter=_submodules_filter)
    datas = collect_data_files('tensorflow_core', excludes=data_excludes)

    # 017430.python.hook-tensorflow.line113.comment Under 1.15.x, we seem to fail collecting a specific submodule, and need to add it manually...
    if version < Version("2.0.0a0"):
        hiddenimports += ['tensorflow_core._api.v1.compat.v2.summary.experimental']
else:
    # 017431.python.hook-tensorflow.line117.comment 2.2.0 and newer: collect everything from tensorflow again
    hiddenimports = collect_submodules('tensorflow', filter=_submodules_filter)
    datas = collect_data_files('tensorflow', excludes=data_excludes)

    # 017432.python.hook-tensorflow.line121.comment From 2.6.0 on, we also need to explicitly collect keras (due to lazy mapping of tensorflow.keras.xyz -> keras.xyz)
    if version >= Version("2.6.0a0"):
        hiddenimports += collect_submodules('keras')

    # 017433.python.hook-tensorflow.line125.comment Starting with 2.14.0, we need `ml_dtypes` among hidden imports.
    if version >= Version("2.14.0"):
        hiddenimports += ['ml_dtypes']

binaries = []
excludedimports = excluded_submodules

# 017434.python.hook-tensorflow.line132.comment Suppress warnings for missing hidden imports generated by this hook.
# 017435.python.hook-tensorflow.line133.comment Requires PyInstaller > 5.1 (with pyinstaller/pyinstaller#6914 merged); no-op otherwise.
warn_on_missing_hiddenimports = False

# 017436.python.hook-tensorflow.line136.comment Collect the AutoGraph part of `tensorflow` code, to avoid a run-time warning about AutoGraph being unavailable:
# 017437.python.hook-tensorflow.line137.comment `WARNING:tensorflow:AutoGraph is not available in this environment: functions lack code information. ...`
# 017438.python.hook-tensorflow.line138.comment The warning is emitted if source for `log` function from `tensorflow.python.autograph.utils.ag_logging` cannot be
# 017439.python.hook-tensorflow.line139.comment looked up. Not sure if we need sources for other parts of `tesnorflow`, though.
# 017440.python.hook-tensorflow.line140.comment Requires PyInstaller >= 5.3, no-op in older versions.
module_collection_mode = {
    'tensorflow.python.autograph': 'py+pyz',
}

# 017441.python.hook-tensorflow.line145.comment Linux builds of tensorflow can optionally use CUDA from nvidia-* packages. If we managed to obtain dist, query the
# 017442.python.hook-tensorflow.line146.comment requirements from metadata (the `and-cuda` extra marker), and convert them to module names.
# 017443.python.hook-tensorflow.line147.comment
# 017444.python.hook-tensorflow.line148.comment NOTE: while the installation of nvidia-* packages via `and-cuda` extra marker is not gated by the OS version check,
# 017445.python.hook-tensorflow.line149.comment it is effectively available only on Linux (last Windows-native build that supported GPU is v2.10.0, and assumed that
# 017446.python.hook-tensorflow.line150.comment CUDA is externally available).
if is_linux and dist is not None:
    def _infer_nvidia_hiddenimports():
        import packaging.requirements
        from _pyinstaller_hooks_contrib.utils import nvidia_cuda as cudautils

        requirements = [packaging.requirements.Requirement(req) for req in dist.requires or []]
        env = {'extra': 'and-cuda'}
        requirements = [req.name for req in requirements if req.marker is None or req.marker.evaluate(env)]

        return cudautils.infer_hiddenimports_from_requirements(requirements)

    try:
        nvidia_hiddenimports = _infer_nvidia_hiddenimports()
    except Exception:
        # 017447.python.hook-tensorflow.line165.comment Log the exception, but make it non-fatal
        logger.warning("hook-tensorflow: failed to infer NVIDIA CUDA hidden imports!", exc_info=True)
        nvidia_hiddenimports = []
    logger.info("hook-tensorflow: inferred hidden imports for CUDA libraries: %r", nvidia_hiddenimports)
    hiddenimports += nvidia_hiddenimports


# 017448.python.hook-tensorflow.line172.comment Collect the tensorflow-plugins (pluggable device plugins)
hiddenimports += ['tensorflow-plugins']
binaries += collect_dynamic_libs('tensorflow-plugins')

# 017449.python.hook-tensorflow.line176.comment On Linux, prevent binary dependency analysis from generating symbolic links for libtensorflow_cc.so.2,
# 017450.python.hook-tensorflow.line177.comment libtensorflow_framework.so.2, and _pywrap_tensorflow_internal.so to the top-level application directory. These
# 017451.python.hook-tensorflow.line178.comment symbolic links seem to confuse tensorflow about its location (likely because code in one of the libraries looks up the
# 017452.python.hook-tensorflow.line179.comment library file's location, but does not fully resolve it), which in turn prevents it from finding the collected CUDA
# 017453.python.hook-tensorflow.line180.comment libraries in the nvidia/cu* package directories.
# 017454.python.hook-tensorflow.line181.comment
# 017455.python.hook-tensorflow.line182.comment The `bindepend_symlink_suppression` hook attribute requires PyInstaller >= 6.11, and is no-op in earlier versions.
if is_linux:
    bindepend_symlink_suppression = [
        '**/libtensorflow_cc.so*',
        '**/libtensorflow_framework.so*',
        '**/_pywrap_tensorflow_internal.so',
    ]
