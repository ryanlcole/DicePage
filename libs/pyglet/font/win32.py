# 027241.python.win32.line1.comment Windows Vista: need to call SetProcessDPIAware?  May affect GDI+ calls as well as font.
from __future__ import annotations

import ctypes
import math
import warnings
from typing import TYPE_CHECKING, ClassVar, Sequence

import pyglet
import pyglet.image
from pyglet.font import base
from pyglet.image.codecs.gdiplus import BitmapData, ImageLockModeRead, PixelFormat32bppARGB, Rect, gdiplus
from pyglet.libs.win32 import _gdi32 as gdi32
from pyglet.libs.win32 import _user32 as user32
from pyglet.libs.win32.constants import ANTIALIASED_QUALITY, FW_BOLD, FW_NORMAL
from pyglet.libs.win32.context_managers import device_context
from pyglet.libs.win32.types import ABC, BYTE, LOGFONTW, TEXTMETRIC

if TYPE_CHECKING:
    from pyglet.font.base import Glyph


DriverStringOptionsCmapLookup = 1
DriverStringOptionsRealizedAdvance = 4
TextRenderingHintSingleBitPerPixelGridFit = 1
TextRenderingHintAntiAlias = 4
TextRenderingHintAntiAliasGridFit = 3


FontStyleBold = 1
FontStyleItalic = 2
UnitPixel = 2
UnitPoint = 3

StringFormatFlagsDirectionRightToLeft = 0x00000001
StringFormatFlagsDirectionVertical = 0x00000002
StringFormatFlagsNoFitBlackBox = 0x00000004
StringFormatFlagsDisplayFormatControl = 0x00000020
StringFormatFlagsNoFontFallback = 0x00000400
StringFormatFlagsMeasureTrailingSpaces = 0x00000800
StringFormatFlagsNoWrap = 0x00001000
StringFormatFlagsLineLimit = 0x00002000
StringFormatFlagsNoClip = 0x00004000

FontFamilyNotFound = 14


_debug_font = pyglet.options["debug_font"]


class Rectf(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
    ]


_text_quality = {
    True: TextRenderingHintAntiAliasGridFit,
    False: TextRenderingHintSingleBitPerPixelGridFit,
}

