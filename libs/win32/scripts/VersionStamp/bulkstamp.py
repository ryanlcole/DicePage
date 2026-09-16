# 047925.python.bulkstamp.line1.comment
# 047926.python.bulkstamp.line2.comment bulkstamp.py:
# 047927.python.bulkstamp.line3.comment Stamp versions on all files that can be found in a given tree.
# 047928.python.bulkstamp.line4.comment
# 047929.python.bulkstamp.line5.comment USAGE: python bulkstamp.py <version> <root directory> <descriptions>
# 047930.python.bulkstamp.line6.comment
# 047931.python.bulkstamp.line7.comment Example: python bulkstamp.py 103 ..\win32\Build\ desc.txt
# 047932.python.bulkstamp.line8.comment
# 047933.python.bulkstamp.line9.comment <version> corresponds to the build number. It will be concatenated with
# 047934.python.bulkstamp.line10.comment the major and minor version numbers found in the description file.
# 047935.python.bulkstamp.line11.comment
# 047936.python.bulkstamp.line12.comment Description information is pulled from an input text file with lines of
# 047937.python.bulkstamp.line13.comment the form:
# 047938.python.bulkstamp.line14.comment
# 047939.python.bulkstamp.line15.comment <basename> <white space> <description>
# 047940.python.bulkstamp.line16.comment
# 047941.python.bulkstamp.line17.comment For example:
# 047942.python.bulkstamp.line18.comment
# 047943.python.bulkstamp.line19.comment PyWinTypes.dll Common types for Python on Win32
# 047944.python.bulkstamp.line20.comment etc
# 047945.python.bulkstamp.line21.comment
# 047946.python.bulkstamp.line22.comment The product's name, major, and minor versions are specified as:
# 047947.python.bulkstamp.line23.comment
# 047948.python.bulkstamp.line24.comment name <white space> <value>
# 047949.python.bulkstamp.line25.comment major <white space> <value>
# 047950.python.bulkstamp.line26.comment minor <white space> <value>
# 047951.python.bulkstamp.line27.comment
# 047952.python.bulkstamp.line28.comment The tags are case-sensitive.
# 047953.python.bulkstamp.line29.comment
# 047954.python.bulkstamp.line30.comment Any line beginning with "#" will be ignored. Empty lines are okay.
# 047955.python.bulkstamp.line31.comment

import fnmatch
import os
import sys
from collections.abc import Mapping
from optparse import Values

try:
    import win32verstamp
except ModuleNotFoundError:
    # 047956.python.bulkstamp.line42.comment If run with pywin32 not already installed
    sys.path.append(os.path.abspath(__file__ + "/../../../Lib"))
    import win32verstamp

g_patterns = [
    "*.dll",
    "*.pyd",
    "*.exe",
    "*.ocx",
]


def walk(vars: Mapping[str, str], debug, descriptions, dirname, names) -> int:
    """Returns the number of stamped files."""
    numStamped = 0
    for name in names:
        for pat in g_patterns:
            if fnmatch.fnmatch(name, pat):
                # 047957.python.bulkstamp.line60.comment Handle the "_d" thing.
                pathname = os.path.join(dirname, name)
                base, ext = os.path.splitext(name)
                if base.endswith("_d"):
                    name = base[:-2] + ext
                is_dll = ext.lower() != ".exe"
                if os.path.normcase(name) in descriptions:
                    description = descriptions[os.path.normcase(name)]
                    try:
                        options = Values(
                            {**vars, "description": description, "dll": is_dll}
                        )
                        win32verstamp.stamp(pathname, options)
                        numStamped += 1
                    except OSError as exc:
                        print(
                            "Could not stamp",
                            pathname,
                            "Error",
                            exc.winerror,
                            "-",
                            exc.strerror,
                        )
                else:
                    print("WARNING: description not provided for:", name)
                    # 047958.python.bulkstamp.line85.comment skip branding this - assume already branded or handled elsewhere
    return numStamped


# 047959.python.bulkstamp.line89.comment print("Stamped", pathname)


def load_descriptions(fname, vars):
    retvars: dict[str, str] = {}
    descriptions = {}

    lines = open(fname, "r").readlines()

    for i in range(len(lines)):
        line = lines[i].strip()
        if line != "" and line[0] != "#":
            idx1 = line.find(" ")
            idx2 = line.find("\t")
            if idx1 == -1 or idx2 < idx1:
                idx1 = idx2
            if idx1 == -1:
                print("ERROR: bad syntax in description file at line %d." % (i + 1))
                sys.exit(1)

            key = line[:idx1]
            val = line[idx1:].strip()
            if key in vars:
                retvars[key] = val
            else:
                descriptions[key] = val

    if "product" not in retvars:
        print("ERROR: description file is missing the product name.")
        sys.exit(1)
    if "major" not in retvars:
        print("ERROR: description file is missing the major version number.")
        sys.exit(1)
    if "minor" not in retvars:
        print("ERROR: description file is missing the minor version number.")
        sys.exit(1)

    return retvars, descriptions


def scan(build, root: str, desc, **custom_vars):
    try:
        build = int(build)
    except ValueError:
        print("ERROR: build number is not a number: %s" % build)
        sys.exit(1)

    debug = 0  ### maybe fix this one day

    varList = ["major", "minor", "sub", "company", "copyright", "trademarks", "product"]

    vars, descriptions = load_descriptions(desc, varList)
    vars["build"] = build
    vars.update(custom_vars)

    numStamped = 0
    for directory, dirnames, filenames in os.walk(root):
        numStamped += walk(vars, debug, descriptions, directory, filenames)

    print(f"Stamped {numStamped} files.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("ERROR: incorrect invocation. See script's header comments.")
        sys.exit(1)

    scan(*sys.argv[1:])
