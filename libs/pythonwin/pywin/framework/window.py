# 038093.python.window.line1.comment Framework Window classes.

# 038094.python.window.line3.comment Most Pythonwin windows should use these classes rather than
# 038095.python.window.line4.comment the raw MFC ones if they want Pythonwin specific functionality.
import pywin.mfc.window
import win32con


class MDIChildWnd(pywin.mfc.window.MDIChildWnd):
    def AutoRestore(self):
        "If the window is minimised or maximised, restore it."
        p = self.GetWindowPlacement()
        if p[1] == win32con.SW_MINIMIZE or p[1] == win32con.SW_SHOWMINIMIZED:
            self.SetWindowPlacement(p[0], win32con.SW_RESTORE, p[2], p[3], p[4])
