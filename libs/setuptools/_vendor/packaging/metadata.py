from __future__ import annotations

import email.feedparser
import email.header
import email.message
import email.parser
import email.policy
import pathlib
import sys
import typing
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    TypedDict,
    cast,
)

from . import licenses, requirements, specifiers, utils
from . import version as version_module
from .licenses import NormalizedLicenseExpression

T = typing.TypeVar("T")


if sys.version_info >= (3, 11):  # pragma: no cover
    ExceptionGroup = ExceptionGroup
else:  # pragma: no cover

    class ExceptionGroup(Exception):
        """A minimal implementation of :external:exc:`ExceptionGroup` from Python 3.11.

        If :external:exc:`ExceptionGroup` is already defined by Python itself,
        that version is used instead.
        """

        message: str
        exceptions: list[Exception]

        def __init__(self, message: str, exceptions: list[Exception]) -> None:
            self.message = message
            self.exceptions = exceptions

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.message!r}, {self.exceptions!r})"


class InvalidMetadata(ValueError):
    """A metadata field contains invalid data."""

    field: str
    """The name of the field that contains invalid data."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(message)


# 042724.python.metadata.line60.comment The RawMetadata class attempts to make as few assumptions about the underlying
# 042725.python.metadata.line61.comment serialization formats as possible. The idea is that as long as a serialization
# 042726.python.metadata.line62.comment formats offer some very basic primitives in *some* way then we can support
# 042727.python.metadata.line63.comment serializing to and from that format.
class RawMetadata(TypedDict, total=False):
    """A dictionary of raw core metadata.

    Each field in core metadata maps to a key of this dictionary (when data is
    provided). The key is lower-case and underscores are used instead of dashes
    compared to the equivalent core metadata field. Any core metadata field that
    can be specified multiple times or can hold multiple values in a single
    field have a key with a plural name. See :class:`Metadata` whose attributes
    match the keys of this dictionary.

    Core metadata fields that can be specified multiple times are stored as a
    list or dict depending on which is appropriate for the field. Any fields
    which hold multiple values in a single field are stored as a list.

    """

    # 042728.python.metadata.line80.comment Metadata 1.0 - PEP 241
    metadata_version: str
    name: str
    version: str
    platforms: list[str]
    summary: str
    description: str
    keywords: list[str]
    home_page: str
    author: str
    author_email: str
    license: str

    # 042729.python.metadata.line93.comment Metadata 1.1 - PEP 314
    supported_platforms: list[str]
    download_url: str
    classifiers: list[str]
    requires: list[str]
    provides: list[str]
    obsoletes: list[str]

    # 042730.python.metadata.line101.comment Metadata 1.2 - PEP 345
    maintainer: str
    maintainer_email: str
    requires_dist: list[str]
    provides_dist: list[str]
    obsoletes_dist: list[str]
    requires_python: str
    requires_external: list[str]
    project_urls: dict[str, str]

    # 042731.python.metadata.line111.comment Metadata 2.0
    # 042732.python.metadata.line112.comment PEP 426 attempted to completely revamp the metadata format
    # 042733.python.metadata.line113.comment but got stuck without ever being able to build consensus on
    # 042734.python.metadata.line114.comment it and ultimately ended up withdrawn.
    # 042735.python.metadata.line115.comment
    # 042736.python.metadata.line116.comment However, a number of tools had started emitting METADATA with
    # 042737.python.metadata.line117.comment `2.0` Metadata-Version, so for historical reasons, this version
    # 042738.python.metadata.line118.comment was skipped.

    # 042739.python.metadata.line120.comment Metadata 2.1 - PEP 566
    description_content_type: str
    provides_extra: list[str]

    # 042740.python.metadata.line124.comment Metadata 2.2 - PEP 643
    dynamic: list[str]

    # 042741.python.metadata.line127.comment Metadata 2.3 - PEP 685
    # 042742.python.metadata.line128.comment No new fields were added in PEP 685, just some edge case were
    # 042743.python.metadata.line129.comment tightened up to provide better interoptability.

    # 042744.python.metadata.line131.comment Metadata 2.4 - PEP 639
    license_expression: str
    license_files: list[str]


_STRING_FIELDS = {
    "author",
    "author_email",
    "description",
    "description_content_type",
    "download_url",
    "home_page",
    "license",
    "license_expression",
    "maintainer",
    "maintainer_email",
    "metadata_version",
    "name",
    "requires_python",
    "summary",
    "version",
}

_LIST_FIELDS = {
    "classifiers",
    "dynamic",
    "license_files",
    "obsoletes",
    "obsoletes_dist",
    "platforms",
    "provides",
    "provides_dist",
    "provides_extra",
    "requires",
    "requires_dist",
    "requires_external",
    "supported_platforms",
}

_DICT_FIELDS = {
    "project_urls",
}


def _parse_keywords(data: str) -> list[str]:
    """Split a string of comma-separated keywords into a list of keywords."""
    return [k.strip() for k in data.split(",")]


def _parse_project_urls(data: list[str]) -> dict[str, str]:
    """Parse a list of label/URL string pairings separated by a comma."""
    urls = {}
    for pair in data:
        # 042745.python.metadata.line184.comment Our logic is slightly tricky here as we want to try and do
        # 042746.python.metadata.line185.comment *something* reasonable with malformed data.
        # 042747.python.metadata.line186.comment
        # 042748.python.metadata.line187.comment The main thing that we have to worry about, is data that does
        # 042749.python.metadata.line188.comment not have a ',' at all to split the label from the Value. There
        # 042750.python.metadata.line189.comment isn't a singular right answer here, and we will fail validation
        # 042751.python.metadata.line190.comment later on (if the caller is validating) so it doesn't *really*
        # 042752.python.metadata.line191.comment matter, but since the missing value has to be an empty str
        # 042753.python.metadata.line192.comment and our return value is dict[str, str], if we let the key
        # 042754.python.metadata.line193.comment be the missing value, then they'd have multiple '' values that
        # 042755.python.metadata.line194.comment overwrite each other in a accumulating dict.
        # 042756.python.metadata.line195.comment
        # 042757.python.metadata.line196.comment The other potentional issue is that it's possible to have the
        # 042758.python.metadata.line197.comment same label multiple times in the metadata, with no solid "right"
        # 042759.python.metadata.line198.comment answer with what to do in that case. As such, we'll do the only
        # 042760.python.metadata.line199.comment thing we can, which is treat the field as unparseable and add it
        # 042761.python.metadata.line200.comment to our list of unparsed fields.
        parts = [p.strip() for p in pair.split(",", 1)]
        parts.extend([""] * (max(0, 2 - len(parts))))  # Ensure 2 items

        # 042763.python.metadata.line204.comment TODO: The spec doesn't say anything about if the keys should be
        # 042764.python.metadata.line205.comment considered case sensitive or not... logically they should
        # 042765.python.metadata.line206.comment be case-preserving and case-insensitive, but doing that
        # 042766.python.metadata.line207.comment would open up more cases where we might have duplicate
        # 042767.python.metadata.line208.comment entries.
        label, url = parts
        if label in urls:
            # 042768.python.metadata.line211.comment The label already exists in our set of urls, so this field
            # 042769.python.metadata.line212.comment is unparseable, and we can just add the whole thing to our
            # 042770.python.metadata.line213.comment unparseable data and stop processing it.
            raise KeyError("duplicate labels in project urls")
        urls[label] = url

    return urls


def _get_payload(msg: email.message.Message, source: bytes | str) -> str:
    """Get the body of the message."""
    # 042771.python.metadata.line222.comment If our source is a str, then our caller has managed encodings for us,
    # 042772.python.metadata.line223.comment and we don't need to deal with it.
    if isinstance(source, str):
        payload = msg.get_payload()
        assert isinstance(payload, str)
        return payload
    # 042773.python.metadata.line228.comment If our source is a bytes, then we're managing the encoding and we need
    # 042774.python.metadata.line229.comment to deal with it.
    else:
        bpayload = msg.get_payload(decode=True)
        assert isinstance(bpayload, bytes)
        try:
            return bpayload.decode("utf8", "strict")
        except UnicodeDecodeError as exc:
            raise ValueError("payload in an invalid encoding") from exc


# 042775.python.metadata.line239.comment The various parse_FORMAT functions here are intended to be as lenient as
# 042776.python.metadata.line240.comment possible in their parsing, while still returning a correctly typed
# 042777.python.metadata.line241.comment RawMetadata.
# 042778.python.metadata.line242.comment
# 042779.python.metadata.line243.comment To aid in this, we also generally want to do as little touching of the
# 042780.python.metadata.line244.comment data as possible, except where there are possibly some historic holdovers
# 042781.python.metadata.line245.comment that make valid data awkward to work with.
# 042782.python.metadata.line246.comment
# 042783.python.metadata.line247.comment While this is a lower level, intermediate format than our ``Metadata``
# 042784.python.metadata.line248.comment class, some light touch ups can make a massive difference in usability.

# 042785.python.metadata.line250.comment Map METADATA fields to RawMetadata.
_EMAIL_TO_RAW_MAPPING = {
    "author": "author",
    "author-email": "author_email",
    "classifier": "classifiers",
    "description": "description",
    "description-content-type": "description_content_type",
    "download-url": "download_url",
    "dynamic": "dynamic",
    "home-page": "home_page",
    "keywords": "keywords",
    "license": "license",
    "license-expression": "license_expression",
    "license-file": "license_files",
    "maintainer": "maintainer",
    "maintainer-email": "maintainer_email",
    "metadata-version": "metadata_version",
    "name": "name",
    "obsoletes": "obsoletes",
    "obsoletes-dist": "obsoletes_dist",
    "platform": "platforms",
    "project-url": "project_urls",
    "provides": "provides",
    "provides-dist": "provides_dist",
    "provides-extra": "provides_extra",
    "requires": "requires",
    "requires-dist": "requires_dist",
    "requires-external": "requires_external",
    "requires-python": "requires_python",
    "summary": "summary",
    "supported-platform": "supported_platforms",
    "version": "version",
}
_RAW_TO_EMAIL_MAPPING = {raw: email for email, raw in _EMAIL_TO_RAW_MAPPING.items()}


def parse_email(data: bytes | str) -> tuple[RawMetadata, dict[str, list[str]]]:
    """Parse a distribution's metadata stored as email headers (e.g. from ``METADATA``).

    This function returns a two-item tuple of dicts. The first dict is of
    recognized fields from the core metadata specification. Fields that can be
    parsed and translated into Python's built-in types are converted
    appropriately. All other fields are left as-is. Fields that are allowed to
    appear multiple times are stored as lists.

    The second dict contains all other fields from the metadata. This includes
    any unrecognized fields. It also includes any fields which are expected to
    be parsed into a built-in type but were not formatted appropriately. Finally,
    any fields that are expected to appear only once but are repeated are
    included in this dict.

    """
    raw: dict[str, str | list[str] | dict[str, str]] = {}
    unparsed: dict[str, list[str]] = {}

    if isinstance(data, str):
        parsed = email.parser.Parser(policy=email.policy.compat32).parsestr(data)
    else:
        parsed = email.parser.BytesParser(policy=email.policy.compat32).parsebytes(data)

    # 042786.python.metadata.line310.comment We have to wrap parsed.keys() in a set, because in the case of multiple
    # 042787.python.metadata.line311.comment values for a key (a list), the key will appear multiple times in the
    # 042788.python.metadata.line312.comment list of keys, but we're avoiding that by using get_all().
    for name in frozenset(parsed.keys()):
        # 042789.python.metadata.line314.comment Header names in RFC are case insensitive, so we'll normalize to all
        # 042790.python.metadata.line315.comment lower case to make comparisons easier.
        name = name.lower()

        # 042791.python.metadata.line318.comment We use get_all() here, even for fields that aren't multiple use,
        # 042792.python.metadata.line319.comment because otherwise someone could have e.g. two Name fields, and we
        # 042793.python.metadata.line320.comment would just silently ignore it rather than doing something about it.
        headers = parsed.get_all(name) or []

        # 042794.python.metadata.line323.comment The way the email module works when parsing bytes is that it
        # 042795.python.metadata.line324.comment unconditionally decodes the bytes as ascii using the surrogateescape
        # 042796.python.metadata.line325.comment handler. When you pull that data back out (such as with get_all() ),
        # 042797.python.metadata.line326.comment it looks to see if the str has any surrogate escapes, and if it does
        # 042798.python.metadata.line327.comment it wraps it in a Header object instead of returning the string.
        # 042799.python.metadata.line328.comment
        # 042800.python.metadata.line329.comment As such, we'll look for those Header objects, and fix up the encoding.
        value = []
        # 042801.python.metadata.line331.comment Flag if we have run into any issues processing the headers, thus
        # 042802.python.metadata.line332.comment signalling that the data belongs in 'unparsed'.
        valid_encoding = True
        for h in headers:
            # 042803.python.metadata.line335.comment It's unclear if this can return more types than just a Header or
            # 042804.python.metadata.line336.comment a str, so we'll just assert here to make sure.
            assert isinstance(h, (email.header.Header, str))

            # 042805.python.metadata.line339.comment If it's a header object, we need to do our little dance to get
            # 042806.python.metadata.line340.comment the real data out of it. In cases where there is invalid data
            # 042807.python.metadata.line341.comment we're going to end up with mojibake, but there's no obvious, good
            # 042808.python.metadata.line342.comment way around that without reimplementing parts of the Header object
            # 042809.python.metadata.line343.comment ourselves.
            # 042810.python.metadata.line344.comment
            # 042811.python.metadata.line345.comment That should be fine since, if mojibacked happens, this key is
            # 042812.python.metadata.line346.comment going into the unparsed dict anyways.
            if isinstance(h, email.header.Header):
                # 042813.python.metadata.line348.comment The Header object stores it's data as chunks, and each chunk
                # 042814.python.metadata.line349.comment can be independently encoded, so we'll need to check each
                # 042815.python.metadata.line350.comment of them.
                chunks: list[tuple[bytes, str | None]] = []
                for bin, encoding in email.header.decode_header(h):
                    try:
                        bin.decode("utf8", "strict")
                    except UnicodeDecodeError:
                        # 042816.python.metadata.line356.comment Enable mojibake.
                        encoding = "latin1"
                        valid_encoding = False
                    else:
                        encoding = "utf8"
                    chunks.append((bin, encoding))

                # 042817.python.metadata.line363.comment Turn our chunks back into a Header object, then let that
                # 042818.python.metadata.line364.comment Header object do the right thing to turn them into a
                # 042819.python.metadata.line365.comment string for us.
                value.append(str(email.header.make_header(chunks)))
            # 042820.python.metadata.line367.comment This is already a string, so just add it.
            else:
                value.append(h)

        # 042821.python.metadata.line371.comment We've processed all of our values to get them into a list of str,
        # 042822.python.metadata.line372.comment but we may have mojibake data, in which case this is an unparsed
        # 042823.python.metadata.line373.comment field.
        if not valid_encoding:
            unparsed[name] = value
            continue

        raw_name = _EMAIL_TO_RAW_MAPPING.get(name)
        if raw_name is None:
            # 042824.python.metadata.line380.comment This is a bit of a weird situation, we've encountered a key that
            # 042825.python.metadata.line381.comment we don't know what it means, so we don't know whether it's meant
            # 042826.python.metadata.line382.comment to be a list or not.
            # 042827.python.metadata.line383.comment
            # 042828.python.metadata.line384.comment Since we can't really tell one way or another, we'll just leave it
            # 042829.python.metadata.line385.comment as a list, even though it may be a single item list, because that's
            # 042830.python.metadata.line386.comment what makes the most sense for email headers.
            unparsed[name] = value
            continue

        # 042831.python.metadata.line390.comment If this is one of our string fields, then we'll check to see if our
        # 042832.python.metadata.line391.comment value is a list of a single item. If it is then we'll assume that
        # 042833.python.metadata.line392.comment it was emitted as a single string, and unwrap the str from inside
        # 042834.python.metadata.line393.comment the list.
        # 042835.python.metadata.line394.comment
        # 042836.python.metadata.line395.comment If it's any other kind of data, then we haven't the faintest clue
        # 042837.python.metadata.line396.comment what we should parse it as, and we have to just add it to our list
        # 042838.python.metadata.line397.comment of unparsed stuff.
        if raw_name in _STRING_FIELDS and len(value) == 1:
            raw[raw_name] = value[0]
        # 042839.python.metadata.line400.comment If this is one of our list of string fields, then we can just assign
        # 042840.python.metadata.line401.comment the value, since email *only* has strings, and our get_all() call
        # 042841.python.metadata.line402.comment above ensures that this is a list.
        elif raw_name in _LIST_FIELDS:
            raw[raw_name] = value
        # 042842.python.metadata.line405.comment Special Case: Keywords
        # 042843.python.metadata.line406.comment The keywords field is implemented in the metadata spec as a str,
        # 042844.python.metadata.line407.comment but it conceptually is a list of strings, and is serialized using
        # 042845.python.metadata.line408.comment ", ".join(keywords), so we'll do some light data massaging to turn
        # 042846.python.metadata.line409.comment this into what it logically is.
        elif raw_name == "keywords" and len(value) == 1:
            raw[raw_name] = _parse_keywords(value[0])
        # 042847.python.metadata.line412.comment Special Case: Project-URL
        # 042848.python.metadata.line413.comment The project urls is implemented in the metadata spec as a list of
        # 042849.python.metadata.line414.comment specially-formatted strings that represent a key and a value, which
        # 042850.python.metadata.line415.comment is fundamentally a mapping, however the email format doesn't support
        # 042851.python.metadata.line416.comment mappings in a sane way, so it was crammed into a list of strings
        # 042852.python.metadata.line417.comment instead.
        # 042853.python.metadata.line418.comment
        # 042854.python.metadata.line419.comment We will do a little light data massaging to turn this into a map as
        # 042855.python.metadata.line420.comment it logically should be.
        elif raw_name == "project_urls":
            try:
                raw[raw_name] = _parse_project_urls(value)
            except KeyError:
                unparsed[name] = value
        # 042856.python.metadata.line426.comment Nothing that we've done has managed to parse this, so it'll just
        # 042857.python.metadata.line427.comment throw it in our unparseable data and move on.
        else:
            unparsed[name] = value

    # 042858.python.metadata.line431.comment We need to support getting the Description from the message payload in
    # 042859.python.metadata.line432.comment addition to getting it from the the headers. This does mean, though, there
    # 042860.python.metadata.line433.comment is the possibility of it being set both ways, in which case we put both
    # 042861.python.metadata.line434.comment in 'unparsed' since we don't know which is right.
    try:
        payload = _get_payload(parsed, data)
    except ValueError:
        unparsed.setdefault("description", []).append(
            parsed.get_payload(decode=isinstance(data, bytes))  # type: ignore[call-overload]
        )
    else:
        if payload:
            # 042863.python.metadata.line443.comment Check to see if we've already got a description, if so then both
            # 042864.python.metadata.line444.comment it, and this body move to unparseable.
            if "description" in raw:
                description_header = cast(str, raw.pop("description"))
                unparsed.setdefault("description", []).extend(
                    [description_header, payload]
                )
            elif "description" in unparsed:
                unparsed["description"].append(payload)
            else:
                raw["description"] = payload

    # 042865.python.metadata.line455.comment We need to cast our `raw` to a metadata, because a TypedDict only support
    # 042866.python.metadata.line456.comment literal key names, but we're computing our key names on purpose, but the
    # 042867.python.metadata.line457.comment way this function is implemented, our `TypedDict` can only have valid key
    # 042868.python.metadata.line458.comment names.
    return cast(RawMetadata, raw), unparsed


_NOT_FOUND = object()


# 042869.python.metadata.line465.comment Keep the two values in sync.
_VALID_METADATA_VERSIONS = ["1.0", "1.1", "1.2", "2.1", "2.2", "2.3", "2.4"]
_MetadataVersion = Literal["1.0", "1.1", "1.2", "2.1", "2.2", "2.3", "2.4"]

_REQUIRED_ATTRS = frozenset(["metadata_version", "name", "version"])


class _Validator(Generic[T]):
    """Validate a metadata field.

    All _process_*() methods correspond to a core metadata field. The method is
    called with the field's raw value. If the raw value is valid it is returned
    in its "enriched" form (e.g. ``version.Version`` for the ``Version`` field).
    If the raw value is invalid, :exc:`InvalidMetadata` is raised (with a cause
    as appropriate).
    """

    name: str
    raw_name: str
    added: _MetadataVersion

    def __init__(
        self,
        *,
        added: _MetadataVersion = "1.0",
    ) -> None:
        self.added = added

    def __set_name__(self, _owner: Metadata, name: str) -> None:
        self.name = name
        self.raw_name = _RAW_TO_EMAIL_MAPPING[name]

    def __get__(self, instance: Metadata, _owner: type[Metadata]) -> T:
        # 042870.python.metadata.line498.comment With Python 3.8, the caching can be replaced with functools.cached_property().
        # 042871.python.metadata.line499.comment No need to check the cache as attribute lookup will resolve into the
        # 042872.python.metadata.line500.comment instance's __dict__ before __get__ is called.
        cache = instance.__dict__
        value = instance._raw.get(self.name)

        # 042873.python.metadata.line504.comment To make the _process_* methods easier, we'll check if the value is None
        # 042874.python.metadata.line505.comment and if this field is NOT a required attribute, and if both of those
        # 042875.python.metadata.line506.comment things are true, we'll skip the the converter. This will mean that the
        # 042876.python.metadata.line507.comment converters never have to deal with the None union.
        if self.name in _REQUIRED_ATTRS or value is not None:
            try:
                converter: Callable[[Any], T] = getattr(self, f"_process_{self.name}")
            except AttributeError:
                pass
            else:
                value = converter(value)

        cache[self.name] = value
        try:
            del instance._raw[self.name]  # type: ignore[misc]
        except KeyError:
            pass

        return cast(T, value)

    def _invalid_metadata(
        self, msg: str, cause: Exception | None = None
    ) -> InvalidMetadata:
        exc = InvalidMetadata(
            self.raw_name, msg.format_map({"field": repr(self.raw_name)})
        )
        exc.__cause__ = cause
        return exc

    def _process_metadata_version(self, value: str) -> _MetadataVersion:
        # 042878.python.metadata.line534.comment Implicitly makes Metadata-Version required.
        if value not in _VALID_METADATA_VERSIONS:
            raise self._invalid_metadata(f"{value!r} is not a valid metadata version")
        return cast(_MetadataVersion, value)

    def _process_name(self, value: str) -> str:
        if not value:
            raise self._invalid_metadata("{field} is a required field")
        # 042879.python.metadata.line542.comment Validate the name as a side-effect.
        try:
            utils.canonicalize_name(value, validate=True)
        except utils.InvalidName as exc:
            raise self._invalid_metadata(
                f"{value!r} is invalid for {{field}}", cause=exc
            ) from exc
        else:
            return value

    def _process_version(self, value: str) -> version_module.Version:
        if not value:
            raise self._invalid_metadata("{field} is a required field")
        try:
            return version_module.parse(value)
        except version_module.InvalidVersion as exc:
            raise self._invalid_metadata(
                f"{value!r} is invalid for {{field}}", cause=exc
            ) from exc

    def _process_summary(self, value: str) -> str:
        """Check the field contains no newlines."""
        if "\n" in value:
            raise self._invalid_metadata("{field} must be a single line")
        return value

    def _process_description_content_type(self, value: str) -> str:
        content_types = {"text/plain", "text/x-rst", "text/markdown"}
        message = email.message.EmailMessage()
        message["content-type"] = value

        content_type, parameters = (
            # 042880.python.metadata.line574.comment Defaults to `text/plain` if parsing failed.
            message.get_content_type().lower(),
            message["content-type"].params,
        )
        # 042881.python.metadata.line578.comment Check if content-type is valid or defaulted to `text/plain` and thus was
        # 042882.python.metadata.line579.comment not parseable.
        if content_type not in content_types or content_type not in value.lower():
            raise self._invalid_metadata(
                f"{{field}} must be one of {list(content_types)}, not {value!r}"
            )

        charset = parameters.get("charset", "UTF-8")
        if charset != "UTF-8":
            raise self._invalid_metadata(
                f"{{field}} can only specify the UTF-8 charset, not {list(charset)}"
            )

        markdown_variants = {"GFM", "CommonMark"}
        variant = parameters.get("variant", "GFM")  # Use an acceptable default.
        if content_type == "text/markdown" and variant not in markdown_variants:
            raise self._invalid_metadata(
                f"valid Markdown variants for {{field}} are {list(markdown_variants)}, "
                f"not {variant!r}",
            )
        return value

    def _process_dynamic(self, value: list[str]) -> list[str]:
        for dynamic_field in map(str.lower, value):
            if dynamic_field in {"name", "version", "metadata-version"}:
                raise self._invalid_metadata(
                    f"{dynamic_field!r} is not allowed as a dynamic field"
                )
            elif dynamic_field not in _EMAIL_TO_RAW_MAPPING:
                raise self._invalid_metadata(
                    f"{dynamic_field!r} is not a valid dynamic field"
                )
        return list(map(str.lower, value))

    def _process_provides_extra(
        self,
        value: list[str],
    ) -> list[utils.NormalizedName]:
        normalized_names = []
        try:
            for name in value:
                normalized_names.append(utils.canonicalize_name(name, validate=True))
        except utils.InvalidName as exc:
            raise self._invalid_metadata(
                f"{name!r} is invalid for {{field}}", cause=exc
            ) from exc
        else:
            return normalized_names

    def _process_requires_python(self, value: str) -> specifiers.SpecifierSet:
        try:
            return specifiers.SpecifierSet(value)
        except specifiers.InvalidSpecifier as exc:
            raise self._invalid_metadata(
                f"{value!r} is invalid for {{field}}", cause=exc
            ) from exc

    def _process_requires_dist(
        self,
        value: list[str],
    ) -> list[requirements.Requirement]:
        reqs = []
        try:
            for req in value:
                reqs.append(requirements.Requirement(req))
        except requirements.InvalidRequirement as exc:
            raise self._invalid_metadata(
                f"{req!r} is invalid for {{field}}", cause=exc
            ) from exc
        else:
            return reqs

    def _process_license_expression(
        self, value: str
    ) -> NormalizedLicenseExpression | None:
        try:
            return licenses.canonicalize_license_expression(value)
        except ValueError as exc:
            raise self._invalid_metadata(
                f"{value!r} is invalid for {{field}}", cause=exc
            ) from exc

    def _process_license_files(self, value: list[str]) -> list[str]:
        paths = []
        for path in value:
            if ".." in path:
                raise self._invalid_metadata(
                    f"{path!r} is invalid for {{field}}, "
                    "parent directory indicators are not allowed"
                )
            if "*" in path:
                raise self._invalid_metadata(
                    f"{path!r} is invalid for {{field}}, paths must be resolved"
                )
            if (
                pathlib.PurePosixPath(path).is_absolute()
                or pathlib.PureWindowsPath(path).is_absolute()
            ):
                raise self._invalid_metadata(
                    f"{path!r} is invalid for {{field}}, paths must be relative"
                )
            if pathlib.PureWindowsPath(path).as_posix() != path:
                raise self._invalid_metadata(
                    f"{path!r} is invalid for {{field}}, "
                    "paths must use '/' delimiter"
                )
            paths.append(path)
        return paths


class Metadata:
    """Representation of distribution metadata.

    Compared to :class:`RawMetadata`, this class provides objects representing
    metadata fields instead of only using built-in types. Any invalid metadata
    will cause :exc:`InvalidMetadata` to be raised (with a
    :py:attr:`~BaseException.__cause__` attribute as appropriate).
    """

    _raw: RawMetadata

    @classmethod
    def from_raw(cls, data: RawMetadata, *, validate: bool = True) -> Metadata:
        """Create an instance from :class:`RawMetadata`.

        If *validate* is true, all metadata will be validated. All exceptions
        related to validation will be gathered and raised as an :class:`ExceptionGroup`.
        """
        ins = cls()
        ins._raw = data.copy()  # Mutations occur due to caching enriched values.

        if validate:
            exceptions: list[Exception] = []
            try:
                metadata_version = ins.metadata_version
                metadata_age = _VALID_METADATA_VERSIONS.index(metadata_version)
            except InvalidMetadata as metadata_version_exc:
                exceptions.append(metadata_version_exc)
                metadata_version = None

            # 042885.python.metadata.line718.comment Make sure to check for the fields that are present, the required
            # 042886.python.metadata.line719.comment fields (so their absence can be reported).
            fields_to_check = frozenset(ins._raw) | _REQUIRED_ATTRS
            # 042887.python.metadata.line721.comment Remove fields that have already been checked.
            fields_to_check -= {"metadata_version"}

            for key in fields_to_check:
                try:
                    if metadata_version:
                        # 042888.python.metadata.line727.comment Can't use getattr() as that triggers descriptor protocol which
                        # 042889.python.metadata.line728.comment will fail due to no value for the instance argument.
                        try:
                            field_metadata_version = cls.__dict__[key].added
                        except KeyError:
                            exc = InvalidMetadata(key, f"unrecognized field: {key!r}")
                            exceptions.append(exc)
                            continue
                        field_age = _VALID_METADATA_VERSIONS.index(
                            field_metadata_version
                        )
                        if field_age > metadata_age:
                            field = _RAW_TO_EMAIL_MAPPING[key]
                            exc = InvalidMetadata(
                                field,
                                f"{field} introduced in metadata version "
                                f"{field_metadata_version}, not {metadata_version}",
                            )
                            exceptions.append(exc)
                            continue
                    getattr(ins, key)
                except InvalidMetadata as exc:
                    exceptions.append(exc)

            if exceptions:
                raise ExceptionGroup("invalid metadata", exceptions)

        return ins

    @classmethod
    def from_email(cls, data: bytes | str, *, validate: bool = True) -> Metadata:
        """Parse metadata from email headers.

        If *validate* is true, the metadata will be validated. All exceptions
        related to validation will be gathered and raised as an :class:`ExceptionGroup`.
        """
        raw, unparsed = parse_email(data)

        if validate:
            exceptions: list[Exception] = []
            for unparsed_key in unparsed:
                if unparsed_key in _EMAIL_TO_RAW_MAPPING:
                    message = f"{unparsed_key!r} has invalid data"
                else:
                    message = f"unrecognized field: {unparsed_key!r}"
                exceptions.append(InvalidMetadata(unparsed_key, message))

            if exceptions:
                raise ExceptionGroup("unparsed", exceptions)

        try:
            return cls.from_raw(raw, validate=validate)
        except ExceptionGroup as exc_group:
            raise ExceptionGroup(
                "invalid or unparsed metadata", exc_group.exceptions
            ) from None

    metadata_version: _Validator[_MetadataVersion] = _Validator()
    """:external:ref:`core-metadata-metadata-version`
    (required; validated to be a valid metadata version)"""
    # 042890.python.metadata.line787.comment `name` is not normalized/typed to NormalizedName so as to provide access to
    # 042891.python.metadata.line788.comment the original/raw name.
    name: _Validator[str] = _Validator()
    """:external:ref:`core-metadata-name`
    (required; validated using :func:`~packaging.utils.canonicalize_name` and its
    *validate* parameter)"""
    version: _Validator[version_module.Version] = _Validator()
    """:external:ref:`core-metadata-version` (required)"""
    dynamic: _Validator[list[str] | None] = _Validator(
        added="2.2",
    )
    """:external:ref:`core-metadata-dynamic`
    (validated against core metadata field names and lowercased)"""
    platforms: _Validator[list[str] | None] = _Validator()
    """:external:ref:`core-metadata-platform`"""
    supported_platforms: _Validator[list[str] | None] = _Validator(added="1.1")
    """:external:ref:`core-metadata-supported-platform`"""
    summary: _Validator[str | None] = _Validator()
    """:external:ref:`core-metadata-summary` (validated to contain no newlines)"""
    description: _Validator[str | None] = _Validator()  # TODO 2.1: can be in body
    """:external:ref:`core-metadata-description`"""
    description_content_type: _Validator[str | None] = _Validator(added="2.1")
    """:external:ref:`core-metadata-description-content-type` (validated)"""
    keywords: _Validator[list[str] | None] = _Validator()
    """:external:ref:`core-metadata-keywords`"""
    home_page: _Validator[str | None] = _Validator()
    """:external:ref:`core-metadata-home-page`"""
    download_url: _Validator[str | None] = _Validator(added="1.1")
    """:external:ref:`core-metadata-download-url`"""
    author: _Validator[str | None] = _Validator()
    """:external:ref:`core-metadata-author`"""
    author_email: _Validator[str | None] = _Validator()
    """:external:ref:`core-metadata-author-email`"""
    maintainer: _Validator[str | None] = _Validator(added="1.2")
    """:external:ref:`core-metadata-maintainer`"""
    maintainer_email: _Validator[str | None] = _Validator(added="1.2")
    """:external:ref:`core-metadata-maintainer-email`"""
    license: _Validator[str | None] = _Validator()
    """:external:ref:`core-metadata-license`"""
    license_expression: _Validator[NormalizedLicenseExpression | None] = _Validator(
        added="2.4"
    )
    """:external:ref:`core-metadata-license-expression`"""
    license_files: _Validator[list[str] | None] = _Validator(added="2.4")
    """:external:ref:`core-metadata-license-file`"""
    classifiers: _Validator[list[str] | None] = _Validator(added="1.1")
    """:external:ref:`core-metadata-classifier`"""
    requires_dist: _Validator[list[requirements.Requirement] | None] = _Validator(
        added="1.2"
    )
    """:external:ref:`core-metadata-requires-dist`"""
    requires_python: _Validator[specifiers.SpecifierSet | None] = _Validator(
        added="1.2"
    )
    """:external:ref:`core-metadata-requires-python`"""
    # 042893.python.metadata.line842.comment Because `Requires-External` allows for non-PEP 440 version specifiers, we
    # 042894.python.metadata.line843.comment don't do any processing on the values.
    requires_external: _Validator[list[str] | None] = _Validator(added="1.2")
    """:external:ref:`core-metadata-requires-external`"""
    project_urls: _Validator[dict[str, str] | None] = _Validator(added="1.2")
    """:external:ref:`core-metadata-project-url`"""
    # 042895.python.metadata.line848.comment PEP 685 lets us raise an error if an extra doesn't pass `Name` validation
    # 042896.python.metadata.line849.comment regardless of metadata version.
    provides_extra: _Validator[list[utils.NormalizedName] | None] = _Validator(
        added="2.1",
    )
    """:external:ref:`core-metadata-provides-extra`"""
    provides_dist: _Validator[list[str] | None] = _Validator(added="1.2")
    """:external:ref:`core-metadata-provides-dist`"""
    obsoletes_dist: _Validator[list[str] | None] = _Validator(added="1.2")
    """:external:ref:`core-metadata-obsoletes-dist`"""
    requires: _Validator[list[str] | None] = _Validator(added="1.1")
    """``Requires`` (deprecated)"""
    provides: _Validator[list[str] | None] = _Validator(added="1.1")
    """``Provides`` (deprecated)"""
    obsoletes: _Validator[list[str] | None] = _Validator(added="1.1")
    """``Obsoletes`` (deprecated)"""
