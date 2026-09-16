# 050409.python.testvb.line1.comment Test code for a VB Program.
# 050410.python.testvb.line2.comment
# 050411.python.testvb.line3.comment This requires the PythonCOM VB Test Harness.
# 050412.python.testvb.line4.comment

import traceback
from collections.abc import Callable

import pythoncom
import win32com.client
import win32com.client.dynamic
import win32com.client.gencache
import winerror
from win32com.server.util import wrap
from win32com.test import util

# 050413.python.testvb.line17.comment for debugging
useDispatcher = None
# 050414.python.testvb.line19.comment import win32com.server.dispatcher
# 050415.python.testvb.line20.comment useDispatcher = win32com.server.dispatcher.DefaultDebugDispatcher


# 050416.python.testvb.line23.comment Set up a COM object that VB will do some callbacks on.  This is used
# 050417.python.testvb.line24.comment to test byref params for gateway IDispatch.
class TestObject:
    _public_methods_ = [
        "CallbackVoidOneByRef",
        "CallbackResultOneByRef",
        "CallbackVoidTwoByRef",
        "CallbackString",
        "CallbackResultOneByRefButReturnNone",
        "CallbackVoidOneByRefButReturnNone",
        "CallbackArrayResult",
        "CallbackArrayResultOneArrayByRef",
        "CallbackArrayResultWrongSize",
    ]

    def CallbackVoidOneByRef(self, intVal):
        return intVal + 1

    def CallbackResultOneByRef(self, intVal):
        return intVal, intVal + 1

    def CallbackVoidTwoByRef(self, int1, int2):
        return int1 + int2, int1 - int2

    def CallbackString(self, strVal):
        return 0, strVal + " has visited Python"

    def CallbackArrayResult(self, arrayVal):
        ret = []
        for i in arrayVal:
            ret.append(i + 1)
        # 050418.python.testvb.line54.comment returning as a list forces it be processed as a single result
        # 050419.python.testvb.line55.comment (rather than a tuple, where it may be interpreted as
        # 050420.python.testvb.line56.comment multiple results for byref unpacking)
        return ret

    def CallbackArrayResultWrongSize(self, arrayVal):
        return list(arrayVal[:-1])

    def CallbackArrayResultOneArrayByRef(self, arrayVal):
        ret = []
        for i in arrayVal:
            ret.append(i + 1)
        # 050421.python.testvb.line66.comment See above for list processing.
        return list(arrayVal), ret

    def CallbackResultOneByRefButReturnNone(self, intVal):
        return

    def CallbackVoidOneByRefButReturnNone(self, intVal):
        return


