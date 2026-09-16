#!/usr/bin/env python

# 026505.python.png.line3.comment png.py - PNG encoder/decoder in pure Python
# 026506.python.png.line4.comment
# 026507.python.png.line5.comment Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
# 026508.python.png.line6.comment Portions Copyright (C) 2009 David Jones <drj@pobox.com>
# 026509.python.png.line7.comment And probably portions Copyright (C) 2006 Nicko van Someren <nicko@nicko.org>
# 026510.python.png.line8.comment
# 026511.python.png.line9.comment Original concept by Johann C. Rocholl.
# 026512.python.png.line10.comment
# 026513.python.png.line11.comment LICENCE (MIT)
# 026514.python.png.line12.comment
# 026515.python.png.line13.comment Permission is hereby granted, free of charge, to any person
# 026516.python.png.line14.comment obtaining a copy of this software and associated documentation files
# 026517.python.png.line15.comment (the "Software"), to deal in the Software without restriction,
# 026518.python.png.line16.comment including without limitation the rights to use, copy, modify, merge,
# 026519.python.png.line17.comment publish, distribute, sublicense, and/or sell copies of the Software,
# 026520.python.png.line18.comment and to permit persons to whom the Software is furnished to do so,
# 026521.python.png.line19.comment subject to the following conditions:
# 026522.python.png.line20.comment
# 026523.python.png.line21.comment The above copyright notice and this permission notice shall be
# 026524.python.png.line22.comment included in all copies or substantial portions of the Software.
# 026525.python.png.line23.comment
# 026526.python.png.line24.comment THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# 026527.python.png.line25.comment EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# 026528.python.png.line26.comment MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# 026529.python.png.line27.comment NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# 026530.python.png.line28.comment BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# 026531.python.png.line29.comment ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# 026532.python.png.line30.comment CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# 026533.python.png.line31.comment SOFTWARE.

"""
The ``png`` module can read and write PNG files.

Installation and Overview
-------------------------

``pip install pypng``

For help, type ``import png; help(png)`` in your python interpreter.

A good place to start is the :class:`Reader` and :class:`Writer` classes.

Coverage of PNG formats is fairly complete;
all allowable bit depths (1/2/4/8/16/24/32/48/64 bits per pixel) and
colour combinations are supported:

- greyscale (1/2/4/8/16 bit);
- RGB, RGBA, LA (greyscale with alpha) with 8/16 bits per channel;
- colour mapped images (1/2/4/8 bit).

Interlaced images,
which support a progressive display when downloading,
are supported for both reading and writing.

A number of optional chunks can be specified (when writing)
and understood (when reading): ``tRNS``, ``bKGD``, ``gAMA``.

The ``sBIT`` chunk can be used to specify precision for
non-native bit depths.

Requires Python 3.5 or higher.
Installation is trivial,
but see the ``README.txt`` file (with the source distribution) for details.

Full use of all features will need some reading of the PNG specification
http://www.w3.org/TR/2003/REC-PNG-20031110/.

The package also comes with command line utilities.

- ``pripamtopng`` converts
  `Netpbm <http://netpbm.sourceforge.net/>`_ PAM/PNM files to PNG;
- ``pripngtopam`` converts PNG to file PAM/PNM.

There are a few more for simple PNG manipulations.

Spelling and Terminology
------------------------

Generally British English spelling is used in the documentation.
So that's "greyscale" and "colour".
This not only matches the author's native language,
it's also used by the PNG specification.

Colour Models
-------------

The major colour models supported by PNG (and hence by PyPNG) are:

- greyscale;
- greyscale--alpha;
- RGB;
- RGB--alpha.

Also referred to using the abbreviations: L, LA, RGB, RGBA.
Each letter codes a single channel:
*L* is for Luminance or Luma or Lightness (greyscale images);
*A* stands for Alpha, the opacity channel
(used for transparency effects, but higher values are more opaque,
so it makes sense to call it opacity);
*R*, *G*, *B* stand for Red, Green, Blue (colour image).

Lists, arrays, sequences, and so on
-----------------------------------

When getting pixel data out of this module (reading) and
presenting data to this module (writing) there are
a number of ways the data could be represented as a Python value.

The preferred format is a sequence of *rows*,
which each row being a sequence of *values*.
In this format, the values are in pixel order,
with all the values from all the pixels in a row
being concatenated into a single sequence for that row.

Consider an image that is 3 pixels wide by 2 pixels high, and each pixel
has RGB components:

Sequence of rows::

  list([R,G,B, R,G,B, R,G,B],
       [R,G,B, R,G,B, R,G,B])

Each row appears as its own list,
but the pixels are flattened so that three values for one pixel
simply follow the three values for the previous pixel.

This is the preferred because
it provides a good compromise between space and convenience.
PyPNG regards itself as at liberty to replace any sequence type with
any sufficiently compatible other sequence type;
in practice each row is an array (``bytearray`` or ``array.array``).

To allow streaming the outer list is sometimes
an iterator rather than an explicit list.

An alternative format is a single array holding all the values.

Array of values::

  [R,G,B, R,G,B, R,G,B,
   R,G,B, R,G,B, R,G,B]

The entire image is one single giant sequence of colour values.
Generally an array will be used (to save space), not a list.

The top row comes first,
and within each row the pixels are ordered from left-to-right.
Within a pixel the values appear in the order R-G-B-A
(or L-A for greyscale--alpha).

There is another format, which should only be used with caution.
It is mentioned because it is used internally,
is close to what lies inside a PNG file itself,
and has some support from the public API.
This format is called *packed*.
When packed, each row is a sequence of bytes (integers from 0 to 255),
just as it is before PNG scanline filtering is applied.
When the bit depth is 8 this is the same as a sequence of rows;
when the bit depth is less than 8 (1, 2 and 4),
several pixels are packed into each byte;
when the bit depth is 16 each pixel value is decomposed into 2 bytes
(and `packed` is a misnomer).
This format is used by the :meth:`Writer.write_packed` method.
It isn't usually a convenient format,
but may be just right if the source data for
the PNG image comes from something that uses a similar format
(for example, 1-bit BMPs, or another PNG file).
"""

__version__ = "0.0.20"

import collections
import io   # For io.BytesIO
import itertools
import math
# 026535.python.png.line178.comment http://www.python.org/doc/2.4.4/lib/module-operator.html
import operator
import re
import struct
import sys
# 026536.python.png.line183.comment http://www.python.org/doc/2.4.4/lib/module-warnings.html
import warnings
import zlib

from array import array


__all__ = ['Image', 'Reader', 'Writer', 'write_chunks', 'from_array']


# 026537.python.png.line193.comment The PNG signature.
# 026538.python.png.line194.comment http://www.w3.org/TR/PNG/#5PNG-file-signature
signature = struct.pack('8B', 137, 80, 78, 71, 13, 10, 26, 10)

# 026539.python.png.line197.comment The xstart, ystart, xstep, ystep for the Adam7 interlace passes.
adam7 = ((0, 0, 8, 8),
         (4, 0, 8, 8),
         (0, 4, 4, 8),
         (2, 0, 4, 4),
         (0, 2, 2, 4),
         (1, 0, 2, 2),
         (0, 1, 1, 2))


def adam7_generate(width, height):
    """
    Generate the coordinates for the reduced scanlines
    of an Adam7 interlaced image
    of size `width` by `height` pixels.

    Yields a generator for each pass,
    and each pass generator yields a series of (x, y, xstep) triples,
    each one identifying a reduced scanline consisting of
    pixels starting at (x, y) and taking every xstep pixel to the right.
    """

    for xstart, ystart, xstep, ystep in adam7:
        if xstart >= width:
            continue
        yield ((xstart, y, xstep) for y in range(ystart, height, ystep))


# 026540.python.png.line225.comment Models the 'pHYs' chunk (used by the Reader)
Resolution = collections.namedtuple('_Resolution', 'x y unit_is_meter')


def group(s, n):
    return list(zip(* [iter(s)] * n))


def isarray(x):
    return isinstance(x, array)


def check_palette(palette):
    """
    Check a palette argument (to the :class:`Writer` class) for validity.
    Returns the palette as a list if okay;
    raises an exception otherwise.
    """

    # 026541.python.png.line244.comment None is the default and is allowed.
    if palette is None:
        return None

    p = list(palette)
    if not (0 < len(p) <= 256):
        raise ProtocolError(
            "a palette must have between 1 and 256 entries,"
            " see https://www.w3.org/TR/PNG/#11PLTE")
    seen_triple = False
    for i, t in enumerate(p):
        if len(t) not in (3, 4):
            raise ProtocolError(
                f"palette entry {i}: entries must be 3- or 4-tuples.")
        if len(t) == 3:
            seen_triple = True
        if seen_triple and len(t) == 4:
            raise ProtocolError(
                f"palette entry {i}: all 4-tuples must precede all 3-tuples")
        for x in t:
            if int(x) != x or not(0 <= x <= 255):
                raise ProtocolError(
                    f"palette entry {i}: "
                    "values must be integer: 0 <= x <= 255")
    return p


def check_sizes(size, width, height):
    """
    Check that these arguments, if supplied, are consistent.
    Return a (width, height) pair.
    """

    if not size:
        return width, height

    if len(size) != 2:
        raise ProtocolError(
            "size argument should be a pair (width, height)")
    if width is not None and width != size[0]:
        raise ProtocolError(
            f"size[0] ({size[0]}) and width ({width}) should match when both are used.")
    if height is not None and height != size[1]:
        raise ProtocolError(
            f"size[1] ({size[1]}) and height ({height}) should match when both are used.")
    return size


