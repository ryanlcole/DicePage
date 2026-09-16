# 008250.python.pyi_rth_inspect.line1.comment -----------------------------------------------------------------------------
# 008251.python.pyi_rth_inspect.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 008252.python.pyi_rth_inspect.line3.comment
# 008253.python.pyi_rth_inspect.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008254.python.pyi_rth_inspect.line5.comment you may not use this file except in compliance with the License.
# 008255.python.pyi_rth_inspect.line6.comment
# 008256.python.pyi_rth_inspect.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008257.python.pyi_rth_inspect.line8.comment
# 008258.python.pyi_rth_inspect.line9.comment SPDX-License-Identifier: Apache-2.0
# 008259.python.pyi_rth_inspect.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import inspect
    import os
    import sys
    import zipfile

    # 008260.python.pyi_rth_inspect.line19.comment Use sys._MEIPASS with normalized path component separator. This is necessary on some platforms (i.e., msys2/mingw
    # 008261.python.pyi_rth_inspect.line20.comment python on Windows), because we use string comparisons on the paths.
    SYS_PREFIX = os.path.normpath(sys._MEIPASS)
    BASE_LIBRARY = os.path.join(SYS_PREFIX, "base_library.zip")

    # 008262.python.pyi_rth_inspect.line24.comment Obtain the list of modules in base_library.zip, so we can use it in our `_pyi_getsourcefile` implementation.
    def _get_base_library_files(filename):
        # 008263.python.pyi_rth_inspect.line26.comment base_library.zip might not exit
        if not os.path.isfile(filename):
            return set()

        with zipfile.ZipFile(filename, 'r') as zf:
            namelist = zf.namelist()

        return set(os.path.normpath(entry) for entry in namelist)

    base_library_files = _get_base_library_files(BASE_LIBRARY)

    # 008264.python.pyi_rth_inspect.line37.comment Provide custom implementation of inspect.getsourcefile() for frozen applications that properly resolves relative
    # 008265.python.pyi_rth_inspect.line38.comment filenames obtained from object (e.g., inspect stack-frames). See #5963.
    # 008266.python.pyi_rth_inspect.line39.comment
    # 008267.python.pyi_rth_inspect.line40.comment Although we are overriding `inspect.getsourcefile` function, we are NOT trying to resolve source file here!
    # 008268.python.pyi_rth_inspect.line41.comment The main purpose of this implementation is to properly resolve relative file names obtained from `co_filename`
    # 008269.python.pyi_rth_inspect.line42.comment attribute of code objects (which are, in turn, obtained from in turn are obtained from `frame` and `traceback`
    # 008270.python.pyi_rth_inspect.line43.comment objects). PyInstaller strips absolute paths from `co_filename` when collecting modules, as the original absolute
    # 008271.python.pyi_rth_inspect.line44.comment paths are not portable/relocatable anyway. The `inspect` module tries to look up the module that corresponds to
    # 008272.python.pyi_rth_inspect.line45.comment the code object by comparing modules' `__file__` attribute to the value of `co_filename`. Therefore, our override
    # 008273.python.pyi_rth_inspect.line46.comment needs to resolve the relative file names (usually having a .py suffix) into absolute module names (which, in the
    # 008274.python.pyi_rth_inspect.line47.comment frozen application, usually have .pyc suffix).
    # 008275.python.pyi_rth_inspect.line48.comment
    # 008276.python.pyi_rth_inspect.line49.comment The `inspect` module retrieves the actual source code using `linecache.getlines()`. If the passed source filename
    # 008277.python.pyi_rth_inspect.line50.comment does not exist, the underlying implementation end up resolving the module, and obtains the source via loader's
    # 008278.python.pyi_rth_inspect.line51.comment `get_source` method. So for modules in the PYZ archive, it ends up calling `get_source` implementation on our
    # 008279.python.pyi_rth_inspect.line52.comment `PyiFrozenLoader`. For modules in `base_library.zip`, it ends up calling `get_source` on python's own
    # 008280.python.pyi_rth_inspect.line53.comment `zipimport.zipimporter`; to properly handle out-of-zip source files, we therefore need to monkey-patch
    # 008281.python.pyi_rth_inspect.line54.comment `get_source` with our own override that translates the in-zip .pyc filename into out-of-zip .py file location
    # 008282.python.pyi_rth_inspect.line55.comment and loads the source (this override is done in `pyimod02_importers` module).
    # 008283.python.pyi_rth_inspect.line56.comment
    # 008284.python.pyi_rth_inspect.line57.comment The above-described fallback takes place if the .pyc file does not exist on filesystem - if this ever becomes
    # 008285.python.pyi_rth_inspect.line58.comment a problem, we could consider monkey-patching `linecache.updatecache` (and possibly `checkcache`) to translate
    # 008286.python.pyi_rth_inspect.line59.comment .pyc paths in `sys._MEIPASS` and `base_library.zip` into .py paths in `sys._MEIPASS` before calling the original
    # 008287.python.pyi_rth_inspect.line60.comment implementation.
    _orig_inspect_getsourcefile = inspect.getsourcefile

    def _pyi_getsourcefile(object):
        filename = inspect.getfile(object)
        filename = os.path.normpath(filename)  # Ensure path component separators are normalized.
        if not os.path.isabs(filename):
            # 008289.python.pyi_rth_inspect.line67.comment Check if given filename matches the basename of __main__'s __file__.
            main_file = getattr(sys.modules['__main__'], '__file__', None)
            if main_file and filename == os.path.basename(main_file):
                return main_file

            # 008290.python.pyi_rth_inspect.line72.comment If the relative filename does not correspond to the frozen entry-point script, convert it to the absolute
            # 008291.python.pyi_rth_inspect.line73.comment path in either `sys._MEIPASS/base_library.zip` or `sys._MEIPASS`, whichever applicable.
            # 008292.python.pyi_rth_inspect.line74.comment
            # 008293.python.pyi_rth_inspect.line75.comment The modules in `sys._MEIPASS/base_library.zip` are handled by python's `zipimport.zipimporter`, and have
            # 008294.python.pyi_rth_inspect.line76.comment their __file__ attribute point to the .pyc file in the archive. So we match the behavior, in order to
            # 008295.python.pyi_rth_inspect.line77.comment facilitate matching via __file__ attribute and use of loader's `get_source`, as per the earlier comment
            # 008296.python.pyi_rth_inspect.line78.comment block.
            # 008297.python.pyi_rth_inspect.line79.comment
            # 008298.python.pyi_rth_inspect.line80.comment The modules in PYZ archive are handled by our `PyFrozenLoader`, which now sets the module's __file__
            # 008299.python.pyi_rth_inspect.line81.comment attribute to point to where .py files would be. Therefore, we can directly merge SYS_PREFIX and filename
            # 008300.python.pyi_rth_inspect.line82.comment (and if the source .py file exists, it will be loaded directly from filename, without the intermediate
            # 008301.python.pyi_rth_inspect.line83.comment loader look-up).
            pyc_filename = filename + 'c'
            if pyc_filename in base_library_files:
                return os.path.normpath(os.path.join(BASE_LIBRARY, pyc_filename))
            return os.path.normpath(os.path.join(SYS_PREFIX, filename))
        elif filename.startswith(SYS_PREFIX):
            # 008302.python.pyi_rth_inspect.line89.comment If filename is already an absolute file path pointing into application's top-level directory, return it
            # 008303.python.pyi_rth_inspect.line90.comment as-is and prevent any further processing.
            return filename
        # 008304.python.pyi_rth_inspect.line92.comment Use original implementation as a fallback.
        return _orig_inspect_getsourcefile(object)

    inspect.getsourcefile = _pyi_getsourcefile


_pyi_rthook()
del _pyi_rthook
