# 008043.python.hook-six.moves.line1.comment -----------------------------------------------------------------------------
# 008044.python.hook-six.moves.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008045.python.hook-six.moves.line3.comment
# 008046.python.hook-six.moves.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008047.python.hook-six.moves.line5.comment or later) with exception for distributing the bootloader.
# 008048.python.hook-six.moves.line6.comment
# 008049.python.hook-six.moves.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008050.python.hook-six.moves.line8.comment
# 008051.python.hook-six.moves.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008052.python.hook-six.moves.line10.comment -----------------------------------------------------------------------------

from PyInstaller import isolated


def pre_safe_import_module(api):
    """
    Add the `six.moves` module as a dynamically defined runtime module node and all modules mapped by
    `six._SixMetaPathImporter` as aliased module nodes to the passed graph.

    The `six.moves` module is dynamically defined at runtime by the `six` module and hence cannot be imported in the
    standard way. Instead, this hook adds a placeholder node for the `six.moves` module to the graph,
    which implicitly adds an edge from that node to the node for its parent `six` module. This ensures that the `six`
    module will be frozen into the executable. (Phew!)

    `six._SixMetaPathImporter` is a PEP 302-compliant module importer converting imports independent of the current
    Python version into imports specific to that version (e.g., under Python 3, from `from six.moves import
    tkinter_tix` to `import tkinter.tix`). For each such mapping, this hook adds a corresponding module alias to the
    graph allowing PyInstaller to translate the former to the latter.
    """
    @isolated.call
    def real_to_six_module_name():
        """
        Generate a dictionary from conventional module names to "six.moves" attribute names (e.g., from `tkinter.tix` to
        `six.moves.tkinter_tix`).
        """
        try:
            import six
        except ImportError:
            return None  # unavailable

        # 008054.python.hook-six.moves.line41.comment Iterate over the "six._moved_attributes" list rather than the "six._importer.known_modules" dictionary, as
        # 008055.python.hook-six.moves.line42.comment "urllib"-specific moved modules are overwritten in the latter with unhelpful "LazyModule" objects. If this is
        # 008056.python.hook-six.moves.line43.comment a moved module or attribute, map the corresponding module. In the case of moved attributes, the attribute's
        # 008057.python.hook-six.moves.line44.comment module is mapped while the attribute itself is mapped at runtime and hence ignored here.
        return {
            moved.mod: 'six.moves.' + moved.name
            for moved in six._moved_attributes if isinstance(moved, (six.MovedModule, six.MovedAttribute))
        }

    # 008058.python.hook-six.moves.line50.comment Add "six.moves" as a runtime package rather than module. Modules cannot physically contain submodules; only
    # 008059.python.hook-six.moves.line51.comment packages can. In "from"-style import statements (e.g., "from six.moves import queue"), this implies that:
    # 008060.python.hook-six.moves.line52.comment * Attributes imported from customary modules are guaranteed *NOT* to be submodules. Hence, ModuleGraph justifiably
    # 008061.python.hook-six.moves.line53.comment ignores these attributes. While some attributes declared by "six.moves" are ignorable non-modules (e.g.,
    # 008062.python.hook-six.moves.line54.comment functions, classes), others are non-ignorable submodules that must be imported. Adding "six.moves" as a runtime
    # 008063.python.hook-six.moves.line55.comment module causes ModuleGraph to ignore these submodules, which defeats the entire point.
    # 008064.python.hook-six.moves.line56.comment * Attributes imported from packages could be submodules. To disambiguate non-ignorable submodules from ignorable
    # 008065.python.hook-six.moves.line57.comment non-submodules (e.g., classes, variables), ModuleGraph first attempts to import these attributes as submodules.
    # 008066.python.hook-six.moves.line58.comment This is exactly what we want.
    if real_to_six_module_name is not None:
        api.add_runtime_package(api.module_name)
        for real_module_name, six_module_name in real_to_six_module_name.items():
            api.add_alias_module(real_module_name, six_module_name)
