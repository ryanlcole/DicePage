# 042689.python.markers.line1.comment This file is dual licensed under the terms of the Apache License, Version
# 042690.python.markers.line2.comment 2.0, and the BSD License. See the LICENSE file in the root of this repository
# 042691.python.markers.line3.comment for complete details.

from __future__ import annotations

import operator
import os
import platform
import sys
from typing import Any, Callable, TypedDict, cast

from ._parser import MarkerAtom, MarkerList, Op, Value, Variable
from ._parser import parse_marker as _parse_marker
from ._tokenizer import ParserSyntaxError
from .specifiers import InvalidSpecifier, Specifier
from .utils import canonicalize_name

__all__ = [
    "InvalidMarker",
    "Marker",
    "UndefinedComparison",
    "UndefinedEnvironmentName",
    "default_environment",
]

Operator = Callable[[str, str], bool]


class InvalidMarker(ValueError):
    """
    An invalid marker was found, users should refer to PEP 508.
    """


class UndefinedComparison(ValueError):
    """
    An invalid operation was attempted on a value that doesn't support it.
    """


class UndefinedEnvironmentName(ValueError):
    """
    A name was attempted to be used that does not exist inside of the
    environment.
    """


class Environment(TypedDict):
    implementation_name: str
    """The implementation's identifier, e.g. ``'cpython'``."""

    implementation_version: str
    """
    The implementation's version, e.g. ``'3.13.0a2'`` for CPython 3.13.0a2, or
    ``'7.3.13'`` for PyPy3.10 v7.3.13.
    """

    os_name: str
    """
    The value of :py:data:`os.name`. The name of the operating system dependent module
    imported, e.g. ``'posix'``.
    """

    platform_machine: str
    """
    Returns the machine type, e.g. ``'i386'``.

    An empty string if the value cannot be determined.
    """

    platform_release: str
    """
    The system's release, e.g. ``'2.2.0'`` or ``'NT'``.

    An empty string if the value cannot be determined.
    """

    platform_system: str
    """
    The system/OS name, e.g. ``'Linux'``, ``'Windows'`` or ``'Java'``.

    An empty string if the value cannot be determined.
    """

    platform_version: str
    """
    The system's release version, e.g. ``'#3 on degas'``.

    An empty string if the value cannot be determined.
    """

    python_full_version: str
    """
    The Python version as string ``'major.minor.patchlevel'``.

    Note that unlike the Python :py:data:`sys.version`, this value will always include
    the patchlevel (it defaults to 0).
    """

    platform_python_implementation: str
    """
    A string identifying the Python implementation, e.g. ``'CPython'``.
    """

    python_version: str
    """The Python version as string ``'major.minor'``."""

    sys_platform: str
    """
    This string contains a platform identifier that can be used to append
    platform-specific components to :py:data:`sys.path`, for instance.

    For Unix systems, except on Linux and AIX, this is the lowercased OS name as
    returned by ``uname -s`` with the first part of the version as returned by
    ``uname -r`` appended, e.g. ``'sunos5'`` or ``'freebsd8'``, at the time when Python
    was built.
    """


def _normalize_extra_values(results: Any) -> Any:
    """
    Normalize extra values.
    """
    if isinstance(results[0], tuple):
        lhs, op, rhs = results[0]
        if isinstance(lhs, Variable) and lhs.value == "extra":
            normalized_extra = canonicalize_name(rhs.value)
            rhs = Value(normalized_extra)
        elif isinstance(rhs, Variable) and rhs.value == "extra":
            normalized_extra = canonicalize_name(lhs.value)
            lhs = Value(normalized_extra)
        results[0] = lhs, op, rhs
    return results


def _format_marker(
    marker: list[str] | MarkerAtom | str, first: bool | None = True
) -> str:
    assert isinstance(marker, (list, tuple, str))

    # 042692.python.markers.line142.comment Sometimes we have a structure like [[...]] which is a single item list
    # 042693.python.markers.line143.comment where the single item is itself it's own list. In that case we want skip
    # 042694.python.markers.line144.comment the rest of this function so that we don't get extraneous () on the
    # 042695.python.markers.line145.comment outside.
    if (
        isinstance(marker, list)
        and len(marker) == 1
        and isinstance(marker[0], (list, tuple))
    ):
        return _format_marker(marker[0])

    if isinstance(marker, list):
        inner = (_format_marker(m, first=False) for m in marker)
        if first:
            return " ".join(inner)
        else:
            return "(" + " ".join(inner) + ")"
    elif isinstance(marker, tuple):
        return " ".join([m.serialize() for m in marker])
    else:
        return marker


_operators: dict[str, Operator] = {
    "in": lambda lhs, rhs: lhs in rhs,
    "not in": lambda lhs, rhs: lhs not in rhs,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    ">": operator.gt,
}


def _eval_op(lhs: str, op: Op, rhs: str) -> bool:
    try:
        spec = Specifier("".join([op.serialize(), rhs]))
    except InvalidSpecifier:
        pass
    else:
        return spec.contains(lhs, prereleases=True)

    oper: Operator | None = _operators.get(op.serialize())
    if oper is None:
        raise UndefinedComparison(f"Undefined {op!r} on {lhs!r} and {rhs!r}.")

    return oper(lhs, rhs)


