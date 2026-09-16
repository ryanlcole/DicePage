# 006900.python.hook-sphinx.line1.comment -----------------------------------------------------------------------------
# 006901.python.hook-sphinx.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006902.python.hook-sphinx.line3.comment
# 006903.python.hook-sphinx.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006904.python.hook-sphinx.line5.comment or later) with exception for distributing the bootloader.
# 006905.python.hook-sphinx.line6.comment
# 006906.python.hook-sphinx.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006907.python.hook-sphinx.line8.comment
# 006908.python.hook-sphinx.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006909.python.hook-sphinx.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, eval_statement

# 006910.python.hook-sphinx.line14.comment Sphinx consists of several extensions that are lazily loaded. So collect all submodules to ensure we do not miss
# 006911.python.hook-sphinx.line15.comment any of them.
hiddenimports = collect_submodules('sphinx')

# 006912.python.hook-sphinx.line18.comment For each extension in sphinx.application.builtin_extensions that does not come from the sphinx package, do a
# 006913.python.hook-sphinx.line19.comment collect_submodules(). We need to do this explicitly because collect_submodules() does not seem to work with
# 006914.python.hook-sphinx.line20.comment namespace packages, which precludes us from simply doing hiddenimports += collect_submodules('sphinxcontrib')
builtin_extensions = list(
    eval_statement(
        """
        from sphinx.application import builtin_extensions
        print(builtin_extensions)
        """
    )
)
for extension in builtin_extensions:
    if extension.startswith('sphinx.'):
        continue  # Already collected
    hiddenimports += collect_submodules(extension)

# 006916.python.hook-sphinx.line34.comment This is inherited from an earlier version of the hook, and seems to have been required in Sphinx v.1.3.1 era due to
# 006917.python.hook-sphinx.line35.comment https://github.com/sphinx-doc/sphinx/blob/b87ce32e7dc09773f9e71305e66e8d6aead53dd1/sphinx/cmdline.py#L173.
# 006918.python.hook-sphinx.line36.comment It does not hurt to keep it around, just in case.
hiddenimports += ['locale']

# 006919.python.hook-sphinx.line39.comment Collect all data files: *.html and *.conf files in ``sphinx.themes``, translation files in ``sphinx.locale``, etc.
# 006920.python.hook-sphinx.line40.comment Also collect all data files for the alabaster theme.
datas = collect_data_files('sphinx') + collect_data_files('alabaster')
