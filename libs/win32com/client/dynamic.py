"""Support for dynamic COM client support.

Introduction
 Dynamic COM client support is the ability to use a COM server without
 prior knowledge of the server.  This can be used to talk to almost all
 COM servers, including much of MS Office.

 In general, you should not use this module directly - see below.

Example
 >>> import win32com.client
 >>> xl = win32com.client.Dispatch("Excel.Application")
 # The line above invokes the functionality of this class.
 # xl is now an object we can use to talk to Excel.
 >>> xl.Visible = 1 # The Excel window becomes visible.

"""

import traceback
from itertools import chain
from types import MethodType

import pythoncom  # Needed as code we eval() references it.
import win32com.client
import winerror
from pywintypes import IIDType

from . import build

debugging = 0  # General debugging
debugging_attr = 0  # Debugging dynamic attribute lookups.

LCID = 0x0

# 048814.python.dynamic.line35.comment These errors generally mean the property or method exists,
# 048815.python.dynamic.line36.comment but can't be used in this context - eg, property instead of a method, etc.
# 048816.python.dynamic.line37.comment Used to determine if we have a real error or not.
ERRORS_BAD_CONTEXT = [
    winerror.DISP_E_MEMBERNOTFOUND,
    winerror.DISP_E_BADPARAMCOUNT,
    winerror.DISP_E_PARAMNOTOPTIONAL,
    winerror.DISP_E_TYPEMISMATCH,
    winerror.E_INVALIDARG,
]

ALL_INVOKE_TYPES = [
    pythoncom.INVOKE_PROPERTYGET,
    pythoncom.INVOKE_PROPERTYPUT,
    pythoncom.INVOKE_PROPERTYPUTREF,
    pythoncom.INVOKE_FUNC,
]


def debug_print(*args):
    if debugging:
        for arg in args:
            print(arg, end=" ")
        print()


def debug_attr_print(*args):
    if debugging_attr:
        for arg in args:
            print(arg, end=" ")
        print()


# 048817.python.dynamic.line68.comment get the type objects for IDispatch and IUnknown
PyIDispatchType = pythoncom.TypeIIDs[pythoncom.IID_IDispatch]
PyIUnknownType = pythoncom.TypeIIDs[pythoncom.IID_IUnknown]

_GoodDispatchTypes = (str, IIDType)


def _GetGoodDispatch(IDispatch, clsctx=pythoncom.CLSCTX_SERVER):
    # 048818.python.dynamic.line76.comment quick return for most common case
    if isinstance(IDispatch, PyIDispatchType):
        return IDispatch
    if isinstance(IDispatch, _GoodDispatchTypes):
        try:
            IDispatch = pythoncom.connect(IDispatch)
        except pythoncom.ole_error:
            IDispatch = pythoncom.CoCreateInstance(
                IDispatch, None, clsctx, pythoncom.IID_IDispatch
            )
    else:
        # 048819.python.dynamic.line87.comment may already be a wrapped class.
        IDispatch = getattr(IDispatch, "_oleobj_", IDispatch)
    return IDispatch


def _GetGoodDispatchAndUserName(IDispatch, userName, clsctx):
    # 048820.python.dynamic.line93.comment Get a dispatch object, and a 'user name' (ie, the name as
    # 048821.python.dynamic.line94.comment displayed to the user in repr() etc.
    if userName is None:
        if isinstance(IDispatch, str):
            userName = IDispatch
        # 048822.python.dynamic.line98.comment # ??? else userName remains None ???
    else:
        userName = str(userName)
    return (_GetGoodDispatch(IDispatch, clsctx), userName)


def _GetDescInvokeType(entry, invoke_type):
    # 048823.python.dynamic.line105.comment determine the wFlags argument passed as input to IDispatch::Invoke
    # 048824.python.dynamic.line106.comment Only ever called by __getattr__ and __setattr__ from dynamic objects!
    # 048825.python.dynamic.line107.comment * `entry` is a MapEntry with whatever typeinfo we have about the property we are getting/setting.
    # 048826.python.dynamic.line108.comment * `invoke_type` is either INVOKE_PROPERTYGET | INVOKE_PROPERTYSET and really just
    # 048827.python.dynamic.line109.comment means "called by __getattr__" or "called by __setattr__"
    if not entry or not entry.desc:
        return invoke_type

    if entry.desc.desckind == pythoncom.DESCKIND_VARDESC:
        return invoke_type

    # 048828.python.dynamic.line116.comment So it's a FUNCDESC - just use what it specifies.
    return entry.desc.invkind


