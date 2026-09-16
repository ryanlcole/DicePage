# 009609.python.grab_version.line1.comment -----------------------------------------------------------------------------
# 009610.python.grab_version.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 009611.python.grab_version.line3.comment
# 009612.python.grab_version.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 009613.python.grab_version.line5.comment or later) with exception for distributing the bootloader.
# 009614.python.grab_version.line6.comment
# 009615.python.grab_version.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009616.python.grab_version.line8.comment
# 009617.python.grab_version.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 009618.python.grab_version.line10.comment -----------------------------------------------------------------------------

import argparse
import codecs

try:
    from argcomplete import autocomplete
except ImportError:

    def autocomplete(parser):
        return None


def run():
    parser = argparse.ArgumentParser(
        epilog=(
            'The printed output may be saved to a file, edited and used as the input for a version resource on any of '
            'the executable targets in a PyInstaller .spec file.'
        )
    )
    parser.add_argument(
        'exe_file',
        metavar='exe-file',
        help="full pathname of a Windows executable",
    )
    parser.add_argument(
        'out_filename',
        metavar='out-filename',
        nargs='?',
        default='file_version_info.txt',
        help="filename where the grabbed version info will be saved",
    )

    autocomplete(parser)
    args = parser.parse_args()

    try:
        from PyInstaller.utils.win32 import versioninfo
        info = versioninfo.read_version_info_from_executable(args.exe_file)
        if not info:
            raise SystemExit("ERROR: VersionInfo resource not found in exe")
        with codecs.open(args.out_filename, 'w', 'utf-8') as fp:
            fp.write(str(info))
        print(f"Version info written to: {args.out_filename!r}")
    except KeyboardInterrupt:
        raise SystemExit("Aborted by user request.")


if __name__ == '__main__':
    run()
