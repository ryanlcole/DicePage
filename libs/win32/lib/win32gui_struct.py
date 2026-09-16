# 047326.python.win32gui_struct.line1.comment This is a work in progress - see Demos/win32gui_menu.py

# 047327.python.win32gui_struct.line3.comment win32gui_struct.py - helpers for working with various win32gui structures.
# 047328.python.win32gui_struct.line4.comment As win32gui is "light-weight", it does not define objects for all possible
# 047329.python.win32gui_struct.line5.comment win32 structures - in general, "buffer" objects are passed around - it is
# 047330.python.win32gui_struct.line6.comment the callers responsibility to pack the buffer in the correct format.
# 047331.python.win32gui_struct.line7.comment
# 047332.python.win32gui_struct.line8.comment This module defines some helpers for the commonly used structures.
# 047333.python.win32gui_struct.line9.comment
# 047334.python.win32gui_struct.line10.comment In general, each structure has 3 functions:
# 047335.python.win32gui_struct.line11.comment
# 047336.python.win32gui_struct.line12.comment buffer, extras = PackSTRUCTURE(items, ...)
# 047337.python.win32gui_struct.line13.comment item, ... = UnpackSTRUCTURE(buffer)
# 047338.python.win32gui_struct.line14.comment buffer, extras = EmtpySTRUCTURE(...)
# 047339.python.win32gui_struct.line15.comment
# 047340.python.win32gui_struct.line16.comment 'extras' is always items that must be held along with the buffer, as the
# 047341.python.win32gui_struct.line17.comment buffer refers to these object's memory.
# 047342.python.win32gui_struct.line18.comment For structures that support a 'mask', this mask is hidden from the user - if
# 047343.python.win32gui_struct.line19.comment 'None' is passed, the mask flag will not be set, or on return, None will
# 047344.python.win32gui_struct.line20.comment be returned for the value if the mask is not set.
# 047345.python.win32gui_struct.line21.comment
# 047346.python.win32gui_struct.line22.comment NOTE: I considered making these structures look like real classes, and
# 047347.python.win32gui_struct.line23.comment support 'attributes' etc - however, ctypes already has a good structure
# 047348.python.win32gui_struct.line24.comment mechanism - I think it makes more sense to support ctype structures
# 047349.python.win32gui_struct.line25.comment at the win32gui level, then there will be no need for this module at all.
# 047350.python.win32gui_struct.line26.comment XXX - the above makes sense in terms of what is built and passed to
# 047351.python.win32gui_struct.line27.comment win32gui (ie, the Pack* functions) - but doesn't make as much sense for
# 047352.python.win32gui_struct.line28.comment the Unpack* functions, where the aim is user convenience.

import array
import struct
import sys
from collections import namedtuple

import commctrl
import pywintypes
import win32con
import win32gui


def _MakeResult(names_str, values):
    names = names_str.split()
    # 047353.python.win32gui_struct.line43.comment TODO: Dynamic namedtuple. This could be made static, also exposing the types
    nt = namedtuple(names[0], names[1:])  # noqa: PYI024
    return nt(*values)


is64bit = "64 bit" in sys.version
_nmhdr_fmt = "PPi"
if is64bit:
    # 047355.python.win32gui_struct.line51.comment When the item past the NMHDR gets aligned (eg, when it is a struct)
    # 047356.python.win32gui_struct.line52.comment we need this many bytes padding.
    _nmhdr_align_padding = "xxxx"
else:
    _nmhdr_align_padding = ""


# 047357.python.win32gui_struct.line58.comment Encode a string suitable for passing in a win32gui related structure
def _make_text_buffer(text):
    if not isinstance(text, str):
        raise TypeError("MENUITEMINFO text must be unicode")
    data = (text + "\0").encode("utf-16le")
    return array.array("b", data)


# 047358.python.win32gui_struct.line66.comment make an 'empty' buffer, ready for filling with cch characters.
def _make_empty_text_buffer(cch):
    return _make_text_buffer("\0" * cch)


# 047359.python.win32gui_struct.line71.comment Generic WM_NOTIFY unpacking
def UnpackWMNOTIFY(lparam):
    format = "PPi"
    buf = win32gui.PyGetMemory(lparam, struct.calcsize(format))
    return _MakeResult("WMNOTIFY hwndFrom idFrom code", struct.unpack(format, buf))


