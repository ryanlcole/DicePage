try:
    # 044933.python.modified.line2.comment Ensure a DistutilsError raised by these methods is the same as distutils.errors.DistutilsError
    from distutils._modified import (
        newer,
        newer_group,
        newer_pairwise,
        newer_pairwise_group,
    )
except ImportError:
    # 044934.python.modified.line10.comment fallback for SETUPTOOLS_USE_DISTUTILS=stdlib, because _modified never existed in stdlib
    from ._distutils._modified import (
        newer,
        newer_group,
        newer_pairwise,
        newer_pairwise_group,
    )

__all__ = ['newer', 'newer_pairwise', 'newer_group', 'newer_pairwise_group']
