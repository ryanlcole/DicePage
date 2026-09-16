# 051459.python.mapiutil.line1.comment General utilities for MAPI and MAPI objects.
from __future__ import annotations

import pythoncom
from pywintypes import TimeType

from . import mapi, mapitags

prTable: dict[int, str] = {}


def GetPropTagName(pt):
    if not prTable:
        for name, value in mapitags.__dict__.items():
            if name[:3] == "PR_":
                # 051460.python.mapiutil.line16.comment Store both the full ID (including type) and just the ID.
                # 051461.python.mapiutil.line17.comment This is so PR_FOO_A and PR_FOO_W are still differentiated,
                # 051462.python.mapiutil.line18.comment but should we get a PT_FOO with PT_ERROR set, we fallback
                # 051463.python.mapiutil.line19.comment to the ID.

                # 051464.python.mapiutil.line21.comment String types should have 3 definitions in mapitags.py
                # 051465.python.mapiutil.line22.comment PR_BODY	= PROP_TAG( PT_TSTRING,	4096)
                # 051466.python.mapiutil.line23.comment PR_BODY_W	= PROP_TAG( PT_UNICODE, 4096)
                # 051467.python.mapiutil.line24.comment PR_BODY_A	= PROP_TAG( PT_STRING8, 4096)
                # 051468.python.mapiutil.line25.comment The following change ensures a lookup using only the the
                # 051469.python.mapiutil.line26.comment property id returns the conditional default.

                # 051470.python.mapiutil.line28.comment PT_TSTRING is a conditional assignment for either PT_UNICODE or
                # 051471.python.mapiutil.line29.comment PT_STRING8 and should not be returned during a lookup.

                if (
                    mapitags.PROP_TYPE(value) == mapitags.PT_UNICODE
                    or mapitags.PROP_TYPE(value) == mapitags.PT_STRING8
                ):
                    if name[-2:] == "_A" or name[-2:] == "_W":
                        prTable[value] = name
                    else:
                        prTable[mapitags.PROP_ID(value)] = name

                else:
                    prTable[value] = name
                    prTable[mapitags.PROP_ID(value)] = name

    try:
        try:
            return prTable[pt]
        except KeyError:
            # 051472.python.mapiutil.line48.comment Can't find it exactly - see if the raw ID exists.
            return prTable[mapitags.PROP_ID(pt)]
    except KeyError:
        # 051473.python.mapiutil.line51.comment god-damn bullshit hex() warnings: I don't see a way to get the
        # 051474.python.mapiutil.line52.comment old behaviour without a warning!!
        ret = hex(int(pt))
        # 051475.python.mapiutil.line54.comment -0x8000000L -> 0x80000000
        if ret[0] == "-":
            ret = ret[1:]
        if ret[-1] == "L":
            ret = ret[:-1]
        return ret


mapiErrorTable: dict[int, str] = {}


def GetScodeString(hr):
    if not mapiErrorTable:
        for name, value in mapi.__dict__.items():
            if name[:7] in ["MAPI_E_", "MAPI_W_"]:
                mapiErrorTable[value] = name
    return mapiErrorTable.get(hr, pythoncom.GetScodeString(hr))


ptTable: dict[int, str] = {}


def GetMapiTypeName(propType, rawType=True):
    """Given a mapi type flag, return a string description of the type"""
    if not ptTable:
        for name, value in mapitags.__dict__.items():
            if name[:3] == "PT_":
                # 051476.python.mapiutil.line81.comment PT_TSTRING is a conditional assignment
                # 051477.python.mapiutil.line82.comment for either PT_UNICODE or PT_STRING8 and
                # 051478.python.mapiutil.line83.comment should not be returned during a lookup.
                if name in ["PT_TSTRING", "PT_MV_TSTRING"]:
                    continue
                ptTable[value] = name

    if rawType:
        propType &= ~mapitags.MV_FLAG
    return ptTable.get(propType, str(hex(propType)))