def UnpackNMITEMACTIVATE(lparam):
    format = _nmhdr_fmt + _nmhdr_align_padding
    if is64bit:
        # 047360.python.win32gui_struct.line81.comment the struct module doesn't handle this correctly as some of the items
        # 047361.python.win32gui_struct.line82.comment are actually structs in structs, which get individually aligned.
        format += "iiiiiiixxxxP"
    else:
        format += "iiiiiiiP"
    buf = win32gui.PyMakeBuffer(struct.calcsize(format), lparam)
    return _MakeResult(
        "NMITEMACTIVATE hwndFrom idFrom code iItem iSubItem uNewState uOldState uChanged actionx actiony lParam",
        struct.unpack(format, buf),
    )


# 047362.python.win32gui_struct.line93.comment MENUITEMINFO struct
# 047363.python.win32gui_struct.line94.comment https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-menuiteminfow
# 047364.python.win32gui_struct.line95.comment We use the struct module to pack and unpack strings as MENUITEMINFO
# 047365.python.win32gui_struct.line96.comment structures.  We also have special handling for the 'fMask' item in that
# 047366.python.win32gui_struct.line97.comment structure to avoid the caller needing to explicitly check validity
# 047367.python.win32gui_struct.line98.comment (None is used if the mask excludes/should exclude the value)
_menuiteminfo_fmt = "5i5PiP"


def PackMENUITEMINFO(
    fType=None,
    fState=None,
    wID=None,
    hSubMenu=None,
    hbmpChecked=None,
    hbmpUnchecked=None,
    dwItemData=None,
    text=None,
    hbmpItem=None,
    dwTypeData=None,
):
    # 047368.python.win32gui_struct.line114.comment 'extras' are objects the caller must keep a reference to (as their
    # 047369.python.win32gui_struct.line115.comment memory is used) for the lifetime of the INFO item.
    extras = []
    # 047370.python.win32gui_struct.line117.comment ack - dwItemData and dwTypeData were confused for a while...
    assert dwItemData is None or dwTypeData is None, (
        "sorry - these were confused - you probably want dwItemData"
    )
    # 047371.python.win32gui_struct.line121.comment if we are a long way past 209, then we can nuke the above...
    if dwTypeData is not None:
        import warnings

        warnings.warn(
            "PackMENUITEMINFO: please use dwItemData instead of dwTypeData",
            DeprecationWarning,
            stacklevel=2,
        )
    if dwItemData is None:
        dwItemData = dwTypeData or 0

    fMask = 0
    if fType is None:
        fType = 0
    else:
        fMask |= win32con.MIIM_FTYPE
    if fState is None:
        fState = 0
    else:
        fMask |= win32con.MIIM_STATE
    if wID is None:
        wID = 0
    else:
        fMask |= win32con.MIIM_ID
    if hSubMenu is None:
        hSubMenu = 0
    else:
        fMask |= win32con.MIIM_SUBMENU
    if hbmpChecked is None:
        assert hbmpUnchecked is None, "neither or both checkmark bmps must be given"
        hbmpChecked = hbmpUnchecked = 0
    else:
        assert hbmpUnchecked is not None, "neither or both checkmark bmps must be given"
        fMask |= win32con.MIIM_CHECKMARKS
    if dwItemData is None:
        dwItemData = 0
    else:
        fMask |= win32con.MIIM_DATA
    if hbmpItem is None:
        hbmpItem = 0
    else:
        fMask |= win32con.MIIM_BITMAP
    if text is not None:
        fMask |= win32con.MIIM_STRING
        str_buf = _make_text_buffer(text)
        cch = len(text)
        # 047372.python.win32gui_struct.line168.comment We are taking address of strbuf - it must not die until windows
        # 047373.python.win32gui_struct.line169.comment has finished with our structure.
        lptext = str_buf.buffer_info()[0]
        extras.append(str_buf)
    else:
        lptext = 0
        cch = 0
    # 047374.python.win32gui_struct.line175.comment Create the struct.
    # 047375.python.win32gui_struct.line176.comment 'P' format does not accept PyHANDLE's !
    item = struct.pack(
        _menuiteminfo_fmt,
        struct.calcsize(_menuiteminfo_fmt),  # cbSize
        fMask,
        fType,
        fState,
        wID,
        int(hSubMenu),
        int(hbmpChecked),
        int(hbmpUnchecked),
        dwItemData,
        lptext,
        cch,
        int(hbmpItem),
    )
    # 047377.python.win32gui_struct.line192.comment Now copy the string to a writable buffer, so that the result
    # 047378.python.win32gui_struct.line193.comment could be passed to a 'Get' function
    return array.array("b", item), extras


