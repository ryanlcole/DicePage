# 050188.python.testPyComTest.line1.comment NOTE - Still seems to be a leak here somewhere
# 050189.python.testPyComTest.line2.comment gateway count doesn't hit zero.  Hence the print statements!

import sys

sys.coinit_flags = 0  # Must be free-threaded!
import datetime
import decimal
import os
import time

import pythoncom
import win32com
import win32com.test.util
import win32timezone
import winerror
from win32api import CloseHandle, GetCurrentProcessId, OpenProcess
from win32com import universal
from win32com.client import (
    VARIANT,
    CastTo,
    DispatchBaseClass,
    Record,
    constants,
    gencache,
    register_record_class,
)
from win32process import GetProcessMemoryInfo

# 050191.python.testPyComTest.line30.comment This test uses a Python implemented COM server - ensure correctly registered.
win32com.test.util.RegisterPythonServer(
    os.path.join(os.path.dirname(__file__), "..", "servers", "test_pycomtest.py"),
    "Python.Test.PyCOMTest",
)

try:
    gencache.EnsureModule(
        "{6BCDCB60-5605-11D0-AE5F-CADD4C000000}", 0, 1, 1, bForDemand=False
    )
except pythoncom.com_error as error:
    importMsg = """*** PyCOMTest is not installed ***
  PyCOMTest is a Python test specific COM client and server.
  It is likely this server is not installed on this machine
  To install the server, you must get the win32com sources
  and build it using MS Visual C++"""
    print(f"The PyCOMTest module can not be located or generated.\n{importMsg}\n")
    raise RuntimeError(importMsg) from error

# 050192.python.testPyComTest.line49.comment We had a bg where RegisterInterfaces would fail if gencache had
# 050193.python.testPyComTest.line50.comment already been run - exercise that here
universal.RegisterInterfaces("{6BCDCB60-5605-11D0-AE5F-CADD4C000000}", 0, 1, 1)

verbose = 0


# 050194.python.testPyComTest.line56.comment Subclasses of pythoncom.com_record.
# 050195.python.testPyComTest.line57.comment Registration is performed in 'TestGenerated'.
class TestStruct1(pythoncom.com_record):
    __slots__ = ()
    TLBID = "{6BCDCB60-5605-11D0-AE5F-CADD4C000000}"
    MJVER = 1
    MNVER = 1
    LCID = 0
    GUID = "{7A4CE6A7-7959-4E85-A3C0-B41442FF0F67}"


class TestStruct2(pythoncom.com_record):
    __slots__ = ()
    TLBID = "{6BCDCB60-5605-11D0-AE5F-CADD4C000000}"
    MJVER = 1
    MNVER = 1
    LCID = 0
    GUID = "{78F0EA07-B7CF-42EA-A251-A4C6269F76AF}"


# 050196.python.testPyComTest.line76.comment We don't need to stick with the struct name in the TypeLibrary for the subclass name.
# 050197.python.testPyComTest.line77.comment The following class has the same GUID as TestStruct2 from the TypeLibrary.
class ArrayOfStructsTestStruct(pythoncom.com_record):
    __slots__ = ()
    TLBID = "{6BCDCB60-5605-11D0-AE5F-CADD4C000000}"
    MJVER = 1
    MNVER = 1
    LCID = 0
    GUID = "{78F0EA07-B7CF-42EA-A251-A4C6269F76AF}"


class NotInTypeLibraryTestStruct(pythoncom.com_record):
    __slots__ = ()
    TLBID = "{6BCDCB60-5605-11D0-AE5F-CADD4C000000}"
    MJVER = 1
    MNVER = 1
    LCID = 0
    GUID = "{79BB6AC3-12DE-4AC5-88AC-225C29A58043}"


def check_get_set(func, arg):
    got = func(arg)
    assert got == arg, f"{func} failed - expected {arg!r}, got {got!r}"


def check_get_set_raises(exc, func, arg):
    try:
        got = func(arg)
    except exc as e:
        pass  # what we expect!
    else:
        raise AssertionError(
            f"{func} with arg {arg!r} didn't raise {exc} - returned {got!r}"
        )


def progress(*args):
    if verbose:
        for arg in args:
            print(arg, end=" ")
        print()


def TestApplyResult(fn, args, result):
    try:
        fnName = str(fn).split()[1]
    except:
        fnName = str(fn)
    progress("Testing ", fnName)
    pref = "function " + fnName
    rc = fn(*args)
    assert rc == result, f"{pref} failed - result not {result!r} but {rc!r}"


def TestConstant(constName, pyConst):
    try:
        comConst = getattr(constants, constName)
    except:
        raise AssertionError(f"Constant {constName} missing")
    assert comConst == pyConst, (
        f"Constant value wrong for {constName} - got {comConst}, wanted {pyConst}"
    )


def GetMemoryUsage():
    pid = GetCurrentProcessId()
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    hprocess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    mem_info = GetProcessMemoryInfo(hprocess)
    CloseHandle(hprocess)
    return mem_info["WorkingSetSize"]


