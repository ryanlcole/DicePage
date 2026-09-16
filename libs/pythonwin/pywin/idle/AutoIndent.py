import tokenize

from pywin import default_scintilla_encoding

from . import PyParse


class AutoIndent:
    menudefs = [
        (
            "edit",
            [
                None,
                ("_Indent region", "<<indent-region>>"),
                ("_Dedent region", "<<dedent-region>>"),
                ("Comment _out region", "<<comment-region>>"),
                ("U_ncomment region", "<<uncomment-region>>"),
                ("Tabify region", "<<tabify-region>>"),
                ("Untabify region", "<<untabify-region>>"),
                ("Toggle tabs", "<<toggle-tabs>>"),
                ("New indent width", "<<change-indentwidth>>"),
            ],
        ),
    ]

    keydefs = {
        "<<smart-backspace>>": ["<Key-BackSpace>"],
        "<<newline-and-indent>>": ["<Key-Return>", "<KP_Enter>"],
        "<<smart-indent>>": ["<Key-Tab>"],
    }

    windows_keydefs = {
        "<<indent-region>>": ["<Control-bracketright>"],
        "<<dedent-region>>": ["<Control-bracketleft>"],
        "<<comment-region>>": ["<Alt-Key-3>"],
        "<<uncomment-region>>": ["<Alt-Key-4>"],
        "<<tabify-region>>": ["<Alt-Key-5>"],
        "<<untabify-region>>": ["<Alt-Key-6>"],
        "<<toggle-tabs>>": ["<Alt-Key-t>"],
        "<<change-indentwidth>>": ["<Alt-Key-u>"],
    }

    unix_keydefs = {
        "<<indent-region>>": [
            "<Alt-bracketright>",
            "<Meta-bracketright>",
            "<Control-bracketright>",
        ],
        "<<dedent-region>>": [
            "<Alt-bracketleft>",
            "<Meta-bracketleft>",
            "<Control-bracketleft>",
        ],
        "<<comment-region>>": ["<Alt-Key-3>", "<Meta-Key-3>"],
        "<<uncomment-region>>": ["<Alt-Key-4>", "<Meta-Key-4>"],
        "<<tabify-region>>": ["<Alt-Key-5>", "<Meta-Key-5>"],
        "<<untabify-region>>": ["<Alt-Key-6>", "<Meta-Key-6>"],
        "<<toggle-tabs>>": ["<Alt-Key-t>"],
        "<<change-indentwidth>>": ["<Alt-Key-u>"],
    }

    # 038190.python.AutoIndent.line62.comment usetabs true  -> literal tab characters are used by indent and
    # 038191.python.AutoIndent.line63.comment dedent cmds, possibly mixed with spaces if
    # 038192.python.AutoIndent.line64.comment indentwidth is not a multiple of tabwidth
    # 038193.python.AutoIndent.line65.comment false -> tab characters are converted to spaces by indent
    # 038194.python.AutoIndent.line66.comment and dedent cmds, and ditto TAB keystrokes
    # 038195.python.AutoIndent.line67.comment indentwidth is the number of characters per logical indent level.
    # 038196.python.AutoIndent.line68.comment tabwidth is the display width of a literal tab character.
    # 038197.python.AutoIndent.line69.comment CAUTION:  telling Tk to use anything other than its default
    # 038198.python.AutoIndent.line70.comment tab setting causes it to use an entirely different tabbing algorithm,
    # 038199.python.AutoIndent.line71.comment treating tab stops as fixed distances from the left margin.
    # 038200.python.AutoIndent.line72.comment Nobody expects this, so for now tabwidth should never be changed.
    usetabs = 1
    indentwidth = 4
    tabwidth = 8  # for IDLE use, must remain 8 until Tk is fixed

    # 038202.python.AutoIndent.line77.comment If context_use_ps1 is true, parsing searches back for a ps1 line;
    # 038203.python.AutoIndent.line78.comment else searches for a popular (if, def, ...) Python stmt.
    context_use_ps1 = 0

    # 038204.python.AutoIndent.line81.comment When searching backwards for a reliable place to begin parsing,
    # 038205.python.AutoIndent.line82.comment first start num_context_lines[0] lines back, then
    # 038206.python.AutoIndent.line83.comment num_context_lines[1] lines back if that didn't work, and so on.
    # 038207.python.AutoIndent.line84.comment The last value should be huge (larger than the # of lines in a
    # 038208.python.AutoIndent.line85.comment conceivable file).
    # 038209.python.AutoIndent.line86.comment Making the initial values larger slows things down more often.
    num_context_lines = 50, 500, 5000000

    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text

    def config(self, **options):
        for key, value in options.items():
            if key == "usetabs":
                self.usetabs = value
            elif key == "indentwidth":
                self.indentwidth = value
            elif key == "tabwidth":
                self.tabwidth = value
            elif key == "context_use_ps1":
                self.context_use_ps1 = value
            else:
                raise KeyError(f"bad option name: {key!r}")

    # 038210.python.AutoIndent.line106.comment If ispythonsource and guess are true, guess a good value for
    # 038211.python.AutoIndent.line107.comment indentwidth based on file content (if possible), and if
    # 038212.python.AutoIndent.line108.comment indentwidth != tabwidth set usetabs false.
    # 038213.python.AutoIndent.line109.comment In any case, adjust the Text widget's view of what a tab
    # 038214.python.AutoIndent.line110.comment character means.

    def set_indentation_params(self, ispythonsource, guess=1):
        if guess and ispythonsource:
            i = self.guess_indent()
            if 2 <= i <= 8:
                self.indentwidth = i
            if self.indentwidth != self.tabwidth:
                self.usetabs = 0

        self.editwin.set_tabwidth(self.tabwidth)

    def smart_backspace_event(self, event):
        text = self.text
        first, last = self.editwin.get_selection_indices()
        if first and last:
            text.delete(first, last)
            text.mark_set("insert", first)
            return "break"
        # 038215.python.AutoIndent.line129.comment Delete whitespace left, until hitting a real char or closest
        # 038216.python.AutoIndent.line130.comment preceding virtual tab stop.
        chars = text.get("insert linestart", "insert")
        if chars == "":
            if text.compare("insert", ">", "1.0"):
                # 038217.python.AutoIndent.line134.comment easy: delete preceding newline
                text.delete("insert-1c")
            else:
                text.bell()  # at start of buffer
            return "break"
        if chars[-1] not in " \t":
            # 038219.python.AutoIndent.line140.comment easy: delete preceding real char
            text.delete("insert-1c")
            return "break"
        # 038220.python.AutoIndent.line143.comment Ick.  It may require *inserting* spaces if we back up over a
        # 038221.python.AutoIndent.line144.comment tab character!  This is written to be clear, not fast.
        have = len(chars.expandtabs(self.tabwidth))
        assert have > 0
        want = int((have - 1) / self.indentwidth) * self.indentwidth
        ncharsdeleted = 0
        while 1:
            chars = chars[:-1]
            ncharsdeleted += 1
            have = len(chars.expandtabs(self.tabwidth))
            if have <= want or chars[-1] not in " \t":
                break
        text.undo_block_start()
        text.delete("insert-%dc" % ncharsdeleted, "insert")
        if have < want:
            text.insert("insert", " " * (want - have))
        text.undo_block_stop()
        return "break"

    def smart_indent_event(self, event):
        # 038222.python.AutoIndent.line163.comment if intraline selection:
        # 038223.python.AutoIndent.line164.comment delete it
        # 038224.python.AutoIndent.line165.comment elif multiline selection:
        # 038225.python.AutoIndent.line166.comment do indent-region & return
        # 038226.python.AutoIndent.line167.comment indent one level
        text = self.text
        first, last = self.editwin.get_selection_indices()
        text.undo_block_start()
        try:
            if first and last:
                if index2line(first) != index2line(last):
                    return self.indent_region_event(event)
                text.delete(first, last)
                text.mark_set("insert", first)
            prefix = text.get("insert linestart", "insert")
            raw, effective = classifyws(prefix, self.tabwidth)
            if raw == len(prefix):
                # 038227.python.AutoIndent.line180.comment only whitespace to the left
                self.reindent_to(effective + self.indentwidth)
            else:
                if self.usetabs:
                    pad = "\t"
                else:
                    effective = len(prefix.expandtabs(self.tabwidth))
                    n = self.indentwidth
                    pad = " " * (n - effective % n)
                text.insert("insert", pad)
            text.see("insert")
            return "break"
        finally:
            text.undo_block_stop()

    def newline_and_indent_event(self, event):
        text = self.text
        first, last = self.editwin.get_selection_indices()
        text.undo_block_start()
        try:
            if first and last:
                text.delete(first, last)
                text.mark_set("insert", first)
            line = text.get("insert linestart", "insert")
            i, n = 0, len(line)
            while i < n and line[i] in " \t":
                i += 1
            if i == n:
                # 038228.python.AutoIndent.line208.comment the cursor is in or at leading indentation; just inject
                # 038229.python.AutoIndent.line209.comment an empty line at the start and strip space from current line
                text.delete("insert - %d chars" % i, "insert")
                text.insert("insert linestart", "\n")
                return "break"
            indent = line[:i]
            # 038230.python.AutoIndent.line214.comment strip whitespace before insert point
            i = 0
            while line and line[-1] in " \t":
                line = line[:-1]
                i += 1
            if i:
                text.delete("insert - %d chars" % i, "insert")
            # 038231.python.AutoIndent.line221.comment strip whitespace after insert point
            while text.get("insert") in " \t":
                text.delete("insert")
            # 038232.python.AutoIndent.line224.comment start new line
            text.insert("insert", "\n")

            # 038233.python.AutoIndent.line227.comment adjust indentation for continuations and block
            # 038234.python.AutoIndent.line228.comment open/close first need to find the last stmt
            lno = index2line(text.index("insert"))
            y = PyParse.Parser(self.indentwidth, self.tabwidth)
            for context in self.num_context_lines:
                startat = max(lno - context, 1)
                startatindex = f"{startat!r}.0"
                rawtext = text.get(startatindex, "insert")
                y.set_str(rawtext)
                bod = y.find_good_parse_start(
                    self.context_use_ps1, self._build_char_in_string_func(startatindex)
                )
                if bod is not None or startat == 1:
                    break
            y.set_lo(bod or 0)
            c = y.get_continuation_type()
            if c != PyParse.C_NONE:
                # 038235.python.AutoIndent.line244.comment The current stmt hasn't ended yet.
                if c == PyParse.C_STRING:
                    # 038236.python.AutoIndent.line246.comment inside a string; just mimic the current indent
                    text.insert("insert", indent)
                elif c == PyParse.C_BRACKET:
                    # 038237.python.AutoIndent.line249.comment line up with the first (if any) element of the
                    # 038238.python.AutoIndent.line250.comment last open bracket structure; else indent one
                    # 038239.python.AutoIndent.line251.comment level beyond the indent of the line with the
                    # 038240.python.AutoIndent.line252.comment last open bracket
                    self.reindent_to(y.compute_bracket_indent())
                elif c == PyParse.C_BACKSLASH:
                    # 038241.python.AutoIndent.line255.comment if more than one line in this stmt already, just
                    # 038242.python.AutoIndent.line256.comment mimic the current indent; else if initial line
                    # 038243.python.AutoIndent.line257.comment has a start on an assignment stmt, indent to
                    # 038244.python.AutoIndent.line258.comment beyond leftmost =; else to beyond first chunk of
                    # 038245.python.AutoIndent.line259.comment non-whitespace on initial line
                    if y.get_num_lines_in_stmt() > 1:
                        text.insert("insert", indent)
                    else:
                        self.reindent_to(y.compute_backslash_indent())
                else:
                    raise ValueError(f"bogus continuation type {c!r}")
                return "break"

            # 038246.python.AutoIndent.line268.comment This line starts a brand new stmt; indent relative to
            # 038247.python.AutoIndent.line269.comment indentation of initial line of closest preceding
            # 038248.python.AutoIndent.line270.comment interesting stmt.
            indent = y.get_base_indent_string()
            text.insert("insert", indent)
            if y.is_block_opener():
                self.smart_indent_event(event)
            elif indent and y.is_block_closer():
                self.smart_backspace_event(event)
            return "break"
        finally:
            text.see("insert")
            text.undo_block_stop()

    auto_indent = newline_and_indent_event

    # 038249.python.AutoIndent.line284.comment Our editwin provides a is_char_in_string function that works
    # 038250.python.AutoIndent.line285.comment with a Tk text index, but PyParse only knows about offsets into
    # 038251.python.AutoIndent.line286.comment a string. This builds a function for PyParse that accepts an
    # 038252.python.AutoIndent.line287.comment offset.

    def _build_char_in_string_func(self, startindex):
        def inner(offset, _startindex=startindex, _icis=self.editwin.is_char_in_string):
            return _icis(_startindex + "+%dc" % offset)

        return inner

    def indent_region_event(self, event):
        head, tail, chars, lines = self.get_region()
        for pos in range(len(lines)):
            line = lines[pos]
            if line:
                raw, effective = classifyws(line, self.tabwidth)
                effective += self.indentwidth
                lines[pos] = self._make_blanks(effective) + line[raw:]
        self.set_region(head, tail, chars, lines)
        return "break"

    def dedent_region_event(self, event):
        head, tail, chars, lines = self.get_region()
        for pos in range(len(lines)):
            line = lines[pos]
            if line:
                raw, effective = classifyws(line, self.tabwidth)
                effective = max(effective - self.indentwidth, 0)
                lines[pos] = self._make_blanks(effective) + line[raw:]
        self.set_region(head, tail, chars, lines)
        return "break"

    def comment_region_event(self, event):
        head, tail, chars, lines = self.get_region()
        for pos in range(len(lines) - 1):
            line = lines[pos]
            lines[pos] = "##" + line
        self.set_region(head, tail, chars, lines)

    def uncomment_region_event(self, event):
        head, tail, chars, lines = self.get_region()
        for pos in range(len(lines)):
            line = lines[pos]
            if not line:
                continue
            if line[:2] == "##":
                line = line[2:]
            elif line[:1] == "#":
                line = line[1:]
            lines[pos] = line
        self.set_region(head, tail, chars, lines)

    def tabify_region_event(self, event):
        head, tail, chars, lines = self.get_region()
        tabwidth = self._asktabwidth()
        for pos in range(len(lines)):
            line = lines[pos]
            if line:
                raw, effective = classifyws(line, tabwidth)
                ntabs, nspaces = divmod(effective, tabwidth)
                lines[pos] = "\t" * ntabs + " " * nspaces + line[raw:]
        self.set_region(head, tail, chars, lines)

    def untabify_region_event(self, event):
        head, tail, chars, lines = self.get_region()
        tabwidth = self._asktabwidth()
        for pos in range(len(lines)):
            lines[pos] = lines[pos].expandtabs(tabwidth)
        self.set_region(head, tail, chars, lines)

    def toggle_tabs_event(self, event):
        if self.editwin.askyesno(
            "Toggle tabs",
            "Turn tabs " + ("on", "off")[self.usetabs] + "?",
            parent=self.text,
        ):
            self.usetabs = not self.usetabs
        return "break"

    # 038253.python.AutoIndent.line364.comment XXX this isn't bound to anything -- see class tabwidth comments
    def change_tabwidth_event(self, event):
        new = self._asktabwidth()
        if new != self.tabwidth:
            self.tabwidth = new
            self.set_indentation_params(0, guess=0)
        return "break"

    def change_indentwidth_event(self, event):
        new = self.editwin.askinteger(
            "Indent width",
            "New indent width (1-16)",
            parent=self.text,
            initialvalue=self.indentwidth,
            minvalue=1,
            maxvalue=16,
        )
        if new and new != self.indentwidth:
            self.indentwidth = new
        return "break"

    def get_region(self):
        text = self.text
        first, last = self.editwin.get_selection_indices()
        if first and last:
            head = text.index(first + " linestart")
            tail = text.index(last + "-1c lineend +1c")
        else:
            head = text.index("insert linestart")
            tail = text.index("insert lineend +1c")
        chars = text.get(head, tail)
        lines = chars.split("\n")
        return head, tail, chars, lines

    def set_region(self, head, tail, chars, lines):
        text = self.text
        newchars = "\n".join(lines)
        if newchars == chars:
            text.bell()
            return
        text.tag_remove("sel", "1.0", "end")
        text.mark_set("insert", head)
        text.undo_block_start()
        text.delete(head, tail)
        text.insert(head, newchars)
        text.undo_block_stop()
        text.tag_add("sel", head, "insert")

    # 038254.python.AutoIndent.line412.comment Make string that displays as n leading blanks.

    def _make_blanks(self, n):
        if self.usetabs:
            ntabs, nspaces = divmod(n, self.tabwidth)
            return "\t" * ntabs + " " * nspaces
        else:
            return " " * n

    # 038255.python.AutoIndent.line421.comment Delete from beginning of line to insert point, then reinsert
    # 038256.python.AutoIndent.line422.comment column logical (meaning use tabs if appropriate) spaces.

    def reindent_to(self, column):
        text = self.text
        text.undo_block_start()
        if text.compare("insert linestart", "!=", "insert"):
            text.delete("insert linestart", "insert")
        if column:
            text.insert("insert", self._make_blanks(column))
        text.undo_block_stop()

    def _asktabwidth(self):
        return (
            self.editwin.askinteger(
                "Tab width",
                "Spaces per tab?",
                parent=self.text,
                initialvalue=self.tabwidth,
                minvalue=1,
                maxvalue=16,
            )
            or self.tabwidth
        )

    # 038257.python.AutoIndent.line446.comment Guess indentwidth from text content.
    # 038258.python.AutoIndent.line447.comment Return guessed indentwidth.  This should not be believed unless
    # 038259.python.AutoIndent.line448.comment it's in a reasonable range (e.g., it will be 0 if no indented
    # 038260.python.AutoIndent.line449.comment blocks are found).

    def guess_indent(self):
        opener, indented = IndentSearcher(self.text, self.tabwidth).run()
        if opener and indented:
            raw, indentsmall = classifyws(opener, self.tabwidth)
            raw, indentlarge = classifyws(indented, self.tabwidth)
        else:
            indentsmall = indentlarge = 0
        return indentlarge - indentsmall