def UnpackMENUITEMINFO(s):
    (
        cb,
        fMask,
        fType,
        fState,
        wID,
        hSubMenu,
        hbmpChecked,
        hbmpUnchecked,
        dwItemData,
        lptext,
        cch,
        hbmpItem,
    ) = struct.unpack(_menuiteminfo_fmt, s)
    assert cb == len(s)
    if fMask & win32con.MIIM_FTYPE == 0:
        fType = None
    if fMask & win32con.MIIM_STATE == 0:
        fState = None
    if fMask & win32con.MIIM_ID == 0:
        wID = None
    if fMask & win32con.MIIM_SUBMENU == 0:
        hSubMenu = None
    if fMask & win32con.MIIM_CHECKMARKS == 0:
        hbmpChecked = hbmpUnchecked = None
    if fMask & win32con.MIIM_DATA == 0:
        dwItemData = None
    if fMask & win32con.MIIM_BITMAP == 0:
        hbmpItem = None
    if fMask & win32con.MIIM_STRING:
        text = win32gui.PyGetString(lptext, cch)
    else:
        text = None
    return _MakeResult(
        "MENUITEMINFO fType fState wID hSubMenu hbmpChecked "
        "hbmpUnchecked dwItemData text hbmpItem",
        (
            fType,
            fState,
            wID,
            hSubMenu,
            hbmpChecked,
            hbmpUnchecked,
            dwItemData,
            text,
            hbmpItem,
        ),
    )


def EmptyMENUITEMINFO(mask=None, text_buf_size=512):
    # 047379.python.win32gui_struct.line249.comment text_buf_size is number of *characters* - not necessarily no of bytes.
    extra = []
    if mask is None:
        mask = (
            win32con.MIIM_BITMAP
            | win32con.MIIM_CHECKMARKS
            | win32con.MIIM_DATA
            | win32con.MIIM_FTYPE
            | win32con.MIIM_ID
            | win32con.MIIM_STATE
            | win32con.MIIM_STRING
            | win32con.MIIM_SUBMENU
        )
        # 047380.python.win32gui_struct.line262.comment Note: No MIIM_TYPE - this screws win2k/98.

    if mask & win32con.MIIM_STRING:
        text_buffer = _make_empty_text_buffer(text_buf_size)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
    else:
        text_addr = text_buf_size = 0

    # 047381.python.win32gui_struct.line271.comment Now copy the string to a writable buffer, so that the result
    # 047382.python.win32gui_struct.line272.comment could be passed to a 'Get' function
    buf = struct.pack(
        _menuiteminfo_fmt,
        struct.calcsize(_menuiteminfo_fmt),  # cbSize
        mask,
        0,  # fType,
        0,  # fState,
        0,  # wID,
        0,  # hSubMenu,
        0,  # hbmpChecked,
        0,  # hbmpUnchecked,
        0,  # dwItemData,
        text_addr,
        text_buf_size,
        0,  # hbmpItem
    )
    return array.array("b", buf), extra


# 047392.python.win32gui_struct.line291.comment MENUINFO struct
_menuinfo_fmt = "iiiiPiP"


def PackMENUINFO(
    dwStyle=None,
    cyMax=None,
    hbrBack=None,
    dwContextHelpID=None,
    dwMenuData=None,
    fMask=0,
):
    if dwStyle is None:
        dwStyle = 0
    else:
        fMask |= win32con.MIM_STYLE
    if cyMax is None:
        cyMax = 0
    else:
        fMask |= win32con.MIM_MAXHEIGHT
    if hbrBack is None:
        hbrBack = 0
    else:
        fMask |= win32con.MIM_BACKGROUND
    if dwContextHelpID is None:
        dwContextHelpID = 0
    else:
        fMask |= win32con.MIM_HELPID
    if dwMenuData is None:
        dwMenuData = 0
    else:
        fMask |= win32con.MIM_MENUDATA
    # 047393.python.win32gui_struct.line323.comment Create the struct.
    item = struct.pack(
        _menuinfo_fmt,
        struct.calcsize(_menuinfo_fmt),  # cbSize
        fMask,
        dwStyle,
        cyMax,
        hbrBack,
        dwContextHelpID,
        dwMenuData,
    )
    return array.array("b", item)


def UnpackMENUINFO(s):
    (cb, fMask, dwStyle, cyMax, hbrBack, dwContextHelpID, dwMenuData) = struct.unpack(
        _menuinfo_fmt, s
    )
    assert cb == len(s)
    if fMask & win32con.MIM_STYLE == 0:
        dwStyle = None
    if fMask & win32con.MIM_MAXHEIGHT == 0:
        cyMax = None
    if fMask & win32con.MIM_BACKGROUND == 0:
        hbrBack = None
    if fMask & win32con.MIM_HELPID == 0:
        dwContextHelpID = None
    if fMask & win32con.MIM_MENUDATA == 0:
        dwMenuData = None
    return _MakeResult(
        "MENUINFO dwStyle cyMax hbrBack dwContextHelpID dwMenuData",
        (dwStyle, cyMax, hbrBack, dwContextHelpID, dwMenuData),
    )


