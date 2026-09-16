# 011577.python.pyi_rth_pygraphviz.line1.comment -----------------------------------------------------------------------------
# 011578.python.pyi_rth_pygraphviz.line2.comment Copyright (c) 2021, PyInstaller Development Team.
# 011579.python.pyi_rth_pygraphviz.line3.comment
# 011580.python.pyi_rth_pygraphviz.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011581.python.pyi_rth_pygraphviz.line5.comment
# 011582.python.pyi_rth_pygraphviz.line6.comment The full license is available in LICENSE, distributed with
# 011583.python.pyi_rth_pygraphviz.line7.comment this software.
# 011584.python.pyi_rth_pygraphviz.line8.comment
# 011585.python.pyi_rth_pygraphviz.line9.comment SPDX-License-Identifier: Apache-2.0
# 011586.python.pyi_rth_pygraphviz.line10.comment -----------------------------------------------------------------------------

import pygraphviz

# 011587.python.pyi_rth_pygraphviz.line14.comment Override pygraphviz.AGraph._which method to search for graphviz executables inside sys._MEIPASS
if hasattr(pygraphviz.AGraph, '_which'):

    def _pygraphviz_override_which(self, name):
        import os
        import sys
        import platform

        program_name = name
        if platform.system() == "Windows":
            program_name += ".exe"

        program_path = os.path.join(sys._MEIPASS, program_name)
        if not os.path.isfile(program_path):
            raise ValueError(f"Prog {name} not found in the PyInstaller-frozen application bundle!")

        return program_path

    pygraphviz.AGraph._which = _pygraphviz_override_which
