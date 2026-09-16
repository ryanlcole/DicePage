import sys
import unittest

import pywintypes
import win32api


class TestError1(Exception):
    pass


class TestError2(Exception):
    pass


# 048152.python.handles.line16.comment A class that will never die vie refcounting, but will die via GC.
class Cycle:
    def __init__(self, handle):
        self.cycle = self
        self.handle = handle


class PyHandleTestCase(unittest.TestCase):
    def testCleanup1(self):
        # 048153.python.handles.line25.comment We used to clobber all outstanding exceptions.
        def f1(invalidate):
            import win32event

            h = win32event.CreateEvent(None, 0, 0, None)
            if invalidate:
                win32api.CloseHandle(int(h))
            raise TestError1
            # 048154.python.handles.line33.comment If we invalidated, then the object destruction code will attempt
            # 048155.python.handles.line34.comment to close an invalid handle.  We don't wan't an exception in
            # 048156.python.handles.line35.comment this case

        def f2(invalidate):
            """This function should throw an OSError."""
            try:
                f1(invalidate)
            except TestError1:
                raise TestError2

        self.assertRaises(TestError2, f2, False)
        # 048157.python.handles.line45.comment Now do it again, but so the auto object destruction
        # 048158.python.handles.line46.comment actually fails.
        self.assertRaises(TestError2, f2, True)

    def testCleanup2(self):
        # 048159.python.handles.line50.comment Cause an exception during object destruction.
        # 048160.python.handles.line51.comment The worst this does is cause an ".XXX undetected error (why=3)"
        # 048161.python.handles.line52.comment So avoiding that is the goal
        import win32event

        h = win32event.CreateEvent(None, 0, 0, None)
        # 048162.python.handles.line56.comment Close the handle underneath the object.
        win32api.CloseHandle(int(h))
        # 048163.python.handles.line58.comment Object destructor runs with the implicit close failing
        h = None

    def testCleanup3(self):
        # 048164.python.handles.line62.comment And again with a class - no __del__
        import win32event

        class Test:
            def __init__(self):
                self.h = win32event.CreateEvent(None, 0, 0, None)
                win32api.CloseHandle(int(self.h))

        t = Test()
        t = None

    def testCleanupGood(self):
        # 048165.python.handles.line74.comment And check that normal error semantics *do* work.
        import win32event

        h = win32event.CreateEvent(None, 0, 0, None)
        win32api.CloseHandle(int(h))
        self.assertRaises(win32api.error, h.Close)
        # 048166.python.handles.line80.comment A following Close is documented as working
        h.Close()

    def testInvalid(self):
        h = pywintypes.HANDLE(-2)
        try:
            h.Close()
            # 048167.python.handles.line87.comment Ideally, we'd:
            # 048168.python.handles.line88.comment self.assertRaises(win32api.error, h.Close)
            # 048169.python.handles.line89.comment and everywhere markh has tried, that would pass - but not on
            # 048170.python.handles.line90.comment GitHub automation, where the .Close apparently works fine.
            # 048171.python.handles.line91.comment (same for -1. Using 0 appears to work fine everywhere)
            # 048172.python.handles.line92.comment There still seems value in testing it though, so we just accept
            # 048173.python.handles.line93.comment either working or failing.
        except win32api.error:
            pass

    def testOtherHandle(self):
        h = pywintypes.HANDLE(1)
        h2 = pywintypes.HANDLE(h)
        self.assertEqual(h, h2)
        # 048174.python.handles.line101.comment but the above doesn't really test everything - we want a way to
        # 048175.python.handles.line102.comment pass the handle directly into PyWinLong_AsVoidPtr.  One way to
        # 048176.python.handles.line103.comment to that is to abuse win32api.GetProcAddress() - the 2nd param
        # 048177.python.handles.line104.comment is passed to PyWinLong_AsVoidPtr() if it's not a string.
        # 048178.python.handles.line105.comment passing a handle value of '1' should work - there is something
        # 048179.python.handles.line106.comment at that ordinal
        win32api.GetProcAddress(sys.dllhandle, h)

    def testHandleInDict(self):
        h = pywintypes.HANDLE(1)
        d = {"foo": h}
        self.assertEqual(d["foo"], h)

    def testHandleInDictThenInt(self):
        h = pywintypes.HANDLE(1)
        d = {"foo": h}
        self.assertEqual(d["foo"], 1)

    def testHandleCompareNone(self):
        h = pywintypes.HANDLE(1)
        self.assertNotEqual(h, None)
        self.assertNotEqual(None, h)
        # 048180.python.handles.line123.comment ensure we use both __eq__ and __ne__ ops
        self.assertFalse(h is None)
        self.assertTrue(h is not None)

    def testHandleCompareInt(self):
        h = pywintypes.HANDLE(1)
        self.assertNotEqual(h, 0)
        self.assertEqual(h, 1)
        # 048181.python.handles.line131.comment ensure we use both __eq__ and __ne__ ops
        self.assertTrue(h == 1)
        self.assertTrue(1 == h)
        self.assertFalse(h != 1)
        self.assertFalse(1 != h)
        self.assertFalse(h == 0)
        self.assertFalse(0 == h)
        self.assertTrue(h != 0)
        self.assertTrue(0 != h)

    def testHandleNonZero(self):
        h = pywintypes.HANDLE(0)
        self.assertFalse(h)

        h = pywintypes.HANDLE(1)
        self.assertTrue(h)

    def testLong(self):
        # 048182.python.handles.line149.comment sys.maxsize+1 should always be a 'valid' handle, treated as an
        # 048183.python.handles.line150.comment unsigned int, even though it is a long. Although pywin32 should not
        # 048184.python.handles.line151.comment directly create such longs, using struct.unpack() with a P format
        # 048185.python.handles.line152.comment may well return them. eg:
        # 048186.python.handles.line153.comment >>> struct.unpack("P", struct.pack("P", -1))
        # 048187.python.handles.line154.comment (4294967295L,)
        pywintypes.HANDLE(sys.maxsize + 1)

    def testGC(self):
        # 048188.python.handles.line158.comment This used to provoke:
        # 048189.python.handles.line159.comment Fatal Python error: unexpected exception during garbage collection
        def make():
            h = pywintypes.HANDLE(-2)
            c = Cycle(h)

        import gc

        make()
        gc.collect()

    def testTypes(self):
        self.assertRaises(TypeError, pywintypes.HANDLE, "foo")
        self.assertRaises(TypeError, pywintypes.HANDLE, ())


if __name__ == "__main__":
    unittest.main()
