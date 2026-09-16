# 008487.python.pyi_rth_pyqt6.line1.comment -----------------------------------------------------------------------------
# 008488.python.pyi_rth_pyqt6.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 008489.python.pyi_rth_pyqt6.line3.comment
# 008490.python.pyi_rth_pyqt6.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008491.python.pyi_rth_pyqt6.line5.comment you may not use this file except in compliance with the License.
# 008492.python.pyi_rth_pyqt6.line6.comment
# 008493.python.pyi_rth_pyqt6.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008494.python.pyi_rth_pyqt6.line8.comment
# 008495.python.pyi_rth_pyqt6.line9.comment SPDX-License-Identifier: Apache-2.0
# 008496.python.pyi_rth_pyqt6.line10.comment -----------------------------------------------------------------------------

# 008497.python.pyi_rth_pyqt6.line12.comment The path to Qt's components may not default to the wheel layout for self-compiled PyQt6 installations. Mandate the
# 008498.python.pyi_rth_pyqt6.line13.comment wheel layout. See ``utils/hooks/qt.py`` for more details.


def _pyi_rthook():
    import os
    import sys

    from _pyi_rth_utils import is_macos_app_bundle, prepend_path_to_environment_variable
    from _pyi_rth_utils import qt as qt_rth_utils

    # 008499.python.pyi_rth_pyqt6.line23.comment Ensure this is the only Qt bindings package in the application.
    qt_rth_utils.ensure_single_qt_bindings_package("PyQt6")

    # 008500.python.pyi_rth_pyqt6.line26.comment Try PyQt6 6.0.3-style path first...
    pyqt_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6')
    if not os.path.isdir(pyqt_path):
        # 008501.python.pyi_rth_pyqt6.line29.comment ... and fall back to the older version.
        pyqt_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt')

    os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt_path, 'plugins')

    if is_macos_app_bundle:
        # 008502.python.pyi_rth_pyqt6.line35.comment Special handling for macOS .app bundles. To satisfy codesign requirements, we are forced to split `qml`
        # 008503.python.pyi_rth_pyqt6.line36.comment directory into two parts; one that keeps only binaries (rooted in `Contents/Frameworks`) and one that keeps
        # 008504.python.pyi_rth_pyqt6.line37.comment only data files (rooted in `Contents/Resources), with files from one directory tree being symlinked to the
        # 008505.python.pyi_rth_pyqt6.line38.comment other to maintain illusion of a single mixed-content directory. As Qt seems to compute the identifier of its
        # 008506.python.pyi_rth_pyqt6.line39.comment QML components based on location of the `qmldir` file w.r.t. the registered QML import paths, we need to
        # 008507.python.pyi_rth_pyqt6.line40.comment register both paths, because the `qmldir` file for a component could be reached via either directory tree.
        pyqt_path_res = os.path.normpath(
            os.path.join(sys._MEIPASS, '..', 'Resources', os.path.relpath(pyqt_path, sys._MEIPASS))
        )
        os.environ['QML2_IMPORT_PATH'] = os.pathsep.join([
            os.path.join(pyqt_path_res, 'qml'),
            os.path.join(pyqt_path, 'qml'),
        ])
    else:
        os.environ['QML2_IMPORT_PATH'] = os.path.join(pyqt_path, 'qml')

    # 008508.python.pyi_rth_pyqt6.line51.comment Add `sys._MEIPASS` to `PATH` in order to ensure that `QtNetwork` can discover OpenSSL DLLs that might have been
    # 008509.python.pyi_rth_pyqt6.line52.comment collected there (i.e., when they were not shipped with the package, and were collected from an external location).
    if sys.platform.startswith('win'):
        prepend_path_to_environment_variable(sys._MEIPASS, 'PATH')

    # 008510.python.pyi_rth_pyqt6.line56.comment For macOS POSIX builds, we need to add `sys._MEIPASS` to `DYLD_LIBRARY_PATH` so that QtNetwork can discover
    # 008511.python.pyi_rth_pyqt6.line57.comment OpenSSL dynamic libraries for its `openssl` TLS backend. This also prevents fallback to external locations, such
    # 008512.python.pyi_rth_pyqt6.line58.comment as Homebrew. For .app bundles, this is unnecessary because `QtNetwork` explicitly searches `Contents/Frameworks`.
    if sys.platform == 'darwin' and not is_macos_app_bundle:
        prepend_path_to_environment_variable(sys._MEIPASS, 'DYLD_LIBRARY_PATH')

    # 008513.python.pyi_rth_pyqt6.line62.comment Qt bindings package installed via PyPI wheels typically ensures that its bundled Qt is relocatable, by creating
    # 008514.python.pyi_rth_pyqt6.line63.comment embedded `qt.conf` file during its initialization. This run-time generated qt.conf dynamically sets the Qt prefix
    # 008515.python.pyi_rth_pyqt6.line64.comment path to the package's Qt directory. For bindings packages that do not create embedded `qt.conf` during their
    # 008516.python.pyi_rth_pyqt6.line65.comment initialization (for example, conda-installed packages), try to perform this step ourselves.
    qt_rth_utils.create_embedded_qt_conf("PyQt6", pyqt_path)


_pyi_rthook()
del _pyi_rthook
