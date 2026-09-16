# 008570.python.pyi_rth_setuptools.line1.comment -----------------------------------------------------------------------------
# 008571.python.pyi_rth_setuptools.line2.comment Copyright (c) 2022-2023, PyInstaller Development Team.
# 008572.python.pyi_rth_setuptools.line3.comment
# 008573.python.pyi_rth_setuptools.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008574.python.pyi_rth_setuptools.line5.comment you may not use this file except in compliance with the License.
# 008575.python.pyi_rth_setuptools.line6.comment
# 008576.python.pyi_rth_setuptools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008577.python.pyi_rth_setuptools.line8.comment
# 008578.python.pyi_rth_setuptools.line9.comment SPDX-License-Identifier: Apache-2.0
# 008579.python.pyi_rth_setuptools.line10.comment -----------------------------------------------------------------------------

# 008580.python.pyi_rth_setuptools.line12.comment This runtime hook performs the equivalent of the distutils-precedence.pth from the setuptools package;
# 008581.python.pyi_rth_setuptools.line13.comment it registers a special meta finder that diverts import of distutils to setuptools._distutils, if available.


def _pyi_rthook():
    def _install_setuptools_distutils_hack():
        import os
        import setuptools

        # 008582.python.pyi_rth_setuptools.line21.comment We need to query setuptools version at runtime, because the default value for SETUPTOOLS_USE_DISTUTILS
        # 008583.python.pyi_rth_setuptools.line22.comment has changed at version 60.0 from "stdlib" to "local", and we want to mimic that behavior.
        setuptools_major = int(setuptools.__version__.split('.')[0])
        default_value = "stdlib" if setuptools_major < 60 else "local"

        if os.environ.get("SETUPTOOLS_USE_DISTUTILS", default_value) == "local":
            import _distutils_hack
            _distutils_hack.add_shim()

    try:
        _install_setuptools_distutils_hack()
    except Exception:
        pass


_pyi_rthook()
del _pyi_rthook