def TestVB(vbtest, bUseGenerated):
    vbtest.LongProperty = -1
    assert vbtest.LongProperty == -1, "Could not set the long property correctly."
    vbtest.IntProperty = 10
    assert vbtest.IntProperty == 10, "Could not set the integer property correctly."
    vbtest.VariantProperty = 10
    assert vbtest.VariantProperty == 10, (
        "Could not set the variant integer property correctly."
    )
    vbtest.VariantProperty = memoryview(b"raw\0data")
    assert vbtest.VariantProperty == memoryview(b"raw\0data"), (
        "Could not set the variant buffer property correctly."
    )
    vbtest.StringProperty = "Hello from Python"
    assert vbtest.StringProperty == "Hello from Python", (
        "Could not set the string property correctly."
    )
    vbtest.VariantProperty = "Hello from Python"
    assert vbtest.VariantProperty == "Hello from Python", (
        "Could not set the variant string property correctly."
    )
    vbtest.VariantProperty = (1.0, 2.0, 3.0)
    assert vbtest.VariantProperty == (1.0, 2.0, 3.0), (
        f"Could not set the variant property to an array of floats correctly - '{vbtest.VariantProperty}'."
    )

    TestArrays(vbtest, bUseGenerated)
    TestStructs(vbtest)
    TestCollections(vbtest)

    assert vbtest.TakeByValObject(vbtest) == vbtest

    # 050422.python.testvb.line108.comment Python doesn't support PUTREF properties without a typeref
    # 050423.python.testvb.line109.comment (although we could)
    if bUseGenerated:
        ob = vbtest.TakeByRefObject(vbtest)
        assert ob[0] == vbtest and ob[1] == vbtest

        # 050424.python.testvb.line114.comment A property that only has PUTREF defined.
        vbtest.VariantPutref = vbtest
        assert vbtest.VariantPutref._oleobj_ == vbtest._oleobj_, (
            "Could not set the VariantPutref property correctly."
        )
        # 050425.python.testvb.line119.comment Can't test further types for this VariantPutref, as only
        # 050426.python.testvb.line120.comment COM objects can be stored ByRef.

        # 050427.python.testvb.line122.comment A "set" type property - only works for generated.
        # 050428.python.testvb.line123.comment VB recognizes a collection via a few "private" interfaces that we
        # 050429.python.testvb.line124.comment could later build support in for.
        # 050430.python.testvb.line125.comment vbtest.CollectionProperty = NewCollection((1, 2, "3", "Four"))
        # 050431.python.testvb.line126.comment assert vbtest.CollectionProperty == (
        # 050432.python.testvb.line127.comment 1, 2, "3", "Four",
        # 050433.python.testvb.line128.comment ), f"Could not set the Collection property correctly - got back {vbtest.CollectionProperty}"

        # 050434.python.testvb.line130.comment These are sub's that have a single byref param
        # 050435.python.testvb.line131.comment Result should be just the byref.
        assert vbtest.IncrementIntegerParam(1) == 2, "Could not pass an integer byref"

        # 050436.python.testvb.line134.comment Sigh - we can't have *both* "ommited byref" and optional args
        # 050437.python.testvb.line135.comment We really have to opt that args nominated as optional work as optional
        # 050438.python.testvb.line136.comment rather than simply all byrefs working as optional.
        # 050439.python.testvb.line137.comment assert vbtest.IncrementIntegerParam() == 1, "Could not pass an omitted integer byref"

        assert vbtest.IncrementVariantParam(1) == 2, (
            f"Could not pass an int VARIANT byref: {vbtest.IncrementVariantParam(1)}"
        )
        assert vbtest.IncrementVariantParam(1.5) == 2.5, (
            "Could not pass a float VARIANT byref"
        )

        # 050440.python.testvb.line146.comment Can't test IncrementVariantParam with the param omitted as it
        # 050441.python.testvb.line147.comment it not declared in the VB code as "Optional"
        callback_ob = wrap(TestObject(), useDispatcher=useDispatcher)
        vbtest.DoSomeCallbacks(callback_ob)

    ret = vbtest.PassIntByVal(1)
    assert ret == 2, f"Could not increment the integer - {ret}"

    TestVBInterface(vbtest)
    # 050442.python.testvb.line155.comment Python doesn't support byrefs without some sort of generated support.
    if bUseGenerated:
        # 050443.python.testvb.line157.comment This is a VB function that takes a single byref
        # 050444.python.testvb.line158.comment Hence 2 return values - function and byref.
        ret = vbtest.PassIntByRef(1)
        assert ret == (1, 2), f"Could not increment the integer - {ret}"
        # 050445.python.testvb.line161.comment Check you can leave a byref arg blank.

    # 050446.python.testvb.line163.comment see above
    # 050447.python.testvb.line164.comment ret = vbtest.PassIntByRef()
    # 050448.python.testvb.line165.comment assert ret == (0, 1), f"Could not increment the integer with default arg - {ret}"


