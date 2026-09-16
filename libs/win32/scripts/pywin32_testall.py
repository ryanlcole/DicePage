"""A test runner for pywin32"""

import os
import site
import subprocess
import sys

# 048092.python.pywin32_testall.line8.comment locate the dirs based on where this script is - it may be either in the
# 048093.python.pywin32_testall.line9.comment source tree, or in an installed Python 'Scripts' tree.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
site_packages = [site.getusersitepackages()] + site.getsitepackages()

failures = []


# 048094.python.pywin32_testall.line16.comment Run a test using subprocess and wait for the result.
# 048095.python.pywin32_testall.line17.comment If we get an returncode != 0, we know that there was an error, but we don't
# 048096.python.pywin32_testall.line18.comment abort immediately - we run as many tests as we can.
def run_test(script, cmdline_extras):
    dirname, scriptname = os.path.split(script)
    # 048097.python.pywin32_testall.line21.comment some tests prefer to be run from their directory.
    cmd = [sys.executable, "-u", scriptname] + cmdline_extras
    print("--- Running '%s' ---" % script)
    sys.stdout.flush()
    result = subprocess.run(cmd, check=False, cwd=dirname)
    print(f"*** Test script '{script}' exited with {result.returncode}")
    sys.stdout.flush()
    if result.returncode:
        failures.append(script)


def find_and_run(possible_locations, extras):
    for maybe in possible_locations:
        if os.path.isfile(maybe):
            run_test(maybe, extras)
            break
    else:
        raise RuntimeError(
            "Failed to locate a test script in one of %s" % possible_locations
        )


def main():
    import argparse

    code_directories = [project_root] + site_packages

    parser = argparse.ArgumentParser(
        description="A script to trigger tests in all subprojects of PyWin32."
    )
    parser.add_argument(
        "-no-user-interaction",
        default=False,
        action="store_true",
        help="(This is now the default - use `-user-interaction` to include them)",
    )

    parser.add_argument(
        "-user-interaction",
        action="store_true",
        help="Include tests which require user interaction",
    )

    parser.add_argument(
        "-skip-adodbapi",
        default=False,
        action="store_true",
        help="Skip the adodbapi tests; useful for CI where there's no provider",
    )

    args, remains = parser.parse_known_args()

    # 048098.python.pywin32_testall.line73.comment win32, win32ui / Pythonwin

    extras = []
    if args.user_interaction:
        extras.append("-user-interaction")
    extras.extend(remains)
    scripts = [
        "win32/test/testall.py",
        "Pythonwin/pywin/test/all.py",
    ]
    for script in scripts:
        maybes = [os.path.join(directory, script) for directory in code_directories]
        find_and_run(maybes, extras)

    # 048099.python.pywin32_testall.line87.comment win32com
    maybes = [
        os.path.join(directory, "win32com", "test", "testall.py")
        for directory in [os.path.join(project_root, "com")] + site_packages
    ]
    extras = remains + ["1"]  # only run "level 1" tests in CI
    find_and_run(maybes, extras)

    # 048101.python.pywin32_testall.line95.comment adodbapi
    if not args.skip_adodbapi:
        maybes = [
            os.path.join(directory, "adodbapi", "test", "adodbapitest.py")
            for directory in code_directories
        ]
        find_and_run(maybes, remains)
        # 048102.python.pywin32_testall.line102.comment This script has a hard-coded sql server name in it, (and markh typically
        # 048103.python.pywin32_testall.line103.comment doesn't have a different server to test on) but there is now supposed to be a server out there on the Internet
        # 048104.python.pywin32_testall.line104.comment just to run these tests, so try it...
        maybes = [
            os.path.join(directory, "adodbapi", "test", "test_adodbapi_dbapi20.py")
            for directory in code_directories
        ]
        find_and_run(maybes, remains)

    if failures:
        print("The following scripts failed")
        for failure in failures:
            print(">", failure)
        sys.exit(1)
    print("All tests passed \\o/")


if __name__ == "__main__":
    main()
