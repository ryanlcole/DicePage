from __future__ import annotations

from ctypes import c_bool, c_void_p
from typing import TYPE_CHECKING

from pyglet.libs.darwin.cocoapy import (
    NSRectEncoding,
    NSUInteger,
    NSUIntegerEncoding,
    ObjCClass,
    ObjCSubclass,
    send_super,
)

if TYPE_CHECKING:
    from pyglet.libs.darwin import ObjCInstance


class PygletWindow_Implementation:
    PygletWindow = ObjCSubclass('NSWindow', 'PygletWindow')

    @PygletWindow.method('B')
    def canBecomeKeyWindow(self) -> bool:
        return True

    # 036244.python.pyglet_window.line26.comment When the window is being resized, it enters into a mini event loop that
    # 036245.python.pyglet_window.line27.comment only looks at mouseDragged and mouseUp events, blocking everything else.
    # 036246.python.pyglet_window.line28.comment Among other things, this makes it impossible to run an NSTimer to call the
    # 036247.python.pyglet_window.line29.comment idle() function in order to update the view during the resize.  So we
    # 036248.python.pyglet_window.line30.comment override this method, called by the resizing event loop, and call the
    # 036249.python.pyglet_window.line31.comment idle() function from here.  This *almost* works.  I can't figure out what
    # 036250.python.pyglet_window.line32.comment is happening at the very beginning of a resize event.  The NSView's
    # 036251.python.pyglet_window.line33.comment viewWillStartLiveResize method is called and then nothing happens until
    # 036252.python.pyglet_window.line34.comment the mouse is dragged.  I think NSApplication's nextEventMatchingMask_etc
    # 036253.python.pyglet_window.line35.comment method is being called instead of this one.  I don't really feel like
    # 036254.python.pyglet_window.line36.comment subclassing NSApplication just to fix this.  Also, to prevent white flashes
    # 036255.python.pyglet_window.line37.comment while resizing, we must also call idle() from the view's reshape method.
    @PygletWindow.method(b'@' + NSUIntegerEncoding + b'@@B')
    def nextEventMatchingMask_untilDate_inMode_dequeue_(self, mask: ObjCInstance, date: ObjCInstance,
                                                        mode: ObjCInstance, dequeue: bool) -> int:
        if self.inLiveResize():
            # 036256.python.pyglet_window.line42.comment Call the idle() method while we're stuck in a live resize event.
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()

        event = send_super(self, 'nextEventMatchingMask:untilDate:inMode:dequeue:',
                           mask, date, mode, dequeue,
                           superclass_name='NSWindow',
                           argtypes=[NSUInteger, c_void_p, c_void_p, c_bool])

        if event.value is None:
            return 0

        return event.value

    # 036257.python.pyglet_window.line57.comment Need this for set_size to not flash.
    @PygletWindow.method(b'd' + NSRectEncoding)
    def animationResizeTime_(self, newFrame: ObjCInstance) -> float:
        return 0.0


class PygletToolWindow_Implementation:
    PygletToolWindow = ObjCSubclass('NSPanel', 'PygletToolWindow')

    @PygletToolWindow.method(b'@' + NSUIntegerEncoding + b'@@B')
    def nextEventMatchingMask_untilDate_inMode_dequeue_(self, mask: ObjCInstance, date: ObjCInstance,
                                                        mode: ObjCInstance, dequeue: bool) -> int:
        if self.inLiveResize():
            # 036258.python.pyglet_window.line70.comment Call the idle() method while we're stuck in a live resize event.
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()

        event = send_super(self, 'nextEventMatchingMask:untilDate:inMode:dequeue:',
                           mask, date, mode, dequeue, argtypes=[NSUInteger, c_void_p, c_void_p, c_bool])

        if event.value is None:
            return 0

        return event.value

    # 036259.python.pyglet_window.line83.comment Need this for set_size to not flash.
    @PygletToolWindow.method(b'd' + NSRectEncoding)
    def animationResizeTime_(self, newFrame: ObjCInstance) -> float:
        return 0.0


PygletWindow = ObjCClass('PygletWindow')
PygletToolWindow = ObjCClass('PygletToolWindow')
