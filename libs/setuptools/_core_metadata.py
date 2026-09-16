"""
Handling of Core Metadata for Python packages (including reading and writing).

See: https://packaging.python.org/en/latest/specifications/core-metadata/
"""

from __future__ import annotations

import os
import stat
import textwrap
from email import message_from_file
from email.message import Message
from tempfile import NamedTemporaryFile

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name, canonicalize_version
from packaging.version import Version

from . import _normalization, _reqs
from ._static import is_static
from .warnings import SetuptoolsDeprecationWarning

from distutils.util import rfc822_escape


def get_metadata_version(self):
    mv = getattr(self, 'metadata_version', None)
    if mv is None:
        mv = Version('2.4')
        self.metadata_version = mv
    return mv


def rfc822_unescape(content: str) -> str:
    """Reverse RFC-822 escaping by removing leading whitespaces from content."""
    lines = content.splitlines()
    if len(lines) == 1:
        return lines[0].lstrip()
    return '\n'.join((lines[0].lstrip(), textwrap.dedent('\n'.join(lines[1:]))))


def _read_field_from_msg(msg: Message, field: str) -> str | None:
    """Read Message header field."""
    value = msg[field]
    if value == 'UNKNOWN':
        return None
    return value


def _read_field_unescaped_from_msg(msg: Message, field: str) -> str | None:
    """Read Message header field and apply rfc822_unescape."""
    value = _read_field_from_msg(msg, field)
    if value is None:
        return value
    return rfc822_unescape(value)


def _read_list_from_msg(msg: Message, field: str) -> list[str] | None:
    """Read Message header field and return all results as list."""
    values = msg.get_all(field, None)
    if values == []:
        return None
    return values


def _read_payload_from_msg(msg: Message) -> str | None:
    value = str(msg.get_payload()).strip()
    if value == 'UNKNOWN' or not value:
        return None
    return value


def read_pkg_file(self, file):
    """Reads the metadata values from a file object."""
    msg = message_from_file(file)

    self.metadata_version = Version(msg['metadata-version'])
    self.name = _read_field_from_msg(msg, 'name')
    self.version = _read_field_from_msg(msg, 'version')
    self.description = _read_field_from_msg(msg, 'summary')
    # 039201.python.core_metadata.line83.comment we are filling author only.
    self.author = _read_field_from_msg(msg, 'author')
    self.maintainer = None
    self.author_email = _read_field_from_msg(msg, 'author-email')
    self.maintainer_email = None
    self.url = _read_field_from_msg(msg, 'home-page')
    self.download_url = _read_field_from_msg(msg, 'download-url')
    self.license = _read_field_unescaped_from_msg(msg, 'license')
    self.license_expression = _read_field_unescaped_from_msg(msg, 'license-expression')

    self.long_description = _read_field_unescaped_from_msg(msg, 'description')
    if self.long_description is None and self.metadata_version >= Version('2.1'):
        self.long_description = _read_payload_from_msg(msg)
    self.description = _read_field_from_msg(msg, 'summary')

    if 'keywords' in msg:
        self.keywords = _read_field_from_msg(msg, 'keywords').split(',')

    self.platforms = _read_list_from_msg(msg, 'platform')
    self.classifiers = _read_list_from_msg(msg, 'classifier')

    # 039202.python.core_metadata.line104.comment PEP 314 - these fields only exist in 1.1
    if self.metadata_version == Version('1.1'):
        self.requires = _read_list_from_msg(msg, 'requires')
        self.provides = _read_list_from_msg(msg, 'provides')
        self.obsoletes = _read_list_from_msg(msg, 'obsoletes')
    else:
        self.requires = None
        self.provides = None
        self.obsoletes = None

    self.license_files = _read_list_from_msg(msg, 'license-file')


def single_line(val):
    """
    Quick and dirty validation for Summary pypa/setuptools#1390.
    """
    if '\n' in val:
        # 039203.python.core_metadata.line122.comment TODO: Replace with `raise ValueError("newlines not allowed")`
        # 039204.python.core_metadata.line123.comment after reviewing #2893.
        msg = "newlines are not allowed in `summary` and will break in the future"
        SetuptoolsDeprecationWarning.emit("Invalid config.", msg)
        # 039205.python.core_metadata.line126.comment due_date is undefined. Controversial change, there was a lot of push back.
        val = val.strip().split('\n')[0]
    return val


