# 008358.python.pyi_rth_pkgres.line1.comment -----------------------------------------------------------------------------
# 008359.python.pyi_rth_pkgres.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008360.python.pyi_rth_pkgres.line3.comment
# 008361.python.pyi_rth_pkgres.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008362.python.pyi_rth_pkgres.line5.comment you may not use this file except in compliance with the License.
# 008363.python.pyi_rth_pkgres.line6.comment
# 008364.python.pyi_rth_pkgres.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008365.python.pyi_rth_pkgres.line8.comment
# 008366.python.pyi_rth_pkgres.line9.comment SPDX-License-Identifier: Apache-2.0
# 008367.python.pyi_rth_pkgres.line10.comment -----------------------------------------------------------------------------

# 008368.python.pyi_rth_pkgres.line12.comment To make pkg_resources work with frozen modules, we need to set the 'Provider' class for PyiFrozenLoader.
# 008369.python.pyi_rth_pkgres.line13.comment This class decides where to look for resources and other stuff.
# 008370.python.pyi_rth_pkgres.line14.comment
# 008371.python.pyi_rth_pkgres.line15.comment 'pkg_resources.NullProvider' is dedicated to abitrary PEP302 loaders, such as our PyiFrozenLoader. It uses method
# 008372.python.pyi_rth_pkgres.line16.comment __loader__.get_data() in methods pkg_resources.resource_string() and pkg_resources.resource_stream().
# 008373.python.pyi_rth_pkgres.line17.comment
# 008374.python.pyi_rth_pkgres.line18.comment We provide PyiFrozenProvider, which subclasses the NullProvider and implements _has(), _isdir(), and _listdir()
# 008375.python.pyi_rth_pkgres.line19.comment methods, which are needed for pkg_resources.resource_exists(), resource_isdir(), and resource_listdir() to work. We
# 008376.python.pyi_rth_pkgres.line20.comment cannot use the DefaultProvider, because it provides filesystem-only implementations (and overrides _get() with a
# 008377.python.pyi_rth_pkgres.line21.comment filesystem-only one), whereas our provider needs to also support embedded resources.
# 008378.python.pyi_rth_pkgres.line22.comment
# 008379.python.pyi_rth_pkgres.line23.comment The PyiFrozenProvider allows querying/listing both PYZ-embedded and on-filesystem resources in a frozen package. The
# 008380.python.pyi_rth_pkgres.line24.comment results are typically combined for both types of resources (e.g., when listing a directory or checking whether a
# 008381.python.pyi_rth_pkgres.line25.comment resource exists). When the order of precedence matters, the PYZ-embedded resources take precedence over the
# 008382.python.pyi_rth_pkgres.line26.comment on-filesystem ones, to keep the behavior consistent with the actual file content retrieval via _get() method (which in
# 008383.python.pyi_rth_pkgres.line27.comment turn uses PyiFrozenLoader's get_data() method). For example, when checking whether a resource is a directory via
# 008384.python.pyi_rth_pkgres.line28.comment _isdir(), a PYZ-embedded file will take precedence over a potential on-filesystem directory. Also, in contrast to
# 008385.python.pyi_rth_pkgres.line29.comment unfrozen packages, the frozen ones do not contain source .py files, which are therefore absent from content listings.