# 038261.python.AutoIndent.line461.comment "line.col" -> line, as an int
def index2line(index):
    return int(float(index))


# 038262.python.AutoIndent.line466.comment Look at the leading whitespace in s.
# 038263.python.AutoIndent.line467.comment Return pair (# of leading ws characters,
# 038264.python.AutoIndent.line468.comment effective # of leading blanks after expanding
# 038265.python.AutoIndent.line469.comment tabs to width tabwidth)


def classifyws(s, tabwidth):
    raw = effective = 0
    for ch in s:
        if ch == " ":
            raw += 1
            effective += 1
        elif ch == "\t":
            raw += 1
            effective = (effective // tabwidth + 1) * tabwidth
        else:
            break
    return raw, effective


class IndentSearcher:
    # 038266.python.AutoIndent.line487.comment .run() chews over the Text widget, looking for a block opener
    # 038267.python.AutoIndent.line488.comment and the stmt following it.  Returns a pair,
    # 038268.python.AutoIndent.line489.comment (line containing block opener, line containing stmt)
    # 038269.python.AutoIndent.line490.comment Either or both may be None.

    def __init__(self, text, tabwidth):
        self.text = text
        self.tabwidth = tabwidth
        self.i = self.finished = 0
        self.blkopenline = self.indentedline = None

    def readline(self):
        if self.finished:
            val = ""
        else:
            i = self.i = self.i + 1
            mark = f"{i!r}.0"
            if self.text.compare(mark, ">=", "end"):
                val = ""
            else:
                val = self.text.get(mark, mark + " lineend+1c")
        # 038270.python.AutoIndent.line508.comment hrm - not sure this is correct - the source code may have
        # 038271.python.AutoIndent.line509.comment an encoding declared, but the data will *always* be in
        # 038272.python.AutoIndent.line510.comment default_scintilla_encoding - so if anyone looks at the encoding decl
        # 038273.python.AutoIndent.line511.comment in the source they will be wrong.  I think.  Maybe.  Or something...
        return val.encode(default_scintilla_encoding)

    def run(self):
        OPENERS = ("class", "def", "for", "if", "try", "while")
        INDENT = tokenize.INDENT
        NAME = tokenize.NAME

        save_tabsize = tokenize.tabsize
        tokenize.tabsize = self.tabwidth
        try:
            try:
                for typ, token, start, end, line in tokenize.tokenize(self.readline):
                    if typ == NAME and token in OPENERS:
                        self.blkopenline = line
                    elif typ == INDENT and self.blkopenline:
                        self.indentedline = line
                        break

            except (tokenize.TokenError, IndentationError):
                # 038274.python.AutoIndent.line531.comment since we cut off the tokenizer early, we can trigger
                # 038275.python.AutoIndent.line532.comment spurious errors
                pass
        finally:
            tokenize.tabsize = save_tabsize
        return self.blkopenline, self.indentedline
