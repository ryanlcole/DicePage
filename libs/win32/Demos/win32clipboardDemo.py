# 046376.python.win32clipboardDemo.line1.comment win32clipboardDemo.py
# 046377.python.win32clipboardDemo.line2.comment
# 046378.python.win32clipboardDemo.line3.comment Demo/test of the win32clipboard module.
import win32con
from win32clipboard import (
    CloseClipboard,
    EmptyClipboard,
    EnumClipboardFormats,
    GetClipboardData,
    GetClipboardFormatName,
    IsClipboardFormatAvailable,
    OpenClipboard,
    RegisterClipboardFormat,
    SetClipboardData,
    SetClipboardText,
)

if not __debug__:
    print("WARNING: The test code in this module uses assert")
    print("This instance of Python has asserts disabled, so many tests will be skipped")

# 046379.python.win32clipboardDemo.line22.comment Build map of CF_* constants to names.
cf_names = {
    val: name
    for name, val in win32con.__dict__.items()
    if name[:3] == "CF_" and name != "CF_SCREENFONTS"  # CF_SCREEN_FONTS==CF_TEXT!?!?
}


def TestEmptyClipboard():
    OpenClipboard()
    try:
        EmptyClipboard()
        assert EnumClipboardFormats(0) == 0, (
            "Clipboard formats were available after emptying it!"
        )
    finally:
        CloseClipboard()


def TestText():
    OpenClipboard()
    try:
        text = "Hello from Python"
        text_bytes = text.encode("latin1")
        SetClipboardText(text)
        got = GetClipboardData(win32con.CF_TEXT)
        # 046381.python.win32clipboardDemo.line48.comment CF_TEXT always gives us 'bytes' back .
        assert got == text_bytes, f"Didn't get the correct result back - '{got!r}'."
    finally:
        CloseClipboard()

    OpenClipboard()
    try:
        # 046382.python.win32clipboardDemo.line55.comment CF_UNICODE text always gives unicode objects back.
        got = GetClipboardData(win32con.CF_UNICODETEXT)
        assert got == text, f"Didn't get the correct result back - '{got!r}'."
        assert isinstance(got, str), f"Didn't get the correct result back - '{got!r}'."

        # 046383.python.win32clipboardDemo.line60.comment CF_OEMTEXT is a bytes-based format.
        got = GetClipboardData(win32con.CF_OEMTEXT)
        assert got == text_bytes, f"Didn't get the correct result back - '{got!r}'."

        # 046384.python.win32clipboardDemo.line64.comment Unicode tests
        EmptyClipboard()
        text = "Hello from Python unicode"
        text_bytes = text.encode("latin1")
        # 046385.python.win32clipboardDemo.line68.comment Now set the Unicode value
        SetClipboardData(win32con.CF_UNICODETEXT, text)
        # 046386.python.win32clipboardDemo.line70.comment Get it in Unicode.
        got = GetClipboardData(win32con.CF_UNICODETEXT)
        assert got == text, f"Didn't get the correct result back - '{got!r}'."
        assert isinstance(got, str), f"Didn't get the correct result back - '{got!r}'."

        # 046387.python.win32clipboardDemo.line75.comment Close and open the clipboard to ensure auto-conversions take place.
    finally:
        CloseClipboard()

    OpenClipboard()
    try:
        # 046388.python.win32clipboardDemo.line81.comment Make sure I can still get the text as bytes
        got = GetClipboardData(win32con.CF_TEXT)
        assert got == text_bytes, f"Didn't get the correct result back - '{got!r}'."
        # 046389.python.win32clipboardDemo.line84.comment Make sure we get back the correct types.
        got = GetClipboardData(win32con.CF_UNICODETEXT)
        assert isinstance(got, str), f"Didn't get the correct result back - '{got!r}'."
        got = GetClipboardData(win32con.CF_OEMTEXT)
        assert got == text_bytes, f"Didn't get the correct result back - '{got!r}'."
        print("Clipboard text tests worked correctly")
    finally:
        CloseClipboard()


def TestClipboardEnum():
    OpenClipboard()
    try:
        # 046390.python.win32clipboardDemo.line97.comment Enumerate over the clipboard types
        enum = 0
        while 1:
            enum = EnumClipboardFormats(enum)
            if enum == 0:
                break
            assert IsClipboardFormatAvailable(enum), (
                "Have format, but clipboard says it is not available!"
            )
            n = cf_names.get(enum, "")
            if not n:
                try:
                    n = GetClipboardFormatName(enum)
                except error:
                    n = f"unknown ({enum})"

            print("Have format", n)
        print("Clipboard enumerator tests worked correctly")
    finally:
        CloseClipboard()


class Foo:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __lt__(self, other):
        return self.__dict__ < other.__dict__

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def TestCustomFormat():
    OpenClipboard()
    try:
        # 046391.python.win32clipboardDemo.line133.comment Just for the fun of it pickle Python objects through the clipboard
        fmt = RegisterClipboardFormat("Python Pickle Format")
        import pickle

        pickled_object = Foo(a=1, b=2, Hi=3)
        SetClipboardData(fmt, pickle.dumps(pickled_object))
        # 046392.python.win32clipboardDemo.line139.comment Now read it back.
        data = GetClipboardData(fmt)
        loaded_object = pickle.loads(data)
        assert pickle.loads(data) == pickled_object, "Didn't get the correct data!"

        print("Clipboard custom format tests worked correctly")
    finally:
        CloseClipboard()


if __name__ == "__main__":
    TestEmptyClipboard()
    TestText()
    TestCustomFormat()
    TestClipboardEnum()
    # 046393.python.win32clipboardDemo.line154.comment And leave it empty at the end!
    TestEmptyClipboard()
