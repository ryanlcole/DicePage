from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING

import pyglet
from pyglet.libs.darwin import (
    NSAlphaShiftKeyMask,
    NSFunctionKeyMask,
    NSLeftAlternateKeyMask,
    NSLeftCommandKeyMask,
    NSLeftControlKeyMask,
    NSLeftShiftKeyMask,
    NSPasteboardURLReadingFileURLsOnlyKey,
    NSRightAlternateKeyMask,
    NSRightCommandKeyMask,
    NSRightControlKeyMask,
    NSRightShiftKeyMask,
    cocoapy, NSMakeRect,
)
from pyglet.libs.darwin.quartzkey import charmap, keymap
from pyglet.window import key, mouse

from .pyglet_textview import PygletTextView

if TYPE_CHECKING:
    from . import CocoaWindow

NSTrackingArea = cocoapy.ObjCClass('NSTrackingArea')
NSURL = cocoapy.ObjCClass('NSURL')
NSArray = cocoapy.ObjCClass('NSArray')
NSDictionary = cocoapy.ObjCClass('NSDictionary')
NSNumber = cocoapy.ObjCClass('NSNumber')
NSNotificationCenter = cocoapy.ObjCClass('NSNotificationCenter')

# 036187.python.pyglet_view.line36.comment Key to mask mapping.
maskForKey: dict[int, int] = {
    key.LSHIFT: NSLeftShiftKeyMask,
    key.RSHIFT: NSRightShiftKeyMask,
    key.LCTRL: NSLeftControlKeyMask,
    key.RCTRL: NSRightControlKeyMask,
    key.LOPTION: NSLeftAlternateKeyMask,
    key.ROPTION: NSRightAlternateKeyMask,
    key.LCOMMAND: NSLeftCommandKeyMask,
    key.RCOMMAND: NSRightCommandKeyMask,
    key.CAPSLOCK: NSAlphaShiftKeyMask,
    key.FUNCTION: NSFunctionKeyMask,
}


# 036188.python.pyglet_view.line51.comment Event data helper functions.


_mouseViewRect = NSMakeRect(0, 0, 0, 0)

def getMouseDelta(nsevent: cocoapy.ObjCInstance) -> tuple[int, int]:
    dx = nsevent.deltaX()
    dy = -nsevent.deltaY()
    return dx, dy


def getMousePosition(self: PygletView_Implementation | cocoapy.ObjCInstance, nsevent: cocoapy.ObjCInstance) \
        -> tuple[int, int]:
    in_window = nsevent.locationInWindow()
    in_window = self.convertPoint_fromView_(in_window, None)
    if pyglet.options.dpi_scaling != "stretch":
        _mouseViewRect.origin.x = in_window.x
        _mouseViewRect.origin.y = in_window.y
        converted = self.convertRectToBacking_(_mouseViewRect)
        in_window = converted.origin
    x = int(in_window.x)
    y = int(in_window.y)
    # 036189.python.pyglet_view.line73.comment Must record mouse position for BaseWindow.draw_mouse_cursor to work.
    self._window._mouse_x = x
    self._window._mouse_y = y
    return x, y


def getModifiers(nsevent: cocoapy.ObjCInstance) -> int:
    modifiers = 0
    modifierFlags = nsevent.modifierFlags()
    if modifierFlags & cocoapy.NSAlphaShiftKeyMask:
        modifiers |= key.MOD_CAPSLOCK
    if modifierFlags & cocoapy.NSShiftKeyMask:
        modifiers |= key.MOD_SHIFT
    if modifierFlags & cocoapy.NSControlKeyMask:
        modifiers |= key.MOD_CTRL
    if modifierFlags & cocoapy.NSAlternateKeyMask:
        modifiers |= key.MOD_ALT
        modifiers |= key.MOD_OPTION
    if modifierFlags & cocoapy.NSCommandKeyMask:
        modifiers |= key.MOD_COMMAND
    if modifierFlags & cocoapy.NSFunctionKeyMask:
        modifiers |= key.MOD_FUNCTION
    return modifiers