def Dispatch(
    IDispatch,
    userName=None,
    createClass=None,
    typeinfo=None,
    clsctx=pythoncom.CLSCTX_SERVER,
):
    IDispatch, userName = _GetGoodDispatchAndUserName(IDispatch, userName, clsctx)
    if createClass is None:
        createClass = CDispatch
    lazydata = None
    try:
        if typeinfo is None:
            typeinfo = IDispatch.GetTypeInfo()
        if typeinfo is not None:
            try:
                # 048829.python.dynamic.line136.comment try for a typecomp
                typecomp = typeinfo.GetTypeComp()
                lazydata = typeinfo, typecomp
            except pythoncom.com_error:
                pass
    except pythoncom.com_error:
        typeinfo = None
    olerepr = MakeOleRepr(IDispatch, typeinfo, lazydata)
    return createClass(IDispatch, olerepr, userName, lazydata=lazydata)


def MakeOleRepr(IDispatch, typeinfo, typecomp):
    olerepr = None
    if typeinfo is not None:
        try:
            attr = typeinfo.GetTypeAttr()
            # 048830.python.dynamic.line152.comment If the type info is a special DUAL interface, magically turn it into
            # 048831.python.dynamic.line153.comment a DISPATCH typeinfo.
            if (
                attr[5] == pythoncom.TKIND_INTERFACE
                and attr[11] & pythoncom.TYPEFLAG_FDUAL
            ):
                # 048832.python.dynamic.line158.comment Get corresponding Disp interface;
                # 048833.python.dynamic.line159.comment -1 is a special value which does this for us.
                href = typeinfo.GetRefTypeOfImplType(-1)
                typeinfo = typeinfo.GetRefTypeInfo(href)
                attr = typeinfo.GetTypeAttr()
            if typecomp is None:
                olerepr = build.DispatchItem(typeinfo, attr, None, 0)
            else:
                olerepr = build.LazyDispatchItem(attr, None)
        except pythoncom.ole_error:
            pass
    if olerepr is None:
        olerepr = build.DispatchItem()
    return olerepr


def DumbDispatch(
    IDispatch,
    userName=None,
    createClass=None,
    clsctx=pythoncom.CLSCTX_SERVER,
):
    "Dispatch with no type info"
    IDispatch, userName = _GetGoodDispatchAndUserName(IDispatch, userName, clsctx)
    if createClass is None:
        createClass = CDispatch
    return createClass(IDispatch, build.DispatchItem(), userName)


