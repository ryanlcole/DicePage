import importlib
import sys

__version__, _, _ = sys.version.partition(' ')


try:
    # 039230.python.init.line8.comment Allow Debian and pkgsrc (only) to customize system
    # 039231.python.init.line9.comment behavior. Ref pypa/distutils#2 and pypa/distutils#16.
    # 039232.python.init.line10.comment This hook is deprecated and no other environments
    # 039233.python.init.line11.comment should use it.
    importlib.import_module('_distutils_system_mod')
except ImportError:
    pass