def check_color(c, greyscale, which):
    """
    Checks that a colour argument for transparent or background options
    is the right form.
    Returns the colour
    (which, if it's a bare integer, is "corrected" to a 1-tuple).
    """

    if c is None:
        return c
    if greyscale:
        try:
            len(c)
        except TypeError:
            c = (c,)
        if len(c) != 1:
            raise ProtocolError(f"{which} for greyscale must be 1-tuple")
        if not is_natural(c[0]):
            raise ProtocolError(
                f"{which} colour for greyscale must be integer")
    else:
        if not (len(c) == 3 and
                is_natural(c[0]) and
                is_natural(c[1]) and
                is_natural(c[2])):
            raise ProtocolError(
                f"{which} colour must be a triple of integers")
    return c


class Error(Exception):
    def __str__(self):
        return self.__class__.__name__ + ': ' + ' '.join(self.args)


class FormatError(Error):
    """
    Problem with input file format.
    In other words, PNG file does not conform to
    the specification in some way and is invalid.
    """


class ProtocolError(Error):
    """
    Problem with the way the programming interface has been used,
    or the data presented to it.
    """


class ChunkError(FormatError):
    pass


class Default:
    """The default for the greyscale paramter."""


class Writer:
    """
    PNG encoder in pure Python.
    """

    def __init__(self, width=None, height=None,
                 size=None,
                 greyscale=Default,
                 alpha=False,
                 bitdepth=8,
                 palette=None,
                 transparent=None,
                 background=None,
                 gamma=None,
                 compression=None,
                 interlace=False,
                 planes=None,
                 colormap=None,
                 maxval=None,
                 chunk_limit=2**20,
                 x_pixels_per_unit=None,
                 y_pixels_per_unit=None,
                 unit_is_meter=False):
        """
        Create a PNG encoder object.

        Arguments:

        width, height
          Image size in pixels, as two separate arguments.
        size
          Image size (w,h) in pixels, as single argument.
        greyscale
          Pixels are greyscale, not RGB.
        alpha
          Input data has alpha channel (RGBA or LA).
        bitdepth
          Bit depth: from 1 to 16 (for each channel).
        palette
          Create a palette for a colour mapped image (colour type 3).
        transparent
          Specify a transparent colour (create a ``tRNS`` chunk).
        background
          Specify a default background colour (create a ``bKGD`` chunk).
        gamma
          Specify a gamma value (create a ``gAMA`` chunk).
        compression
          zlib compression level: 0 (none) to 9 (more compressed);
          default: -1 or None.
        interlace
          Create an interlaced image.
        chunk_limit
          Write multiple ``IDAT`` chunks to save memory.
        x_pixels_per_unit
          Number of pixels a unit along the x axis (write a
          `pHYs` chunk).
        y_pixels_per_unit
          Number of pixels a unit along the y axis (write a
          `pHYs` chunk). Along with `x_pixel_unit`, this gives
          the pixel size ratio.
        unit_is_meter
          `True` to indicate that the unit (for the `pHYs`
          chunk) is metre.

        The image size (in pixels) can be specified either by using the
        `width` and `height` arguments, or with the single `size`
        argument.
        If `size` is used it should be a pair (*width*, *height*).

        The `greyscale` argument indicates whether input pixels
        are greyscale (when true), or colour (when false).
        The default is true unless `palette=` is used.

        The `alpha` argument (a boolean) specifies
        whether input pixels have an alpha channel (or not).

        `bitdepth` specifies the bit depth of the source pixel values.
        Each channel may have a different bit depth.
        Each source pixel must have values that are
        an integer between 0 and ``2**bitdepth-1``, where
        `bitdepth` is the bit depth for the corresponding channel.
        For example, 8-bit images have values between 0 and 255.
        PNG only stores images with bit depths of
        1,2,4,8, or 16 (the same for all channels).
        When `bitdepth` is not one of these values or where
        channels have different bit depths,
        the next highest valid bit depth is selected,
        and an ``sBIT`` (significant bits) chunk is generated
        that specifies the original precision of the source image.
        In this case the supplied pixel values will be rescaled to
        fit the range of the selected bit depth.

        The PNG file format supports many bit depth / colour model
        combinations, but not all.
        The details are somewhat arcane
        (refer to the PNG specification for full details).
        Briefly:
        Bit depths < 8 (1,2,4) are only allowed with greyscale and
        colour mapped images;
        colour mapped images cannot have bit depth 16.

        For colour mapped images
        (in other words, when the `palette` argument is specified)
        the `bitdepth` argument must match one of
        the valid PNG bit depths: 1, 2, 4, or 8.
        (It is valid to have a PNG image with a palette and
        an ``sBIT`` chunk, but the meaning is slightly different;
        it would be awkward to use the `bitdepth` argument for this.)

        The `palette` option, when specified,
        causes a colour mapped image to be created:
        the PNG colour type is set to 3;
        `greyscale` must not be true; `alpha` must not be true;
        `transparent` must not be set.
        The bit depth must be 1,2,4, or 8.
        When a colour mapped image is created,
        the pixel values are palette indexes and
        the `bitdepth` argument specifies the size of these indexes
        (not the size of the colour values in the palette).

        The palette argument value should be a sequence of 3- or
        4-tuples.
        3-tuples specify RGB palette entries;
        4-tuples specify RGBA palette entries.
        All the 4-tuples (if present) must come before all the 3-tuples.
        A ``PLTE`` chunk is created;
        if there are 4-tuples then a ``tRNS`` chunk is created as well.
        The ``PLTE`` chunk will contain all the RGB triples in the same
        sequence;
        the ``tRNS`` chunk will contain the alpha channel for
        all the 4-tuples, in the same sequence.
        Palette entries are always 8-bit.

        If specified, the `transparent` and `background` parameters must be
        a tuple with one element for each channel in the image.
        Either a 3-tuple of integer (RGB) values for a colour image, or
        a 1-tuple of a single integer for a greyscale image.

        If specified, the `gamma` parameter must be a positive number
        (generally, a `float`).
        A ``gAMA`` chunk will be created.
        Note that this will not change the values of the pixels as
        they appear in the PNG file,
        they are assumed to have already
        been converted appropriately for the gamma specified.

        The `compression` argument specifies the compression level to
        be used by the ``zlib`` module.
        Values from 1 to 9 (highest) specify compression.
        0 means no compression.
        -1 and ``None`` both mean that the ``zlib`` module uses
        the default level of compession (which is generally acceptable).

        If `interlace` is true then an interlaced image is created
        (using PNG's so far only interace method, *Adam7*).
        This does not affect how the pixels should be passed in,
        rather it changes how they are arranged into the PNG file.
        On slow connexions interlaced images can be
        partially decoded by the browser to give
        a rough view of the image that is
        successively refined as more image data appears.

        .. note ::

          Enabling the `interlace` option requires the entire image
          to be processed in working memory.

        `chunk_limit` is used to limit the amount of memory used whilst
        compressing the image.
        In order to avoid using large amounts of memory,
        multiple ``IDAT`` chunks may be created.
        """

        # 026542.python.png.line523.comment At the moment the `planes` argument is ignored;
        # 026543.python.png.line524.comment its purpose is to act as a dummy so that
        # 026544.python.png.line525.comment ``Writer(x, y, **info)`` works, where `info` is a dictionary
        # 026545.python.png.line526.comment returned by Reader.read and friends.
        # 026546.python.png.line527.comment Ditto for `colormap`.

        width, height = check_sizes(size, width, height)
        del size

        if not is_natural(width) or not is_natural(height):
            raise ProtocolError("width and height must be integers")
        if width <= 0 or height <= 0:
            raise ProtocolError("width and height must be greater than zero")
        # 026547.python.png.line536.comment http://www.w3.org/TR/PNG/#7Integers-and-byte-order
        if width > 2 ** 31 - 1 or height > 2 ** 31 - 1:
            raise ProtocolError("width and height cannot exceed 2**31-1")

        if alpha and transparent is not None:
            raise ProtocolError(
                "transparent colour not allowed with alpha channel")

        # 026548.python.png.line544.comment bitdepth is either single integer, or tuple of integers.
        # 026549.python.png.line545.comment Convert to tuple.
        try:
            len(bitdepth)
        except TypeError:
            bitdepth = (bitdepth, )
        for b in bitdepth:
            valid = is_natural(b) and 1 <= b <= 16
            if not valid:
                raise ProtocolError(
                    f"each bitdepth {bitdepth} must be a positive integer <= 16")

        # 026550.python.png.line556.comment Calculate channels, and
        # 026551.python.png.line557.comment expand bitdepth to be one element per channel.
        palette = check_palette(palette)
        alpha = bool(alpha)
        colormap = bool(palette)
        if greyscale is Default and palette:
            greyscale = False
        greyscale = bool(greyscale)
        if colormap:
            color_planes = 1
            planes = 1
        else:
            color_planes = (3, 1)[greyscale]
            planes = color_planes + alpha
        if len(bitdepth) == 1:
            bitdepth *= planes

        bitdepth, self.rescale = check_bitdepth_rescale(
                palette,
                bitdepth,
                transparent, alpha, greyscale)

        # 026552.python.png.line578.comment These are assertions, because above logic should have
        # 026553.python.png.line579.comment corrected or raised all problematic cases.
        if bitdepth < 8:
            assert greyscale or palette
            assert not alpha
        if bitdepth > 8:
            assert not palette

        transparent = check_color(transparent, greyscale, 'transparent')
        background = check_color(background, greyscale, 'background')

        # 026554.python.png.line589.comment It's important that the true boolean values
        # 026555.python.png.line590.comment (greyscale, alpha, colormap, interlace) are converted
        # 026556.python.png.line591.comment to bool because Iverson's convention is relied upon later on.
        self.width = width
        self.height = height
        self.transparent = transparent
        self.background = background
        self.gamma = gamma
        self.greyscale = greyscale
        self.alpha = alpha
        self.colormap = colormap
        self.bitdepth = int(bitdepth)
        self.compression = compression
        self.chunk_limit = chunk_limit
        self.interlace = bool(interlace)
        self.palette = palette
        self.x_pixels_per_unit = x_pixels_per_unit
        self.y_pixels_per_unit = y_pixels_per_unit
        self.unit_is_meter = bool(unit_is_meter)

        self.color_type = (4 * self.alpha +
                           2 * (not greyscale) +
                           1 * self.colormap)
        assert self.color_type in (0, 2, 3, 4, 6)

        self.color_planes = color_planes
        self.planes = planes
        # 026557.python.png.line616.comment :todo: fix for bitdepth < 8
        self.psize = (self.bitdepth / 8) * self.planes

    def write(self, outfile, rows):
        """
        Write a PNG image to the output file.
        `rows` should be an iterable that yields each row
        (each row is a sequence of values).
        The rows should be the rows of the original image,
        so there should be ``self.height`` rows of
        ``self.width * self.planes`` values.
        If `interlace` is specified (when creating the instance),
        then an interlaced PNG file will be written.
        Supply the rows in the normal image order;
        the interlacing is carried out internally.

        .. note ::

          Interlacing requires the entire image to be in working memory.
        """

        # 026558.python.png.line637.comment Values per row
        vpr = self.width * self.planes

        def check_rows(rows):
            """
            Yield each row in rows,
            but check each row first (for correct width).
            """
            for i, row in enumerate(rows):
                try:
                    wrong_length = len(row) != vpr
                except TypeError:
                    # 026559.python.png.line649.comment When using an itertools.ichain object or
                    # 026560.python.png.line650.comment other generator not supporting __len__,
                    # 026561.python.png.line651.comment we set this to False to skip the check.
                    wrong_length = False
                if wrong_length:
                    # 026562.python.png.line654.comment Note: row numbers start at 0.
                    raise ProtocolError(
                        f"Expected {vpr} values but got {len(row)} values, in row {i}")
                yield row

        if self.interlace:
            fmt = 'BH'[self.bitdepth > 8]
            a = array(fmt, itertools.chain(*check_rows(rows)))
            return self.write_array(outfile, a)

        nrows = self.write_passes(outfile, check_rows(rows))
        if nrows != self.height:
            raise ProtocolError(
                f"rows supplied ({nrows}) does not match height ({self.height})")
        return nrows

    def write_passes(self, outfile, rows):
        """
        Write a PNG image to the output file.

        Most users are expected to find the :meth:`write` or
        :meth:`write_array` method more convenient.

        The rows should be given to this method in the order that
        they appear in the output file.
        For straightlaced images, this is the usual top to bottom ordering.
        For interlaced images the rows should have been interlaced before
        passing them to this function.

        `rows` should be an iterable that yields each row
        (each row being a sequence of values).
        """

        # 026563.python.png.line687.comment Ensure rows are scaled (to 4-/8-/16-bit),
        # 026564.python.png.line688.comment and packed into bytes.

        if self.rescale:
            rows = rescale_rows(rows, self.rescale)

        if self.bitdepth < 8:
            rows = pack_rows(rows, self.bitdepth)
        elif self.bitdepth == 16:
            rows = unpack_rows(rows)

        return self.write_packed(outfile, rows)

    def write_packed(self, outfile, rows):
        """
        Write PNG file to `outfile`.
        `rows` should be an iterator that yields each packed row;
        a packed row being a sequence of packed bytes.

        The rows have a filter byte prefixed and
        are then compressed into one or more IDAT chunks.
        They are not processed any further,
        so if bitdepth is other than 1, 2, 4, 8, 16,
        the pixel values should have been scaled
        before passing them to this method.

        This method does work for interlaced images but it is best avoided.
        For interlaced images, the rows should be
        presented in the order that they appear in the file.
        """

        self.write_preamble(outfile)

        # 026565.python.png.line720.comment http://www.w3.org/TR/PNG/#11IDAT
        if self.compression is not None:
            compressor = zlib.compressobj(self.compression)
        else:
            compressor = zlib.compressobj()

        # 026566.python.png.line726.comment data accumulates bytes to be compressed for the IDAT chunk;
        # 026567.python.png.line727.comment it's compressed when sufficiently large.
        data = bytearray()

        # 026568.python.png.line730.comment raise i scope out of the for loop. set to -1, because the for loop
        # 026569.python.png.line731.comment sets i to 0 on the first pass
        i = -1
        for i, row in enumerate(rows):
            # 026570.python.png.line734.comment Add "None" filter type.
            # 026571.python.png.line735.comment Currently, it's essential that this filter type be used
            # 026572.python.png.line736.comment for every scanline as
            # 026573.python.png.line737.comment we do not mark the first row of a reduced pass image;
            # 026574.python.png.line738.comment that means we could accidentally compute
            # 026575.python.png.line739.comment the wrong filtered scanline if we used
            # 026576.python.png.line740.comment "up", "average", or "paeth" on such a line.
            data.append(0)
            data.extend(row)
            if len(data) > self.chunk_limit:
                compressed = compressor.compress(data)
                if len(compressed):
                    write_chunk(outfile, b'IDAT', compressed)
                data = bytearray()

        compressed = compressor.compress(bytes(data))
        flushed = compressor.flush()
        if len(compressed) or len(flushed):
            write_chunk(outfile, b'IDAT', compressed + flushed)
        # 026577.python.png.line753.comment http://www.w3.org/TR/PNG/#11IEND
        write_chunk(outfile, b'IEND')
        return i + 1

    def write_preamble(self, outfile):
        # 026578.python.png.line758.comment http://www.w3.org/TR/PNG/#5PNG-file-signature
        outfile.write(signature)

        # 026579.python.png.line761.comment http://www.w3.org/TR/PNG/#11IHDR
        write_chunk(outfile, b'IHDR',
                    struct.pack("!2I5B", self.width, self.height,
                                self.bitdepth, self.color_type,
                                0, 0, self.interlace))

        # 026580.python.png.line767.comment See :chunk:order
        # 026581.python.png.line768.comment http://www.w3.org/TR/PNG/#11gAMA
        if self.gamma is not None:
            write_chunk(outfile, b'gAMA',
                        struct.pack("!L", int(round(self.gamma * 1e5))))

        # 026582.python.png.line773.comment See :chunk:order
        # 026583.python.png.line774.comment http://www.w3.org/TR/PNG/#11sBIT
        if self.rescale:
            write_chunk(
                outfile, b'sBIT',
                struct.pack(f'{self.planes,* [s[0] for s in self.rescale]}B' ))

        # 026584.python.png.line780.comment :chunk:order: Without a palette (PLTE chunk),
        # 026585.python.png.line781.comment ordering is relatively relaxed.
        # 026586.python.png.line782.comment With one, gAMA chunk must precede PLTE chunk
        # 026587.python.png.line783.comment which must precede tRNS and bKGD.
        # 026588.python.png.line784.comment See http://www.w3.org/TR/PNG/#5ChunkOrdering
        if self.palette:
            p, t = make_palette_chunks(self.palette)
            write_chunk(outfile, b'PLTE', p)
            if t:
                # 026589.python.png.line789.comment tRNS chunk is optional;
                # 026590.python.png.line790.comment Only needed if palette entries have alpha.
                write_chunk(outfile, b'tRNS', t)

        # 026591.python.png.line793.comment http://www.w3.org/TR/PNG/#11tRNS
        if self.transparent is not None:
            if self.greyscale:
                fmt = "!1H"
            else:
                fmt = "!3H"
            write_chunk(outfile, b'tRNS',
                        struct.pack(fmt, *self.transparent))

        # 026592.python.png.line802.comment http://www.w3.org/TR/PNG/#11bKGD
        if self.background is not None:
            if self.greyscale:
                fmt = "!1H"
            else:
                fmt = "!3H"
            write_chunk(outfile, b'bKGD',
                        struct.pack(fmt, *self.background))

        # 026593.python.png.line811.comment http://www.w3.org/TR/PNG/#11pHYs
        if (self.x_pixels_per_unit is not None and
                self.y_pixels_per_unit is not None):
            tup = (self.x_pixels_per_unit,
                   self.y_pixels_per_unit,
                   int(self.unit_is_meter))
            write_chunk(outfile, b'pHYs', struct.pack("!LLB", *tup))

    def write_array(self, outfile, pixels):
        """
        Write an array that holds all the image values
        as a PNG file on the output file.
        See also :meth:`write` method.
        """

        if self.interlace:
            if type(pixels) != array:
                # 026594.python.png.line828.comment Coerce to array type
                fmt = 'BH'[self.bitdepth > 8]
                pixels = array(fmt, pixels)
            return self.write_passes(
                outfile,
                self.array_scanlines_interlace(pixels)
            )
        else:
            return self.write_passes(
                outfile,
                self.array_scanlines(pixels)
            )

    def array_scanlines(self, pixels):
        """
        Generates rows (each a sequence of values) from
        a single array of values.
        """

        # 026595.python.png.line847.comment Values per row
        vpr = self.width * self.planes
        stop = 0
        for y in range(self.height):
            start = stop
            stop = start + vpr
            yield pixels[start:stop]

    def array_scanlines_interlace(self, pixels):
        """
        Generator for interlaced scanlines from an array.
        `pixels` is the full source image as a single array of values.
        The generator yields each scanline of the reduced passes in turn,
        each scanline being a sequence of values.
        """

        # 026596.python.png.line863.comment http://www.w3.org/TR/PNG/#8InterlaceMethods
        # 026597.python.png.line864.comment Array type.
        fmt = 'BH'[self.bitdepth > 8]
        # 026598.python.png.line866.comment Value per row
        vpr = self.width * self.planes

        # 026599.python.png.line869.comment Each iteration generates a scanline starting at (x, y)
        # 026600.python.png.line870.comment and consisting of every xstep pixels.
        for lines in adam7_generate(self.width, self.height):
            for x, y, xstep in lines:
                # 026601.python.png.line873.comment Pixels per row (of reduced image)
                ppr = int(math.ceil((self.width - x) / float(xstep)))
                # 026602.python.png.line875.comment Values per row (of reduced image)
                reduced_row_len = ppr * self.planes
                if xstep == 1:
                    # 026603.python.png.line878.comment Easy case: line is a simple slice.
                    offset = y * vpr
                    yield pixels[offset: offset + vpr]
                    continue
                # 026604.python.png.line882.comment We have to step by xstep,
                # 026605.python.png.line883.comment which we can do one plane at a time
                # 026606.python.png.line884.comment using the step in Python slices.
                row = array(fmt)
                # 026607.python.png.line886.comment There's no easier way to set the length of an array
                row.extend(pixels[0:reduced_row_len])
                offset = y * vpr + x * self.planes
                end_offset = (y + 1) * vpr
                skip = self.planes * xstep
                for i in range(self.planes):
                    row[i::self.planes] = \
                        pixels[offset + i: end_offset: skip]
                yield row


