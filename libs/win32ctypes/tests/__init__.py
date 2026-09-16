# 052318.python.init.line1.comment
# 052319.python.init.line2.comment (C) Copyright 2014 Enthought, Inc., Austin, TX
# 052320.python.init.line3.comment All right reserved.
# 052321.python.init.line4.comment
# 052322.python.init.line5.comment This file is open source software distributed according to the terms in
# 052323.python.init.line6.comment LICENSE.txt
# 052324.python.init.line7.comment
import os

if 'SHOW_TEST_ENV' in os.environ:
    import sys
    from win32ctypes.core import _backend
    is_64bits = sys.maxsize > 2**32
    print('=' * 30, file=sys.stderr)
    print(
        'Running on python: {} {}'.format(
            sys.version, '64bit' if is_64bits else '32bit'),
        file=sys.stderr)
    print('The executable is: {}'.format(sys.executable), file=sys.stderr)
    print('Using the {} backend'.format(_backend), file=sys.stderr)
    print('=' * 30, file=sys.stderr, flush=True)
