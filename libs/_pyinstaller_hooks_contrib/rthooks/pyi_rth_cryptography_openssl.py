# 011488.python.pyi_rth_cryptography_openssl.line1.comment -----------------------------------------------------------------------------
# 011489.python.pyi_rth_cryptography_openssl.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 011490.python.pyi_rth_cryptography_openssl.line3.comment
# 011491.python.pyi_rth_cryptography_openssl.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011492.python.pyi_rth_cryptography_openssl.line5.comment
# 011493.python.pyi_rth_cryptography_openssl.line6.comment The full license is available in LICENSE, distributed with
# 011494.python.pyi_rth_cryptography_openssl.line7.comment this software.
# 011495.python.pyi_rth_cryptography_openssl.line8.comment
# 011496.python.pyi_rth_cryptography_openssl.line9.comment SPDX-License-Identifier: Apache-2.0
# 011497.python.pyi_rth_cryptography_openssl.line10.comment -----------------------------------------------------------------------------

import os
import sys

# 011498.python.pyi_rth_cryptography_openssl.line15.comment If we collected OpenSSL modules into `ossl-modules` directory, override the OpenSSL search path by setting the
# 011499.python.pyi_rth_cryptography_openssl.line16.comment `OPENSSL_MODULES` environment variable.
_ossl_modules_dir = os.path.join(sys._MEIPASS, 'ossl-modules')
if os.path.isdir(_ossl_modules_dir):
    os.environ['OPENSSL_MODULES'] = _ossl_modules_dir
del _ossl_modules_dir