def write_pkg_info(self, base_dir):
    """Write the PKG-INFO file into the release tree."""
    temp = ""
    final = os.path.join(base_dir, 'PKG-INFO')
    try:
        # 039206.python.core_metadata.line136.comment Use a temporary file while writing to avoid race conditions
        # 039207.python.core_metadata.line137.comment (e.g. `importlib.metadata` reading `.egg-info/PKG-INFO`):
        with NamedTemporaryFile("w", encoding="utf-8", dir=base_dir, delete=False) as f:
            temp = f.name
            self.write_pkg_file(f)
        permissions = stat.S_IMODE(os.lstat(temp).st_mode)
        os.chmod(temp, permissions | stat.S_IRGRP | stat.S_IROTH)
        os.replace(temp, final)  # atomic operation.
    finally:
        if temp and os.path.exists(temp):
            os.remove(temp)


# 039209.python.core_metadata.line149.comment Based on Python 3.5 version
def write_pkg_file(self, file):  # noqa: C901  # is too complex (14)  # FIXME
    """Write the PKG-INFO format data to a file object."""
    version = self.get_metadata_version()

    def write_field(key, value):
        file.write(f"{key}: {value}\n")

    write_field('Metadata-Version', str(version))
    write_field('Name', self.get_name())
    write_field('Version', self.get_version())

    summary = self.get_description()
    if summary:
        write_field('Summary', single_line(summary))

    optional_fields = (
        ('Home-page', 'url'),
        ('Download-URL', 'download_url'),
        ('Author', 'author'),
        ('Author-email', 'author_email'),
        ('Maintainer', 'maintainer'),
        ('Maintainer-email', 'maintainer_email'),
    )

    for field, attr in optional_fields:
        attr_val = getattr(self, attr, None)
        if attr_val is not None:
            write_field(field, attr_val)

    if license_expression := self.license_expression:
        write_field('License-Expression', license_expression)
    elif license := self.get_license():
        write_field('License', rfc822_escape(license))

    for label, url in self.project_urls.items():
        write_field('Project-URL', f'{label}, {url}')

    keywords = ','.join(self.get_keywords())
    if keywords:
        write_field('Keywords', keywords)

    platforms = self.get_platforms() or []
    for platform in platforms:
        write_field('Platform', platform)

    self._write_list(file, 'Classifier', self.get_classifiers())

    # 039211.python.core_metadata.line197.comment PEP 314
    self._write_list(file, 'Requires', self.get_requires())
    self._write_list(file, 'Provides', self.get_provides())
    self._write_list(file, 'Obsoletes', self.get_obsoletes())

    # 039212.python.core_metadata.line202.comment Setuptools specific for PEP 345
    if hasattr(self, 'python_requires'):
        write_field('Requires-Python', self.python_requires)

    # 039213.python.core_metadata.line206.comment PEP 566
    if self.long_description_content_type:
        write_field('Description-Content-Type', self.long_description_content_type)

    safe_license_files = map(_safe_license_file, self.license_files or [])
    self._write_list(file, 'License-File', safe_license_files)
    _write_requirements(self, file)

    for field, attr in _POSSIBLE_DYNAMIC_FIELDS.items():
        if (val := getattr(self, attr, None)) and not is_static(val):
            write_field('Dynamic', field)

    long_description = self.get_long_description()
    if long_description:
        file.write(f"\n{long_description}")
        if not long_description.endswith("\n"):
            file.write("\n")


def _write_requirements(self, file):
    for req in _reqs.parse(self.install_requires):
        file.write(f"Requires-Dist: {req}\n")

    processed_extras = {}
    for augmented_extra, reqs in self.extras_require.items():
        # 039214.python.core_metadata.line231.comment Historically, setuptools allows "augmented extras": `<extra>:<condition>`
        unsafe_extra, _, condition = augmented_extra.partition(":")
        unsafe_extra = unsafe_extra.strip()
        extra = _normalization.safe_extra(unsafe_extra)

        if extra:
            _write_provides_extra(file, processed_extras, extra, unsafe_extra)
        for req in _reqs.parse_strings(reqs):
            r = _include_extra(req, extra, condition.strip())
            file.write(f"Requires-Dist: {r}\n")

    return processed_extras