# 050199.python.testPyComTest.line150.comment Simple handler class.  This demo only fires one event.
class RandomEventHandler:
    def _Init(self):
        self.fireds = {}

    def OnFire(self, no):
        try:
            self.fireds[no] += 1
        except KeyError:
            self.fireds[no] = 0

    def OnFireWithNamedParams(self, no, a_bool, out1, out2):
        # 050200.python.testPyComTest.line162.comment This test exists mainly to help with an old bug, where named
        # 050201.python.testPyComTest.line163.comment params would come in reverse.
        Missing = pythoncom.Missing
        if no is not Missing:
            # 050202.python.testPyComTest.line166.comment We know our impl called 'OnFire' with the same ID
            assert no in self.fireds
            assert no + 1 == out1, "expecting 'out1' param to be ID+1"
            assert no + 2 == out2, "expecting 'out2' param to be ID+2"
        # 050203.python.testPyComTest.line170.comment The middle must be a boolean.
        assert a_bool is Missing or isinstance(a_bool, bool), "middle param not a bool"
        return out1 + 2, out2 + 2

    def _DumpFireds(self):
        if not self.fireds:
            print("ERROR: Nothing was received!")
        for firedId, no in self.fireds.items():
            progress("ID %d fired %d times" % (firedId, no))


# 050204.python.testPyComTest.line181.comment Test everything which can be tested using both the "dynamic" and "generated"
# 050205.python.testPyComTest.line182.comment COM objects (or when there are very subtle differences)
def TestCommon(o, is_generated):
    progress("Getting counter")
    counter = o.GetSimpleCounter()
    TestCounter(counter, is_generated)

    progress("Checking default args")
    rc = o.TestOptionals()
    assert rc[:-1] == ("def", 0, 1) and abs(rc[-1] - 3.14) <= 0.01, (
        "Did not get the optional values correctly",
        rc,
    )
    rc = o.TestOptionals("Hi", 2, 3, 1.1)
    assert rc[:-1] == ("Hi", 2, 3) and abs(rc[-1] - 1.1) <= 0.01, (
        "Did not get the specified optional values correctly",
        rc,
    )
    rc = o.TestOptionals2(0)
    assert rc == (0, "", 1), ("Did not get the optional2 values correctly", rc)
    rc = o.TestOptionals2(1.1, "Hi", 2)
    assert rc[1:] == ("Hi", 2) and abs(rc[0] - 1.1) <= 0.01, (
        "Did not get the specified optional2 values correctly",
        rc,
    )

    progress("Checking getting/passing IUnknown")
    check_get_set(o.GetSetUnknown, o)
    progress("Checking getting/passing IDispatch")
    # 050206.python.testPyComTest.line210.comment This might be called with either the interface or the CoClass - but these
    # 050207.python.testPyComTest.line211.comment functions always return from the interface.
    expected_class = o.__class__
    # 050208.python.testPyComTest.line213.comment CoClass instances have `default_interface`
    expected_class = getattr(expected_class, "default_interface", expected_class)
    assert isinstance(o.GetSetDispatch(o), expected_class), (
        f"GetSetDispatch failed: {o.GetSetDispatch(o)!r}"
    )
    progress("Checking getting/passing IDispatch of known type")
    expected_class = o.__class__
    expected_class = getattr(expected_class, "default_interface", expected_class)
    assert o.GetSetInterface(o).__class__ == expected_class, "GetSetDispatch failed"

    progress("Checking misc args")
    check_get_set(o.GetSetVariant, 4)
    check_get_set(o.GetSetVariant, "foo")
    check_get_set(o.GetSetVariant, o)

    # 050209.python.testPyComTest.line228.comment signed/unsigned.
    check_get_set(o.GetSetInt, 0)
    check_get_set(o.GetSetInt, -1)
    check_get_set(o.GetSetInt, 1)

    check_get_set(o.GetSetUnsignedInt, 0)
    check_get_set(o.GetSetUnsignedInt, 1)
    check_get_set(o.GetSetUnsignedInt, 0x80000000)
    # 050210.python.testPyComTest.line236.comment -1 is a special case - we accept a negative int (silently converting to unsigned)
    # 050211.python.testPyComTest.line237.comment but when getting it back we convert it to a long.
    assert o.GetSetUnsignedInt(-1) == 0xFFFFFFFF, "unsigned -1 failed"

    check_get_set(o.GetSetLong, 0)
    check_get_set(o.GetSetLong, -1)
    check_get_set(o.GetSetLong, 1)

    check_get_set(o.GetSetUnsignedLong, 0)
    check_get_set(o.GetSetUnsignedLong, 1)
    check_get_set(o.GetSetUnsignedLong, 0x80000000)
    # 050212.python.testPyComTest.line247.comment -1 is a special case - see above.
    assert o.GetSetUnsignedLong(-1) == 0xFFFFFFFF, "unsigned -1 failed"

    # 050213.python.testPyComTest.line250.comment We want to explicitly test > 32 bits.
    # 050214.python.testPyComTest.line251.comment 'maxsize+1' is no good on 64bit platforms as it's 65 bits!
    big = 2147483647
    for l in big, big + 1, 1 << 65:
        check_get_set(o.GetSetVariant, l)

    progress("Checking structs")
    r = o.GetStruct()
    assert r.int_value == 99 and str(r.str_value) == "Hello from C++"
    assert o.DoubleString("foo") == "foofoo"

    progress("Checking var args")
    o.SetVarArgs("Hi", "There", "From", "Python", 1)
    assert o.GetLastVarArgs() == (
        "Hi",
        "There",
        "From",
        "Python",
        1,
    ), f"VarArgs failed -{o.GetLastVarArgs()}"

    progress("Checking arrays")
    l = []
    TestApplyResult(o.SetVariantSafeArray, (l,), len(l))
    l = [1, 2, 3, 4]
    TestApplyResult(o.SetVariantSafeArray, (l,), len(l))
    TestApplyResult(
        o.CheckVariantSafeArray,
        (
            (
                1,
                2,
                3,
                4,
            ),
        ),
        1,
    )

    # 050215.python.testPyComTest.line289.comment and binary
    TestApplyResult(o.SetBinSafeArray, (memoryview(b"foo\0bar"),), 7)

    progress("Checking properties")
    o.LongProp = 3
    assert o.LongProp == o.IntProp == 3, (
        f"Property value wrong - got {o.LongProp}/{o.IntProp}"
    )
    o.LongProp = o.IntProp = -3
    assert o.LongProp == o.IntProp == -3, (
        f"Property value wrong - got {o.LongProp}/{o.IntProp}"
    )
    # 050216.python.testPyComTest.line301.comment This number fits in an unsigned long.  Attempting to set it to a normal
    # 050217.python.testPyComTest.line302.comment long will involve overflow, which is to be expected. But we do
    # 050218.python.testPyComTest.line303.comment expect it to work in a property explicitly a VT_UI4.
    check = 3 * 10**9
    o.ULongProp = check
    assert o.ULongProp == check, (
        f"Property value wrong - got {o.ULongProp} (expected {check})"
    )
    TestApplyResult(o.Test, ("Unused", 99), 1)  # A bool function
    TestApplyResult(o.Test, ("Unused", -1), 1)  # A bool function
    TestApplyResult(o.Test, ("Unused", True), 1)  # A bool function
    TestApplyResult(o.Test, ("Unused", 0), 0)
    TestApplyResult(o.Test, ("Unused", False), 0)

    assert o.DoubleString("foo") == "foofoo"

    TestConstant("ULongTest1", 0xFFFFFFFF)
    TestConstant("ULongTest2", 0x7FFFFFFF)
    TestConstant("LongTest1", -0x7FFFFFFF)
    TestConstant("LongTest2", 0x7FFFFFFF)
    TestConstant("UCharTest", 255)
    TestConstant("CharTest", -1)
    # 050222.python.testPyComTest.line323.comment 'Hello World', but the 'r' is the "Registered" sign (\xae)
    TestConstant("StringTest", "Hello Wo\xaeld")

    progress("Checking dates and times")
    # 050223.python.testPyComTest.line327.comment For now *all* times passed must be tz-aware.
    now = win32timezone.now()
    # 050224.python.testPyComTest.line329.comment but conversion to and from a VARIANT loses sub-second...
    now = now.replace(microsecond=0)
    later = now + datetime.timedelta(seconds=1)
    TestApplyResult(o.EarliestDate, (now, later), now)

    # 050225.python.testPyComTest.line334.comment The below used to fail with `ValueError: microsecond must be in 0..999999` - see #1655
    # 050226.python.testPyComTest.line335.comment https://planetcalc.com/7027/ says that float is: Sun, 25 Mar 1951 7:23:49 am
    assert o.MakeDate(18712.308206013888) == datetime.datetime.fromisoformat(
        "1951-03-25 07:23:49+00:00"
    )

    progress("Checking currency")
    # 050227.python.testPyComTest.line341.comment currency.
    pythoncom.__future_currency__ = 1
    assert o.CurrencyProp == 0, f"Expecting 0, got {o.CurrencyProp!r}"
    for val in ("1234.5678", "1234.56", "1234"):
        o.CurrencyProp = decimal.Decimal(val)
        assert o.CurrencyProp == decimal.Decimal(val), f"{val} got {o.CurrencyProp!r}"
    v1 = decimal.Decimal("1234.5678")
    TestApplyResult(o.DoubleCurrency, (v1,), v1 * 2)

    v2 = decimal.Decimal("9012.3456")
    TestApplyResult(o.AddCurrencies, (v1, v2), v1 + v2)

    progress("Checking decimal type")
    assert o.DecimalProp == 0, f"Expecting 0, got {o.DecimalProp!r}"
    for val in (
        "1234",
        "123456789.1234",
        "-987654321.9876",
        "0.1234",
        "-0.1234",
    ):
        o.DecimalProp = decimal.Decimal(val)
        assert o.DecimalProp == decimal.Decimal(val), f"{val} got {o.DecimalProp!r}"
    v1 = decimal.Decimal("1234.5678")
    TestApplyResult(o.DoubleDecimal, (v1,), v1 * 2)

    v2 = decimal.Decimal("654.321")
    TestApplyResult(o.AddDecimals, (v1, v2), v1 + v2)

    TestTrickyTypesWithVariants(o, is_generated)
    progress("Checking win32com.client.VARIANT")
    TestPyVariant(o, is_generated)


