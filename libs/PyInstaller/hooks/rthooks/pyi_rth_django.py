# 008164.python.pyi_rth_django.line1.comment -----------------------------------------------------------------------------
# 008165.python.pyi_rth_django.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 008166.python.pyi_rth_django.line3.comment
# 008167.python.pyi_rth_django.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008168.python.pyi_rth_django.line5.comment you may not use this file except in compliance with the License.
# 008169.python.pyi_rth_django.line6.comment
# 008170.python.pyi_rth_django.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008171.python.pyi_rth_django.line8.comment
# 008172.python.pyi_rth_django.line9.comment SPDX-License-Identifier: Apache-2.0
# 008173.python.pyi_rth_django.line10.comment -----------------------------------------------------------------------------

# 008174.python.pyi_rth_django.line12.comment This Django rthook was tested with Django 1.8.3.


def _pyi_rthook():
    import django.utils.autoreload

    _old_restart_with_reloader = django.utils.autoreload.restart_with_reloader

    def _restart_with_reloader(*args):
        import sys
        a0 = sys.argv.pop(0)
        try:
            return _old_restart_with_reloader(*args)
        finally:
            sys.argv.insert(0, a0)

    # 008175.python.pyi_rth_django.line28.comment Override restart_with_reloader() function, otherwise the app might complain that some commands do not exist;
    # 008176.python.pyi_rth_django.line29.comment e.g., runserver.
    django.utils.autoreload.restart_with_reloader = _restart_with_reloader


_pyi_rthook()
del _pyi_rthook
