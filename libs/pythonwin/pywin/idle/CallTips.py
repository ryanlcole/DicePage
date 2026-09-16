# 038276.python.CallTips.line1.comment CallTips.py - An IDLE extension that provides "Call Tips" - ie, a floating window that
# 038277.python.CallTips.line2.comment displays parameter information as you open parens.

import inspect
import string
import sys
import traceback


class CallTips:
    menudefs = []

    keydefs = {
        "<<paren-open>>": ["<Key-parenleft>"],
        "<<paren-close>>": ["<Key-parenright>"],
        "<<check-calltip-cancel>>": ["<KeyRelease>"],
        "<<calltip-cancel>>": ["<ButtonPress>", "<Key-Escape>"],
    }

    windows_keydefs = {}

    unix_keydefs = {}

    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.calltip = None
        if hasattr(self.text, "make_calltip_window"):
            self._make_calltip_window = self.text.make_calltip_window
        else:
            self._make_calltip_window = self._make_tk_calltip_window

    def close(self):
        self._make_calltip_window = None

    # 038278.python.CallTips.line36.comment Makes a Tk based calltip window.  Used by IDLE, but not Pythonwin.
    # 038279.python.CallTips.line37.comment See __init__ above for how this is used.
    def _make_tk_calltip_window(self):
        import CallTipWindow

        return CallTipWindow.CallTip(self.text)

    def _remove_calltip_window(self):
        if self.calltip:
            self.calltip.hidetip()
            self.calltip = None

    def paren_open_event(self, event):
        self._remove_calltip_window()
        arg_text = get_arg_text(self.get_object_at_cursor())
        if arg_text:
            self.calltip_start = self.text.index("insert")
            self.calltip = self._make_calltip_window()
            self.calltip.showtip(arg_text)
        return ""  # so the event is handled normally.

    def paren_close_event(self, event):
        # 038281.python.CallTips.line58.comment Now just hides, but later we should check if other
        # 038282.python.CallTips.line59.comment paren'd expressions remain open.
        self._remove_calltip_window()
        return ""  # so the event is handled normally.

    def check_calltip_cancel_event(self, event):
        if self.calltip:
            # 038284.python.CallTips.line65.comment If we have moved before the start of the calltip,
            # 038285.python.CallTips.line66.comment or off the calltip line, then cancel the tip.
            # 038286.python.CallTips.line67.comment (Later need to be smarter about multi-line, etc)
            if self.text.compare(
                "insert", "<=", self.calltip_start
            ) or self.text.compare("insert", ">", self.calltip_start + " lineend"):
                self._remove_calltip_window()
        return ""  # so the event is handled normally.

    def calltip_cancel_event(self, event):
        self._remove_calltip_window()
        return ""  # so the event is handled normally.

    def get_object_at_cursor(
        self,
        wordchars="._"
        + string.ascii_uppercase
        + string.ascii_lowercase
        + string.digits,
    ):
        # 038289.python.CallTips.line85.comment XXX - This needs to be moved to a better place
        # 038290.python.CallTips.line86.comment so the "." attribute lookup code can also use it.
        text = self.text
        chars = text.get("insert linestart", "insert")
        i = len(chars)
        while i and chars[i - 1] in wordchars:
            i -= 1
        word = chars[i:]
        if word:
            # 038291.python.CallTips.line94.comment How is this for a hack!
            import __main__

            namespace = sys.modules.copy()
            namespace.update(__main__.__dict__)
            try:
                return eval(word, namespace)
            except:
                pass
        return None  # Can't find an object.


def _find_constructor(class_ob):
    # 038293.python.CallTips.line107.comment Given a class object, return a function object used for the
    # 038294.python.CallTips.line108.comment constructor (ie, __init__() ) or None if we can't find one.
    try:
        return class_ob.__init__
    except AttributeError:
        for base in class_ob.__bases__:
            rc = _find_constructor(base)
            if rc is not None:
                return rc
    return None


def get_arg_text(ob):
    # 038295.python.CallTips.line120.comment Get a string describing the arguments for the given object.
    argText = ""
    if ob is not None:
        if inspect.isclass(ob):
            # 038296.python.CallTips.line124.comment Look for the highest __init__ in the class chain.
            fob = _find_constructor(ob)
            if fob is None:
                fob = lambda: None
        else:
            fob = ob
        if inspect.isfunction(fob) or inspect.ismethod(fob):
            try:
                argText = str(inspect.signature(fob))
            except:
                print("Failed to format the args")
                traceback.print_exc()
        # 038297.python.CallTips.line136.comment See if we can use the docstring
        if hasattr(ob, "__doc__"):
            doc = ob.__doc__
            try:
                doc = doc.strip()
                pos = doc.find("\n")
            except AttributeError:
                # 038298.python.CallTips.line143.comment # New style classes may have __doc__ slot without actually
                # 038299.python.CallTips.line144.comment # having a string assigned to it
                pass
            else:
                if pos < 0 or pos > 70:
                    pos = 70
                if argText:
                    argText += "\n"
                argText += doc[:pos]

    return argText


# 038300.python.CallTips.line156.comment ################################################
# 038301.python.CallTips.line157.comment
# 038302.python.CallTips.line158.comment Test code
# 038303.python.CallTips.line159.comment
if __name__ == "__main__":

    def t1():
        "()"

    def t2(a, b=None):
        "(a, b=None)"

    def t3(a, *args):
        "(a, *args)"

    def t4(*args):
        "(*args)"

    def t5(a, *args):
        "(a, *args)"

    def t6(a, b=None, *args, **kw):
        "(a, b=None, *args, **kw)"

    class TC:
        "(self, a=None, *b)"

        def __init__(self, a=None, *b):
            "(self, a=None, *b)"

        def t1(self):
            "(self)"

        def t2(self, a, b=None):
            "(self, a, b=None)"

        def t3(self, a, *args):
            "(self, a, *args)"

        def t4(self, *args):
            "(self, *args)"

        def t5(self, a, *args):
            "(self, a, *args)"

        def t6(self, a, b=None, *args, **kw):
            "(self, a, b=None, *args, **kw)"

    def test(tests):
        failed = []
        for t in tests:
            expected = t.__doc__ + "\n" + t.__doc__
            if get_arg_text(t) != expected:
                failed.append(t)
                print(f"{t} - expected {expected!r}, but got {get_arg_text(t)!r}")
        print("%d of %d tests failed" % (len(failed), len(tests)))

    tc = TC()
    tests = t1, t2, t3, t4, t5, t6, TC, tc.t1, tc.t2, tc.t3, tc.t4, tc.t5, tc.t6

    test(tests)
