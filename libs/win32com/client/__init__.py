# 048587.python.init.line1.comment This module exists to create the "best" dispatch object for a given
# 048588.python.init.line2.comment object.  If "makepy" support for a given object is detected, it is
# 048589.python.init.line3.comment used, otherwise a dynamic dispatch object.

# 048590.python.init.line5.comment Note that if the unknown dispatch object then returns a known
# 048591.python.init.line6.comment dispatch object, the known class will be used.  This contrasts
# 048592.python.init.line7.comment with dynamic.Dispatch behaviour, where dynamic objects are always used.
from __future__ import annotations

import sys
from itertools import chain

import pythoncom
import pywintypes

from . import dynamic, gencache

_PyIDispatchType = pythoncom.TypeIIDs[pythoncom.IID_IDispatch]


def __WrapDispatch(
    dispatch,
    userName=None,
    resultCLSID=None,
    typeinfo=None,
    clsctx=pythoncom.CLSCTX_SERVER,
    WrapperClass=None,
):
    """
    Helper function to return a makepy generated class for a CLSID if it exists,
    otherwise cope by using CDispatch.
    """
    if resultCLSID is None:
        try:
            typeinfo = dispatch.GetTypeInfo()
            if (
                typeinfo is not None
            ):  # Some objects return NULL, some raise exceptions...
                resultCLSID = str(typeinfo.GetTypeAttr()[0])
        except (pythoncom.com_error, AttributeError):
            pass
    if resultCLSID is not None:
        from . import gencache

        # 048594.python.init.line45.comment Attempt to load generated module support
        # 048595.python.init.line46.comment This may load the module, and make it available
        klass = gencache.GetClassForCLSID(resultCLSID)
        if klass is not None:
            return klass(dispatch)

    # 048596.python.init.line51.comment Return a "dynamic" object - best we can do!
    if WrapperClass is None:
        WrapperClass = CDispatch
    return dynamic.Dispatch(dispatch, userName, WrapperClass, typeinfo, clsctx=clsctx)


def GetObject(Pathname=None, Class=None, clsctx=None):
    r"""
    Mimic VB's GetObject() function.

    ob = GetObject(Class = "ProgID") or GetObject(Class = clsid) will
    connect to an already running instance of the COM object.

    ob = GetObject(r"c:\blah\blah\foo.xls") (aka the COM moniker syntax)
    will return a ready to use Python wrapping of the required COM object.

    Note: You must specifiy one or the other of these arguments. I know
    this isn't pretty, but it is what VB does. Blech. If you don't
    I'll throw ValueError at you. :)

    This will most likely throw pythoncom.com_error if anything fails.
    """
    if clsctx is None:
        clsctx = pythoncom.CLSCTX_ALL

    if (Pathname is None and Class is None) or (
        Pathname is not None and Class is not None
    ):
        raise ValueError(
            "You must specify a value for Pathname or Class, but not both."
        )

    if Class is not None:
        return GetActiveObject(Class, clsctx)
    else:
        return Moniker(Pathname, clsctx)


def GetActiveObject(Class, clsctx=pythoncom.CLSCTX_ALL):
    """
    Python friendly version of GetObject's ProgID/CLSID functionality.
    """
    resultCLSID = pywintypes.IID(Class)
    dispatch = pythoncom.GetActiveObject(resultCLSID)
    dispatch = dispatch.QueryInterface(pythoncom.IID_IDispatch)
    return __WrapDispatch(dispatch, Class, resultCLSID=resultCLSID, clsctx=clsctx)


def Moniker(Pathname, clsctx=pythoncom.CLSCTX_ALL):
    """
    Python friendly version of GetObject's moniker functionality.
    """
    moniker, i, bindCtx = pythoncom.MkParseDisplayName(Pathname)
    dispatch = moniker.BindToObject(bindCtx, None, pythoncom.IID_IDispatch)
    return __WrapDispatch(dispatch, Pathname, clsctx=clsctx)