def TestTrickyTypesWithVariants(o, is_generated):
    # 050228.python.testPyComTest.line376.comment Test tricky stuff with type handling and generally only works with
    # 050229.python.testPyComTest.line377.comment "generated" support but can be worked around using VARIANT.
    if is_generated:
        got = o.TestByRefVariant(2)
    else:
        v = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, 2)
        o.TestByRefVariant(v)
        got = v.value
    assert got == 4, "TestByRefVariant failed"

    if is_generated:
        got = o.TestByRefString("Foo")
    else:
        v = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, "Foo")
        o.TestByRefString(v)
        got = v.value
    assert got == "FooFoo", "TestByRefString failed"

    # 050230.python.testPyComTest.line394.comment check we can pass ints as a VT_UI1
    vals = [1, 2, 3, 4]
    if is_generated:
        arg = vals
    else:
        arg = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_UI1, vals)
    TestApplyResult(o.SetBinSafeArray, (arg,), len(vals))

    # 050231.python.testPyComTest.line402.comment safearrays of doubles and floats
    vals = [0, 1.1, 2.2, 3.3]
    if is_generated:
        arg = vals
    else:
        arg = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, vals)
    TestApplyResult(o.SetDoubleSafeArray, (arg,), len(vals))

    if is_generated:
        arg = vals
    else:
        arg = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R4, vals)
    TestApplyResult(o.SetFloatSafeArray, (arg,), len(vals))

    vals = [1.1, 2.2, 3.3, 4.4]
    expected = (1.1 * 2, 2.2 * 2, 3.3 * 2, 4.4 * 2)
    if is_generated:
        TestApplyResult(o.ChangeDoubleSafeArray, (vals,), expected)
    else:
        arg = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_ARRAY | pythoncom.VT_R8, vals)
        o.ChangeDoubleSafeArray(arg)
        assert arg.value == expected, "ChangeDoubleSafeArray got the wrong value"

    if is_generated:
        got = o.DoubleInOutString("foo")
    else:
        v = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, "foo")
        o.DoubleInOutString(v)
        got = v.value
    assert got == "foofoo", got

    val = decimal.Decimal("1234.5678")
    if is_generated:
        got = o.DoubleCurrencyByVal(val)
    else:
        v = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_CY, val)
        o.DoubleCurrencyByVal(v)
        got = v.value
    assert got == val * 2

    val = decimal.Decimal("123456789.1234")
    if is_generated:
        got = o.DoubleDecimalByVal(val)
    else:
        v = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_DECIMAL, val)
        o.DoubleDecimalByVal(v)
        got = v.value
    assert got == val * 2


