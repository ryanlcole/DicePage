# 046895.python.pywin32_bootstrap.line1.comment Imported by pywin32.pth to bootstrap the pywin32 environment in "portable"
# 046896.python.pywin32_bootstrap.line2.comment environments or any other case where the post-install script isn't run.
# 046897.python.pywin32_bootstrap.line3.comment
# 046898.python.pywin32_bootstrap.line4.comment In short, there's a directory installed by pywin32 named 'pywin32_system32'
# 046899.python.pywin32_bootstrap.line5.comment with some important DLLs which need to be found by Python when some pywin32
# 046900.python.pywin32_bootstrap.line6.comment modules are imported.


try:
    import pywin32_system32
except ImportError:  # Python ≥3.6: replace ImportError with ModuleNotFoundError
    pass
else:
    import os

    # 046902.python.pywin32_bootstrap.line16.comment We're guaranteed only that __path__: Iterable[str]
    # 046903.python.pywin32_bootstrap.line17.comment https://docs.python.org/3/reference/import.html#path-attributes-on-modules
    for path in pywin32_system32.__path__:
        if os.path.isdir(path):
            os.add_dll_directory(path)
            break
