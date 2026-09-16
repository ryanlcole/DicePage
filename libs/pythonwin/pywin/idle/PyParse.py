import re
import sys

# 038333.python.PyParse.line4.comment Reason last stmt is continued (or C_NONE if it's not).
C_NONE, C_BACKSLASH, C_STRING, C_BRACKET = list(range(4))

if 0:  # for throwaway debugging output

    def dump(*stuff):
        sys.__stdout__.write(" ".join(map(str, stuff)) + "\n")


# 038335.python.PyParse.line13.comment Find what looks like the start of a popular stmt.

_synchre = re.compile(
    r"""
    ^
    [ \t]*
    (?: if
    |   for
    |   while
    |   else
    |   def
    |   return
    |   assert
    |   break
    |   class
    |   continue
    |   elif
    |   try
    |   except
    |   raise
    |   import
    )
    \b
""",
    re.VERBOSE | re.MULTILINE,
).search

# 038336.python.PyParse.line40.comment Match blank line or non-indenting comment line.

_junkre = re.compile(
    r"""
    [ \t]*
    (?: \# \S .* )?
    \n
""",
    re.VERBOSE,
).match

# 038337.python.PyParse.line51.comment Match any flavor of string; the terminating quote is optional
# 038338.python.PyParse.line52.comment so that we're robust in the face of incomplete program text.

_match_stringre = re.compile(
    r"""
    \""" [^"\\]* (?:
                     (?: \\. | "(?!"") )
                     [^"\\]*
                 )*
    (?: \""" )?

|   " [^"\\\n]* (?: \\. [^"\\\n]* )* "?

|   ''' [^'\\]* (?:
                   (?: \\. | '(?!'') )
                   [^'\\]*
                )*
    (?: ''' )?

|   ' [^'\\\n]* (?: \\. [^'\\\n]* )* '?
""",
    re.VERBOSE | re.DOTALL,
).match

# 038339.python.PyParse.line75.comment Match a line that starts with something interesting;
# 038340.python.PyParse.line76.comment used to find the first item of a bracket structure.

_itemre = re.compile(
    r"""
    [ \t]*
    [^\s#\\]    # if we match, m.end()-1 is the interesting char
""",
    re.VERBOSE,
).match

# 038341.python.PyParse.line86.comment Match start of stmts that should be followed by a dedent.

_closere = re.compile(
    r"""
    \s*
    (?: return
    |   break
    |   continue
    |   raise
    |   pass
    )
    \b
""",
    re.VERBOSE,
).match

# 038342.python.PyParse.line102.comment Chew up non-special chars as quickly as possible.  If match is
# 038343.python.PyParse.line103.comment successful, m.end() less 1 is the index of the last boring char
# 038344.python.PyParse.line104.comment matched.  If match is unsuccessful, the string starts with an
# 038345.python.PyParse.line105.comment interesting char.

_chew_ordinaryre = re.compile(
    r"""
    [^[\](){}#'"\\]+
""",
    re.VERBOSE,
).match

# 038346.python.PyParse.line114.comment Build translation table to map uninteresting chars to "x", open
# 038347.python.PyParse.line115.comment brackets to "(", and close brackets to ")".

_tran = ["x"] * 256
for ch in "({[":
    _tran[ord(ch)] = "("
for ch in ")}]":
    _tran[ord(ch)] = ")"
for ch in "\"'\\\n#":
    _tran[ord(ch)] = ch
del ch


