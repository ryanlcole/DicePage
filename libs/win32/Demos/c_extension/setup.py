# 046030.python.setup.line1.comment A sample distutils script to show to build your own
# 046031.python.setup.line2.comment extension module which extends pywintypes or pythoncom.
# 046032.python.setup.line3.comment
# 046033.python.setup.line4.comment Use 'python -m build' to build this extension.
import os
from setuptools import Extension, setup
from sysconfig import get_paths

sources = ["win32_extension.cpp"]
lib_dir = get_paths()["platlib"]

# 046034.python.setup.line12.comment Specify the directory where the PyWin32 .h and .lib files are installed.
# 046035.python.setup.line13.comment If you are doing a win32com extension, you will also need to add
# 046036.python.setup.line14.comment win32com\Include and win32com\Libs.
ext = Extension(
    "win32_extension",
    sources,
    include_dirs=[os.path.join(lib_dir, "win32", "include")],
    library_dirs=[os.path.join(lib_dir, "win32", "libs")],
)

setup(
    name="win32 extension sample",
    version="0.1",
    ext_modules=[ext],
)
