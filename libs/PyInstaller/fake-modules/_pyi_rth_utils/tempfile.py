# 002935.python.tempfile.line1.comment -----------------------------------------------------------------------------
# 002936.python.tempfile.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 002937.python.tempfile.line3.comment
# 002938.python.tempfile.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 002939.python.tempfile.line5.comment you may not use this file except in compliance with the License.
# 002940.python.tempfile.line6.comment
# 002941.python.tempfile.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002942.python.tempfile.line8.comment
# 002943.python.tempfile.line9.comment SPDX-License-Identifier: Apache-2.0
# 002944.python.tempfile.line10.comment -----------------------------------------------------------------------------

import os
import sys
import errno
import tempfile

# 002945.python.tempfile.line17.comment Helper for creating temporary directories with access restricted to the user running the process.
# 002946.python.tempfile.line18.comment On POSIX systems, this is already achieved by `tempfile.mkdtemp`, which uses 0o700 permissions mask.
# 002947.python.tempfile.line19.comment On Windows, however, the POSIX permissions semantics have no effect, and we need to provide our own implementation
# 002948.python.tempfile.line20.comment that restricts the access by passing appropriate security attributes to the `CreateDirectory` function.

if os.name == 'nt':
    from . import _win32

    def secure_mkdtemp(suffix=None, prefix=None, dir=None):
        """
        Windows-specific replacement for `tempfile.mkdtemp` that restricts access to the user running the process.
        Based on `mkdtemp` implementation from python 3.11 stdlib.
        """

        prefix, suffix, dir, output_type = tempfile._sanitize_params(prefix, suffix, dir)

        names = tempfile._get_candidate_names()
        if output_type is bytes:
            names = map(os.fsencode, names)

        for seq in range(tempfile.TMP_MAX):
            name = next(names)
            file = os.path.join(dir, prefix + name + suffix)
            sys.audit("tempfile.mkdtemp", file)
            try:
                _win32.secure_mkdir(file)
            except FileExistsError:
                continue  # try again
            except PermissionError:
                # 002950.python.tempfile.line46.comment This exception is thrown when a directory with the chosen name already exists on windows.
                if (os.name == 'nt' and os.path.isdir(dir) and os.access(dir, os.W_OK)):
                    continue
                else:
                    raise
            return file

        raise FileExistsError(errno.EEXIST, "No usable temporary directory name found")

else:
    secure_mkdtemp = tempfile.mkdtemp
