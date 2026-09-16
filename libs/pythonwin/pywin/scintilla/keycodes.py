import win32api
import win32con
import win32ui

MAPVK_VK_TO_CHAR = 2

key_name_to_vk = {}
key_code_to_name = {}

_better_names = {
    "escape": "esc",
    "return": "enter",
    "back": "pgup",
    "next": "pgdn",
}


def _fillvkmap():
    # 038882.python.keycodes.line19.comment Pull the VK_names from win32con
    names = [entry for entry in win32con.__dict__ if entry.startswith("VK_")]
    for name in names:
        code = getattr(win32con, name)
        n = name[3:].lower()
        key_name_to_vk[n] = code
        if n in _better_names:
            n = _better_names[n]
            key_name_to_vk[n] = code
        key_code_to_name[code] = n


_fillvkmap()


def get_vk(chardesc):
    if len(chardesc) == 1:
        # 038883.python.keycodes.line36.comment it is a character.
        info = win32api.VkKeyScan(chardesc)
        if info == -1:
            # 038884.python.keycodes.line39.comment Note: returning None, None causes an error when keyboard layout is non-English, see the report below
            # 038885.python.keycodes.line40.comment https://stackoverflow.com/questions/45138084/pythonwin-occasionally-gives-an-error-on-opening
            return 0, 0
        vk = win32api.LOBYTE(info)
        state = win32api.HIBYTE(info)
        modifiers = 0
        if state & 0x1:
            modifiers |= win32con.SHIFT_PRESSED
        if state & 0x2:
            modifiers |= win32con.LEFT_CTRL_PRESSED | win32con.RIGHT_CTRL_PRESSED
        if state & 0x4:
            modifiers |= win32con.LEFT_ALT_PRESSED | win32con.RIGHT_ALT_PRESSED
        return vk, modifiers
    # 038886.python.keycodes.line52.comment must be a 'key name'
    return key_name_to_vk.get(chardesc.lower()), 0


modifiers = {
    "alt": win32con.LEFT_ALT_PRESSED | win32con.RIGHT_ALT_PRESSED,
    "lalt": win32con.LEFT_ALT_PRESSED,
    "ralt": win32con.RIGHT_ALT_PRESSED,
    "ctrl": win32con.LEFT_CTRL_PRESSED | win32con.RIGHT_CTRL_PRESSED,
    "ctl": win32con.LEFT_CTRL_PRESSED | win32con.RIGHT_CTRL_PRESSED,
    "control": win32con.LEFT_CTRL_PRESSED | win32con.RIGHT_CTRL_PRESSED,
    "lctrl": win32con.LEFT_CTRL_PRESSED,
    "lctl": win32con.LEFT_CTRL_PRESSED,
    "rctrl": win32con.RIGHT_CTRL_PRESSED,
    "rctl": win32con.RIGHT_CTRL_PRESSED,
    "shift": win32con.SHIFT_PRESSED,
    "key": 0,  # ignore key tag.
}


def parse_key_name(name):
    name += "-"  # Add a sentinel
    start = pos = 0
    max = len(name)
    toks = []
    while pos < max:
        if name[pos] in "+-":
            tok = name[start:pos]
            # 038889.python.keycodes.line80.comment use the ascii lower() version of tok, so ascii chars require
            # 038890.python.keycodes.line81.comment an explicit shift modifier - ie 'Ctrl+G' should be treated as
            # 038891.python.keycodes.line82.comment 'ctrl+g' - 'ctrl+shift+g' would be needed if desired.
            # 038892.python.keycodes.line83.comment This is mainly to avoid changing all the old keystroke defs
            toks.append(tok.lower())
            pos += 1  # skip the sep
            start = pos
        pos += 1
    flags = 0
    # 038894.python.keycodes.line89.comment do the modifiers
    for tok in toks[:-1]:
        mod = modifiers.get(tok.lower())
        if mod is not None:
            flags |= mod
    # 038895.python.keycodes.line94.comment the key name
    vk, this_flags = get_vk(toks[-1])
    return vk, flags | this_flags


_checks = [
    [  # Shift
        ("Shift", win32con.SHIFT_PRESSED),
    ],
    [  # Ctrl key
        ("Ctrl", win32con.LEFT_CTRL_PRESSED | win32con.RIGHT_CTRL_PRESSED),
        ("LCtrl", win32con.LEFT_CTRL_PRESSED),
        ("RCtrl", win32con.RIGHT_CTRL_PRESSED),
    ],
    [  # Alt key
        ("Alt", win32con.LEFT_ALT_PRESSED | win32con.RIGHT_ALT_PRESSED),
        ("LAlt", win32con.LEFT_ALT_PRESSED),
        ("RAlt", win32con.RIGHT_ALT_PRESSED),
    ],
]


def make_key_name(vk, flags):
    # 038899.python.keycodes.line117.comment Check alt keys.
    flags_done = 0
    parts = []
    for moddata in _checks:
        for name, checkflag in moddata:
            if flags & checkflag:
                parts.append(name)
                flags_done &= checkflag
                break
    if flags_done & flags:
        parts.append(hex(flags & ~flags_done))
    # 038900.python.keycodes.line128.comment Now the key name.
    if vk is None:
        parts.append("<Unknown scan code>")
    else:
        try:
            parts.append(key_code_to_name[vk])
        except KeyError:
            # 038901.python.keycodes.line135.comment Not in our virtual key map - ask Windows what character this
            # 038902.python.keycodes.line136.comment key corresponds to.
            scancode = win32api.MapVirtualKey(vk, MAPVK_VK_TO_CHAR)
            parts.append(chr(scancode))
    sep = "+"
    if sep in parts:
        sep = "-"
    return sep.join([p.capitalize() for p in parts])


def _psc(char):
    sc, mods = get_vk(char)
    print(f"Char {char!r} -> {sc} -> {key_code_to_name.get(sc)}")


def test1():
    for ch in """aA0/?[{}];:'"`~_-+=\\|,<.>/?""":
        _psc(ch)
    for code in ["Home", "End", "Left", "Right", "Up", "Down", "Menu", "Next"]:
        _psc(code)


def _pkn(n):
    vk, flags = parse_key_name(n)
    print(f"{n} -> {vk},{flags} -> {make_key_name(vk, flags)}")


def test2():
    _pkn("ctrl+alt-shift+x")
    _pkn("ctrl-home")
    _pkn("Shift-+")
    _pkn("Shift--")
    _pkn("Shift+-")
    _pkn("Shift++")
    _pkn("LShift-+")
    _pkn("ctl+home")
    _pkn("ctl+enter")
    _pkn("alt+return")
    _pkn("Alt+/")
    _pkn("Alt+BadKeyName")
    _pkn("A")  # an ascii char - should be seen as 'a'
    _pkn("a")
    _pkn("Shift-A")
    _pkn("Shift-a")
    _pkn("a")
    _pkn("(")
    _pkn("Ctrl+(")
    _pkn("Ctrl+Shift-8")
    _pkn("Ctrl+*")
    _pkn("{")
    _pkn("!")
    _pkn(".")


if __name__ == "__main__":
    test2()
