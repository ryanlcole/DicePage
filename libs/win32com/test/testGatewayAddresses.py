# 050049.python.testGatewayAddresses.line1.comment The purpose of this test is to ensure that the gateways objects
# 050050.python.testGatewayAddresses.line2.comment do the right thing WRT COM rules about object identity etc.

# 050051.python.testGatewayAddresses.line4.comment Also includes a basic test that we support inheritance correctly in
# 050052.python.testGatewayAddresses.line5.comment gateway interfaces.

# 050053.python.testGatewayAddresses.line7.comment For our test, we create an object of type IID_IPersistStorage
# 050054.python.testGatewayAddresses.line8.comment This interface derives from IPersist.
# 050055.python.testGatewayAddresses.line9.comment Therefore, QI's for IID_IDispatch, IID_IUnknown, IID_IPersist and
# 050056.python.testGatewayAddresses.line10.comment IID_IPersistStorage should all return the same gateway object.
# 050057.python.testGatewayAddresses.line11.comment
# 050058.python.testGatewayAddresses.line12.comment In addition, the interface should only need to declare itself as
# 050059.python.testGatewayAddresses.line13.comment using the IPersistStorage interface, and as the gateway derives
# 050060.python.testGatewayAddresses.line14.comment from IPersist, it should automatically be available without declaration.
# 050061.python.testGatewayAddresses.line15.comment
# 050062.python.testGatewayAddresses.line16.comment We also create an object of type IID_I??, and perform a QI for it.
# 050063.python.testGatewayAddresses.line17.comment We then jump through a number of hoops, ensuring that the objects
# 050064.python.testGatewayAddresses.line18.comment returned by the QIs follow all the rules.
# 050065.python.testGatewayAddresses.line19.comment
# 050066.python.testGatewayAddresses.line20.comment Here is Gregs summary of the rules:
# 050067.python.testGatewayAddresses.line21.comment 1) the set of supported interfaces is static and unchanging
# 050068.python.testGatewayAddresses.line22.comment 2) symmetric: if you QI an interface for that interface, it succeeds
# 050069.python.testGatewayAddresses.line23.comment 3) reflexive: if you QI against A for B, the new pointer must succeed
# 050070.python.testGatewayAddresses.line24.comment for a QI for A
# 050071.python.testGatewayAddresses.line25.comment 4) transitive: if you QI for B, then QI that for C, then QI'ing A for C
# 050072.python.testGatewayAddresses.line26.comment must succeed
# 050073.python.testGatewayAddresses.line27.comment
# 050074.python.testGatewayAddresses.line28.comment
# 050075.python.testGatewayAddresses.line29.comment Note that 1) Requires cooperation of the Python programmer.  The rule to keep is:
# 050076.python.testGatewayAddresses.line30.comment "whenever you return an _object_ from _query_interface_(), you must return the
# 050077.python.testGatewayAddresses.line31.comment same object each time for a given IID.  Note that you must return the same
# 050078.python.testGatewayAddresses.line32.comment _wrapped_ object
# 050079.python.testGatewayAddresses.line33.comment you
# 050080.python.testGatewayAddresses.line34.comment The rest are tested here.


import pythoncom
from win32com.server.util import wrap

from .util import CheckClean

numErrors = 0


# 050081.python.testGatewayAddresses.line45.comment Check that the 2 objects both have identical COM pointers.
def CheckSameCOMObject(ob1, ob2):
    addr1 = repr(ob1).split()[6][:-1]
    addr2 = repr(ob2).split()[6][:-1]
    return addr1 == addr2


# 050082.python.testGatewayAddresses.line52.comment Check that the objects conform to COM identity rules.
def CheckObjectIdentity(ob1, ob2):
    u1 = ob1.QueryInterface(pythoncom.IID_IUnknown)
    u2 = ob2.QueryInterface(pythoncom.IID_IUnknown)
    return CheckSameCOMObject(u1, u2)