def GetProperties(obj, propList):
    """Given a MAPI object and a list of properties, return a list of property values.

    Allows a single property to be passed, and the result is a single object.

    Each request property can be an integer or a string.  Of a string, it is
    automatically converted to an integer via the GetIdsFromNames function.

    If the property fetch fails, the result is None.
    """
    bRetList = 1
    if not isinstance(propList, (tuple, list)):
        bRetList = 0
        propList = (propList,)
    realPropList = []
    rc = []
    for prop in propList:
        if not isinstance(prop, int):
            props = ((mapi.PS_PUBLIC_STRINGS, prop),)
            propIds = obj.GetIDsFromNames(props, 0)
            prop = mapitags.PROP_TAG(
                mapitags.PT_UNSPECIFIED, mapitags.PROP_ID(propIds[0])
            )
        realPropList.append(prop)

    hr, data = obj.GetProps(realPropList, 0)
    if hr != 0:
        data = None
        return None
    if bRetList:
        return [v[1] for v in data]
    else:
        return data[0][1]


def GetAllProperties(obj, make_tag_names=True):
    tags = obj.GetPropList(0)
    hr, data = obj.GetProps(tags)
    ret = []
    for tag, val in data:
        if make_tag_names:
            hr, tags, array = obj.GetNamesFromIDs((tag,))
            if isinstance(array[0][1], str):
                name = array[0][1]
            else:
                name = GetPropTagName(tag)
        else:
            name = tag
        ret.append((name, val))
    return ret


_MapiTypeMap = {
    float: mapitags.PT_DOUBLE,
    int: mapitags.PT_I4,
    bytes: mapitags.PT_STRING8,
    str: mapitags.PT_UNICODE,
    type(None): mapitags.PT_UNSPECIFIED,
    bool: mapitags.PT_BOOLEAN,
}


def SetPropertyValue(obj, prop, val):
    if not isinstance(prop, int):
        props = ((mapi.PS_PUBLIC_STRINGS, prop),)
        propIds = obj.GetIDsFromNames(props, mapi.MAPI_CREATE)
        if val == True or val == False:
            type_tag = mapitags.PT_BOOLEAN
        else:
            type_tag = _MapiTypeMap.get(type(val))
            if type_tag is None:
                raise ValueError(
                    f"Don't know what to do with '{val!r}' ('{type(val)}')"
                )
        prop = mapitags.PROP_TAG(type_tag, mapitags.PROP_ID(propIds[0]))
    if val is None:
        # 051479.python.mapiutil.line169.comment Delete the property
        obj.DeleteProps((prop,))
    else:
        obj.SetProps(((prop, val),))


def SetProperties(msg, propDict):
    """Given a Python dictionary, set the objects properties.

    If the dictionary key is a string, then a property ID is queried
    otherwise the ID is assumed native.

    Coded for maximum efficiency wrt server calls - ie, maximum of
    2 calls made to the object, regardless of the dictionary contents
    (only 1 if dictionary full of int keys)
    """

    newProps = []
    # 051480.python.mapiutil.line187.comment First pass over the properties we should get IDs for.
    for key, val in propDict.items():
        if isinstance(key, str):
            newProps.append((mapi.PS_PUBLIC_STRINGS, key))
    # 051481.python.mapiutil.line191.comment Query for the new IDs
    if newProps:
        newIds = msg.GetIDsFromNames(newProps, mapi.MAPI_CREATE)
    newIdNo = 0
    newProps = []
    for key, val in propDict.items():
        if isinstance(key, str):
            if isinstance(val, str):
                tagType = mapitags.PT_UNICODE
            elif isinstance(val, int):
                tagType = mapitags.PT_I4
            elif isinstance(val, TimeType):
                tagType = mapitags.PT_SYSTIME
            else:
                raise ValueError(
                    f"The type of object {val!r}({type(val)}) can not be written"
                )
            key = mapitags.PROP_TAG(tagType, mapitags.PROP_ID(newIds[newIdNo]))
            newIdNo += 1
        newProps.append((key, val))
    msg.SetProps(newProps)
