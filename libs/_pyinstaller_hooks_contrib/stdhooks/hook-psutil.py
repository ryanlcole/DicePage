# 015417.python.hook-psutil.line1.comment ------------------------------------------------------------------
# 015418.python.hook-psutil.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015419.python.hook-psutil.line3.comment
# 015420.python.hook-psutil.line4.comment This file is distributed under the terms of the GNU General Public
# 015421.python.hook-psutil.line5.comment License (version 2.0 or later).
# 015422.python.hook-psutil.line6.comment
# 015423.python.hook-psutil.line7.comment The full license is available in LICENSE, distributed with
# 015424.python.hook-psutil.line8.comment this software.
# 015425.python.hook-psutil.line9.comment
# 015426.python.hook-psutil.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015427.python.hook-psutil.line11.comment ------------------------------------------------------------------
import os
import sys

# 015428.python.hook-psutil.line15.comment see https://github.com/giampaolo/psutil/blob/release-5.9.5/psutil/_common.py#L82
WINDOWS = os.name == "nt"
LINUX = sys.platform.startswith("linux")
MACOS = sys.platform.startswith("darwin")
FREEBSD = sys.platform.startswith(("freebsd", "midnightbsd"))
OPENBSD = sys.platform.startswith("openbsd")
NETBSD = sys.platform.startswith("netbsd")
BSD = FREEBSD or OPENBSD or NETBSD
SUNOS = sys.platform.startswith(("sunos", "solaris"))
AIX = sys.platform.startswith("aix")

excludedimports = [
    "psutil._pslinux",
    "psutil._pswindows",
    "psutil._psosx",
    "psutil._psbsd",
    "psutil._pssunos",
    "psutil._psaix",
]

# 015429.python.hook-psutil.line35.comment see https://github.com/giampaolo/psutil/blob/release-5.9.5/psutil/__init__.py#L97
if LINUX:
    excludedimports.remove("psutil._pslinux")
elif WINDOWS:
    excludedimports.remove("psutil._pswindows")
    # 015430.python.hook-psutil.line40.comment see https://github.com/giampaolo/psutil/blob/release-5.9.5/psutil/_common.py#L856
    # 015431.python.hook-psutil.line41.comment This will exclude `curses` for windows
    excludedimports.append("curses")
elif MACOS:
    excludedimports.remove("psutil._psosx")
elif BSD:
    excludedimports.remove("psutil._psbsd")
elif SUNOS:
    excludedimports.remove("psutil._pssunos")
elif AIX:
    excludedimports.remove("psutil._psaix")
