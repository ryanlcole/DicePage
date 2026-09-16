# 041597.python.autocommand.line1.comment Copyright 2014-2015 Nathan West
# 041598.python.autocommand.line2.comment
# 041599.python.autocommand.line3.comment This file is part of autocommand.
# 041600.python.autocommand.line4.comment
# 041601.python.autocommand.line5.comment autocommand is free software: you can redistribute it and/or modify
# 041602.python.autocommand.line6.comment it under the terms of the GNU Lesser General Public License as published by
# 041603.python.autocommand.line7.comment the Free Software Foundation, either version 3 of the License, or
# 041604.python.autocommand.line8.comment (at your option) any later version.
# 041605.python.autocommand.line9.comment
# 041606.python.autocommand.line10.comment autocommand is distributed in the hope that it will be useful,
# 041607.python.autocommand.line11.comment but WITHOUT ANY WARRANTY; without even the implied warranty of
# 041608.python.autocommand.line12.comment MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 041609.python.autocommand.line13.comment GNU Lesser General Public License for more details.
# 041610.python.autocommand.line14.comment
# 041611.python.autocommand.line15.comment You should have received a copy of the GNU Lesser General Public License
# 041612.python.autocommand.line16.comment along with autocommand.  If not, see <http://www.gnu.org/licenses/>.

from .autoparse import autoparse
from .automain import automain
try:
    from .autoasync import autoasync
except ImportError:  # pragma: no cover
    pass


def autocommand(
        module, *,
        description=None,
        epilog=None,
        add_nos=False,
        parser=None,
        loop=None,
        forever=False,
        pass_loop=False):

    if callable(module):
        raise TypeError('autocommand requires a module name argument')

    def autocommand_decorator(func):
        # 041614.python.autocommand.line40.comment Step 1: if requested, run it all in an asyncio event loop. autoasync
        # 041615.python.autocommand.line41.comment patches the __signature__ of the decorated function, so that in the
        # 041616.python.autocommand.line42.comment event that pass_loop is True, the `loop` parameter of the original
        # 041617.python.autocommand.line43.comment function will *not* be interpreted as a command-line argument by
        # 041618.python.autocommand.line44.comment autoparse
        if loop is not None or forever or pass_loop:
            func = autoasync(
                func,
                loop=None if loop is True else loop,
                pass_loop=pass_loop,
                forever=forever)

        # 041619.python.autocommand.line52.comment Step 2: create parser. We do this second so that the arguments are
        # 041620.python.autocommand.line53.comment parsed and passed *before* entering the asyncio event loop, if it
        # 041621.python.autocommand.line54.comment exists. This simplifies the stack trace and ensures errors are
        # 041622.python.autocommand.line55.comment reported earlier. It also ensures that errors raised during parsing &
        # 041623.python.autocommand.line56.comment passing are still raised if `forever` is True.
        func = autoparse(
            func,
            description=description,
            epilog=epilog,
            add_nos=add_nos,
            parser=parser)

        # 041624.python.autocommand.line64.comment Step 3: call the function automatically if __name__ == '__main__' (or
        # 041625.python.autocommand.line65.comment if True was provided)
        func = automain(module)(func)

        return func

    return autocommand_decorator