def TestDynamic():
    progress("Testing Dynamic")
    import win32com.client.dynamic

    o = win32com.client.dynamic.DumbDispatch("PyCOMTest.PyCOMTest")
    TestCommon(o, False)

    counter = win32com.client.dynamic.DumbDispatch("PyCOMTest.SimpleCounter")
    TestCounter(counter, False)

    # 050232.python.testPyComTest.line462.comment Dynamic doesn't know this should be an int, so we get a COM
    # 050233.python.testPyComTest.line463.comment TypeMismatch error.
    try:
        check_get_set_raises(ValueError, o.GetSetInt, "foo")
        raise AssertionError("no exception raised")
    except pythoncom.com_error as exc:
        if exc.hresult != winerror.DISP_E_TYPEMISMATCH:
            raise

    arg1 = VARIANT(pythoncom.VT_R4 | pythoncom.VT_BYREF, 2.0)
    arg2 = VARIANT(pythoncom.VT_BOOL | pythoncom.VT_BYREF, True)
    arg3 = VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 4)
    o.TestInOut(arg1, arg2, arg3)
    assert arg1.value == 4.0, arg1
    assert arg2.value == False
    assert arg3.value == 8

    # 050234.python.testPyComTest.line479.comment damn - props with params don't work for dynamic objects :(
    # 050235.python.testPyComTest.line480.comment o.SetParamProp(0, 1)
    # 050236.python.testPyComTest.line481.comment assert o.ParamProp(0) == 1, o.paramProp(0)


def TestStructByref(o, r):
    progress("Checking struct byref as [ in, out ] parameter")
    mod_r = o.ModifyStruct(r)
    # 050237.python.testPyComTest.line487.comment If 'TestStruct1' was registered as an instantiable subclass
    # 050238.python.testPyComTest.line488.comment of pythoncom.com_record, the return value should have this type.
    if isinstance(r, TestStruct1):
        assert type(mod_r) is TestStruct1
    else:
        assert type(mod_r) is pythoncom.com_record
    # 050239.python.testPyComTest.line493.comment We expect the input value to stay unchanged
    assert r.int_value == 99 and str(r.str_value) == "Hello from C++"
    # 050240.python.testPyComTest.line495.comment and the return value to reflect the modifications performed on the COM server side
    assert (
        mod_r.int_value == 100
        and str(mod_r.str_value) == "Nothing is as constant as change"
    )


