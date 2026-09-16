# 002403.python.bytecode.line1.comment -----------------------------------------------------------------------------
# 002404.python.bytecode.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 002405.python.bytecode.line3.comment
# 002406.python.bytecode.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 002407.python.bytecode.line5.comment or later) with exception for distributing the bootloader.
# 002408.python.bytecode.line6.comment
# 002409.python.bytecode.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002410.python.bytecode.line8.comment
# 002411.python.bytecode.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 002412.python.bytecode.line10.comment -----------------------------------------------------------------------------
"""
Tools for searching bytecode for key statements that indicate the need for additional resources, such as data files
and package metadata.

By *bytecode* I mean the ``code`` object given by ``compile()``, accessible from the ``__code__`` attribute of any
non-builtin function or, in PyInstallerLand, the ``PyiModuleGraph.node("some.module").code`` attribute. The best
guide for bytecode format I have found is the disassembler reference: https://docs.python.org/3/library/dis.html

This parser implementation aims to combine the flexibility and speed of regex with the clarity of the output of
``dis.dis(code)``. It has not achieved the 2nd, but C'est la vie...

The biggest clarity killer here is the ``EXTENDED_ARG`` opcode which can appear almost anywhere and therefore needs
to be tiptoed around at every step. If this code needs to expand significantly, I would recommend an upgrade to a
regex-based grammar parsing library such as Reparse. This way, little steps like unpacking ``EXTENDED_ARGS`` can be
defined once then simply referenced forming a nice hierarchy rather than copied everywhere its needed.
"""

import dis
import re
from types import CodeType
from typing import Pattern

from PyInstaller import compat

# 002413.python.bytecode.line35.comment opcode name -> opcode map
# 002414.python.bytecode.line36.comment Python 3.11 introduced specialized opcodes that are not covered by opcode.opmap (and equivalent dis.opmap), but dis
# 002415.python.bytecode.line37.comment has a private map of all opcodes called _all_opmap. So use the latter, if available.
opmap = getattr(dis, '_all_opmap', dis.opmap)


def _instruction_to_regex(x: str):
    """
    Get a regex-escaped opcode byte from its human readable name.
    """
    return re.escape(bytes([opmap[x]]))


def bytecode_regex(pattern: bytes, flags=re.VERBOSE | re.DOTALL):
    """
    A regex-powered Python bytecode matcher.

    ``bytecode_regex`` provides a very thin wrapper around :func:`re.compile`.

      * Any opcode names wrapped in backticks are substituted for their corresponding opcode bytes.
      * Patterns are compiled in VERBOSE mode by default so that whitespace and comments may be used.

    This aims to mirror the output of :func:`dis.dis`, which is far more readable than looking at raw byte strings.
    """
    assert isinstance(pattern, bytes)

    # 002416.python.bytecode.line61.comment Replace anything wrapped in backticks with regex-escaped opcodes.
    pattern = re.sub(
        rb"`(\w+)`",
        lambda m: _instruction_to_regex(m[1].decode()),
        pattern,
    )
    return re.compile(pattern, flags=flags)


def finditer(pattern: Pattern, string: bytes):
    """
    Call ``pattern.finditer(string)``, but remove any matches beginning on an odd byte (i.e., matches where
    match.start() is not a multiple of 2).

    This should be used to avoid false positive matches where a bytecode pair's argument is mistaken for an opcode.
    """
    assert isinstance(string, bytes)
    string = _cleanup_bytecode_string(string)
    matches = pattern.finditer(string)
    while True:
        for match in matches:
            if match.start() % 2 == 0:
                # 002417.python.bytecode.line83.comment All is good. This match starts on an OPCODE.
                yield match
            else:
                # 002418.python.bytecode.line86.comment This match has started on an odd byte, meaning that it is a false positive and should be skipped.
                # 002419.python.bytecode.line87.comment There is a very slim chance that a genuine match overlaps this one and, because re.finditer() does not
                # 002420.python.bytecode.line88.comment allow overlapping matches, it would be lost. To avoid that, restart the regex scan, starting at the
                # 002421.python.bytecode.line89.comment next even byte.
                matches = pattern.finditer(string, match.start() + 1)
                break
        else:
            break