def _DoTestCollection(vbtest, col_name, expected):
    # 050449.python.testvb.line169.comment It sucks that some objects allow "Count()", but others "Count"
    def _getcount(ob):
        r = getattr(ob, "Count")
        if isinstance(r, Callable):
            return r()
        return r

    c = getattr(vbtest, col_name)
    check = []
    for item in c:
        check.append(item)
    assert check == list(expected), (
        f"Collection {col_name} didn't have {expected!r} (had {check!r})"
    )
    # 050450.python.testvb.line183.comment Just looping over the collection again works (ie, is restartable)
    check = []
    for item in c:
        check.append(item)
    assert check == list(expected), (
        f"Collection 2nd time around {col_name} didn't have {expected!r} (had {check!r})"
    )

    # 050451.python.testvb.line191.comment Check we can get it via iter()
    i = iter(getattr(vbtest, col_name))
    check = []
    for item in i:
        check.append(item)
    assert check == list(expected), (
        f"Collection iterator {col_name} didn't have {expected!r} 2nd time around (had {check!r})"
    )
    # 050452.python.testvb.line199.comment but an iterator is not restartable
    check = []
    for item in i:
        check.append(item)
    assert check == [], (
        "2nd time around Collection iterator {col_name} wasn't empty (had {check!r})"
    )
    # 050453.python.testvb.line206.comment Check len()==Count()
    c = getattr(vbtest, col_name)
    assert len(c) == _getcount(c), (
        f"Collection {col_name} __len__({len(c)!r}) wasn't==Count({_getcount(c)!r})"
    )
    # 050454.python.testvb.line211.comment Check we can do it with zero based indexing.
    c = getattr(vbtest, col_name)
    check = []
    for i in range(_getcount(c)):
        check.append(c[i])
    assert check == list(expected), (
        f"Collection {col_name} didn't have {expected!r} (had {check!r})"
    )

    # 050455.python.testvb.line220.comment Check we can do it with our old "Skip/Next" methods.
    c = getattr(vbtest, col_name)._NewEnum()
    check = []
    while 1:
        n = c.Next()
        if not n:
            break
        check.append(n[0])
    assert check == list(expected), (
        f"Collection {col_name} didn't have {expected!r} (had {check!r})"
    )


def TestCollections(vbtest):
    _DoTestCollection(vbtest, "CollectionProperty", [1, "Two", "3"])
    # 050456.python.testvb.line235.comment zero based indexing works for simple VB collections.
    assert vbtest.CollectionProperty[0] == 1, (
        "The CollectionProperty[0] element was not the default value"
    )

    _DoTestCollection(vbtest, "EnumerableCollectionProperty", [])
    vbtest.EnumerableCollectionProperty.Add(1)
    vbtest.EnumerableCollectionProperty.Add("Two")
    vbtest.EnumerableCollectionProperty.Add("3")
    _DoTestCollection(vbtest, "EnumerableCollectionProperty", [1, "Two", "3"])


def _DoTestArray(vbtest, data, expected_exception=None):
    try:
        vbtest.ArrayProperty = data
        assert expected_exception is None, f"Expected '{expected_exception}'"
    except expected_exception:
        return
    got = vbtest.ArrayProperty
    assert got == data, (
        f"Could not set the array data correctly - got {got!r}, expected {data!r}"
    )


