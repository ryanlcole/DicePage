# 052325.python.test_backends.line1.comment
# 052326.python.test_backends.line2.comment (C) Copyright 2023 Enthought, Inc., Austin, TX
# 052327.python.test_backends.line3.comment All right reserved.
# 052328.python.test_backends.line4.comment
# 052329.python.test_backends.line5.comment This file is open source software distributed according to the terms in
# 052330.python.test_backends.line6.comment LICENSE.txt
# 052331.python.test_backends.line7.comment
import importlib
import unittest

from win32ctypes.core import _backend

_modules = [
    '_dll', '_authentication', '_time', '_common',
    '_resource',  '_nl_support', '_system_information']


class TestBackends(unittest.TestCase):

    @unittest.skipIf(_backend != 'cffi', 'cffi backend not enabled')
    def test_backend_cffi_load(self):
        # 052332.python.test_backends.line22.comment when/then
        for name in _modules:
            module = importlib.import_module(f'win32ctypes.core.{name}')
            self.assertEqual(
                module.__spec__.name, f'win32ctypes.core.{name}')
            self.assertTrue(module.__file__.endswith(f'cffi\\{name}.py'))

    @unittest.skipIf(_backend != 'ctypes', 'ctypes backend not enabled')
    def test_backend_ctypes_load(self):
        # 052333.python.test_backends.line31.comment when/then
        for name in _modules:
            module = importlib.import_module(f'win32ctypes.core.{name}')
            self.assertEqual(
                module.__spec__.name, f'win32ctypes.core.{name}')
            self.assertTrue(module.__file__.endswith(f'ctypes\\{name}.py'))
