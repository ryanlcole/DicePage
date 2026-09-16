# 052129.python.init.line1.comment
# 052130.python.init.line2.comment (C) Copyright 2014-2024 Enthought, Inc., Austin, TX
# 052131.python.init.line3.comment All right reserved.
# 052132.python.init.line4.comment
# 052133.python.init.line5.comment This file is open source software distributed according to the terms in
# 052134.python.init.line6.comment LICENSE.txt
# 052135.python.init.line7.comment
import sys
import importlib
from importlib.abc import MetaPathFinder, Loader

from . import _winerrors  # noqa

# 052137.python.init.line14.comment Setup module redirection based on the backend
try:
    import cffi
except ImportError:
    _backend = 'ctypes'
else:
    del cffi
    _backend = 'cffi'


class BackendLoader(Loader):

    def __init__(self, redirect_module):
        self.redirect_module = redirect_module

    def create_module(self, spec):
        return importlib.import_module(self.redirect_module)

    def exec_module(self, module):
        pass


class BackendFinder(MetaPathFinder):

    def __init__(self, modules):
        self.redirected_modules = {
            'win32ctypes.core.{}'.format(module)
            for module in modules}

    def find_spec(self, fullname, path, target=None):
        if fullname in self.redirected_modules:
            module_name = fullname.split('.')[-1]
            if _backend == 'ctypes':
                redirected = f'win32ctypes.core.ctypes.{module_name}'
            else:
                redirected = f'win32ctypes.core.cffi.{module_name}'
            loader = BackendLoader(redirected)
            return importlib.machinery.ModuleSpec(
                f'win32ctypes.core.{module_name}', loader)
        else:
            return None


sys.meta_path.append(BackendFinder([
    '_dll', '_authentication', '_time',
    '_common', '_resource', '_nl_support',
    '_system_information']))