def write_chunk(outfile, tag, data=b''):
    """
    Write a PNG chunk to the output file, including length and
    checksum.
    """

    data = bytes(data)
    # 026608.python.png.line904.comment http://www.w3.org/TR/PNG/#5Chunk-layout
    outfile.write(struct.pack("!I", len(data)))
    outfile.write(tag)
    outfile.write(data)
    checksum = zlib.crc32(tag)
    checksum = zlib.crc32(data, checksum)
    checksum &= 2 ** 32 - 1
    outfile.write(struct.pack("!I", checksum))


def write_chunks(out, chunks):
    """Create a PNG file by writing out the chunks."""

    out.write(signature)
    for chunk in chunks:
        write_chunk(out, *chunk)


def rescale_rows(rows, rescale):
    """
    Take each row in rows (an iterator) and yield
    a fresh row with the pixels scaled according to
    the rescale parameters in the list `rescale`.
    Each element of `rescale` is a tuple of
    (source_bitdepth, target_bitdepth),
    with one element per channel.
    """

    # 026609.python.png.line932.comment One factor for each channel
    fs = [float(2 ** s[1] - 1)/float(2 ** s[0] - 1)
          for s in rescale]

    # 026610.python.png.line936.comment Assume all target_bitdepths are the same
    target_bitdepths = set(s[1] for s in rescale)
    assert len(target_bitdepths) == 1
    (target_bitdepth, ) = target_bitdepths
    typecode = 'BH'[target_bitdepth > 8]

    # 026611.python.png.line942.comment Number of channels
    n_chans = len(rescale)

    for row in rows:
        rescaled_row = array(typecode, iter(row))
        for i in range(n_chans):
            channel = array(
                typecode,
                (int(round(fs[i] * x)) for x in row[i::n_chans]))
            rescaled_row[i::n_chans] = channel
        yield rescaled_row


