# 044160.python.utils.line1.comment This file is dual licensed under the terms of the Apache License, Version
# 044161.python.utils.line2.comment 2.0, and the BSD License. See the LICENSE file in the root of this repository
# 044162.python.utils.line3.comment for complete details.

import re
from typing import FrozenSet, NewType, Tuple, Union, cast

from .tags import Tag, parse_tag
from .version import InvalidVersion, Version

BuildTag = Union[Tuple[()], Tuple[int, str]]
NormalizedName = NewType("NormalizedName", str)


class InvalidName(ValueError):
    """
    An invalid distribution name; users should refer to the packaging user guide.
    """


class InvalidWheelFilename(ValueError):
    """
    An invalid wheel filename was found, users should refer to PEP 427.
    """


class InvalidSdistFilename(ValueError):
    """
    An invalid sdist filename was found, users should refer to the packaging user guide.
    """


# 044163.python.utils.line33.comment Core metadata spec for `Name`
_validate_regex = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)
_canonicalize_regex = re.compile(r"[-_.]+")
_normalized_regex = re.compile(r"^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$")
# 044164.python.utils.line39.comment PEP 427: The build number must start with a digit.
_build_tag_regex = re.compile(r"(\d+)(.*)")


def canonicalize_name(name: str, *, validate: bool = False) -> NormalizedName:
    if validate and not _validate_regex.match(name):
        raise InvalidName(f"name is invalid: {name!r}")
    # 044165.python.utils.line46.comment This is taken from PEP 503.
    value = _canonicalize_regex.sub("-", name).lower()
    return cast(NormalizedName, value)


def is_normalized_name(name: str) -> bool:
    return _normalized_regex.match(name) is not None


def canonicalize_version(
    version: Union[Version, str], *, strip_trailing_zero: bool = True
) -> str:
    """
    This is very similar to Version.__str__, but has one subtle difference
    with the way it handles the release segment.
    """
    if isinstance(version, str):
        try:
            parsed = Version(version)
        except InvalidVersion:
            # 044166.python.utils.line66.comment Legacy versions cannot be normalized
            return version
    else:
        parsed = version

    parts = []

    # 044167.python.utils.line73.comment Epoch
    if parsed.epoch != 0:
        parts.append(f"{parsed.epoch}!")

    # 044168.python.utils.line77.comment Release segment
    release_segment = ".".join(str(x) for x in parsed.release)
    if strip_trailing_zero:
        # 044169.python.utils.line80.comment NB: This strips trailing '.0's to normalize
        release_segment = re.sub(r"(\.0)+$", "", release_segment)
    parts.append(release_segment)

    # 044170.python.utils.line84.comment Pre-release
    if parsed.pre is not None:
        parts.append("".join(str(x) for x in parsed.pre))

    # 044171.python.utils.line88.comment Post-release
    if parsed.post is not None:
        parts.append(f".post{parsed.post}")

    # 044172.python.utils.line92.comment Development release
    if parsed.dev is not None:
        parts.append(f".dev{parsed.dev}")

    # 044173.python.utils.line96.comment Local version segment
    if parsed.local is not None:
        parts.append(f"+{parsed.local}")

    return "".join(parts)


def parse_wheel_filename(
    filename: str,
) -> Tuple[NormalizedName, Version, BuildTag, FrozenSet[Tag]]:
    if not filename.endswith(".whl"):
        raise InvalidWheelFilename(
            f"Invalid wheel filename (extension must be '.whl'): {filename}"
        )

    filename = filename[:-4]
    dashes = filename.count("-")
    if dashes not in (4, 5):
        raise InvalidWheelFilename(
            f"Invalid wheel filename (wrong number of parts): {filename}"
        )

    parts = filename.split("-", dashes - 2)
    name_part = parts[0]
    # 044174.python.utils.line120.comment See PEP 427 for the rules on escaping the project name.
    if "__" in name_part or re.match(r"^[\w\d._]*$", name_part, re.UNICODE) is None:
        raise InvalidWheelFilename(f"Invalid project name: {filename}")
    name = canonicalize_name(name_part)

    try:
        version = Version(parts[1])
    except InvalidVersion as e:
        raise InvalidWheelFilename(
            f"Invalid wheel filename (invalid version): {filename}"
        ) from e

    if dashes == 5:
        build_part = parts[2]
        build_match = _build_tag_regex.match(build_part)
        if build_match is None:
            raise InvalidWheelFilename(
                f"Invalid build number: {build_part} in '{filename}'"
            )
        build = cast(BuildTag, (int(build_match.group(1)), build_match.group(2)))
    else:
        build = ()
    tags = parse_tag(parts[-1])
    return (name, version, build, tags)


def parse_sdist_filename(filename: str) -> Tuple[NormalizedName, Version]:
    if filename.endswith(".tar.gz"):
        file_stem = filename[: -len(".tar.gz")]
    elif filename.endswith(".zip"):
        file_stem = filename[: -len(".zip")]
    else:
        raise InvalidSdistFilename(
            f"Invalid sdist filename (extension must be '.tar.gz' or '.zip'):"
            f" {filename}"
        )

    # 044175.python.utils.line157.comment We are requiring a PEP 440 version, which cannot contain dashes,
    # 044176.python.utils.line158.comment so we split on the last dash.
    name_part, sep, version_part = file_stem.rpartition("-")
    if not sep:
        raise InvalidSdistFilename(f"Invalid sdist filename: {filename}")

    name = canonicalize_name(name_part)

    try:
        version = Version(version_part)
    except InvalidVersion as e:
        raise InvalidSdistFilename(
            f"Invalid sdist filename (invalid version): {filename}"
        ) from e

    return (name, version)
