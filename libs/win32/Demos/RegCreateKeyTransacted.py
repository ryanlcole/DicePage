import win32api
import win32con
import win32transaction

keyname = "Pywin32 test transacted registry functions"
subkeyname = "test transacted subkey"
classname = "Transacted Class"

trans = win32transaction.CreateTransaction(Description="test RegCreateKeyTransacted")
key, disp = win32api.RegCreateKeyEx(
    win32con.HKEY_CURRENT_USER,
    keyname,
    samDesired=win32con.KEY_ALL_ACCESS,
    Class=classname,
)
# 046009.python.RegCreateKeyTransacted.line16.comment # clean up any existing keys
for subk in win32api.RegEnumKeyExW(key):
    win32api.RegDeleteKey(key, subk[0])

# 046010.python.RegCreateKeyTransacted.line20.comment # reopen key in transacted mode
transacted_key = win32api.RegOpenKeyTransacted(
    Key=win32con.HKEY_CURRENT_USER,
    SubKey=keyname,
    Transaction=trans,
    samDesired=win32con.KEY_ALL_ACCESS,
)
subkey, disp = win32api.RegCreateKeyEx(
    transacted_key,
    subkeyname,
    Transaction=trans,
    samDesired=win32con.KEY_ALL_ACCESS,
    Class=classname,
)

# 046011.python.RegCreateKeyTransacted.line35.comment # Newly created key should not be visible from non-transacted handle
subkeys = [s[0] for s in win32api.RegEnumKeyExW(key)]
assert subkeyname not in subkeys

transacted_subkeys = [s[0] for s in win32api.RegEnumKeyExW(transacted_key)]
assert subkeyname in transacted_subkeys

# 046012.python.RegCreateKeyTransacted.line42.comment # Key should be visible to non-transacted handle after commit
win32transaction.CommitTransaction(trans)
subkeys = [s[0] for s in win32api.RegEnumKeyExW(key)]
assert subkeyname in subkeys

# 046013.python.RegCreateKeyTransacted.line47.comment # test transacted delete
del_trans = win32transaction.CreateTransaction(
    Description="test RegDeleteKeyTransacted"
)
win32api.RegDeleteKeyEx(key, subkeyname, Transaction=del_trans)
# 046014.python.RegCreateKeyTransacted.line52.comment # subkey should still show up for non-transacted handle
subkeys = [s[0] for s in win32api.RegEnumKeyExW(key)]
assert subkeyname in subkeys
# 046015.python.RegCreateKeyTransacted.line55.comment # ... and should be gone after commit
win32transaction.CommitTransaction(del_trans)
subkeys = [s[0] for s in win32api.RegEnumKeyExW(key)]
assert subkeyname not in subkeys

win32api.RegDeleteKey(win32con.HKEY_CURRENT_USER, keyname)
