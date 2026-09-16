# 016530.python.hook-ruamel.yaml.line1.comment ------------------------------------------------------------------
# 016531.python.hook-ruamel.yaml.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 016532.python.hook-ruamel.yaml.line3.comment
# 016533.python.hook-ruamel.yaml.line4.comment This file is distributed under the terms of the GNU General Public
# 016534.python.hook-ruamel.yaml.line5.comment License (version 2.0 or later).
# 016535.python.hook-ruamel.yaml.line6.comment
# 016536.python.hook-ruamel.yaml.line7.comment The full license is available in LICENSE, distributed with
# 016537.python.hook-ruamel.yaml.line8.comment this software.
# 016538.python.hook-ruamel.yaml.line9.comment
# 016539.python.hook-ruamel.yaml.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016540.python.hook-ruamel.yaml.line11.comment ------------------------------------------------------------------

# 016541.python.hook-ruamel.yaml.line13.comment `ruamel.yaml` offers several optional plugins that can be installed via additional packages
# 016542.python.hook-ruamel.yaml.line14.comment (e.g., `runamel.yaml.string`). Unfortunately, the discovery of these plugins is predicated on their `__plug_in__.py`
# 016543.python.hook-ruamel.yaml.line15.comment files being visible on filesystem.
# 016544.python.hook-ruamel.yaml.line16.comment See: https://sourceforge.net/p/ruamel-yaml/code/ci/0bef9fa8b3c43637cd90ce3f2e299e81c2122128/tree/main.py#l757

import pathlib

from PyInstaller.utils.hooks import get_module_file_attribute, logger

ruamel_path = pathlib.Path(get_module_file_attribute('ruamel.yaml')).parent

plugin_files = ruamel_path.glob('*/__plug_in__.py')
plugin_names = [plugin_file.parent.name for plugin_file in plugin_files]
logger.debug("hook-ruamel.yaml: found plugins: %r", plugin_names)

# 016545.python.hook-ruamel.yaml.line28.comment Add `__plug_in__` modules to hiddenimports to ensure they are collected and scanned for imports. This also implicitly
# 016546.python.hook-ruamel.yaml.line29.comment collects the plugin's `__init__` module.
plugin_modules = [f"ruamel.yaml.{plugin_name}.__plug_in__" for plugin_name in plugin_names]

hiddenimports = plugin_modules

# 016547.python.hook-ruamel.yaml.line34.comment Collect the plugins' `__plug_in__` modules both as byte-compiled .pyc in PYZ archive (to be actually loaded) and
# 016548.python.hook-ruamel.yaml.line35.comment source .py file (which allows plugin to be discovered).
module_collection_mode = {
    plugin_module: "pyz+py"
    for plugin_module in plugin_modules
}
