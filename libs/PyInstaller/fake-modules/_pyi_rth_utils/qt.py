# 002900.python.qt.line1.comment -----------------------------------------------------------------------------
# 002901.python.qt.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 002902.python.qt.line3.comment
# 002903.python.qt.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 002904.python.qt.line5.comment you may not use this file except in compliance with the License.
# 002905.python.qt.line6.comment
# 002906.python.qt.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002907.python.qt.line8.comment
# 002908.python.qt.line9.comment SPDX-License-Identifier: Apache-2.0
# 002909.python.qt.line10.comment -----------------------------------------------------------------------------

import os
import importlib
import atexit

# 002910.python.qt.line16.comment Helper for ensuring that only one Qt bindings package is registered at run-time via run-time hooks.
_registered_qt_bindings = None


def ensure_single_qt_bindings_package(qt_bindings):
    global _registered_qt_bindings
    if _registered_qt_bindings is not None:
        raise RuntimeError(
            f"Cannot execute run-time hook for {qt_bindings!r} because run-time hook for {_registered_qt_bindings!r} "
            "has been run before, and PyInstaller-frozen applications do not support multiple Qt bindings in the same "
            "application!"
        )
    _registered_qt_bindings = qt_bindings


# 002911.python.qt.line31.comment Helper for relocating Qt prefix via embedded qt.conf file.
_QT_CONF_FILENAME = ":/qt/etc/qt.conf"

_QT_CONF_RESOURCE_NAME = (
    # 002912.python.qt.line35.comment qt
    b"\x00\x02"
    b"\x00\x00\x07\x84"
    b"\x00\x71"
    b"\x00\x74"
    # 002913.python.qt.line40.comment etc
    b"\x00\x03"
    b"\x00\x00\x6c\xa3"
    b"\x00\x65"
    b"\x00\x74\x00\x63"
    # 002914.python.qt.line45.comment qt.conf
    b"\x00\x07"
    b"\x08\x74\xa6\xa6"
    b"\x00\x71"
    b"\x00\x74\x00\x2e\x00\x63\x00\x6f\x00\x6e\x00\x66"
)

_QT_CONF_RESOURCE_STRUCT = (
    # 002915.python.qt.line53.comment :
    b"\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01"
    # 002916.python.qt.line55.comment :/qt
    b"\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02"
    # 002917.python.qt.line57.comment :/qt/etc
    b"\x00\x00\x00\x0a\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03"
    # 002918.python.qt.line59.comment :/qt/etc/qt.conf
    b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00"
)


def create_embedded_qt_conf(qt_bindings, prefix_path):
    # 002919.python.qt.line65.comment The QtCore module might be unavailable if we collected just the top-level binding package (e.g., PyQt5) without
    # 002920.python.qt.line66.comment any of its submodules. Since this helper is called from run-time hook for the binding package, we need to handle
    # 002921.python.qt.line67.comment that scenario here.
    try:
        QtCore = importlib.import_module(qt_bindings + ".QtCore")
    except ImportError:
        return

    # 002922.python.qt.line73.comment No-op if embedded qt.conf already exists
    if QtCore.QFile.exists(_QT_CONF_FILENAME):
        return

    # 002923.python.qt.line77.comment Create qt.conf file that relocates Qt prefix.
    # 002924.python.qt.line78.comment NOTE: paths should use POSIX-style forward slashes as separator, even on Windows.
    if os.sep == '\\':
        prefix_path = prefix_path.replace(os.sep, '/')

    qt_conf = f"[Paths]\nPrefix = {prefix_path}\n"
    if os.name == 'nt' and qt_bindings in {"PySide2", "PySide6"}:
        # 002925.python.qt.line84.comment PySide PyPI wheels on Windows set LibraryExecutablesPath to PrefixPath
        qt_conf += f"LibraryExecutables = {prefix_path}"

    # 002926.python.qt.line87.comment Encode the contents; in Qt5, QSettings uses Latin1 encoding, in Qt6, it uses UTF8.
    if qt_bindings in {"PySide2", "PyQt5"}:
        qt_conf = qt_conf.encode("latin1")
    else:
        qt_conf = qt_conf.encode("utf-8")

    # 002927.python.qt.line93.comment Prepend data size (32-bit integer, big endian)
    qt_conf_size = len(qt_conf)
    qt_resource_data = qt_conf_size.to_bytes(4, 'big') + qt_conf

    # 002928.python.qt.line97.comment Register
    succeeded = QtCore.qRegisterResourceData(
        0x01,
        _QT_CONF_RESOURCE_STRUCT,
        _QT_CONF_RESOURCE_NAME,
        qt_resource_data,
    )
    if not succeeded:
        return  # Tough luck

    # 002930.python.qt.line107.comment Unregister the resource at exit, to ensure that the registered resource on Qt/C++ side does not outlive the
    # 002931.python.qt.line108.comment `_qt_resource_data` python variable and its data buffer. This also adds a reference to the `_qt_resource_data`,
    # 002932.python.qt.line109.comment which conveniently ensures that the data is not garbage collected before we perform the cleanup (otherwise garbage
    # 002933.python.qt.line110.comment collector might kick in at any time after we exit this helper function, and `qRegisterResourceData` does not seem
    # 002934.python.qt.line111.comment to make a copy of the data!).
    atexit.register(
        QtCore.qUnregisterResourceData,
        0x01,
        _QT_CONF_RESOURCE_STRUCT,
        _QT_CONF_RESOURCE_NAME,
        qt_resource_data,
    )
