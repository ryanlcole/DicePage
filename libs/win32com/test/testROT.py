import unittest

import pythoncom
import win32com.test.util
import winerror


class TestROT(win32com.test.util.TestCase):
    def testit(self):
        ctx = pythoncom.CreateBindCtx()
        rot = pythoncom.GetRunningObjectTable()
        num = 0
        for mk in rot:
            name = mk.GetDisplayName(ctx, None)
            num += 1
            # 050320.python.testROT.line16.comment Monikers themselves can iterate their contents (sometimes :)
            try:
                for sub in mk:
                    num += 1
            except pythoncom.com_error as exc:
                if exc.hresult != winerror.E_NOTIMPL:
                    raise

        # 050321.python.testROT.line24.comment if num < 2:
        # 050322.python.testROT.line25.comment print("Only", num, "objects in the ROT - this is unusual")


if __name__ == "__main__":
    unittest.main()
