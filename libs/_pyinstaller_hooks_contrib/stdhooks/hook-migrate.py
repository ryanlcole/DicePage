# 014563.python.hook-migrate.line1.comment ------------------------------------------------------------------
# 014564.python.hook-migrate.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014565.python.hook-migrate.line3.comment
# 014566.python.hook-migrate.line4.comment This file is distributed under the terms of the GNU General Public
# 014567.python.hook-migrate.line5.comment License (version 2.0 or later).
# 014568.python.hook-migrate.line6.comment
# 014569.python.hook-migrate.line7.comment The full license is available in LICENSE, distributed with
# 014570.python.hook-migrate.line8.comment this software.
# 014571.python.hook-migrate.line9.comment
# 014572.python.hook-migrate.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014573.python.hook-migrate.line11.comment ------------------------------------------------------------------
# 014574.python.hook-migrate.line12.comment hook for https://github.com/openstack/sqlalchemy-migrate
# 014575.python.hook-migrate.line13.comment Since v0.12.0 importing migrate requires metadata to resolve __version__
# 014576.python.hook-migrate.line14.comment attribute

from PyInstaller.utils.hooks import copy_metadata, is_module_satisfies

if is_module_satisfies('sqlalchemy-migrate >= 0.12.0'):
    datas = copy_metadata('sqlalchemy-migrate')
