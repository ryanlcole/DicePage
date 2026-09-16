"""distutils.fancy_getopt

Wrapper around the standard getopt module that provides the following
additional features:
  * short and long options are tied together
  * options have help strings, so fancy_getopt could potentially
    create a complete usage summary
  * options set attributes of a passed-in object
"""

from __future__ import annotations

import getopt
import re
import string
import sys
from collections.abc import Sequence
from typing import Any

from .errors import DistutilsArgError, DistutilsGetoptError

# 040627.python.fancy_getopt.line22.comment Much like command_re in distutils.core, this is close to but not quite
# 040628.python.fancy_getopt.line23.comment the same as a Python NAME -- except, in the spirit of most GNU
# 040629.python.fancy_getopt.line24.comment utilities, we use '-' in place of '_'.  (The spirit of LISP lives on!)
# 040630.python.fancy_getopt.line25.comment The similarities to NAME are again not a coincidence...
longopt_pat = r'[a-zA-Z](?:[a-zA-Z0-9-]*)'
longopt_re = re.compile(rf'^{longopt_pat}$')

# 040631.python.fancy_getopt.line29.comment For recognizing "negative alias" options, eg. "quiet=!verbose"
neg_alias_re = re.compile(f"^({longopt_pat})=!({longopt_pat})$")

# 040632.python.fancy_getopt.line32.comment This is used to translate long options to legitimate Python identifiers
# 040633.python.fancy_getopt.line33.comment (for use as attributes of some object).
longopt_xlate = str.maketrans('-', '_')


