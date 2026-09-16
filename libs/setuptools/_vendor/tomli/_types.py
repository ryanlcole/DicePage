# 043376.python.types.line1.comment SPDX-License-Identifier: MIT
# 043377.python.types.line2.comment SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# 043378.python.types.line3.comment Licensed to PSF under a Contributor Agreement.

from typing import Any, Callable, Tuple

# 043379.python.types.line7.comment Type annotations
ParseFloat = Callable[[str], Any]
Key = Tuple[str, ...]
Pos = int
