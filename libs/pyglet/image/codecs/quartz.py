from ctypes import c_void_p, c_ubyte

from pyglet.image import ImageData, Animation, AnimationFrame
from pyglet.image.codecs import *

from pyglet.libs.darwin.cocoapy import cf, quartz, NSMakeRect
from pyglet.libs.darwin.cocoapy import cfnumber_to_number
from pyglet.libs.darwin.cocoapy import kCGImageAlphaPremultipliedLast
from pyglet.libs.darwin.cocoapy import kCGImagePropertyGIFDictionary
from pyglet.libs.darwin.cocoapy import kCGImagePropertyGIFDelayTime


class QuartzImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        # 030378.python.quartz.line15.comment Quartz can actually decode many more formats, but these are the most common.
        return [ '.bmp', '.cur', '.gif', '.ico', '.jp2', '.jpg', '.jpeg',
                 '.pcx', '.png', '.tga', '.tif', '.tiff', '.xbm', '.xpm' ]

    def get_animation_file_extensions(self):
        return ['.gif']

    def _get_pyglet_ImageData_from_source_at_index(self, sourceRef, index):
        imageRef = c_void_p(quartz.CGImageSourceCreateImageAtIndex(sourceRef, index, None))

        # 030379.python.quartz.line25.comment Regardless of the internal format of the image (L, LA, RGB, RGBA, etc)
        # 030380.python.quartz.line26.comment we just automatically convert everything to an RGBA format.
        format = 'RGBA'
        rgbColorSpace = c_void_p(quartz.CGColorSpaceCreateDeviceRGB())
        bitsPerComponent = 8
        width = quartz.CGImageGetWidth(imageRef)
        height = quartz.CGImageGetHeight(imageRef)
        bytesPerRow = 4 * width

        # 030381.python.quartz.line34.comment Create a buffer to store the RGBA formatted data.
        bufferSize = height * bytesPerRow
        buffer = (c_ubyte * bufferSize)()

        # 030382.python.quartz.line38.comment Create a bitmap context for the RGBA formatted data.
        # 030383.python.quartz.line39.comment Note that premultiplied alpha is required:
        # 030384.python.quartz.line40.comment http://developer.apple.com/library/mac/#qa/qa1037/_index.html
        bitmap = c_void_p(quartz.CGBitmapContextCreate(buffer,
                                                       width, height,
                                                       bitsPerComponent,
                                                       bytesPerRow,
                                                       rgbColorSpace,
                                                       kCGImageAlphaPremultipliedLast))

        # 030385.python.quartz.line48.comment Write the image data into the bitmap.
        quartz.CGContextDrawImage(bitmap, NSMakeRect(0,0,width,height), imageRef)

        quartz.CGImageRelease(imageRef)
        quartz.CGContextRelease(bitmap)
        quartz.CGColorSpaceRelease(rgbColorSpace)

        pitch = bytesPerRow
        return ImageData(width, height, format, buffer, -pitch)

    def decode(self, filename, file):
        if not file:
            file = open(filename, 'rb')
        file_bytes = file.read()
        data = c_void_p(cf.CFDataCreate(None, file_bytes, len(file_bytes)))
        # 030386.python.quartz.line63.comment Second argument is an options dictionary.  It might be a good idea to provide
        # 030387.python.quartz.line64.comment a value for kCGImageSourceTypeIdentifierHint here using filename extension.
        sourceRef = c_void_p(quartz.CGImageSourceCreateWithData(data, None))
        image = self._get_pyglet_ImageData_from_source_at_index(sourceRef, 0)

        cf.CFRelease(data)
        cf.CFRelease(sourceRef)

        return image

    def decode_animation(self, filename, file):
        if not file:
            file = open(filename, 'rb')
        # 030388.python.quartz.line76.comment If file is not an animated GIF, it will be loaded as a single-frame animation.
        file_bytes = file.read()
        data = c_void_p(cf.CFDataCreate(None, file_bytes, len(file_bytes)))
        sourceRef = c_void_p(quartz.CGImageSourceCreateWithData(data, None))

        # 030389.python.quartz.line81.comment Get number of frames in the animation.
        count = quartz.CGImageSourceGetCount(sourceRef)

        frames = []

        for index in range(count):
            # 030390.python.quartz.line87.comment Try to determine frame duration from GIF properties dictionary.
            duration = 0.1  # default duration if none found
            props = c_void_p(quartz.CGImageSourceCopyPropertiesAtIndex(sourceRef, index, None))
            if cf.CFDictionaryContainsKey(props, kCGImagePropertyGIFDictionary):
                gif_props = c_void_p(cf.CFDictionaryGetValue(props, kCGImagePropertyGIFDictionary))
                if cf.CFDictionaryContainsKey(gif_props, kCGImagePropertyGIFDelayTime):
                    duration = cfnumber_to_number(c_void_p(cf.CFDictionaryGetValue(gif_props, kCGImagePropertyGIFDelayTime)))

            cf.CFRelease(props)
            image = self._get_pyglet_ImageData_from_source_at_index(sourceRef, index)
            frames.append( AnimationFrame(image, duration) )

        cf.CFRelease(data)
        cf.CFRelease(sourceRef)

        return Animation(frames)


def get_decoders():
    return [ QuartzImageDecoder() ]

def get_encoders():
    return []
