# 008517.python.pyi_rth_pyside2.line1.comment -----------------------------------------------------------------------------
# 008518.python.pyi_rth_pyside2.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008519.python.pyi_rth_pyside2.line3.comment
# 008520.python.pyi_rth_pyside2.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008521.python.pyi_rth_pyside2.line5.comment you may not use this file except in compliance with the License.
# 008522.python.pyi_rth_pyside2.line6.comment
# 008523.python.pyi_rth_pyside2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008524.python.pyi_rth_pyside2.line8.comment
# 008525.python.pyi_rth_pyside2.line9.comment SPDX-License-Identifier: Apache-2.0
# 008526.python.pyi_rth_pyside2.line10.comment -----------------------------------------------------------------------------

# 008527.python.pyi_rth_pyside2.line12.comment The path to Qt's components may not default to the wheel layout for self-compiled PySide2 installations. Mandate the
# 008528.python.pyi_rth_pyside2.line13.comment wheel layout. See ``utils/hooks/qt.py`` for more details.


def _pyi_rthook():
    import os
    import sys

    from _pyi_rth_utils import is_macos_app_bundle, prepend_path_to_environment_variable
    from _pyi_rth_utils import qt as qt_rth_utils

    # 008529.python.pyi_rth_pyside2.line23.comment Ensure this is the only Qt bindings package in the application.
    qt_rth_utils.ensure_single_qt_bindings_package("PySide2")

    if sys.platform.startswith('win'):
        pyqt_path = os.path.join(sys._MEIPASS, 'PySide2')
    else:
        pyqt_path = os.path.join(sys._MEIPASS, 'PySide2', 'Qt')

    os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt_path, 'plugins')

    if is_macos_app_bundle:
        # 008530.python.pyi_rth_pyside2.line34.comment Special handling for macOS .app bundles. To satisfy codesign requirements, we are forced to split `qml`
        # 008531.python.pyi_rth_pyside2.line35.comment directory into two parts; one that keeps only binaries (rooted in `Contents/Frameworks`) and one that keeps
        # 008532.python.pyi_rth_pyside2.line36.comment only data files (rooted in `Contents/Resources), with files from one directory tree being symlinked to the
        # 008533.python.pyi_rth_pyside2.line37.comment other to maintain illusion of a single mixed-content directory. As Qt seems to compute the identifier of its
        # 008534.python.pyi_rth_pyside2.line38.comment QML components based on location of the `qmldir` file w.r.t. the registered QML import paths, we need to
        # 008535.python.pyi_rth_pyside2.line39.comment register both paths, because the `qmldir` file for a component could be reached via either directory tree.
        pyqt_path_res = os.path.normpath(
            os.path.join(sys._MEIPASS, '..', 'Resources', os.path.relpath(pyqt_path, sys._MEIPASS))
        )
        os.environ['QML2_IMPORT_PATH'] = os.pathsep.join([
            os.path.join(pyqt_path_res, 'qml'),
            os.path.join(pyqt_path, 'qml'),
        ])
    else:
        os.environ['QML2_IMPORT_PATH'] = os.path.join(pyqt_path, 'qml')

    # 008536.python.pyi_rth_pyside2.line50.comment Add `sys._MEIPASS` to `PATH` in order to ensure that `QtNetwork` can discover OpenSSL DLLs that might have been
    # 008537.python.pyi_rth_pyside2.line51.comment collected there (i.e., when they were not shipped with the package, and were collected from an external location).
    if sys.platform.startswith('win'):
        prepend_path_to_environment_variable(sys._MEIPASS, 'PATH')

    # 008538.python.pyi_rth_pyside2.line55.comment Qt bindings package installed via PyPI wheels typically ensures that its bundled Qt is relocatable, by creating
    # 008539.python.pyi_rth_pyside2.line56.comment embedded `qt.conf` file during its initialization. This run-time generated qt.conf dynamically sets the Qt prefix
    # 008540.python.pyi_rth_pyside2.line57.comment path to the package's Qt directory. For bindings packages that do not create embedded `qt.conf` during their
    # 008541.python.pyi_rth_pyside2.line58.comment initialization (for example, conda-installed packages), try to perform this step ourselves.
    qt_rth_utils.create_embedded_qt_conf("PySide2", pyqt_path)


_pyi_rthook()
del _pyi_rthook
