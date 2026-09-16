# 050091.python.testIterators.line1.comment Some raw iter tests.  Some "high-level" iterator tests can be found in
# 050092.python.testIterators.line2.comment testvb.py and testOutlook.py
import sys
import unittest

import pythoncom
import win32com.server.util
import win32com.test.util
from win32com.client import Dispatch
from win32com.client.gencache import EnsureDispatch


class _BaseTestCase(win32com.test.util.TestCase):
    def test_enumvariant_vb(self):
        ob, iter = self.iter_factory()
        got = []
        for v in iter:
            got.append(v)
        self.assertEqual(got, self.expected_data)

    def test_yield(self):
        ob, i = self.iter_factory()
        got = []
        for v in iter(i):
            got.append(v)
        self.assertEqual(got, self.expected_data)

    def _do_test_nonenum(self, object):
        try:
            for i in object:
                pass
            self.fail("Could iterate over a non-iterable object")
        except TypeError:
            pass  # this is expected.
        self.assertRaises(TypeError, iter, object)
        self.assertRaises(AttributeError, getattr, object, "next")

    def test_nonenum_wrapper(self):
        # 050094.python.testIterators.line39.comment Check our raw PyIDispatch
        ob = self.object._oleobj_
        try:
            for i in ob:
                pass
            self.fail("Could iterate over a non-iterable object")
        except TypeError:
            pass  # this is expected.
        self.assertRaises(TypeError, iter, ob)
        self.assertRaises(AttributeError, getattr, ob, "next")

        # 050096.python.testIterators.line50.comment And our Dispatch wrapper
        ob = self.object
        try:
            for i in ob:
                pass
            self.fail("Could iterate over a non-iterable object")
        except TypeError:
            pass  # this is expected.
        # 050098.python.testIterators.line58.comment Note that as our object may be dynamic, we *do* have a __getitem__
        # 050099.python.testIterators.line59.comment method, meaning we *can* call iter() on the object.  In this case
        # 050100.python.testIterators.line60.comment actual iteration is what fails.
        # 050101.python.testIterators.line61.comment So either the 'iter(); will raise a type error, or an attempt to
        # 050102.python.testIterators.line62.comment fetch it
        try:
            next(iter(ob))
            self.fail("Expected a TypeError fetching this iterator")
        except TypeError:
            pass
        # 050103.python.testIterators.line68.comment And it should never have a 'next' method
        self.assertRaises(AttributeError, getattr, ob, "next")


class VBTestCase(_BaseTestCase):
    def setUp(self):
        def factory():
            # 050104.python.testIterators.line75.comment Our VB test harness exposes a property with IEnumVariant.
            ob = self.object.EnumerableCollectionProperty
            for i in self.expected_data:
                ob.Add(i)
            # 050105.python.testIterators.line79.comment Get the raw IEnumVARIANT.
            invkind = pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET
            iter = ob._oleobj_.InvokeTypes(
                pythoncom.DISPID_NEWENUM, 0, invkind, (13, 10), ()
            )
            return ob, iter.QueryInterface(pythoncom.IID_IEnumVARIANT)

        # 050106.python.testIterators.line86.comment We *need* generated dispatch semantics, so dynamic __getitem__ etc
        # 050107.python.testIterators.line87.comment don't get in the way of our tests.
        self.object = EnsureDispatch("PyCOMVBTest.Tester")
        self.expected_data = [1, "Two", "3"]
        self.iter_factory = factory

    def tearDown(self):
        self.object = None


# 050108.python.testIterators.line96.comment Test our client semantics, but using a wrapped Python list object.
# 050109.python.testIterators.line97.comment This has the effect of re-using our client specific tests, but in this
# 050110.python.testIterators.line98.comment case is exercising the server side.
class SomeObject:
    _public_methods_ = ["GetCollection"]

    def __init__(self, data):
        self.data = data

    def GetCollection(self):
        return win32com.server.util.NewCollection(self.data)


class WrappedPythonCOMServerTestCase(_BaseTestCase):
    def setUp(self):
        def factory():
            ob = self.object.GetCollection()
            flags = pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET
            enum = ob._oleobj_.Invoke(pythoncom.DISPID_NEWENUM, 0, flags, 1)
            return ob, enum.QueryInterface(pythoncom.IID_IEnumVARIANT)

        self.expected_data = [1, "Two", 3]
        sv = win32com.server.util.wrap(SomeObject(self.expected_data))
        self.object = Dispatch(sv)
        self.iter_factory = factory

    def tearDown(self):
        self.object = None


def suite():
    # 050111.python.testIterators.line127.comment We don't want our base class run
    suite = unittest.TestSuite()
    for item in globals().values():
        if (
            isinstance(item, type)
            and issubclass(item, unittest.TestCase)
            and item != _BaseTestCase
        ):
            suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(item))
    return suite


if __name__ == "__main__":
    unittest.main(argv=sys.argv + ["suite"])
