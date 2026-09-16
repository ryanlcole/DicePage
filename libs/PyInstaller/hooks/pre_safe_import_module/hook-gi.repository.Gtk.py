# 007733.python.hook-gi.repository.Gtk.line1.comment -----------------------------------------------------------------------------
# 007734.python.hook-gi.repository.Gtk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007735.python.hook-gi.repository.Gtk.line3.comment
# 007736.python.hook-gi.repository.Gtk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007737.python.hook-gi.repository.Gtk.line5.comment or later) with exception for distributing the bootloader.
# 007738.python.hook-gi.repository.Gtk.line6.comment
# 007739.python.hook-gi.repository.Gtk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007740.python.hook-gi.repository.Gtk.line8.comment
# 007741.python.hook-gi.repository.Gtk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007742.python.hook-gi.repository.Gtk.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007743.python.hook-gi.repository.Gtk.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007744.python.hook-gi.repository.Gtk.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
