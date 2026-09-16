# 012983.python.hook-distributed.line1.comment -----------------------------------------------------------------------------
# 012984.python.hook-distributed.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 012985.python.hook-distributed.line3.comment
# 012986.python.hook-distributed.line4.comment This file is distributed under the terms of the GNU General Public
# 012987.python.hook-distributed.line5.comment License (version 2.0 or later).
# 012988.python.hook-distributed.line6.comment
# 012989.python.hook-distributed.line7.comment The full license is available in LICENSE, distributed with
# 012990.python.hook-distributed.line8.comment this software.
# 012991.python.hook-distributed.line9.comment
# 012992.python.hook-distributed.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012993.python.hook-distributed.line11.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 012994.python.hook-distributed.line15.comment Collect submodules of distributed.http, many of which are imported indirectly.
hiddenimports = collect_submodules("distributed.http")

# 012995.python.hook-distributed.line18.comment Collect data files (distributed.yaml, distributed-schema.yaml, templates).
datas = collect_data_files("distributed")

# 012996.python.hook-distributed.line21.comment `distributed.dashboard.components.scheduler` attempts to refer to data files relative to its parent directory, but
# 012997.python.hook-distributed.line22.comment with non-normalized '..' elements in the path (e.g., `_MEIPASS/distributed/dashboard/components/../theme.yaml`). On
# 012998.python.hook-distributed.line23.comment POSIX systems, such paths are treated as non-existent if a component does not exist, even if the file exists at the
# 012999.python.hook-distributed.line24.comment normalized location (i.e., if `_MEIPASS/distributed/dashboard/theme.yaml` file exists but
# 013000.python.hook-distributed.line25.comment `_MEIPASS/distributed/dashboard/components` directory does not). As a work around, collect source .py files from
# 013001.python.hook-distributed.line26.comment `distributed.dashboard.components` to ensure existence of the `components` directory.
module_collection_mode = {
    'distributed.dashboard.components': 'pyz+py',
}