def EmptyMENUINFO(mask=None):
    if mask is None:
        mask = (
            win32con.MIM_STYLE
            | win32con.MIM_MAXHEIGHT
            | win32con.MIM_BACKGROUND
            | win32con.MIM_HELPID
            | win32con.MIM_MENUDATA
        )

    buf = struct.pack(
        _menuinfo_fmt,
        struct.calcsize(_menuinfo_fmt),  # cbSize
        mask,
        0,  # dwStyle
        0,  # cyMax
        0,  # hbrBack,
        0,  # dwContextHelpID,
        0,  # dwMenuData,
    )
    return array.array("b", buf)


# 047401.python.win32gui_struct.line381.comment #########################################################################
# 047402.python.win32gui_struct.line382.comment
# 047403.python.win32gui_struct.line383.comment Tree View structure support - TVITEM, TVINSERTSTRUCT and TVDISPINFO
# 047404.python.win32gui_struct.line384.comment
# 047405.python.win32gui_struct.line385.comment #########################################################################

# 047406.python.win32gui_struct.line387.comment XXX - Note that the following implementation of TreeView structures is ripped
# 047407.python.win32gui_struct.line388.comment XXX - from the SpamBayes project.  It may not quite work correctly yet - I
# 047408.python.win32gui_struct.line389.comment XXX - intend checking them later - but having them is better than not at all!

_tvitem_fmt = "iPiiPiiiiP"


# 047409.python.win32gui_struct.line394.comment Helpers for the ugly win32 structure packing/unpacking
# 047410.python.win32gui_struct.line395.comment XXX - Note that functions using _GetMaskAndVal run 3x faster if they are
# 047411.python.win32gui_struct.line396.comment 'inlined' into the function - see PackLVITEM.  If the profiler points at
# 047412.python.win32gui_struct.line397.comment _GetMaskAndVal(), you should nuke it (patches welcome once they have been
# 047413.python.win32gui_struct.line398.comment tested)
def _GetMaskAndVal(val, default, mask, flag):
    if val is None:
        return mask, default
    else:
        if flag is not None:
            mask |= flag
        return mask, val


def PackTVINSERTSTRUCT(parent, insertAfter, tvitem):
    tvitem_buf, extra = PackTVITEM(*tvitem)
    tvitem_buf = tvitem_buf.tobytes()
    format = "PP%ds" % len(tvitem_buf)
    return struct.pack(format, parent, insertAfter, tvitem_buf), extra


def PackTVITEM(hitem, state, stateMask, text, image, selimage, citems, param):
    extra = []  # objects we must keep references to
    mask = 0
    mask, hitem = _GetMaskAndVal(hitem, 0, mask, commctrl.TVIF_HANDLE)
    mask, state = _GetMaskAndVal(state, 0, mask, commctrl.TVIF_STATE)
    if not mask & commctrl.TVIF_STATE:
        stateMask = 0
    mask, text = _GetMaskAndVal(text, None, mask, commctrl.TVIF_TEXT)
    mask, image = _GetMaskAndVal(image, 0, mask, commctrl.TVIF_IMAGE)
    mask, selimage = _GetMaskAndVal(selimage, 0, mask, commctrl.TVIF_SELECTEDIMAGE)
    mask, citems = _GetMaskAndVal(citems, 0, mask, commctrl.TVIF_CHILDREN)
    mask, param = _GetMaskAndVal(param, 0, mask, commctrl.TVIF_PARAM)
    if text is None:
        text_addr = text_len = 0
    else:
        text_buffer = _make_text_buffer(text)
        text_len = len(text)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
    buf = struct.pack(
        _tvitem_fmt,
        mask,
        hitem,
        state,
        stateMask,
        text_addr,
        text_len,  # text
        image,
        selimage,
        citems,
        param,
    )
    return array.array("b", buf), extra


# 047416.python.win32gui_struct.line450.comment Make a new buffer suitable for querying hitem's attributes.
def EmptyTVITEM(hitem, mask=None, text_buf_size=512):
    extra = []  # objects we must keep references to
    if mask is None:
        mask = (
            commctrl.TVIF_HANDLE
            | commctrl.TVIF_STATE
            | commctrl.TVIF_TEXT
            | commctrl.TVIF_IMAGE
            | commctrl.TVIF_SELECTEDIMAGE
            | commctrl.TVIF_CHILDREN
            | commctrl.TVIF_PARAM
        )
    if mask & commctrl.TVIF_TEXT:
        text_buffer = _make_empty_text_buffer(text_buf_size)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
    else:
        text_addr = text_buf_size = 0
    buf = struct.pack(
        _tvitem_fmt, mask, hitem, 0, 0, text_addr, text_buf_size, 0, 0, 0, 0
    )
    return array.array("b", buf), extra


