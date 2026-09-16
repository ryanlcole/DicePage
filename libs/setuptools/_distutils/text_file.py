"""text_file

provides the TextFile class, which gives an interface to text files
that (optionally) takes care of stripping comments, ignoring blank
lines, and joining lines with backslashes."""

import sys


class TextFile:
    """Provides a file-like object that takes care of all the things you
    commonly want to do when processing a text file that has some
    line-by-line syntax: strip comments (as long as "#" is your
    comment character), skip blank lines, join adjacent lines by
    escaping the newline (ie. backslash at end of line), strip
    leading and/or trailing whitespace.  All of these are optional
    and independently controllable.

    Provides a 'warn()' method so you can generate warning messages that
    report physical line number, even if the logical line in question
    spans multiple physical lines.  Also provides 'unreadline()' for
    implementing line-at-a-time lookahead.

    Constructor is called as:

        TextFile (filename=None, file=None, **options)

    It bombs (RuntimeError) if both 'filename' and 'file' are None;
    'filename' should be a string, and 'file' a file object (or
    something that provides 'readline()' and 'close()' methods).  It is
    recommended that you supply at least 'filename', so that TextFile
    can include it in warning messages.  If 'file' is not supplied,
    TextFile creates its own using 'io.open()'.

    The options are all boolean, and affect the value returned by
    'readline()':
      strip_comments [default: true]
        strip from "#" to end-of-line, as well as any whitespace
        leading up to the "#" -- unless it is escaped by a backslash
      lstrip_ws [default: false]
        strip leading whitespace from each line before returning it
      rstrip_ws [default: true]
        strip trailing whitespace (including line terminator!) from
        each line before returning it
      skip_blanks [default: true}
        skip lines that are empty *after* stripping comments and
        whitespace.  (If both lstrip_ws and rstrip_ws are false,
        then some lines may consist of solely whitespace: these will
        *not* be skipped, even if 'skip_blanks' is true.)
      join_lines [default: false]
        if a backslash is the last non-newline character on a line
        after stripping comments and whitespace, join the following line
        to it to form one "logical line"; if N consecutive lines end
        with a backslash, then N+1 physical lines will be joined to
        form one logical line.
      collapse_join [default: false]
        strip leading whitespace from lines that are joined to their
        predecessor; only matters if (join_lines and not lstrip_ws)
      errors [default: 'strict']
        error handler used to decode the file content

    Note that since 'rstrip_ws' can strip the trailing newline, the
    semantics of 'readline()' must differ from those of the builtin file
    object's 'readline()' method!  In particular, 'readline()' returns
    None for end-of-file: an empty string might just be a blank line (or
    an all-whitespace line), if 'rstrip_ws' is true but 'skip_blanks' is
    not."""

    default_options = {
        'strip_comments': 1,
        'skip_blanks': 1,
        'lstrip_ws': 0,
        'rstrip_ws': 1,
        'join_lines': 0,
        'collapse_join': 0,
        'errors': 'strict',
    }

    def __init__(self, filename=None, file=None, **options):
        """Construct a new TextFile object.  At least one of 'filename'
        (a string) and 'file' (a file-like object) must be supplied.
        They keyword argument options are described above and affect
        the values returned by 'readline()'."""
        if filename is None and file is None:
            raise RuntimeError(
                "you must supply either or both of 'filename' and 'file'"
            )

        # 041279.python.text_file.line89.comment set values for all options -- either from client option hash
        # 041280.python.text_file.line90.comment or fallback to default_options
        for opt in self.default_options.keys():
            if opt in options:
                setattr(self, opt, options[opt])
            else:
                setattr(self, opt, self.default_options[opt])

        # 041281.python.text_file.line97.comment sanity check client option hash
        for opt in options.keys():
            if opt not in self.default_options:
                raise KeyError(f"invalid TextFile option '{opt}'")

        if file is None:
            self.open(filename)
        else:
            self.filename = filename
            self.file = file
            self.current_line = 0  # assuming that file is at BOF!

        # 041283.python.text_file.line109.comment 'linebuf' is a stack of lines that will be emptied before we
        # 041284.python.text_file.line110.comment actually read from the file; it's only populated by an
        # 041285.python.text_file.line111.comment 'unreadline()' operation
        self.linebuf = []

    def open(self, filename):
        """Open a new file named 'filename'.  This overrides both the
        'filename' and 'file' arguments to the constructor."""
        self.filename = filename
        self.file = open(self.filename, errors=self.errors, encoding='utf-8')
        self.current_line = 0

    def close(self):
        """Close the current file and forget everything we know about it
        (filename, current line number)."""
        file = self.file
        self.file = None
        self.filename = None
        self.current_line = None
        file.close()

    def gen_error(self, msg, line=None):
        outmsg = []
        if line is None:
            line = self.current_line
        outmsg.append(self.filename + ", ")
        if isinstance(line, (list, tuple)):
            outmsg.append("lines {}-{}: ".format(*line))
        else:
            outmsg.append(f"line {int(line)}: ")
        outmsg.append(str(msg))
        return "".join(outmsg)

    def error(self, msg, line=None):
        raise ValueError("error: " + self.gen_error(msg, line))

    def warn(self, msg, line=None):
        """Print (to stderr) a warning message tied to the current logical
        line in the current file.  If the current logical line in the
        file spans multiple physical lines, the warning refers to the
        whole range, eg. "lines 3-5".  If 'line' supplied, it overrides
        the current line number; it may be a list or tuple to indicate a
        range of physical lines, or an integer for a single physical
        line."""
        sys.stderr.write("warning: " + self.gen_error(msg, line) + "\n")

    def readline(self):  # noqa: C901
        """Read and return a single logical line from the current file (or
        from an internal buffer if lines have previously been "unread"
        with 'unreadline()').  If the 'join_lines' option is true, this
        may involve reading multiple physical lines concatenated into a
        single string.  Updates the current line number, so calling
        'warn()' after 'readline()' emits a warning about the physical
        line(s) just read.  Returns None on end-of-file, since the empty
        string can occur if 'rstrip_ws' is true but 'strip_blanks' is
        not."""
        # 041287.python.text_file.line165.comment If any "unread" lines waiting in 'linebuf', return the top
        # 041288.python.text_file.line166.comment one.  (We don't actually buffer read-ahead data -- lines only
        # 041289.python.text_file.line167.comment get put in 'linebuf' if the client explicitly does an
        # 041290.python.text_file.line168.comment 'unreadline()'.
        if self.linebuf:
            line = self.linebuf[-1]
            del self.linebuf[-1]
            return line

        buildup_line = ''

        while True:
            # 041291.python.text_file.line177.comment read the line, make it None if EOF
            line = self.file.readline()
            if line == '':
                line = None

            if self.strip_comments and line:
                # 041292.python.text_file.line183.comment Look for the first "#" in the line.  If none, never
                # 041293.python.text_file.line184.comment mind.  If we find one and it's the first character, or
                # 041294.python.text_file.line185.comment is not preceded by "\", then it starts a comment --
                # 041295.python.text_file.line186.comment strip the comment, strip whitespace before it, and
                # 041296.python.text_file.line187.comment carry on.  Otherwise, it's just an escaped "#", so
                # 041297.python.text_file.line188.comment unescape it (and any other escaped "#"'s that might be
                # 041298.python.text_file.line189.comment lurking in there) and otherwise leave the line alone.

                pos = line.find("#")
                if pos == -1:  # no "#" -- no comments
                    pass

                # 041300.python.text_file.line195.comment It's definitely a comment -- either "#" is the first
                # 041301.python.text_file.line196.comment character, or it's elsewhere and unescaped.
                elif pos == 0 or line[pos - 1] != "\\":
                    # 041302.python.text_file.line198.comment Have to preserve the trailing newline, because it's
                    # 041303.python.text_file.line199.comment the job of a later step (rstrip_ws) to remove it --
                    # 041304.python.text_file.line200.comment and if rstrip_ws is false, we'd better preserve it!
                    # 041305.python.text_file.line201.comment (NB. this means that if the final line is all comment
                    # 041306.python.text_file.line202.comment and has no trailing newline, we will think that it's
                    # 041307.python.text_file.line203.comment EOF; I think that's OK.)
                    eol = (line[-1] == '\n') and '\n' or ''
                    line = line[0:pos] + eol

                    # 041308.python.text_file.line207.comment If all that's left is whitespace, then skip line
                    # 041309.python.text_file.line208.comment *now*, before we try to join it to 'buildup_line' --
                    # 041310.python.text_file.line209.comment that way constructs like
                    # 041311.python.text_file.line210.comment hello \\
                    # 041312.python.text_file.line211.comment # comment that should be ignored
                    # 041313.python.text_file.line212.comment there
                    # 041314.python.text_file.line213.comment result in "hello there".
                    if line.strip() == "":
                        continue
                else:  # it's an escaped "#"
                    line = line.replace("\\#", "#")

            # 041316.python.text_file.line219.comment did previous line end with a backslash? then accumulate
            if self.join_lines and buildup_line:
                # 041317.python.text_file.line221.comment oops: end of file
                if line is None:
                    self.warn("continuation line immediately precedes end-of-file")
                    return buildup_line

                if self.collapse_join:
                    line = line.lstrip()
                line = buildup_line + line

                # 041318.python.text_file.line230.comment careful: pay attention to line number when incrementing it
                if isinstance(self.current_line, list):
                    self.current_line[1] = self.current_line[1] + 1
                else:
                    self.current_line = [self.current_line, self.current_line + 1]
            # 041319.python.text_file.line235.comment just an ordinary line, read it as usual
            else:
                if line is None:  # eof
                    return None

                # 041321.python.text_file.line240.comment still have to be careful about incrementing the line number!
                if isinstance(self.current_line, list):
                    self.current_line = self.current_line[1] + 1
                else:
                    self.current_line = self.current_line + 1

            # 041322.python.text_file.line246.comment strip whitespace however the client wants (leading and
            # 041323.python.text_file.line247.comment trailing, or one or the other, or neither)
            if self.lstrip_ws and self.rstrip_ws:
                line = line.strip()
            elif self.lstrip_ws:
                line = line.lstrip()
            elif self.rstrip_ws:
                line = line.rstrip()

            # 041324.python.text_file.line255.comment blank line (whether we rstrip'ed or not)? skip to next line
            # 041325.python.text_file.line256.comment if appropriate
            if line in ('', '\n') and self.skip_blanks:
                continue

            if self.join_lines:
                if line[-1] == '\\':
                    buildup_line = line[:-1]
                    continue

                if line[-2:] == '\\\n':
                    buildup_line = line[0:-2] + '\n'
                    continue

            # 041326.python.text_file.line269.comment well, I guess there's some actual content there: return it
            return line

    def readlines(self):
        """Read and return the list of all logical lines remaining in the
        current file."""
        lines = []
        while True:
            line = self.readline()
            if line is None:
                return lines
            lines.append(line)

    def unreadline(self, line):
        """Push 'line' (a string) onto an internal buffer that will be
        checked by future 'readline()' calls.  Handy for implementing
        a parser with line-at-a-time lookahead."""
        self.linebuf.append(line)
