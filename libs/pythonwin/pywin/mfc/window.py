# 038519.python.window.line1.comment The MFCish window classes.
import win32con
import win32ui

from . import object


class Wnd(object.CmdTarget):
    def __init__(self, initobj=None):
        object.CmdTarget.__init__(self, initobj)
        if self._obj_:
            self._obj_.HookMessage(self.OnDestroy, win32con.WM_DESTROY)

    def OnDestroy(self, msg):
        pass


# 038520.python.window.line18.comment NOTE NOTE - This facility is currently disabled in Pythonwin!!!!!
# 038521.python.window.line19.comment Note - to process all messages for your window, add the following method
# 038522.python.window.line20.comment to a derived class.  This code provides default message handling (ie, is
# 038523.python.window.line21.comment identical, except presumably in speed, as if the method did not exist at
# 038524.python.window.line22.comment all, so presumably will be modified to test for specific messages to be
# 038525.python.window.line23.comment useful!
# 038526.python.window.line24.comment def WindowProc(self, msg, wParam, lParam):
# 038527.python.window.line25.comment rc, lResult = self._obj_.OnWndMsg(msg, wParam, lParam)
# 038528.python.window.line26.comment if not rc: lResult = self._obj_.DefWindowProc(msg, wParam, lParam)
# 038529.python.window.line27.comment return lResult


class FrameWnd(Wnd):
    def __init__(self, wnd):
        Wnd.__init__(self, wnd)


class MDIChildWnd(FrameWnd):
    def __init__(self, wnd=None):
        if wnd is None:
            wnd = win32ui.CreateMDIChild()
        FrameWnd.__init__(self, wnd)

    def OnCreateClient(self, cp, context):
        if context is not None and context.template is not None:
            context.template.CreateView(self, context)


class MDIFrameWnd(FrameWnd):
    def __init__(self, wnd=None):
        if wnd is None:
            wnd = win32ui.CreateMDIFrame()
        FrameWnd.__init__(self, wnd)