def TestArrayOfStructs(o, test_rec):
    progress("Testing struct with SAFEARRAY(VT_RECORD) fields.")
    rec_list = []
    for i in range(3):
        # 050241.python.testPyComTest.line506.comment If 'ArrayOfStructsTestStruct' and 'TestStruct1' were registered as instantiable
        # 050242.python.testPyComTest.line507.comment subclasses of pythoncom.com_record, we expect to work with these types.
        if isinstance(test_rec, ArrayOfStructsTestStruct):
            rec = TestStruct1()
            assert type(rec) is TestStruct1
        else:
            rec = Record("TestStruct1", o)
            assert type(rec) is pythoncom.com_record
        rec.str_value = "This is record number"
        rec.int_value = i + 1
        rec_list.append(rec)
    test_rec.array_of_records = rec_list
    test_rec.rec_count = i + 1
    assert o.VerifyArrayOfStructs(test_rec)


def TestGenerated():
    # 050243.python.testPyComTest.line523.comment Create an instance of the server.
    from win32com.client.gencache import EnsureDispatch

    o = EnsureDispatch("PyCOMTest.PyCOMTest")
    TestCommon(o, True)

    counter = EnsureDispatch("PyCOMTest.SimpleCounter")
    TestCounter(counter, True)

    # 050244.python.testPyComTest.line532.comment This dance lets us get a CoClass even though it's not explicitly registered.
    # 050245.python.testPyComTest.line533.comment This is `CoPyComTest`
    from win32com.client.CLSIDToClass import GetClass

    coclass_o = GetClass("{8EE0C520-5605-11D0-AE5F-CADD4C000000}")()
    TestCommon(coclass_o, True)

    # 050246.python.testPyComTest.line539.comment Test the regression reported in #1753
    assert bool(coclass_o)

    # 050247.python.testPyComTest.line542.comment This is `CoSimpleCounter` and the counter tests should work.
    coclass = GetClass("{B88DD310-BAE8-11D0-AE86-76F2C1000000}")()
    TestCounter(coclass, True)

    # 050248.python.testPyComTest.line546.comment Test plain pythoncom.com_record structs.
    progress("Testing baseclass pythoncom.com_record structs.")
    r = o.GetStruct()
    assert type(r) is pythoncom.com_record
    TestStructByref(o, r)
    test_rec = Record("TestStruct2", o)
    assert type(test_rec) is pythoncom.com_record
    TestArrayOfStructs(o, test_rec)

    progress("Testing registration of pythoncom.com_record subclasses.")
    # 050249.python.testPyComTest.line556.comment Instantiating a pythoncom.com_record subclass, which has proper GUID attributes,
    # 050250.python.testPyComTest.line557.comment does raise a TypeError, as long as we have not registered it.
    try:
        r_sub = TestStruct1()
    except TypeError:
        pass
    except Exception as e:
        raise AssertionError from e
    else:
        raise AssertionError
    # 050251.python.testPyComTest.line566.comment Register the subclasses in pythoncom.
    register_record_class(TestStruct1)
    register_record_class(ArrayOfStructsTestStruct)
    # 050252.python.testPyComTest.line569.comment Now the type of the instance is the registered subclass.
    r_sub = TestStruct1()
    assert type(r_sub) is TestStruct1
    # 050253.python.testPyComTest.line572.comment Now also the 'Record' factory function returns an instance of the registered subtype.
    r_sub = Record("TestStruct1", o)
    assert type(r_sub) is TestStruct1
    # 050254.python.testPyComTest.line575.comment It should not be possible to register multiple classes with the same GUID, e.g.
    # 050255.python.testPyComTest.line576.comment 'TestStruct2' has the same GUID class attribute value as 'ArrayOfStructsTestStruct'.
    check_get_set_raises(ValueError, register_record_class, TestStruct2)
    # 050256.python.testPyComTest.line578.comment Also registering a class with a GUID that is not in the TypeLibrary should fail.
    check_get_set_raises(TypeError, register_record_class, NotInTypeLibraryTestStruct)

    # 050257.python.testPyComTest.line581.comment Perform the 'Byref' and 'ArrayOfStruct tests using the registered subclasses.
    progress("Testing subclasses of pythoncom.com_record.")
    r = o.GetStruct()
    # 050258.python.testPyComTest.line584.comment After 'TestStruct1' was registered as an instantiable subclass
    # 050259.python.testPyComTest.line585.comment of pythoncom.com_record, the return value should have this type.
    assert type(r) is TestStruct1
    TestStructByref(o, r)
    test_rec = ArrayOfStructsTestStruct()
    assert type(test_rec) is ArrayOfStructsTestStruct
    TestArrayOfStructs(o, test_rec)

    # 050260.python.testPyComTest.line592.comment Test initialization of registered pythoncom.com_record subclasses.
    progress("Testing initialization of pythoncom.com_record subclasses.")
    buf = o.GetStruct().__reduce__()[1][5]
    test_rec = TestStruct1(buf)
    assert test_rec.int_value == 99 and str(test_rec.str_value) == "Hello from C++"

    # 050261.python.testPyComTest.line598.comment XXX - this is failing in dynamic tests, but should work fine.
    i1, i2 = o.GetMultipleInterfaces()
    # 050262.python.testPyComTest.line600.comment Yay - is now an instance returned!
    assert isinstance(i1, DispatchBaseClass) and isinstance(i2, DispatchBaseClass), (
        f"GetMultipleInterfaces did not return instances - got '{i1}', '{i2}'"
    )
    del i1
    del i2

    # 050263.python.testPyComTest.line607.comment Generated knows to only pass a 32bit int, so should fail.
    check_get_set_raises(OverflowError, o.GetSetInt, 0x80000000)
    check_get_set_raises(OverflowError, o.GetSetLong, 0x80000000)

    # 050264.python.testPyComTest.line611.comment Generated knows this should be an int, so raises ValueError
    check_get_set_raises(ValueError, o.GetSetInt, "foo")
    check_get_set_raises(ValueError, o.GetSetLong, "foo")

    # 050265.python.testPyComTest.line615.comment Pass some non-sequence objects to our array decoder, and watch it fail.
    try:
        o.SetVariantSafeArray("foo")
        raise AssertionError("Expected a type error")
    except TypeError:
        pass
    try:
        o.SetVariantSafeArray(666)
        raise AssertionError("Expected a type error")
    except TypeError:
        pass

    o.GetSimpleSafeArray(None)
    TestApplyResult(o.GetSimpleSafeArray, (None,), tuple(range(10)))
    resultCheck = tuple(range(5)), tuple(range(10)), tuple(range(20))
    TestApplyResult(o.GetSafeArrays, (None, None, None), resultCheck)

    l = []
    TestApplyResult(o.SetIntSafeArray, (l,), len(l))
    l = [1, 2, 3, 4]
    TestApplyResult(o.SetIntSafeArray, (l,), len(l))
    ll = [1, 2, 3, 0x100000000]
    TestApplyResult(o.SetLongLongSafeArray, (ll,), len(ll))
    TestApplyResult(o.SetULongLongSafeArray, (ll,), len(ll))

    # 050266.python.testPyComTest.line640.comment check freeing of safe arrays
    mem_before = GetMemoryUsage()
    o.GetByteArray(50 * 1024 * 1024)
    mem_after = GetMemoryUsage()
    delta = mem_after - mem_before
    assert delta < 1024 * 1024, f"Memory not freed - delta {delta / (1024 * 1024)} MB"

    # 050267.python.testPyComTest.line647.comment Tell the server to do what it does!
    TestApplyResult(o.Test2, (constants.Attr2,), constants.Attr2)
    TestApplyResult(o.Test3, (constants.Attr2,), constants.Attr2)
    TestApplyResult(o.Test4, (constants.Attr2,), constants.Attr2)
    TestApplyResult(o.Test5, (constants.Attr2,), constants.Attr2)

    TestApplyResult(o.Test6, (constants.WideAttr1,), constants.WideAttr1)
    TestApplyResult(o.Test6, (constants.WideAttr2,), constants.WideAttr2)
    TestApplyResult(o.Test6, (constants.WideAttr3,), constants.WideAttr3)
    TestApplyResult(o.Test6, (constants.WideAttr4,), constants.WideAttr4)
    TestApplyResult(o.Test6, (constants.WideAttr5,), constants.WideAttr5)

    TestApplyResult(o.TestInOut, (2.0, True, 4), (4.0, False, 8))

    o.SetParamProp(0, 1)
    assert o.ParamProp(0) == 1, o.paramProp(0)

    # 050268.python.testPyComTest.line664.comment Make sure CastTo works - even though it is only casting it to itself!
    o2 = CastTo(o, "IPyCOMTest")
    assert o == o2, "CastTo should have returned the same object"

    # 050269.python.testPyComTest.line668.comment Do the connection point thing...
    # 050270.python.testPyComTest.line669.comment Create a connection object.
    progress("Testing connection points")
    o2 = win32com.client.DispatchWithEvents(o, RandomEventHandler)
    TestEvents(o2, o2)
    # 050271.python.testPyComTest.line673.comment and a plain "WithEvents".
    handler = win32com.client.WithEvents(o, RandomEventHandler)
    TestEvents(o, handler)
    progress("Finished generated .py test.")