def _include_extra(req: str, extra: str, condition: str) -> Requirement:
    r = Requirement(req)  # create a fresh object that can be modified
    parts = (
        f"({r.marker})" if r.marker else None,
        f"({condition})" if condition else None,
        f"extra == {extra!r}" if extra else None,
    )
    r.marker = Marker(" and ".join(x for x in parts if x))
    return r


def _write_provides_extra(file, processed_extras, safe, unsafe):
    previous = processed_extras.get(safe)
    if previous == unsafe:
        SetuptoolsDeprecationWarning.emit(
            'Ambiguity during "extra" normalization for dependencies.',
            f"""
            {previous!r} and {unsafe!r} normalize to the same value:\n
                {safe!r}\n
            In future versions, setuptools might halt the build process.
            """,
            see_url="https://peps.python.org/pep-0685/",
        )
    else:
        processed_extras[safe] = unsafe
        file.write(f"Provides-Extra: {safe}\n")


# 039216.python.core_metadata.line273.comment from pypa/distutils#244; needed only until that logic is always available
def get_fullname(self):
    return _distribution_fullname(self.get_name(), self.get_version())


def _distribution_fullname(name: str, version: str) -> str:
    """
    >>> _distribution_fullname('setup.tools', '1.0-2')
    'setup_tools-1.0.post2'
    >>> _distribution_fullname('setup-tools', '1.2post2')
    'setup_tools-1.2.post2'
    >>> _distribution_fullname('setup-tools', '1.0-r2')
    'setup_tools-1.0.post2'
    >>> _distribution_fullname('setup.tools', '1.0.post')
    'setup_tools-1.0.post0'
    >>> _distribution_fullname('setup.tools', '1.0+ubuntu-1')
    'setup_tools-1.0+ubuntu.1'
    """
    return "{}-{}".format(
        canonicalize_name(name).replace('-', '_'),
        canonicalize_version(version, strip_trailing_zero=False),
    )


def _safe_license_file(file):
    # 039217.python.core_metadata.line298.comment XXX: Do we need this after the deprecation discussed in #4892, #4896??
    normalized = os.path.normpath(file).replace(os.sep, "/")
    if "../" in normalized:
        return os.path.basename(normalized)  # Temporarily restore pre PEP639 behaviour
    return normalized


_POSSIBLE_DYNAMIC_FIELDS = {
    # 039219.python.core_metadata.line306.comment Core Metadata Field x related Distribution attribute
    "author": "author",
    "author-email": "author_email",
    "classifier": "classifiers",
    "description": "long_description",
    "description-content-type": "long_description_content_type",
    "download-url": "download_url",
    "home-page": "url",
    "keywords": "keywords",
    "license": "license",
    # 039220.python.core_metadata.line316.comment XXX: License-File is complicated because the user gives globs that are expanded
    # 039221.python.core_metadata.line317.comment during the build. Without special handling it is likely always
    # 039222.python.core_metadata.line318.comment marked as Dynamic, which is an acceptable outcome according to:
    # 039223.python.core_metadata.line319.comment https://github.com/pypa/setuptools/issues/4629#issuecomment-2331233677
    "license-file": "license_files",
    "license-expression": "license_expression",  # PEP 639
    "maintainer": "maintainer",
    "maintainer-email": "maintainer_email",
    "obsoletes": "obsoletes",
    # 039225.python.core_metadata.line325.comment "obsoletes-dist": "obsoletes_dist",  # NOT USED
    "platform": "platforms",
    "project-url": "project_urls",
    "provides": "provides",
    # 039226.python.core_metadata.line329.comment "provides-dist": "provides_dist",  # NOT USED
    "provides-extra": "extras_require",
    "requires": "requires",
    "requires-dist": "install_requires",
    # 039227.python.core_metadata.line333.comment "requires-external": "requires_external",  # NOT USED
    "requires-python": "python_requires",
    "summary": "description",
    # 039228.python.core_metadata.line336.comment "supported-platform": "supported_platforms",  # NOT USED
}