# 002422.python.bytecode.line96.comment Opcodes involved in function calls with constant arguments. The differences between python versions are handled by
# 002423.python.bytecode.line97.comment variables below, which are then used to construct the _call_function_bytecode regex.
# 002424.python.bytecode.line98.comment NOTE1: the _OPCODES_* entries are typically used in (non-capturing) groups that match the opcode plus an arbitrary
# 002425.python.bytecode.line99.comment argument. But because the entries themselves may contain more than on opcode (with OR operator between them), they
# 002426.python.bytecode.line100.comment themselves need to be enclosed in another (non-capturing) group. E.g., "(?:(?:_OPCODES_FUNCTION_GLOBAL).)".
# 002427.python.bytecode.line101.comment NOTE2: _OPCODES_EXTENDED_ARG2 is an exception, as it is used as a list of opcodes to exclude, i.e.,
# 002428.python.bytecode.line102.comment "[^_OPCODES_EXTENDED_ARG2]". Therefore, multiple opcodes are not separated by the OR operator.
if not compat.is_py311:
    # 002429.python.bytecode.line104.comment Python 3.7 introduced two new function-related opcodes, LOAD_METHOD and CALL_METHOD
    _OPCODES_EXTENDED_ARG = rb"`EXTENDED_ARG`"
    _OPCODES_EXTENDED_ARG2 = _OPCODES_EXTENDED_ARG
    _OPCODES_FUNCTION_GLOBAL = rb"`LOAD_NAME`|`LOAD_GLOBAL`|`LOAD_FAST`"
    _OPCODES_FUNCTION_LOAD = rb"`LOAD_ATTR`|`LOAD_METHOD`"
    _OPCODES_FUNCTION_ARGS = rb"`LOAD_CONST`"
    _OPCODES_FUNCTION_CALL = rb"`CALL_FUNCTION`|`CALL_METHOD`|`CALL_FUNCTION_EX`"

    def _cleanup_bytecode_string(bytecode):
        return bytecode  # Nothing to do here
elif not compat.is_py312:
    # 002431.python.bytecode.line115.comment Python 3.11 removed CALL_FUNCTION and CALL_METHOD, and replaced them with PRECALL + CALL instruction sequence.
    # 002432.python.bytecode.line116.comment As both PRECALL and CALL have the same parameter (the argument count), we need to match only up to the PRECALL.
    # 002433.python.bytecode.line117.comment The CALL_FUNCTION_EX is still present.
    # 002434.python.bytecode.line118.comment From Python 3.11b1 on, there is an EXTENDED_ARG_QUICK specialization opcode present.
    _OPCODES_EXTENDED_ARG = rb"`EXTENDED_ARG`|`EXTENDED_ARG_QUICK`"
    _OPCODES_EXTENDED_ARG2 = rb"`EXTENDED_ARG``EXTENDED_ARG_QUICK`"  # Special case; see note above the if/else block!
    _OPCODES_FUNCTION_GLOBAL = rb"`LOAD_NAME`|`LOAD_GLOBAL`|`LOAD_FAST`"
    _OPCODES_FUNCTION_LOAD = rb"`LOAD_ATTR`|`LOAD_METHOD`"
    _OPCODES_FUNCTION_ARGS = rb"`LOAD_CONST`"
    _OPCODES_FUNCTION_CALL = rb"`PRECALL`|`CALL_FUNCTION_EX`"

    # 002436.python.bytecode.line126.comment Starting with python 3.11, the bytecode is peppered with CACHE instructions (which dis module conveniently hides
    # 002437.python.bytecode.line127.comment unless show_caches=True is used). Dealing with these CACHE instructions in regex rules is going to render them
    # 002438.python.bytecode.line128.comment unreadable, so instead we pre-process the bytecode and filter the offending opcodes out.
    _cache_instruction_filter = bytecode_regex(rb"(`CACHE`.)|(..)")

    def _cleanup_bytecode_string(bytecode):
        return _cache_instruction_filter.sub(rb"\2", bytecode)
