# 011121.python.run_tests.line1.comment -----------------------------------------------------------------------------
# 011122.python.run_tests.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 011123.python.run_tests.line3.comment
# 011124.python.run_tests.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 011125.python.run_tests.line5.comment or later) with exception for distributing the bootloader.
# 011126.python.run_tests.line6.comment
# 011127.python.run_tests.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 011128.python.run_tests.line8.comment
# 011129.python.run_tests.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 011130.python.run_tests.line10.comment -----------------------------------------------------------------------------

import argparse
import sys

import pytest

from PyInstaller.compat import importlib_metadata


def paths_to_test(include_only=None):
    """
    If ``include_only`` is falsey, this functions returns paths from all entry points. Otherwise, this parameter
    must be a string or sequence of strings. In this case, this function will return *only* paths from entry points
    whose ``module_name`` begins with the provided string(s).
    """
    # 011131.python.run_tests.line26.comment Convert a string to a list.
    if isinstance(include_only, str):
        include_only = [include_only]

    # 011132.python.run_tests.line30.comment Walk through all entry points.
    test_path_list = []
    for entry_point in importlib_metadata.entry_points(group="pyinstaller40", name="tests"):
        # 011133.python.run_tests.line33.comment Implement ``include_only``.
        if (
            not include_only  # If falsey, include everything,
            # 011135.python.run_tests.line36.comment Otherwise, include only the specified modules.
            or any(entry_point.module.startswith(name) for name in include_only)
        ):
            test_path_list += list(entry_point.load()())
    return test_path_list


# 011136.python.run_tests.line43.comment Run pytest on all tests registered by the PyInstaller setuptools testing entry point. If provided,
# 011137.python.run_tests.line44.comment the ``include_only`` argument is passed to ``path_to_test``.
def run_pytest(*args, **kwargs):
    paths = paths_to_test(include_only=kwargs.pop("include_only", None))
    # 011138.python.run_tests.line47.comment Return an error code if no tests were discovered.
    if not paths:
        print("Error: no tests discovered.", file=sys.stderr)
        # 011139.python.run_tests.line50.comment This indicates no tests were discovered; see
        # 011140.python.run_tests.line51.comment https://docs.pytest.org/en/latest/usage.html#possible-exit-codes.
        return 5
    else:
        # 011141.python.run_tests.line54.comment See https://docs.pytest.org/en/latest/usage.html#calling-pytest-from-python-code.
        # 011142.python.run_tests.line55.comment Omit ``args[0]``, which is the name of this script.
        print("pytest " + " ".join([*paths, *args[1:]]))
        return pytest.main([*paths, *args[1:]], **kwargs)


if __name__ == "__main__":
    # 011143.python.run_tests.line61.comment Look only for the ``--include_only`` argument.
    parser = argparse.ArgumentParser(description='Run PyInstaller packaging tests.')
    parser.add_argument(
        "--include_only",
        action="append",
        help="Only run tests from the specified package.",
    )
    args, unknown = parser.parse_known_args(sys.argv)
    # 011144.python.run_tests.line69.comment Convert the parsed args into a dict using ``vars(args)``.
    sys.exit(run_pytest(*unknown, **vars(args)))
