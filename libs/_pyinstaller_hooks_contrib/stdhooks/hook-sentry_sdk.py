# 016652.python.hook-sentry_sdk.line1.comment ------------------------------------------------------------------
# 016653.python.hook-sentry_sdk.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016654.python.hook-sentry_sdk.line3.comment
# 016655.python.hook-sentry_sdk.line4.comment This file is distributed under the terms of the GNU General Public
# 016656.python.hook-sentry_sdk.line5.comment License (version 2.0 or later).
# 016657.python.hook-sentry_sdk.line6.comment
# 016658.python.hook-sentry_sdk.line7.comment The full license is available in LICENSE, distributed with
# 016659.python.hook-sentry_sdk.line8.comment this software.
# 016660.python.hook-sentry_sdk.line9.comment
# 016661.python.hook-sentry_sdk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016662.python.hook-sentry_sdk.line11.comment ------------------------------------------------------------------
import json
from PyInstaller.utils.hooks import exec_statement

hiddenimports = ["sentry_sdk.integrations.stdlib",
                 "sentry_sdk.integrations.excepthook",
                 "sentry_sdk.integrations.dedupe",
                 "sentry_sdk.integrations.atexit",
                 "sentry_sdk.integrations.modules",
                 "sentry_sdk.integrations.argv",
                 "sentry_sdk.integrations.logging",
                 "sentry_sdk.integrations.threading"]

statement = """
import json
import sentry_sdk.integrations as si

integrations = []
if hasattr(si, '_AUTO_ENABLING_INTEGRATIONS'):
    # _AUTO_ENABLING_INTEGRATIONS is a list of strings with default enabled integrations
    # https://github.com/getsentry/sentry-python/blob/c6b6f2086b58ffc674df5c25a600b8a615079fb5/sentry_sdk/integrations/__init__.py#L54-L66

    def make_integration_name(integration_name: str):
        return integration_name.rsplit(".", maxsplit=1)[0]

    integrations.extend(map(make_integration_name, si._AUTO_ENABLING_INTEGRATIONS))
print(json.dumps(integrations))
"""

hiddenimports.extend(json.loads(exec_statement(statement)))
