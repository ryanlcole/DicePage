# 012313.python.hook-bokeh.line1.comment ------------------------------------------------------------------
# 012314.python.hook-bokeh.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012315.python.hook-bokeh.line3.comment
# 012316.python.hook-bokeh.line4.comment This file is distributed under the terms of the GNU General Public
# 012317.python.hook-bokeh.line5.comment License (version 2.0 or later).
# 012318.python.hook-bokeh.line6.comment
# 012319.python.hook-bokeh.line7.comment The full license is available in LICENSE, distributed with
# 012320.python.hook-bokeh.line8.comment this software.
# 012321.python.hook-bokeh.line9.comment
# 012322.python.hook-bokeh.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012323.python.hook-bokeh.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, copy_metadata, is_module_satisfies

# 012324.python.hook-bokeh.line15.comment core/_templates/*
# 012325.python.hook-bokeh.line16.comment server/static/**/*
# 012326.python.hook-bokeh.line17.comment subcommands/*.py
# 012327.python.hook-bokeh.line18.comment bokeh/_sri.json

datas = collect_data_files('bokeh.core') + \
    collect_data_files('bokeh.server') + \
    collect_data_files('bokeh.command.subcommands', include_py_files=True) + \
    collect_data_files('bokeh')

# 012328.python.hook-bokeh.line25.comment bokeh >= 3.0.0 sets its __version__ from metadata
if is_module_satisfies('bokeh >= 3.0.0'):
    datas += copy_metadata('bokeh')
