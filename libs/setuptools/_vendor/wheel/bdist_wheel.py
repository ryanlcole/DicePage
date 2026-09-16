from typing import TYPE_CHECKING
from warnings import warn

warn(
    "The 'wheel' package is no longer the canonical location of the 'bdist_wheel' "
    "command, and will be removed in a future release. Please update to setuptools "
    "v70.1 or later which contains an integrated version of this command.",
    DeprecationWarning,
    stacklevel=1,
)

if TYPE_CHECKING:
    from ._bdist_wheel import bdist_wheel as bdist_wheel
else:
    try:
        # 043814.python.bdist_wheel.line16.comment Better integration/compatibility with setuptools:
        # 043815.python.bdist_wheel.line17.comment in the case new fixes or PEPs are implemented in setuptools
        # 043816.python.bdist_wheel.line18.comment there is no need to backport them to the deprecated code base.
        # 043817.python.bdist_wheel.line19.comment This is useful in the case of old packages in the ecosystem
        # 043818.python.bdist_wheel.line20.comment that are still used but have low maintenance.
        from setuptools.command.bdist_wheel import bdist_wheel
    except ImportError:
        # 043819.python.bdist_wheel.line23.comment Only used in the case of old setuptools versions.
        # 043820.python.bdist_wheel.line24.comment If the user wants to get the latest fixes/PEPs,
        # 043821.python.bdist_wheel.line25.comment they are encouraged to address the deprecation warning.
        from ._bdist_wheel import bdist_wheel as bdist_wheel
