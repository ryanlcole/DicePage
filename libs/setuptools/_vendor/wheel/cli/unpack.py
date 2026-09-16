from __future__ import annotations

from pathlib import Path

from ..wheelfile import WheelFile


def unpack(path: str, dest: str = ".") -> None:
    """Unpack a wheel.

    Wheel content will be unpacked to {dest}/{name}-{ver}, where {name}
    is the package name and {ver} its version.

    :param path: The path to the wheel.
    :param dest: Destination directory (default to current directory).
    """
    with WheelFile(path) as wf:
        namever = wf.parsed_filename.group("namever")
        destination = Path(dest) / namever
        print(f"Unpacking to: {destination}...", end="", flush=True)
        for zinfo in wf.filelist:
            wf.extract(zinfo, destination)

            # 043845.python.unpack.line24.comment Set permissions to the same values as they were set in the archive
            # 043846.python.unpack.line25.comment We have to do this manually due to
            # 043847.python.unpack.line26.comment https://github.com/python/cpython/issues/59999
            permissions = zinfo.external_attr >> 16 & 0o777
            destination.joinpath(zinfo.filename).chmod(permissions)

    print("OK")
