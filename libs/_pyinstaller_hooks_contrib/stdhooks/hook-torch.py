# 017648.python.hook-torch.line1.comment ------------------------------------------------------------------
# 017649.python.hook-torch.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017650.python.hook-torch.line3.comment
# 017651.python.hook-torch.line4.comment This file is distributed under the terms of the GNU General Public
# 017652.python.hook-torch.line5.comment License (version 2.0 or later).
# 017653.python.hook-torch.line6.comment
# 017654.python.hook-torch.line7.comment The full license is available in LICENSE, distributed with
# 017655.python.hook-torch.line8.comment this software.
# 017656.python.hook-torch.line9.comment
# 017657.python.hook-torch.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017658.python.hook-torch.line11.comment ------------------------------------------------------------------

import os

from PyInstaller.utils.hooks import (
    logger,
    collect_data_files,
    is_module_satisfies,
    collect_dynamic_libs,
    collect_submodules,
    get_package_paths,
)

if is_module_satisfies("PyInstaller >= 6.0"):
    from PyInstaller import compat
    from PyInstaller.utils.hooks import PY_DYLIB_PATTERNS

    module_collection_mode = "pyz+py"
    warn_on_missing_hiddenimports = False

    datas = collect_data_files(
        "torch",
        excludes=[
            "**/*.h",
            "**/*.hpp",
            "**/*.cuh",
            "**/*.lib",
            "**/*.cpp",
            "**/*.pyi",
            "**/*.cmake",
        ],
    )
    hiddenimports = collect_submodules("torch")
    binaries = collect_dynamic_libs(
        "torch",
        # 017659.python.hook-torch.line46.comment Ensure we pick up fully-versioned .so files as well
        search_patterns=PY_DYLIB_PATTERNS + ['*.so.*'],
    )

    # 017660.python.hook-torch.line50.comment On Linux, torch wheels built with non-default CUDA version bundle CUDA libraries themselves (and should be handled
    # 017661.python.hook-torch.line51.comment by the above `collect_dynamic_libs`). Wheels built with default CUDA version (which are available on PyPI), on the
    # 017662.python.hook-torch.line52.comment other hand, use CUDA libraries provided by nvidia-* packages. Due to all possible combinations (CUDA libs from
    # 017663.python.hook-torch.line53.comment nvidia-* packages, torch-bundled CUDA libs, CPU-only CUDA libs) we do not add hidden imports directly, but instead
    # 017664.python.hook-torch.line54.comment attempt to infer them from requirements listed in the `torch` metadata.
    if compat.is_linux:
        def _infer_nvidia_hiddenimports():
            import packaging.requirements
            from _pyinstaller_hooks_contrib.compat import importlib_metadata
            from _pyinstaller_hooks_contrib.utils import nvidia_cuda as cudautils

            dist = importlib_metadata.distribution("torch")
            requirements = [packaging.requirements.Requirement(req) for req in dist.requires or []]
            requirements = [req.name for req in requirements if req.marker is None or req.marker.evaluate()]

            return cudautils.infer_hiddenimports_from_requirements(requirements)

        try:
            nvidia_hiddenimports = _infer_nvidia_hiddenimports()
        except Exception:
            # 017665.python.hook-torch.line70.comment Log the exception, but make it non-fatal
            logger.warning("hook-torch: failed to infer NVIDIA CUDA hidden imports!", exc_info=True)
            nvidia_hiddenimports = []
        logger.info("hook-torch: inferred hidden imports for CUDA libraries: %r", nvidia_hiddenimports)
        hiddenimports += nvidia_hiddenimports

        # 017666.python.hook-torch.line76.comment On Linux, prevent binary dependency analysis from generating symbolic links for libraries from `torch/lib` to
        # 017667.python.hook-torch.line77.comment the top-level application directory. These symbolic links seem to confuse `torch` about location of its shared
        # 017668.python.hook-torch.line78.comment libraries (likely because code in one of the libraries looks up the library file's location, but does not
        # 017669.python.hook-torch.line79.comment fully resolve it), and prevent it from finding dynamically-loaded libraries in `torch/lib` directory, such as
        # 017670.python.hook-torch.line80.comment `torch/lib/libtorch_cuda_linalg.so`. The issue was observed with earlier versions of `torch` builds provided
        # 017671.python.hook-torch.line81.comment by https://download.pytorch.org/whl/torch, specifically 1.13.1+cu117, 2.0.1+cu117, and 2.1.2+cu118; later
        # 017672.python.hook-torch.line82.comment versions do not seem to be affected. The wheels provided on PyPI do not seem to be affected, either, even
        # 017673.python.hook-torch.line83.comment for torch 1.13.1, 2.01, and 2.1.2. However, these symlinks should be not necessary on linux in general, so
        # 017674.python.hook-torch.line84.comment there should be no harm in suppressing them for all versions.
        # 017675.python.hook-torch.line85.comment
        # 017676.python.hook-torch.line86.comment The `bindepend_symlink_suppression` hook attribute requires PyInstaller >= 6.11, and is no-op in earlier
        # 017677.python.hook-torch.line87.comment versions.
        bindepend_symlink_suppression = ['**/torch/lib/*.so*']

    # 017678.python.hook-torch.line90.comment The Windows nightly build for torch 2.3.0 added dependency on MKL. The `mkl` distribution does not provide an
    # 017679.python.hook-torch.line91.comment importable package, but rather installs the DLLs in <env>/Library/bin directory. Therefore, we cannot write a
    # 017680.python.hook-torch.line92.comment separate hook for it, and must collect the DLLs here. (Most of these DLLs are missed by PyInstaller's binary
    # 017681.python.hook-torch.line93.comment dependency analysis due to being dynamically loaded at run-time).
    if compat.is_win:
        def _collect_mkl_dlls():
            # 017682.python.hook-torch.line96.comment Determine if torch is packaged by Anaconda or not. Ideally, we would use our `get_installer()` hook
            # 017683.python.hook-torch.line97.comment utility function to check if installer is `conda`. However, it seems that some builds (e.g., those from
            # 017684.python.hook-torch.line98.comment `pytorch` and `nvidia` channels) provide legacy metadata in form of .egg-info directory, which does not
            # 017685.python.hook-torch.line99.comment include an INSTALLER file. So instead, search the conda metadata for a conda distribution/package that
            # 017686.python.hook-torch.line100.comment provides a `torch` importable package, if any.
            conda_torch_dist = None
            if compat.is_conda:
                from PyInstaller.utils.hooks import conda_support
                try:
                    conda_torch_dist = conda_support.package_distribution('torch')
                except ModuleNotFoundError:
                    conda_torch_dist = None

            if conda_torch_dist:
                # 017687.python.hook-torch.line110.comment Anaconda-packaged torch
                if 'mkl' not in conda_torch_dist.dependencies:
                    logger.info('hook-torch: this torch build (Anaconda package) does not depend on MKL...')
                    return []

                logger.info('hook-torch: collecting DLLs from MKL and its dependencies (Anaconda packages)')
                mkl_binaries = conda_support.collect_dynamic_libs('mkl', dependencies=True)
            else:
                # 017688.python.hook-torch.line118.comment Non-Anaconda torch (e.g., PyPI wheel)
                import packaging.requirements
                from _pyinstaller_hooks_contrib.compat import importlib_metadata

                # 017689.python.hook-torch.line122.comment Check if torch depends on `mkl`
                dist = importlib_metadata.distribution("torch")
                requirements = [packaging.requirements.Requirement(req) for req in dist.requires or []]
                requirements = [req.name for req in requirements if req.marker is None or req.marker.evaluate()]
                if 'mkl' not in requirements:
                    logger.info('hook-torch: this torch build does not depend on MKL...')
                    return []

                # 017690.python.hook-torch.line130.comment Find requirements of mkl - this should yield `intel-openmp` and `tbb`, which install DLLs in the same
                # 017691.python.hook-torch.line131.comment way as `mkl`.
                try:
                    dist = importlib_metadata.distribution("mkl")
                except importlib_metadata.PackageNotFoundError:
                    return []  # For some reason, `mkl` distribution is unavailable.
                requirements = [packaging.requirements.Requirement(req) for req in dist.requires or []]
                requirements = [req.name for req in requirements if req.marker is None or req.marker.evaluate()]

                requirements = ['mkl'] + requirements

                mkl_binaries = []
                logger.info('hook-torch: collecting DLLs from MKL and its dependencies: %r', requirements)
                for requirement in requirements:
                    try:
                        dist = importlib_metadata.distribution(requirement)
                    except importlib_metadata.PackageNotFoundError:
                        continue

                    # 017693.python.hook-torch.line149.comment Go over files, and match DLLs in <env>/Library/bin directory
                    for dist_file in (dist.files or []):
                        # 017694.python.hook-torch.line151.comment NOTE: `importlib_metadata.PackagePath.match()` does not seem to properly normalize the
                        # 017695.python.hook-torch.line152.comment separator, and on Windows, RECORD can apparently end up with entries that use either Windows
                        # 017696.python.hook-torch.line153.comment or POSIX-style separators (see pyinstaller/pyinstaller-hooks-contrib#879). This is why we
                        # 017697.python.hook-torch.line154.comment first resolve the file's location (which yields a `pathlib.Path` instance), and perform
                        # 017698.python.hook-torch.line155.comment matching on resolved path.
                        dll_file = dist.locate_file(dist_file).resolve()
                        if not dll_file.match('**/Library/bin/*.dll'):
                            continue
                        mkl_binaries.append((str(dll_file), '.'))

            if mkl_binaries:
                logger.info(
                    'hook-torch: found MKL DLLs: %r',
                    sorted([os.path.basename(src_name) for src_name, dest_name in mkl_binaries])
                )
            else:
                logger.info('hook-torch: no MKL DLLs found.')

            return mkl_binaries

        try:
            mkl_binaries = _collect_mkl_dlls()
        except Exception:
            # 017699.python.hook-torch.line174.comment Log the exception, but make it non-fatal
            logger.warning("hook-torch: failed to collect MKL DLLs!", exc_info=True)
            mkl_binaries = []
        binaries += mkl_binaries
else:
    datas = [(get_package_paths("torch")[1], "torch")]