def UnpackTVITEM(buffer):
    (
        item_mask,
        item_hItem,
        item_state,
        item_stateMask,
        item_textptr,
        item_cchText,
        item_image,
        item_selimage,
        item_cChildren,
        item_param,
    ) = struct.unpack(_tvitem_fmt, buffer)
    # 047418.python.win32gui_struct.line488.comment ensure only items listed by the mask are valid (except we assume the
    # 047419.python.win32gui_struct.line489.comment handle is always valid - some notifications (eg, TVN_ENDLABELEDIT) set a
    # 047420.python.win32gui_struct.line490.comment mask that doesn't include the handle, but the docs explicity say it is.)
    if not (item_mask & commctrl.TVIF_TEXT):
        item_textptr = item_cchText = None
    if not (item_mask & commctrl.TVIF_CHILDREN):
        item_cChildren = None
    if not (item_mask & commctrl.TVIF_IMAGE):
        item_image = None
    if not (item_mask & commctrl.TVIF_PARAM):
        item_param = None
    if not (item_mask & commctrl.TVIF_SELECTEDIMAGE):
        item_selimage = None
    if not (item_mask & commctrl.TVIF_STATE):
        item_state = item_stateMask = None

    if item_textptr:
        text = win32gui.PyGetString(item_textptr)
    else:
        text = None
    return _MakeResult(
        "TVITEM item_hItem item_state item_stateMask "
        "text item_image item_selimage item_cChildren item_param",
        (
            item_hItem,
            item_state,
            item_stateMask,
            text,
            item_image,
            item_selimage,
            item_cChildren,
            item_param,
        ),
    )


# 047421.python.win32gui_struct.line524.comment Unpack the lparm from a "TVNOTIFY" message
def UnpackTVNOTIFY(lparam):
    item_size = struct.calcsize(_tvitem_fmt)
    format = _nmhdr_fmt + _nmhdr_align_padding
    if is64bit:
        format += "ixxxx"
    else:
        format += "i"
    format += "%ds%ds" % (item_size, item_size)
    buf = win32gui.PyGetMemory(lparam, struct.calcsize(format))
    hwndFrom, id, code, action, buf_old, buf_new = struct.unpack(format, buf)
    item_old = UnpackTVITEM(buf_old)
    item_new = UnpackTVITEM(buf_new)
    return _MakeResult(
        "TVNOTIFY hwndFrom id code action item_old item_new",
        (hwndFrom, id, code, action, item_old, item_new),
    )


def UnpackTVDISPINFO(lparam):
    item_size = struct.calcsize(_tvitem_fmt)
    format = "PPi%ds" % (item_size,)
    buf = win32gui.PyGetMemory(lparam, struct.calcsize(format))
    hwndFrom, id, code, buf_item = struct.unpack(format, buf)
    item = UnpackTVITEM(buf_item)
    return _MakeResult("TVDISPINFO hwndFrom id code item", (hwndFrom, id, code, item))


# 047422.python.win32gui_struct.line552.comment
# 047423.python.win32gui_struct.line553.comment List view items
_lvitem_fmt = "iiiiiPiiPi"


def PackLVITEM(
    item=None,
    subItem=None,
    state=None,
    stateMask=None,
    text=None,
    image=None,
    param=None,
    indent=None,
):
    extra = []  # objects we must keep references to
    mask = 0
    # 047425.python.win32gui_struct.line569.comment _GetMaskAndVal adds quite a bit of overhead to this function.
    if item is None:
        item = 0  # No mask for item
    if subItem is None:
        subItem = 0  # No mask for sibItem
    if state is None:
        state = 0
        stateMask = 0
    else:
        mask |= commctrl.LVIF_STATE
        if stateMask is None:
            stateMask = state

    if image is None:
        image = 0
    else:
        mask |= commctrl.LVIF_IMAGE
    if param is None:
        param = 0
    else:
        mask |= commctrl.LVIF_PARAM
    if indent is None:
        indent = 0
    else:
        mask |= commctrl.LVIF_INDENT

    if text is None:
        text_addr = text_len = 0
    else:
        mask |= commctrl.LVIF_TEXT
        text_buffer = _make_text_buffer(text)
        text_len = len(text)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
    buf = struct.pack(
        _lvitem_fmt,
        mask,
        item,
        subItem,
        state,
        stateMask,
        text_addr,
        text_len,  # text
        image,
        param,
        indent,
    )
    return array.array("b", buf), extra