def pack_rows(rows, bitdepth):
    """Yield packed rows that are a byte array.
    Each byte is packed with the values from several pixels.
    """

    assert bitdepth < 8
    assert 8 % bitdepth == 0

    # 026612.python.png.line963.comment samples per byte
    spb = int(8 / bitdepth)

    def make_byte(block):
        """Take a block of (2, 4, or 8) values,
        and pack them into a single byte.
        """

        res = 0
        for v in block:
            res = (res << bitdepth) + v
        return res

    for row in rows:
        a = bytearray(row)
        # 026613.python.png.line978.comment Adding padding bytes so we can group into a whole
        # 026614.python.png.line979.comment number of spb-tuples.
        n = float(len(a))
        extra = math.ceil(n / spb) * spb - n
        a.extend([0] * int(extra))
        # 026615.python.png.line983.comment Pack into bytes.
        # 026616.python.png.line984.comment Each block is the samples for one byte.
        blocks = group(a, spb)
        yield bytearray(make_byte(block) for block in blocks)


def unpack_rows(rows):
    """Unpack each row from being 16-bits per value,
    to being a sequence of bytes.
    """
    for row in rows:
        fmt = f'!{len(row)}H'
        yield bytearray(struct.pack(fmt, *row))


def make_palette_chunks(palette):
    """
    Create the byte sequences for a ``PLTE`` and
    if necessary a ``tRNS`` chunk.
    Returned as a pair (*p*, *t*).
    *t* will be ``None`` if no ``tRNS`` chunk is necessary.
    """

    p = bytearray()
    t = bytearray()

    for x in palette:
        p.extend(x[0:3])
        if len(x) > 3:
            t.append(x[3])
    if t:
        return p, t
    return p, None


def check_bitdepth_rescale(
        palette, bitdepth, transparent, alpha, greyscale):
    """
    Returns (bitdepth, rescale) pair.
    """

    if palette:
        if len(bitdepth) != 1:
            raise ProtocolError(
                "with palette, only a single bitdepth may be used")
        (bitdepth, ) = bitdepth
        if bitdepth not in (1, 2, 4, 8):
            raise ProtocolError(
                "with palette, bitdepth must be 1, 2, 4, or 8")
        if transparent is not None:
            raise ProtocolError("transparent and palette not compatible")
        if alpha:
            raise ProtocolError("alpha and palette not compatible")
        if greyscale:
            raise ProtocolError("greyscale and palette not compatible")
        return bitdepth, None

    # 026617.python.png.line1040.comment No palette, check for sBIT chunk generation.

    if greyscale and not alpha:
        # 026618.python.png.line1043.comment Single channel, L.
        (bitdepth,) = bitdepth
        if bitdepth in (1, 2, 4, 8, 16):
            return bitdepth, None
        if bitdepth > 8:
            targetbitdepth = 16
        elif bitdepth == 3:
            targetbitdepth = 4
        else:
            assert bitdepth in (5, 6, 7)
            targetbitdepth = 8
        return targetbitdepth, [(bitdepth, targetbitdepth)]

    assert alpha or not greyscale

    depth_set = tuple(set(bitdepth))
    if depth_set in [(8,), (16,)]:
        # 026619.python.png.line1060.comment No sBIT required.
        (bitdepth, ) = depth_set
        return bitdepth, None

    targetbitdepth = (8, 16)[max(bitdepth) > 8]
    return targetbitdepth, [(b, targetbitdepth) for b in bitdepth]


# 026620.python.png.line1068.comment Regex for decoding mode string
RegexModeDecode = re.compile("(LA?|RGBA?);?([0-9]*)", flags=re.IGNORECASE)


