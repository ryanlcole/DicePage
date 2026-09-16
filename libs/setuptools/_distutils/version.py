# 041390.python.version.line1.comment
# 041391.python.version.line2.comment distutils/version.py
# 041392.python.version.line3.comment
# 041393.python.version.line4.comment Implements multiple version numbering conventions for the
# 041394.python.version.line5.comment Python Module Distribution Utilities.
# 041395.python.version.line6.comment
# 041396.python.version.line7.comment $Id$
# 041397.python.version.line8.comment

"""Provides classes to represent module version numbers (one class for
each style of version numbering).  There are currently two such classes
implemented: StrictVersion and LooseVersion.

Every version number class implements the following interface:
  * the 'parse' method takes a string and parses it to some internal
    representation; if the string is an invalid version number,
    'parse' raises a ValueError exception
  * the class constructor takes an optional string argument which,
    if supplied, is passed to 'parse'
  * __str__ reconstructs the string that was passed to 'parse' (or
    an equivalent string -- ie. one that will generate an equivalent
    version number instance)
  * __repr__ generates Python code to recreate the version number instance
  * _cmp compares the current instance with either another instance
    of the same class or a string (which will be parsed to an instance
    of the same class, thus must follow the same rules)
"""

import contextlib
import re
import warnings


@contextlib.contextmanager
def suppress_known_deprecation():
    with warnings.catch_warnings(record=True) as ctx:
        warnings.filterwarnings(
            action='default',
            category=DeprecationWarning,
            message="distutils Version classes are deprecated.",
        )
        yield ctx


