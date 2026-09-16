# 016591.python.hook-saml2.line1.comment ------------------------------------------------------------------
# 016592.python.hook-saml2.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 016593.python.hook-saml2.line3.comment
# 016594.python.hook-saml2.line4.comment This file is distributed under the terms of the GNU General Public
# 016595.python.hook-saml2.line5.comment License (version 2.0 or later).
# 016596.python.hook-saml2.line6.comment
# 016597.python.hook-saml2.line7.comment The full license is available in LICENSE, distributed with
# 016598.python.hook-saml2.line8.comment this software.
# 016599.python.hook-saml2.line9.comment
# 016600.python.hook-saml2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016601.python.hook-saml2.line11.comment ------------------------------------------------------------------

# 016602.python.hook-saml2.line13.comment Hook for https://github.com/IdentityPython/pysaml2
from PyInstaller.utils.hooks import collect_data_files, copy_metadata, collect_submodules

datas = copy_metadata("pysaml2")

# 016603.python.hook-saml2.line18.comment The library contains a bunch of XSD schemas that are loaded by the code:
# 016604.python.hook-saml2.line19.comment https://github.com/IdentityPython/pysaml2/blob/7cb4f09dce87a7e8098b9c7552ebab8bc77bc896/src/saml2/xml/schema/__init__.py#L23
# 016605.python.hook-saml2.line20.comment On the other hand, runtime tools are not needed.
datas += collect_data_files("saml2", excludes=["**/tools"])

# 016606.python.hook-saml2.line23.comment Submodules are loaded dynamically by:
# 016607.python.hook-saml2.line24.comment https://github.com/IdentityPython/pysaml2/blob/7cb4f09dce87a7e8098b9c7552ebab8bc77bc896/src/saml2/attribute_converter.py#L52
hiddenimports = collect_submodules("saml2.attributemaps")
