# 036735.python.fontdemo.line1.comment Demo of Generic document windows, DC, and Font usage
# 036736.python.fontdemo.line2.comment by Dave Brennan (brennan@hal.com)

# 036737.python.fontdemo.line4.comment usage examples:

# 036738.python.fontdemo.line6.comment >>> from fontdemo import *
# 036739.python.fontdemo.line7.comment >>> d = FontDemo('Hello, Python')
# 036740.python.fontdemo.line8.comment >>> f1 = { 'name':'Arial', 'height':36, 'weight':win32con.FW_BOLD}
# 036741.python.fontdemo.line9.comment >>> d.SetFont(f1)
# 036742.python.fontdemo.line10.comment >>> f2 = {'name':'Courier New', 'height':24, 'italic':1}
# 036743.python.fontdemo.line11.comment >>> d.SetFont (f2)

import win32api
import win32con
import win32ui
from pywin.mfc import docview

# 036744.python.fontdemo.line18.comment font is a dictionary in which the following elements matter:
# 036745.python.fontdemo.line19.comment (the best matching font to supplied parameters is returned)
# 036746.python.fontdemo.line20.comment name		string name of the font as known by Windows
# 036747.python.fontdemo.line21.comment size		point size of font in logical units
# 036748.python.fontdemo.line22.comment weight		weight of font (win32con.FW_NORMAL, win32con.FW_BOLD)
# 036749.python.fontdemo.line23.comment italic		boolean; true if set to anything but None
# 036750.python.fontdemo.line24.comment underline	boolean; true if set to anything but None


class FontView(docview.ScrollView):
    def __init__(
        self, doc, text="Python Rules!", font_spec={"name": "Arial", "height": 42}
    ):
        docview.ScrollView.__init__(self, doc)
        self.font = win32ui.CreateFont(font_spec)
        self.text = text
        self.width = self.height = 0
        # 036751.python.fontdemo.line35.comment set up message handlers
        self.HookMessage(self.OnSize, win32con.WM_SIZE)

    def OnAttachedObjectDeath(self):
        docview.ScrollView.OnAttachedObjectDeath(self)
        del self.font

    def SetFont(self, new_font):
        # 036752.python.fontdemo.line43.comment Change font on the fly
        self.font = win32ui.CreateFont(new_font)
        # 036753.python.fontdemo.line45.comment redraw the entire client window
        self.InvalidateRect(None)

    def OnSize(self, params):
        lParam = params[3]
        self.width = win32api.LOWORD(lParam)
        self.height = win32api.HIWORD(lParam)

    def OnPrepareDC(self, dc, printinfo):
        # 036754.python.fontdemo.line54.comment Set up the DC for forthcoming OnDraw call
        self.SetScrollSizes(win32con.MM_TEXT, (100, 100))
        dc.SetTextColor(win32api.RGB(0, 0, 255))
        dc.SetBkColor(win32api.GetSysColor(win32con.COLOR_WINDOW))
        dc.SelectObject(self.font)
        dc.SetTextAlign(win32con.TA_CENTER | win32con.TA_BASELINE)

    def OnDraw(self, dc):
        if self.width == 0 and self.height == 0:
            left, top, right, bottom = self.GetClientRect()
            self.width = right - left
            self.height = bottom - top
        x, y = self.width // 2, self.height // 2
        dc.TextOut(x, y, self.text)


def FontDemo():
    # 036755.python.fontdemo.line71.comment create doc/view
    template = docview.DocTemplate(win32ui.IDR_PYTHONTYPE, None, None, FontView)
    doc = template.OpenDocumentFile(None)
    doc.SetTitle("Font Demo")
    # 036756.python.fontdemo.line75.comment print("template is ", template, "obj is", template._obj_)
    template.close()
    # 036757.python.fontdemo.line77.comment print("closed")
    # 036758.python.fontdemo.line78.comment del template


if __name__ == "__main__":
    import demoutils

    if demoutils.NeedGoodGUI():
        FontDemo()
