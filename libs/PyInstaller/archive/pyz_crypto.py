# 000188.python.pyz_crypto.line1.comment -----------------------------------------------------------------------------
# 000189.python.pyz_crypto.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 000190.python.pyz_crypto.line3.comment
# 000191.python.pyz_crypto.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000192.python.pyz_crypto.line5.comment or later) with exception for distributing the bootloader.
# 000193.python.pyz_crypto.line6.comment
# 000194.python.pyz_crypto.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000195.python.pyz_crypto.line8.comment
# 000196.python.pyz_crypto.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000197.python.pyz_crypto.line10.comment -----------------------------------------------------------------------------


class PyiBlockCipher:
    def __init__(self, key=None):
        from PyInstaller.exceptions import RemovedCipherFeatureError
        raise RemovedCipherFeatureError("Please remove cipher and block_cipher parameters from your spec file.")