def TestEvents(o, handler):
    sessions = []
    handler._Init()
    try:
        for i in range(3):
            session = o.Start()
            sessions.append(session)
        time.sleep(0.5)
    finally:
        # 050272.python.testPyComTest.line688.comment Stop the servers
        for session in sessions:
            o.Stop(session)
        handler._DumpFireds()
        handler.close()


def _TestPyVariant(o, is_generated, val, checker=None):
    if is_generated:
        vt, got = o.GetVariantAndType(val)
    else:
        # 050273.python.testPyComTest.line699.comment Gotta supply all 3 args with the last 2 being explicit variants to
        # 050274.python.testPyComTest.line700.comment get the byref behaviour.
        var_vt = VARIANT(pythoncom.VT_UI2 | pythoncom.VT_BYREF, 0)
        var_result = VARIANT(pythoncom.VT_VARIANT | pythoncom.VT_BYREF, 0)
        o.GetVariantAndType(val, var_vt, var_result)
        vt = var_vt.value
        got = var_result.value
    if checker is not None:
        checker(got)
        return
    # 050275.python.testPyComTest.line709.comment default checking.
    assert vt == val.varianttype, (vt, val.varianttype)
    # 050276.python.testPyComTest.line711.comment Handle our safe-array test - if the passed value is a list of variants,
    # 050277.python.testPyComTest.line712.comment compare against the actual values.
    if isinstance(val.value, (tuple, list)):
        check = [v.value if isinstance(v, VARIANT) else v for v in val.value]
        # 050278.python.testPyComTest.line715.comment pythoncom always returns arrays as tuples.
        got = list(got)
    else:
        check = val.value
    assert type(check) == type(got), (type(check), type(got))
    assert check == got, (check, got)