class GDIPlusGlyphRenderer(base.GlyphRenderer):

    def __init__(self, font: GDIPlusFont) -> None:
        self._bitmap = None
        self._dc = None
        self._bitmap_rect = None
        super().__init__(font)
        self.font = font

        # 027242.python.win32.line74.comment Pessimistically round up width and height to 4 byte alignment
        width = font.max_glyph_width
        height = font.ascent - font.descent
        width = (width | 0x3) + 1
        height = (height | 0x3) + 1
        self._create_bitmap(width, height)

        gdi32.SelectObject(self._dc, self.font.hfont)

    def __del__(self) -> None:
        try:
            if self._matrix:
                gdiplus.GdipDeleteMatrix(self._matrix)
            if self._brush:
                gdiplus.GdipDeleteBrush(self._brush)
            if self._graphics:
                gdiplus.GdipDeleteGraphics(self._graphics)
            if self._bitmap:
                gdiplus.GdipDisposeImage(self._bitmap)
            if self._dc:
                user32.ReleaseDC(0, self._dc)
        except Exception:  # noqa: S110, BLE001
            pass

    def _create_bitmap(self, width: int, height: int) -> None:
        self._data = (BYTE * (4 * width * height))()
        self._bitmap = ctypes.c_void_p()
        self._format = PixelFormat32bppARGB
        gdiplus.GdipCreateBitmapFromScan0(width, height, width * 4,
            self._format, self._data, ctypes.byref(self._bitmap))

        self._graphics = ctypes.c_void_p()
        gdiplus.GdipGetImageGraphicsContext(self._bitmap,
            ctypes.byref(self._graphics))
        gdiplus.GdipSetPageUnit(self._graphics, UnitPixel)

        self._dc = user32.GetDC(0)
        gdi32.SelectObject(self._dc, self.font.hfont)

        gdiplus.GdipSetTextRenderingHint(self._graphics,
            _text_quality[pyglet.options.text_antialiasing])

        self._brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xffffffff, ctypes.byref(self._brush))

        self._matrix = ctypes.c_void_p()
        gdiplus.GdipCreateMatrix(ctypes.byref(self._matrix))

        self._flags = (DriverStringOptionsCmapLookup |
                       DriverStringOptionsRealizedAdvance)

        self._rect = Rect(0, 0, width, height)

        self._bitmap_height = height

    def render(self, text: str) -> Glyph:
        ch = ctypes.create_unicode_buffer(text)
        len_ch = len(text)

        # 027244.python.win32.line133.comment Layout rectangle; not clipped against so not terribly important.
        width = 10000
        height = self._bitmap_height
        rect = Rectf(0, self._bitmap_height
                        - self.font.ascent + self.font.descent,
                     width, height)

        # 027245.python.win32.line140.comment Set up GenericTypographic with 1 character measure range
        generic = ctypes.c_void_p()
        gdiplus.GdipStringFormatGetGenericTypographic(ctypes.byref(generic))
        fmt = ctypes.c_void_p()
        gdiplus.GdipCloneStringFormat(generic, ctypes.byref(fmt))
        gdiplus.GdipDeleteStringFormat(generic)

        # 027246.python.win32.line147.comment --- Measure advance

        # 027247.python.win32.line149.comment XXX HACK HACK HACK
        # 027248.python.win32.line150.comment Windows GDI+ is a filthy broken toy.  No way to measure the bounding
        # 027249.python.win32.line151.comment box of a string, or to obtain LSB.  What a joke.
        # 027250.python.win32.line152.comment
        # 027251.python.win32.line153.comment For historical note, GDI cannot be used because it cannot composite
        # 027252.python.win32.line154.comment into a bitmap with alpha.
        # 027253.python.win32.line155.comment
        # 027254.python.win32.line156.comment It looks like MS have abandoned GDI and GDI+ and are finally
        # 027255.python.win32.line157.comment supporting accurate text measurement with alpha composition in .NET
        # 027256.python.win32.line158.comment 2.0 (WinForms) via the TextRenderer class; this has no C interface
        # 027257.python.win32.line159.comment though, so we're entirely screwed.
        # 027258.python.win32.line160.comment
        # 027259.python.win32.line161.comment So anyway, we first try to get the width with GdipMeasureString.
        # 027260.python.win32.line162.comment Then if it's a TrueType font, we use GetCharABCWidthsW to get the
        # 027261.python.win32.line163.comment correct LSB. If it's a negative LSB, we move the layoutRect `rect`
        # 027262.python.win32.line164.comment to the right so that the whole glyph is rendered on the surface.
        # 027263.python.win32.line165.comment For positive LSB, we let the renderer render the correct white
        # 027264.python.win32.line166.comment space and we don't pass the LSB info to the Glyph.set_bearings

        bbox = Rectf()
        flags = (StringFormatFlagsMeasureTrailingSpaces |
                 StringFormatFlagsNoClip |
                 StringFormatFlagsNoFitBlackBox)
        gdiplus.GdipSetStringFormatFlags(fmt, flags)
        gdiplus.GdipMeasureString(self._graphics,
                                  ch,
                                  len_ch,
                                  self.font._gdipfont,
                                  ctypes.byref(rect),
                                  fmt,
                                  ctypes.byref(bbox),
                                  None,
                                  None)

        # 027265.python.win32.line183.comment We only care about the advance from this whole thing.
        advance = int(math.ceil(bbox.width))

        # 027266.python.win32.line186.comment GDI functions only work for a single character so we transform
        # 027267.python.win32.line187.comment grapheme \r\n into \r
        if text == "\r\n":
            text = "\r"

        # 027268.python.win32.line191.comment XXX END HACK HACK HACK

        abc = ABC()
        width = 0
        lsb = 0
        ttf_font = True
        # 027269.python.win32.line197.comment Use GDI to get code points for the text passed. This is almost always 1.
        # 027270.python.win32.line198.comment For special unicode characters it may be comprised of 2+ codepoints. Get the width/lsb of each.
        # 027271.python.win32.line199.comment Function only works on TTF fonts.
        for codepoint in [ord(c) for c in text]:
            if gdi32.GetCharABCWidthsW(self._dc, codepoint, codepoint, ctypes.byref(abc)):
                lsb += abc.abcA
                width += abc.abcB

                if lsb < 0:
                    # 027272.python.win32.line206.comment Negative LSB: we shift the layout rect to the right
                    # 027273.python.win32.line207.comment Otherwise we will cut the left part of the glyph
                    rect.x = -lsb
                    width -= lsb
                else:
                    width += lsb
            else:
                ttf_font = False
                break

        # 027274.python.win32.line216.comment Almost always a TTF font. Haven't seen a modern font that GetCharABCWidthsW fails on.
        # 027275.python.win32.line217.comment For safety, just use the advance as the width.
        if not ttf_font:
            width = advance

            # 027276.python.win32.line221.comment This hack bumps up the width if the font is italic;
            # 027277.python.win32.line222.comment this compensates for some common fonts.  It's also a stupid
            # 027278.python.win32.line223.comment waste of texture memory.
            if self.font.italic:
                width += width // 2
                # 027279.python.win32.line226.comment Do not enlarge more than the _rect width.
                width = min(width, self._rect.Width)

        # 027280.python.win32.line229.comment Draw character to bitmap
        gdiplus.GdipGraphicsClear(self._graphics, 0x00000000)
        gdiplus.GdipDrawString(self._graphics,
                               ch,
                               len_ch,
                               self.font._gdipfont,
                               ctypes.byref(rect),
                               fmt,
                               self._brush)

        gdiplus.GdipFlush(self._graphics, 1)
        gdiplus.GdipDeleteStringFormat(fmt)

        bitmap_data = BitmapData()
        gdiplus.GdipBitmapLockBits(
            self._bitmap,
            ctypes.byref(self._rect), ImageLockModeRead, self._format,
            ctypes.byref(bitmap_data))

        # 027281.python.win32.line248.comment Create buffer for RawImage
        buffer = ctypes.create_string_buffer(
            bitmap_data.Stride * bitmap_data.Height)
        ctypes.memmove(buffer, bitmap_data.Scan0, len(buffer))

        # 027282.python.win32.line253.comment Unlock data
        gdiplus.GdipBitmapUnlockBits(self._bitmap, ctypes.byref(bitmap_data))

        image = pyglet.image.ImageData(
            width, height,
            "BGRA", buffer, -bitmap_data.Stride)

        glyph = self.font.create_glyph(image)
        # 027283.python.win32.line261.comment Only pass negative LSB info
        lsb = min(lsb, 0)
        glyph.set_bearings(-self.font.descent, lsb, advance)
        return glyph


