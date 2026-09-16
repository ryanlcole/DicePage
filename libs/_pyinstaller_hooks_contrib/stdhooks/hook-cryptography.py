# 012648.python.hook-cryptography.line1.comment ------------------------------------------------------------------
# 012649.python.hook-cryptography.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012650.python.hook-cryptography.line3.comment
# 012651.python.hook-cryptography.line4.comment This file is distributed under the terms of the GNU General Public
# 012652.python.hook-cryptography.line5.comment License (version 2.0 or later).
# 012653.python.hook-cryptography.line6.comment
# 012654.python.hook-cryptography.line7.comment The full license is available in LICENSE, distributed with
# 012655.python.hook-cryptography.line8.comment this software.
# 012656.python.hook-cryptography.line9.comment
# 012657.python.hook-cryptography.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012658.python.hook-cryptography.line11.comment ------------------------------------------------------------------
"""
Hook for cryptography module from the Python Cryptography Authority.
"""

import os
import glob
import pathlib

from PyInstaller import compat
from PyInstaller import isolated
from PyInstaller.utils.hooks import (
    collect_submodules,
    copy_metadata,
    get_module_file_attribute,
    is_module_satisfies,
    logger,
)

# 012659.python.hook-cryptography.line30.comment get the package data so we can load the backends
datas = copy_metadata('cryptography')

# 012660.python.hook-cryptography.line33.comment Add the backends as hidden imports
hiddenimports = collect_submodules('cryptography.hazmat.backends')

# 012661.python.hook-cryptography.line36.comment Add the OpenSSL FFI binding modules as hidden imports
hiddenimports += collect_submodules('cryptography.hazmat.bindings.openssl') + ['_cffi_backend']


# 012662.python.hook-cryptography.line40.comment Include the cffi extensions as binaries in a subfolder named like the package.
# 012663.python.hook-cryptography.line41.comment The cffi verifier expects to find them inside the package directory for
# 012664.python.hook-cryptography.line42.comment the main module. We cannot use hiddenimports because that would add the modules
# 012665.python.hook-cryptography.line43.comment outside the package.
# 012666.python.hook-cryptography.line44.comment NOTE: this is not true anymore with PyInstaller >= 6.0, but we keep it like this for compatibility with 5.x series.
binaries = []
cryptography_dir = os.path.dirname(get_module_file_attribute('cryptography'))
for ext in compat.EXTENSION_SUFFIXES:
    ffimods = glob.glob(os.path.join(cryptography_dir, '*_cffi_*%s*' % ext))
    for f in ffimods:
        binaries.append((f, 'cryptography'))


# 012667.python.hook-cryptography.line53.comment Check if `cryptography` is dynamically linked against OpenSSL >= 3.0.0. In that case, we might need to collect
# 012668.python.hook-cryptography.line54.comment external OpenSSL modules, if OpenSSL was built with modules support. It seems the best indication of this is the
# 012669.python.hook-cryptography.line55.comment presence of `ossl-modules` directory next to the OpenSSL shared library.
# 012670.python.hook-cryptography.line56.comment
# 012671.python.hook-cryptography.line57.comment NOTE: PyPI wheels ship with extensions statically linked against OpenSSL, so this is mostly catering alternative
# 012672.python.hook-cryptography.line58.comment installation methods (Anaconda on all OSes, Homebrew on macOS, various linux distributions).
try:
    @isolated.decorate
    def _check_cryptography_openssl3():
        # 012673.python.hook-cryptography.line62.comment Check if OpenSSL 3 is used.
        from cryptography.hazmat.backends.openssl.backend import backend
        openssl_version = backend.openssl_version_number()
        if openssl_version < 0x30000000:
            return False, None

        # 012674.python.hook-cryptography.line68.comment Obtain path to the bindings module for binary dependency analysis. Under older versions of cryptography,
        # 012675.python.hook-cryptography.line69.comment this was a separate `_openssl` module; in contemporary versions, it is `_rust` module.
        try:
            import cryptography.hazmat.bindings._openssl as bindings_module
        except ImportError:
            import cryptography.hazmat.bindings._rust as bindings_module

        return True, str(bindings_module.__file__)

    uses_openssl3, bindings_module = _check_cryptography_openssl3()
except Exception:
    logger.warning(
        "hook-cryptography: failed to determine whether cryptography is using OpenSSL >= 3.0.0", exc_info=True
    )
    uses_openssl3, bindings_module = False, None

if uses_openssl3:
    # 012676.python.hook-cryptography.line85.comment Determine location of OpenSSL shared library, provided that extension module is dynamically linked against it.
    # 012677.python.hook-cryptography.line86.comment This requires the new PyInstaller.bindepend API from PyInstaller >= 6.0.
    openssl_lib = None
    if is_module_satisfies("PyInstaller >= 6.0"):
        from PyInstaller.depend import bindepend

        if compat.is_win:
            SSL_LIB_NAME = 'libssl-3-x64.dll' if compat.is_64bits else 'libssl-3.dll'
        elif compat.is_darwin:
            SSL_LIB_NAME = 'libssl.3.dylib'
        else:
            SSL_LIB_NAME = 'libssl.so.3'

        linked_libs = bindepend.get_imports(bindings_module)
        openssl_lib = [
            # 012678.python.hook-cryptography.line100.comment Compare the basename of lib_name, because lib_fullpath is None if we fail to resolve the library.
            lib_fullpath for lib_name, lib_fullpath in linked_libs if os.path.basename(lib_name) == SSL_LIB_NAME
        ]
        openssl_lib = openssl_lib[0] if openssl_lib else None
    else:
        logger.warning(
            "hook-cryptography: full support for cryptography + OpenSSL >= 3.0.0 requires PyInstaller >= 6.0"
        )

    # 012679.python.hook-cryptography.line109.comment Check for presence of ossl-modules directory next to the OpenSSL shared library.
    if openssl_lib:
        logger.info("hook-cryptography: cryptography uses dynamically-linked OpenSSL: %r", openssl_lib)

        openssl_lib_dir = pathlib.Path(openssl_lib).parent

        # 012680.python.hook-cryptography.line115.comment Collect whole ossl-modules directory, if it exists.
        ossl_modules_dir = openssl_lib_dir / 'ossl-modules'

        # 012681.python.hook-cryptography.line118.comment Msys2/MinGW installations on Windows put the shared library into `bin` directory, but the modules are
        # 012682.python.hook-cryptography.line119.comment located in `lib` directory. Account for that possibility.
        if not ossl_modules_dir.is_dir() and openssl_lib_dir.name == 'bin':
            ossl_modules_dir = openssl_lib_dir.parent / 'lib' / 'ossl-modules'

        # 012683.python.hook-cryptography.line123.comment On Alpine linux, the true location of shared library is /lib directory, but the modules' directory is located
        # 012684.python.hook-cryptography.line124.comment in /usr/lib instead. Account for that possibility.
        if not ossl_modules_dir.is_dir() and openssl_lib_dir == pathlib.Path('/lib'):
            ossl_modules_dir = pathlib.Path('/usr/lib/ossl-modules')

        if ossl_modules_dir.is_dir():
            logger.debug("hook-cryptography: collecting OpenSSL modules directory: %r", str(ossl_modules_dir))
            binaries.append((str(ossl_modules_dir), 'ossl-modules'))
    else:
        logger.info("hook-cryptography: cryptography does not seem to be using dynamically linked OpenSSL.")
