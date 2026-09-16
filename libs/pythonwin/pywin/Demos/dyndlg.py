# 036715.python.dyndlg.line1.comment dyndlg.py
# 036716.python.dyndlg.line2.comment contributed by Curt Hagenlocher <chi@earthlink.net>

# 036717.python.dyndlg.line4.comment Dialog Template params:
# 036718.python.dyndlg.line5.comment Parameter 0 - Window caption
# 036719.python.dyndlg.line6.comment Parameter 1 - Bounds (rect tuple)
# 036720.python.dyndlg.line7.comment Parameter 2 - Window style
# 036721.python.dyndlg.line8.comment Parameter 3 - Extended style
# 036722.python.dyndlg.line9.comment Parameter 4 - Font tuple
# 036723.python.dyndlg.line10.comment Parameter 5 - Menu name
# 036724.python.dyndlg.line11.comment Parameter 6 - Window class
# 036725.python.dyndlg.line12.comment Dialog item params:
# 036726.python.dyndlg.line13.comment Parameter 0 - Window class
# 036727.python.dyndlg.line14.comment Parameter 1 - Text
# 036728.python.dyndlg.line15.comment Parameter 2 - ID
# 036729.python.dyndlg.line16.comment Parameter 3 - Bounds
# 036730.python.dyndlg.line17.comment Parameter 4 - Style
# 036731.python.dyndlg.line18.comment Parameter 5 - Extended style
# 036732.python.dyndlg.line19.comment Parameter 6 - Extra data


import win32con
import win32ui
from pywin.mfc import dialog


def MakeDlgTemplate():
    style = (
        win32con.DS_MODALFRAME
        | win32con.WS_POPUP
        | win32con.WS_VISIBLE
        | win32con.WS_CAPTION
        | win32con.WS_SYSMENU
        | win32con.DS_SETFONT
    )
    cs = win32con.WS_CHILD | win32con.WS_VISIBLE
    dlg = [
        ["Select Warehouse", (0, 0, 177, 93), style, None, (8, "MS Sans Serif")],
    ]
    dlg.append([130, "Current Warehouse:", -1, (7, 7, 69, 9), cs | win32con.SS_LEFT])
    dlg.append([130, "ASTORIA", 128, (16, 17, 99, 7), cs | win32con.SS_LEFT])
    dlg.append([130, "New &Warehouse:", -1, (7, 29, 69, 9), cs | win32con.SS_LEFT])
    s = win32con.WS_TABSTOP | cs
    # 036733.python.dyndlg.line44.comment dlg.append([131, None, 130, (5, 40, 110, 48),
    # 036734.python.dyndlg.line45.comment s | win32con.LBS_NOTIFY | win32con.LBS_SORT | win32con.LBS_NOINTEGRALHEIGHT | win32con.WS_VSCROLL | win32con.WS_BORDER])
    dlg.append(
        [
            "{8E27C92B-1264-101C-8A2F-040224009C02}",
            None,
            131,
            (5, 40, 110, 48),
            win32con.WS_TABSTOP,
        ]
    )

    dlg.append(
        [128, "OK", win32con.IDOK, (124, 5, 50, 14), s | win32con.BS_DEFPUSHBUTTON]
    )
    s = win32con.BS_PUSHBUTTON | s
    dlg.append([128, "Cancel", win32con.IDCANCEL, (124, 22, 50, 14), s])
    dlg.append([128, "&Help", 100, (124, 74, 50, 14), s])

    return dlg


def test1():
    win32ui.CreateDialogIndirect(MakeDlgTemplate()).DoModal()


def test2():
    dialog.Dialog(MakeDlgTemplate()).DoModal()


def test3():
    dlg = win32ui.LoadDialogResource(win32ui.IDD_SET_TABSTOPS)
    dlg[0][0] = "New Dialog Title"
    dlg[0][1] = (80, 20, 161, 60)
    dlg[1][1] = "&Confusion:"
    cs = (
        win32con.WS_CHILD
        | win32con.WS_VISIBLE
        | win32con.WS_TABSTOP
        | win32con.BS_PUSHBUTTON
    )
    dlg.append([128, "&Help", 100, (111, 41, 40, 14), cs])
    dialog.Dialog(dlg).DoModal()


def test4():
    page1 = dialog.PropertyPage(win32ui.LoadDialogResource(win32ui.IDD_PROPDEMO1))
    page2 = dialog.PropertyPage(win32ui.LoadDialogResource(win32ui.IDD_PROPDEMO2))
    ps = dialog.PropertySheet("Property Sheet/Page Demo", None, [page1, page2])
    ps.DoModal()


def testall():
    test1()
    test2()
    test3()
    test4()


if __name__ == "__main__":
    testall()