class FancyGetopt:
    """Wrapper around the standard 'getopt()' module that provides some
    handy extra functionality:
      * short and long options are tied together
      * options have help strings, and help text can be assembled
        from them
      * options set attributes of a passed-in object
      * boolean options can have "negative aliases" -- eg. if
        --quiet is the "negative alias" of --verbose, then "--quiet"
        on the command line sets 'verbose' to false
    """

    def __init__(self, option_table=None):
        # 040634.python.fancy_getopt.line50.comment The option table is (currently) a list of tuples.  The
        # 040635.python.fancy_getopt.line51.comment tuples may have 3 or four values:
        # 040636.python.fancy_getopt.line52.comment (long_option, short_option, help_string [, repeatable])
        # 040637.python.fancy_getopt.line53.comment if an option takes an argument, its long_option should have '='
        # 040638.python.fancy_getopt.line54.comment appended; short_option should just be a single character, no ':'
        # 040639.python.fancy_getopt.line55.comment in any case.  If a long_option doesn't have a corresponding
        # 040640.python.fancy_getopt.line56.comment short_option, short_option should be None.  All option tuples
        # 040641.python.fancy_getopt.line57.comment must have long options.
        self.option_table = option_table

        # 040642.python.fancy_getopt.line60.comment 'option_index' maps long option names to entries in the option
        # 040643.python.fancy_getopt.line61.comment table (ie. those 3-tuples).
        self.option_index = {}
        if self.option_table:
            self._build_index()

        # 040644.python.fancy_getopt.line66.comment 'alias' records (duh) alias options; {'foo': 'bar'} means
        # 040645.python.fancy_getopt.line67.comment --foo is an alias for --bar
        self.alias = {}

        # 040646.python.fancy_getopt.line70.comment 'negative_alias' keeps track of options that are the boolean
        # 040647.python.fancy_getopt.line71.comment opposite of some other option
        self.negative_alias = {}

        # 040648.python.fancy_getopt.line74.comment These keep track of the information in the option table.  We
        # 040649.python.fancy_getopt.line75.comment don't actually populate these structures until we're ready to
        # 040650.python.fancy_getopt.line76.comment parse the command-line, since the 'option_table' passed in here
        # 040651.python.fancy_getopt.line77.comment isn't necessarily the final word.
        self.short_opts = []
        self.long_opts = []
        self.short2long = {}
        self.attr_name = {}
        self.takes_arg = {}

        # 040652.python.fancy_getopt.line84.comment And 'option_order' is filled up in 'getopt()'; it records the
        # 040653.python.fancy_getopt.line85.comment original order of options (and their values) on the command-line,
        # 040654.python.fancy_getopt.line86.comment but expands short options, converts aliases, etc.
        self.option_order = []

    def _build_index(self):
        self.option_index.clear()
        for option in self.option_table:
            self.option_index[option[0]] = option

    def set_option_table(self, option_table):
        self.option_table = option_table
        self._build_index()

    def add_option(self, long_option, short_option=None, help_string=None):
        if long_option in self.option_index:
            raise DistutilsGetoptError(
                f"option conflict: already an option '{long_option}'"
            )
        else:
            option = (long_option, short_option, help_string)
            self.option_table.append(option)
            self.option_index[long_option] = option

    def has_option(self, long_option):
        """Return true if the option table for this parser has an
        option with long name 'long_option'."""
        return long_option in self.option_index

    def get_attr_name(self, long_option):
        """Translate long option name 'long_option' to the form it
        has as an attribute of some object: ie., translate hyphens
        to underscores."""
        return long_option.translate(longopt_xlate)

    def _check_alias_dict(self, aliases, what):
        assert isinstance(aliases, dict)
        for alias, opt in aliases.items():
            if alias not in self.option_index:
                raise DistutilsGetoptError(
                    f"invalid {what} '{alias}': option '{alias}' not defined"
                )
            if opt not in self.option_index:
                raise DistutilsGetoptError(
                    f"invalid {what} '{alias}': aliased option '{opt}' not defined"
                )

    def set_aliases(self, alias):
        """Set the aliases for this option parser."""
        self._check_alias_dict(alias, "alias")
        self.alias = alias

    def set_negative_aliases(self, negative_alias):
        """Set the negative aliases for this option parser.
        'negative_alias' should be a dictionary mapping option names to
        option names, both the key and value must already be defined
        in the option table."""
        self._check_alias_dict(negative_alias, "negative alias")
        self.negative_alias = negative_alias

    def _grok_option_table(self):  # noqa: C901
        """Populate the various data structures that keep tabs on the
        option table.  Called by 'getopt()' before it can do anything
        worthwhile.
        """
        self.long_opts = []
        self.short_opts = []
        self.short2long.clear()
        self.repeat = {}

        for option in self.option_table:
            if len(option) == 3:
                long, short, help = option
                repeat = 0
            elif len(option) == 4:
                long, short, help, repeat = option
            else:
                # 040656.python.fancy_getopt.line161.comment the option table is part of the code, so simply
                # 040657.python.fancy_getopt.line162.comment assert that it is correct
                raise ValueError(f"invalid option tuple: {option!r}")

            # 040658.python.fancy_getopt.line165.comment Type- and value-check the option names
            if not isinstance(long, str) or len(long) < 2:
                raise DistutilsGetoptError(
                    f"invalid long option '{long}': must be a string of length >= 2"
                )

            if not ((short is None) or (isinstance(short, str) and len(short) == 1)):
                raise DistutilsGetoptError(
                    f"invalid short option '{short}': must a single character or None"
                )

            self.repeat[long] = repeat
            self.long_opts.append(long)

            if long[-1] == '=':  # option takes an argument?
                if short:
                    short = short + ':'
                long = long[0:-1]
                self.takes_arg[long] = True
            else:
                # 040660.python.fancy_getopt.line185.comment Is option is a "negative alias" for some other option (eg.
                # 040661.python.fancy_getopt.line186.comment "quiet" == "!verbose")?
                alias_to = self.negative_alias.get(long)
                if alias_to is not None:
                    if self.takes_arg[alias_to]:
                        raise DistutilsGetoptError(
                            f"invalid negative alias '{long}': "
                            f"aliased option '{alias_to}' takes a value"
                        )

                    self.long_opts[-1] = long  # XXX redundant?!
                self.takes_arg[long] = False

            # 040663.python.fancy_getopt.line198.comment If this is an alias option, make sure its "takes arg" flag is
            # 040664.python.fancy_getopt.line199.comment the same as the option it's aliased to.
            alias_to = self.alias.get(long)
            if alias_to is not None:
                if self.takes_arg[long] != self.takes_arg[alias_to]:
                    raise DistutilsGetoptError(
                        f"invalid alias '{long}': inconsistent with "
                        f"aliased option '{alias_to}' (one of them takes a value, "
                        "the other doesn't"
                    )

            # 040665.python.fancy_getopt.line209.comment Now enforce some bondage on the long option name, so we can
            # 040666.python.fancy_getopt.line210.comment later translate it to an attribute name on some object.  Have
            # 040667.python.fancy_getopt.line211.comment to do this a bit late to make sure we've removed any trailing
            # 040668.python.fancy_getopt.line212.comment '='.
            if not longopt_re.match(long):
                raise DistutilsGetoptError(
                    f"invalid long option name '{long}' "
                    "(must be letters, numbers, hyphens only"
                )

            self.attr_name[long] = self.get_attr_name(long)
            if short:
                self.short_opts.append(short)
                self.short2long[short[0]] = long

    def getopt(self, args: Sequence[str] | None = None, object=None):  # noqa: C901
        """Parse command-line options in args. Store as attributes on object.

        If 'args' is None or not supplied, uses 'sys.argv[1:]'.  If
        'object' is None or not supplied, creates a new OptionDummy
        object, stores option values there, and returns a tuple (args,
        object).  If 'object' is supplied, it is modified in place and
        'getopt()' just returns 'args'; in both cases, the returned
        'args' is a modified copy of the passed-in 'args' list, which
        is left untouched.
        """
        if args is None:
            args = sys.argv[1:]
        if object is None:
            object = OptionDummy()
            created_object = True
        else:
            created_object = False

        self._grok_option_table()

        short_opts = ' '.join(self.short_opts)
        try:
            opts, args = getopt.getopt(args, short_opts, self.long_opts)
        except getopt.error as msg:
            raise DistutilsArgError(msg)

        for opt, val in opts:
            if len(opt) == 2 and opt[0] == '-':  # it's a short option
                opt = self.short2long[opt[1]]
            else:
                assert len(opt) > 2 and opt[:2] == '--'
                opt = opt[2:]

            alias = self.alias.get(opt)
            if alias:
                opt = alias

            if not self.takes_arg[opt]:  # boolean option?
                assert val == '', "boolean option can't have value"
                alias = self.negative_alias.get(opt)
                if alias:
                    opt = alias
                    val = 0
                else:
                    val = 1

            attr = self.attr_name[opt]
            # 040672.python.fancy_getopt.line272.comment The only repeating option at the moment is 'verbose'.
            # 040673.python.fancy_getopt.line273.comment It has a negative option -q quiet, which should set verbose = False.
            if val and self.repeat.get(attr) is not None:
                val = getattr(object, attr, 0) + 1
            setattr(object, attr, val)
            self.option_order.append((opt, val))

        # 040674.python.fancy_getopt.line279.comment for opts
        if created_object:
            return args, object
        else:
            return args

    def get_option_order(self):
        """Returns the list of (option, value) tuples processed by the
        previous run of 'getopt()'.  Raises RuntimeError if
        'getopt()' hasn't been called yet.
        """
        if self.option_order is None:
            raise RuntimeError("'getopt()' hasn't been called yet")
        else:
            return self.option_order

    def generate_help(self, header=None):  # noqa: C901
        """Generate help text (a list of strings, one per suggested line of
        output) from the option table for this FancyGetopt object.
        """
        # 040676.python.fancy_getopt.line299.comment Blithely assume the option table is good: probably wouldn't call
        # 040677.python.fancy_getopt.line300.comment 'generate_help()' unless you've already called 'getopt()'.

        # 040678.python.fancy_getopt.line302.comment First pass: determine maximum length of long option names
        max_opt = 0
        for option in self.option_table:
            long = option[0]
            short = option[1]
            ell = len(long)
            if long[-1] == '=':
                ell = ell - 1
            if short is not None:
                ell = ell + 5  # " (-x)" where short == 'x'
            if ell > max_opt:
                max_opt = ell

        opt_width = max_opt + 2 + 2 + 2  # room for indent + dashes + gutter

        # 040681.python.fancy_getopt.line317.comment Typical help block looks like this:
        # 040682.python.fancy_getopt.line318.comment --foo       controls foonabulation
        # 040683.python.fancy_getopt.line319.comment Help block for longest option looks like this:
        # 040684.python.fancy_getopt.line320.comment --flimflam  set the flim-flam level
        # 040685.python.fancy_getopt.line321.comment and with wrapped text:
        # 040686.python.fancy_getopt.line322.comment --flimflam  set the flim-flam level (must be between
        # 040687.python.fancy_getopt.line323.comment 0 and 100, except on Tuesdays)
        # 040688.python.fancy_getopt.line324.comment Options with short names will have the short name shown (but
        # 040689.python.fancy_getopt.line325.comment it doesn't contribute to max_opt):
        # 040690.python.fancy_getopt.line326.comment --foo (-f)  controls foonabulation
        # 040691.python.fancy_getopt.line327.comment If adding the short option would make the left column too wide,
        # 040692.python.fancy_getopt.line328.comment we push the explanation off to the next line
        # 040693.python.fancy_getopt.line329.comment --flimflam (-l)
        # 040694.python.fancy_getopt.line330.comment set the flim-flam level
        # 040695.python.fancy_getopt.line331.comment Important parameters:
        # 040696.python.fancy_getopt.line332.comment - 2 spaces before option block start lines
        # 040697.python.fancy_getopt.line333.comment - 2 dashes for each long option name
        # 040698.python.fancy_getopt.line334.comment - min. 2 spaces between option and explanation (gutter)
        # 040699.python.fancy_getopt.line335.comment - 5 characters (incl. space) for short option name

        # 040700.python.fancy_getopt.line337.comment Now generate lines of help text.  (If 80 columns were good enough
        # 040701.python.fancy_getopt.line338.comment for Jesus, then 78 columns are good enough for me!)
        line_width = 78
        text_width = line_width - opt_width
        big_indent = ' ' * opt_width
        if header:
            lines = [header]
        else:
            lines = ['Option summary:']

        for option in self.option_table:
            long, short, help = option[:3]
            text = wrap_text(help, text_width)
            if long[-1] == '=':
                long = long[0:-1]

            # 040702.python.fancy_getopt.line353.comment Case 1: no short option at all (makes life easy)
            if short is None:
                if text:
                    lines.append(f"  --{long:<{max_opt}}  {text[0]}")
                else:
                    lines.append(f"  --{long:<{max_opt}}")

            # 040703.python.fancy_getopt.line360.comment Case 2: we have a short option, so we have to include it
            # 040704.python.fancy_getopt.line361.comment just after the long option
            else:
                opt_names = f"{long} (-{short})"
                if text:
                    lines.append(f"  --{opt_names:<{max_opt}}  {text[0]}")
                else:
                    lines.append(f"  --{opt_names:<{max_opt}}")

            for ell in text[1:]:
                lines.append(big_indent + ell)
        return lines

    def print_help(self, header=None, file=None):
        if file is None:
            file = sys.stdout
        for line in self.generate_help(header):
            file.write(line + "\n")


