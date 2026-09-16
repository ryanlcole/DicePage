# 011653.python.pyi_rth_tensorflow.line1.comment -----------------------------------------------------------------------------
# 011654.python.pyi_rth_tensorflow.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 011655.python.pyi_rth_tensorflow.line3.comment
# 011656.python.pyi_rth_tensorflow.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011657.python.pyi_rth_tensorflow.line5.comment
# 011658.python.pyi_rth_tensorflow.line6.comment The full license is available in LICENSE, distributed with
# 011659.python.pyi_rth_tensorflow.line7.comment this software.
# 011660.python.pyi_rth_tensorflow.line8.comment
# 011661.python.pyi_rth_tensorflow.line9.comment SPDX-License-Identifier: Apache-2.0
# 011662.python.pyi_rth_tensorflow.line10.comment -----------------------------------------------------------------------------

def _pyi_rthook():
    import sys

    # 011663.python.pyi_rth_tensorflow.line15.comment `tensorflow` versions prior to 2.3.0 attempt to use `site.USER_SITE` in path/string manipulation functions.
    # 011664.python.pyi_rth_tensorflow.line16.comment As frozen application runs with disabled `site`, the value of this variable is `None`, and causes path/string
    # 011665.python.pyi_rth_tensorflow.line17.comment manipulation functions to raise an error. As a work-around, we set `site.USER_SITE` to an empty string, which is
    # 011666.python.pyi_rth_tensorflow.line18.comment also what the fake `site` module available in PyInstaller prior to v5.5 did.
    import site

    if site.USER_SITE is None:
        site.USER_SITE = ''

    # 011667.python.pyi_rth_tensorflow.line24.comment The issue described about with site.USER_SITE being None has largely been resolved in contemporary `tensorflow`
    # 011668.python.pyi_rth_tensorflow.line25.comment versions, which now check that `site.ENABLE_USER_SITE` is set and that `site.USER_SITE` is not None before
    # 011669.python.pyi_rth_tensorflow.line26.comment trying to use it.
    # 011670.python.pyi_rth_tensorflow.line27.comment
    # 011671.python.pyi_rth_tensorflow.line28.comment However, `tensorflow` will attempt to search and load its plugins only if it believes that it is running from
    # 011672.python.pyi_rth_tensorflow.line29.comment "a pip-based installation" - if the package's location is rooted in one of the "site-packages" directories. See
    # 011673.python.pyi_rth_tensorflow.line30.comment https://github.com/tensorflow/tensorflow/blob/6887368d6d46223f460358323c4b76d61d1558a8/tensorflow/api_template.__init__.py#L110C76-L156
    # 011674.python.pyi_rth_tensorflow.line31.comment Unfortunately, they "cleverly" infer the module's location via `inspect.getfile(inspect.currentframe())`, which
    # 011675.python.pyi_rth_tensorflow.line32.comment in the frozen application returns anonymized relative source file name (`tensorflow/__init__.py`) - so we need one
    # 011676.python.pyi_rth_tensorflow.line33.comment of the "site directories" to be just "tensorflow" (to fool the `_running_from_pip_package()` check), and we also
    # 011677.python.pyi_rth_tensorflow.line34.comment need `sys._MEIPASS` to be among them (to load the plugins from the actual `sys._MEIPASS/tensorflow-plugins`).
    # 011678.python.pyi_rth_tensorflow.line35.comment Therefore, we monkey-patch `site.getsitepackages` to add those two entries to the list of "site directories".

    _orig_getsitepackages = getattr(site, 'getsitepackages', None)

    def _pyi_getsitepackages():
        return [
            sys._MEIPASS,
            "tensorflow",
            *(_orig_getsitepackages() if _orig_getsitepackages is not None else []),
        ]

    site.getsitepackages = _pyi_getsitepackages

    # 011679.python.pyi_rth_tensorflow.line48.comment NOTE: instead of the above override, we could also set TF_PLUGGABLE_DEVICE_LIBRARY_PATH, but that works only
    # 011680.python.pyi_rth_tensorflow.line49.comment for tensorflow >= 2.12.


_pyi_rthook()
del _pyi_rthook