def _normalize(*values: str, key: str) -> tuple[str, ...]:
    # 042696.python.markers.line193.comment PEP 685 – Comparison of extra names for optional distribution dependencies
    # 042697.python.markers.line194.comment https://peps.python.org/pep-0685/
    # 042698.python.markers.line195.comment > When comparing extra names, tools MUST normalize the names being
    # 042699.python.markers.line196.comment > compared using the semantics outlined in PEP 503 for names
    if key == "extra":
        return tuple(canonicalize_name(v) for v in values)

    # 042700.python.markers.line200.comment other environment markers don't have such standards
    return values


def _evaluate_markers(markers: MarkerList, environment: dict[str, str]) -> bool:
    groups: list[list[bool]] = [[]]

    for marker in markers:
        assert isinstance(marker, (list, tuple, str))

        if isinstance(marker, list):
            groups[-1].append(_evaluate_markers(marker, environment))
        elif isinstance(marker, tuple):
            lhs, op, rhs = marker

            if isinstance(lhs, Variable):
                environment_key = lhs.value
                lhs_value = environment[environment_key]
                rhs_value = rhs.value
            else:
                lhs_value = lhs.value
                environment_key = rhs.value
                rhs_value = environment[environment_key]

            lhs_value, rhs_value = _normalize(lhs_value, rhs_value, key=environment_key)
            groups[-1].append(_eval_op(lhs_value, op, rhs_value))
        else:
            assert marker in ["and", "or"]
            if marker == "or":
                groups.append([])

    return any(all(item) for item in groups)


def format_full_version(info: sys._version_info) -> str:
    version = f"{info.major}.{info.minor}.{info.micro}"
    kind = info.releaselevel
    if kind != "final":
        version += kind[0] + str(info.serial)
    return version


def default_environment() -> Environment:
    iver = format_full_version(sys.implementation.version)
    implementation_name = sys.implementation.name
    return {
        "implementation_name": implementation_name,
        "implementation_version": iver,
        "os_name": os.name,
        "platform_machine": platform.machine(),
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "platform_version": platform.version(),
        "python_full_version": platform.python_version(),
        "platform_python_implementation": platform.python_implementation(),
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "sys_platform": sys.platform,
    }


class Marker:
    def __init__(self, marker: str) -> None:
        # 042701.python.markers.line262.comment Note: We create a Marker object without calling this constructor in
        # 042702.python.markers.line263.comment packaging.requirements.Requirement. If any additional logic is
        # 042703.python.markers.line264.comment added here, make sure to mirror/adapt Requirement.
        try:
            self._markers = _normalize_extra_values(_parse_marker(marker))
            # 042704.python.markers.line267.comment The attribute `_markers` can be described in terms of a recursive type:
            # 042705.python.markers.line268.comment MarkerList = List[Union[Tuple[Node, ...], str, MarkerList]]
            # 042706.python.markers.line269.comment
            # 042707.python.markers.line270.comment For example, the following expression:
            # 042708.python.markers.line271.comment python_version > "3.6" or (python_version == "3.6" and os_name == "unix")
            # 042709.python.markers.line272.comment
            # 042710.python.markers.line273.comment is parsed into:
            # 042711.python.markers.line274.comment [
            # 042712.python.markers.line275.comment (<Variable('python_version')>, <Op('>')>, <Value('3.6')>),
            # 042713.python.markers.line276.comment 'and',
            # 042714.python.markers.line277.comment [
            # 042715.python.markers.line278.comment (<Variable('python_version')>, <Op('==')>, <Value('3.6')>),
            # 042716.python.markers.line279.comment 'or',
            # 042717.python.markers.line280.comment (<Variable('os_name')>, <Op('==')>, <Value('unix')>)
            # 042718.python.markers.line281.comment ]
            # 042719.python.markers.line282.comment ]
        except ParserSyntaxError as e:
            raise InvalidMarker(str(e)) from e

    def __str__(self) -> str:
        return _format_marker(self._markers)

    def __repr__(self) -> str:
        return f"<Marker('{self}')>"

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, str(self)))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Marker):
            return NotImplemented

        return str(self) == str(other)

    def evaluate(self, environment: dict[str, str] | None = None) -> bool:
        """Evaluate a marker.

        Return the boolean from evaluating the given marker against the
        environment. environment is an optional argument to override all or
        part of the determined environment.

        The environment is determined from the current Python process.
        """
        current_environment = cast("dict[str, str]", default_environment())
        current_environment["extra"] = ""
        if environment is not None:
            current_environment.update(environment)
            # 042720.python.markers.line314.comment The API used to allow setting extra to None. We need to handle this
            # 042721.python.markers.line315.comment case for backwards compatibility.
            if current_environment["extra"] is None:
                current_environment["extra"] = ""

        return _evaluate_markers(
            self._markers, _repair_python_full_version(current_environment)
        )


def _repair_python_full_version(env: dict[str, str]) -> dict[str, str]:
    """
    Work around platform.python_version() returning something that is not PEP 440
    compliant for non-tagged Python builds.
    """
    if env["python_full_version"].endswith("+"):
        env["python_full_version"] += "local"
    return env