def Dispatch(
    dispatch,
    userName=None,
    resultCLSID=None,
    typeinfo=None,
    clsctx=pythoncom.CLSCTX_SERVER,
):
    """Creates a Dispatch based COM object."""
    dispatch, userName = dynamic._GetGoodDispatchAndUserName(dispatch, userName, clsctx)
    return __WrapDispatch(dispatch, userName, resultCLSID, typeinfo, clsctx=clsctx)


def DispatchEx(
    clsid,
    machine=None,
    userName=None,
    resultCLSID=None,
    typeinfo=None,
    clsctx=None,
):
    """Creates a Dispatch based COM object on a specific machine."""
    # 048597.python.init.line129.comment If InProc is registered, DCOM will use it regardless of the machine name
    # 048598.python.init.line130.comment (and regardless of the DCOM config for the object.)  So unless the user
    # 048599.python.init.line131.comment specifies otherwise, we exclude inproc apps when a remote machine is used.
    if clsctx is None:
        clsctx = pythoncom.CLSCTX_SERVER
        if machine is not None:
            clsctx &= ~pythoncom.CLSCTX_INPROC
    if machine is None:
        serverInfo = None
    else:
        serverInfo = (machine,)
    if userName is None:
        userName = clsid
    dispatch = pythoncom.CoCreateInstanceEx(
        clsid, None, clsctx, serverInfo, (pythoncom.IID_IDispatch,)
    )[0]
    return Dispatch(dispatch, userName, resultCLSID, typeinfo, clsctx=clsctx)


class CDispatch(dynamic.CDispatch):
    """
    The dynamic class used as a last resort.
    The purpose of this overriding of dynamic.CDispatch is to perpetuate the policy
    of using the makepy generated wrapper Python class instead of dynamic.CDispatch
    if/when possible.
    """

    def _wrap_dispatch_(self, ob, userName=None, returnCLSID=None):
        return Dispatch(ob, userName, returnCLSID)

    def __dir__(self):
        return dynamic.CDispatch.__dir__(self)


def CastTo(ob, target, typelib=None):
    """'Cast' a COM object to another interface"""
    # 048600.python.init.line165.comment todo - should support target being an IID
    mod = None
    if (
        typelib is not None
    ):  # caller specified target typelib (TypelibSpec). See e.g. selecttlb.EnumTlbs().
        mod = gencache.MakeModuleForTypelib(
            typelib.clsid, typelib.lcid, int(typelib.major, 16), int(typelib.minor, 16)
        )
        if not hasattr(mod, target):
            raise ValueError(
                f"The interface name '{target}' does not appear in the "
                f"specified library {typelib.ver_desc!r}"
            )

    elif hasattr(target, "index"):  # string like
        # 048603.python.init.line180.comment for now, we assume makepy for this to work.
        if "CLSID" not in ob.__class__.__dict__:
            # 048604.python.init.line182.comment Eeek - no makepy support - try and build it.
            ob = gencache.EnsureDispatch(ob)
        if "CLSID" not in ob.__class__.__dict__:
            raise ValueError("Must be a makepy-able object for this to work")
        clsid = ob.CLSID
        # 048605.python.init.line187.comment Lots of hoops to support "demand-build" - ie, generating
        # 048606.python.init.line188.comment code for an interface first time it is used.  We assume the
        # 048607.python.init.line189.comment interface name exists in the same library as the object.
        # 048608.python.init.line190.comment This is generally the case - only referenced typelibs may be
        # 048609.python.init.line191.comment a problem, and we can handle that later.  Maybe <wink>
        # 048610.python.init.line192.comment So get the generated module for the library itself, then
        # 048611.python.init.line193.comment find the interface CLSID there.
        mod = gencache.GetModuleForCLSID(clsid)
        # 048612.python.init.line195.comment Get the 'root' module.
        mod = gencache.GetModuleForTypelib(
            mod.CLSID, mod.LCID, mod.MajorVersion, mod.MinorVersion
        )
        # 048613.python.init.line199.comment Find the CLSID of the target
        target_clsid = mod.NamesToIIDMap.get(target)
        if target_clsid is None:
            raise ValueError(
                f"The interface name '{target}' does not appear in the "
                f"same library as object '{ob!r}'"
            )
        mod = gencache.GetModuleForCLSID(target_clsid)
    if mod is not None:
        target_class = getattr(mod, target)
        # 048614.python.init.line209.comment resolve coclass to interface
        target_class = getattr(target_class, "default_interface", target_class)
        return target_class(ob)  # auto QI magic happens
    raise ValueError


