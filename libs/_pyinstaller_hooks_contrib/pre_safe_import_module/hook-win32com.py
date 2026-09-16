# 011465.python.hook-win32com.line1.comment -----------------------------------------------------------------------------
# 011466.python.hook-win32com.line2.comment Copyright (c) 2005-2020, PyInstaller Development Team.
# 011467.python.hook-win32com.line3.comment
# 011468.python.hook-win32com.line4.comment This file is distributed under the terms of the GNU General Public
# 011469.python.hook-win32com.line5.comment License (version 2.0 or later).
# 011470.python.hook-win32com.line6.comment
# 011471.python.hook-win32com.line7.comment The full license is available in LICENSE, distributed with
# 011472.python.hook-win32com.line8.comment this software.
# 011473.python.hook-win32com.line9.comment
# 011474.python.hook-win32com.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011475.python.hook-win32com.line11.comment -----------------------------------------------------------------------------
"""
PyWin32 package 'win32com' extends it's __path__ attribute with win32comext
directory and thus PyInstaller is not able to find modules in it. For example
module 'win32com.shell' is in reality 'win32comext.shell'.

>>> win32com.__path__
['win32com', 'C:\\Python27\\Lib\\site-packages\\win32comext']

"""

import os

from PyInstaller.utils.hooks import logger, exec_statement
from PyInstaller.compat import is_win, is_cygwin


def pre_safe_import_module(api):
    if not (is_win or is_cygwin):
        return
    win32com_file = exec_statement(
        """
        try:
            from win32com import __file__
            print(__file__)
        except Exception:
            pass
        """).strip()
    if not win32com_file:
        logger.debug('win32com: module not available')
        return  # win32com unavailable
    win32com_dir = os.path.dirname(win32com_file)
    comext_dir = os.path.join(os.path.dirname(win32com_dir), 'win32comext')
    logger.debug('win32com: extending __path__ with dir %r' % comext_dir)
    # 011477.python.hook-win32com.line45.comment Append the __path__ where PyInstaller will look for 'win32com' modules.'
    api.append_package_path(comext_dir)