def _TestPyVariantFails(o, is_generated, val, exc):
    try:
        _TestPyVariant(o, is_generated, val)
        raise AssertionError(f"Setting {val!r} didn't raise {exc}")
    except exc:
        pass


def TestPyVariant(o, is_generated):
    _TestPyVariant(o, is_generated, VARIANT(pythoncom.VT_UI1, 1))
    _TestPyVariant(
        o, is_generated, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_UI4, [1, 2, 3])
    )
    _TestPyVariant(o, is_generated, VARIANT(pythoncom.VT_BSTR, "hello"))
    _TestPyVariant(
        o,
        is_generated,
        VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR, ["hello", "there"]),
    )

    def check_dispatch(got):
        assert isinstance(got._oleobj_, pythoncom.TypeIIDs[pythoncom.IID_IDispatch])

    _TestPyVariant(o, is_generated, VARIANT(pythoncom.VT_DISPATCH, o), check_dispatch)
    _TestPyVariant(
        o, is_generated, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [o])
    )
    # 050279.python.testPyComTest.line750.comment an array of variants each with a specific type.
    v = VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_VARIANT,
        [
            VARIANT(pythoncom.VT_UI4, 1),
            VARIANT(pythoncom.VT_UI4, 2),
            VARIANT(pythoncom.VT_UI4, 3),
        ],
    )
    _TestPyVariant(o, is_generated, v)

    # 050280.python.testPyComTest.line761.comment and failures
    _TestPyVariantFails(o, is_generated, VARIANT(pythoncom.VT_UI1, "foo"), ValueError)


def TestCounter(counter, bIsGenerated):
    # 050281.python.testPyComTest.line766.comment Test random access into container
    progress(f"Testing counter {counter!r}")
    import random

    for i in range(50):
        num = int(random.random() * len(counter))
        try:
            # 050282.python.testPyComTest.line773.comment XXX - this appears broken by commit 08a14d4deb374eaa06378509cf44078ad467b9dc -
            # 050283.python.testPyComTest.line774.comment We shouldn't need to do generated differently than dynamic.
            if bIsGenerated:
                ret = counter.Item(num + 1)
            else:
                ret = counter[num]
            assert ret == num + 1, (
                f"Random access into element {num} failed - return was {ret!r}"
            )
        except IndexError:
            raise AssertionError(f"** IndexError accessing collection element {num}")

    num = 0
    if bIsGenerated:
        counter.SetTestProperty(1)
        counter.TestProperty = 1  # Note this has a second, default arg.
        counter.SetTestProperty(1, 2)
        assert counter.TestPropertyWithDef == 0, "Unexpected property set value!"
        assert counter.TestPropertyNoDef(1) == 1, "Unexpected property set value!"
    else:
        pass
        # 050285.python.testPyComTest.line794.comment counter.TestProperty = 1

    counter.LBound = 1
    counter.UBound = 10
    if counter.LBound != 1 or counter.UBound != 10:
        print("** Error - counter did not keep its properties")

    if bIsGenerated:
        bounds = counter.GetBounds()
        assert bounds[0] == 1 and bounds[1] == 10, (
            "** Error - counter did not give the same properties back"
        )
        counter.SetBounds(bounds[0], bounds[1])

    for item in counter:
        num += 1
    assert num == len(counter), (
        "*** Length of counter and loop iterations don't match ***"
    )
    assert num == 10, "*** Unexpected number of loop iterations ***"

    try:
        counter = iter(counter)._iter_.Clone()  # Test Clone() and enum directly
    except AttributeError:
        # 050287.python.testPyComTest.line818.comment *sob* - sometimes this is a real iterator and sometimes not :/
        progress("Finished testing counter (but skipped the iterator stuff")
        return
    counter.Reset()
    num = 0
    for item in counter:
        num += 1
    assert num == 10, f"*** Unexpected number of loop iterations - got {num} ***"
    progress("Finished testing counter")


def TestLocalVTable(ob):
    # 050288.python.testPyComTest.line830.comment Python doesn't fully implement this interface.
    assert ob.DoubleString("foo") == "foofoo", "couldn't foofoo"


# 050289.python.testPyComTest.line834.comment ##############################
# 050290.python.testPyComTest.line835.comment #
# 050291.python.testPyComTest.line836.comment # Some vtable tests of the interface
# 050292.python.testPyComTest.line837.comment #
def TestVTable(clsctx=pythoncom.CLSCTX_ALL):
    # 050293.python.testPyComTest.line839.comment Any vtable interfaces marked as dual *should* be able to be
    # 050294.python.testPyComTest.line840.comment correctly implemented as IDispatch.
    ob = win32com.client.Dispatch("Python.Test.PyCOMTest")
    TestLocalVTable(ob)
    # 050295.python.testPyComTest.line843.comment Now test it via vtable - use some C++ code to help here as Python can't do it directly yet.
    tester = win32com.client.Dispatch("PyCOMTest.PyCOMTest")
    testee = pythoncom.CoCreateInstance(
        "Python.Test.PyCOMTest", None, clsctx, pythoncom.IID_IUnknown
    )
    # 050296.python.testPyComTest.line848.comment check we fail gracefully with None passed.
    try:
        tester.TestMyInterface(None)
    except pythoncom.com_error as details:
        pass
    # 050297.python.testPyComTest.line853.comment and a real object.
    tester.TestMyInterface(testee)