def fancy_getopt(options, negative_opt, object, args: Sequence[str] | None):
    parser = FancyGetopt(options)
    parser.set_negative_aliases(negative_opt)
    return parser.getopt(args, object)


WS_TRANS = {ord(_wschar): ' ' for _wschar in string.whitespace}


def wrap_text(text, width):
    """wrap_text(text : string, width : int) -> [string]

    Split 'text' into multiple lines of no more than 'width' characters
    each, and return the list of strings that results.
    """
    if text is None:
        return []
    if len(text) <= width:
        return [text]

    text = text.expandtabs()
    text = text.translate(WS_TRANS)
    chunks = re.split(r'( +|-+)', text)
    chunks = [ch for ch in chunks if ch]  # ' - ' results in empty strings
    lines = []

    while chunks:
        cur_line = []  # list of chunks (to-be-joined)
        cur_len = 0  # length of current line

        while chunks:
            ell = len(chunks[0])
            if cur_len + ell <= width:  # can squeeze (at least) this chunk in
                cur_line.append(chunks[0])
                del chunks[0]
                cur_len = cur_len + ell
            else:  # this line is full
                # 040710.python.fancy_getopt.line417.comment drop last chunk if all space
                if cur_line and cur_line[-1][0] == ' ':
                    del cur_line[-1]
                break

        if chunks:  # any chunks left to process?
            # 040712.python.fancy_getopt.line423.comment if the current line is still empty, then we had a single
            # 040713.python.fancy_getopt.line424.comment chunk that's too big too fit on a line -- so we break
            # 040714.python.fancy_getopt.line425.comment down and break it up at the line width
            if cur_len == 0:
                cur_line.append(chunks[0][0:width])
                chunks[0] = chunks[0][width:]

            # 040715.python.fancy_getopt.line430.comment all-whitespace chunks at the end of a line can be discarded
            # 040716.python.fancy_getopt.line431.comment (and we know from the re.split above that if a chunk has
            # 040717.python.fancy_getopt.line432.comment *any* whitespace, it is *all* whitespace)
            if chunks[0][0] == ' ':
                del chunks[0]

        # 040718.python.fancy_getopt.line436.comment and store this line in the list-of-all-lines -- as a single
        # 040719.python.fancy_getopt.line437.comment string, of course!
        lines.append(''.join(cur_line))

    return lines


def translate_longopt(opt):
    """Convert a long option name to a valid Python identifier by
    changing "-" to "_".
    """
    return opt.translate(longopt_xlate)


class OptionDummy:
    """Dummy class just used as a place to hold command-line option
    values as instance attributes."""

    def __init__(self, options: Sequence[Any] = []):
        """Create a new OptionDummy instance.  The attributes listed in
        'options' will be initialized to None."""
        for opt in options:
            setattr(self, opt, None)


if __name__ == "__main__":
    text = """\
Tra-la-la, supercalifragilisticexpialidocious.
How *do* you spell that odd word, anyways?
(Someone ask Mary -- she'll know [or she'll
say, "How should I know?"].)"""

    for w in (10, 20, 30, 40):
        print(f"width: {w}")
        print("\n".join(wrap_text(text, w)))
        print()