def _pyi_rthook():
    import os
    import pathlib
    import sys
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=UserWarning,
            message="pkg_resources is deprecated",
        )
        import pkg_resources

    import pyimod02_importers  # PyInstaller's bootstrap module

    SYS_PREFIX = pathlib.PurePath(sys._MEIPASS)

    class _TocFilesystem:
        """
        A prefix tree implementation for embedded filesystem reconstruction.

        NOTE: as of PyInstaller 6.0, the embedded PYZ archive cannot contain data files anymore. Instead, it contains
        only .pyc modules - which are by design not returned by `PyiFrozenProvider`. So this implementation has been
        reduced to supporting only directories implied by collected packages.
        """
        def __init__(self, tree_node):
            self._tree = tree_node

        def _get_tree_node(self, path):
            path = pathlib.PurePath(path)
            current = self._tree
            for component in path.parts:
                if component not in current:
                    return None
                current = current[component]
            return current

        def path_exists(self, path):
            node = self._get_tree_node(path)
            return isinstance(node, dict)  # Directory only

        def path_isdir(self, path):
            node = self._get_tree_node(path)
            return isinstance(node, dict)  # Directory only

        def path_listdir(self, path):
            node = self._get_tree_node(path)
            if not isinstance(node, dict):
                return []  # Non-existent or file
            # 008390.python.pyi_rth_pkgres.line82.comment Return only sub-directories
            return [entry_name for entry_name, entry_data in node.items() if isinstance(entry_data, dict)]

    class PyiFrozenProvider(pkg_resources.NullProvider):
        """
        Custom pkg_resources provider for PyiFrozenLoader.
        """
        def __init__(self, module):
            super().__init__(module)

            # 008391.python.pyi_rth_pkgres.line92.comment Get top-level path; if "module" corresponds to a package, we need the path to the package itself.
            # 008392.python.pyi_rth_pkgres.line93.comment If "module" is a submodule in a package, we need the path to the parent package.
            # 008393.python.pyi_rth_pkgres.line94.comment
            # 008394.python.pyi_rth_pkgres.line95.comment This is equivalent to `pkg_resources.NullProvider.module_path`, except we construct a `pathlib.PurePath`
            # 008395.python.pyi_rth_pkgres.line96.comment for easier manipulation.
            # 008396.python.pyi_rth_pkgres.line97.comment
            # 008397.python.pyi_rth_pkgres.line98.comment NOTE: the path is NOT resolved for symbolic links, as neither are paths that are passed by `pkg_resources`
            # 008398.python.pyi_rth_pkgres.line99.comment to `_has`, `_isdir`, `_listdir` (they are all anchored to `module_path`, which in turn is just
            # 008399.python.pyi_rth_pkgres.line100.comment `os.path.dirname(module.__file__)`. As `__file__` returned by `PyiFrozenLoader` is always anchored to
            # 008400.python.pyi_rth_pkgres.line101.comment `sys._MEIPASS`, we do not have to worry about cross-linked directories in macOS .app bundles, where the
            # 008401.python.pyi_rth_pkgres.line102.comment resolved `__file__` could be either in the `Contents/Frameworks` directory (the "true" `sys._MEIPASS`), or
            # 008402.python.pyi_rth_pkgres.line103.comment in the `Contents/Resources` directory due to cross-linking.
            self._pkg_path = pathlib.PurePath(module.__file__).parent

            # 008403.python.pyi_rth_pkgres.line106.comment Construct _TocFilesystem on top of pre-computed prefix tree provided by pyimod02_importers.
            self.embedded_tree = _TocFilesystem(pyimod02_importers.get_pyz_toc_tree())

        def _normalize_path(self, path):
            # 008404.python.pyi_rth_pkgres.line110.comment Avoid using `Path.resolve`, because it resolves symlinks. This is undesirable, because the pure path in
            # 008405.python.pyi_rth_pkgres.line111.comment `self._pkg_path` does not have symlinks resolved, so comparison between the two would be faulty. Instead,
            # 008406.python.pyi_rth_pkgres.line112.comment use `os.path.normpath` to normalize the path and get rid of any '..' elements (the path itself should
            # 008407.python.pyi_rth_pkgres.line113.comment already be absolute).
            return pathlib.Path(os.path.normpath(path))

        def _is_relative_to_package(self, path):
            return path == self._pkg_path or self._pkg_path in path.parents

        def _has(self, path):
            # 008408.python.pyi_rth_pkgres.line120.comment Prevent access outside the package.
            path = self._normalize_path(path)
            if not self._is_relative_to_package(path):
                return False

            # 008409.python.pyi_rth_pkgres.line125.comment Check the filesystem first to avoid unnecessarily computing the relative path...
            if path.exists():
                return True
            rel_path = path.relative_to(SYS_PREFIX)
            return self.embedded_tree.path_exists(rel_path)

        def _isdir(self, path):
            # 008410.python.pyi_rth_pkgres.line132.comment Prevent access outside the package.
            path = self._normalize_path(path)
            if not self._is_relative_to_package(path):
                return False

            # 008411.python.pyi_rth_pkgres.line137.comment Embedded resources have precedence over filesystem...
            rel_path = path.relative_to(SYS_PREFIX)
            node = self.embedded_tree._get_tree_node(rel_path)
            if node is None:
                return path.is_dir()  # No match found; try the filesystem.
            else:
                # 008413.python.pyi_rth_pkgres.line143.comment str = file, dict = directory
                return not isinstance(node, str)

        def _listdir(self, path):
            # 008414.python.pyi_rth_pkgres.line147.comment Prevent access outside the package.
            path = self._normalize_path(path)
            if not self._is_relative_to_package(path):
                return []

            # 008415.python.pyi_rth_pkgres.line152.comment Relative path for searching embedded resources.
            rel_path = path.relative_to(SYS_PREFIX)
            # 008416.python.pyi_rth_pkgres.line154.comment List content from embedded filesystem...
            content = self.embedded_tree.path_listdir(rel_path)
            # 008417.python.pyi_rth_pkgres.line156.comment ... as well as the actual one.
            if path.is_dir():
                # 008418.python.pyi_rth_pkgres.line158.comment Use os.listdir() to avoid having to convert Path objects to strings... Also make sure to de-duplicate
                # 008419.python.pyi_rth_pkgres.line159.comment the results.
                path = str(path)  # not is_py36
                content = list(set(content + os.listdir(path)))
            return content

    pkg_resources.register_loader_type(pyimod02_importers.PyiFrozenLoader, PyiFrozenProvider)

    # 008421.python.pyi_rth_pkgres.line166.comment With our PyiFrozenFinder now being a path entry finder, it effectively replaces python's FileFinder. So we need
    # 008422.python.pyi_rth_pkgres.line167.comment to register it with `pkg_resources.find_on_path` to allow metadata to be found on filesystem.
    pkg_resources.register_finder(pyimod02_importers.PyiFrozenFinder, pkg_resources.find_on_path)

    # 008423.python.pyi_rth_pkgres.line170.comment For the above change to fully take effect, we need to re-initialize pkg_resources's master working set (since the
    # 008424.python.pyi_rth_pkgres.line171.comment original one was built with assumption that sys.path entries are handled by python's FileFinder).
    # 008425.python.pyi_rth_pkgres.line172.comment See https://github.com/pypa/setuptools/issues/373
    if hasattr(pkg_resources, '_initialize_master_working_set'):
        pkg_resources._initialize_master_working_set()


_pyi_rthook()
del _pyi_rthook
