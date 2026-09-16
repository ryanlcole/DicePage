# 014121.python.hook-jsonschema.line1.comment ------------------------------------------------------------------
# 014122.python.hook-jsonschema.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014123.python.hook-jsonschema.line3.comment
# 014124.python.hook-jsonschema.line4.comment This file is distributed under the terms of the GNU General Public
# 014125.python.hook-jsonschema.line5.comment License (version 2.0 or later).
# 014126.python.hook-jsonschema.line6.comment
# 014127.python.hook-jsonschema.line7.comment The full license is available in LICENSE, distributed with
# 014128.python.hook-jsonschema.line8.comment this software.
# 014129.python.hook-jsonschema.line9.comment
# 014130.python.hook-jsonschema.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014131.python.hook-jsonschema.line11.comment ------------------------------------------------------------------

# 014132.python.hook-jsonschema.line13.comment This is needed to bundle draft3.json and draft4.json files that come with jsonschema module.
# 014133.python.hook-jsonschema.line14.comment NOTE: with jsonschema >= 4.18.0, the specification files are part of jsonschema_specifications package, and are
# 014134.python.hook-jsonschema.line15.comment handled by the corresponding hook-jsonschema.

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = collect_data_files('jsonschema')
datas += copy_metadata('jsonschema')
