# 012329.python.hook-boto.line1.comment ------------------------------------------------------------------
# 012330.python.hook-boto.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012331.python.hook-boto.line3.comment
# 012332.python.hook-boto.line4.comment This file is distributed under the terms of the GNU General Public
# 012333.python.hook-boto.line5.comment License (version 2.0 or later).
# 012334.python.hook-boto.line6.comment
# 012335.python.hook-boto.line7.comment The full license is available in LICENSE, distributed with
# 012336.python.hook-boto.line8.comment this software.
# 012337.python.hook-boto.line9.comment
# 012338.python.hook-boto.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012339.python.hook-boto.line11.comment ------------------------------------------------------------------
# 012340.python.hook-boto.line12.comment
# 012341.python.hook-boto.line13.comment Boto3, the next version of Boto, is now stable and recommended for general
# 012342.python.hook-boto.line14.comment use.
# 012343.python.hook-boto.line15.comment
# 012344.python.hook-boto.line16.comment Boto is an integrated interface to current and future infrastructural
# 012345.python.hook-boto.line17.comment services offered by Amazon Web Services.
# 012346.python.hook-boto.line18.comment
# 012347.python.hook-boto.line19.comment http://boto.readthedocs.org/en/latest/
# 012348.python.hook-boto.line20.comment
# 012349.python.hook-boto.line21.comment Tested with boto 2.38.0

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('boto')
