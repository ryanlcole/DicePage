#!/usr/bin/env bash
set -euo pipefail
grep -q 'RistWorld.styles.css' apps/rist-world/wwwroot/index.html
test -f build/rist/wwwroot/RistWorld.styles.css
