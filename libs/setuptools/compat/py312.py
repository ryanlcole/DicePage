from __future__ import annotations

import sys

if sys.version_info >= (3, 12, 4):
    # 044605.python.py312.line6.comment Python 3.13 should support `.pth` files encoded in UTF-8
    # 044606.python.py312.line7.comment See discussion in https://github.com/python/cpython/issues/77102
    PTH_ENCODING: str | None = "utf-8"
else:
    from .py39 import LOCALE_ENCODING

    # 044607.python.py312.line12.comment PTH_ENCODING = "locale"
    PTH_ENCODING = LOCALE_ENCODING
