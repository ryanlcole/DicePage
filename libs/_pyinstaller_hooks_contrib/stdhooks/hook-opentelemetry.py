# 015118.python.hook-opentelemetry.line1.comment ------------------------------------------------------------------
# 015119.python.hook-opentelemetry.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 015120.python.hook-opentelemetry.line3.comment
# 015121.python.hook-opentelemetry.line4.comment This file is distributed under the terms of the GNU General Public
# 015122.python.hook-opentelemetry.line5.comment License (version 2.0 or later).
# 015123.python.hook-opentelemetry.line6.comment
# 015124.python.hook-opentelemetry.line7.comment The full license is available in LICENSE, distributed with
# 015125.python.hook-opentelemetry.line8.comment this software.
# 015126.python.hook-opentelemetry.line9.comment
# 015127.python.hook-opentelemetry.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015128.python.hook-opentelemetry.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_entry_point

# 015129.python.hook-opentelemetry.line15.comment All known `opentelementry_` entry-point groups
ENTRY_POINT_GROUPS = (
    'opentelemetry_context',
    'opentelemetry_environment_variables',
    'opentelemetry_id_generator',
    'opentelemetry_logger_provider',
    'opentelemetry_logs_exporter',
    'opentelemetry_meter_provider',
    'opentelemetry_metrics_exporter',
    'opentelemetry_propagator',
    'opentelemetry_resource_detector',
    'opentelemetry_tracer_provider',
    'opentelemetry_traces_exporter',
    'opentelemetry_traces_sampler',
)

# 015130.python.hook-opentelemetry.line31.comment Collect entry points
datas = set()
hiddenimports = set()

for entry_point_group in ENTRY_POINT_GROUPS:
    ep_datas, ep_hiddenimports = collect_entry_point(entry_point_group)
    datas.update(ep_datas)
    hiddenimports.update(ep_hiddenimports)

datas = list(datas)
hiddenimports = list(hiddenimports)