else:
    # 002439.python.bytecode.line134.comment Python 3.12 merged EXTENDED_ARG_QUICK back in to EXTENDED_ARG, and LOAD_METHOD in to LOAD_ATTR
    # 002440.python.bytecode.line135.comment PRECALL is no longer a valid key
    _OPCODES_EXTENDED_ARG = rb"`EXTENDED_ARG`"
    _OPCODES_EXTENDED_ARG2 = _OPCODES_EXTENDED_ARG
    if compat.is_py314:
        # 002441.python.bytecode.line139.comment Python 3.14.0a7 added LOAD_FAST_BORROW.
        _OPCODES_FUNCTION_GLOBAL = rb"`LOAD_NAME`|`LOAD_GLOBAL`|`LOAD_FAST`|`LOAD_FAST_BORROW`"
    else:
        _OPCODES_FUNCTION_GLOBAL = rb"`LOAD_NAME`|`LOAD_GLOBAL`|`LOAD_FAST`"
    _OPCODES_FUNCTION_LOAD = rb"`LOAD_ATTR`"
    if compat.is_py314:
        # 002442.python.bytecode.line145.comment Python 3.14.0a2 split LOAD_CONST into LOAD_CONST, LOAD_IMMORTAL_CONST, and LOAD_SMALL_INT.
        # 002443.python.bytecode.line146.comment https://github.com/python/cpython/commit/faa3272fb8d63d481a136cc0467a0cba6ed7b264
        _OPCODES_FUNCTION_ARGS = rb"`LOAD_CONST`|`LOAD_SMALL_INT`|`LOAD_CONST_IMMORTAL`"
    else:
        _OPCODES_FUNCTION_ARGS = rb"`LOAD_CONST`"
    _OPCODES_FUNCTION_CALL = rb"`CALL`|`CALL_FUNCTION_EX`"

    # 002444.python.bytecode.line152.comment In Python 3.13, PUSH_NULL opcode is emitted after the LOAD_NAME (and after LOAD_ATTR opcode(s), if applicable).
    # 002445.python.bytecode.line153.comment In python 3.11 and 3.12, it was emitted before the LOAD_NAME, and thus fell outside of our regex matching; now,
    # 002446.python.bytecode.line154.comment we have to deal with it. But, instead of trying to add it to matching rules and adjusting the post-processing
    # 002447.python.bytecode.line155.comment to deal with it, we opt to filter them out (at the same time as we filter out CACHE opcodes), and leave the rest
    # 002448.python.bytecode.line156.comment of processing untouched.
    if compat.is_py313:
        _cache_instruction_filter = bytecode_regex(rb"(`CACHE`.)|(`PUSH_NULL`.)|(..)")

        def _cleanup_bytecode_string(bytecode):
            return _cache_instruction_filter.sub(rb"\3", bytecode)
    else:
        _cache_instruction_filter = bytecode_regex(rb"(`CACHE`.)|(..)")

        def _cleanup_bytecode_string(bytecode):
            return _cache_instruction_filter.sub(rb"\2", bytecode)


# 002449.python.bytecode.line169.comment language=PythonVerboseRegExp
_call_function_bytecode = bytecode_regex(
    rb"""
    # Matches `global_function('some', 'constant', 'arguments')`.

    # Load the global function. In code with >256 of names, this may require extended name references.
    (
     (?:(?:""" + _OPCODES_EXTENDED_ARG + rb""").)*
     (?:(?:""" + _OPCODES_FUNCTION_GLOBAL + rb""").)
    )

    # For foo.bar.whizz(), the above is the 'foo', below is the 'bar.whizz' (one opcode per name component, each
    # possibly preceded by name reference extension).
    (
     (?:
       (?:(?:""" + _OPCODES_EXTENDED_ARG + rb""").)*
       (?:""" + _OPCODES_FUNCTION_LOAD + rb""").
     )*
    )

    # Load however many arguments it takes. These (for now) must all be constants.
    # Again, code with >256 constants may need extended enumeration.
    (
      (?:
        (?:(?:""" + _OPCODES_EXTENDED_ARG + rb""").)*
        (?:""" + _OPCODES_FUNCTION_ARGS + rb""").
      )*
    )

    # Call the function. If opcode is CALL_FUNCTION_EX, the parameter are flags. For other opcodes, the parameter
    # is the argument count (which may be > 256).
    (
      (?:(?:""" + _OPCODES_EXTENDED_ARG + rb""").)*
      (?:""" + _OPCODES_FUNCTION_CALL + rb""").
    )
"""
)

# 002450.python.bytecode.line207.comment language=PythonVerboseRegExp
_extended_arg_bytecode = bytecode_regex(
    rb"""(
    # Arbitrary number of EXTENDED_ARG pairs.
    (?:(?:""" + _OPCODES_EXTENDED_ARG + rb""").)*

    # Followed by some other instruction (usually a LOAD).
    [^""" + _OPCODES_EXTENDED_ARG2 + rb"""].
)"""
)


def extended_arguments(extended_args: bytes):
    """
    Unpack the (extended) integer used to reference names or constants.

    The input should be a bytecode snippet of the following form::

        EXTENDED_ARG    ?      # Repeated 0-4 times.
        LOAD_xxx        ?      # Any of LOAD_NAME/LOAD_CONST/LOAD_METHOD/...

    Each ? byte combined together gives the number we want.
    """
    return int.from_bytes(extended_args[1::2], "big")