def UnpackLVITEM(buffer):
    (
        item_mask,
        item_item,
        item_subItem,
        item_state,
        item_stateMask,
        item_textptr,
        item_cchText,
        item_image,
        item_param,
        item_indent,
    ) = struct.unpack(_lvitem_fmt, buffer)
    # 047429.python.win32gui_struct.line632.comment ensure only items listed by the mask are valid
    if not (item_mask & commctrl.LVIF_TEXT):
        item_textptr = item_cchText = None
    if not (item_mask & commctrl.LVIF_IMAGE):
        item_image = None
    if not (item_mask & commctrl.LVIF_PARAM):
        item_param = None
    if not (item_mask & commctrl.LVIF_INDENT):
        item_indent = None
    if not (item_mask & commctrl.LVIF_STATE):
        item_state = item_stateMask = None

    if item_textptr:
        text = win32gui.PyGetString(item_textptr)
    else:
        text = None
    return _MakeResult(
        "LVITEM item_item item_subItem item_state "
        "item_stateMask text item_image item_param item_indent",
        (
            item_item,
            item_subItem,
            item_state,
            item_stateMask,
            text,
            item_image,
            item_param,
            item_indent,
        ),
    )


# 047430.python.win32gui_struct.line664.comment Unpack an "LVNOTIFY" message
def UnpackLVDISPINFO(lparam):
    item_size = struct.calcsize(_lvitem_fmt)
    format = _nmhdr_fmt + _nmhdr_align_padding + ("%ds" % (item_size,))
    buf = win32gui.PyGetMemory(lparam, struct.calcsize(format))
    hwndFrom, id, code, buf_item = struct.unpack(format, buf)
    item = UnpackLVITEM(buf_item)
    return _MakeResult("LVDISPINFO hwndFrom id code item", (hwndFrom, id, code, item))


def UnpackLVNOTIFY(lparam):
    format = _nmhdr_fmt + _nmhdr_align_padding + "7i"
    if is64bit:
        format += "xxxx"  # point needs padding.
    format += "P"
    buf = win32gui.PyGetMemory(lparam, struct.calcsize(format))
    (
        hwndFrom,
        id,
        code,
        item,
        subitem,
        newstate,
        oldstate,
        changed,
        pt_x,
        pt_y,
        lparam,
    ) = struct.unpack(format, buf)
    return _MakeResult(
        "UnpackLVNOTIFY hwndFrom id code item subitem "
        "newstate oldstate changed pt lparam",
        (
            hwndFrom,
            id,
            code,
            item,
            subitem,
            newstate,
            oldstate,
            changed,
            (pt_x, pt_y),
            lparam,
        ),
    )


# 047432.python.win32gui_struct.line711.comment Make a new buffer suitable for querying an items attributes.
def EmptyLVITEM(item, subitem, mask=None, text_buf_size=512):
    extra = []  # objects we must keep references to
    if mask is None:
        mask = (
            commctrl.LVIF_IMAGE
            | commctrl.LVIF_INDENT
            | commctrl.LVIF_TEXT
            | commctrl.LVIF_PARAM
            | commctrl.LVIF_STATE
        )
    if mask & commctrl.LVIF_TEXT:
        text_buffer = _make_empty_text_buffer(text_buf_size)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
    else:
        text_addr = text_buf_size = 0
    buf = struct.pack(
        _lvitem_fmt,
        mask,
        item,
        subitem,
        0,
        0,
        text_addr,
        text_buf_size,  # text
        0,
        0,
        0,
    )
    return array.array("b", buf), extra


# 047435.python.win32gui_struct.line744.comment List view column structure
_lvcolumn_fmt = "iiiPiiii"


def PackLVCOLUMN(fmt=None, cx=None, text=None, subItem=None, image=None, order=None):
    extra = []  # objects we must keep references to
    mask = 0
    mask, fmt = _GetMaskAndVal(fmt, 0, mask, commctrl.LVCF_FMT)
    mask, cx = _GetMaskAndVal(cx, 0, mask, commctrl.LVCF_WIDTH)
    mask, text = _GetMaskAndVal(text, None, mask, commctrl.LVCF_TEXT)
    mask, subItem = _GetMaskAndVal(subItem, 0, mask, commctrl.LVCF_SUBITEM)
    mask, image = _GetMaskAndVal(image, 0, mask, commctrl.LVCF_IMAGE)
    mask, order = _GetMaskAndVal(order, 0, mask, commctrl.LVCF_ORDER)
    if text is None:
        text_addr = text_len = 0
    else:
        text_buffer = _make_text_buffer(text)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
        text_len = len(text)
    buf = struct.pack(
        _lvcolumn_fmt, mask, fmt, cx, text_addr, text_len, subItem, image, order
    )
    return array.array("b", buf), extra


