# 047918.python.BrandProject.line1.comment BrandProject.py
# 047919.python.BrandProject.line2.comment
# 047920.python.BrandProject.line3.comment Brand a VSS project with a "build number", then optionally
# 047921.python.BrandProject.line4.comment stamp DLL/EXE files with version information.

import getopt
import os
import sys

import bulkstamp
import vssutil
import win32api


def BrandProject(
    vssProjectName,
    descFile,
    stampPath,
    filesToSubstitute,
    buildDesc=None,
    auto=0,
    bRebrand=0,
):
    # 047922.python.BrandProject.line24.comment vssProjectName -- The name of the VSS project to brand.
    # 047923.python.BrandProject.line25.comment descFile -- A test file containing descriptions of the files in the release.
    # 047924.python.BrandProject.line26.comment stampPath -- The full path to where the files referenced in descFile can be found.
    path = win32api.GetFullPathName(stampPath)

    build = vssutil.MakeNewBuildNo(vssProjectName, buildDesc, auto, bRebrand)
    if build is None:
        print("Cancelled")
        return

    bulkstamp.scan(build, stampPath, descFile)
    for infile, outfile in filesToSubstitute:
        vssutil.SubstituteVSSInFile(vssProjectName, infile, outfile)
    return 1


def usage(msg):
    print(msg)
    print(
        f"""\
{os.path.basename(sys.argv[0])} Usage:
{os.path.basename(sys.argv[0])} [options] vssProject descFile stampPath

Automatically brand a VSS project with an automatically incremented
build number, and stamp DLL/EXE files with the build number.

Checks that no files are checked out in the project, and finds the last
build number, and suggests the next number.

Options:
-a     - Auto increment the build number, and brand (otherwise prompt
         for the build number after looking for the previous)
-r     - Restamp the files with the existing build number.
-d     - A description for the VSS Label.
-f infile=outfile - Substitute special VSS labels in the specified text
                    file with the text extracted from VSS.
"""
    )
    sys.exit(1)


if __name__ == "__main__":
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], "af:d:r")
    except getopt.GetoptError as msg:
        usage(msg)
    bAuto = bRebrand = 0
    stampFiles = []
    desc = None
    for opt, val in opts:
        if opt == "-a":
            bAuto = 1
        if opt == "-f":
            infile, outfile = val.split("=", 2)
            stampFiles.append((infile, outfile))
        if opt == "-d":
            desc = val
        if opt == "-r":
            bRebrand = 1
    if len(args) < 3:
        usage("You must specify the required arguments")
    vssProjectName = "$\\" + args[0]
    descFile = args[1]
    path = args[2]
    try:
        os.stat(descFile)
    except OSError:
        usage("The description file '%s' can not be found" % (descFile))
    if not os.path.isdir(path):
        usage("The path to the files to stamp '%s' does not exist" % (path))

    BrandProject(vssProjectName, descFile, path, stampFiles, desc, bAuto, bRebrand)
