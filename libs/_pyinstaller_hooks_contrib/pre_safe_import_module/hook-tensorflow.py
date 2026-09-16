# 011446.python.hook-tensorflow.line1.comment -----------------------------------------------------------------------------
# 011447.python.hook-tensorflow.line2.comment Copyright (c) 2022, PyInstaller Development Team.
# 011448.python.hook-tensorflow.line3.comment
# 011449.python.hook-tensorflow.line4.comment This file is distributed under the terms of the GNU General Public
# 011450.python.hook-tensorflow.line5.comment License (version 2.0 or later).
# 011451.python.hook-tensorflow.line6.comment
# 011452.python.hook-tensorflow.line7.comment The full license is available in LICENSE, distributed with
# 011453.python.hook-tensorflow.line8.comment this software.
# 011454.python.hook-tensorflow.line9.comment
# 011455.python.hook-tensorflow.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011456.python.hook-tensorflow.line11.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies


def pre_safe_import_module(api):
    # 011457.python.hook-tensorflow.line17.comment As of tensorflow 2.8.0, the `tensorflow.keras` is entirely gone, replaced by a lazy-loaded alias for
    # 011458.python.hook-tensorflow.line18.comment `keras.api._v2.keras`. Without us registering the alias here, a program that imports only from
    # 011459.python.hook-tensorflow.line19.comment `tensorflow.keras` fails to collect `tensorflow`.
    # 011460.python.hook-tensorflow.line20.comment See: https://github.com/pyinstaller/pyinstaller/discussions/6890
    # 011461.python.hook-tensorflow.line21.comment The alias was already present in earlier releases, but it does not seem to be causing problems there,
    # 011462.python.hook-tensorflow.line22.comment so keep this specific to tensorflow >= 2.8.0 to avoid accidentally breaking something else.
    # 011463.python.hook-tensorflow.line23.comment
    # 011464.python.hook-tensorflow.line24.comment Starting with tensorflow 2.16.0, the alias points to `keras._tf_keras.keras`.
    if is_module_satisfies("tensorflow >= 2.16.0"):
        api.add_alias_module('keras._tf_keras.keras', 'tensorflow.keras')
    elif is_module_satisfies("tensorflow >= 2.8.0"):
        api.add_alias_module('keras.api._v2.keras', 'tensorflow.keras')