def from_array(a, mode=None, info={}):
    """
    Create a PNG :class:`Image` object from a 2-dimensional array.
    One application of this function is easy PIL-style saving:
    ``png.from_array(pixels, 'L').save('foo.png')``.

    Unless they are specified using the *info* parameter,
    the PNG's height and width are taken from the array size.
    The first axis is the height; the second axis is the
    ravelled width and channel index.
    The array is treated is a sequence of rows,
    each row being a sequence of values (``width*channels`` in number).
    So an RGB image that is 16 pixels high and 8 wide will
    occupy a 2-dimensional array that is 16x24
    (each row will be 8*3 = 24 sample values).

    *mode* is a string that specifies the image colour format in a
    PIL-style mode.  It can be:

    ``'L'``
      greyscale (1 channel)
    ``'LA'``
      greyscale with alpha (2 channel)
    ``'RGB'``
      colour image (3 channel)
    ``'RGBA'``
      colour image with alpha (4 channel)

    The mode string can also specify the bit depth
    (overriding how this function normally derives the bit depth,
    see below).
    Appending ``';16'`` to the mode will cause the PNG to be
    16 bits per channel;
    any decimal from 1 to 16 can be used to specify the bit depth.

    When a 2-dimensional array is used *mode* determines how many
    channels the image has, and so allows the width to be derived from
    the second array dimension.

    The array is expected to be a ``numpy`` array,
    but it can be any suitable Python sequence.
    For example, a list of lists can be used:
    ``png.from_array([[0, 255, 0], [255, 0, 255]], 'L')``.
    The exact rules are: ``len(a)`` gives the first dimension, height;
    ``len(a[0])`` gives the second dimension.
    It's slightly more complicated than that because
    an iterator of rows can be used, and it all still works.
    Using an iterator allows data to be streamed efficiently.

    The bit depth of the PNG is normally taken from
    the array element's datatype
    (but if *mode* specifies a bitdepth then that is used instead).
    The array element's datatype is determined in a way which
    is supposed to work both for ``numpy`` arrays and for Python
    ``array.array`` objects.
    A 1 byte datatype will give a bit depth of 8,
    a 2 byte datatype will give a bit depth of 16.
    If the datatype does not have an implicit size,
    like the above example where it is a plain Python list of lists,
    then a default of 8 is used.

    The *info* parameter is a dictionary that can
    be used to specify metadata (in the same style as
    the arguments to the :class:`png.Writer` class).
    For this function the keys that are useful are:

    height
      overrides the height derived from the array dimensions and
      allows *a* to be an iterable.
    width
      overrides the width derived from the array dimensions.
    bitdepth
      overrides the bit depth derived from the element datatype
      (but must match *mode* if that also specifies a bit depth).

    Generally anything specified in the *info* dictionary will
    override any implicit choices that this function would otherwise make,
    but must match any explicit ones.
    For example, if the *info* dictionary has a ``greyscale`` key then
    this must be true when mode is ``'L'`` or ``'LA'`` and
    false when mode is ``'RGB'`` or ``'RGBA'``.
    """

    # 026621.python.png.line1155.comment We abuse the *info* parameter by modifying it.  Take a copy here.
    # 026622.python.png.line1156.comment (Also typechecks *info* to some extent).
    info = dict(info)

    # 026623.python.png.line1159.comment Syntax check mode string.
    match = RegexModeDecode.match(mode)
    if not match:
        raise Error("mode string should be 'RGB' or 'L;16' or similar.")

    mode, bitdepth = match.groups()
    if bitdepth:
        bitdepth = int(bitdepth)

    # 026624.python.png.line1168.comment Colour format.
    if 'greyscale' in info:
        if bool(info['greyscale']) != ('L' in mode):
            raise ProtocolError("info['greyscale'] should match mode.")
    info['greyscale'] = 'L' in mode

    alpha = 'A' in mode
    if 'alpha' in info:
        if bool(info['alpha']) != alpha:
            raise ProtocolError("info['alpha'] should match mode.")
    info['alpha'] = alpha

    # 026625.python.png.line1180.comment Get bitdepth from *mode* if possible.
    if bitdepth:
        if info.get("bitdepth") and bitdepth != info['bitdepth']:
            raise ProtocolError(
                f"bitdepth ({bitdepth}) should match bitdepth of info ({info[bitdepth]}).")
        info['bitdepth'] = bitdepth

    # 026626.python.png.line1187.comment Fill in and/or check entries in *info*.
    # 026627.python.png.line1188.comment Dimensions.
    width, height = check_sizes(
        info.get("size"),
        info.get("width"),
        info.get("height"))
    if width:
        info["width"] = width
    if height:
        info["height"] = height

    if "height" not in info:
        try:
            info['height'] = len(a)
        except TypeError:
            raise ProtocolError(
                "len(a) does not work, supply info['height'] instead.")

    planes = len(mode)
    if 'planes' in info:
        if info['planes'] != planes:
            raise Error("info['planes'] should match mode.")

    # 026628.python.png.line1210.comment In order to work out whether we the array is 2D or 3D we need its
    # 026629.python.png.line1211.comment first row, which requires that we take a copy of its iterator.
    # 026630.python.png.line1212.comment We may also need the first row to derive width and bitdepth.
    a, t = itertools.tee(a)
    row = next(t)
    del t

    testelement = row
    if 'width' not in info:
        width = len(row) // planes
        info['width'] = width

    if 'bitdepth' not in info:
        try:
            dtype = testelement.dtype
            # 026631.python.png.line1225.comment goto the "else:" clause.  Sorry.
        except AttributeError:
            try:
                # 026632.python.png.line1228.comment Try a Python array.array.
                bitdepth = 8 * testelement.itemsize
            except AttributeError:
                # 026633.python.png.line1231.comment We can't determine it from the array element's datatype,
                # 026634.python.png.line1232.comment use a default of 8.
                bitdepth = 8
        else:
            # 026635.python.png.line1235.comment If we got here without exception,
            # 026636.python.png.line1236.comment we now assume that the array is a numpy array.
            if dtype.kind == 'b':
                bitdepth = 1
            else:
                bitdepth = 8 * dtype.itemsize
        info['bitdepth'] = bitdepth

    for thing in ["width", "height", "bitdepth", "greyscale", "alpha"]:
        assert thing in info

    return Image(a, info)


# 026637.python.png.line1249.comment So that refugee's from PIL feel more at home.  Not documented.
fromarray = from_array


class Image:
    """A PNG image.  You can create an :class:`Image` object from
    an array of pixels by calling :meth:`png.from_array`.  It can be
    saved to disk with the :meth:`save` method.
    """

    def __init__(self, rows, info):
        """
        .. note ::

          The constructor is not public.  Please do not call it.
        """

        self.rows = rows
        self.info = info

    def save(self, file):
        """Save the image to the named *file*.

        See `.write()` if you already have an open file object.

        In general, you can only call this method once;
        after it has been called the first time the PNG image is written,
        the source data will have been streamed, and
        cannot be streamed again.
        """

        w = Writer(**self.info)

        with open(file, 'wb') as fd:
            w.write(fd, self.rows)

    def write(self, file):
        """Write the image to the open file object.

        See `.save()` if you have a filename.

        In general, you can only call this method once;
        after it has been called the first time the PNG image is written,
        the source data will have been streamed, and
        cannot be streamed again.
        """

        w = Writer(**self.info)
        w.write(file, self.rows)


