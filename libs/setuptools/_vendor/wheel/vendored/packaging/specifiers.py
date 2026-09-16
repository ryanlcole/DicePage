# 043981.python.specifiers.line1.comment This file is dual licensed under the terms of the Apache License, Version
# 043982.python.specifiers.line2.comment 2.0, and the BSD License. See the LICENSE file in the root of this repository
# 043983.python.specifiers.line3.comment for complete details.
"""
.. testsetup::

    from packaging.specifiers import Specifier, SpecifierSet, InvalidSpecifier
    from packaging.version import Version
"""

import abc
import itertools
import re
from typing import Callable, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union

from .utils import canonicalize_version
from .version import Version

UnparsedVersion = Union[Version, str]
UnparsedVersionVar = TypeVar("UnparsedVersionVar", bound=UnparsedVersion)
CallableOperator = Callable[[Version, str], bool]


def _coerce_version(version: UnparsedVersion) -> Version:
    if not isinstance(version, Version):
        version = Version(version)
    return version


class InvalidSpecifier(ValueError):
    """
    Raised when attempting to create a :class:`Specifier` with a specifier
    string that is invalid.

    >>> Specifier("lolwat")
    Traceback (most recent call last):
        ...
    packaging.specifiers.InvalidSpecifier: Invalid specifier: 'lolwat'
    """


class BaseSpecifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __str__(self) -> str:
        """
        Returns the str representation of this Specifier-like object. This
        should be representative of the Specifier itself.
        """

    @abc.abstractmethod
    def __hash__(self) -> int:
        """
        Returns a hash value for this Specifier-like object.
        """

    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        Returns a boolean representing whether or not the two Specifier-like
        objects are equal.

        :param other: The other object to check against.
        """

    @property
    @abc.abstractmethod
    def prereleases(self) -> Optional[bool]:
        """Whether or not pre-releases as a whole are allowed.

        This can be set to either ``True`` or ``False`` to explicitly enable or disable
        prereleases or it can be set to ``None`` (the default) to use default semantics.
        """

    @prereleases.setter
    def prereleases(self, value: bool) -> None:
        """Setter for :attr:`prereleases`.

        :param value: The value to set.
        """

    @abc.abstractmethod
    def contains(self, item: str, prereleases: Optional[bool] = None) -> bool:
        """
        Determines if the given item is contained within this specifier.
        """

    @abc.abstractmethod
    def filter(
        self, iterable: Iterable[UnparsedVersionVar], prereleases: Optional[bool] = None
    ) -> Iterator[UnparsedVersionVar]:
        """
        Takes an iterable of items and filters them so that only items which
        are contained within this specifier are allowed in it.
        """


class Specifier(BaseSpecifier):
    """This class abstracts handling of version specifiers.

    .. tip::

        It is generally not required to instantiate this manually. You should instead
        prefer to work with :class:`SpecifierSet` instead, which can parse
        comma-separated version specifiers (which is what package metadata contains).
    """

    _operator_regex_str = r"""
        (?P<operator>(~=|==|!=|<=|>=|<|>|===))
        """
    _version_regex_str = r"""
        (?P<version>
            (?:
                # The identity operators allow for an escape hatch that will
                # do an exact string match of the version you wish to install.
                # This will not be parsed by PEP 440 and we cannot determine
                # any semantic meaning from it. This operator is discouraged
                # but included entirely as an escape hatch.
                (?<====)  # Only match for the identity operator
                \s*
                [^\s;)]*  # The arbitrary version can be just about anything,
                          # we match everything except for whitespace, a
                          # semi-colon for marker support, and a closing paren
                          # since versions can be enclosed in them.
            )
            |
            (?:
                # The (non)equality operators allow for wild card and local
                # versions to be specified so we have to define these two
                # operators separately to enable that.
                (?<===|!=)            # Only match for equals and not equals

                \s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\.[0-9]+)*   # release

                # You cannot use a wild card and a pre-release, post-release, a dev or
                # local version together so group them with a | and make them optional.
                (?:
                    \.\*  # Wild card syntax of .*
                    |
                    (?:                                  # pre release
                        [-_\.]?
                        (alpha|beta|preview|pre|a|b|c|rc)
                        [-_\.]?
                        [0-9]*
                    )?
                    (?:                                  # post release
                        (?:-[0-9]+)|(?:[-_\.]?(post|rev|r)[-_\.]?[0-9]*)
                    )?
                    (?:[-_\.]?dev[-_\.]?[0-9]*)?         # dev release
                    (?:\+[a-z0-9]+(?:[-_\.][a-z0-9]+)*)? # local
                )?
            )
            |
            (?:
                # The compatible operator requires at least two digits in the
                # release segment.
                (?<=~=)               # Only match for the compatible operator

                \s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\.[0-9]+)+   # release  (We have a + instead of a *)
                (?:                   # pre release
                    [-_\.]?
                    (alpha|beta|preview|pre|a|b|c|rc)
                    [-_\.]?
                    [0-9]*
                )?
                (?:                                   # post release
                    (?:-[0-9]+)|(?:[-_\.]?(post|rev|r)[-_\.]?[0-9]*)
                )?
                (?:[-_\.]?dev[-_\.]?[0-9]*)?          # dev release
            )
            |
            (?:
                # All other operators only allow a sub set of what the
                # (non)equality operators do. Specifically they do not allow
                # local versions to be specified nor do they allow the prefix
                # matching wild cards.
                (?<!==|!=|~=)         # We have special cases for these
                                      # operators so we want to make sure they
                                      # don't match here.

                \s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\.[0-9]+)*   # release
                (?:                   # pre release
                    [-_\.]?
                    (alpha|beta|preview|pre|a|b|c|rc)
                    [-_\.]?
                    [0-9]*
                )?
                (?:                                   # post release
                    (?:-[0-9]+)|(?:[-_\.]?(post|rev|r)[-_\.]?[0-9]*)
                )?
                (?:[-_\.]?dev[-_\.]?[0-9]*)?          # dev release
            )
        )
        """

    _regex = re.compile(
        r"^\s*" + _operator_regex_str + _version_regex_str + r"\s*$",
        re.VERBOSE | re.IGNORECASE,
    )

    _operators = {
        "~=": "compatible",
        "==": "equal",
        "!=": "not_equal",
        "<=": "less_than_equal",
        ">=": "greater_than_equal",
        "<": "less_than",
        ">": "greater_than",
        "===": "arbitrary",
    }

    def __init__(self, spec: str = "", prereleases: Optional[bool] = None) -> None:
        """Initialize a Specifier instance.

        :param spec:
            The string representation of a specifier which will be parsed and
            normalized before use.
        :param prereleases:
            This tells the specifier if it should accept prerelease versions if
            applicable or not. The default of ``None`` will autodetect it from the
            given specifiers.
        :raises InvalidSpecifier:
            If the given specifier is invalid (i.e. bad syntax).
        """
        match = self._regex.search(spec)
        if not match:
            raise InvalidSpecifier(f"Invalid specifier: '{spec}'")

        self._spec: Tuple[str, str] = (
            match.group("operator").strip(),
            match.group("version").strip(),
        )

        # 043984.python.specifiers.line242.comment Store whether or not this Specifier should accept prereleases
        self._prereleases = prereleases

    # 043985.python.specifiers.line245.comment https://github.com/python/mypy/pull/13475#pullrequestreview-1079784515
    @property  # type: ignore[override]
    def prereleases(self) -> bool:
        # 043987.python.specifiers.line248.comment If there is an explicit prereleases set for this, then we'll just
        # 043988.python.specifiers.line249.comment blindly use that.
        if self._prereleases is not None:
            return self._prereleases

        # 043989.python.specifiers.line253.comment Look at all of our specifiers and determine if they are inclusive
        # 043990.python.specifiers.line254.comment operators, and if they are if they are including an explicit
        # 043991.python.specifiers.line255.comment prerelease.
        operator, version = self._spec
        if operator in ["==", ">=", "<=", "~=", "==="]:
            # 043992.python.specifiers.line258.comment The == specifier can include a trailing .*, if it does we
            # 043993.python.specifiers.line259.comment want to remove before parsing.
            if operator == "==" and version.endswith(".*"):
                version = version[:-2]

            # 043994.python.specifiers.line263.comment Parse the version, and if it is a pre-release than this
            # 043995.python.specifiers.line264.comment specifier allows pre-releases.
            if Version(version).is_prerelease:
                return True

        return False

    @prereleases.setter
    def prereleases(self, value: bool) -> None:
        self._prereleases = value

    @property
    def operator(self) -> str:
        """The operator of this specifier.

        >>> Specifier("==1.2.3").operator
        '=='
        """
        return self._spec[0]

    @property
    def version(self) -> str:
        """The version of this specifier.

        >>> Specifier("==1.2.3").version
        '1.2.3'
        """
        return self._spec[1]

    def __repr__(self) -> str:
        """A representation of the Specifier that shows all internal state.

        >>> Specifier('>=1.0.0')
        <Specifier('>=1.0.0')>
        >>> Specifier('>=1.0.0', prereleases=False)
        <Specifier('>=1.0.0', prereleases=False)>
        >>> Specifier('>=1.0.0', prereleases=True)
        <Specifier('>=1.0.0', prereleases=True)>
        """
        pre = (
            f", prereleases={self.prereleases!r}"
            if self._prereleases is not None
            else ""
        )

        return f"<{self.__class__.__name__}({str(self)!r}{pre})>"

    def __str__(self) -> str:
        """A string representation of the Specifier that can be round-tripped.

        >>> str(Specifier('>=1.0.0'))
        '>=1.0.0'
        >>> str(Specifier('>=1.0.0', prereleases=False))
        '>=1.0.0'
        """
        return "{}{}".format(*self._spec)

    @property
    def _canonical_spec(self) -> Tuple[str, str]:
        canonical_version = canonicalize_version(
            self._spec[1],
            strip_trailing_zero=(self._spec[0] != "~="),
        )
        return self._spec[0], canonical_version

    def __hash__(self) -> int:
        return hash(self._canonical_spec)

    def __eq__(self, other: object) -> bool:
        """Whether or not the two Specifier-like objects are equal.

        :param other: The other object to check against.

        The value of :attr:`prereleases` is ignored.

        >>> Specifier("==1.2.3") == Specifier("== 1.2.3.0")
        True
        >>> (Specifier("==1.2.3", prereleases=False) ==
        ...  Specifier("==1.2.3", prereleases=True))
        True
        >>> Specifier("==1.2.3") == "==1.2.3"
        True
        >>> Specifier("==1.2.3") == Specifier("==1.2.4")
        False
        >>> Specifier("==1.2.3") == Specifier("~=1.2.3")
        False
        """
        if isinstance(other, str):
            try:
                other = self.__class__(str(other))
            except InvalidSpecifier:
                return NotImplemented
        elif not isinstance(other, self.__class__):
            return NotImplemented

        return self._canonical_spec == other._canonical_spec

    def _get_operator(self, op: str) -> CallableOperator:
        operator_callable: CallableOperator = getattr(
            self, f"_compare_{self._operators[op]}"
        )
        return operator_callable

    def _compare_compatible(self, prospective: Version, spec: str) -> bool:
        # 043996.python.specifiers.line367.comment Compatible releases have an equivalent combination of >= and ==. That
        # 043997.python.specifiers.line368.comment is that ~=2.2 is equivalent to >=2.2,==2.*. This allows us to
        # 043998.python.specifiers.line369.comment implement this in terms of the other specifiers instead of
        # 043999.python.specifiers.line370.comment implementing it ourselves. The only thing we need to do is construct
        # 044000.python.specifiers.line371.comment the other specifiers.

        # 044001.python.specifiers.line373.comment We want everything but the last item in the version, but we want to
        # 044002.python.specifiers.line374.comment ignore suffix segments.
        prefix = _version_join(
            list(itertools.takewhile(_is_not_suffix, _version_split(spec)))[:-1]
        )

        # 044003.python.specifiers.line379.comment Add the prefix notation to the end of our string
        prefix += ".*"

        return self._get_operator(">=")(prospective, spec) and self._get_operator("==")(
            prospective, prefix
        )

    def _compare_equal(self, prospective: Version, spec: str) -> bool:
        # 044004.python.specifiers.line387.comment We need special logic to handle prefix matching
        if spec.endswith(".*"):
            # 044005.python.specifiers.line389.comment In the case of prefix matching we want to ignore local segment.
            normalized_prospective = canonicalize_version(
                prospective.public, strip_trailing_zero=False
            )
            # 044006.python.specifiers.line393.comment Get the normalized version string ignoring the trailing .*
            normalized_spec = canonicalize_version(spec[:-2], strip_trailing_zero=False)
            # 044007.python.specifiers.line395.comment Split the spec out by bangs and dots, and pretend that there is
            # 044008.python.specifiers.line396.comment an implicit dot in between a release segment and a pre-release segment.
            split_spec = _version_split(normalized_spec)

            # 044009.python.specifiers.line399.comment Split the prospective version out by bangs and dots, and pretend
            # 044010.python.specifiers.line400.comment that there is an implicit dot in between a release segment and
            # 044011.python.specifiers.line401.comment a pre-release segment.
            split_prospective = _version_split(normalized_prospective)

            # 044012.python.specifiers.line404.comment 0-pad the prospective version before shortening it to get the correct
            # 044013.python.specifiers.line405.comment shortened version.
            padded_prospective, _ = _pad_version(split_prospective, split_spec)

            # 044014.python.specifiers.line408.comment Shorten the prospective version to be the same length as the spec
            # 044015.python.specifiers.line409.comment so that we can determine if the specifier is a prefix of the
            # 044016.python.specifiers.line410.comment prospective version or not.
            shortened_prospective = padded_prospective[: len(split_spec)]

            return shortened_prospective == split_spec
        else:
            # 044017.python.specifiers.line415.comment Convert our spec string into a Version
            spec_version = Version(spec)

            # 044018.python.specifiers.line418.comment If the specifier does not have a local segment, then we want to
            # 044019.python.specifiers.line419.comment act as if the prospective version also does not have a local
            # 044020.python.specifiers.line420.comment segment.
            if not spec_version.local:
                prospective = Version(prospective.public)

            return prospective == spec_version

    def _compare_not_equal(self, prospective: Version, spec: str) -> bool:
        return not self._compare_equal(prospective, spec)

    def _compare_less_than_equal(self, prospective: Version, spec: str) -> bool:
        # 044021.python.specifiers.line430.comment NB: Local version identifiers are NOT permitted in the version
        # 044022.python.specifiers.line431.comment specifier, so local version labels can be universally removed from
        # 044023.python.specifiers.line432.comment the prospective version.
        return Version(prospective.public) <= Version(spec)

    def _compare_greater_than_equal(self, prospective: Version, spec: str) -> bool:
        # 044024.python.specifiers.line436.comment NB: Local version identifiers are NOT permitted in the version
        # 044025.python.specifiers.line437.comment specifier, so local version labels can be universally removed from
        # 044026.python.specifiers.line438.comment the prospective version.
        return Version(prospective.public) >= Version(spec)

    def _compare_less_than(self, prospective: Version, spec_str: str) -> bool:
        # 044027.python.specifiers.line442.comment Convert our spec to a Version instance, since we'll want to work with
        # 044028.python.specifiers.line443.comment it as a version.
        spec = Version(spec_str)

        # 044029.python.specifiers.line446.comment Check to see if the prospective version is less than the spec
        # 044030.python.specifiers.line447.comment version. If it's not we can short circuit and just return False now
        # 044031.python.specifiers.line448.comment instead of doing extra unneeded work.
        if not prospective < spec:
            return False

        # 044032.python.specifiers.line452.comment This special case is here so that, unless the specifier itself
        # 044033.python.specifiers.line453.comment includes is a pre-release version, that we do not accept pre-release
        # 044034.python.specifiers.line454.comment versions for the version mentioned in the specifier (e.g. <3.1 should
        # 044035.python.specifiers.line455.comment not match 3.1.dev0, but should match 3.0.dev0).
        if not spec.is_prerelease and prospective.is_prerelease:
            if Version(prospective.base_version) == Version(spec.base_version):
                return False

        # 044036.python.specifiers.line460.comment If we've gotten to here, it means that prospective version is both
        # 044037.python.specifiers.line461.comment less than the spec version *and* it's not a pre-release of the same
        # 044038.python.specifiers.line462.comment version in the spec.
        return True

    def _compare_greater_than(self, prospective: Version, spec_str: str) -> bool:
        # 044039.python.specifiers.line466.comment Convert our spec to a Version instance, since we'll want to work with
        # 044040.python.specifiers.line467.comment it as a version.
        spec = Version(spec_str)

        # 044041.python.specifiers.line470.comment Check to see if the prospective version is greater than the spec
        # 044042.python.specifiers.line471.comment version. If it's not we can short circuit and just return False now
        # 044043.python.specifiers.line472.comment instead of doing extra unneeded work.
        if not prospective > spec:
            return False

        # 044044.python.specifiers.line476.comment This special case is here so that, unless the specifier itself
        # 044045.python.specifiers.line477.comment includes is a post-release version, that we do not accept
        # 044046.python.specifiers.line478.comment post-release versions for the version mentioned in the specifier
        # 044047.python.specifiers.line479.comment (e.g. >3.1 should not match 3.0.post0, but should match 3.2.post0).
        if not spec.is_postrelease and prospective.is_postrelease:
            if Version(prospective.base_version) == Version(spec.base_version):
                return False

        # 044048.python.specifiers.line484.comment Ensure that we do not allow a local version of the version mentioned
        # 044049.python.specifiers.line485.comment in the specifier, which is technically greater than, to match.
        if prospective.local is not None:
            if Version(prospective.base_version) == Version(spec.base_version):
                return False

        # 044050.python.specifiers.line490.comment If we've gotten to here, it means that prospective version is both
        # 044051.python.specifiers.line491.comment greater than the spec version *and* it's not a pre-release of the
        # 044052.python.specifiers.line492.comment same version in the spec.
        return True

    def _compare_arbitrary(self, prospective: Version, spec: str) -> bool:
        return str(prospective).lower() == str(spec).lower()

    def __contains__(self, item: Union[str, Version]) -> bool:
        """Return whether or not the item is contained in this specifier.

        :param item: The item to check for.

        This is used for the ``in`` operator and behaves the same as
        :meth:`contains` with no ``prereleases`` argument passed.

        >>> "1.2.3" in Specifier(">=1.2.3")
        True
        >>> Version("1.2.3") in Specifier(">=1.2.3")
        True
        >>> "1.0.0" in Specifier(">=1.2.3")
        False
        >>> "1.3.0a1" in Specifier(">=1.2.3")
        False
        >>> "1.3.0a1" in Specifier(">=1.2.3", prereleases=True)
        True
        """
        return self.contains(item)

    def contains(
        self, item: UnparsedVersion, prereleases: Optional[bool] = None
    ) -> bool:
        """Return whether or not the item is contained in this specifier.

        :param item:
            The item to check for, which can be a version string or a
            :class:`Version` instance.
        :param prereleases:
            Whether or not to match prereleases with this Specifier. If set to
            ``None`` (the default), it uses :attr:`prereleases` to determine
            whether or not prereleases are allowed.

        >>> Specifier(">=1.2.3").contains("1.2.3")
        True
        >>> Specifier(">=1.2.3").contains(Version("1.2.3"))
        True
        >>> Specifier(">=1.2.3").contains("1.0.0")
        False
        >>> Specifier(">=1.2.3").contains("1.3.0a1")
        False
        >>> Specifier(">=1.2.3", prereleases=True).contains("1.3.0a1")
        True
        >>> Specifier(">=1.2.3").contains("1.3.0a1", prereleases=True)
        True
        """

        # 044053.python.specifiers.line546.comment Determine if prereleases are to be allowed or not.
        if prereleases is None:
            prereleases = self.prereleases

        # 044054.python.specifiers.line550.comment Normalize item to a Version, this allows us to have a shortcut for
        # 044055.python.specifiers.line551.comment "2.0" in Specifier(">=2")
        normalized_item = _coerce_version(item)

        # 044056.python.specifiers.line554.comment Determine if we should be supporting prereleases in this specifier
        # 044057.python.specifiers.line555.comment or not, if we do not support prereleases than we can short circuit
        # 044058.python.specifiers.line556.comment logic if this version is a prereleases.
        if normalized_item.is_prerelease and not prereleases:
            return False

        # 044059.python.specifiers.line560.comment Actually do the comparison to determine if this item is contained
        # 044060.python.specifiers.line561.comment within this Specifier or not.
        operator_callable: CallableOperator = self._get_operator(self.operator)
        return operator_callable(normalized_item, self.version)

    def filter(
        self, iterable: Iterable[UnparsedVersionVar], prereleases: Optional[bool] = None
    ) -> Iterator[UnparsedVersionVar]:
        """Filter items in the given iterable, that match the specifier.

        :param iterable:
            An iterable that can contain version strings and :class:`Version` instances.
            The items in the iterable will be filtered according to the specifier.
        :param prereleases:
            Whether or not to allow prereleases in the returned iterator. If set to
            ``None`` (the default), it will be intelligently decide whether to allow
            prereleases or not (based on the :attr:`prereleases` attribute, and
            whether the only versions matching are prereleases).

        This method is smarter than just ``filter(Specifier().contains, [...])``
        because it implements the rule from :pep:`440` that a prerelease item
        SHOULD be accepted if no other versions match the given specifier.

        >>> list(Specifier(">=1.2.3").filter(["1.2", "1.3", "1.5a1"]))
        ['1.3']
        >>> list(Specifier(">=1.2.3").filter(["1.2", "1.2.3", "1.3", Version("1.4")]))
        ['1.2.3', '1.3', <Version('1.4')>]
        >>> list(Specifier(">=1.2.3").filter(["1.2", "1.5a1"]))
        ['1.5a1']
        >>> list(Specifier(">=1.2.3").filter(["1.3", "1.5a1"], prereleases=True))
        ['1.3', '1.5a1']
        >>> list(Specifier(">=1.2.3", prereleases=True).filter(["1.3", "1.5a1"]))
        ['1.3', '1.5a1']
        """

        yielded = False
        found_prereleases = []

        kw = {"prereleases": prereleases if prereleases is not None else True}

        # 044061.python.specifiers.line600.comment Attempt to iterate over all the values in the iterable and if any of
        # 044062.python.specifiers.line601.comment them match, yield them.
        for version in iterable:
            parsed_version = _coerce_version(version)

            if self.contains(parsed_version, **kw):
                # 044063.python.specifiers.line606.comment If our version is a prerelease, and we were not set to allow
                # 044064.python.specifiers.line607.comment prereleases, then we'll store it for later in case nothing
                # 044065.python.specifiers.line608.comment else matches this specifier.
                if parsed_version.is_prerelease and not (
                    prereleases or self.prereleases
                ):
                    found_prereleases.append(version)
                # 044066.python.specifiers.line613.comment Either this is not a prerelease, or we should have been
                # 044067.python.specifiers.line614.comment accepting prereleases from the beginning.
                else:
                    yielded = True
                    yield version

        # 044068.python.specifiers.line619.comment Now that we've iterated over everything, determine if we've yielded
        # 044069.python.specifiers.line620.comment any values, and if we have not and we have any prereleases stored up
        # 044070.python.specifiers.line621.comment then we will go ahead and yield the prereleases.
        if not yielded and found_prereleases:
            for version in found_prereleases:
                yield version


_prefix_regex = re.compile(r"^([0-9]+)((?:a|b|c|rc)[0-9]+)$")


def _version_split(version: str) -> List[str]:
    """Split version into components.

    The split components are intended for version comparison. The logic does
    not attempt to retain the original version string, so joining the
    components back with :func:`_version_join` may not produce the original
    version string.
    """
    result: List[str] = []

    epoch, _, rest = version.rpartition("!")
    result.append(epoch or "0")

    for item in rest.split("."):
        match = _prefix_regex.search(item)
        if match:
            result.extend(match.groups())
        else:
            result.append(item)
    return result


def _version_join(components: List[str]) -> str:
    """Join split version components into a version string.

    This function assumes the input came from :func:`_version_split`, where the
    first component must be the epoch (either empty or numeric), and all other
    components numeric.
    """
    epoch, *rest = components
    return f"{epoch}!{'.'.join(rest)}"


def _is_not_suffix(segment: str) -> bool:
    return not any(
        segment.startswith(prefix) for prefix in ("dev", "a", "b", "rc", "post")
    )


def _pad_version(left: List[str], right: List[str]) -> Tuple[List[str], List[str]]:
    left_split, right_split = [], []

    # 044071.python.specifiers.line672.comment Get the release segment of our versions
    left_split.append(list(itertools.takewhile(lambda x: x.isdigit(), left)))
    right_split.append(list(itertools.takewhile(lambda x: x.isdigit(), right)))

    # 044072.python.specifiers.line676.comment Get the rest of our versions
    left_split.append(left[len(left_split[0]) :])
    right_split.append(right[len(right_split[0]) :])

    # 044073.python.specifiers.line680.comment Insert our padding
    left_split.insert(1, ["0"] * max(0, len(right_split[0]) - len(left_split[0])))
    right_split.insert(1, ["0"] * max(0, len(left_split[0]) - len(right_split[0])))

    return (
        list(itertools.chain.from_iterable(left_split)),
        list(itertools.chain.from_iterable(right_split)),
    )


class SpecifierSet(BaseSpecifier):
    """This class abstracts handling of a set of version specifiers.

    It can be passed a single specifier (``>=3.0``), a comma-separated list of
    specifiers (``>=3.0,!=3.1``), or no specifier at all.
    """

    def __init__(
        self, specifiers: str = "", prereleases: Optional[bool] = None
    ) -> None:
        """Initialize a SpecifierSet instance.

        :param specifiers:
            The string representation of a specifier or a comma-separated list of
            specifiers which will be parsed and normalized before use.
        :param prereleases:
            This tells the SpecifierSet if it should accept prerelease versions if
            applicable or not. The default of ``None`` will autodetect it from the
            given specifiers.

        :raises InvalidSpecifier:
            If the given ``specifiers`` are not parseable than this exception will be
            raised.
        """

        # 044074.python.specifiers.line715.comment Split on `,` to break each individual specifier into it's own item, and
        # 044075.python.specifiers.line716.comment strip each item to remove leading/trailing whitespace.
        split_specifiers = [s.strip() for s in specifiers.split(",") if s.strip()]

        # 044076.python.specifiers.line719.comment Make each individual specifier a Specifier and save in a frozen set for later.
        self._specs = frozenset(map(Specifier, split_specifiers))

        # 044077.python.specifiers.line722.comment Store our prereleases value so we can use it later to determine if
        # 044078.python.specifiers.line723.comment we accept prereleases or not.
        self._prereleases = prereleases

    @property
    def prereleases(self) -> Optional[bool]:
        # 044079.python.specifiers.line728.comment If we have been given an explicit prerelease modifier, then we'll
        # 044080.python.specifiers.line729.comment pass that through here.
        if self._prereleases is not None:
            return self._prereleases

        # 044081.python.specifiers.line733.comment If we don't have any specifiers, and we don't have a forced value,
        # 044082.python.specifiers.line734.comment then we'll just return None since we don't know if this should have
        # 044083.python.specifiers.line735.comment pre-releases or not.
        if not self._specs:
            return None

        # 044084.python.specifiers.line739.comment Otherwise we'll see if any of the given specifiers accept
        # 044085.python.specifiers.line740.comment prereleases, if any of them do we'll return True, otherwise False.
        return any(s.prereleases for s in self._specs)

    @prereleases.setter
    def prereleases(self, value: bool) -> None:
        self._prereleases = value

    def __repr__(self) -> str:
        """A representation of the specifier set that shows all internal state.

        Note that the ordering of the individual specifiers within the set may not
        match the input string.

        >>> SpecifierSet('>=1.0.0,!=2.0.0')
        <SpecifierSet('!=2.0.0,>=1.0.0')>
        >>> SpecifierSet('>=1.0.0,!=2.0.0', prereleases=False)
        <SpecifierSet('!=2.0.0,>=1.0.0', prereleases=False)>
        >>> SpecifierSet('>=1.0.0,!=2.0.0', prereleases=True)
        <SpecifierSet('!=2.0.0,>=1.0.0', prereleases=True)>
        """
        pre = (
            f", prereleases={self.prereleases!r}"
            if self._prereleases is not None
            else ""
        )

        return f"<SpecifierSet({str(self)!r}{pre})>"

    def __str__(self) -> str:
        """A string representation of the specifier set that can be round-tripped.

        Note that the ordering of the individual specifiers within the set may not
        match the input string.

        >>> str(SpecifierSet(">=1.0.0,!=1.0.1"))
        '!=1.0.1,>=1.0.0'
        >>> str(SpecifierSet(">=1.0.0,!=1.0.1", prereleases=False))
        '!=1.0.1,>=1.0.0'
        """
        return ",".join(sorted(str(s) for s in self._specs))

    def __hash__(self) -> int:
        return hash(self._specs)

    def __and__(self, other: Union["SpecifierSet", str]) -> "SpecifierSet":
        """Return a SpecifierSet which is a combination of the two sets.

        :param other: The other object to combine with.

        >>> SpecifierSet(">=1.0.0,!=1.0.1") & '<=2.0.0,!=2.0.1'
        <SpecifierSet('!=1.0.1,!=2.0.1,<=2.0.0,>=1.0.0')>
        >>> SpecifierSet(">=1.0.0,!=1.0.1") & SpecifierSet('<=2.0.0,!=2.0.1')
        <SpecifierSet('!=1.0.1,!=2.0.1,<=2.0.0,>=1.0.0')>
        """
        if isinstance(other, str):
            other = SpecifierSet(other)
        elif not isinstance(other, SpecifierSet):
            return NotImplemented

        specifier = SpecifierSet()
        specifier._specs = frozenset(self._specs | other._specs)

        if self._prereleases is None and other._prereleases is not None:
            specifier._prereleases = other._prereleases
        elif self._prereleases is not None and other._prereleases is None:
            specifier._prereleases = self._prereleases
        elif self._prereleases == other._prereleases:
            specifier._prereleases = self._prereleases
        else:
            raise ValueError(
                "Cannot combine SpecifierSets with True and False prerelease "
                "overrides."
            )

        return specifier

    def __eq__(self, other: object) -> bool:
        """Whether or not the two SpecifierSet-like objects are equal.

        :param other: The other object to check against.

        The value of :attr:`prereleases` is ignored.

        >>> SpecifierSet(">=1.0.0,!=1.0.1") == SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> (SpecifierSet(">=1.0.0,!=1.0.1", prereleases=False) ==
        ...  SpecifierSet(">=1.0.0,!=1.0.1", prereleases=True))
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1") == ">=1.0.0,!=1.0.1"
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1") == SpecifierSet(">=1.0.0")
        False
        >>> SpecifierSet(">=1.0.0,!=1.0.1") == SpecifierSet(">=1.0.0,!=1.0.2")
        False
        """
        if isinstance(other, (str, Specifier)):
            other = SpecifierSet(str(other))
        elif not isinstance(other, SpecifierSet):
            return NotImplemented

        return self._specs == other._specs

    def __len__(self) -> int:
        """Returns the number of specifiers in this specifier set."""
        return len(self._specs)

    def __iter__(self) -> Iterator[Specifier]:
        """
        Returns an iterator over all the underlying :class:`Specifier` instances
        in this specifier set.

        >>> sorted(SpecifierSet(">=1.0.0,!=1.0.1"), key=str)
        [<Specifier('!=1.0.1')>, <Specifier('>=1.0.0')>]
        """
        return iter(self._specs)

    def __contains__(self, item: UnparsedVersion) -> bool:
        """Return whether or not the item is contained in this specifier.

        :param item: The item to check for.

        This is used for the ``in`` operator and behaves the same as
        :meth:`contains` with no ``prereleases`` argument passed.

        >>> "1.2.3" in SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> Version("1.2.3") in SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> "1.0.1" in SpecifierSet(">=1.0.0,!=1.0.1")
        False
        >>> "1.3.0a1" in SpecifierSet(">=1.0.0,!=1.0.1")
        False
        >>> "1.3.0a1" in SpecifierSet(">=1.0.0,!=1.0.1", prereleases=True)
        True
        """
        return self.contains(item)

    def contains(
        self,
        item: UnparsedVersion,
        prereleases: Optional[bool] = None,
        installed: Optional[bool] = None,
    ) -> bool:
        """Return whether or not the item is contained in this SpecifierSet.

        :param item:
            The item to check for, which can be a version string or a
            :class:`Version` instance.
        :param prereleases:
            Whether or not to match prereleases with this SpecifierSet. If set to
            ``None`` (the default), it uses :attr:`prereleases` to determine
            whether or not prereleases are allowed.

        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.2.3")
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains(Version("1.2.3"))
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.0.1")
        False
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.3.0a1")
        False
        >>> SpecifierSet(">=1.0.0,!=1.0.1", prereleases=True).contains("1.3.0a1")
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.3.0a1", prereleases=True)
        True
        """
        # 044086.python.specifiers.line906.comment Ensure that our item is a Version instance.
        if not isinstance(item, Version):
            item = Version(item)

        # 044087.python.specifiers.line910.comment Determine if we're forcing a prerelease or not, if we're not forcing
        # 044088.python.specifiers.line911.comment one for this particular filter call, then we'll use whatever the
        # 044089.python.specifiers.line912.comment SpecifierSet thinks for whether or not we should support prereleases.
        if prereleases is None:
            prereleases = self.prereleases

        # 044090.python.specifiers.line916.comment We can determine if we're going to allow pre-releases by looking to
        # 044091.python.specifiers.line917.comment see if any of the underlying items supports them. If none of them do
        # 044092.python.specifiers.line918.comment and this item is a pre-release then we do not allow it and we can
        # 044093.python.specifiers.line919.comment short circuit that here.
        # 044094.python.specifiers.line920.comment Note: This means that 1.0.dev1 would not be contained in something
        # 044095.python.specifiers.line921.comment like >=1.0.devabc however it would be in >=1.0.debabc,>0.0.dev0
        if not prereleases and item.is_prerelease:
            return False

        if installed and item.is_prerelease:
            item = Version(item.base_version)

        # 044096.python.specifiers.line928.comment We simply dispatch to the underlying specs here to make sure that the
        # 044097.python.specifiers.line929.comment given version is contained within all of them.
        # 044098.python.specifiers.line930.comment Note: This use of all() here means that an empty set of specifiers
        # 044099.python.specifiers.line931.comment will always return True, this is an explicit design decision.
        return all(s.contains(item, prereleases=prereleases) for s in self._specs)

    def filter(
        self, iterable: Iterable[UnparsedVersionVar], prereleases: Optional[bool] = None
    ) -> Iterator[UnparsedVersionVar]:
        """Filter items in the given iterable, that match the specifiers in this set.

        :param iterable:
            An iterable that can contain version strings and :class:`Version` instances.
            The items in the iterable will be filtered according to the specifier.
        :param prereleases:
            Whether or not to allow prereleases in the returned iterator. If set to
            ``None`` (the default), it will be intelligently decide whether to allow
            prereleases or not (based on the :attr:`prereleases` attribute, and
            whether the only versions matching are prereleases).

        This method is smarter than just ``filter(SpecifierSet(...).contains, [...])``
        because it implements the rule from :pep:`440` that a prerelease item
        SHOULD be accepted if no other versions match the given specifier.

        >>> list(SpecifierSet(">=1.2.3").filter(["1.2", "1.3", "1.5a1"]))
        ['1.3']
        >>> list(SpecifierSet(">=1.2.3").filter(["1.2", "1.3", Version("1.4")]))
        ['1.3', <Version('1.4')>]
        >>> list(SpecifierSet(">=1.2.3").filter(["1.2", "1.5a1"]))
        []
        >>> list(SpecifierSet(">=1.2.3").filter(["1.3", "1.5a1"], prereleases=True))
        ['1.3', '1.5a1']
        >>> list(SpecifierSet(">=1.2.3", prereleases=True).filter(["1.3", "1.5a1"]))
        ['1.3', '1.5a1']

        An "empty" SpecifierSet will filter items based on the presence of prerelease
        versions in the set.

        >>> list(SpecifierSet("").filter(["1.3", "1.5a1"]))
        ['1.3']
        >>> list(SpecifierSet("").filter(["1.5a1"]))
        ['1.5a1']
        >>> list(SpecifierSet("", prereleases=True).filter(["1.3", "1.5a1"]))
        ['1.3', '1.5a1']
        >>> list(SpecifierSet("").filter(["1.3", "1.5a1"], prereleases=True))
        ['1.3', '1.5a1']
        """
        # 044100.python.specifiers.line975.comment Determine if we're forcing a prerelease or not, if we're not forcing
        # 044101.python.specifiers.line976.comment one for this particular filter call, then we'll use whatever the
        # 044102.python.specifiers.line977.comment SpecifierSet thinks for whether or not we should support prereleases.
        if prereleases is None:
            prereleases = self.prereleases

        # 044103.python.specifiers.line981.comment If we have any specifiers, then we want to wrap our iterable in the
        # 044104.python.specifiers.line982.comment filter method for each one, this will act as a logical AND amongst
        # 044105.python.specifiers.line983.comment each specifier.
        if self._specs:
            for spec in self._specs:
                iterable = spec.filter(iterable, prereleases=bool(prereleases))
            return iter(iterable)
        # 044106.python.specifiers.line988.comment If we do not have any specifiers, then we need to have a rough filter
        # 044107.python.specifiers.line989.comment which will filter out any pre-releases, unless there are no final
        # 044108.python.specifiers.line990.comment releases.
        else:
            filtered: List[UnparsedVersionVar] = []
            found_prereleases: List[UnparsedVersionVar] = []

            for item in iterable:
                parsed_version = _coerce_version(item)

                # 044109.python.specifiers.line998.comment Store any item which is a pre-release for later unless we've
                # 044110.python.specifiers.line999.comment already found a final version or we are accepting prereleases
                if parsed_version.is_prerelease and not prereleases:
                    if not filtered:
                        found_prereleases.append(item)
                else:
                    filtered.append(item)

            # 044111.python.specifiers.line1006.comment If we've found no items except for pre-releases, then we'll go
            # 044112.python.specifiers.line1007.comment ahead and use the pre-releases
            if not filtered and found_prereleases and prereleases is None:
                return iter(found_prereleases)

            return iter(filtered)
