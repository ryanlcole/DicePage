# 009630.python.set_version.line1.comment -----------------------------------------------------------------------------
# 009631.python.set_version.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 009632.python.set_version.line3.comment
# 009633.python.set_version.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 009634.python.set_version.line5.comment or later) with exception for distributing the bootloader.
# 009635.python.set_version.line6.comment
# 009636.python.set_version.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009637.python.set_version.line8.comment
# 009638.python.set_version.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 009639.python.set_version.line10.comment -----------------------------------------------------------------------------

import argparse
import os

try:
    from argcomplete import autocomplete
except ImportError:

    def autocomplete(parser):
        return None


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'info_file',
        metavar='info-file',
        help="text file containing version info",
    )
    parser.add_argument(
        'exe_file',
        metavar='exe-file',
        help="full pathname of a Windows executable",
    )
    autocomplete(parser)
    args = parser.parse_args()

    info_file = os.path.abspath(args.info_file)
    exe_file = os.path.abspath(args.exe_file)

    try:
        from PyInstaller.utils.win32 import versioninfo
        info = versioninfo.load_version_info_from_text_file(info_file)
        versioninfo.write_version_info_to_executable(exe_file, info)
        print(f"Version info written to: {exe_file!r}")
    except KeyboardInterrupt:
        raise SystemExit("Aborted by user request.")


if __name__ == '__main__':
    run()