class Parser:
    def __init__(self, indentwidth, tabwidth):
        self.indentwidth = indentwidth
        self.tabwidth = tabwidth

    def set_str(self, str):
        assert len(str) == 0 or str[-1] == "\n", f"Oops - have str {str!r}"
        self.str = str
        self.study_level = 0

    # 038348.python.PyParse.line137.comment Return index of a good place to begin parsing, as close to the
    # 038349.python.PyParse.line138.comment end of the string as possible.  This will be the start of some
    # 038350.python.PyParse.line139.comment popular stmt like "if" or "def".  Return None if none found:
    # 038351.python.PyParse.line140.comment the caller should pass more prior context then, if possible, or
    # 038352.python.PyParse.line141.comment if not (the entire program text up until the point of interest
    # 038353.python.PyParse.line142.comment has already been tried) pass 0 to set_lo.
    # 038354.python.PyParse.line143.comment
    # 038355.python.PyParse.line144.comment This will be reliable iff given a reliable is_char_in_string
    # 038356.python.PyParse.line145.comment function, meaning that when it says "no", it's absolutely
    # 038357.python.PyParse.line146.comment guaranteed that the char is not in a string.
    # 038358.python.PyParse.line147.comment
    # 038359.python.PyParse.line148.comment Ack, hack: in the shell window this kills us, because there's
    # 038360.python.PyParse.line149.comment no way to tell the differences between output, >>> etc and
    # 038361.python.PyParse.line150.comment user input.  Indeed, IDLE's first output line makes the rest
    # 038362.python.PyParse.line151.comment look like it's in an unclosed paren!:
    # 038363.python.PyParse.line152.comment Python X.X.X (#0, Apr 13 1999, ...

    def find_good_parse_start(self, use_ps1, is_char_in_string=None):
        str, pos = self.str, None
        if use_ps1:
            # 038364.python.PyParse.line157.comment shell window
            ps1 = "\n" + sys.ps1
            i = str.rfind(ps1)
            if i >= 0:
                pos = i + len(ps1)
                # 038365.python.PyParse.line162.comment make it look like there's a newline instead
                # 038366.python.PyParse.line163.comment of ps1 at the start -- hacking here once avoids
                # 038367.python.PyParse.line164.comment repeated hackery later
                self.str = str[: pos - 1] + "\n" + str[pos:]
            return pos

        # 038368.python.PyParse.line168.comment File window -- real work.
        if not is_char_in_string:
            # 038369.python.PyParse.line170.comment no clue -- make the caller pass everything
            return None

        # 038370.python.PyParse.line173.comment Peek back from the end for a good place to start,
        # 038371.python.PyParse.line174.comment but don't try too often; pos will be left None, or
        # 038372.python.PyParse.line175.comment bumped to a legitimate synch point.
        limit = len(str)
        for tries in range(5):
            i = str.rfind(":\n", 0, limit)
            if i < 0:
                break
            i = str.rfind("\n", 0, i) + 1  # start of colon line
            m = _synchre(str, i, limit)
            if m and not is_char_in_string(m.start()):
                pos = m.start()
                break
            limit = i
        if pos is None:
            # 038374.python.PyParse.line188.comment Nothing looks like a block-opener, or stuff does
            # 038375.python.PyParse.line189.comment but is_char_in_string keeps returning true; most likely
            # 038376.python.PyParse.line190.comment we're in or near a giant string, the colorizer hasn't
            # 038377.python.PyParse.line191.comment caught up enough to be helpful, or there simply *aren't*
            # 038378.python.PyParse.line192.comment any interesting stmts.  In any of these cases we're
            # 038379.python.PyParse.line193.comment going to have to parse the whole thing to be sure, so
            # 038380.python.PyParse.line194.comment give it one last try from the start, but stop wasting
            # 038381.python.PyParse.line195.comment time here regardless of the outcome.
            m = _synchre(str)
            if m and not is_char_in_string(m.start()):
                pos = m.start()
            return pos

        # 038382.python.PyParse.line201.comment Peeking back worked; look forward until _synchre no longer
        # 038383.python.PyParse.line202.comment matches.
        i = pos + 1
        while 1:
            m = _synchre(str, i)
            if m:
                s, i = m.span()
                if not is_char_in_string(s):
                    pos = s
            else:
                break
        return pos

    # 038384.python.PyParse.line214.comment Throw away the start of the string.  Intended to be called with
    # 038385.python.PyParse.line215.comment find_good_parse_start's result.

    def set_lo(self, lo):
        assert lo == 0 or self.str[lo - 1] == "\n"
        if lo > 0:
            self.str = self.str[lo:]

    # 038386.python.PyParse.line222.comment As quickly as humanly possible <wink>, find the line numbers (0-
    # 038387.python.PyParse.line223.comment based) of the non-continuation lines.
    # 038388.python.PyParse.line224.comment Creates self.{goodlines, continuation}.

    def _study1(self):
        if self.study_level >= 1:
            return
        self.study_level = 1

        # 038389.python.PyParse.line231.comment Map all uninteresting characters to "x", all open brackets
        # 038390.python.PyParse.line232.comment to "(", all close brackets to ")", then collapse runs of
        # 038391.python.PyParse.line233.comment uninteresting characters.  This can cut the number of chars
        # 038392.python.PyParse.line234.comment by a factor of 10-40, and so greatly speed the following loop.
        str = self.str
        str = str.translate(_tran)
        str = str.replace("xxxxxxxx", "x")
        str = str.replace("xxxx", "x")
        str = str.replace("xx", "x")
        str = str.replace("xx", "x")
        str = str.replace("\nx", "\n")
        # 038393.python.PyParse.line242.comment note that replacing x\n with \n would be incorrect, because
        # 038394.python.PyParse.line243.comment x may be preceded by a backslash

        # 038395.python.PyParse.line245.comment March over the squashed version of the program, accumulating
        # 038396.python.PyParse.line246.comment the line numbers of non-continued stmts, and determining
        # 038397.python.PyParse.line247.comment whether & why the last stmt is a continuation.
        continuation = C_NONE
        level = lno = 0  # level is nesting level; lno is line number
        self.goodlines = goodlines = [0]
        push_good = goodlines.append
        i, n = 0, len(str)
        while i < n:
            ch = str[i]
            i += 1

            # 038399.python.PyParse.line257.comment cases are checked in decreasing order of frequency
            if ch == "x":
                continue

            if ch == "\n":
                lno += 1
                if level == 0:
                    push_good(lno)
                    # 038400.python.PyParse.line265.comment else we're in an unclosed bracket structure
                continue

            if ch == "(":
                level += 1
                continue

            if ch == ")":
                if level:
                    level -= 1
                    # 038401.python.PyParse.line275.comment else the program is invalid, but we can't complain
                continue

            if ch == '"' or ch == "'":
                # 038402.python.PyParse.line279.comment consume the string
                quote = ch
                if str[i - 1 : i + 2] == quote * 3:
                    quote *= 3
                w = len(quote) - 1
                i += w
                while i < n:
                    ch = str[i]
                    i += 1

                    if ch == "x":
                        continue

                    if str[i - 1 : i + w] == quote:
                        i += w
                        break

                    if ch == "\n":
                        lno += 1
                        if w == 0:
                            # 038403.python.PyParse.line299.comment unterminated single-quoted string
                            if level == 0:
                                push_good(lno)
                            break
                        continue

                    if ch == "\\":
                        assert i < n
                        if str[i] == "\n":
                            lno += 1
                        i += 1
                        continue

                    # 038404.python.PyParse.line312.comment else comment char or paren inside string

                else:
                    # 038405.python.PyParse.line315.comment didn't break out of the loop, so we're still
                    # 038406.python.PyParse.line316.comment inside a string
                    continuation = C_STRING
                continue  # with outer loop

            if ch == "#":
                # 038408.python.PyParse.line321.comment consume the comment
                i = str.find("\n", i)
                assert i >= 0
                continue

            assert ch == "\\"
            assert i < n
            if str[i] == "\n":
                lno += 1
                if i + 1 == n:
                    continuation = C_BACKSLASH
            i += 1

        # 038409.python.PyParse.line334.comment The last stmt may be continued for all 3 reasons.
        # 038410.python.PyParse.line335.comment String continuation takes precedence over bracket
        # 038411.python.PyParse.line336.comment continuation, which beats backslash continuation.
        if continuation != C_STRING and level > 0:
            continuation = C_BRACKET
        self.continuation = continuation

        # 038412.python.PyParse.line341.comment Push the final line number as a sentinel value, regardless of
        # 038413.python.PyParse.line342.comment whether it's continued.
        assert (continuation == C_NONE) == (goodlines[-1] == lno)
        if goodlines[-1] != lno:
            push_good(lno)

    def get_continuation_type(self):
        self._study1()
        return self.continuation

    # 038414.python.PyParse.line351.comment study1 was sufficient to determine the continuation status,
    # 038415.python.PyParse.line352.comment but doing more requires looking at every character.  study2
    # 038416.python.PyParse.line353.comment does this for the last interesting statement in the block.
    # 038417.python.PyParse.line354.comment Creates:
    # 038418.python.PyParse.line355.comment self.stmt_start, stmt_end
    # 038419.python.PyParse.line356.comment slice indices of last interesting stmt
    # 038420.python.PyParse.line357.comment self.lastch
    # 038421.python.PyParse.line358.comment last non-whitespace character before optional trailing
    # 038422.python.PyParse.line359.comment comment
    # 038423.python.PyParse.line360.comment self.lastopenbracketpos
    # 038424.python.PyParse.line361.comment if continuation is C_BRACKET, index of last open bracket

    def _study2(self):
        if self.study_level >= 2:
            return
        self._study1()
        self.study_level = 2

        # 038425.python.PyParse.line369.comment Set p and q to slice indices of last interesting stmt.
        str, goodlines = self.str, self.goodlines
        i = len(goodlines) - 1
        p = len(str)  # index of newest line
        while i:
            assert p
            # 038427.python.PyParse.line375.comment p is the index of the stmt at line number goodlines[i].
            # 038428.python.PyParse.line376.comment Move p back to the stmt at line number goodlines[i-1].
            q = p
            for nothing in range(goodlines[i - 1], goodlines[i]):
                # 038429.python.PyParse.line379.comment tricky: sets p to 0 if no preceding newline
                p = str.rfind("\n", 0, p - 1) + 1
            # 038430.python.PyParse.line381.comment The stmt str[p:q] isn't a continuation, but may be blank
            # 038431.python.PyParse.line382.comment or a non-indenting comment line.
            if _junkre(str, p):
                i -= 1
            else:
                break
        if i == 0:
            # 038432.python.PyParse.line388.comment nothing but junk!
            assert p == 0
            q = p
        self.stmt_start, self.stmt_end = p, q

        # 038433.python.PyParse.line393.comment Analyze this stmt, to find the last open bracket (if any)
        # 038434.python.PyParse.line394.comment and last interesting character (if any).
        lastch = ""
        stack = []  # stack of open bracket indices
        push_stack = stack.append
        while p < q:
            # 038436.python.PyParse.line399.comment suck up all except ()[]{}'"#\\
            m = _chew_ordinaryre(str, p, q)
            if m:
                # 038437.python.PyParse.line402.comment we skipped at least one boring char
                newp = m.end()
                # 038438.python.PyParse.line404.comment back up over totally boring whitespace
                i = newp - 1  # index of last boring char
                while i >= p and str[i] in " \t\n":
                    i -= 1
                if i >= p:
                    lastch = str[i]
                p = newp
                if p >= q:
                    break

            ch = str[p]

            if ch in "([{":
                push_stack(p)
                lastch = ch
                p += 1
                continue

            if ch in ")]}":
                if stack:
                    del stack[-1]
                lastch = ch
                p += 1
                continue

            if ch == '"' or ch == "'":
                # 038440.python.PyParse.line430.comment consume string
                # 038441.python.PyParse.line431.comment Note that study1 did this with a Python loop, but
                # 038442.python.PyParse.line432.comment we use a regexp here; the reason is speed in both
                # 038443.python.PyParse.line433.comment cases; the string may be huge, but study1 pre-squashed
                # 038444.python.PyParse.line434.comment strings to a couple of characters per line.  study1
                # 038445.python.PyParse.line435.comment also needed to keep track of newlines, and we don't
                # 038446.python.PyParse.line436.comment have to.
                lastch = ch
                p = _match_stringre(str, p, q).end()
                continue

            if ch == "#":
                # 038447.python.PyParse.line442.comment consume comment and trailing newline
                p = str.find("\n", p, q) + 1
                assert p > 0
                continue

            assert ch == "\\"
            p += 1  # beyond backslash
            assert p < q
            if str[p] != "\n":
                # 038449.python.PyParse.line451.comment the program is invalid, but can't complain
                lastch = ch + str[p]
            p += 1  # beyond escaped char

        # 038451.python.PyParse.line455.comment end while p < q:

        self.lastch = lastch
        if stack:
            self.lastopenbracketpos = stack[-1]

    # 038452.python.PyParse.line461.comment Assuming continuation is C_BRACKET, return the number
    # 038453.python.PyParse.line462.comment of spaces the next line should be indented.

    def compute_bracket_indent(self):
        self._study2()
        assert self.continuation == C_BRACKET
        j = self.lastopenbracketpos
        str = self.str
        n = len(str)
        origi = i = str.rfind("\n", 0, j) + 1
        j += 1  # one beyond open bracket
        # 038455.python.PyParse.line472.comment find first list item; set i to start of its line
        while j < n:
            m = _itemre(str, j)
            if m:
                j = m.end() - 1  # index of first interesting char
                extra = 0
                break
            else:
                # 038457.python.PyParse.line480.comment this line is junk; advance to next line
                i = j = str.find("\n", j) + 1
        else:
            # 038458.python.PyParse.line483.comment nothing interesting follows the bracket;
            # 038459.python.PyParse.line484.comment reproduce the bracket line's indentation + a level
            j = i = origi
            while str[j] in " \t":
                j += 1
            extra = self.indentwidth
        return len(str[i:j].expandtabs(self.tabwidth)) + extra

    # 038460.python.PyParse.line491.comment Return number of physical lines in last stmt (whether or not
    # 038461.python.PyParse.line492.comment it's an interesting stmt!  this is intended to be called when
    # 038462.python.PyParse.line493.comment continuation is C_BACKSLASH).

    def get_num_lines_in_stmt(self):
        self._study1()
        goodlines = self.goodlines
        return goodlines[-1] - goodlines[-2]

    # 038463.python.PyParse.line500.comment Assuming continuation is C_BACKSLASH, return the number of spaces
    # 038464.python.PyParse.line501.comment the next line should be indented.  Also assuming the new line is
    # 038465.python.PyParse.line502.comment the first one following the initial line of the stmt.

    def compute_backslash_indent(self):
        self._study2()
        assert self.continuation == C_BACKSLASH
        str = self.str
        i = self.stmt_start
        while str[i] in " \t":
            i += 1
        startpos = i

        # 038466.python.PyParse.line513.comment See whether the initial line starts an assignment stmt; i.e.,
        # 038467.python.PyParse.line514.comment look for an = operator
        endpos = str.find("\n", startpos) + 1
        found = level = 0
        while i < endpos:
            ch = str[i]
            if ch in "([{":
                level += 1
                i += 1
            elif ch in ")]}":
                if level:
                    level -= 1
                i += 1
            elif ch == '"' or ch == "'":
                i = _match_stringre(str, i, endpos).end()
            elif ch == "#":
                break
            elif (
                level == 0
                and ch == "="
                and (i == 0 or str[i - 1] not in "=<>!")
                and str[i + 1] != "="
            ):
                found = 1
                break
            else:
                i += 1

        if found:
            # 038468.python.PyParse.line542.comment found a legit =, but it may be the last interesting
            # 038469.python.PyParse.line543.comment thing on the line
            i += 1  # move beyond the =
            found = re.match(r"\s*\\", str[i:endpos]) is None

        if not found:
            # 038471.python.PyParse.line548.comment oh well ... settle for moving beyond the first chunk
            # 038472.python.PyParse.line549.comment of non-whitespace chars
            i = startpos
            while str[i] not in " \t\n":
                i += 1

        return len(str[self.stmt_start : i].expandtabs(self.tabwidth)) + 1

    # 038473.python.PyParse.line556.comment Return the leading whitespace on the initial line of the last
    # 038474.python.PyParse.line557.comment interesting stmt.

    def get_base_indent_string(self):
        self._study2()
        i, n = self.stmt_start, self.stmt_end
        j = i
        str = self.str
        while j < n and str[j] in " \t":
            j += 1
        return str[i:j]

    # 038475.python.PyParse.line568.comment Did the last interesting stmt open a block?

    def is_block_opener(self):
        self._study2()
        return self.lastch == ":"

    # 038476.python.PyParse.line574.comment Did the last interesting stmt close a block?

    def is_block_closer(self):
        self._study2()
        return _closere(self.str, self.stmt_start) is not None

    # 038477.python.PyParse.line580.comment index of last open bracket ({[, or None if none
    lastopenbracketpos = None

    def get_last_open_bracket_pos(self):
        self._study2()
        return self.lastopenbracketpos