class Constants:
    """A container for generated COM constants."""

    def __init__(self):
        self.__dicts__ = []  # A list of dictionaries

    def __getattr__(self, a):
        for d in self.__dicts__:
            if a in d:
                return d[a]
        raise AttributeError(a)


# 048617.python.init.line228.comment And create an instance.
constants = Constants()


# 048618.python.init.line232.comment A helpers for DispatchWithEvents - this becomes __setattr__ for the
# 048619.python.init.line233.comment temporary class.
def _event_setattr_(self, attr, val):
    try:
        # 048620.python.init.line236.comment Does the COM object have an attribute of this name?
        self.__class__.__bases__[0].__setattr__(self, attr, val)
    except AttributeError:
        # 048621.python.init.line239.comment Otherwise just stash it away in the instance.
        self.__dict__[attr] = val


# 048622.python.init.line243.comment An instance of this "proxy" is created to break the COM circular references
# 048623.python.init.line244.comment that exist (ie, when we connect to the COM events, COM keeps a reference
# 048624.python.init.line245.comment to the object.  Thus, the Event connection must be manually broken before
# 048625.python.init.line246.comment our object can die.  This solves the problem by manually breaking the connection
# 048626.python.init.line247.comment to the real object as the proxy dies.
class EventsProxy:
    def __init__(self, ob):
        self.__dict__["_obj_"] = ob

    def __del__(self):
        try:
            # 048627.python.init.line254.comment If there is a COM error on disconnection we should
            # 048628.python.init.line255.comment just ignore it - object probably already shut down...
            self._obj_.close()
        except pythoncom.com_error:
            pass

    def __getattr__(self, attr):
        return getattr(self._obj_, attr)

    def __setattr__(self, attr, val):
        setattr(self._obj_, attr, val)


def __get_disp_and_event_classes(dispatch):
    # 048629.python.init.line268.comment Create/Get the object.
    disp = Dispatch(dispatch)

    if disp.__class__.__dict__.get("CLSID"):
        disp_class = disp.__class__
    else:
        # 048630.python.init.line274.comment Eeek - no makepy support - try and build it.
        error_msg = "This COM object can not automate the makepy process - please run makepy manually for this object"
        try:
            ti = disp._oleobj_.GetTypeInfo()
            disp_clsid = ti.GetTypeAttr()[0]
            tlb, index = ti.GetContainingTypeLib()
            tla = tlb.GetLibAttr()
            gencache.EnsureModule(tla[0], tla[1], tla[3], tla[4], bValidateFile=0)
            # 048631.python.init.line282.comment Get the class from the module.
            disp_class = gencache.GetClassForProgID(str(disp_clsid))
        except pythoncom.com_error as error:
            raise TypeError(error_msg) from error

        if disp_class is None:
            raise TypeError(error_msg)

    # 048632.python.init.line290.comment Get the clsid
    clsid = disp_class.CLSID
    # 048633.python.init.line292.comment Create a new class that derives from 2 classes:
    # 048634.python.init.line293.comment the event sink class and the user class.
    events_class = getevents(clsid)
    if events_class is None:
        raise ValueError("This COM object does not support events.")
    return disp, disp_class, events_class