def TestArrays(vbtest, bUseGenerated):
    # 050457.python.testvb.line260.comment Try and use a safe array (note that the VB code has this declared as a VARIANT
    # 050458.python.testvb.line261.comment and I can't work out how to force it to use native arrays!
    # 050459.python.testvb.line262.comment (NOTE Python will convert incoming arrays to tuples, so we pass a tuple, even tho
    # 050460.python.testvb.line263.comment a list works fine - just makes it easier for us to compare the result!
    # 050461.python.testvb.line264.comment Empty array
    _DoTestArray(vbtest, ())
    # 050462.python.testvb.line266.comment Empty child array
    _DoTestArray(vbtest, ((), ()))
    # 050463.python.testvb.line268.comment ints
    _DoTestArray(vbtest, tuple(range(1, 100)))
    # 050464.python.testvb.line270.comment Floats
    _DoTestArray(vbtest, (1.0, 2.0, 3.0))
    # 050465.python.testvb.line272.comment Strings.
    _DoTestArray(vbtest, tuple("Hello from Python".split()))
    # 050466.python.testvb.line274.comment Date and Time?
    # 050467.python.testvb.line275.comment COM objects.
    _DoTestArray(vbtest, (vbtest, vbtest))
    # 050468.python.testvb.line277.comment Mixed
    _DoTestArray(vbtest, (1, 2.0, "3"))
    # 050469.python.testvb.line279.comment Array alements containing other arrays
    _DoTestArray(vbtest, (1, (vbtest, vbtest), ("3", "4")))
    # 050470.python.testvb.line281.comment Multi-dimensional
    _DoTestArray(vbtest, (((1, 2, 3), (4, 5, 6))))
    _DoTestArray(vbtest, (((vbtest, vbtest, vbtest), (vbtest, vbtest, vbtest))))
    # 050471.python.testvb.line284.comment Another dimension!
    arrayData = (((1, 2), (3, 4), (5, 6)), ((7, 8), (9, 10), (11, 12)))
    arrayData = (
        ((vbtest, vbtest), (vbtest, vbtest), (vbtest, vbtest)),
        ((vbtest, vbtest), (vbtest, vbtest), (vbtest, vbtest)),
    )
    _DoTestArray(vbtest, arrayData)

    # 050472.python.testvb.line292.comment Check that when a '__getitem__ that fails' object is the first item
    # 050473.python.testvb.line293.comment in the structure, we don't mistake it for a sequence.
    _DoTestArray(vbtest, (vbtest, 2.0, "3"))
    _DoTestArray(vbtest, (1, 2.0, vbtest))

    # 050474.python.testvb.line297.comment Pass arbitrarily sized arrays - these used to fail, but thanks to
    # 050475.python.testvb.line298.comment Stefan Schukat, they now work!
    expected_exception = None
    arrayData = (((1, 2, 1), (3, 4), (5, 6)), ((7, 8), (9, 10), (11, 12)))
    _DoTestArray(vbtest, arrayData, expected_exception)
    arrayData = (((vbtest, vbtest),), ((vbtest,),))
    _DoTestArray(vbtest, arrayData, expected_exception)
    # 050476.python.testvb.line304.comment Pass bad data - last item wrong size
    arrayData = (((1, 2), (3, 4), (5, 6, 8)), ((7, 8), (9, 10), (11, 12)))
    _DoTestArray(vbtest, arrayData, expected_exception)

    # 050477.python.testvb.line308.comment byref safearray results with incorrect size.
    callback_ob = wrap(TestObject(), useDispatcher=useDispatcher)
    print("** Expecting a 'ValueError' exception to be printed next:")
    try:
        vbtest.DoCallbackSafeArraySizeFail(callback_ob)
    except pythoncom.com_error as exc:
        assert exc.excepinfo[1] == "Python COM Server Internal Error", (
            f"Didn't get the correct exception - '{exc}'"
        )

    if bUseGenerated:
        # 050478.python.testvb.line319.comment This one is a bit strange!  The array param is "ByRef", as VB insists.
        # 050479.python.testvb.line320.comment The function itself also _returns_ the arram param.
        # 050480.python.testvb.line321.comment Therefore, Python sees _2_ result values - one for the result,
        # 050481.python.testvb.line322.comment and one for the byref.
        testData = "Mark was here".split()
        resultData, byRefParam = vbtest.PassSAFEARRAY(testData)
        assert testData == list(resultData), (
            f"The safe array data was not what we expected - got {resultData}"
        )
        assert testData == list(byRefParam), (
            f"The safe array data was not what we expected - got {byRefParam}"
        )
        testData = [1.0, 2.0, 3.0]
        resultData, byRefParam = vbtest.PassSAFEARRAYVariant(testData)
        assert testData == list(byRefParam)
        assert testData == list(resultData)
        testData = ["hi", "from", "Python"]
        resultData, byRefParam = vbtest.PassSAFEARRAYVariant(testData)
        assert testData == list(byRefParam), "Expected '{}', got '{}'".format(
            testData,
            list(byRefParam),
        )
        assert testData == list(resultData), "Expected '{}', got '{}'".format(
            testData,
            list(resultData),
        )
        # 050482.python.testvb.line345.comment This time, we just pass Unicode, so the result should compare equal
        testData = [1, 2.0, "3"]
        resultData, byRefParam = vbtest.PassSAFEARRAYVariant(testData)
        assert testData == list(byRefParam)
        assert testData == list(resultData)
    print("Array tests passed")