class Reader:
    """
    Pure Python PNG decoder in pure Python.
    """

    def __init__(self, _guess=None, filename=None, file=None, bytes=None):
        """
        The constructor expects exactly one keyword argument.
        If you supply a positional argument instead,
        it will guess the input type.
        Choose from the following keyword arguments:

        filename
          Name of input file (a PNG file).
        file
          A file-like object (object with a read() method).
        bytes
          ``bytes`` or ``bytearray`` with PNG data.

        """
        keywords_supplied = (
            (_guess is not None) +
            (filename is not None) +
            (file is not None) +
            (bytes is not None))
        if keywords_supplied != 1:
            raise TypeError("Reader() takes exactly 1 argument")

        # 026638.python.png.line1328.comment Will be the first 8 bytes, later on.  See validate_signature.
        self.signature = None
        self.transparent = None
        # 026639.python.png.line1331.comment A pair of (len,type) if a chunk has been read but its data and
        # 026640.python.png.line1332.comment checksum have not (in other words the file position is just
        # 026641.python.png.line1333.comment past the 4 bytes that specify the chunk type).
        # 026642.python.png.line1334.comment See preamble method for how this is used.
        self.atchunk = None

        if _guess is not None:
            if isarray(_guess):
                bytes = _guess
            elif isinstance(_guess, str):
                filename = _guess
            elif hasattr(_guess, 'read'):
                file = _guess

        if bytes is not None:
            self.file = io.BytesIO(bytes)
        elif filename is not None:
            self.file = open(filename, "rb")
        elif file is not None:
            self.file = file
        else:
            raise ProtocolError("expecting filename, file or bytes array")

    def chunk(self, lenient=False):
        """
        Read the next PNG chunk from the input file;
        returns a (*type*, *data*) tuple.
        *type* is the chunk's type as a byte string
        (all PNG chunk types are 4 bytes long).
        *data* is the chunk's data content, as a byte string.

        If the optional `lenient` argument evaluates to `True`,
        checksum failures will raise warnings rather than exceptions.
        """

        self.validate_signature()

        # 026643.python.png.line1368.comment http://www.w3.org/TR/PNG/#5Chunk-layout
        if not self.atchunk:
            self.atchunk = self._chunk_len_type()
        if not self.atchunk:
            raise ChunkError("No more chunks.")
        length, type = self.atchunk
        self.atchunk = None

        data = self.file.read(length)
        if len(data) != length:
            raise ChunkError(
                f'Chunk {type} too short for required {length} octets.')
        checksum = self.file.read(4)
        if len(checksum) != 4:
            raise ChunkError(f'Chunk {type} too short for checksum.')
        verify = zlib.crc32(type)
        verify = zlib.crc32(data, verify)
        verify = struct.pack('!I', verify)
        if checksum != verify:
            (a, ) = struct.unpack('!I', checksum)
            (b, ) = struct.unpack('!I', verify)
            message = f"Checksum error in {type.decode('ascii')} chunk: 0x{a:08X} != 0x{b:08X}."
            if lenient:
                warnings.warn(message, RuntimeWarning)
            else:
                raise ChunkError(message)
        return type, data

    def chunks(self):
        """Return an iterator that will yield each chunk as a
        (*chunktype*, *content*) pair.
        """

        while True:
            t, v = self.chunk()
            yield t, v
            if t == b'IEND':
                break

    def undo_filter(self, filter_type, scanline, previous):
        """
        Undo the filter for a scanline.
        `scanline` is a sequence of bytes that
        does not include the initial filter type byte.
        `previous` is decoded previous scanline
        (for straightlaced images this is the previous pixel row,
        but for interlaced images, it is
        the previous scanline in the reduced image,
        which in general is not the previous pixel row in the final image).
        When there is no previous scanline
        (the first row of a straightlaced image,
        or the first row in one of the passes in an interlaced image),
        then this argument should be ``None``.

        The scanline will have the effects of filtering removed;
        the result will be returned as a fresh sequence of bytes.
        """

        # 026644.python.png.line1426.comment :todo: Would it be better to update scanline in place?
        result = scanline

        if filter_type == 0:
            return result

        if filter_type not in (1, 2, 3, 4):
            raise FormatError(
                'Invalid PNG Filter Type.  '
                'See http://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters .')

        # 026645.python.png.line1437.comment Filter unit.  The stride from one pixel to the corresponding
        # 026646.python.png.line1438.comment byte from the previous pixel.  Normally this is the pixel
        # 026647.python.png.line1439.comment size in bytes, but when this is smaller than 1, the previous
        # 026648.python.png.line1440.comment byte is used instead.
        fu = max(1, self.psize)

        # 026649.python.png.line1443.comment For the first line of a pass, synthesize a dummy previous
        # 026650.python.png.line1444.comment line.  An alternative approach would be to observe that on the
        # 026651.python.png.line1445.comment first line 'up' is the same as 'null', 'paeth' is the same
        # 026652.python.png.line1446.comment as 'sub', with only 'average' requiring any special case.
        if not previous:
            previous = bytearray([0] * len(scanline))

        # 026653.python.png.line1450.comment Call appropriate filter algorithm.  Note that 0 has already
        # 026654.python.png.line1451.comment been dealt with.
        fn = (None,
              undo_filter_sub,
              undo_filter_up,
              undo_filter_average,
              undo_filter_paeth)[filter_type]
        fn(fu, scanline, previous, result)
        return result

    def _deinterlace(self, raw):
        """
        Read raw pixel data, undo filters, deinterlace, and flatten.
        Return a single array of values.
        """

        # 026655.python.png.line1466.comment Values per row (of the target image)
        vpr = self.width * self.planes

        # 026656.python.png.line1469.comment Values per image
        vpi = vpr * self.height
        # 026657.python.png.line1471.comment Interleaving writes to the output array randomly
        # 026658.python.png.line1472.comment (well, not quite), so the entire output array must be in memory.
        # 026659.python.png.line1473.comment Make a result array, and make it big enough.
        if self.bitdepth > 8:
            a = array('H', [0] * vpi)
        else:
            a = bytearray([0] * vpi)
        source_offset = 0

        for lines in adam7_generate(self.width, self.height):
            # 026660.python.png.line1481.comment The previous (reconstructed) scanline.
            # 026661.python.png.line1482.comment `None` at the beginning of a pass
            # 026662.python.png.line1483.comment to indicate that there is no previous line.
            recon = None
            for x, y, xstep in lines:
                # 026663.python.png.line1486.comment Pixels per row (reduced pass image)
                ppr = int(math.ceil((self.width - x) / float(xstep)))
                # 026664.python.png.line1488.comment Row size in bytes for this pass.
                row_size = int(math.ceil(self.psize * ppr))

                filter_type = raw[source_offset]
                source_offset += 1
                scanline = raw[source_offset: source_offset + row_size]
                source_offset += row_size
                recon = self.undo_filter(filter_type, scanline, recon)
                # 026665.python.png.line1496.comment Convert so that there is one element per pixel value
                flat = self._bytes_to_values(recon, width=ppr)
                if xstep == 1:
                    assert x == 0
                    offset = y * vpr
                    a[offset: offset + vpr] = flat
                else:
                    offset = y * vpr + x * self.planes
                    end_offset = (y + 1) * vpr
                    skip = self.planes * xstep
                    for i in range(self.planes):
                        a[offset + i: end_offset: skip] = \
                            flat[i:: self.planes]

        return a

    def _iter_bytes_to_values(self, byte_rows):
        """
        Iterator that yields each scanline;
        each scanline being a sequence of values.
        `byte_rows` should be an iterator that yields
        the bytes of each row in turn.
        """

        for row in byte_rows:
            yield self._bytes_to_values(row)

    def _bytes_to_values(self, bs, width=None):
        """Convert a packed row of bytes into a row of values.
        Result will be a freshly allocated object,
        not shared with the argument.
        """

        if self.bitdepth == 8:
            return bytearray(bs)
        if self.bitdepth == 16:
            return array('H',
                         struct.unpack(f'!{(len(bs) // 2)}H' , bs))

        assert self.bitdepth < 8
        if width is None:
            width = self.width
        # 026666.python.png.line1538.comment Samples per byte
        spb = 8 // self.bitdepth
        out = bytearray()
        mask = 2**self.bitdepth - 1
        shifts = [self.bitdepth * i
                  for i in reversed(list(range(spb)))]
        for o in bs:
            out.extend([mask & (o >> i) for i in shifts])
        return out[:width]

    def _iter_straight_packed(self, byte_blocks):
        """Iterator that undoes the effect of filtering;
        yields each row as a sequence of packed bytes.
        Assumes input is straightlaced.
        `byte_blocks` should be an iterable that yields the raw bytes
        in blocks of arbitrary size.
        """

        # 026667.python.png.line1556.comment length of row, in bytes
        rb = self.row_bytes
        a = bytearray()
        # 026668.python.png.line1559.comment The previous (reconstructed) scanline.
        # 026669.python.png.line1560.comment None indicates first line of image.
        recon = None
        for some_bytes in byte_blocks:
            a.extend(some_bytes)
            while len(a) >= rb + 1:
                filter_type = a[0]
                scanline = a[1: rb + 1]
                del a[: rb + 1]
                recon = self.undo_filter(filter_type, scanline, recon)
                yield recon
        if len(a) != 0:
            # 026670.python.png.line1571.comment :file:format We get here with a file format error:
            # 026671.python.png.line1572.comment when the available bytes (after decompressing) do not
            # 026672.python.png.line1573.comment pack into exact rows.
            raise FormatError('Wrong size for decompressed IDAT chunk.')
        assert len(a) == 0

    def validate_signature(self):
        """
        If signature (header) has not been read then read and
        validate it; otherwise do nothing.
        """

        if self.signature:
            return
        self.signature = self.file.read(8)
        if self.signature != signature:
            raise FormatError("PNG file has invalid signature.")

    def preamble(self, lenient=False):
        """
        Extract the image metadata by reading
        the initial part of the PNG file up to
        the start of the ``IDAT`` chunk.
        All the chunks that precede the ``IDAT`` chunk are
        read and either processed for metadata or discarded.

        If the optional `lenient` argument evaluates to `True`,
        checksum failures will raise warnings rather than exceptions.
        """

        self.validate_signature()

        while True:
            if not self.atchunk:
                self.atchunk = self._chunk_len_type()
                if self.atchunk is None:
                    raise FormatError('This PNG file has no IDAT chunks.')
            if self.atchunk[1] == b'IDAT':
                return
            self.process_chunk(lenient=lenient)

    def _chunk_len_type(self):
        """
        Reads just enough of the input to
        determine the next chunk's length and type;
        return a (*length*, *type*) pair where *type* is a byte sequence.
        If there are no more chunks, ``None`` is returned.
        """

        x = self.file.read(8)
        if not x:
            return None
        if len(x) != 8:
            raise FormatError(
                'End of file whilst reading chunk length and type.')
        length, type = struct.unpack('!I4s', x)
        if length > 2 ** 31 - 1:
            raise FormatError(f'Chunk {type} is too large: {length}.')
        # 026673.python.png.line1629.comment Check that all bytes are in valid ASCII range.
        # 026674.python.png.line1630.comment https://www.w3.org/TR/2003/REC-PNG-20031110/#5Chunk-layout
        type_bytes = set(bytearray(type))
        if not(type_bytes <= set(range(65, 91)) | set(range(97, 123))):
            raise FormatError(
                f'Chunk {list(type)} has invalid Chunk Type.')
        return length, type

    def process_chunk(self, lenient=False):
        """
        Process the next chunk and its data.
        This only processes the following chunk types:
        ``IHDR``, ``PLTE``, ``bKGD``, ``tRNS``, ``gAMA``, ``sBIT``, ``pHYs``.
        All other chunk types are ignored.

        If the optional `lenient` argument evaluates to `True`,
        checksum failures will raise warnings rather than exceptions.
        """

        type, data = self.chunk(lenient=lenient)
        method = '_process_' + type.decode('ascii')
        m = getattr(self, method, None)
        if m:
            m(data)

    def _process_IHDR(self, data):
        # 026675.python.png.line1655.comment http://www.w3.org/TR/PNG/#11IHDR
        if len(data) != 13:
            raise FormatError('IHDR chunk has incorrect length.')
        (self.width, self.height, self.bitdepth, self.color_type,
         self.compression, self.filter,
         self.interlace) = struct.unpack("!2I5B", data)

        check_bitdepth_colortype(self.bitdepth, self.color_type)

        if self.compression != 0:
            raise FormatError(
                f"Unknown compression method {self.compression}")
        if self.filter != 0:
            raise FormatError(
                f"Unknown filter method {self.filter},"
                " see http://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters ."
                )
        if self.interlace not in (0, 1):
            raise FormatError(
                f"Unknown interlace method {self.interlace}, see "
                "http://www.w3.org/TR/2003/REC-PNG-20031110/#8InterlaceMethods"
                " .")

        # 026676.python.png.line1678.comment Derived values
        # 026677.python.png.line1679.comment http://www.w3.org/TR/PNG/#6Colour-values
        colormap = bool(self.color_type & 1)
        greyscale = not(self.color_type & 2)
        alpha = bool(self.color_type & 4)
        color_planes = (3, 1)[greyscale or colormap]
        planes = color_planes + alpha

        self.colormap = colormap
        self.greyscale = greyscale
        self.alpha = alpha
        self.color_planes = color_planes
        self.planes = planes
        self.psize = float(self.bitdepth) / float(8) * planes
        if int(self.psize) == self.psize:
            self.psize = int(self.psize)
        self.row_bytes = int(math.ceil(self.width * self.psize))
        # 026678.python.png.line1695.comment Stores PLTE chunk if present, and is used to check
        # 026679.python.png.line1696.comment chunk ordering constraints.
        self.plte = None
        # 026680.python.png.line1698.comment Stores tRNS chunk if present, and is used to check chunk
        # 026681.python.png.line1699.comment ordering constraints.
        self.trns = None
        # 026682.python.png.line1701.comment Stores sBIT chunk if present.
        self.sbit = None

    def _process_PLTE(self, data):
        # 026683.python.png.line1705.comment http://www.w3.org/TR/PNG/#11PLTE
        if self.plte:
            warnings.warn("Multiple PLTE chunks present.")
        self.plte = data
        if len(data) % 3 != 0:
            raise FormatError(
                "PLTE chunk's length should be a multiple of 3.")
        if len(data) > (2 ** self.bitdepth) * 3:
            raise FormatError("PLTE chunk is too long.")
        if len(data) == 0:
            raise FormatError("Empty PLTE is not allowed.")

    def _process_bKGD(self, data):
        try:
            if self.colormap:
                if not self.plte:
                    warnings.warn(
                        "PLTE chunk is required before bKGD chunk.")
                self.background = struct.unpack('B', data)
            else:
                self.background = struct.unpack(f"!{self.color_planes}H",
                                                data)
        except struct.error:
            raise FormatError("bKGD chunk has incorrect length.")

    def _process_tRNS(self, data):
        # 026684.python.png.line1731.comment http://www.w3.org/TR/PNG/#11tRNS
        self.trns = data
        if self.colormap:
            if not self.plte:
                warnings.warn("PLTE chunk is required before tRNS chunk.")
            else:
                if len(data) > len(self.plte) / 3:
                    # 026685.python.png.line1738.comment Was warning, but promoted to Error as it
                    # 026686.python.png.line1739.comment would otherwise cause pain later on.
                    raise FormatError("tRNS chunk is too long.")
        else:
            if self.alpha:
                raise FormatError(
                    f"tRNS chunk is not valid with colour type {self.color_type}.")
            try:
                self.transparent = \
                    struct.unpack(f"!{self.color_planes}H", data)
            except struct.error:
                raise FormatError("tRNS chunk has incorrect length.")

    def _process_gAMA(self, data):
        try:
            self.gamma = struct.unpack("!L", data)[0] / 100000.0
        except struct.error:
            raise FormatError("gAMA chunk has incorrect length.")

    def _process_sBIT(self, data):
        self.sbit = data
        if (self.colormap and len(data) != 3 or
                not self.colormap and len(data) != self.planes):
            raise FormatError("sBIT chunk has incorrect length.")

    def _process_pHYs(self, data):
        # 026687.python.png.line1764.comment http://www.w3.org/TR/PNG/#11pHYs
        self.phys = data
        fmt = "!LLB"
        if len(data) != struct.calcsize(fmt):
            raise FormatError("pHYs chunk has incorrect length.")
        self.x_pixels_per_unit, self.y_pixels_per_unit, unit = \
            struct.unpack(fmt, data)
        self.unit_is_meter = bool(unit)

    def read(self, lenient=False):
        """
        Read the PNG file and decode it.
        Returns (`width`, `height`, `rows`, `info`).

        May use excessive memory.

        `rows` is a sequence of rows;
        each row is a sequence of values.

        If the optional `lenient` argument evaluates to True,
        checksum failures will raise warnings rather than exceptions.
        """

        def iteridat():
            """Iterator that yields all the ``IDAT`` chunks as strings."""
            while True:
                type, data = self.chunk(lenient=lenient)
                if type == b'IEND':
                    # 026688.python.png.line1792.comment http://www.w3.org/TR/PNG/#11IEND
                    break
                if type != b'IDAT':
                    continue
                # 026689.python.png.line1796.comment type == b'IDAT'
                # 026690.python.png.line1797.comment http://www.w3.org/TR/PNG/#11IDAT
                if self.colormap and not self.plte:
                    warnings.warn("PLTE chunk is required before IDAT chunk")
                yield data

        self.preamble(lenient=lenient)
        raw = decompress(iteridat())

        if self.interlace:
            def rows_from_interlace():
                """Yield each row from an interlaced PNG."""
                # 026691.python.png.line1808.comment It's important that this iterator doesn't read
                # 026692.python.png.line1809.comment IDAT chunks until it yields the first row.
                bs = bytearray(itertools.chain(*raw))
                arraycode = 'BH'[self.bitdepth > 8]
                # 026693.python.png.line1812.comment Like :meth:`group` but
                # 026694.python.png.line1813.comment producing an array.array object for each row.
                values = self._deinterlace(bs)
                vpr = self.width * self.planes
                for i in range(0, len(values), vpr):
                    row = array(arraycode, values[i:i+vpr])
                    yield row
            rows = rows_from_interlace()
        else:
            rows = self._iter_bytes_to_values(self._iter_straight_packed(raw))
        info = dict()
        for attr in 'greyscale alpha planes bitdepth interlace'.split():
            info[attr] = getattr(self, attr)
        info['size'] = (self.width, self.height)
        for attr in 'gamma transparent background'.split():
            a = getattr(self, attr, None)
            if a is not None:
                info[attr] = a
        if getattr(self, 'x_pixels_per_unit', None):
            info['physical'] = Resolution(self.x_pixels_per_unit,
                                          self.y_pixels_per_unit,
                                          self.unit_is_meter)
        if self.plte:
            info['palette'] = self.palette()
        return self.width, self.height, rows, info

    def read_flat(self):
        """
        Read a PNG file and decode it into a single array of values.
        Returns (*width*, *height*, *values*, *info*).

        May use excessive memory.

        `values` is a single array.

        The :meth:`read` method is more stream-friendly than this,
        because it returns a sequence of rows.
        """

        x, y, pixel, info = self.read()
        arraycode = 'BH'[info['bitdepth'] > 8]
        pixel = array(arraycode, itertools.chain(*pixel))
        return x, y, pixel, info

    def palette(self, alpha='natural'):
        """
        Returns a palette that is a sequence of 3-tuples or 4-tuples,
        synthesizing it from the ``PLTE`` and ``tRNS`` chunks.
        These chunks should have already been processed (for example,
        by calling the :meth:`preamble` method).
        All the tuples are the same size:
        3-tuples if there is no ``tRNS`` chunk,
        4-tuples when there is a ``tRNS`` chunk.

        Assumes that the image is colour type
        3 and therefore a ``PLTE`` chunk is required.

        If the `alpha` argument is ``'force'`` then an alpha channel is
        always added, forcing the result to be a sequence of 4-tuples.
        """

        if not self.plte:
            raise FormatError(
                "Required PLTE chunk is missing in colour type 3 image.")
        plte = group(array('B', self.plte), 3)
        if self.trns or alpha == 'force':
            trns = array('B', self.trns or [])
            trns.extend([255] * (len(plte) - len(trns)))
            plte = list(map(operator.add, plte, group(trns, 1)))
        return plte

    def asDirect(self):
        """
        Returns the image data as a direct representation of
        an ``x * y * planes`` array.
        This removes the need for callers to deal with
        palettes and transparency themselves.
        Images with a palette (colour type 3) are converted to RGB or RGBA;
        images with transparency (a ``tRNS`` chunk) are converted to
        LA or RGBA as appropriate.
        When returned in this format the pixel values represent
        the colour value directly without needing to refer
        to palettes or transparency information.

        Like the :meth:`read` method this method returns a 4-tuple:

        (*width*, *height*, *rows*, *info*)

        This method normally returns pixel values with
        the bit depth they have in the source image, but
        when the source PNG has an ``sBIT`` chunk it is inspected and
        can reduce the bit depth of the result pixels;
        pixel values will be reduced according to the bit depth
        specified in the ``sBIT`` chunk.
        PNG nerds should note a single result bit depth is
        used for all channels:
        the maximum of the ones specified in the ``sBIT`` chunk.
        An RGB565 image will be rescaled to 6-bit RGB666.

        The *info* dictionary that is returned reflects
        the `direct` format and not the original source image.
        For example, an RGB source image with a ``tRNS`` chunk
        to represent a transparent colour,
        will start with ``planes=3`` and ``alpha=False`` for the
        source image,
        but the *info* dictionary returned by this method
        will have ``planes=4`` and ``alpha=True`` because
        an alpha channel is synthesized and added.

        *rows* is a sequence of rows;
        each row being a sequence of values
        (like the :meth:`read` method).

        All the other aspects of the image data are not changed.
        """

        self.preamble()

        # 026695.python.png.line1930.comment Simple case, no conversion necessary.
        if not self.colormap and not self.trns and not self.sbit:
            return self.read()

        x, y, pixels, info = self.read()

        if self.colormap:
            info['colormap'] = False
            info['alpha'] = bool(self.trns)
            info['bitdepth'] = 8
            info['planes'] = 3 + bool(self.trns)
            plte = self.palette()

            def iterpal(pixels):
                for row in pixels:
                    row = [plte[x] for x in row]
                    yield array('B', itertools.chain(*row))
            pixels = iterpal(pixels)
        elif self.trns:
            # 026696.python.png.line1949.comment It would be nice if there was some reasonable way
            # 026697.python.png.line1950.comment of doing this without generating a whole load of
            # 026698.python.png.line1951.comment intermediate tuples.  But tuples does seem like the
            # 026699.python.png.line1952.comment easiest way, with no other way clearly much simpler or
            # 026700.python.png.line1953.comment much faster.  (Actually, the L to LA conversion could
            # 026701.python.png.line1954.comment perhaps go faster (all those 1-tuples!), but I still
            # 026702.python.png.line1955.comment wonder whether the code proliferation is worth it)
            it = self.transparent
            maxval = 2 ** info['bitdepth'] - 1
            planes = info['planes']
            info['alpha'] = True
            info['planes'] += 1
            typecode = 'BH'[info['bitdepth'] > 8]

            def itertrns(pixels):
                for row in pixels:
                    # 026703.python.png.line1965.comment For each row we group it into pixels, then form a
                    # 026704.python.png.line1966.comment characterisation vector that says whether each
                    # 026705.python.png.line1967.comment pixel is opaque or not.  Then we convert
                    # 026706.python.png.line1968.comment True/False to 0/maxval (by multiplication),
                    # 026707.python.png.line1969.comment and add it as the extra channel.
                    row = group(row, planes)
                    opa = map(it.__ne__, row)
                    opa = map(maxval.__mul__, opa)
                    opa = list(zip(opa))    # convert to 1-tuples
                    yield array(
                        typecode,
                        itertools.chain(*map(operator.add, row, opa)))
            pixels = itertrns(pixels)
        targetbitdepth = None
        if self.sbit:
            sbit = struct.unpack(f'{len(self.sbit)}B', self.sbit)
            targetbitdepth = max(sbit)
            if targetbitdepth > info['bitdepth']:
                raise Error(f'sBIT chunk {sbit!r} exceeds bitdepth {self.bitdepth}')
            if min(sbit) <= 0:
                raise Error(f'sBIT chunk {sbit} has a 0-entry')
        if targetbitdepth:
            shift = info['bitdepth'] - targetbitdepth
            info['bitdepth'] = targetbitdepth

            def itershift(pixels):
                for row in pixels:
                    yield [p >> shift for p in row]
            pixels = itershift(pixels)
        return x, y, pixels, info

    def _as_rescale(self, get, targetbitdepth):
        """Helper used by :meth:`asRGB8` and :meth:`asRGBA8`."""

        width, height, pixels, info = get()
        maxval = 2**info['bitdepth'] - 1
        targetmaxval = 2**targetbitdepth - 1
        factor = float(targetmaxval) / float(maxval)
        info['bitdepth'] = targetbitdepth

        def iterscale():
            for row in pixels:
                yield [int(round(x * factor)) for x in row]
        if maxval == targetmaxval:
            return width, height, pixels, info
        else:
            return width, height, iterscale(), info

    def asRGB8(self):
        """
        Return the image data as an RGB pixels with 8-bits per sample.
        This is like the :meth:`asRGB` method except that
        this method additionally rescales the values so that
        they are all between 0 and 255 (8-bit).
        In the case where the source image has a bit depth < 8
        the transformation preserves all the information;
        where the source image has bit depth > 8, then
        rescaling to 8-bit values loses precision.
        No dithering is performed.
        Like :meth:`asRGB`,
        an alpha channel in the source image will raise an exception.

        This function returns a 4-tuple:
        (*width*, *height*, *rows*, *info*).
        *width*, *height*, *info* are as per the :meth:`read` method.

        *rows* is the pixel data as a sequence of rows.
        """

        return self._as_rescale(self.asRGB, 8)

    def asRGBA8(self):
        """
        Return the image data as RGBA pixels with 8-bits per sample.
        This method is similar to :meth:`asRGB8` and :meth:`asRGBA`:
        The result pixels have an alpha channel, *and*
        values are rescaled to the range 0 to 255.
        The alpha channel is synthesized if necessary
        (with a small speed penalty).
        """

        return self._as_rescale(self.asRGBA, 8)

    def asRGB(self):
        """
        Return image as RGB pixels.
        RGB colour images are passed through unchanged;
        greyscales are expanded into RGB triplets
        (there is a small speed overhead for doing this).

        An alpha channel in the source image will raise an exception.

        The return values are as for the :meth:`read` method except that
        the *info* reflect the returned pixels, not the source image.
        In particular,
        for this method ``info['greyscale']`` will be ``False``.
        """

        width, height, pixels, info = self.asDirect()
        if info['alpha']:
            raise Error("will not convert image with alpha channel to RGB")
        if not info['greyscale']:
            return width, height, pixels, info
        info['greyscale'] = False
        info['planes'] = 3

        if info['bitdepth'] > 8:
            def newarray():
                return array('H', [0])
        else:
            def newarray():
                return bytearray([0])

        def iterrgb():
            for row in pixels:
                a = newarray() * 3 * width
                for i in range(3):
                    a[i::3] = row
                yield a
        return width, height, iterrgb(), info

    def asRGBA(self):
        """
        Return image as RGBA pixels.
        Greyscales are expanded into RGB triplets;
        an alpha channel is synthesized if necessary.
        The return values are as for the :meth:`read` method except that
        the *info* reflect the returned pixels, not the source image.
        In particular, for this method
        ``info['greyscale']`` will be ``False``, and
        ``info['alpha']`` will be ``True``.
        """

        width, height, pixels, info = self.asDirect()
        if info['alpha'] and not info['greyscale']:
            return width, height, pixels, info
        typecode = 'BH'[info['bitdepth'] > 8]
        maxval = 2**info['bitdepth'] - 1
        maxbuffer = struct.pack('=' + typecode, maxval) * 4 * width

        if info['bitdepth'] > 8:
            def newarray():
                return array('H', maxbuffer)
        else:
            def newarray():
                return bytearray(maxbuffer)

        if info['alpha'] and info['greyscale']:
            # 026709.python.png.line2113.comment LA to RGBA
            def convert():
                for row in pixels:
                    # 026710.python.png.line2116.comment Create a fresh target row, then copy L channel
                    # 026711.python.png.line2117.comment into first three target channels, and A channel
                    # 026712.python.png.line2118.comment into fourth channel.
                    a = newarray()
                    convert_la_to_rgba(row, a)
                    yield a
        elif info['greyscale']:
            # 026713.python.png.line2123.comment L to RGBA
            def convert():
                for row in pixels:
                    a = newarray()
                    convert_l_to_rgba(row, a)
                    yield a
        else:
            assert not info['alpha'] and not info['greyscale']
            # 026714.python.png.line2131.comment RGB to RGBA

            def convert():
                for row in pixels:
                    a = newarray()
                    convert_rgb_to_rgba(row, a)
                    yield a
        info['alpha'] = True
        info['greyscale'] = False
        info['planes'] = 4
        return width, height, convert(), info