def DispatchWithEvents(clsid, user_event_class) -> EventsProxy:
    """Create a COM object that can fire events to a user defined class.
    clsid -- The ProgID or CLSID of the object to create.
    user_event_class -- A Python class object that responds to the events.

    This requires makepy support for the COM object being created.  If
    this support does not exist it will be automatically generated by
    this function.  If the object does not support makepy, a TypeError
    exception will be raised.

    The result is a class instance that both represents the COM object
    and handles events from the COM object.

    It is important to note that the returned instance is not a direct
    instance of the user_event_class, but an instance of a temporary
    class object that derives from three classes:
    * The makepy generated class for the COM object
    * The makepy generated class for the COM events
    * The user_event_class as passed to this function.

    If this is not suitable, see the getevents function for an alternative
    technique of handling events.

    Object Lifetimes:  Whenever the object returned from this function is
    cleaned-up by Python, the events will be disconnected from
    the COM object.  This is almost always what should happen,
    but see the documentation for getevents() for more details.

    Example:

    >>> class IEEvents:
    ...    def OnVisible(self, visible):
    ...       print("Visible changed:", visible)
    ...
    >>> ie = DispatchWithEvents("InternetExplorer.Application", IEEvents)
    >>> ie.Visible = 1
    Visible changed: 1
    """
    disp, disp_class, events_class = __get_disp_and_event_classes(clsid)
    result_class = type(
        "COMEventClass",
        (disp_class, events_class, user_event_class),
        {"__setattr__": _event_setattr_},
    )
    # 048635.python.init.line344.comment This only calls the first base class __init__.
    instance = result_class(disp._oleobj_)
    events_class.__init__(instance, instance)
    if hasattr(user_event_class, "__init__"):
        user_event_class.__init__(instance)
    return EventsProxy(instance)


def WithEvents(disp, user_event_class):
    """Similar to DispatchWithEvents - except that the returned
    object is *not* also usable as the original Dispatch object - that is
    the returned object is not dispatchable.

    The difference is best summarised by example.

    >>> class IEEvents:
    ...    def OnVisible(self, visible):
    ...       print("Visible changed:", visible)
    ...
    >>> ie = Dispatch("InternetExplorer.Application")
    >>> ie_events = WithEvents(ie, IEEvents)
    >>> ie.Visible = 1
    Visible changed: 1

    Compare with the code sample for DispatchWithEvents, where you get a
    single object that is both the interface and the event handler.  Note that
    the event handler instance will *not* be able to use 'self.' to refer to
    IE's methods and properties.

    This is mainly useful where using DispatchWithEvents causes
    circular reference problems that the simple proxy doesn't deal with
    """
    disp, disp_class, events_class = __get_disp_and_event_classes(disp)
    result_class = type(
        "COMEventClass",
        (events_class, user_event_class),
        {},
    )
    # 048636.python.init.line382.comment This only calls the first base class __init__.
    instance = result_class(disp)
    if hasattr(user_event_class, "__init__"):
        user_event_class.__init__(instance)
    return instance


