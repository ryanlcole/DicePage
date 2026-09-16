"""
Demonstrates prompting for credentials, saving, and loggging on with marshalled credential.
Also shows how to load user's profile
"""

import win32api
import win32con
import win32cred
import win32net
import win32profile
import win32security

# 046445.python.win32cred_demo.line13.comment # Prompt for a username/pwd for local computer
uiinfo = {
    "MessageText": "Enter credentials for local machine",
    "CaptionText": "win32cred_demo.py",
}
target, pwd, save = win32cred.CredUIPromptForCredentials(
    TargetName=win32api.GetComputerName(),
    AuthError=0,
    Flags=win32cred.CREDUI_FLAGS_DO_NOT_PERSIST
    | win32cred.CREDUI_FLAGS_SHOW_SAVE_CHECK_BOX,
    Save=False,
    UiInfo=uiinfo,
)

attrs = [
    {"Keyword": "attr1", "Flags": 0, "Value": "unicode data"},
    {"Keyword": "attr2", "Flags": 0, "Value": b"character data"},
]
cred = {
    "Comment": "Created by win32cred_demo.py",
    "UserName": target,
    "TargetAlias": None,
    "TargetName": target,
    "CredentialBlob": pwd,
    "Flags": win32cred.CRED_FLAGS_USERNAME_TARGET,
    "Persist": win32cred.CRED_PERSIST_ENTERPRISE,
    "Type": win32cred.CRED_TYPE_DOMAIN_PASSWORD,
    "Attributes": attrs,
}
win32cred.CredWrite(cred)
pwd = None
print(win32cred.CredRead(target, win32cred.CRED_TYPE_DOMAIN_PASSWORD))

# 046446.python.win32cred_demo.line46.comment # Marshal saved credential and use it to log on
mc = win32cred.CredMarshalCredential(win32cred.UsernameTargetCredential, target)

# 046447.python.win32cred_demo.line49.comment As of pywin32 301 this no longer works for markh and unclear when it stopped, or
# 046448.python.win32cred_demo.line50.comment even if it ever did! # Fails in Python 2.7 too, so not a Python 3 regression.
try:
    th = win32security.LogonUser(
        mc,
        None,
        "",
        win32con.LOGON32_LOGON_INTERACTIVE,
        win32con.LOGON32_PROVIDER_DEFAULT,
    )
    win32security.ImpersonateLoggedOnUser(th)
    print("GetUserName:", win32api.GetUserName())
    win32security.RevertToSelf()

    # 046449.python.win32cred_demo.line63.comment # Load user's profile.  (first check if user has a roaming profile)
    username, domain = win32cred.CredUIParseUserName(target)
    user_info_4 = win32net.NetUserGetInfo(None, username, 4)
    profilepath = user_info_4["profile"]
    # 046450.python.win32cred_demo.line67.comment # LoadUserProfile apparently doesn't like an empty string
    if not profilepath:
        profilepath = None

    # 046451.python.win32cred_demo.line71.comment # leave Flags in since 2.3 still chokes on some types of optional keyword args
    hk = win32profile.LoadUserProfile(
        th, {"UserName": username, "Flags": 0, "ProfilePath": profilepath}
    )
    # 046452.python.win32cred_demo.line75.comment # Get user's environment variables in a form that can be passed to win32process.CreateProcessAsUser
    env = win32profile.CreateEnvironmentBlock(th, False)

    # 046453.python.win32cred_demo.line78.comment # Cleanup should probably be in a finally block
    win32profile.UnloadUserProfile(th, hk)
    th.Close()
except win32security.error as exc:
    print("Failed to login for some reason", exc)
