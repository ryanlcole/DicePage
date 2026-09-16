# 000163.python.shared_with_waf.line1.comment -----------------------------------------------------------------------------
# 000164.python.shared_with_waf.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 000165.python.shared_with_waf.line3.comment
# 000166.python.shared_with_waf.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000167.python.shared_with_waf.line5.comment or later) with exception for distributing the bootloader.
# 000168.python.shared_with_waf.line6.comment
# 000169.python.shared_with_waf.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000170.python.shared_with_waf.line8.comment
# 000171.python.shared_with_waf.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000172.python.shared_with_waf.line10.comment -----------------------------------------------------------------------------
"""
Code to be shared by PyInstaller and the bootloader/wscript file.

This code must not assume that either PyInstaller or any of its dependencies installed. I.e., the only imports allowed
in here are standard library ones. Within reason, it is preferable that this file should still run under Python 2.7 as
many compiler docker images still have only Python 2 installed.
"""

import platform
import re


def _pyi_machine(machine, system):
    # 000173.python.shared_with_waf.line24.comment type: (str, str) -> str
    """
    Choose an intentionally simplified architecture identifier to be used in the bootloader's directory name.

    Args:
        machine:
            The output of ``platform.machine()`` or any known architecture alias or shorthand that may be used by a
            C compiler.
        system:
            The output of ``platform.system()`` on the target machine.
    Returns:
        Either a string tag or, on platforms that don't need an architecture tag, ``None``.

    Ideally, we would just use ``platform.machine()`` directly, but that makes cross-compiling the bootloader almost
    impossible, because you need to know at compile time exactly what ``platform.machine()`` will be at run time, based
    only on the machine name alias or shorthand reported by the C compiler at the build time. Rather, use a loose
    differentiation, and trust that anyone mixing armv6l with armv6h knows what they are doing.
    """
    # 000174.python.shared_with_waf.line42.comment See the corresponding tests in tests/unit/test_compat.py for examples.

    if platform.machine() == "sw_64" or platform.machine() == "loongarch64":
        # 000175.python.shared_with_waf.line45.comment This explicitly inhibits cross compiling the bootloader for or on SunWay and LoongArch machine.
        return platform.machine()

    if system == "Windows":
        if machine.lower().startswith("arm"):
            return "arm"
        else:
            return "intel"

    if system == "SunOS":
        if machine.lower() in ("x86", "i86pc"):
            return "intel"
        else:
            return "sparc"

    if system != "Linux":
        # 000176.python.shared_with_waf.line61.comment No architecture specifier for anything par Linux.
        # 000177.python.shared_with_waf.line62.comment - macOS is on two 64 bit architectures, but they are merged into one "universal2" bootloader.
        # 000178.python.shared_with_waf.line63.comment - BSD supports a wide range of architectures, but according to PyPI's download statistics, every one of our
        # 000179.python.shared_with_waf.line64.comment BSD users are on x86_64. This may change in the distant future.
        return

    if machine.startswith(("arm", "aarch")):
        # 000180.python.shared_with_waf.line68.comment ARM has a huge number of similar and aliased sub-versions, such as armv5, armv6l armv8h, aarch64.
        return "arm"
    if machine in ("thumb"):
        # 000181.python.shared_with_waf.line71.comment Reported by waf/gcc when Thumb instruction set is enabled on 32-bit ARM. The platform.machine() returns "arm"
        # 000182.python.shared_with_waf.line72.comment regardless of the instruction set.
        return "arm"
    if machine in ("x86_64", "x64", "x86"):
        return "intel"
    if re.fullmatch("i[1-6]86", machine):
        return "intel"
    if machine.startswith(("ppc", "powerpc")):
        # 000183.python.shared_with_waf.line79.comment PowerPC comes in 64 vs 32 bit and little vs big endian variants.
        return "ppc"
    if machine in ("mips64", "mips"):
        return "mips"
    if machine.startswith("riscv"):
        return "riscv"
    # 000184.python.shared_with_waf.line85.comment Machines with no known aliases :)
    if machine in ("s390x",):
        return machine

    # 000185.python.shared_with_waf.line89.comment Unknown architectures are allowed by default, but will all be placed under one directory. In theory, trying to
    # 000186.python.shared_with_waf.line90.comment have multiple unknown architectures in one copy of PyInstaller will not work, but that should be sufficiently
    # 000187.python.shared_with_waf.line91.comment unlikely to ever happen.
    return "unknown"
