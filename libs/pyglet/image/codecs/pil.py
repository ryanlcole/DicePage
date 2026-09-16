import os.path

from pyglet.image import *
from pyglet.image.codecs import *

from PIL import Image


class PILImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        # 030369.python.pil.line11.comment Only most common ones shown here
        return ['.bmp', '.cur', '.gif', '.ico', '.jpg', '.jpeg', '.pcx', '.png',
                '.tga', '.tif', '.tiff', '.xbm', '.xpm']

    # 030370.python.pil.line15.comment def get_animation_file_extensions(self):
    # 030371.python.pil.line16.comment return ['.gif', '.ani']

    def decode(self, filename, file):
        if not file:
            file = open(filename, 'rb')

        try:
            image = Image.open(file)
        except Exception as e:
            raise ImageDecodeException('PIL cannot read %r: %s' % (filename or file, e))

        try:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            raise ImageDecodeException('PIL failed to transpose %r: %s' % (filename or file, e))

        # 030372.python.pil.line32.comment Convert bitmap and palette images to component
        if image.mode in ('1', 'P'):
            image = image.convert()

        if image.mode not in ('L', 'LA', 'RGB', 'RGBA'):
            raise ImageDecodeException('Unsupported mode "%s"' % image.mode)
        width, height = image.size

        return ImageData(width, height, image.mode, image.tobytes())


class PILImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        # 030373.python.pil.line45.comment Most common only
        return ['.bmp', '.eps', '.gif', '.jpg', '.jpeg',
                '.pcx', '.png', '.ppm', '.tiff', '.xbm']

    def encode(self, image, filename, file):
        # 030374.python.pil.line50.comment File format is guessed from filename extension, otherwise defaults to PNG.
        pil_format = (filename and os.path.splitext(filename)[1][1:]) or 'png'

        if pil_format.lower() == 'jpg':
            pil_format = 'JPEG'

        image = image.get_image_data()
        fmt = image.format
        if fmt != 'RGB':
            # 030375.python.pil.line59.comment Only save in RGB or RGBA formats.
            fmt = 'RGBA'
        pitch = -(image.width * len(fmt))

        # 030376.python.pil.line63.comment fromstring is deprecated, replaced by frombytes in Pillow (PIL fork)
        # 030377.python.pil.line64.comment (1.1.7) PIL still uses it
        try:
            image_from_fn = getattr(Image, "frombytes")
        except AttributeError:
            image_from_fn = getattr(Image, "fromstring")
        pil_image = image_from_fn(fmt, (image.width, image.height), image.get_data(fmt, pitch))

        try:
            pil_image.save(file, pil_format)
        except Exception as e:
            raise ImageEncodeException(e)


def get_decoders():
    return [PILImageDecoder()]


def get_encoders():
    return [PILImageEncoder()]
