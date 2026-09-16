# 001887.python.configure.line1.comment -----------------------------------------------------------------------------
# 001888.python.configure.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 001889.python.configure.line3.comment
# 001890.python.configure.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 001891.python.configure.line5.comment or later) with exception for distributing the bootloader.
# 001892.python.configure.line6.comment
# 001893.python.configure.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 001894.python.configure.line8.comment
# 001895.python.configure.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 001896.python.configure.line10.comment -----------------------------------------------------------------------------
"""
Configure PyInstaller for the current Python installation.
"""

import os
import subprocess

from PyInstaller import compat
from PyInstaller import log as logging

logger = logging.getLogger(__name__)


def _check_upx_availability(upx_dir):
    logger.debug('Testing UPX availability ...')

    upx_exe = "upx"
    if upx_dir:
        upx_exe = os.path.normpath(os.path.join(upx_dir, upx_exe))

    # 001897.python.configure.line31.comment Check if we can call `upx -V`.
    try:
        output = subprocess.check_output(
            [upx_exe, '-V'],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            encoding='utf-8',
        )
    except Exception:
        logger.debug('UPX is not available.')
        return False

    # 001898.python.configure.line43.comment Read the first line to display version string
    try:
        version_string = output.splitlines()[0]
    except IndexError:
        version_string = 'version string unavailable'

    logger.debug('UPX is available: %s', version_string)
    return True


def _get_pyinstaller_cache_dir():
    old_cache_dir = None
    if compat.getenv('PYINSTALLER_CONFIG_DIR'):
        cache_dir = compat.getenv('PYINSTALLER_CONFIG_DIR')
    elif compat.is_win:
        cache_dir = compat.getenv('LOCALAPPDATA')
        if not cache_dir:
            cache_dir = os.path.expanduser('~\\Application Data')
    elif compat.is_darwin:
        cache_dir = os.path.expanduser('~/Library/Application Support')
    else:
        # 001899.python.configure.line64.comment According to XDG specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
        old_cache_dir = compat.getenv('XDG_DATA_HOME')
        if not old_cache_dir:
            old_cache_dir = os.path.expanduser('~/.local/share')
        cache_dir = compat.getenv('XDG_CACHE_HOME')
        if not cache_dir:
            cache_dir = os.path.expanduser('~/.cache')
    cache_dir = os.path.join(cache_dir, 'pyinstaller')
    # 001900.python.configure.line72.comment Move old cache-dir, if any, to new location.
    if old_cache_dir and not os.path.exists(cache_dir):
        old_cache_dir = os.path.join(old_cache_dir, 'pyinstaller')
        if os.path.exists(old_cache_dir):
            parent_dir = os.path.dirname(cache_dir)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            os.rename(old_cache_dir, cache_dir)
    return cache_dir


def get_config(upx_dir=None):
    config = {}

    config['cachedir'] = _get_pyinstaller_cache_dir()
    config['upx_dir'] = upx_dir

    # 001901.python.configure.line89.comment Disable UPX on non-Windows. Using UPX (3.96) on modern Linux shared libraries (for example, the python3.x.so
    # 001902.python.configure.line90.comment shared library) seems to result in segmentation fault when they are dlopen'd. This happens in recent versions
    # 001903.python.configure.line91.comment of Fedora and Ubuntu linux, as well as in Alpine containers. On macOS, UPX (3.96) fails with
    # 001904.python.configure.line92.comment UnknownExecutableFormatException on most .dylibs (and interferes with code signature on other occasions). And
    # 001905.python.configure.line93.comment even when it would succeed, compressed libraries cannot be (re)signed due to failed strict validation.
    upx_available = _check_upx_availability(upx_dir)
    if upx_available:
        if compat.is_win or compat.is_cygwin:
            logger.info("UPX is available and will be used if enabled on build targets.")
        elif os.environ.get("PYINSTALLER_FORCE_UPX", "0") != "0":
            logger.warning(
                "UPX is available and force-enabled on platform with known compatibility problems - use at own risk!"
            )
        else:
            upx_available = False
            logger.info("UPX is available but is disabled on non-Windows due to known compatibility problems.")
    config['upx_available'] = upx_available

    return config
