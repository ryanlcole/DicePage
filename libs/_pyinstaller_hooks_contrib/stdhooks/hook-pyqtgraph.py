# 016177.python.hook-pyqtgraph.line1.comment ------------------------------------------------------------------
# 016178.python.hook-pyqtgraph.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016179.python.hook-pyqtgraph.line3.comment
# 016180.python.hook-pyqtgraph.line4.comment This file is distributed under the terms of the GNU General Public
# 016181.python.hook-pyqtgraph.line5.comment License (version 2.0 or later).
# 016182.python.hook-pyqtgraph.line6.comment
# 016183.python.hook-pyqtgraph.line7.comment The full license is available in LICENSE, distributed with
# 016184.python.hook-pyqtgraph.line8.comment this software.
# 016185.python.hook-pyqtgraph.line9.comment
# 016186.python.hook-pyqtgraph.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016187.python.hook-pyqtgraph.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 016188.python.hook-pyqtgraph.line15.comment Collect all data files, excluding the examples' data
datas = collect_data_files('pyqtgraph', excludes=['**/examples/*'])

# 016189.python.hook-pyqtgraph.line18.comment pyqtgraph uses Qt-version-specific templates for the UI elements.
# 016190.python.hook-pyqtgraph.line19.comment There are templates for different versions of PySide and PyQt, e.g.
# 016191.python.hook-pyqtgraph.line20.comment
# 016192.python.hook-pyqtgraph.line21.comment - pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt5
# 016193.python.hook-pyqtgraph.line22.comment - pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt6
# 016194.python.hook-pyqtgraph.line23.comment - pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyside2
# 016195.python.hook-pyqtgraph.line24.comment - pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyside6
# 016196.python.hook-pyqtgraph.line25.comment - pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt5
# 016197.python.hook-pyqtgraph.line26.comment - pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt6
# 016198.python.hook-pyqtgraph.line27.comment - pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyside2
# 016199.python.hook-pyqtgraph.line28.comment - pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyside6
# 016200.python.hook-pyqtgraph.line29.comment
# 016201.python.hook-pyqtgraph.line30.comment To be future-proof, we collect all modules by
# 016202.python.hook-pyqtgraph.line31.comment using collect-submodules, and filtering the modules
# 016203.python.hook-pyqtgraph.line32.comment which appear to be templates.
# 016204.python.hook-pyqtgraph.line33.comment We need to avoid recursing into `pyqtgraph.examples`, because that
# 016205.python.hook-pyqtgraph.line34.comment triggers instantiation of `QApplication` (which requires X/Wayland
# 016206.python.hook-pyqtgraph.line35.comment session on linux).
# 016207.python.hook-pyqtgraph.line36.comment Tested with pyqtgraph master branch (commit c1900aa).
all_imports = collect_submodules("pyqtgraph", filter=lambda name: name != "pyqtgraph.examples")
hiddenimports = [name for name in all_imports if "Template" in name]

# 016208.python.hook-pyqtgraph.line40.comment Collect the pyqtgraph/multiprocess/bootstrap.py as a module; this is required by our pyqtgraph.multiprocess runtime
# 016209.python.hook-pyqtgraph.line41.comment hook to handle the pyqtgraph's multiprocessing implementation. The pyqtgraph.multiprocess seems to be imported
# 016210.python.hook-pyqtgraph.line42.comment automatically on the import of pyqtgraph itself, so there is no point in creating a separate hook for this.
hiddenimports += ['pyqtgraph.multiprocess.bootstrap']

# 016211.python.hook-pyqtgraph.line45.comment Attempt to auto-select applicable Qt bindings and exclude extraneous Qt bindings.
# 016212.python.hook-pyqtgraph.line46.comment Available in PyInstaller >= 6.5, which has `PyInstaller.utils.hooks.qt.exclude_extraneous_qt_bindings` helper.
try:
    from PyInstaller.utils.hooks.qt import exclude_extraneous_qt_bindings
except ImportError:
    pass
else:
    # 016213.python.hook-pyqtgraph.line52.comment Use the helper's default preference order, to keep it consistent across multiple hooks that use the same helper.
    excludedimports = exclude_extraneous_qt_bindings(
        hook_name="hook-pyqtgraph",
        qt_bindings_order=None,
    )