class Version:
    """Abstract base class for version numbering classes.  Just provides
    constructor (__init__) and reproducer (__repr__), because those
    seem to be the same for all version numbering classes; and route
    rich comparisons to _cmp.
    """

    def __init__(self, vstring=None):
        if vstring:
            self.parse(vstring)
        warnings.warn(
            "distutils Version classes are deprecated. Use packaging.version instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def __repr__(self):
        return f"{self.__class__.__name__} ('{self}')"

    def __eq__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c == 0

    def __lt__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c < 0

    def __le__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c <= 0

    def __gt__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c > 0

    def __ge__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c >= 0


# 041398.python.version.line95.comment Interface for version-number classes -- must be implemented
# 041399.python.version.line96.comment by the following classes (the concrete ones -- Version should
# 041400.python.version.line97.comment be treated as an abstract class).
# 041401.python.version.line98.comment __init__ (string) - create and take same action as 'parse'
# 041402.python.version.line99.comment (string parameter is optional)
# 041403.python.version.line100.comment parse (string)    - convert a string representation to whatever
# 041404.python.version.line101.comment internal representation is appropriate for
# 041405.python.version.line102.comment this style of version numbering
# 041406.python.version.line103.comment __str__ (self)    - convert back to a string; should be very similar
# 041407.python.version.line104.comment (if not identical to) the string supplied to parse
# 041408.python.version.line105.comment __repr__ (self)   - generate Python code to recreate
# 041409.python.version.line106.comment the instance
# 041410.python.version.line107.comment _cmp (self, other) - compare two version numbers ('other' may
# 041411.python.version.line108.comment be an unparsed version string, or another
# 041412.python.version.line109.comment instance of your version class)


class StrictVersion(Version):
    """Version numbering for anal retentives and software idealists.
    Implements the standard interface for version number classes as
    described above.  A version number consists of two or three
    dot-separated numeric components, with an optional "pre-release" tag
    on the end.  The pre-release tag consists of the letter 'a' or 'b'
    followed by a number.  If the numeric components of two version
    numbers are equal, then one with a pre-release tag will always
    be deemed earlier (lesser) than one without.

    The following are valid version numbers (shown in the order that
    would be obtained by sorting according to the supplied cmp function):

        0.4       0.4.0  (these two are equivalent)
        0.4.1
        0.5a1
        0.5b3
        0.5
        0.9.6
        1.0
        1.0.4a3
        1.0.4b1
        1.0.4

    The following are examples of invalid version numbers:

        1
        2.7.2.2
        1.3.a4
        1.3pl1
        1.3c4

    The rationale for this version numbering system will be explained
    in the distutils documentation.
    """

    version_re = re.compile(
        r'^(\d+) \. (\d+) (\. (\d+))? ([ab](\d+))?$', re.VERBOSE | re.ASCII
    )

    def parse(self, vstring):
        match = self.version_re.match(vstring)
        if not match:
            raise ValueError(f"invalid version number '{vstring}'")

        (major, minor, patch, prerelease, prerelease_num) = match.group(1, 2, 4, 5, 6)

        if patch:
            self.version = tuple(map(int, [major, minor, patch]))
        else:
            self.version = tuple(map(int, [major, minor])) + (0,)

        if prerelease:
            self.prerelease = (prerelease[0], int(prerelease_num))
        else:
            self.prerelease = None

    def __str__(self):
        if self.version[2] == 0:
            vstring = '.'.join(map(str, self.version[0:2]))
        else:
            vstring = '.'.join(map(str, self.version))

        if self.prerelease:
            vstring = vstring + self.prerelease[0] + str(self.prerelease[1])

        return vstring

    def _cmp(self, other):
        if isinstance(other, str):
            with suppress_known_deprecation():
                other = StrictVersion(other)
        elif not isinstance(other, StrictVersion):
            return NotImplemented

        if self.version == other.version:
            # 041413.python.version.line188.comment versions match; pre-release drives the comparison
            return self._cmp_prerelease(other)

        return -1 if self.version < other.version else 1

    def _cmp_prerelease(self, other):
        """
        case 1: self has prerelease, other doesn't; other is greater
        case 2: self doesn't have prerelease, other does: self is greater
        case 3: both or neither have prerelease: compare them!
        """
        if self.prerelease and not other.prerelease:
            return -1
        elif not self.prerelease and other.prerelease:
            return 1

        if self.prerelease == other.prerelease:
            return 0
        elif self.prerelease < other.prerelease:
            return -1
        else:
            return 1


# 041414.python.version.line212.comment end class StrictVersion


# 041415.python.version.line215.comment The rules according to Greg Stein:
# 041416.python.version.line216.comment 1) a version number has 1 or more numbers separated by a period or by
# 041417.python.version.line217.comment sequences of letters. If only periods, then these are compared
# 041418.python.version.line218.comment left-to-right to determine an ordering.
# 041419.python.version.line219.comment 2) sequences of letters are part of the tuple for comparison and are
# 041420.python.version.line220.comment compared lexicographically
# 041421.python.version.line221.comment 3) recognize the numeric components may have leading zeroes
# 041422.python.version.line222.comment
# 041423.python.version.line223.comment The LooseVersion class below implements these rules: a version number
# 041424.python.version.line224.comment string is split up into a tuple of integer and string components, and
# 041425.python.version.line225.comment comparison is a simple tuple comparison.  This means that version
# 041426.python.version.line226.comment numbers behave in a predictable and obvious way, but a way that might
# 041427.python.version.line227.comment not necessarily be how people *want* version numbers to behave.  There
# 041428.python.version.line228.comment wouldn't be a problem if people could stick to purely numeric version
# 041429.python.version.line229.comment numbers: just split on period and compare the numbers as tuples.
# 041430.python.version.line230.comment However, people insist on putting letters into their version numbers;
# 041431.python.version.line231.comment the most common purpose seems to be:
# 041432.python.version.line232.comment - indicating a "pre-release" version
# 041433.python.version.line233.comment ('alpha', 'beta', 'a', 'b', 'pre', 'p')
# 041434.python.version.line234.comment - indicating a post-release patch ('p', 'pl', 'patch')
# 041435.python.version.line235.comment but of course this can't cover all version number schemes, and there's
# 041436.python.version.line236.comment no way to know what a programmer means without asking him.
# 041437.python.version.line237.comment
# 041438.python.version.line238.comment The problem is what to do with letters (and other non-numeric
# 041439.python.version.line239.comment characters) in a version number.  The current implementation does the
# 041440.python.version.line240.comment obvious and predictable thing: keep them as strings and compare
# 041441.python.version.line241.comment lexically within a tuple comparison.  This has the desired effect if
# 041442.python.version.line242.comment an appended letter sequence implies something "post-release":
# 041443.python.version.line243.comment eg. "0.99" < "0.99pl14" < "1.0", and "5.001" < "5.001m" < "5.002".
# 041444.python.version.line244.comment
# 041445.python.version.line245.comment However, if letters in a version number imply a pre-release version,
# 041446.python.version.line246.comment the "obvious" thing isn't correct.  Eg. you would expect that
# 041447.python.version.line247.comment "1.5.1" < "1.5.2a2" < "1.5.2", but under the tuple/lexical comparison
# 041448.python.version.line248.comment implemented here, this just isn't so.
# 041449.python.version.line249.comment
# 041450.python.version.line250.comment Two possible solutions come to mind.  The first is to tie the
# 041451.python.version.line251.comment comparison algorithm to a particular set of semantic rules, as has
# 041452.python.version.line252.comment been done in the StrictVersion class above.  This works great as long
# 041453.python.version.line253.comment as everyone can go along with bondage and discipline.  Hopefully a
# 041454.python.version.line254.comment (large) subset of Python module programmers will agree that the
# 041455.python.version.line255.comment particular flavour of bondage and discipline provided by StrictVersion
# 041456.python.version.line256.comment provides enough benefit to be worth using, and will submit their
# 041457.python.version.line257.comment version numbering scheme to its domination.  The free-thinking
# 041458.python.version.line258.comment anarchists in the lot will never give in, though, and something needs
# 041459.python.version.line259.comment to be done to accommodate them.
# 041460.python.version.line260.comment
# 041461.python.version.line261.comment Perhaps a "moderately strict" version class could be implemented that
# 041462.python.version.line262.comment lets almost anything slide (syntactically), and makes some heuristic
# 041463.python.version.line263.comment assumptions about non-digits in version number strings.  This could
# 041464.python.version.line264.comment sink into special-case-hell, though; if I was as talented and
# 041465.python.version.line265.comment idiosyncratic as Larry Wall, I'd go ahead and implement a class that
# 041466.python.version.line266.comment somehow knows that "1.2.1" < "1.2.2a2" < "1.2.2" < "1.2.2pl3", and is
# 041467.python.version.line267.comment just as happy dealing with things like "2g6" and "1.13++".  I don't
# 041468.python.version.line268.comment think I'm smart enough to do it right though.
# 041469.python.version.line269.comment
# 041470.python.version.line270.comment In any case, I've coded the test suite for this module (see
# 041471.python.version.line271.comment ../test/test_version.py) specifically to fail on things like comparing
# 041472.python.version.line272.comment "1.2a2" and "1.2".  That's not because the *code* is doing anything
# 041473.python.version.line273.comment wrong, it's because the simple, obvious design doesn't match my
# 041474.python.version.line274.comment complicated, hairy expectations for real-world version numbers.  It
# 041475.python.version.line275.comment would be a snap to fix the test suite to say, "Yep, LooseVersion does
# 041476.python.version.line276.comment the Right Thing" (ie. the code matches the conception).  But I'd rather
# 041477.python.version.line277.comment have a conception that matches common notions about version numbers.


class LooseVersion(Version):
    """Version numbering for anarchists and software realists.
    Implements the standard interface for version number classes as
    described above.  A version number consists of a series of numbers,
    separated by either periods or strings of letters.  When comparing
    version numbers, the numeric components will be compared
    numerically, and the alphabetic components lexically.  The following
    are all valid version numbers, in no particular order:

        1.5.1
        1.5.2b2
        161
        3.10a
        8.02
        3.4j
        1996.07.12
        3.2.pl0
        3.1.1.6
        2g6
        11g
        0.960923
        2.2beta29
        1.13++
        5.5.kw
        2.0b1pl0

    In fact, there is no such thing as an invalid version number under
    this scheme; the rules for comparison are simple and predictable,
    but may not always give the results you want (for some definition
    of "want").
    """

    component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)

    def parse(self, vstring):
        # 041478.python.version.line315.comment I've given up on thinking I can reconstruct the version string
        # 041479.python.version.line316.comment from the parsed tuple -- so I just store the string here for
        # 041480.python.version.line317.comment use by __str__
        self.vstring = vstring
        components = [x for x in self.component_re.split(vstring) if x and x != '.']
        for i, obj in enumerate(components):
            try:
                components[i] = int(obj)
            except ValueError:
                pass

        self.version = components

    def __str__(self):
        return self.vstring

    def __repr__(self):
        return f"LooseVersion ('{self}')"

    def _cmp(self, other):
        if isinstance(other, str):
            other = LooseVersion(other)
        elif not isinstance(other, LooseVersion):
            return NotImplemented

        if self.version == other.version:
            return 0
        if self.version < other.version:
            return -1
        if self.version > other.version:
            return 1


# 041481.python.version.line348.comment end class LooseVersion