def getevents(clsid):
    """Determine the default outgoing interface for a class, given
    either a clsid or progid. It returns a class - you can
    conveniently derive your own handler from this class and implement
    the appropriate methods.

    This method relies on the classes produced by makepy. You must use
    either makepy or the gencache module to ensure that the
    appropriate support classes have been generated for the com server
    that you will be handling events from.

    Beware of COM circular references.  When the Events class is connected
    to the COM object, the COM object itself keeps a reference to the Python
    events class.  Thus, neither the Events instance or the COM object will
    ever die by themselves.  The 'close' method on the events instance
    must be called to break this chain and allow standard Python collection
    rules to manage object lifetimes.  Note that DispatchWithEvents() does
    work around this problem by the use of a proxy object, but if you use
    the getevents() function yourself, you must make your own arrangements
    to manage this circular reference issue.

    Beware of creating Python circular references: this will happen if your
    handler has a reference to an object that has a reference back to
    the event source. Call the 'close' method to break the chain.

    Example:

    >>>win32com.client.gencache.EnsureModule('{EAB22AC0-30C1-11CF-A7EB-0000C05BAE0B}',0,1,1)
    <module 'win32com.gen_py.....
    >>>
    >>> class InternetExplorerEvents(win32com.client.getevents("InternetExplorer.Application.1")):
    ...    def OnVisible(self, Visible):
    ...        print("Visibility changed: ", Visible)
    ...
    >>>
    >>> ie=win32com.client.Dispatch("InternetExplorer.Application.1")
    >>> events=InternetExplorerEvents(ie)
    >>> ie.Visible=1
    Visibility changed:  1
    >>>
    """

    # 048637.python.init.line431.comment find clsid given progid or clsid
    clsid = str(pywintypes.IID(clsid))
    # 048638.python.init.line433.comment return default outgoing interface for that class
    klass = gencache.GetClassForCLSID(clsid)
    try:
        return klass.default_source
    except AttributeError:
        # 048639.python.init.line438.comment See if we have a coclass for the interfaces.
        try:
            return gencache.GetClassForCLSID(klass.coclass_clsid).default_source
        except AttributeError:
            return None


# 048640.python.init.line445.comment A Record object, as used by the COM struct support
def Record(name, object):
    """Creates a new record object, given the name of the record,
    and an object from the same type library.

    Example usage would be:
      app = win32com.client.Dispatch("Some.Application")
      point = win32com.client.Record("SomeAppPoint", app)
      point.x = 0
      point.y = 0
      app.MoveTo(point)
    """
    # 048641.python.init.line457.comment XXX - to do - probably should allow "object" to already be a module object.
    from . import gencache

    object = gencache.EnsureDispatch(object)
    module = sys.modules[object.__class__.__module__]
    # 048642.python.init.line462.comment to allow us to work correctly with "demand generated" code,
    # 048643.python.init.line463.comment we must use the typelib CLSID to obtain the module
    # 048644.python.init.line464.comment (otherwise we get the sub-module for the object, which
    # 048645.python.init.line465.comment does not hold the records)
    # 048646.python.init.line466.comment thus, package may be module, or may be module's parent if demand generated.
    package = gencache.GetModuleForTypelib(
        module.CLSID, module.LCID, module.MajorVersion, module.MinorVersion
    )
    try:
        struct_guid = package.RecordMap[name]
    except KeyError:
        raise ValueError(f"The structure '{name}' is not defined in module '{package}'")
    return pythoncom.GetRecordFromGuids(
        module.CLSID, module.MajorVersion, module.MinorVersion, module.LCID, struct_guid
    )


# 048647.python.init.line479.comment Registration function for com_record subclasses.
def register_record_class(cls):
    """
    Register a subclass of com_record to enable creation of the represented record objects.

    A subclass of com_record requires the following class attributes to be instantiable:

        TLBID : The GUID of the containing TypeLibrary as a string.
        MJVER : The major version number of the TypeLibrary as an integer.
        MNVER : The minor version number of the TypeLibrary as an integer.
        LCID  : The LCID of the TypeLibrary as an integer.
        GUID  : The GUID of the COM Record as a string.

    with GUID strings in {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} notation.

    To instantiate such a subclasses it has to be registered via this function.
    """
    if not issubclass(cls, pythoncom.com_record):
        raise TypeError("Only subclasses of 'com_record' can be registered.")
    try:
        TLBID = cls.TLBID
        MJVER = cls.MJVER
        MNVER = cls.MNVER
        LCID = cls.LCID
        GUID = cls.GUID
    except AttributeError as e:
        raise AttributeError(f"Class {cls.__name__} cannot be instantiated.") from e
    try:
        _ = pythoncom.GetRecordFromGuids(TLBID, MJVER, MNVER, LCID, GUID)
    except Exception as e:
        raise TypeError(f"Class {cls.__name__} cannot be instantiated.") from e
    # 048648.python.init.line510.comment Since the class can be instantiated we know that it represents a valid COM Record
    # 048649.python.init.line511.comment in a properly registered TypeLibrary and that it has a 'GUID' class attribute.
    if cls.GUID in pythoncom.RecordClasses:
        raise ValueError(
            f"Record class with same GUID {cls.GUID} "
            f"is already registered with name '{pythoncom.RecordClasses[cls.GUID].__name__}'."
        )
    pythoncom.RecordClasses[cls.GUID] = cls