def decompress(data_blocks):
    """
    `data_blocks` should be an iterable that
    yields the compressed data (from the ``IDAT`` chunks).
    This yields decompressed byte strings.
    """

    # 026715.python.png.line2151.comment Currently, with no max_length parameter to decompress,
    # 026716.python.png.line2152.comment this routine will do one yield per IDAT chunk: Not very
    # 026717.python.png.line2153.comment incremental.
    d = zlib.decompressobj()
    # 026718.python.png.line2155.comment Each IDAT chunk is passed to the decompressor, then any
    # 026719.python.png.line2156.comment remaining state is decompressed out.
    for data in data_blocks:
        # 026720.python.png.line2158.comment :todo: add a max_length argument here to limit output size.
        yield bytearray(d.decompress(data))
    yield bytearray(d.flush())


def check_bitdepth_colortype(bitdepth, colortype):
    """
    Check that `bitdepth` and `colortype` are both valid,
    and specified in a valid combination.
    Returns (None) if valid, raise an Exception if not valid.
    """

    if bitdepth not in (1, 2, 4, 8, 16):
        raise FormatError(f"invalid bit depth {bitdepth}")
    if colortype not in (0, 2, 3, 4, 6):
        raise FormatError(f"invalid colour type {colortype}")
    # 026721.python.png.line2174.comment Check indexed (palettized) images have 8 or fewer bits
    # 026722.python.png.line2175.comment per pixel; check only indexed or greyscale images have
    # 026723.python.png.line2176.comment fewer than 8 bits per pixel.
    if colortype & 1 and bitdepth > 8:
        raise FormatError(
            f"Indexed images (colour type {bitdepth}) cannot"
            f" have bitdepth > 8 (bit depth {colortype})."
            " See http://www.w3.org/TR/2003/REC-PNG-20031110/#table111 ."
            )
    if bitdepth < 8 and colortype not in (0, 3):
        raise FormatError(
            f"Illegal combination of bit depth ({bitdepth})"
            f" and colour type ({colortype})."
            " See http://www.w3.org/TR/2003/REC-PNG-20031110/#table111 .")


