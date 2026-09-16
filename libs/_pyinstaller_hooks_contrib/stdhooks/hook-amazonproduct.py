# 011963.python.hook-amazonproduct.line1.comment ------------------------------------------------------------------
# 011964.python.hook-amazonproduct.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011965.python.hook-amazonproduct.line3.comment
# 011966.python.hook-amazonproduct.line4.comment This file is distributed under the terms of the GNU General Public
# 011967.python.hook-amazonproduct.line5.comment License (version 2.0 or later).
# 011968.python.hook-amazonproduct.line6.comment
# 011969.python.hook-amazonproduct.line7.comment The full license is available in LICENSE, distributed with
# 011970.python.hook-amazonproduct.line8.comment this software.
# 011971.python.hook-amazonproduct.line9.comment
# 011972.python.hook-amazonproduct.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011973.python.hook-amazonproduct.line11.comment ------------------------------------------------------------------
"""
Hook for Python bindings for Amazon's Product Advertising API.
https://bitbucket.org/basti/python-amazon-product-api
"""

hiddenimports = ['amazonproduct.processors.__init__',
                 'amazonproduct.processors._lxml',
                 'amazonproduct.processors.objectify',
                 'amazonproduct.processors.elementtree',
                 'amazonproduct.processors.etree',
                 'amazonproduct.processors.minidom',
                 'amazonproduct.contrib.__init__',
                 'amazonproduct.contrib.cart',
                 'amazonproduct.contrib.caching',
                 'amazonproduct.contrib.retry']