# 048650.python.init.line520.comment ###########################################
# 048651.python.init.line521.comment The base of all makepy generated classes
# 048652.python.init.line522.comment ###########################################
class DispatchBaseClass:
    def __init__(self, oobj=None):
        if oobj is None:
            oobj = pythoncom.new(self.CLSID)
        elif isinstance(oobj, (DispatchBaseClass, _PyIDispatchType)):
            try:
                oobj = oobj._oleobj_ if isinstance(oobj, DispatchBaseClass) else oobj
                oobj = oobj.QueryInterface(self.CLSID, pythoncom.IID_IDispatch)
            except pythoncom.com_error as details:
                import winerror

                # 048653.python.init.line534.comment Some stupid objects fail here, even tho it is _already_ IDispatch!!??
                # 048654.python.init.line535.comment Eg, Lotus notes.
                # 048655.python.init.line536.comment So just let it use the existing object if E_NOINTERFACE
                if details.hresult != winerror.E_NOINTERFACE:
                    raise

        self.__dict__["_oleobj_"] = oobj  # so we don't call __setattr__

    def __dir__(self):
        attributes = chain(
            self.__dict__,
            dir(self.__class__),
            self._prop_map_get_,
            self._prop_map_put_,
        )

        try:
            attributes = chain(attributes, [p.Name for p in self.Properties_])
        except AttributeError:
            pass
        return list(set(attributes))

    # 048657.python.init.line556.comment Provide a prettier name than the CLSID
    def __repr__(self):
        # 048658.python.init.line558.comment Need to get the docstring for the module for this class.
        try:
            mod_doc = sys.modules[self.__class__.__module__].__doc__
            if mod_doc:
                mod_name = "win32com.gen_py." + mod_doc
            else:
                mod_name = sys.modules[self.__class__.__module__].__name__
        except KeyError:
            mod_name = "win32com.gen_py.unknown"
        return f"<{mod_name}.{self.__class__.__name__} instance at 0x{id(self)}>"

    # 048659.python.init.line569.comment Delegate comparison to the oleobjs, as they know how to do identity.
    def __eq__(self, other):
        other = getattr(other, "_oleobj_", other)
        return self._oleobj_ == other

    def __ne__(self, other):
        other = getattr(other, "_oleobj_", other)
        return self._oleobj_ != other

    def _ApplyTypes_(self, dispid, wFlags, retType, argTypes, user, resultCLSID, *args):
        return self._get_good_object_(
            self._oleobj_.InvokeTypes(dispid, 0, wFlags, retType, argTypes, *args),
            user,
            resultCLSID,
        )

    def __getattr__(self, attr):
        args = self._prop_map_get_.get(attr)
        if args is None:
            raise AttributeError(f"'{self!r}' object has no attribute '{attr}'")
        return self._ApplyTypes_(*args)

    def __setattr__(self, attr, value):
        if attr in self.__dict__:
            self.__dict__[attr] = value
            return
        try:
            args, defArgs = self._prop_map_put_[attr]
        except KeyError:
            raise AttributeError(f"'{self!r}' object has no attribute '{attr}'")
        self._oleobj_.Invoke(*(args + (value,) + defArgs))

    def _get_good_single_object_(self, obj, obUserName=None, resultCLSID=None):
        return _get_good_single_object_(obj, obUserName, resultCLSID)

    def _get_good_object_(self, obj, obUserName=None, resultCLSID=None):
        return _get_good_object_(obj, obUserName, resultCLSID)


