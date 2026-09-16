# 012350.python.hook-boto3.line1.comment ------------------------------------------------------------------
# 012351.python.hook-boto3.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012352.python.hook-boto3.line3.comment
# 012353.python.hook-boto3.line4.comment This file is distributed under the terms of the GNU General Public
# 012354.python.hook-boto3.line5.comment License (version 2.0 or later).
# 012355.python.hook-boto3.line6.comment
# 012356.python.hook-boto3.line7.comment The full license is available in LICENSE, distributed with
# 012357.python.hook-boto3.line8.comment this software.
# 012358.python.hook-boto3.line9.comment
# 012359.python.hook-boto3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012360.python.hook-boto3.line11.comment ------------------------------------------------------------------
# 012361.python.hook-boto3.line12.comment
# 012362.python.hook-boto3.line13.comment Boto is the Amazon Web Services (AWS) SDK for Python, which allows Python
# 012363.python.hook-boto3.line14.comment developers to write software that makes use of Amazon services like S3 and
# 012364.python.hook-boto3.line15.comment EC2. Boto provides an easy to use, object-oriented API as well as low-level
# 012365.python.hook-boto3.line16.comment direct service access.
# 012366.python.hook-boto3.line17.comment
# 012367.python.hook-boto3.line18.comment http://boto3.readthedocs.org/en/latest/
# 012368.python.hook-boto3.line19.comment
# 012369.python.hook-boto3.line20.comment Tested with boto3 1.2.1

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = (
    collect_submodules('boto3.dynamodb') +
    collect_submodules('boto3.ec2') +
    collect_submodules('boto3.s3')
)
datas = collect_data_files('boto3')
