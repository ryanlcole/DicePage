# 000083.python.init.line1.comment -----------------------------------------------------------------------------
# 000084.python.init.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 000085.python.init.line3.comment
# 000086.python.init.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000087.python.init.line5.comment or later) with exception for distributing the bootloader.
# 000088.python.init.line6.comment
# 000089.python.init.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000090.python.init.line8.comment
# 000091.python.init.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000092.python.init.line10.comment -----------------------------------------------------------------------------

__all__ = ('HOMEPATH', 'PLATFORM', '__version__', 'DEFAULT_DISTPATH', 'DEFAULT_SPECPATH', 'DEFAULT_WORKPATH')

import os

from PyInstaller import compat

# 000093.python.init.line18.comment Note: Keep this variable as plain string so it could be updated automatically when doing a release.
__version__ = '6.16.0'

# 000094.python.init.line21.comment Absolute path of this package's directory. Save this early so all submodules can use the absolute path. This is
# 000095.python.init.line22.comment required for example if the current directory changes prior to loading the hooks.
PACKAGEPATH = os.path.abspath(os.path.dirname(__file__))

HOMEPATH = os.path.dirname(PACKAGEPATH)

# 000096.python.init.line27.comment Default values of paths where to put files created by PyInstaller. If changing these, do not forget to update the
# 000097.python.init.line28.comment help text for corresponding command-line options, defined in build_main.

# 000098.python.init.line30.comment Where to put created .spec file.
DEFAULT_SPECPATH = os.getcwd()
# 000099.python.init.line32.comment Where to put the final frozen application.
DEFAULT_DISTPATH = os.path.join(os.getcwd(), 'dist')
# 000100.python.init.line34.comment Where to put all the temporary files; .log, .pyz, etc.
DEFAULT_WORKPATH = os.path.join(os.getcwd(), 'build')

PLATFORM = compat.system + '-' + compat.architecture
# 000101.python.init.line38.comment Include machine name in path to bootloader for some machines (e.g., 'arm'). Explicitly avoid doing this on macOS,
# 000102.python.init.line39.comment where we keep universal2 bootloaders in Darwin-64bit folder regardless of whether we are on x86_64 or arm64.
if compat.machine and not compat.is_darwin:
    PLATFORM += '-' + compat.machine
# 000103.python.init.line42.comment Similarly, disambiguate musl Linux from glibc Linux.
if compat.is_musl:
    PLATFORM += '-musl'
