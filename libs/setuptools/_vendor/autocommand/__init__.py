# 041544.python.init.line1.comment Copyright 2014-2016 Nathan West
# 041545.python.init.line2.comment
# 041546.python.init.line3.comment This file is part of autocommand.
# 041547.python.init.line4.comment
# 041548.python.init.line5.comment autocommand is free software: you can redistribute it and/or modify
# 041549.python.init.line6.comment it under the terms of the GNU Lesser General Public License as published by
# 041550.python.init.line7.comment the Free Software Foundation, either version 3 of the License, or
# 041551.python.init.line8.comment (at your option) any later version.
# 041552.python.init.line9.comment
# 041553.python.init.line10.comment autocommand is distributed in the hope that it will be useful,
# 041554.python.init.line11.comment but WITHOUT ANY WARRANTY; without even the implied warranty of
# 041555.python.init.line12.comment MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 041556.python.init.line13.comment GNU Lesser General Public License for more details.
# 041557.python.init.line14.comment
# 041558.python.init.line15.comment You should have received a copy of the GNU Lesser General Public License
# 041559.python.init.line16.comment along with autocommand.  If not, see <http://www.gnu.org/licenses/>.

# 041560.python.init.line18.comment flake8 flags all these imports as unused, hence the NOQAs everywhere.

from .automain import automain  # NOQA
from .autoparse import autoparse, smart_open  # NOQA
from .autocommand import autocommand  # NOQA

try:
    from .autoasync import autoasync  # NOQA
except ImportError:  # pragma: no cover
    pass