def is_natural(x):
    """A non-negative integer."""
    try:
        is_integer = int(x) == x
    except (TypeError, ValueError):
        return False
    return is_integer and x >= 0


def undo_filter_sub(filter_unit, scanline, previous, result):
    """Undo sub filter."""

    ai = 0
    # 026724.python.png.line2203.comment Loops starts at index fu.  Observe that the initial part
    # 026725.python.png.line2204.comment of the result is already filled in correctly with
    # 026726.python.png.line2205.comment scanline.
    for i in range(filter_unit, len(result)):
        x = scanline[i]
        a = result[ai]
        result[i] = (x + a) & 0xff
        ai += 1


def undo_filter_up(filter_unit, scanline, previous, result):
    """Undo up filter."""

    for i in range(len(result)):
        x = scanline[i]
        b = previous[i]
        result[i] = (x + b) & 0xff


def undo_filter_average(filter_unit, scanline, previous, result):
    """Undo up filter."""

    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = 0
        else:
            a = result[ai]
        b = previous[i]
        result[i] = (x + ((a + b) >> 1)) & 0xff
        ai += 1


def undo_filter_paeth(filter_unit, scanline, previous, result):
    """Undo Paeth filter."""

    # 026727.python.png.line2240.comment Also used for ci.
    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = c = 0
        else:
            a = result[ai]
            c = previous[ai]
        b = previous[i]
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            pr = a
        elif pb <= pc:
            pr = b
        else:
            pr = c
        result[i] = (x + pr) & 0xff
        ai += 1


def convert_la_to_rgba(row, result):
    for i in range(3):
        result[i::4] = row[0::2]
    result[3::4] = row[1::2]


def convert_l_to_rgba(row, result):
    """
    Convert a grayscale image to RGBA.
    This method assumes the alpha channel in result is
    already correctly initialized.
    """
    for i in range(3):
        result[i::4] = row


def convert_rgb_to_rgba(row, result):
    """
    Convert an RGB image to RGBA.
    This method assumes the alpha channel in result is
    already correctly initialized.
    """
    for i in range(3):
        result[i::4] = row[i::3]


# 026728.python.png.line2290.comment Only reason to include this in this module is that
# 026729.python.png.line2291.comment several utilities need it, and it is small.
def binary_stdin():
    """
    A sys.stdin that returns bytes.
    """

    return sys.stdin.buffer


def binary_stdout():
    """
    A sys.stdout that accepts bytes.
    """

    stdout = sys.stdout.buffer

    # 026730.python.png.line2307.comment On Windows the C runtime file orientation needs changing.
    if sys.platform == "win32":
        import msvcrt
        import os
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    return stdout


def cli_open(path):
    if path == "-":
        return binary_stdin()
    return open(path, "rb")


def main(argv):
    """
    Run command line PNG.
    """
    print("What should the command line tool do?", file=sys.stderr)


if __name__ == '__main__':
    try:
        main(sys.argv)
    except Error as e:
        print(e, file=sys.stderr)