def TestVTable2():
    # 050298.python.testPyComTest.line858.comment We once crashed creating our object with the native interface as
    # 050299.python.testPyComTest.line859.comment the first IID specified.  We must do it _after_ the tests, so that
    # 050300.python.testPyComTest.line860.comment Python has already had the gateway registered from last run.
    ob = win32com.client.Dispatch("Python.Test.PyCOMTest")
    iid = pythoncom.InterfaceNames["IPyCOMTest"]
    clsid = "Python.Test.PyCOMTest"
    clsctx = pythoncom.CLSCTX_SERVER
    try:
        testee = pythoncom.CoCreateInstance(clsid, None, clsctx, iid)
    except TypeError:
        # 050301.python.testPyComTest.line868.comment Python can't actually _use_ this interface yet, so this is
        # 050302.python.testPyComTest.line869.comment "expected".  Any COM error is not.
        pass


def TestVTableMI():
    clsctx = pythoncom.CLSCTX_SERVER
    ob = pythoncom.CoCreateInstance(
        "Python.Test.PyCOMTestMI", None, clsctx, pythoncom.IID_IUnknown
    )
    # 050303.python.testPyComTest.line878.comment This inherits from IStream.
    ob.QueryInterface(pythoncom.IID_IStream)
    # 050304.python.testPyComTest.line880.comment This implements IStorage, specifying the IID as a string
    ob.QueryInterface(pythoncom.IID_IStorage)
    # 050305.python.testPyComTest.line882.comment IDispatch should always work
    ob.QueryInterface(pythoncom.IID_IDispatch)

    iid = pythoncom.InterfaceNames["IPyCOMTest"]
    try:
        ob.QueryInterface(iid)
    except TypeError:
        # 050306.python.testPyComTest.line889.comment Python can't actually _use_ this interface yet, so this is
        # 050307.python.testPyComTest.line890.comment "expected".  Any COM error is not.
        pass


def TestQueryInterface(long_lived_server=0, iterations=5):
    tester = win32com.client.Dispatch("PyCOMTest.PyCOMTest")
    if long_lived_server:
        # 050308.python.testPyComTest.line897.comment Create a local server
        t0 = win32com.client.Dispatch(
            "Python.Test.PyCOMTest", clsctx=pythoncom.CLSCTX_LOCAL_SERVER
        )
    # 050309.python.testPyComTest.line901.comment Request custom interfaces a number of times
    prompt = [
        "Testing QueryInterface without long-lived local-server #%d of %d...",
        "Testing QueryInterface with long-lived local-server #%d of %d...",
    ]

    for i in range(iterations):
        progress(prompt[long_lived_server != 0] % (i + 1, iterations))
        tester.TestQueryInterface()


class Tester(win32com.test.util.TestCase):
    def testVTableInProc(self):
        # 050310.python.testPyComTest.line914.comment We used to crash running this the second time - do it a few times
        for i in range(3):
            progress("Testing VTables in-process #%d..." % (i + 1))
            TestVTable(pythoncom.CLSCTX_INPROC_SERVER)

    def testVTableLocalServer(self):
        for i in range(3):
            progress("Testing VTables out-of-process #%d..." % (i + 1))
            TestVTable(pythoncom.CLSCTX_LOCAL_SERVER)

    def testVTable2(self):
        for i in range(3):
            TestVTable2()

    def testVTableMI(self):
        for i in range(3):
            TestVTableMI()

    def testMultiQueryInterface(self):
        TestQueryInterface(0, 6)
        # 050311.python.testPyComTest.line934.comment When we use the custom interface in the presence of a long-lived
        # 050312.python.testPyComTest.line935.comment local server, i.e. a local server that is already running when
        # 050313.python.testPyComTest.line936.comment we request an instance of our COM object, and remains afterwards,
        # 050314.python.testPyComTest.line937.comment then after repeated requests to create an instance of our object
        # 050315.python.testPyComTest.line938.comment the custom interface disappears -- i.e. QueryInterface fails with
        # 050316.python.testPyComTest.line939.comment E_NOINTERFACE. Set the upper range of the following test to 2 to
        # 050317.python.testPyComTest.line940.comment pass this test, i.e. TestQueryInterface(1,2)
        TestQueryInterface(1, 6)

    def testDynamic(self):
        TestDynamic()

    def testGenerated(self):
        TestGenerated()


if __name__ == "__main__":
    # 050318.python.testPyComTest.line951.comment XXX - todo - Complete hack to crank threading support.
    # 050319.python.testPyComTest.line952.comment Should NOT be necessary
    def NullThreadFunc():
        pass

    import _thread

    _thread.start_new(NullThreadFunc, ())

    if "-v" in sys.argv:
        verbose = 1

    win32com.test.util.testmain()