def TestStructs(vbtest):
    try:
        vbtest.IntProperty = "One"
        raise AssertionError("Should have failed by now")
    except pythoncom.com_error as exc:
        assert exc.hresult == winerror.DISP_E_TYPEMISMATCH, (
            "Expected DISP_E_TYPEMISMATCH"
        )

    s = vbtest.StructProperty
    assert s.int_val == 99 and str(s.str_val) == "hello", (
        "The struct value was not correct"
    )
    s.str_val = "Hi from Python"
    s.int_val = 11
    assert s.int_val == 11 and str(s.str_val) == "Hi from Python", (
        "The struct value didn't persist!"
    )
    assert s.sub_val.int_val == 66 and str(s.sub_val.str_val) == "sub hello", (
        "The sub-struct value was not correct"
    )
    sub = s.sub_val
    sub.int_val = 22
    assert sub.int_val == 22, (
        f"The sub-struct value didn't persist!",
        str(sub.int_val),
    )
    assert s.sub_val.int_val == 22, (
        "The sub-struct value (re-fetched) didn't persist!",
        str(s.sub_val.int_val),
    )
    assert (
        s.sub_val.array_val[0].int_val == 0
        and str(s.sub_val.array_val[0].str_val) == "zero"
    ), ("The array element wasn't correct", str(s.sub_val.array_val[0].int_val))
    s.sub_val.array_val[0].int_val = 99
    s.sub_val.array_val[1].int_val = 66
    assert (
        s.sub_val.array_val[0].int_val == 99 and s.sub_val.array_val[1].int_val == 66
    ), (
        "The array elements didn't persist.",
        str(s.sub_val.array_val[0].int_val),
        str(s.sub_val.array_val[1].int_val),
    )
    # 050483.python.testvb.line397.comment Now pass the struct back to VB
    vbtest.StructProperty = s
    # 050484.python.testvb.line399.comment And get it back again
    s = vbtest.StructProperty
    assert s.int_val == 11 and str(s.str_val) == "Hi from Python", (
        "After sending to VB, the struct value didn't persist!"
    )
    assert s.sub_val.array_val[0].int_val == 99, (
        "After sending to VB, the struct array value didn't persist!"
    )

    # 050485.python.testvb.line408.comment Now do some object equality tests.
    assert s == s
    assert s is not None
    try:
        s < None
        raise AssertionError("Expected type error")
    except TypeError:
        pass
    try:
        None < s
        raise AssertionError("Expected type error")
    except TypeError:
        pass
    assert s != s.sub_val
    import copy

    s2 = copy.copy(s)
    assert s is not s2
    assert s == s2
    s2.int_val = 123
    assert s != s2
    # 050486.python.testvb.line429.comment Make sure everything works with functions
    s2 = vbtest.GetStructFunc()
    assert s == s2
    vbtest.SetStructSub(s2)

    # 050487.python.testvb.line434.comment Create a new structure, and set its elements.
    s = win32com.client.Record("VBStruct", vbtest)
    assert s.int_val == 0, "new struct inst initialized correctly!"
    s.int_val = -1
    vbtest.SetStructSub(s)
    assert vbtest.GetStructFunc().int_val == -1, (
        "new struct didn't make the round trip!"
    )
    # 050488.python.testvb.line442.comment Finally, test stand-alone structure arrays.
    s_array = vbtest.StructArrayProperty
    assert s_array is None, "Expected None from the uninitialized VB array"
    vbtest.MakeStructArrayProperty(3)
    s_array = vbtest.StructArrayProperty
    assert len(s_array) == 3
    for i in range(len(s_array)):
        assert s_array[i].int_val == i
        assert s_array[i].sub_val.int_val == i
        assert s_array[i].sub_val.array_val[0].int_val == i
        assert s_array[i].sub_val.array_val[1].int_val == i + 1
        assert s_array[i].sub_val.array_val[2].int_val == i + 2

    # 050489.python.testvb.line455.comment Some error type checks.
    try:
        s.bad_attribute
        raise AssertionError("Could get a bad attribute")
    except AttributeError:
        pass
    m = s.__members__
    assert (
        m[0] == "int_val"
        and m[1] == "str_val"
        and m[2] == "ob_val"
        and m[3] == "sub_val"
    ), m

    # 050490.python.testvb.line469.comment Test attribute errors.
    try:
        s.foo
        raise AssertionError("Expected attribute error")
    except AttributeError as exc:
        assert "foo" in str(exc), exc

    # 050491.python.testvb.line476.comment test repr - it uses repr() of the sub-objects, so check it matches.
    expected = (
        "com_struct(int_val={!r}, str_val={!r}, ob_val={!r}, sub_val={!r})".format(
            s.int_val,
            s.str_val,
            s.ob_val,
            s.sub_val,
        )
    )
    repr_s = repr(s)
    if repr_s != expected:
        print("Expected repr:", expected)
        print("Actual repr  :", repr_s)
        raise AssertionError("repr() of record object failed")

    print("Struct/Record tests passed")