def FailObjectIdentity(ob1, ob2, when):
    if not CheckObjectIdentity(ob1, ob2):
        global numErrors
        numErrors += 1
        print(f"{when} are not identical ({ob1!r}, {ob2!r})")


class Dummy:
    _public_methods_ = []  # We never attempt to make a call on this object.
    _com_interfaces_ = [pythoncom.IID_IPersistStorage]


class Dummy2:
    _public_methods_ = []  # We never attempt to make a call on this object.
    _com_interfaces_ = [
        pythoncom.IID_IPersistStorage,
        pythoncom.IID_IExternalConnection,
    ]


class DelegatedDummy:
    _public_methods_ = []


class Dummy3:
    _public_methods_ = []  # We never attempt to make a call on this object.
    _com_interfaces_ = [pythoncom.IID_IPersistStorage]

    def _query_interface_(self, iid):
        if iid == pythoncom.IID_IExternalConnection:
            # 050086.python.testGatewayAddresses.line89.comment This will NEVER work - can only wrap the object once!
            return wrap(DelegatedDummy())


def TestGatewayInheritance():
    # 050087.python.testGatewayAddresses.line94.comment By default, wrap() creates and discards a temporary object.
    # 050088.python.testGatewayAddresses.line95.comment This is not necessary, but just the current implementation of wrap.
    # 050089.python.testGatewayAddresses.line96.comment As the object is correctly discarded, it doesn't affect this test.
    o = wrap(Dummy(), pythoncom.IID_IPersistStorage)
    o2 = o.QueryInterface(pythoncom.IID_IUnknown)
    FailObjectIdentity(o, o2, "IID_IPersistStorage->IID_IUnknown")

    o3 = o2.QueryInterface(pythoncom.IID_IDispatch)

    FailObjectIdentity(o2, o3, "IID_IUnknown->IID_IDispatch")
    FailObjectIdentity(o, o3, "IID_IPersistStorage->IID_IDispatch")

    o4 = o3.QueryInterface(pythoncom.IID_IPersistStorage)
    FailObjectIdentity(o, o4, "IID_IPersistStorage->IID_IPersistStorage(2)")
    FailObjectIdentity(o2, o4, "IID_IUnknown->IID_IPersistStorage(2)")
    FailObjectIdentity(o3, o4, "IID_IDispatch->IID_IPersistStorage(2)")

    o5 = o4.QueryInterface(pythoncom.IID_IPersist)
    FailObjectIdentity(o, o5, "IID_IPersistStorage->IID_IPersist")
    FailObjectIdentity(o2, o5, "IID_IUnknown->IID_IPersist")
    FailObjectIdentity(o3, o5, "IID_IDispatch->IID_IPersist")
    FailObjectIdentity(o4, o5, "IID_IPersistStorage(2)->IID_IPersist")


def TestMultiInterface():
    o = wrap(Dummy2(), pythoncom.IID_IPersistStorage)
    o2 = o.QueryInterface(pythoncom.IID_IExternalConnection)

    FailObjectIdentity(o, o2, "IID_IPersistStorage->IID_IExternalConnection")

    # 050090.python.testGatewayAddresses.line124.comment Make the same QI again, to make sure it is stable.
    o22 = o.QueryInterface(pythoncom.IID_IExternalConnection)
    FailObjectIdentity(o, o22, "IID_IPersistStorage->IID_IExternalConnection")
    FailObjectIdentity(
        o2, o22, "IID_IPersistStorage->IID_IExternalConnection (stability)"
    )

    o3 = o2.QueryInterface(pythoncom.IID_IPersistStorage)
    FailObjectIdentity(o2, o3, "IID_IExternalConnection->IID_IPersistStorage")
    FailObjectIdentity(
        o, o3, "IID_IPersistStorage->IID_IExternalConnection->IID_IPersistStorage"
    )


def test():
    TestGatewayInheritance()
    TestMultiInterface()
    if numErrors == 0:
        print("Worked ok")
    else:
        print("There were", numErrors, "errors.")


if __name__ == "__main__":
    test()
    CheckClean()
