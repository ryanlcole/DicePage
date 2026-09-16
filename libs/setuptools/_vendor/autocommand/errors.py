# 041699.python.errors.line1.comment Copyright 2014-2016 Nathan West
# 041700.python.errors.line2.comment
# 041701.python.errors.line3.comment This file is part of autocommand.
# 041702.python.errors.line4.comment
# 041703.python.errors.line5.comment autocommand is free software: you can redistribute it and/or modify
# 041704.python.errors.line6.comment it under the terms of the GNU Lesser General Public License as published by
# 041705.python.errors.line7.comment the Free Software Foundation, either version 3 of the License, or
# 041706.python.errors.line8.comment (at your option) any later version.
# 041707.python.errors.line9.comment
# 041708.python.errors.line10.comment autocommand is distributed in the hope that it will be useful,
# 041709.python.errors.line11.comment but WITHOUT ANY WARRANTY; without even the implied warranty of
# 041710.python.errors.line12.comment MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 041711.python.errors.line13.comment GNU Lesser General Public License for more details.
# 041712.python.errors.line14.comment
# 041713.python.errors.line15.comment You should have received a copy of the GNU Lesser General Public License
# 041714.python.errors.line16.comment along with autocommand.  If not, see <http://www.gnu.org/licenses/>.


class AutocommandError(Exception):
    '''Base class for autocommand exceptions'''
    pass

# 041715.python.errors.line23.comment Individual modules will define errors specific to that module.