class CDispatch:
    def __init__(self, IDispatch, olerepr, userName=None, lazydata=None):
        if userName is None:
            userName = "<unknown>"
        self.__dict__["_oleobj_"] = IDispatch
        self.__dict__["_username_"] = userName
        self.__dict__["_olerepr_"] = olerepr
        self.__dict__["_mapCachedItems_"] = {}
        self.__dict__["_builtMethods_"] = {}
        self.__dict__["_enum_"] = None
        self.__dict__["_unicode_to_string_"] = None
        self.__dict__["_lazydata_"] = lazydata

    def __call__(self, *args):
        "Provide 'default dispatch' COM functionality - allow instance to be called"
        if self._olerepr_.defaultDispatchName:
            invkind, dispid = self._find_dispatch_type_(
                self._olerepr_.defaultDispatchName
            )
        else:
            invkind, dispid = (
                pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET,
                pythoncom.DISPID_VALUE,
            )
        if invkind is not None:
            allArgs = (dispid, LCID, invkind, 1) + args
            return self._get_good_object_(
                self._oleobj_.Invoke(*allArgs), self._olerepr_.defaultDispatchName, None
            )
        raise TypeError("This dispatch object does not define a default method")

    def __bool__(self):
        return True  # ie "if object:" should always be "true" - without this, __len__ is tried.
        # 048835.python.dynamic.line220.comment _Possibly_ want to defer to __len__ if available, but I'm not sure this is
        # 048836.python.dynamic.line221.comment desirable???

    def __repr__(self):
        return "<COMObject %s>" % (self._username_)

    def __str__(self):
        # 048837.python.dynamic.line227.comment __str__ is used when the user does "print(object)", so we gracefully
        # 048838.python.dynamic.line228.comment fall back to the __repr__ if the object has no default method.
        try:
            return str(self.__call__())
        except pythoncom.com_error as details:
            if details.hresult not in ERRORS_BAD_CONTEXT:
                raise
            return self.__repr__()

    def __dir__(self):
        attributes = chain(self.__dict__, dir(self.__class__), self._dir_ole_())
        try:
            attributes = chain(attributes, [p.Name for p in self.Properties_])
        except AttributeError:
            pass
        return list(set(attributes))

    def _dir_ole_(self):
        items_dict = {}
        for iTI in range(0, self._oleobj_.GetTypeInfoCount()):
            typeInfo = self._oleobj_.GetTypeInfo(iTI)
            self._UpdateWithITypeInfo_(items_dict, typeInfo)
        return list(items_dict)

    def _UpdateWithITypeInfo_(self, items_dict, typeInfo):
        typeInfos = [typeInfo]
        # 048839.python.dynamic.line253.comment suppress IDispatch and IUnknown methods
        inspectedIIDs = {pythoncom.IID_IDispatch: None}

        while len(typeInfos) > 0:
            typeInfo = typeInfos.pop()
            typeAttr = typeInfo.GetTypeAttr()

            if typeAttr.iid not in inspectedIIDs:
                inspectedIIDs[typeAttr.iid] = None
                for iFun in range(0, typeAttr.cFuncs):
                    funDesc = typeInfo.GetFuncDesc(iFun)
                    funName = typeInfo.GetNames(funDesc.memid)[0]
                    if funName not in items_dict:
                        items_dict[funName] = None

                # 048840.python.dynamic.line268.comment Inspect the type info of all implemented types
                # 048841.python.dynamic.line269.comment E.g. IShellDispatch5 implements IShellDispatch4 which implements IShellDispatch3 ...
                for iImplType in range(0, typeAttr.cImplTypes):
                    iRefType = typeInfo.GetRefTypeOfImplType(iImplType)
                    refTypeInfo = typeInfo.GetRefTypeInfo(iRefType)
                    typeInfos.append(refTypeInfo)

    # 048842.python.dynamic.line275.comment Delegate comparison to the oleobjs, as they know how to do identity.
    def __eq__(self, other):
        other = getattr(other, "_oleobj_", other)
        return self._oleobj_ == other

    def __ne__(self, other):
        other = getattr(other, "_oleobj_", other)
        return self._oleobj_ != other

    def __int__(self):
        return int(self.__call__())

    def __len__(self):
        invkind, dispid = self._find_dispatch_type_("Count")
        if invkind:
            return self._oleobj_.Invoke(dispid, LCID, invkind, 1)
        raise TypeError("This dispatch object does not define a Count method")

    def _NewEnum(self):
        try:
            invkind = pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET
            enum = self._oleobj_.InvokeTypes(
                pythoncom.DISPID_NEWENUM, LCID, invkind, (13, 10), ()
            )
        except pythoncom.com_error:
            return None  # no enumerator for this object.
        from . import util

        return util.WrapEnum(enum, None)

    def __getitem__(self, index):  # syver modified
        # 048845.python.dynamic.line306.comment Improved __getitem__ courtesy Syver Enstad
        # 048846.python.dynamic.line307.comment Must check _NewEnum before Item, to ensure b/w compat.
        if isinstance(index, int):
            if self.__dict__["_enum_"] is None:
                self.__dict__["_enum_"] = self._NewEnum()
            if self.__dict__["_enum_"] is not None:
                return self._get_good_object_(self._enum_.__getitem__(index))
        # 048847.python.dynamic.line313.comment See if we have an "Item" method/property we can use (goes hand in hand with Count() above!)
        invkind, dispid = self._find_dispatch_type_("Item")
        if invkind is not None:
            return self._get_good_object_(
                self._oleobj_.Invoke(dispid, LCID, invkind, 1, index)
            )
        raise TypeError("This object does not support enumeration")

    def __setitem__(self, index, *args):
        # 048848.python.dynamic.line322.comment XXX - todo - We should support calling Item() here too!
        # 048849.python.dynamic.line323.comment print("__setitem__ with", index, args)
        if self._olerepr_.defaultDispatchName:
            invkind, dispid = self._find_dispatch_type_(
                self._olerepr_.defaultDispatchName
            )
        else:
            invkind, dispid = (
                pythoncom.DISPATCH_PROPERTYPUT | pythoncom.DISPATCH_PROPERTYPUTREF,
                pythoncom.DISPID_VALUE,
            )
        if invkind is not None:
            allArgs = (dispid, LCID, invkind, 0, index) + args
            return self._get_good_object_(
                self._oleobj_.Invoke(*allArgs), self._olerepr_.defaultDispatchName, None
            )
        raise TypeError("This dispatch object does not define a default method")

    def _find_dispatch_type_(self, methodName):
        if methodName in self._olerepr_.mapFuncs:
            item = self._olerepr_.mapFuncs[methodName]
            return item.desc[4], item.dispid

        if methodName in self._olerepr_.propMapGet:
            item = self._olerepr_.propMapGet[methodName]
            return item.desc[4], item.dispid

        try:
            dispid = self._oleobj_.GetIDsOfNames(0, methodName)
        except:  ### what error?
            return None, None
        return pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET, dispid

    def _ApplyTypes_(self, dispid, wFlags, retType, argTypes, user, resultCLSID, *args):
        result = self._oleobj_.InvokeTypes(
            *(dispid, LCID, wFlags, retType, argTypes) + args
        )
        return self._get_good_object_(result, user, resultCLSID)

    def _wrap_dispatch_(
        self,
        ob,
        userName=None,
        returnCLSID=None,
    ):
        # 048851.python.dynamic.line367.comment Given a dispatch object, wrap it in a class
        return Dispatch(ob, userName)

    def _get_good_single_object_(self, ob, userName=None, ReturnCLSID=None):
        if isinstance(ob, PyIDispatchType):
            # 048852.python.dynamic.line372.comment make a new instance of (probably this) class.
            return self._wrap_dispatch_(ob, userName, ReturnCLSID)
        if isinstance(ob, PyIUnknownType):
            try:
                ob = ob.QueryInterface(pythoncom.IID_IDispatch)
            except pythoncom.com_error:
                # 048853.python.dynamic.line378.comment It is an IUnknown, but not an IDispatch, so just let it through.
                return ob
            return self._wrap_dispatch_(ob, userName, ReturnCLSID)
        return ob

    def _get_good_object_(self, ob, userName=None, ReturnCLSID=None):
        """Given an object (usually the retval from a method), make it a good object to return.
        Basically checks if it is a COM object, and wraps it up.
        Also handles the fact that a retval may be a tuple of retvals"""
        if ob is None:  # Quick exit!
            return None
        elif isinstance(ob, tuple):
            return tuple(
                map(
                    lambda o,
                    s=self,
                    oun=userName,
                    rc=ReturnCLSID: s._get_good_single_object_(o, oun, rc),
                    ob,
                )
            )
        else:
            return self._get_good_single_object_(ob)

    def _make_method_(self, name):
        "Make a method object - Assumes in olerepr funcmap"
        methodName = build.MakePublicAttributeName(name)  # translate keywords etc.
        methodCodeList = self._olerepr_.MakeFuncMethod(
            self._olerepr_.mapFuncs[name], methodName, 0
        )
        methodCode = "\n".join(methodCodeList)
        try:
            # 048856.python.dynamic.line410.comment print(f"Method code for {self._username_} is:\n", methodCode)
            # 048857.python.dynamic.line411.comment self._print_details_()
            codeObject = compile(methodCode, "<COMObject %s>" % self._username_, "exec")
            # 048858.python.dynamic.line413.comment Exec the code object
            tempNameSpace = {}
            # 048859.python.dynamic.line415.comment "Dispatch" in the exec'd code is win32com.client.Dispatch, not ours.
            globNameSpace = globals().copy()
            globNameSpace["Dispatch"] = win32com.client.Dispatch
            exec(
                codeObject, globNameSpace, tempNameSpace
            )  # self.__dict__, self.__dict__
            name = methodName
            # 048861.python.dynamic.line422.comment Save the function in map.
            fn = self._builtMethods_[name] = tempNameSpace[name]
            return MethodType(fn, self)
        except:
            debug_print("Error building OLE definition for code ", methodCode)
            traceback.print_exc()
        return None

    def _Release_(self):
        """Cleanup object - like a close - to force cleanup when you don't
        want to rely on Python's reference counting."""
        for childCont in self._mapCachedItems_.values():
            childCont._Release_()
        self._mapCachedItems_ = {}
        if self._oleobj_:
            self._oleobj_.Release()
            self.__dict__["_oleobj_"] = None
        if self._olerepr_:
            self.__dict__["_olerepr_"] = None
        self._enum_ = None

    def _proc_(self, name, *args):
        """Call the named method as a procedure, rather than function.
        Mainly used by Word.Basic, which whinges about such things."""
        try:
            item = self._olerepr_.mapFuncs[name]
            dispId = item.dispid
            return self._get_good_object_(
                self._oleobj_.Invoke(*(dispId, LCID, item.desc[4], 0) + (args))
            )
        except KeyError:
            raise AttributeError(name)

    def _print_details_(self):
        "Debug routine - dumps what it knows about an object."
        print("AxDispatch container", self._username_)
        try:
            print("Methods:")
            for method in self._olerepr_.mapFuncs:
                print("\t", method)
            print("Props:")
            for prop, entry in self._olerepr_.propMap.items():
                print(f"\t{prop} = 0x{entry.dispid:x} - {entry!r}")
            print("Get Props:")
            for prop, entry in self._olerepr_.propMapGet.items():
                print(f"\t{prop} = 0x{entry.dispid:x} - {entry!r}")
            print("Put Props:")
            for prop, entry in self._olerepr_.propMapPut.items():
                print(f"\t{prop} = 0x{entry.dispid:x} - {entry!r}")
        except:
            traceback.print_exc()

    def __LazyMap__(self, attr):
        try:
            if self._LazyAddAttr_(attr):
                debug_attr_print(
                    f"{self._username_}.__LazyMap__({attr}) added something"
                )
                return 1
        except AttributeError:
            return 0

    # 048862.python.dynamic.line484.comment Using the typecomp, lazily create a new attribute definition.
    def _LazyAddAttr_(self, attr):
        if self._lazydata_ is None:
            return 0
        res = 0
        typeinfo, typecomp = self._lazydata_
        olerepr = self._olerepr_
        # 048863.python.dynamic.line491.comment We need to explicitly check each invoke type individually - simply
        # 048864.python.dynamic.line492.comment specifying '0' will bind to "any member", which may not be the one
        # 048865.python.dynamic.line493.comment we are actually after (ie, we may be after prop_get, but returned
        # 048866.python.dynamic.line494.comment the info for the prop_put.)
        for i in ALL_INVOKE_TYPES:
            try:
                x, t = typecomp.Bind(attr, i)
                # 048867.python.dynamic.line498.comment Support 'Get' and 'Set' properties - see
                # 048868.python.dynamic.line499.comment bug 1587023
                if x == 0 and attr[:3] in ("Set", "Get"):
                    x, t = typecomp.Bind(attr[3:], i)
                if x == pythoncom.DESCKIND_FUNCDESC:  # it's a FUNCDESC
                    r = olerepr._AddFunc_(typeinfo, t, 0)
                elif x == pythoncom.DESCKIND_VARDESC:  # it's a VARDESC
                    r = olerepr._AddVar_(typeinfo, t, 0)
                else:  # not found or TYPEDESC/IMPLICITAPP
                    r = None
                if not r is None:
                    key, map = r[0], r[1]
                    item = map[key]
                    if map == olerepr.propMapPut:
                        olerepr._propMapPutCheck_(key, item)
                    elif map == olerepr.propMapGet:
                        olerepr._propMapGetCheck_(key, item)
                    res = 1
            except:
                pass
        return res

    def _FlagAsMethod(self, *methodNames):
        """Flag these attribute names as being methods.
        Some objects do not correctly differentiate methods and
        properties, leading to problems when calling these methods.

        Specifically, trying to say: ob.SomeFunc()
        may yield an exception "None object is not callable"
        In this case, an attempt to fetch the *property* has worked
        and returned None, rather than indicating it is really a method.
        Calling: ob._FlagAsMethod("SomeFunc")
        should then allow this to work.
        """
        for name in methodNames:
            details = build.MapEntry(self.__AttrToID__(name), (name,))
            self._olerepr_.mapFuncs[name] = details

    def __AttrToID__(self, attr):
        debug_attr_print(
            "Calling GetIDsOfNames for property {} in Dispatch container {}".format(
                attr, self._username_
            )
        )
        return self._oleobj_.GetIDsOfNames(0, attr)

    def __getattr__(self, attr):
        if attr == "__iter__":
            # 048872.python.dynamic.line546.comment We can't handle this as a normal method, as if the attribute
            # 048873.python.dynamic.line547.comment exists, then it must return an iterable object.
            try:
                invkind = pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET
                enum = self._oleobj_.InvokeTypes(
                    pythoncom.DISPID_NEWENUM, LCID, invkind, (13, 10), ()
                )
            except pythoncom.com_error:
                raise AttributeError("This object can not function as an iterator")

            # 048874.python.dynamic.line556.comment We must return a callable object.
            class Factory:
                def __init__(self, ob):
                    self.ob = ob

                def __call__(self):
                    import win32com.client.util

                    return win32com.client.util.Iterator(self.ob)

            return Factory(enum)

        if attr.startswith("_") and attr.endswith("_"):  # Fast-track.
            raise AttributeError(attr)
        # 048876.python.dynamic.line570.comment If a known method, create new instance and return.
        try:
            return MethodType(self._builtMethods_[attr], self)
        except KeyError:
            pass
        # 048877.python.dynamic.line575.comment XXX - Note that we current are case sensitive in the method.
        # 048878.python.dynamic.line576.comment debug_attr_print("GetAttr called for %s on DispatchContainer %s" % (attr,self._username_))
        # 048879.python.dynamic.line577.comment First check if it is in the method map.  Note that an actual method
        # 048880.python.dynamic.line578.comment must not yet exist, (otherwise we would not be here).  This
        # 048881.python.dynamic.line579.comment means we create the actual method object - which also means
        # 048882.python.dynamic.line580.comment this code will never be asked for that method name again.
        if attr in self._olerepr_.mapFuncs:
            return self._make_method_(attr)

        # 048883.python.dynamic.line584.comment Delegate to property maps/cached items
        retEntry = None
        if self._olerepr_ and self._oleobj_:
            # 048884.python.dynamic.line587.comment first check general property map, then specific "put" map.
            retEntry = self._olerepr_.propMap.get(attr)
            if retEntry is None:
                retEntry = self._olerepr_.propMapGet.get(attr)
            # 048885.python.dynamic.line591.comment Not found so far - See what COM says.
            if retEntry is None:
                try:
                    if self.__LazyMap__(attr):
                        if attr in self._olerepr_.mapFuncs:
                            return self._make_method_(attr)
                        retEntry = self._olerepr_.propMap.get(attr)
                        if retEntry is None:
                            retEntry = self._olerepr_.propMapGet.get(attr)
                    if retEntry is None:
                        retEntry = build.MapEntry(self.__AttrToID__(attr), (attr,))
                except pythoncom.ole_error:
                    pass  # No prop by that name - retEntry remains None.

        if retEntry is not None:  # see if in my cache
            try:
                ret = self._mapCachedItems_[retEntry.dispid]
                debug_attr_print("Cached items has attribute!", ret)
                return ret
            except (KeyError, AttributeError):
                debug_attr_print("Attribute %s not in cache" % attr)

        # 048888.python.dynamic.line613.comment If we are still here, and have a retEntry, get the OLE item
        if retEntry is not None:
            invoke_type = _GetDescInvokeType(retEntry, pythoncom.INVOKE_PROPERTYGET)
            debug_attr_print(
                "Getting property Id 0x%x from OLE object" % retEntry.dispid
            )
            try:
                ret = self._oleobj_.Invoke(retEntry.dispid, 0, invoke_type, 1)
            except pythoncom.com_error as details:
                if details.hresult in ERRORS_BAD_CONTEXT:
                    # 048889.python.dynamic.line623.comment May be a method.
                    self._olerepr_.mapFuncs[attr] = retEntry
                    return self._make_method_(attr)
                raise
            debug_attr_print("OLE returned ", ret)
            return self._get_good_object_(ret)

        # 048890.python.dynamic.line630.comment no where else to look.
        raise AttributeError(f"{self._username_}.{attr}")

    def __setattr__(self, attr, value):
        if (
            attr in self.__dict__
        ):  # Fast-track - if already in our dict, just make the assignment.
            # 048892.python.dynamic.line637.comment XXX - should maybe check method map - if someone assigns to a method,
            # 048893.python.dynamic.line638.comment it could mean something special (not sure what, tho!)
            self.__dict__[attr] = value
            return
        # 048894.python.dynamic.line641.comment Allow property assignment.
        debug_attr_print(
            f"SetAttr called for {self._username_}.{attr}={value!r} on DispatchContainer"
        )

        if self._olerepr_:
            # 048895.python.dynamic.line647.comment Check the "general" property map.
            if attr in self._olerepr_.propMap:
                entry = self._olerepr_.propMap[attr]
                invoke_type = _GetDescInvokeType(entry, pythoncom.INVOKE_PROPERTYPUT)
                self._oleobj_.Invoke(entry.dispid, 0, invoke_type, 0, value)
                return
            # 048896.python.dynamic.line653.comment Check the specific "put" map.
            if attr in self._olerepr_.propMapPut:
                entry = self._olerepr_.propMapPut[attr]
                invoke_type = _GetDescInvokeType(entry, pythoncom.INVOKE_PROPERTYPUT)
                self._oleobj_.Invoke(entry.dispid, 0, invoke_type, 0, value)
                return

        # 048897.python.dynamic.line660.comment Try the OLE Object
        if self._oleobj_:
            if self.__LazyMap__(attr):
                # 048898.python.dynamic.line663.comment Check the "general" property map.
                if attr in self._olerepr_.propMap:
                    entry = self._olerepr_.propMap[attr]
                    invoke_type = _GetDescInvokeType(
                        entry, pythoncom.INVOKE_PROPERTYPUT
                    )
                    self._oleobj_.Invoke(entry.dispid, 0, invoke_type, 0, value)
                    return
                # 048899.python.dynamic.line671.comment Check the specific "put" map.
                if attr in self._olerepr_.propMapPut:
                    entry = self._olerepr_.propMapPut[attr]
                    invoke_type = _GetDescInvokeType(
                        entry, pythoncom.INVOKE_PROPERTYPUT
                    )
                    self._oleobj_.Invoke(entry.dispid, 0, invoke_type, 0, value)
                    return
            try:
                entry = build.MapEntry(self.__AttrToID__(attr), (attr,))
            except pythoncom.com_error:
                # 048900.python.dynamic.line682.comment No attribute of that name
                entry = None
            if entry is not None:
                try:
                    invoke_type = _GetDescInvokeType(
                        entry, pythoncom.INVOKE_PROPERTYPUT
                    )
                    self._oleobj_.Invoke(entry.dispid, 0, invoke_type, 0, value)
                    self._olerepr_.propMap[attr] = entry
                    debug_attr_print(
                        "__setattr__ property {} (id=0x{:x}) in Dispatch container {}".format(
                            attr, entry.dispid, self._username_
                        )
                    )
                    return
                except pythoncom.com_error:
                    pass
        raise AttributeError(f"Property '{self._username_}.{attr}' can not be set.")
