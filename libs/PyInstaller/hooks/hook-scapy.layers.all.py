# 006650.python.hook-scapy.layers.all.line1.comment -----------------------------------------------------------------------------
# 006651.python.hook-scapy.layers.all.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006652.python.hook-scapy.layers.all.line3.comment
# 006653.python.hook-scapy.layers.all.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006654.python.hook-scapy.layers.all.line5.comment or later) with exception for distributing the bootloader.
# 006655.python.hook-scapy.layers.all.line6.comment
# 006656.python.hook-scapy.layers.all.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006657.python.hook-scapy.layers.all.line8.comment
# 006658.python.hook-scapy.layers.all.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006659.python.hook-scapy.layers.all.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 006660.python.hook-scapy.layers.all.line14.comment The layers to load can be configured using scapy's conf.load_layers.
# 006661.python.hook-scapy.layers.all.line15.comment from scapy.config import conf; print(conf.load_layers)
# 006662.python.hook-scapy.layers.all.line16.comment I decided not to use this, but to include all layer modules. The reason is: When building the package, load_layers may
# 006663.python.hook-scapy.layers.all.line17.comment not include all the layer modules the program will use later.

hiddenimports = collect_submodules('scapy.layers')