class Win32Font(base.Font):
    glyph_renderer_class = GDIPlusGlyphRenderer

    def __init__(
            self,
            name: str, size: float,
            weight: str = "normal", italic: bool = False, stretch: bool = False,
            dpi: int | None = None,
    ) -> None:
        super().__init__()

        bold = weight if weight in (None, True, False) else "bold" in weight

        self.logfont = self.get_logfont(name, size, bold, italic, dpi)
        self.hfont = gdi32.CreateFontIndirectW(ctypes.byref(self.logfont))

        # 027284.python.win32.line283.comment Create a dummy DC for coordinate mapping
        with device_context(None) as dc:
            metrics = TEXTMETRIC()
            gdi32.SelectObject(dc, self.hfont)
            gdi32.GetTextMetricsA(dc, ctypes.byref(metrics))
            self.ascent = metrics.tmAscent
            self.descent = -metrics.tmDescent
            self.max_glyph_width = metrics.tmMaxCharWidth

    @staticmethod
    def get_logfont(name: str, size: float, bold: bool, italic: bool, dpi: int | None = None) -> LOGFONTW:
        """Get a raw Win32 :py:class:`.LOGFONTW` struct for the given arguments.

        Args:
            name: The name of the font
            size: The font size in points
            bold: Whether to request the font as bold
            italic: Whether to request the font as italic
            dpi: The screen dpi

        Returns:
            LOGFONTW: a ctypes binding of a Win32 LOGFONTW struct
        """

        # 027285.python.win32.line307.comment Create a dummy DC for coordinate mapping
        with device_context(None) as dc:

            # 027286.python.win32.line310.comment Default to 96 DPI unless otherwise specified
            if dpi is None:
                dpi = 96
            log_pixels_y = dpi

            # 027287.python.win32.line315.comment Create LOGFONTW font description struct
            logfont = LOGFONTW()

            # 027288.python.win32.line318.comment Convert point size to actual device pixels
            logfont.lfHeight = int(-size * log_pixels_y // 72)

            # 027289.python.win32.line321.comment Configure the LOGFONTW's font properties
            if bold:
                logfont.lfWeight = FW_BOLD
            else:
                logfont.lfWeight = FW_NORMAL
            logfont.lfItalic = italic
            logfont.lfFaceName = name
            logfont.lfQuality = ANTIALIASED_QUALITY

        return logfont


def _get_font_families(font_collection: ctypes.c_void_p) -> Sequence[ctypes.c_void_p]:
    num_count = ctypes.c_int()
    gdiplus.GdipGetFontCollectionFamilyCount(
        font_collection, ctypes.byref(num_count))
    gpfamilies = (ctypes.c_void_p * num_count.value)()
    numFound = ctypes.c_int()
    gdiplus.GdipGetFontCollectionFamilyList(
        font_collection, num_count, gpfamilies, ctypes.byref(numFound))

    return gpfamilies

def _font_exists_in_collection(font_collection: ctypes.c_void_p, name: str) -> bool:
    font_name = ctypes.create_unicode_buffer(32)
    for gpfamily in _get_font_families(font_collection):
        gdiplus.GdipGetFamilyName(gpfamily, font_name, "\0")
        if font_name.value == name:
            return True

    return False


class GDIPlusFont(Win32Font):
    glyph_renderer_class: ClassVar[type[base.GlyphRenderer]] = GDIPlusGlyphRenderer

    _private_collection: ctypes.c_void_p | None = None
    _system_collection: ctypes.c_void_p | None = None

    _default_name = "Arial"

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool=False, stretch: bool=False,
                 dpi: int | None=None) -> None:
        if not name:
            name = self._default_name

        if stretch:
            warnings.warn("The current font render does not support stretching.")  # noqa: B028

        bold = weight if weight in (None, True, False) else "bold" in weight

        super().__init__(name, size, bold, italic, stretch, dpi)

        self._name = name

        family = ctypes.c_void_p()

        # 027291.python.win32.line378.comment GDI will add @ in front of a localized font for some Asian languages. However, GDI will also not find it
        # 027292.python.win32.line379.comment based on that name (???). Here we remove it before checking font collections.
        if name[0] == "@":
            name = name[1:]

        name = ctypes.c_wchar_p(name)

        # 027293.python.win32.line385.comment Look in private collection first:
        if self._private_collection:
            gdiplus.GdipCreateFontFamilyFromName(name, self._private_collection, ctypes.byref(family))

        # 027294.python.win32.line389.comment Then in system collection:
        if not family:
            if _debug_font:
                print(f"Warning: Font '{name}' was not found. Defaulting to: {self._default_name}") 

            gdiplus.GdipCreateFontFamilyFromName(name, None, ctypes.byref(family))

        # 027295.python.win32.line396.comment Nothing found, use default font.
        if not family:
            self._name = self._default_name
            gdiplus.GdipCreateFontFamilyFromName(ctypes.c_wchar_p(self._name), None, ctypes.byref(family))

        if dpi is None:
            unit = UnitPoint
            self.dpi = 96
        else:
            unit = UnitPixel
            size = (size * dpi) // 72
            self.dpi = dpi

        style = 0
        if bold:
            style |= FontStyleBold
        if italic:
            style |= FontStyleItalic
        self._gdipfont = ctypes.c_void_p()
        gdiplus.GdipCreateFont(family, ctypes.c_float(size), style, unit, ctypes.byref(self._gdipfont))
        gdiplus.GdipDeleteFontFamily(family)

    @property
    def name(self) -> str:
        return self._name

    def __del__(self) -> None:
        gdi32.DeleteObject(self.hfont)
        gdiplus.GdipDeleteFont(self._gdipfont)

    @classmethod
    def add_font_data(cls: type[GDIPlusFont], data: bytes) -> None:
        numfonts = ctypes.c_uint32()
        _handle = gdi32.AddFontMemResourceEx(data, len(data), 0, ctypes.byref(numfonts))

        # 027296.python.win32.line431.comment None means a null handle was returned, ie something went wrong
        if _handle is None:
            raise ctypes.WinError()

        if not cls._private_collection:
            cls._private_collection = ctypes.c_void_p()
            gdiplus.GdipNewPrivateFontCollection(
                ctypes.byref(cls._private_collection))
        gdiplus.GdipPrivateAddMemoryFont(cls._private_collection, data, len(data))

    @classmethod
    def have_font(cls: type[GDIPlusFont], name: str) -> bool:
        # 027297.python.win32.line443.comment Enumerate the private collection fonts first, as those are most likely to be used.
        if cls._private_collection and _font_exists_in_collection(cls._private_collection, name):
            return True

        # 027298.python.win32.line447.comment Instead of enumerating all fonts on the system, as there can potentially be thousands, attempt to create
        # 027299.python.win32.line448.comment the font family with the name. If it does not error (0), then it exists in the system.
        family = ctypes.c_void_p()
        status = gdiplus.GdipCreateFontFamilyFromName(name, None, ctypes.byref(family))
        if status == 0:
            # 027300.python.win32.line452.comment Delete temp family to prevent leak.
            gdiplus.GdipDeleteFontFamily(family)
            return True

        return False
