# 008315.python.pyi_rth_mplconfig.line1.comment -----------------------------------------------------------------------------
# 008316.python.pyi_rth_mplconfig.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008317.python.pyi_rth_mplconfig.line3.comment
# 008318.python.pyi_rth_mplconfig.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008319.python.pyi_rth_mplconfig.line5.comment you may not use this file except in compliance with the License.
# 008320.python.pyi_rth_mplconfig.line6.comment
# 008321.python.pyi_rth_mplconfig.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008322.python.pyi_rth_mplconfig.line8.comment
# 008323.python.pyi_rth_mplconfig.line9.comment SPDX-License-Identifier: Apache-2.0
# 008324.python.pyi_rth_mplconfig.line10.comment -----------------------------------------------------------------------------

# 008325.python.pyi_rth_mplconfig.line12.comment matplotlib will create $HOME/.matplotlib folder in user's home directory. In this directory there is fontList.cache
# 008326.python.pyi_rth_mplconfig.line13.comment file which lists paths to matplotlib fonts.
# 008327.python.pyi_rth_mplconfig.line14.comment
# 008328.python.pyi_rth_mplconfig.line15.comment When you run your onefile exe for the first time it's extracted to for example "_MEIxxxxx" temp directory and
# 008329.python.pyi_rth_mplconfig.line16.comment fontList.cache file is created with fonts paths pointing to this directory.
# 008330.python.pyi_rth_mplconfig.line17.comment
# 008331.python.pyi_rth_mplconfig.line18.comment Second time you run your exe new directory is created "_MEIyyyyy" but fontList.cache file still points to previous
# 008332.python.pyi_rth_mplconfig.line19.comment directory which was deleted. And then you will get error like:
# 008333.python.pyi_rth_mplconfig.line20.comment
# 008334.python.pyi_rth_mplconfig.line21.comment RuntimeError: Could not open facefile
# 008335.python.pyi_rth_mplconfig.line22.comment
# 008336.python.pyi_rth_mplconfig.line23.comment We need to force matplotlib to recreate config directory every time you run your app.


def _pyi_rthook():
    import atexit
    import os
    import shutil

    import _pyi_rth_utils.tempfile  # PyInstaller's run-time hook utilities module

    # 008338.python.pyi_rth_mplconfig.line33.comment Isolate matplotlib's config dir into temporary directory.
    # 008339.python.pyi_rth_mplconfig.line34.comment Use our replacement for `tempfile.mkdtemp` function that properly restricts access to directory on all platforms.
    configdir = _pyi_rth_utils.tempfile.secure_mkdtemp()
    os.environ['MPLCONFIGDIR'] = configdir

    try:
        # 008340.python.pyi_rth_mplconfig.line39.comment Remove temp directory at application exit and ignore any errors.
        atexit.register(shutil.rmtree, configdir, ignore_errors=True)
    except OSError:
        pass


_pyi_rthook()
del _pyi_rthook