def UnpackLVCOLUMN(lparam):
    mask, fmt, cx, text_addr, text_size, subItem, image, order = struct.unpack(
        _lvcolumn_fmt, lparam
    )
    # 047437.python.win32gui_struct.line774.comment ensure only items listed by the mask are valid
    if not (mask & commctrl.LVCF_FMT):
        fmt = None
    if not (mask & commctrl.LVCF_WIDTH):
        cx = None
    if not (mask & commctrl.LVCF_TEXT):
        text_addr = text_size = None
    if not (mask & commctrl.LVCF_SUBITEM):
        subItem = None
    if not (mask & commctrl.LVCF_IMAGE):
        image = None
    if not (mask & commctrl.LVCF_ORDER):
        order = None
    if text_addr:
        text = win32gui.PyGetString(text_addr)
    else:
        text = None
    return _MakeResult(
        "LVCOLUMN fmt cx text subItem image order",
        (fmt, cx, text, subItem, image, order),
    )


# 047438.python.win32gui_struct.line797.comment Make a new buffer suitable for querying an items attributes.
def EmptyLVCOLUMN(mask=None, text_buf_size=512):
    extra = []  # objects we must keep references to
    if mask is None:
        mask = (
            commctrl.LVCF_FMT
            | commctrl.LVCF_WIDTH
            | commctrl.LVCF_TEXT
            | commctrl.LVCF_SUBITEM
            | commctrl.LVCF_IMAGE
            | commctrl.LVCF_ORDER
        )
    if mask & commctrl.LVCF_TEXT:
        text_buffer = _make_empty_text_buffer(text_buf_size)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
    else:
        text_addr = text_buf_size = 0
    buf = struct.pack(_lvcolumn_fmt, mask, 0, 0, text_addr, text_buf_size, 0, 0, 0)
    return array.array("b", buf), extra


# 047440.python.win32gui_struct.line819.comment List view hit-test.
def PackLVHITTEST(pt):
    format = "iiiii"
    buf = struct.pack(format, pt[0], pt[1], 0, 0, 0)
    return array.array("b", buf), None


def UnpackLVHITTEST(buf):
    format = "iiiii"
    x, y, flags, item, subitem = struct.unpack(format, buf)
    return _MakeResult(
        "LVHITTEST pt flags item subitem", ((x, y), flags, item, subitem)
    )


def PackHDITEM(
    cxy=None, text=None, hbm=None, fmt=None, param=None, image=None, order=None
):
    extra = []  # objects we must keep references to
    mask = 0
    mask, cxy = _GetMaskAndVal(cxy, 0, mask, commctrl.HDI_HEIGHT)
    mask, text = _GetMaskAndVal(text, None, mask, commctrl.LVCF_TEXT)
    mask, hbm = _GetMaskAndVal(hbm, 0, mask, commctrl.HDI_BITMAP)
    mask, fmt = _GetMaskAndVal(fmt, 0, mask, commctrl.HDI_FORMAT)
    mask, param = _GetMaskAndVal(param, 0, mask, commctrl.HDI_LPARAM)
    mask, image = _GetMaskAndVal(image, 0, mask, commctrl.HDI_IMAGE)
    mask, order = _GetMaskAndVal(order, 0, mask, commctrl.HDI_ORDER)

    if text is None:
        text_addr = text_len = 0
    else:
        text_buffer = _make_text_buffer(text)
        extra.append(text_buffer)
        text_addr, _ = text_buffer.buffer_info()
        text_len = len(text)

    format = "iiPPiiPiiii"
    buf = struct.pack(
        format, mask, cxy, text_addr, hbm, text_len, fmt, param, image, order, 0, 0
    )
    return array.array("b", buf), extra


# 047442.python.win32gui_struct.line862.comment Device notification stuff


