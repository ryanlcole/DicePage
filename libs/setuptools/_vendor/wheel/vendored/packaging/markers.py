# 043941.python.markers.line1.comment This file is dual licensed under the terms of the Apache License, Version
# 043942.python.markers.line2.comment 2.0, and the BSD License. See the LICENSE file in the root of this repository
# 043943.python.markers.line3.comment for complete details.

import operator
import os
import platform
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ._parser import (
    MarkerAtom,
    MarkerList,
    Op,
    Value,
    Variable,
)
from ._parser import (
    parse_marker as _parse_marker,
)
from ._tokenizer import ParserSyntaxError
from .specifiers import InvalidSpecifier, Specifier
from .utils import canonicalize_name

__all__ = [
    "InvalidMarker",
    "UndefinedComparison",
    "UndefinedEnvironmentName",
    "Marker",
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
    marker: Union[List[str], MarkerAtom, str], first: Optional[bool] = True
) -> str:
    assert isinstance(marker, (list, tuple, str))

    # 043944.python.markers.line76.comment Sometimes we have a structure like [[...]] which is a single item list
    # 043945.python.markers.line77.comment where the single item is itself it's own list. In that case we want skip
    # 043946.python.markers.line78.comment the rest of this function so that we don't get extraneous () on the
    # 043947.python.markers.line79.comment outside.
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


_operators: Dict[str, Operator] = {
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

    oper: Optional[Operator] = _operators.get(op.serialize())
    if oper is None:
        raise UndefinedComparison(f"Undefined {op!r} on {lhs!r} and {rhs!r}.")

    return oper(lhs, rhs)


def _normalize(*values: str, key: str) -> Tuple[str, ...]:
    # 043948.python.markers.line127.comment PEP 685 – Comparison of extra names for optional distribution dependencies
    # 043949.python.markers.line128.comment https://peps.python.org/pep-0685/
    # 043950.python.markers.line129.comment > When comparing extra names, tools MUST normalize the names being
    # 043951.python.markers.line130.comment > compared using the semantics outlined in PEP 503 for names
    if key == "extra":
        return tuple(canonicalize_name(v) for v in values)

    # 043952.python.markers.line134.comment other environment markers don't have such standards
    return values


def _evaluate_markers(markers: MarkerList, environment: Dict[str, str]) -> bool:
    groups: List[List[bool]] = [[]]

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


def format_full_version(info: "sys._version_info") -> str:
    version = "{0.major}.{0.minor}.{0.micro}".format(info)
    kind = info.releaselevel
    if kind != "final":
        version += kind[0] + str(info.serial)
    return version


def default_environment() -> Dict[str, str]:
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
        # 043953.python.markers.line196.comment Note: We create a Marker object without calling this constructor in
        # 043954.python.markers.line197.comment packaging.requirements.Requirement. If any additional logic is
        # 043955.python.markers.line198.comment added here, make sure to mirror/adapt Requirement.
        try:
            self._markers = _normalize_extra_values(_parse_marker(marker))
            # 043956.python.markers.line201.comment The attribute `_markers` can be described in terms of a recursive type:
            # 043957.python.markers.line202.comment MarkerList = List[Union[Tuple[Node, ...], str, MarkerList]]
            # 043958.python.markers.line203.comment
            # 043959.python.markers.line204.comment For example, the following expression:
            # 043960.python.markers.line205.comment python_version > "3.6" or (python_version == "3.6" and os_name == "unix")
            # 043961.python.markers.line206.comment
            # 043962.python.markers.line207.comment is parsed into:
            # 043963.python.markers.line208.comment [
            # 043964.python.markers.line209.comment (<Variable('python_version')>, <Op('>')>, <Value('3.6')>),
            # 043965.python.markers.line210.comment 'and',
            # 043966.python.markers.line211.comment [
            # 043967.python.markers.line212.comment (<Variable('python_version')>, <Op('==')>, <Value('3.6')>),
            # 043968.python.markers.line213.comment 'or',
            # 043969.python.markers.line214.comment (<Variable('os_name')>, <Op('==')>, <Value('unix')>)
            # 043970.python.markers.line215.comment ]
            # 043971.python.markers.line216.comment ]
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

    def evaluate(self, environment: Optional[Dict[str, str]] = None) -> bool:
        """Evaluate a marker.

        Return the boolean from evaluating the given marker against the
        environment. environment is an optional argument to override all or
        part of the determined environment.

        The environment is determined from the current Python process.
        """
        current_environment = default_environment()
        current_environment["extra"] = ""
        if environment is not None:
            current_environment.update(environment)
            # 043972.python.markers.line248.comment The API used to allow setting extra to None. We need to handle this
            # 043973.python.markers.line249.comment case for backwards compatibility.
            if current_environment["extra"] is None:
                current_environment["extra"] = ""

        return _evaluate_markers(self._markers, current_environment)
