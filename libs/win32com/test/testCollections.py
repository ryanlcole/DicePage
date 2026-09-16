# 049973.python.testCollections.line1.comment testCollections.py
# 049974.python.testCollections.line2.comment
# 049975.python.testCollections.line3.comment This code tests both the client and server side of collections
# 049976.python.testCollections.line4.comment and enumerators.
# 049977.python.testCollections.line5.comment
# 049978.python.testCollections.line6.comment Also has the side effect of testing some of the PythonCOM error semantics.
import sys
import unittest

import pythoncom
import win32com.client
import win32com.server.util
import win32com.test.util
import winerror


def MakeEmptyEnum():
    # 049979.python.testCollections.line18.comment create the Python enumerator object as a real COM object
    o = win32com.server.util.wrap(win32com.server.util.Collection())
    return win32com.client.Dispatch(o)


def MakeTestEnum():
    # 049980.python.testCollections.line24.comment create a sub-collection, just to make sure it works :-)
    sub = win32com.server.util.wrap(
        win32com.server.util.Collection(["Sub1", 2, "Sub3"])
    )
    # 049981.python.testCollections.line28.comment create the Python enumerator object as a real COM object
    o = win32com.server.util.wrap(win32com.server.util.Collection([1, "Two", 3, sub]))
    return win32com.client.Dispatch(o)


def TestEnumAgainst(o, check):
    for i in range(len(check)):
        assert o(i) == check[i], (
            f"Using default method gave the incorrect value - {o(i)!r}/{check[i]!r}"
        )

    for i in range(len(check)):
        assert o.Item(i) == check[i], (
            f"Using Item method gave the incorrect value - {o(i)!r}/{check[i]!r}"
        )

    # 049982.python.testCollections.line44.comment First try looping.
    cmp = []
    for s in o:
        cmp.append(s)

    assert cmp[: len(check)] == check, (
        f"Result after looping isn't correct - {cmp[: len(check)]!r}/{check!r}"
    )

    for i in range(len(check)):
        assert o[i] == check[i], "Using indexing gave the incorrect value"


def TestEnum(quiet=None):
    if quiet is None:
        quiet = not "-v" in sys.argv
    if not quiet:
        print("Simple enum test")
    o = MakeTestEnum()
    check = [1, "Two", 3]
    TestEnumAgainst(o, check)

    if not quiet:
        print("sub-collection test")
    sub = o[3]
    TestEnumAgainst(sub, ["Sub1", 2, "Sub3"])

    # 049983.python.testCollections.line71.comment Remove the sublist for this test!
    o.Remove(o.Count() - 1)

    if not quiet:
        print("Remove item test")
    del check[1]
    o.Remove(1)
    TestEnumAgainst(o, check)

    if not quiet:
        print("Add item test")
    o.Add("New Item")
    check.append("New Item")
    TestEnumAgainst(o, check)

    if not quiet:
        print("Insert item test")
    o.Insert(2, -1)
    check.insert(2, -1)
    TestEnumAgainst(o, check)

    # 049984.python.testCollections.line92.comment ## This does not work!
    # 049985.python.testCollections.line93.comment if not quiet: print("Indexed replace item test")
    # 049986.python.testCollections.line94.comment o[2] = 'Replaced Item'
    # 049987.python.testCollections.line95.comment check[2] = 'Replaced Item'
    # 049988.python.testCollections.line96.comment TestEnumAgainst(o, check)

    try:
        o()
        raise AssertionError(
            "default method with no args worked when it shouldn't have!"
        )
    except pythoncom.com_error as exc:
        assert exc.hresult == winerror.DISP_E_BADPARAMCOUNT, (
            f"Expected DISP_E_BADPARAMCOUNT - got {exc}"
        )

    try:
        o.Insert("foo", 2)
        raise AssertionError("Insert worked when it shouldn't have!")
    except pythoncom.com_error as exc:
        assert exc.hresult == winerror.DISP_E_TYPEMISMATCH, (
            f"Expected DISP_E_TYPEMISMATCH - got {exc}"
        )

    # 049989.python.testCollections.line116.comment Remove the sublist for this test!
    try:
        o.Remove(o.Count())
        raise AssertionError("Remove worked when it shouldn't have!")
    except pythoncom.com_error as exc:
        assert exc.hresult == winerror.DISP_E_BADINDEX, (
            f"Expected DISP_E_BADINDEX - got {exc}"
        )

    # 049990.python.testCollections.line125.comment Test an empty collection
    if not quiet:
        print("Empty collection test")
    o = MakeEmptyEnum()
    for item in o:
        raise AssertionError("Empty list performed an iteration")

    try:
        ob = o[1]
        raise AssertionError("Empty list could be indexed")
    except IndexError:
        pass

    try:
        ob = o[0]
        raise AssertionError("Empty list could be indexed")
    except IndexError:
        pass

    try:
        ob = o(0)
        raise AssertionError("Empty list could be indexed")
    except pythoncom.com_error as exc:
        assert exc.hresult == winerror.DISP_E_BADINDEX, (
            f"Expected DISP_E_BADINDEX - got {exc}"
        )


class TestCase(win32com.test.util.TestCase):
    def testEnum(self):
        TestEnum()


if __name__ == "__main__":
    unittest.main()