# 048660.python.init.line608.comment XXX - These should be consolidated with dynamic.py versions.
def _get_good_single_object_(obj, obUserName=None, resultCLSID=None):
    if isinstance(obj, _PyIDispatchType):
        return Dispatch(obj, obUserName, resultCLSID)
    return obj


def _get_good_object_(obj, obUserName=None, resultCLSID=None):
    if obj is None:
        return None
    elif isinstance(obj, tuple):
        obUserNameTuple = (obUserName,) * len(obj)
        resultCLSIDTuple = (resultCLSID,) * len(obj)
        return tuple(map(_get_good_object_, obj, obUserNameTuple, resultCLSIDTuple))
    else:
        return _get_good_single_object_(obj, obUserName, resultCLSID)


class CoClassBaseClass:
    def __init__(self, oobj=None):
        if oobj is None:
            oobj = pythoncom.new(self.CLSID)
        self.__dict__["_dispobj_"] = self.default_interface(oobj)

    def __repr__(self):
        return f"<win32com.gen_py.{__doc__}.{self.__class__.__name__}>"

    def __getattr__(self, attr):
        d = self.__dict__["_dispobj_"]
        if d is not None:
            return getattr(d, attr)
        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if attr in self.__dict__:
            self.__dict__[attr] = value
            return
        try:
            d = self.__dict__["_dispobj_"]
            if d is not None:
                d.__setattr__(attr, value)
                return
        except AttributeError:
            pass
        self.__dict__[attr] = value

    # 048661.python.init.line654.comment Special methods don't use __getattr__ etc, so explicitly delegate here.
    # 048662.python.init.line655.comment Some wrapped objects might not have them, but that's OK - the attribute
    # 048663.python.init.line656.comment error can just bubble up.
    # 048664.python.init.line657.comment This was initially implemented to address #1699 which did cause a problem
    # 048665.python.init.line658.comment with bool() in #1753 because the code initially implemented __nonzero__
    # 048666.python.init.line659.comment instead of __bool__, which was pointed out in the conclusion of #1870.
    def __call__(self, *args, **kwargs):
        return self.__dict__["_dispobj_"](*args, **kwargs)

    def __str__(self, *args):
        return str(self.__dict__["_dispobj_"])

    def __int__(self, *args):
        return int(self.__dict__["_dispobj_"])

    def __iter__(self):
        return iter(self.__dict__["_dispobj_"])

    def __len__(self):
        return len(self.__dict__["_dispobj_"])

    def __bool__(self):
        return bool(self.__dict__["_dispobj_"])


# 048667.python.init.line679.comment A very simple VARIANT class.  Only to be used with poorly-implemented COM
# 048668.python.init.line680.comment objects.  If an object accepts an arg which is a simple "VARIANT", but still
# 048669.python.init.line681.comment is very pickly about the actual variant type (eg, isn't happy with a VT_I4,
# 048670.python.init.line682.comment which it would get from a Python integer), you can use this to force a
# 048671.python.init.line683.comment particular VT.
class VARIANT:
    def __init__(self, vt, value):
        self.varianttype = vt
        self._value = value

    # 048672.python.init.line689.comment 'value' is a property so when set by pythoncom it gets any magic wrapping
    # 048673.python.init.line690.comment which normally happens for result objects
    def _get_value(self):
        return self._value

    def _set_value(self, newval):
        self._value = _get_good_object_(newval)

    def _del_value(self):
        del self._value

    value = property(_get_value, _set_value, _del_value)

    def __repr__(self):
        return f"win32com.client.VARIANT({self.varianttype!r}, {self._value!r})"
