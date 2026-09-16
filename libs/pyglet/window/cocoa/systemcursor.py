from __future__ import annotations

from pyglet.libs.darwin import cocoapy


# 036260.python.systemcursor.line6.comment This class is a wrapper around NSCursor which prevents us from
# 036261.python.systemcursor.line7.comment sending too many hide or unhide messages in a row.  Apparently
# 036262.python.systemcursor.line8.comment NSCursor treats them like retain/release messages, which can be
# 036263.python.systemcursor.line9.comment problematic when we are e.g. switching between window & fullscreen.
class SystemCursor:
    cursor_is_hidden = False

    @classmethod
    def hide(cls) -> None:  # noqa: ANN102
        if not cls.cursor_is_hidden:
            cocoapy.send_message('NSCursor', 'hide')
            cls.cursor_is_hidden = True

    @classmethod
    def unhide(cls) -> None:  # noqa: ANN102
        if cls.cursor_is_hidden:
            cocoapy.send_message('NSCursor', 'unhide')
            cls.cursor_is_hidden = False
