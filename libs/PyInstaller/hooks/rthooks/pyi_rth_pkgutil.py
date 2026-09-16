# 008426.python.pyi_rth_pkgutil.line1.comment -----------------------------------------------------------------------------
# 008427.python.pyi_rth_pkgutil.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 008428.python.pyi_rth_pkgutil.line3.comment
# 008429.python.pyi_rth_pkgutil.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008430.python.pyi_rth_pkgutil.line5.comment you may not use this file except in compliance with the License.
# 008431.python.pyi_rth_pkgutil.line6.comment
# 008432.python.pyi_rth_pkgutil.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008433.python.pyi_rth_pkgutil.line8.comment
# 008434.python.pyi_rth_pkgutil.line9.comment SPDX-License-Identifier: Apache-2.0
# 008435.python.pyi_rth_pkgutil.line10.comment -----------------------------------------------------------------------------
# 008436.python.pyi_rth_pkgutil.line11.comment
# 008437.python.pyi_rth_pkgutil.line12.comment The run-time hook provides a custom module iteration function for our PyiFrozenFinder, which allows
# 008438.python.pyi_rth_pkgutil.line13.comment `pkgutil.iter_modules()` to return entries for modules that are embedded in the PYZ archive. The non-embedded modules
# 008439.python.pyi_rth_pkgutil.line14.comment (binary extensions, modules collected as only source .py files, etc.) are enumerated using the `fallback_finder`
# 008440.python.pyi_rth_pkgutil.line15.comment provided by `PyiFrozenFinder` (which typically would be the python's `FileFinder`).
def _pyi_rthook():
    import pkgutil

    import pyimod02_importers  # PyInstaller's bootstrap module

    # 008442.python.pyi_rth_pkgutil.line21.comment This could, in fact, be implemented as `iter_modules()` method of the `PyiFrozenFinder`. However, we want to
    # 008443.python.pyi_rth_pkgutil.line22.comment avoid importing `pkgutil` in that bootstrap module (i.e., for the `pkgutil.iter_importer_modules()` call on the
    # 008444.python.pyi_rth_pkgutil.line23.comment fallback finder).
    def _iter_pyi_frozen_finder_modules(finder, prefix=''):
        # 008445.python.pyi_rth_pkgutil.line25.comment Fetch PYZ TOC tree from pyimod02_importers
        pyz_toc_tree = pyimod02_importers.get_pyz_toc_tree()

        # 008446.python.pyi_rth_pkgutil.line28.comment Finder has already pre-computed the package prefix implied by the search path. Use it to find the starting
        # 008447.python.pyi_rth_pkgutil.line29.comment node in the prefix tree.
        if finder._pyz_entry_prefix:
            pkg_name_parts = finder._pyz_entry_prefix.split('.')
        else:
            pkg_name_parts = []

        tree_node = pyz_toc_tree
        for pkg_name_part in pkg_name_parts:
            tree_node = tree_node.get(pkg_name_part)
            if not isinstance(tree_node, dict):
                # 008448.python.pyi_rth_pkgutil.line39.comment This check handles two cases:
                # 008449.python.pyi_rth_pkgutil.line40.comment a) path does not exist (`tree_node` is `None`)
                # 008450.python.pyi_rth_pkgutil.line41.comment b) path corresponds to a module instead of a package (`tree_node` is a leaf node (`str`)).
                tree_node = {}
                break

        # 008451.python.pyi_rth_pkgutil.line45.comment Dump the contents of the tree node.
        for entry_name, entry_data in tree_node.items():
            is_pkg = isinstance(entry_data, dict)
            yield prefix + entry_name, is_pkg

        # 008452.python.pyi_rth_pkgutil.line50.comment If our finder has a fall-back finder available, iterate its modules as well. By using the public
        # 008453.python.pyi_rth_pkgutil.line51.comment `fallback_finder` attribute, we force creation of the fallback finder as necessary.
        # 008454.python.pyi_rth_pkgutil.line52.comment NOTE: we do not care about potential duplicates here, because `pkgutil.iter_modules()` itself
        # 008455.python.pyi_rth_pkgutil.line53.comment keeps track of yielded names for purposes of de-duplication.
        if finder.fallback_finder is not None:
            yield from pkgutil.iter_importer_modules(finder.fallback_finder, prefix)

    pkgutil.iter_importer_modules.register(
        pyimod02_importers.PyiFrozenFinder,
        _iter_pyi_frozen_finder_modules,
    )


_pyi_rthook()
del _pyi_rthook
