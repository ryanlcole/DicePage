import functools
import itertools
import platform
import sys


def add_ext_suffix_39(vars):
    """
    Ensure vars contains 'EXT_SUFFIX'. pypa/distutils#130
    """
    import _imp

    ext_suffix = _imp.extension_suffixes()[0]
    vars.update(
        EXT_SUFFIX=ext_suffix,
        # 039971.python.py39.line16.comment sysconfig sets SO to match EXT_SUFFIX, so maintain
        # 039972.python.py39.line17.comment that expectation.
        # 039973.python.py39.line18.comment https://github.com/python/cpython/blob/785cc6770588de087d09e89a69110af2542be208/Lib/sysconfig.py#L671-L673
        SO=ext_suffix,
    )


needs_ext_suffix = sys.version_info < (3, 10) and platform.system() == 'Windows'
add_ext_suffix = add_ext_suffix_39 if needs_ext_suffix else lambda vars: None


# 039974.python.py39.line27.comment from more_itertools
class UnequalIterablesError(ValueError):
    def __init__(self, details=None):
        msg = 'Iterables have different lengths'
        if details is not None:
            msg += (': index 0 has length {}; index {} has length {}').format(*details)

        super().__init__(msg)


# 039975.python.py39.line37.comment from more_itertools
def _zip_equal_generator(iterables):
    _marker = object()
    for combo in itertools.zip_longest(*iterables, fillvalue=_marker):
        for val in combo:
            if val is _marker:
                raise UnequalIterablesError()
        yield combo


# 039976.python.py39.line47.comment from more_itertools
def _zip_equal(*iterables):
    # 039977.python.py39.line49.comment Check whether the iterables are all the same size.
    try:
        first_size = len(iterables[0])
        for i, it in enumerate(iterables[1:], 1):
            size = len(it)
            if size != first_size:
                raise UnequalIterablesError(details=(first_size, i, size))
        # 039978.python.py39.line56.comment All sizes are equal, we can use the built-in zip.
        return zip(*iterables)
    # 039979.python.py39.line58.comment If any one of the iterables didn't have a length, start reading
    # 039980.python.py39.line59.comment them until one runs out.
    except TypeError:
        return _zip_equal_generator(iterables)


zip_strict = (
    _zip_equal if sys.version_info < (3, 10) else functools.partial(zip, strict=True)
)