# 047443.python.win32gui_struct.line865.comment Generic function for packing a DEV_BROADCAST_* structure - generally used
# 047444.python.win32gui_struct.line866.comment by the other PackDEV_BROADCAST_* functions in this module.
def PackDEV_BROADCAST(devicetype, rest_fmt, rest_data, extra_data=b""):
    # 047445.python.win32gui_struct.line868.comment It seems a requirement is 4 byte alignment, even for the 'BYTE data[1]'
    # 047446.python.win32gui_struct.line869.comment field (eg, that would make DEV_BROADCAST_HANDLE 41 bytes, but we must
    # 047447.python.win32gui_struct.line870.comment be 44.
    extra_data += b"\0" * (4 - len(extra_data) % 4)
    format = "iii" + rest_fmt
    full_size = struct.calcsize(format) + len(extra_data)
    data = (full_size, devicetype, 0) + rest_data
    return struct.pack(format, *data) + extra_data


def PackDEV_BROADCAST_HANDLE(
    handle,
    hdevnotify=0,
    guid=b"\0" * 16,
    name_offset=0,
    data=b"\0",
):
    return PackDEV_BROADCAST(
        win32con.DBT_DEVTYP_HANDLE,
        "PP16sl",
        (int(handle), int(hdevnotify), bytes(memoryview(guid)), name_offset),
        data,
    )


def PackDEV_BROADCAST_VOLUME(unitmask, flags):
    return PackDEV_BROADCAST(win32con.DBT_DEVTYP_VOLUME, "II", (unitmask, flags))


def PackDEV_BROADCAST_DEVICEINTERFACE(classguid, name=""):
    if not isinstance(name, str):
        raise TypeError("Must provide unicode for the name")
    name = name.encode("utf-16le")

    # 047448.python.win32gui_struct.line902.comment 16 bytes for the IID followed by \0 term'd string.
    rest_fmt = "16s%ds" % len(name)
    # 047449.python.win32gui_struct.line904.comment bytes(memoryview(iid)) hoops necessary to get the raw IID bytes.
    rest_data = (bytes(memoryview(pywintypes.IID(classguid))), name)
    return PackDEV_BROADCAST(win32con.DBT_DEVTYP_DEVICEINTERFACE, rest_fmt, rest_data)


# 047450.python.win32gui_struct.line909.comment An object returned by UnpackDEV_BROADCAST.
class DEV_BROADCAST_INFO:
    def __init__(self, devicetype, **kw):
        self.devicetype = devicetype
        self.__dict__.update(kw)

    def __str__(self):
        return "DEV_BROADCAST_INFO:" + str(self.__dict__)


# 047451.python.win32gui_struct.line919.comment Support for unpacking the 'lparam'
def UnpackDEV_BROADCAST(lparam):
    if lparam == 0:
        return None
    hdr_format = "iii"
    hdr_size = struct.calcsize(hdr_format)
    hdr_buf = win32gui.PyGetMemory(lparam, hdr_size)
    size, devtype, reserved = struct.unpack("iii", hdr_buf)
    # 047452.python.win32gui_struct.line927.comment Due to x64 alignment issues, we need to use the full format string over
    # 047453.python.win32gui_struct.line928.comment the entire buffer.  ie, on x64:
    # 047454.python.win32gui_struct.line929.comment calcsize('iiiP') != calcsize('iii')+calcsize('P')
    buf = win32gui.PyGetMemory(lparam, size)

    extra = x = {}
    if devtype == win32con.DBT_DEVTYP_HANDLE:
        # 047455.python.win32gui_struct.line934.comment 2 handles, a GUID, a LONG and possibly an array following...
        fmt = hdr_format + "PP16sl"
        (
            _,
            _,
            _,
            x["handle"],
            x["hdevnotify"],
            guid_bytes,
            x["nameoffset"],
        ) = struct.unpack(fmt, buf[: struct.calcsize(fmt)])
        x["eventguid"] = pywintypes.IID(guid_bytes, True)
    elif devtype == win32con.DBT_DEVTYP_DEVICEINTERFACE:
        fmt = hdr_format + "16s"
        _, _, _, guid_bytes = struct.unpack(fmt, buf[: struct.calcsize(fmt)])
        x["classguid"] = pywintypes.IID(guid_bytes, True)
        x["name"] = win32gui.PyGetString(lparam + struct.calcsize(fmt))
    elif devtype == win32con.DBT_DEVTYP_VOLUME:
        # 047456.python.win32gui_struct.line952.comment int mask and flags
        fmt = hdr_format + "II"
        _, _, _, x["unitmask"], x["flags"] = struct.unpack(
            fmt, buf[: struct.calcsize(fmt)]
        )
    elif devtype == win32con.DBT_DEVTYP_PORT:
        x["name"] = win32gui.PyGetString(lparam + struct.calcsize(hdr_format))
    else:
        raise NotImplementedError("unknown device type %d" % (devtype,))
    return DEV_BROADCAST_INFO(devtype, **extra)
