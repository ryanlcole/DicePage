# 041626.python.automain.line1.comment Copyright 2014-2015 Nathan West
# 041627.python.automain.line2.comment
# 041628.python.automain.line3.comment This file is part of autocommand.
# 041629.python.automain.line4.comment
# 041630.python.automain.line5.comment autocommand is free software: you can redistribute it and/or modify
# 041631.python.automain.line6.comment it under the terms of the GNU Lesser General Public License as published by
# 041632.python.automain.line7.comment the Free Software Foundation, either version 3 of the License, or
# 041633.python.automain.line8.comment (at your option) any later version.
# 041634.python.automain.line9.comment
# 041635.python.automain.line10.comment autocommand is distributed in the hope that it will be useful,
# 041636.python.automain.line11.comment but WITHOUT ANY WARRANTY; without even the implied warranty of
# 041637.python.automain.line12.comment MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 041638.python.automain.line13.comment GNU Lesser General Public License for more details.
# 041639.python.automain.line14.comment
# 041640.python.automain.line15.comment You should have received a copy of the GNU Lesser General Public License
# 041641.python.automain.line16.comment along with autocommand.  If not, see <http://www.gnu.org/licenses/>.

import sys
from .errors import AutocommandError


class AutomainRequiresModuleError(AutocommandError, TypeError):
    pass


def automain(module, *, args=(), kwargs=None):
    '''
    This decorator automatically invokes a function if the module is being run
    as the "__main__" module. Optionally, provide args or kwargs with which to
    call the function. If `module` is "__main__", the function is called, and
    the program is `sys.exit`ed with the return value. You can also pass `True`
    to cause the function to be called unconditionally. If the function is not
    called, it is returned unchanged by the decorator.

    Usage:

    @automain(__name__)  # Pass __name__ to check __name__=="__main__"
    def main():
        ...

    If __name__ is "__main__" here, the main function is called, and then
    sys.exit called with the return value.
    '''

    # 041642.python.automain.line45.comment Check that @automain(...) was called, rather than @automain
    if callable(module):
        raise AutomainRequiresModuleError(module)

    if module == '__main__' or module is True:
        if kwargs is None:
            kwargs = {}

        # 041643.python.automain.line53.comment Use a function definition instead of a lambda for a neater traceback
        def automain_decorator(main):
            sys.exit(main(*args, **kwargs))

        return automain_decorator
    else:
        return lambda main: main
