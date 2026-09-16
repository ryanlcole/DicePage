# 046144.python.localized_names.line1.comment A Python port of the MS knowledge base article Q157234
# 046145.python.localized_names.line2.comment "How to deal with localized and renamed user and group names"
# 046146.python.localized_names.line3.comment https://www.betaarchive.com/wiki/index.php?title=Microsoft_KB_Archive/157234

import sys

import pywintypes
from ntsecuritycon import (
    DOMAIN_ALIAS_RID_ADMINS,
    DOMAIN_USER_RID_ADMIN,
    SECURITY_BUILTIN_DOMAIN_RID,
    SECURITY_NT_AUTHORITY,
)
from win32net import NetUserModalsGet
from win32security import LookupAccountSid


def LookupAliasFromRid(TargetComputer, Rid):
    # 046147.python.localized_names.line19.comment Sid is the same regardless of machine, since the well-known
    # 046148.python.localized_names.line20.comment BUILTIN domain is referenced.
    sid = pywintypes.SID()
    sid.Initialize(SECURITY_NT_AUTHORITY, 2)

    for i, r in enumerate((SECURITY_BUILTIN_DOMAIN_RID, Rid)):
        sid.SetSubAuthority(i, r)

    name, domain, typ = LookupAccountSid(TargetComputer, sid)
    return name


def LookupUserGroupFromRid(TargetComputer, Rid):
    # 046149.python.localized_names.line32.comment get the account domain Sid on the target machine
    # 046150.python.localized_names.line33.comment note: if you were looking up multiple sids based on the same
    # 046151.python.localized_names.line34.comment account domain, only need to call this once.
    umi2 = NetUserModalsGet(TargetComputer, 2)
    domain_sid = umi2["domain_id"]

    SubAuthorityCount = domain_sid.GetSubAuthorityCount()

    # 046152.python.localized_names.line40.comment create and init new sid with acct domain Sid + acct Rid
    sid = pywintypes.SID()
    sid.Initialize(domain_sid.GetSidIdentifierAuthority(), SubAuthorityCount + 1)

    # 046153.python.localized_names.line44.comment copy existing subauthorities from account domain Sid into
    # 046154.python.localized_names.line45.comment new Sid
    for i in range(SubAuthorityCount):
        sid.SetSubAuthority(i, domain_sid.GetSubAuthority(i))

    # 046155.python.localized_names.line49.comment append Rid to new Sid
    sid.SetSubAuthority(SubAuthorityCount, Rid)

    name, domain, typ = LookupAccountSid(TargetComputer, sid)
    return name


def main():
    if len(sys.argv) == 2:
        targetComputer = sys.argv[1]
    else:
        targetComputer = None

    name = LookupUserGroupFromRid(targetComputer, DOMAIN_USER_RID_ADMIN)
    print(f"'Administrator' user name = {name}")

    name = LookupAliasFromRid(targetComputer, DOMAIN_ALIAS_RID_ADMINS)
    print(f"'Administrators' local group/alias name = {name}")


if __name__ == "__main__":
    main()
