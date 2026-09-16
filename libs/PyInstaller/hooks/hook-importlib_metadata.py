# 006188.python.hook-importlib_metadata.line1.comment -----------------------------------------------------------------------------
# 006189.python.hook-importlib_metadata.line2.comment Copyright (c) 2019-2023, PyInstaller Development Team.
# 006190.python.hook-importlib_metadata.line3.comment
# 006191.python.hook-importlib_metadata.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006192.python.hook-importlib_metadata.line5.comment or later) with exception for distributing the bootloader.
# 006193.python.hook-importlib_metadata.line6.comment
# 006194.python.hook-importlib_metadata.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006195.python.hook-importlib_metadata.line8.comment
# 006196.python.hook-importlib_metadata.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006197.python.hook-importlib_metadata.line10.comment -----------------------------------------------------------------------------
"""
importlib_metadata is a library to access the metadata for a Python package. This functionality intends to replace most
uses of pkg_resources entry point API and metadata API.
"""

from PyInstaller.utils.hooks import copy_metadata

# 006198.python.hook-importlib_metadata.line18.comment Normally, we should never need to use copy_metadata() in a hook since metadata requirements detection is now
# 006199.python.hook-importlib_metadata.line19.comment automatic. However, that detection first uses `PyiModuleGraph.get_code_using("importlib_metadata")` to find
# 006200.python.hook-importlib_metadata.line20.comment files which `import importlib_metadata` and `get_code_using()` intentionally excludes internal imports. This
# 006201.python.hook-importlib_metadata.line21.comment means that importlib_metadata is not scanned for usages of importlib_metadata and therefore when
# 006202.python.hook-importlib_metadata.line22.comment importlib_metadata uses its own API to get its version, this goes undetected. Therefore, we must collect its
# 006203.python.hook-importlib_metadata.line23.comment metadata manually.
datas = copy_metadata('importlib_metadata')
