#!/usr/bin/env python3
"""Install the tracked ReLiC pre-push capture hook into this clone."""
from pathlib import Path
import shutil
import stat
import subprocess

root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
hooks = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "hooks"], text=True).strip())
if not hooks.is_absolute():
    hooks = root / hooks
hooks.mkdir(parents=True, exist_ok=True)
target = hooks / "pre-push"
if target.exists():
    backup = hooks / "pre-push.before-relic"
    if not backup.exists():
        shutil.copy2(target, backup)
        print(f"Preserved existing hook as {backup}")
shutil.copy2(root / "tools" / "relic-pre-push", target)
target.chmod(target.stat().st_mode | stat.S_IXUSR)
print(f"Installed ReLiC warn-only pre-push capture hook: {target}")
print("Captures are written under .git/relic-observatory/pre-push/ and do not modify the working tree.")
