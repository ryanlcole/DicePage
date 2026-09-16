import sys

# 044608.python.py39.line3.comment Explicitly use the ``"locale"`` encoding in versions that support it,
# 044609.python.py39.line4.comment otherwise just rely on the implicit handling of ``encoding=None``.
# 044610.python.py39.line5.comment Since all platforms that support ``EncodingWarning`` also support
# 044611.python.py39.line6.comment ``encoding="locale"``, this can be used to suppress the warning.
# 044612.python.py39.line7.comment However, please try to use UTF-8 when possible
# 044613.python.py39.line8.comment (.pth files are the notorious exception: python/cpython#77102, pypa/setuptools#3937).
LOCALE_ENCODING = "locale" if sys.version_info >= (3, 10) else None
