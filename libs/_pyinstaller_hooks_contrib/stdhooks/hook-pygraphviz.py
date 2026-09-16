# 015825.python.hook-pygraphviz.line1.comment ------------------------------------------------------------------
# 015826.python.hook-pygraphviz.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 015827.python.hook-pygraphviz.line3.comment
# 015828.python.hook-pygraphviz.line4.comment This file is distributed under the terms of the GNU General Public
# 015829.python.hook-pygraphviz.line5.comment License (version 2.0 or later).
# 015830.python.hook-pygraphviz.line6.comment
# 015831.python.hook-pygraphviz.line7.comment The full license is available in LICENSE, distributed with
# 015832.python.hook-pygraphviz.line8.comment this software.
# 015833.python.hook-pygraphviz.line9.comment
# 015834.python.hook-pygraphviz.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015835.python.hook-pygraphviz.line11.comment ------------------------------------------------------------------
import os
import pathlib
import shutil

from PyInstaller import compat
from PyInstaller.depend import bindepend
from PyInstaller.utils.hooks import logger


def _collect_graphviz_files():
    binaries = []
    datas = []

    # 015836.python.hook-pygraphviz.line25.comment A working `pygraphviz` installation requires graphviz programs in PATH. Attempt to resolve the `dot` executable to
    # 015837.python.hook-pygraphviz.line26.comment see if this is the case.
    dot_binary = shutil.which('dot')
    if not dot_binary:
        logger.warning(
            "hook-pygraphviz: 'dot' program not found in PATH!"
        )
        return binaries, datas
    logger.info("hook-pygraphviz: found 'dot' program: %r", dot_binary)
    bin_dir = pathlib.Path(dot_binary).parent

    # 015838.python.hook-pygraphviz.line36.comment Collect graphviz programs that might be called from `pygaphviz.agraph.AGraph`:
    # 015839.python.hook-pygraphviz.line37.comment https://github.com/pygraphviz/pygraphviz/blob/pygraphviz-1.14/pygraphviz/agraph.py#L1330-L1348
    # 015840.python.hook-pygraphviz.line38.comment On macOS and on Linux, several of these are symbolic links to a single executable.
    progs = (
        "neato",
        "dot",
        "twopi",
        "circo",
        "fdp",
        "nop",
        "osage",
        "patchwork",
        "gc",
        "acyclic",
        "gvpr",
        "gvcolor",
        "ccomps",
        "sccmap",
        "tred",
        "sfdp",
        "unflatten",
    )

    logger.debug("hook-pygraphviz: collecting graphviz program executables...")
    for program_name in progs:
        program_binary = shutil.which(program_name)
        if not program_binary:
            logger.debug("hook-pygaphviz: graphviz program %r not found!", program_name)
            continue

        # 015841.python.hook-pygraphviz.line66.comment Ensure that the program executable was found in the same directory as the `dot` executable. This should
        # 015842.python.hook-pygraphviz.line67.comment prevent us from falling back to other graphviz installations that happen to be in PATH.
        if pathlib.Path(program_binary).parent != bin_dir:
            logger.debug(
                "hook-pygraphviz: found program %r (%r) outside of directory %r - ignoring!",
                program_name, program_binary, str(bin_dir)
            )
            continue

        logger.debug("hook-pygraphviz: collecting graphviz program %r: %r", program_name, program_binary)
        binaries += [(program_binary, '.')]

    # 015843.python.hook-pygraphviz.line78.comment Graphviz shared libraries should be automatically collected when PyInstaller performs binary dependency
    # 015844.python.hook-pygraphviz.line79.comment analysis of the collected program executables as part of the main build process. However, we need to manually
    # 015845.python.hook-pygraphviz.line80.comment collect plugins and their accompanying config file.
    logger.debug("hook-pygraphviz: looking for graphviz plugin directory...")
    if compat.is_win:
        # 015846.python.hook-pygraphviz.line83.comment Under Windows, we have several installation variants:
        # 015847.python.hook-pygraphviz.line84.comment - official installers and builds from https://gitlab.com/graphviz/graphviz/-/releases
        # 015848.python.hook-pygraphviz.line85.comment - chocolatey
        # 015849.python.hook-pygraphviz.line86.comment - msys2
        # 015850.python.hook-pygraphviz.line87.comment - Anaconda
        # 015851.python.hook-pygraphviz.line88.comment In all variants, the plugins and the config file are located in the `bin` directory, next to the program
        # 015852.python.hook-pygraphviz.line89.comment executables.
        plugin_dir = bin_dir
        plugin_dest_dir = '.'  # Collect into top-level application directory.
        # 015854.python.hook-pygraphviz.line92.comment Official builds and Anaconda use unversioned `gvplugin-{name}.dll` plugin names, while msys2 uses
        # 015855.python.hook-pygraphviz.line93.comment versioned `libgvplugin-{name}-{version}.dll` plugin names (with "lib" prefix).
        plugin_pattern = '*gvplugin*.dll'
    else:
        # 015856.python.hook-pygraphviz.line96.comment Perform binary dependency analysis on the `dot` executable to obtain the path to graphiz shared libraries.
        # 015857.python.hook-pygraphviz.line97.comment These need to be in the library search path for the programs to work, or discoverable via run-paths
        # 015858.python.hook-pygraphviz.line98.comment (e.g., Anaconda on Linux and macOS, Homebrew on macOS).
        graphviz_lib_candidates = ['cdt', 'gvc', 'cgraph']

        if hasattr(bindepend, 'get_imports'):
            # 015859.python.hook-pygraphviz.line102.comment PyInstaller >= 6.0
            dot_imports = [path for name, path in bindepend.get_imports(dot_binary) if path is not None]
        else:
            # 015860.python.hook-pygraphviz.line105.comment PyInstaller < 6.0
            dot_imports = bindepend.getImports(dot_binary)

        graphviz_lib_paths = [
            path for path in dot_imports
            if any(candidate in os.path.basename(path) for candidate in graphviz_lib_candidates)
        ]

        if not graphviz_lib_paths:
            logger.warning("hook-pygraphviz: could not determine location of graphviz shared libraries!")
            return binaries, datas

        graphviz_lib_dir = pathlib.Path(graphviz_lib_paths[0]).parent
        logger.debug("hook-pygraphviz: location of graphviz shared libraries: %r", str(graphviz_lib_dir))

        # 015861.python.hook-pygraphviz.line120.comment Plugins should be located in `graphviz` directory next to shared libraries.
        plugin_dir = graphviz_lib_dir / 'graphviz'
        plugin_dest_dir = 'graphviz'  # Collect into graphviz sub-directory.

        if compat.is_darwin:
            plugin_pattern = '*gvplugin*.dylib'
        else:
            # 015863.python.hook-pygraphviz.line127.comment Collect only versioned .so library files (for example, `/lib64/graphviz/libgvplugin_core.so.6` and
            # 015864.python.hook-pygraphviz.line128.comment `/lib64/graphviz/libgvplugin_core.so.6.0.0`; the former usually being a symbolic link to the latter).
            # 015865.python.hook-pygraphviz.line129.comment The unversioned .so library files (such as `lib64/graphviz/libgvplugin_core.so`), if available, are
            # 015866.python.hook-pygraphviz.line130.comment meant for linking (and are usually installed as part of development package).
            plugin_pattern = '*gvplugin*.so.*'

    if not plugin_dir.is_dir():
        logger.warning("hook-pygraphviz: could not determine location of graphviz plugins!")
        return binaries, datas

    logger.info("hook-pygraphviz: collecting graphviz plugins from directory: %r", str(plugin_dir))

    binaries += [(str(file), plugin_dest_dir) for file in plugin_dir.glob(plugin_pattern)]
    datas += [(str(file), plugin_dest_dir) for file in plugin_dir.glob("config*")]  # e.g., `config6`

    return binaries, datas


binaries, datas = _collect_graphviz_files()
