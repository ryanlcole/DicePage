# 008456.python.pyi_rth_pyqt5.line1.comment -----------------------------------------------------------------------------
# 008457.python.pyi_rth_pyqt5.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 008458.python.pyi_rth_pyqt5.line3.comment
# 008459.python.pyi_rth_pyqt5.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008460.python.pyi_rth_pyqt5.line5.comment you may not use this file except in compliance with the License.
# 008461.python.pyi_rth_pyqt5.line6.comment
# 008462.python.pyi_rth_pyqt5.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008463.python.pyi_rth_pyqt5.line8.comment
# 008464.python.pyi_rth_pyqt5.line9.comment SPDX-License-Identifier: Apache-2.0
# 008465.python.pyi_rth_pyqt5.line10.comment -----------------------------------------------------------------------------

# 008466.python.pyi_rth_pyqt5.line12.comment The path to Qt's components may not default to the wheel layout for self-compiled PyQt5 installations. Mandate the
# 008467.python.pyi_rth_pyqt5.line13.comment wheel layout. See ``utils/hooks/qt.py`` for more details.


def _pyi_rthook():
    import os
    import sys

    from _pyi_rth_utils import is_macos_app_bundle, prepend_path_to_environment_variable
    from _pyi_rth_utils import qt as qt_rth_utils

    # 008468.python.pyi_rth_pyqt5.line23.comment Ensure this is the only Qt bindings package in the application.
    qt_rth_utils.ensure_single_qt_bindings_package("PyQt5")

    # 008469.python.pyi_rth_pyqt5.line26.comment Try PyQt5 5.15.4-style path first...
    pyqt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt5')
    if not os.path.isdir(pyqt_path):
        # 008470.python.pyi_rth_pyqt5.line29.comment ... and fall back to the older version
        pyqt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')

    os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt_path, 'plugins')

    if is_macos_app_bundle:
        # 008471.python.pyi_rth_pyqt5.line35.comment Special handling for macOS .app bundles. To satisfy codesign requirements, we are forced to split `qml`
        # 008472.python.pyi_rth_pyqt5.line36.comment directory into two parts; one that keeps only binaries (rooted in `Contents/Frameworks`) and one that keeps
        # 008473.python.pyi_rth_pyqt5.line37.comment only data files (rooted in `Contents/Resources), with files from one directory tree being symlinked to the
        # 008474.python.pyi_rth_pyqt5.line38.comment other to maintain illusion of a single mixed-content directory. As Qt seems to compute the identifier of its
        # 008475.python.pyi_rth_pyqt5.line39.comment QML components based on location of the `qmldir` file w.r.t. the registered QML import paths, we need to
        # 008476.python.pyi_rth_pyqt5.line40.comment register both paths, because the `qmldir` file for a component could be reached via either directory tree.
        pyqt_path_res = os.path.normpath(
            os.path.join(sys._MEIPASS, '..', 'Resources', os.path.relpath(pyqt_path, sys._MEIPASS))
        )
        os.environ['QML2_IMPORT_PATH'] = os.pathsep.join([
            os.path.join(pyqt_path_res, 'qml'),
            os.path.join(pyqt_path, 'qml'),
        ])
    else:
        os.environ['QML2_IMPORT_PATH'] = os.path.join(pyqt_path, 'qml')

    # 008477.python.pyi_rth_pyqt5.line51.comment Back in the day, this was required because PyQt5 5.12.3 explicitly checked that `Qt5Core.dll` was in `PATH`
    # 008478.python.pyi_rth_pyqt5.line52.comment (see #4293), and contemporary PyInstaller versions collected that DLL to `sys._MEIPASS`.
    # 008479.python.pyi_rth_pyqt5.line53.comment
    # 008480.python.pyi_rth_pyqt5.line54.comment Nowadays, we add `sys._MEIPASS` to `PATH` in order to ensure that `QtNetwork` can discover OpenSSL DLLs that might
    # 008481.python.pyi_rth_pyqt5.line55.comment have been collected there (i.e., when they were not shipped with the package, and were collected from an external
    # 008482.python.pyi_rth_pyqt5.line56.comment location).
    if sys.platform.startswith('win'):
        prepend_path_to_environment_variable(sys._MEIPASS, 'PATH')

    # 008483.python.pyi_rth_pyqt5.line60.comment Qt bindings package installed via PyPI wheels typically ensures that its bundled Qt is relocatable, by creating
    # 008484.python.pyi_rth_pyqt5.line61.comment embedded `qt.conf` file during its initialization. This run-time generated qt.conf dynamically sets the Qt prefix
    # 008485.python.pyi_rth_pyqt5.line62.comment path to the package's Qt directory. For bindings packages that do not create embedded `qt.conf` during their
    # 008486.python.pyi_rth_pyqt5.line63.comment initialization (for example, conda-installed packages), try to perform this step ourselves.
    qt_rth_utils.create_embedded_qt_conf("PyQt5", pyqt_path)


_pyi_rthook()
del _pyi_rthook