def TestVBInterface(ob):
    t = ob.GetInterfaceTester(2)
    assert t.getn() == 2, "Initial value wrong"
    t.setn(3)
    assert t.getn() == 3, "New value wrong"


def TestObjectSemantics(ob):
    # 050492.python.testvb.line502.comment a convenient place to test some of our equality semantics
    assert ob == ob._oleobj_
    assert not ob != ob._oleobj_
    # 050493.python.testvb.line505.comment same test again, but lhs and rhs reversed.
    assert ob._oleobj_ == ob
    assert not ob._oleobj_ != ob
    # 050494.python.testvb.line508.comment same tests but against different pointers.  COM identity rules should
    # 050495.python.testvb.line509.comment still ensure all works
    assert ob._oleobj_ == ob._oleobj_.QueryInterface(pythoncom.IID_IUnknown)
    assert not ob._oleobj_ != ob._oleobj_.QueryInterface(pythoncom.IID_IUnknown)

    assert ob._oleobj_ is not None
    assert None != ob._oleobj_
    assert ob is not None
    assert None != ob
    try:
        ob < None
        raise AssertionError("Expected type error")
    except TypeError:
        pass
    try:
        None < ob
        raise AssertionError("Expected type error")
    except TypeError:
        pass

    assert ob._oleobj_.QueryInterface(pythoncom.IID_IUnknown) == ob._oleobj_
    assert not ob._oleobj_.QueryInterface(pythoncom.IID_IUnknown) != ob._oleobj_

    assert ob._oleobj_ == ob._oleobj_.QueryInterface(pythoncom.IID_IDispatch)
    assert not ob._oleobj_ != ob._oleobj_.QueryInterface(pythoncom.IID_IDispatch)

    assert ob._oleobj_.QueryInterface(pythoncom.IID_IDispatch) == ob._oleobj_
    assert not ob._oleobj_.QueryInterface(pythoncom.IID_IDispatch) != ob._oleobj_

    print("Object semantic tests passed")


def DoTestAll():
    o = win32com.client.Dispatch("PyCOMVBTest.Tester")
    TestObjectSemantics(o)
    TestVB(o, 1)

    o = win32com.client.dynamic.DumbDispatch("PyCOMVBTest.Tester")
    TestObjectSemantics(o)
    TestVB(o, 0)


def TestAll():
    # 050496.python.testvb.line551.comment Import the type library for the test module.  Let the 'invalid clsid'
    # 050497.python.testvb.line552.comment exception filter up, where the test runner will treat it as 'skipped'
    win32com.client.gencache.EnsureDispatch("PyCOMVBTest.Tester")

    if not __debug__:
        raise RuntimeError("This must be run in debug mode - we use assert!")
    try:
        DoTestAll()
        print("All tests appear to have worked!")
    except:
        # 050498.python.testvb.line561.comment ?????
        print("TestAll() failed!!")
        traceback.print_exc()
        raise


# 050499.python.testvb.line567.comment Make this test run under our test suite to leak tests etc work
def suite():
    import unittest

    test = util.CapturingFunctionTestCase(TestAll, description="VB tests")
    suite = unittest.TestSuite()
    suite.addTest(test)
    return suite


if __name__ == "__main__":
    util.testmain()
