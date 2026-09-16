# 044280.python.init.line1.comment mypy: disable_error_code=call-overload
# 044281.python.init.line2.comment pyright: reportCallIssue=false, reportArgumentType=false
# 044282.python.init.line3.comment Can't disable on the exact line because distutils doesn't exists on Python 3.12
# 044283.python.init.line4.comment and type-checkers aren't aware of distutils_hack,
# 044284.python.init.line5.comment causing distutils.command.bdist.bdist.format_commands to be Any.

import sys

from distutils.command.bdist import bdist

if 'egg' not in bdist.format_commands:
    try:
        # 044285.python.init.line13.comment format_commands is a dict in vendored distutils
        # 044286.python.init.line14.comment It used to be a list in older (stdlib) distutils
        # 044287.python.init.line15.comment We support both for backwards compatibility
        bdist.format_commands['egg'] = ('bdist_egg', "Python .egg file")
    except TypeError:
        bdist.format_command['egg'] = ('bdist_egg', "Python .egg file")
        bdist.format_commands.append('egg')

del bdist, sys
