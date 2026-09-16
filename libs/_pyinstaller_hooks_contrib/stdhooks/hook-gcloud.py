# 013549.python.hook-gcloud.line1.comment ------------------------------------------------------------------
# 013550.python.hook-gcloud.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013551.python.hook-gcloud.line3.comment
# 013552.python.hook-gcloud.line4.comment This file is distributed under the terms of the GNU General Public
# 013553.python.hook-gcloud.line5.comment License (version 2.0 or later).
# 013554.python.hook-gcloud.line6.comment
# 013555.python.hook-gcloud.line7.comment The full license is available in LICENSE, distributed with
# 013556.python.hook-gcloud.line8.comment this software.
# 013557.python.hook-gcloud.line9.comment
# 013558.python.hook-gcloud.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013559.python.hook-gcloud.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata

# 013560.python.hook-gcloud.line15.comment This hook was written for `gcloud` - https://pypi.org/project/gcloud
# 013561.python.hook-gcloud.line16.comment Suppress package-not-found errors when the hook is triggered by `gcloud` namespace package from `gcloud-aio-*` and
# 013562.python.hook-gcloud.line17.comment `gcloud-rest-*` dists (https://github.com/talkiq/gcloud-aio).
try:
    datas = copy_metadata('gcloud')
except Exception:
    pass
