# 012441.python.hook-cassandra.line1.comment ------------------------------------------------------------------
# 012442.python.hook-cassandra.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 012443.python.hook-cassandra.line3.comment
# 012444.python.hook-cassandra.line4.comment This file is distributed under the terms of the GNU General Public
# 012445.python.hook-cassandra.line5.comment License (version 2.0 or later).
# 012446.python.hook-cassandra.line6.comment
# 012447.python.hook-cassandra.line7.comment The full license is available in LICENSE, distributed with
# 012448.python.hook-cassandra.line8.comment this software.
# 012449.python.hook-cassandra.line9.comment
# 012450.python.hook-cassandra.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012451.python.hook-cassandra.line11.comment ------------------------------------------------------------------
# 012452.python.hook-cassandra.line12.comment
# 012453.python.hook-cassandra.line13.comment A modern, feature-rich and highly-tunable Python client library for Apache Cassandra (2.1+) and
# 012454.python.hook-cassandra.line14.comment DataStax Enterprise (4.7+) using exclusively Cassandra's binary protocol and Cassandra Query Language v3.
# 012455.python.hook-cassandra.line15.comment
# 012456.python.hook-cassandra.line16.comment http://datastax.github.io/python-driver/api/index.html
# 012457.python.hook-cassandra.line17.comment
# 012458.python.hook-cassandra.line18.comment Tested with cassandra-driver 3.25.0

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('cassandra')
