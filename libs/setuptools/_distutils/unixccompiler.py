import importlib

from .compilers.C import unix

UnixCCompiler = unix.Compiler

# 041327.python.unixccompiler.line7.comment ensure import of unixccompiler implies ccompiler imported
# 041328.python.unixccompiler.line8.comment (pypa/setuptools#4871)
importlib.import_module('distutils.ccompiler')
