# 012370.python.hook-botocore.line1.comment ------------------------------------------------------------------
# 012371.python.hook-botocore.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012372.python.hook-botocore.line3.comment
# 012373.python.hook-botocore.line4.comment This file is distributed under the terms of the GNU General Public
# 012374.python.hook-botocore.line5.comment License (version 2.0 or later).
# 012375.python.hook-botocore.line6.comment
# 012376.python.hook-botocore.line7.comment The full license is available in LICENSE, distributed with
# 012377.python.hook-botocore.line8.comment this software.
# 012378.python.hook-botocore.line9.comment
# 012379.python.hook-botocore.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012380.python.hook-botocore.line11.comment ------------------------------------------------------------------
# 012381.python.hook-botocore.line12.comment
# 012382.python.hook-botocore.line13.comment Botocore is a low-level interface to a growing number of Amazon Web Services.
# 012383.python.hook-botocore.line14.comment Botocore serves as the foundation for the AWS-CLI command line utilities. It
# 012384.python.hook-botocore.line15.comment will also play an important role in the boto3.x project.
# 012385.python.hook-botocore.line16.comment
# 012386.python.hook-botocore.line17.comment The botocore package is compatible with Python versions 2.6.5, Python 2.7.x,
# 012387.python.hook-botocore.line18.comment and Python 3.3.x and higher.
# 012388.python.hook-botocore.line19.comment
# 012389.python.hook-botocore.line20.comment https://botocore.readthedocs.org/en/latest/
# 012390.python.hook-botocore.line21.comment
# 012391.python.hook-botocore.line22.comment Tested with botocore 1.4.36

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import is_module_satisfies

if is_module_satisfies('botocore >= 1.4.36'):
    hiddenimports = ['html.parser']

datas = collect_data_files('botocore')
