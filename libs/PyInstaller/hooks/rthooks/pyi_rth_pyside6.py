# 008542.python.pyi_rth_pyside6.line1.comment -----------------------------------------------------------------------------
# 008543.python.pyi_rth_pyside6.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 008544.python.pyi_rth_pyside6.line3.comment
# 008545.python.pyi_rth_pyside6.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008546.python.pyi_rth_pyside6.line5.comment you may not use this file except in compliance with the License.
# 008547.python.pyi_rth_pyside6.line6.comment
# 008548.python.pyi_rth_pyside6.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008549.python.pyi_rth_pyside6.line8.comment
# 008550.python.pyi_rth_pyside6.line9.comment SPDX-License-Identifier: Apache-2.0
# 008551.python.pyi_rth_pyside6.line10.comment -----------------------------------------------------------------------------

# 008552.python.pyi_rth_pyside6.line12.comment The path to Qt's components may not default to the wheel layout for self-compiled PySide6 installations. Mandate the
# 008553.python.pyi_rth_pyside6.line13.comment wheel layout. See ``utils/hooks/qt.py`` for more details.


def _pyi_rthook():
    import os
    import sys

    from _pyi_rth_utils import is_macos_app_bundle, prepend_path_to_environment_variable
    from _pyi_rth_utils import qt as qt_rth_utils

    # 008554.python.pyi_rth_pyside6.line23.comment Ensure this is the only Qt bindings package in the application.
    qt_rth_utils.ensure_single_qt_bindings_package("PySide6")

    if sys.platform.startswith('win'):
        pyqt_path = os.path.join(sys._MEIPASS, 'PySide6')
    else:
        pyqt_path = os.path.join(sys._MEIPASS, 'PySide6', 'Qt')

    os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt_path, 'plugins')

    if is_macos_app_bundle:
        # 008555.python.pyi_rth_pyside6.line34.comment Special handling for macOS .app bundles. To satisfy codesign requirements, we are forced to split `qml`
        # 008556.python.pyi_rth_pyside6.line35.comment directory into two parts; one that keeps only binaries (rooted in `Contents/Frameworks`) and one that keeps
        # 008557.python.pyi_rth_pyside6.line36.comment only data files (rooted in `Contents/Resources), with files from one directory tree being symlinked to the
        # 008558.python.pyi_rth_pyside6.line37.comment other to maintain illusion of a single mixed-content directory. As Qt seems to compute the identifier of its
        # 008559.python.pyi_rth_pyside6.line38.comment QML components based on location of the `qmldir` file w.r.t. the registered QML import paths, we need to
        # 008560.python.pyi_rth_pyside6.line39.comment register both paths, because the `qmldir` file for a component could be reached via either directory tree.
        pyqt_path_res = os.path.normpath(
            os.path.join(sys._MEIPASS, '..', 'Resources', os.path.relpath(pyqt_path, sys._MEIPASS))
        )
        os.environ['QML2_IMPORT_PATH'] = os.pathsep.join([
            os.path.join(pyqt_path_res, 'qml'),
            os.path.join(pyqt_path, 'qml'),
        ])
    else:
        os.environ['QML2_IMPORT_PATH'] = os.path.join(pyqt_path, 'qml')

    # 008561.python.pyi_rth_pyside6.line50.comment Add `sys._MEIPASS` to `PATH` in order to ensure that `QtNetwork` can discover OpenSSL DLLs that might have been
    # 008562.python.pyi_rth_pyside6.line51.comment collected there (i.e., when they were not shipped with the package, and were collected from an external location).
    if sys.platform.startswith('win'):
        prepend_path_to_environment_variable(sys._MEIPASS, 'PATH')

    # 008563.python.pyi_rth_pyside6.line55.comment For macOS POSIX builds, we need to add `sys._MEIPASS` to `DYLD_LIBRARY_PATH` so that QtNetwork can discover
    # 008564.python.pyi_rth_pyside6.line56.comment OpenSSL dynamic libraries for its `openssl` TLS backend. This also prevents fallback to external locations, such
    # 008565.python.pyi_rth_pyside6.line57.comment as Homebrew. For .app bundles, this is unnecessary because `QtNetwork` explicitly searches `Contents/Frameworks`.
    if sys.platform == 'darwin' and not is_macos_app_bundle:
        prepend_path_to_environment_variable(sys._MEIPASS, 'DYLD_LIBRARY_PATH')

    # 008566.python.pyi_rth_pyside6.line61.comment Qt bindings package installed via PyPI wheels typically ensures that its bundled Qt is relocatable, by creating
    # 008567.python.pyi_rth_pyside6.line62.comment embedded `qt.conf` file during its initialization. This run-time generated qt.conf dynamically sets the Qt prefix
    # 008568.python.pyi_rth_pyside6.line63.comment path to the package's Qt directory. For bindings packages that do not create embedded `qt.conf` during their
    # 008569.python.pyi_rth_pyside6.line64.comment initialization (for example, conda-installed packages), try to perform this step ourselves.
    qt_rth_utils.create_embedded_qt_conf("PySide6", pyqt_path)


_pyi_rthook()
del _pyi_rthook
