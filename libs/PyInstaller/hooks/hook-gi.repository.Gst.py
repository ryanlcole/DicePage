# 005715.python.hook-gi.repository.Gst.line1.comment -----------------------------------------------------------------------------
# 005716.python.hook-gi.repository.Gst.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005717.python.hook-gi.repository.Gst.line3.comment
# 005718.python.hook-gi.repository.Gst.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005719.python.hook-gi.repository.Gst.line5.comment or later) with exception for distributing the bootloader.
# 005720.python.hook-gi.repository.Gst.line6.comment
# 005721.python.hook-gi.repository.Gst.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005722.python.hook-gi.repository.Gst.line8.comment
# 005723.python.hook-gi.repository.Gst.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005724.python.hook-gi.repository.Gst.line10.comment -----------------------------------------------------------------------------

# 005725.python.hook-gi.repository.Gst.line12.comment GStreamer contains a lot of plugins. We need to collect them and bundle them with the exe file. We also need to
# 005726.python.hook-gi.repository.Gst.line13.comment resolve binary dependencies of these GStreamer plugins.

import pathlib

from PyInstaller.utils.hooks import get_hook_config, include_or_exclude_file
import PyInstaller.log as logging
from PyInstaller import isolated
from PyInstaller.utils.hooks.gi import GiModuleInfo, collect_glib_share_files, collect_glib_translations

logger = logging.getLogger(__name__)


@isolated.decorate
def _get_gst_plugin_path():
    import os
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    reg = Gst.Registry.get()
    plug = reg.find_plugin('coreelements')
    path = plug.get_filename()
    return os.path.dirname(path)


def _format_plugin_pattern(plugin_name):
    return f"**/*gst{plugin_name}.*"


def hook(hook_api):
    module_info = GiModuleInfo('Gst', '1.0')
    if not module_info.available:
        return

    binaries, datas, hiddenimports = module_info.collect_typelib_data()
    hiddenimports += ["gi.repository.Gio"]

    # 005727.python.hook-gi.repository.Gst.line50.comment Collect data files
    datas += collect_glib_share_files('gstreamer-1.0')

    # 005728.python.hook-gi.repository.Gst.line53.comment Translations
    lang_list = get_hook_config(hook_api, "gi", "languages")
    for prog in [
        'gst-plugins-bad-1.0',
        'gst-plugins-base-1.0',
        'gst-plugins-good-1.0',
        'gst-plugins-ugly-1.0',
        'gstreamer-1.0',
    ]:
        datas += collect_glib_translations(prog, lang_list)

    # 005729.python.hook-gi.repository.Gst.line64.comment Plugins
    try:
        plugin_path = _get_gst_plugin_path()
    except Exception as e:
        logger.warning("Failed to determine gstreamer plugin path: %s", e)
        plugin_path = None

    if plugin_path:
        plugin_path = pathlib.Path(plugin_path)

        # 005730.python.hook-gi.repository.Gst.line74.comment Obtain optional include/exclude list from hook config
        include_list = get_hook_config(hook_api, "gstreamer", "include_plugins")
        exclude_list = get_hook_config(hook_api, "gstreamer", "exclude_plugins")

        # 005731.python.hook-gi.repository.Gst.line78.comment Format plugin basenames into filename patterns for matching
        if include_list is not None:
            include_list = [_format_plugin_pattern(name) for name in include_list]
        if exclude_list is not None:
            exclude_list = [_format_plugin_pattern(name) for name in exclude_list]

        # 005732.python.hook-gi.repository.Gst.line84.comment The names of GStreamer plugins typically start with libgst (or just gst, depending on the toolchain). We also
        # 005733.python.hook-gi.repository.Gst.line85.comment need to account for different extensions that might be used on a particular OS (for example, on macOS, the
        # 005734.python.hook-gi.repository.Gst.line86.comment extension may be either .so or .dylib).
        for lib_pattern in ['*gst*.dll', '*gst*.dylib', '*gst*.so']:
            binaries += [(str(filename), 'gst_plugins') for filename in plugin_path.glob(lib_pattern)
                         if include_or_exclude_file(filename, include_list, exclude_list)]

    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