def load(raw: bytes, code: CodeType) -> str:
    """
    Parse an (extended) LOAD_xxx instruction.
    """
    # 002451.python.bytecode.line237.comment Get the enumeration.
    index = extended_arguments(raw)

    # 002452.python.bytecode.line240.comment Work out what that enumeration was for (constant/local var/global var).

    # 002453.python.bytecode.line242.comment If the last instruction byte is a LOAD_FAST:
    if raw[-2] == opmap["LOAD_FAST"]:
        # 002454.python.bytecode.line244.comment Then this is a local variable.
        return code.co_varnames[index]
    # 002455.python.bytecode.line246.comment Or if it is a LOAD_CONST:
    if raw[-2] == opmap["LOAD_CONST"]:
        # 002456.python.bytecode.line248.comment Then this is a literal.
        return code.co_consts[index]
    # 002457.python.bytecode.line250.comment Otherwise, it is a global name.
    if compat.is_py311 and raw[-2] == opmap["LOAD_GLOBAL"]:
        # 002458.python.bytecode.line252.comment In python 3.11, namei>>1 is pushed on stack...
        return code.co_names[index >> 1]
    if compat.is_py312 and raw[-2] == opmap["LOAD_ATTR"]:
        # 002459.python.bytecode.line255.comment In python 3.12, namei>>1 is pushed on stack...
        return code.co_names[index >> 1]
    if compat.is_py314 and raw[-2] == opmap["LOAD_SMALL_INT"]:
        # 002460.python.bytecode.line258.comment python 3.14 introduced LOAD_SMALL_INT, which pushes its argument (int value < 256) on the stack
        return index
    if compat.is_py314 and raw[-2] == opmap["LOAD_CONST_IMMORTAL"]:
        # 002461.python.bytecode.line261.comment python 3.14 introduced LOAD_CONST_IMMORTAL, which pushes co_consts[consti] on the stack. This is intended to
        # 002462.python.bytecode.line262.comment be a variant of LOAD_CONST for constants that are known to be immortal.
        return code.co_consts[index]
    if compat.is_py314 and raw[-2] == opmap["LOAD_FAST_BORROW"]:
        # 002463.python.bytecode.line265.comment python 3.14 introduced LOAD_FAST_BORROW, which pushes a borrowed reference to the local co_varnames[var_num]
        # 002464.python.bytecode.line266.comment onto the stack.
        return code.co_varnames[index]

    return code.co_names[index]


def loads(raw: bytes, code: CodeType) -> list:
    """
    Parse multiple consecutive LOAD_xxx instructions. Or load() in a for loop.

    May be used to unpack a function's parameters or nested attributes ``(foo.bar.pop.whack)``.
    """
    return [load(i, code) for i in _extended_arg_bytecode.findall(raw)]


def function_calls(code: CodeType) -> list:
    """
    Scan a code object for all function calls on constant arguments.
    """
    match: re.Match
    out = []

    for match in finditer(_call_function_bytecode, code.co_code):
        function_root, methods, args, function_call = match.groups()

        # 002465.python.bytecode.line291.comment For foo():
        # 002466.python.bytecode.line292.comment `function_root` contains 'foo' and `methods` is empty.
        # 002467.python.bytecode.line293.comment For foo.bar.whizz():
        # 002468.python.bytecode.line294.comment `function_root` contains 'foo' and `methods` contains the rest.
        function_root = load(function_root, code)
        methods = loads(methods, code)
        function = ".".join([function_root] + methods)

        args = loads(args, code)
        if function_call[0] == opmap['CALL_FUNCTION_EX']:
            flags = extended_arguments(function_call)
            if flags != 0:
                # 002469.python.bytecode.line303.comment Keyword arguments present. Unhandled at the moment.
                continue
            # 002470.python.bytecode.line305.comment In calls with const arguments, args contains a single
            # 002471.python.bytecode.line306.comment tuple with all values.
            if len(args) != 1 or not isinstance(args[0], tuple):
                continue
            args = list(args[0])
        else:
            arg_count = extended_arguments(function_call)

            if arg_count != len(args):
                # 002472.python.bytecode.line314.comment This happens if there are variable or keyword arguments. Bail out in either case.
                continue

        out.append((function, args))

    return out


def search_recursively(search: callable, code: CodeType, _memo=None) -> dict:
    """
    Apply a search function to a code object, recursing into child code objects (function definitions).
    """
    if _memo is None:
        _memo = {}
    if code not in _memo:
        _memo[code] = search(code)
        for const in code.co_consts:
            if isinstance(const, CodeType):
                search_recursively(search, const, _memo)
    return _memo


def recursive_function_calls(code: CodeType) -> dict:
    """
    Scan a code object for function calls on constant arguments, recursing into function definitions and bodies of
    comprehension loops.
    """
    return search_recursively(function_calls, code)


def any_alias(full_name: str):
    """List possible aliases of a fully qualified Python name.

        >>> list(any_alias("foo.bar.wizz"))
        ['foo.bar.wizz', 'bar.wizz', 'wizz']

    This crudely allows us to capture uses of wizz() under any of
    ::
        import foo
        foo.bar.wizz()
    ::
        from foo import bar
        bar.wizz()
    ::
        from foo.bar import wizz
        wizz()

    However, it will fail for any form of aliases and quite likely find false matches.
    """
    parts = full_name.split('.')
    while parts:
        yield ".".join(parts)
        parts = parts[1:]