def getSymbol(nsevent: cocoapy.ObjCInstance) -> str | None:
    symbol = keymap.get(nsevent.keyCode(), None)
    if symbol is not None:
        return symbol

    chars = cocoapy.cfstring_to_string(nsevent.charactersIgnoringModifiers())
    if chars:
        return charmap.get(chars[0].upper(), None)

    return None


class PygletView_Implementation:
    PygletView = cocoapy.ObjCSubclass('NSView', 'PygletView')

    @PygletView.method(b'@' + cocoapy.NSRectEncoding + cocoapy.PyObjectEncoding)
    def initWithFrame_cocoaWindow_(self, frame: cocoapy.NSRect, window: CocoaWindow) -> cocoapy.ObjCInstance | None:

        # 036190.python.pyglet_view.line116.comment The tracking area is used to get mouseEntered, mouseExited, and cursorUpdate
        # 036191.python.pyglet_view.line117.comment events so that we can custom set the mouse cursor within the view.
        # 036192.python.pyglet_view.line118.comment self._tracking_area = None

        self = cocoapy.ObjCInstance(cocoapy.send_super(self, 'initWithFrame:', frame, argtypes=[cocoapy.NSRect]))

        if not self:
            return None

        # 036193.python.pyglet_view.line125.comment CocoaWindow object.
        self._window = window

        self.associate("_tracking_area", None)

        self.updateTrackingAreas()

        # 036194.python.pyglet_view.line132.comment Create an instance of PygletTextView to handle text events.
        # 036195.python.pyglet_view.line133.comment We must do this because NSOpenGLView doesn't conform to the
        # 036196.python.pyglet_view.line134.comment NSTextInputClient protocol by default, and the insertText: method will
        # 036197.python.pyglet_view.line135.comment not do the right thing with respect to translating key sequences like
        # 036198.python.pyglet_view.line136.comment "Option-e", "e" if the protocol isn't implemented.  So the easiest
        # 036199.python.pyglet_view.line137.comment thing to do is to subclass NSTextView which *does* implement the
        # 036200.python.pyglet_view.line138.comment protocol and let it handle text input.
        textview = PygletTextView.alloc().initWithCocoaWindow_(window)
        self.associate("_textview", textview)
        # 036201.python.pyglet_view.line141.comment Add text view to the responder chain.
        self.addSubview_(self._textview)
        return self

    @PygletView.method('v')
    def dealloc(self) -> None:
        self._window = None
        self._textview.removeFromSuperviewWithoutNeedingDisplay()
        self._textview.release()
        self._tracking_area.release()
        cocoapy.send_super(self, 'dealloc')

    @PygletView.method('v')
    def updateTrackingAreas(self) -> None:
        # 036202.python.pyglet_view.line155.comment This method is called automatically whenever the tracking areas need to be
        # 036203.python.pyglet_view.line156.comment recreated, for example when window resizes.
        if self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
            self._tracking_area.release()
            self.associate("_tracking_area", None)

        tracking_options = (cocoapy.NSTrackingMouseEnteredAndExited | cocoapy.NSTrackingActiveInActiveApp |
                            cocoapy.NSTrackingCursorUpdate | cocoapy.NSTrackingInVisibleRect)
        frame = self.frame()
        tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            frame,  # rect
            tracking_options,  # options
            self,  # owner
            None)  # userInfo

        self.associate("_tracking_area", tracking_area)

        self.addTrackingArea_(self._tracking_area)
        cocoapy.send_super(self, 'updateTrackingAreas')

    @PygletView.method('B')
    def canBecomeKeyView(self) -> bool:
        return True

    @PygletView.method('B')
    def isOpaque(self) -> bool:
        return True

    # 036208.python.pyglet_view.line184.comment # Event responders.

    # 036209.python.pyglet_view.line186.comment This method is called whenever the view changes size.
    @PygletView.method(b'v' + cocoapy.NSSizeEncoding)
    def setFrameSize_(self, size: cocoapy.NSSize) -> None:
        cocoapy.send_super(self, 'setFrameSize:', size,
                           superclass_name='NSView',
                           argtypes=[cocoapy.NSSize])

        # 036210.python.pyglet_view.line193.comment This method is called when view is first installed as the
        # 036211.python.pyglet_view.line194.comment contentView of window.  Don't do anything on first call.
        # 036212.python.pyglet_view.line195.comment This also helps ensure correct window creation event ordering.
        if not self._window.context.canvas or self._window._shadow:
            return

        width, height = int(size.width), int(size.height)
        self._window.switch_to()
        self._window.context.update_geometry()
        self._window._width, self._window._height = width, height  # noqa: SLF001
        self._window.dispatch_event('_on_internal_resize', width, height)
        self._window.dispatch_event('on_expose')
        # 036214.python.pyglet_view.line205.comment Can't get app.event_loop.enter_blocking() working with Cocoa, because
        # 036215.python.pyglet_view.line206.comment when mouse clicks on the window's resize control, Cocoa enters into a
        # 036216.python.pyglet_view.line207.comment mini-event loop that only responds to mouseDragged and mouseUp events.
        # 036217.python.pyglet_view.line208.comment This means that using NSTimer to call idle() won't work.  Our kludge
        # 036218.python.pyglet_view.line209.comment is to override NSWindow's nextEventMatchingMask_etc method and call
        # 036219.python.pyglet_view.line210.comment idle() from there.
        if self.inLiveResize():
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()

    @PygletView.method('v@')
    def keyDown_(self, nsevent: cocoapy.ObjCInstance) -> None:
        if not nsevent.isARepeat():
            symbol = getSymbol(nsevent)
            modifiers = getModifiers(nsevent)
            self._window.dispatch_event('on_key_press', symbol, modifiers)

    @PygletView.method('v@')
    def keyUp_(self, nsevent: cocoapy.ObjCInstance) -> None:
        symbol = getSymbol(nsevent)
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_key_release', symbol, modifiers)

    @PygletView.method('v@')
    def flagsChanged_(self, nsevent: cocoapy.ObjCInstance) -> None:
        # 036220.python.pyglet_view.line231.comment Handles on_key_press and on_key_release events for modifier keys.
        # 036221.python.pyglet_view.line232.comment Note that capslock is handled differently than other keys; it acts
        # 036222.python.pyglet_view.line233.comment as a toggle, so on_key_release is only sent when it's turned off.
        symbol = keymap.get(nsevent.keyCode(), None)

        # 036223.python.pyglet_view.line236.comment Ignore this event if symbol is not a modifier key.  We must check this
        # 036224.python.pyglet_view.line237.comment because e.g., we receive a flagsChanged message when using CMD-tab to
        # 036225.python.pyglet_view.line238.comment switch applications, with symbol == "a" when command key is released.
        if symbol is None or symbol not in maskForKey:
            return

        modifiers = getModifiers(nsevent)
        modifierFlags = nsevent.modifierFlags()

        if symbol and modifierFlags & maskForKey[symbol]:
            self._window.dispatch_event('on_key_press', symbol, modifiers)
        else:
            self._window.dispatch_event('on_key_release', symbol, modifiers)

    @PygletView.method('v:')
    def doCommandBySelector_(self, selector: ctypes.c_void_p) -> None:
        """Prevent system beeps when an event or key is not handled."""

    @PygletView.method('v@')
    def mouseMoved_(self, nsevent: cocoapy.ObjCInstance) -> None:
        if self._window._mouse_ignore_motion:  # noqa: SLF001
            self._window._mouse_ignore_motion = False  # noqa: SLF001
            return
        # 036228.python.pyglet_view.line259.comment Don't send on_mouse_motion events if we're not inside the content rectangle.
        if not self._window._mouse_in_window:  # noqa: SLF001
            return
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        factor = self._window._nswindow.backingScaleFactor()
        self._window.dispatch_event('on_mouse_motion', x, y, dx * factor, dy * factor)

    @PygletView.method('v@')
    def scrollWheel_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        scroll_x, scroll_y = getMouseDelta(nsevent)
        self._window.dispatch_event('on_mouse_scroll', x, y, scroll_x, scroll_y)

    @PygletView.method('v@')
    def mouseDown_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.LEFT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)

    @PygletView.method('v@')
    def mouseDragged_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        buttons = mouse.LEFT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @PygletView.method('v@')
    def mouseUp_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.LEFT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    @PygletView.method('v@')
    def rightMouseDown_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.RIGHT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)

    @PygletView.method('v@')
    def rightMouseDragged_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        buttons = mouse.RIGHT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @PygletView.method('v@')
    def rightMouseUp_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.RIGHT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    @PygletView.method('v@')
    def otherMouseDown_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.MIDDLE
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)

    @PygletView.method('v@')
    def otherMouseDragged_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        buttons = mouse.MIDDLE
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @PygletView.method('v@')
    def otherMouseUp_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.MIDDLE
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    @PygletView.method('v@')
    def mouseEntered_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        self._window._mouse_in_window = True  # noqa: SLF001
        # 036231.python.pyglet_view.line343.comment Don't call self._window.set_mouse_platform_visible() from here.
        # 036232.python.pyglet_view.line344.comment Better to do it from cursorUpdate:
        self._window.dispatch_event('on_mouse_enter', x, y)

    @PygletView.method('v@')
    def mouseExited_(self, nsevent: cocoapy.ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        self._window._mouse_in_window = False  # noqa: SLF001
        if not self._window._mouse_exclusive:  # noqa: SLF001
            self._window.set_mouse_platform_visible()
        self._window.dispatch_event('on_mouse_leave', x, y)

    @PygletView.method('v@')
    def cursorUpdate_(self, nsevent: cocoapy.ObjCInstance) -> None:
        # 036235.python.pyglet_view.line357.comment Called when mouse cursor enters view.  Unlike mouseEntered:,
        # 036236.python.pyglet_view.line358.comment this method will be called if the view appears underneath a
        # 036237.python.pyglet_view.line359.comment motionless mouse cursor, as can happen during window creation,
        # 036238.python.pyglet_view.line360.comment or when switching into fullscreen mode.
        # 036239.python.pyglet_view.line361.comment BUG: If the mouse enters the window via the resize control at the
        # 036240.python.pyglet_view.line362.comment the bottom right corner, the resize control will set the cursor
        # 036241.python.pyglet_view.line363.comment to the default arrow and screw up our cursor tracking.
        self._window._mouse_in_window = True  # noqa: SLF001
        if not self._window._mouse_exclusive:  # noqa: SLF001
            self._window.set_mouse_platform_visible()

    @PygletView.method('Q@')
    def draggingEntered_(self, draginfo: cocoapy.ObjCInstance) -> int:
        return cocoapy.NSDragOperationGeneric

    @PygletView.method('B@')
    def performDragOperation_(self, sender: cocoapy.ObjCInstance) -> None:
        pos = sender.draggingLocation()

        pasteboard = sender.draggingPasteboard()

        classes = NSArray.arrayWithObject_(NSURL)

        options = NSDictionary.dictionaryWithObject_forKey_(
            NSNumber.numberWithBool_(True), NSPasteboardURLReadingFileURLsOnlyKey,
        )

        urls = pasteboard.readObjectsForClasses_options_(classes, options)

        url_count = urls.count()
        paths = []
        for i in range(url_count):
            fpath = urls.objectAtIndex_(i).fileSystemRepresentation()
            paths.append(fpath.decode())

        self._window.dispatch_event('on_file_drop', pos.x, pos.y, paths)


PygletView = cocoapy.ObjCClass('PygletView')
