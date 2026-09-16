"""cat.py
a version of unix cat, tweaked to show off runproc.py
"""

import sys

data = sys.stdin.read(1)
sys.stdout.write(data)
sys.stdout.flush()
while data:
    data = sys.stdin.read(1)
    sys.stdout.write(data)
    sys.stdout.flush()
# 046075.python.cat.line14.comment Just here to have something to read from stderr.
sys.stderr.write("Blah...")

# 046076.python.cat.line17.comment end of cat.py
