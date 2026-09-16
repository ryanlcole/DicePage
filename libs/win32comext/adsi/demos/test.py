import sys
from collections.abc import Callable

import pythoncom
import win32api
from win32com.adsi import *

verbose_level = 0

server = ""  # Must have trailing /
local_name = win32api.GetComputerName()


def DumpRoot():
    "Dumps the root DSE"
    path = "LDAP://%srootDSE" % server
    rootdse = ADsGetObject(path)

    for item in rootdse.Get("SupportedLDAPVersion"):
        print(f"{path} supports ldap version {item}")

    attributes = ["CurrentTime", "defaultNamingContext"]
    for attr in attributes:
        val = rootdse.Get(attr)
        print(f" {attr}={val}")


# 050693.python.test.line28.comment ##############################################
# 050694.python.test.line29.comment
# 050695.python.test.line30.comment Code taken from article titled:
# 050696.python.test.line31.comment Reading attributeSchema and classSchema Objects
def _DumpClass(child):
    attrs = "Abstract lDAPDisplayName schemaIDGUID schemaNamingContext attributeSyntax oMSyntax"
    _DumpTheseAttributes(child, attrs.split())


def _DumpAttribute(child):
    attrs = "lDAPDisplayName schemaIDGUID adminDescription adminDisplayName rDNAttID defaultHidingValue defaultObjectCategory systemOnly defaultSecurityDescriptor"
    _DumpTheseAttributes(child, attrs.split())


def _DumpTheseAttributes(child, attrs):
    for attr in attrs:
        try:
            val = child.Get(attr)
        except pythoncom.com_error as details:
            continue
            # 050697.python.test.line48.comment ###
            (hr, msg, exc, arg) = details
            if exc and exc[2]:
                msg = exc[2]
            val = f"<Error: {msg}>"
        if verbose_level >= 2:
            print(f" {child.Class}: {attr}={val}")


def DumpSchema():
    "Dumps the default DSE schema"
    # 050698.python.test.line59.comment Bind to rootDSE to get the schemaNamingContext property.
    path = "LDAP://%srootDSE" % server
    rootdse = ADsGetObject(path)
    name = rootdse.Get("schemaNamingContext")

    # 050699.python.test.line64.comment Bind to the actual schema container.
    path = "LDAP://" + server + name
    print("Binding to", path)
    ob = ADsGetObject(path)
    nclasses = nattr = nsub = nunk = 0

    # 050700.python.test.line70.comment Enumerate the attribute and class objects in the schema container.
    for child in ob:
        # 050701.python.test.line72.comment Find out if this is a class, attribute, or subSchema object.
        class_name = child.Class
        if class_name == "classSchema":
            _DumpClass(child)
            nclasses += 1
        elif class_name == "attributeSchema":
            _DumpAttribute(child)
            nattr += 1
        elif class_name == "subSchema":
            nsub += 1
        else:
            print("Unknown class:", class_name)
            nunk += 1
    if verbose_level:
        print("Processed", nclasses, "classes")
        print("Processed", nattr, "attributes")
        print("Processed", nsub, "sub-schema's")
        print("Processed", nunk, "unknown types")


def _DumpObject(ob, level=0):
    prefix = "  " * level
    print(f"{prefix}{ob.Class} object: {ob.Name}")
    # 050702.python.test.line95.comment Do the directory object thing
    try:
        dir_ob = ADsGetObject(ob.ADsPath, IID_IDirectoryObject)
    except pythoncom.com_error:
        dir_ob = None
    if dir_ob is not None:
        info = dir_ob.GetObjectInformation()
        print(f"{prefix} RDN='{info.RDN}', ObjectDN='{info.ObjectDN}'")
        # 050703.python.test.line103.comment Create a list of names to fetch
        names = ["distinguishedName"]
        attrs = dir_ob.GetObjectAttributes(names)
        for attr in attrs:
            for val, typ in attr.Values:
                print(f"{prefix} Attribute '{attr.AttrName}' = {val}")

    for child in ob:
        _DumpObject(child, level + 1)


def DumpAllObjects():
    "Recursively dump the entire directory!"
    path = "LDAP://%srootDSE" % server
    rootdse = ADsGetObject(path)
    name = rootdse.Get("defaultNamingContext")

    # 050704.python.test.line120.comment Bind to the actual schema container.
    path = "LDAP://" + server + name
    print("Binding to", path)
    ob = ADsGetObject(path)

    # 050705.python.test.line125.comment Enumerate the attribute and class objects in the schema container.
    _DumpObject(ob)


# 050706.python.test.line129.comment #########################################################
# 050707.python.test.line130.comment
# 050708.python.test.line131.comment Code taken from article:
# 050709.python.test.line132.comment Example Code for Enumerating Schema Classes, Attributes, and Syntaxes

# 050710.python.test.line134.comment Fill a map with VT_ datatypes, to give us better names:
vt_map = {}
for name, val in pythoncom.__dict__.items():
    if name[:3] == "VT_":
        vt_map[val] = name


def DumpSchema2():
    "Dumps the schema using an alternative technique"
    path = f"LDAP://{server}schema"
    schema = ADsGetObject(path, IID_IADsContainer)
    nclass = nprop = nsyntax = 0
    for item in schema:
        item_class = item.Class.lower()
        if item_class == "class":
            items = []
            if item.Abstract:
                items.append("Abstract")
            if item.Auxiliary:
                items.append("Auxiliary")
            # 050711.python.test.line154.comment if item.Structural: items.append("Structural")
            desc = ", ".join(items)
            import win32com.util

            iid_name = win32com.util.IIDToInterfaceName(item.PrimaryInterface)
            if verbose_level >= 2:
                print(
                    "Class: Name={}, Flags={}, Primary Interface={}".format(
                        item.Name, desc, iid_name
                    )
                )
            nclass += 1
        elif item_class == "property":
            if item.MultiValued:
                val_type = "Multi-Valued"
            else:
                val_type = "Single-Valued"
            if verbose_level >= 2:
                print(f"Property: Name={item.Name}, {val_type}")
            nprop += 1
        elif item_class == "syntax":
            data_type = vt_map.get(item.OleAutoDataType, "<unknown type>")
            if verbose_level >= 2:
                print(f"Syntax: Name={item.Name}, Datatype = {data_type}")
            nsyntax += 1
    if verbose_level >= 1:
        print("Processed", nclass, "classes")
        print("Processed", nprop, "properties")
        print("Processed", nsyntax, "syntax items")


def DumpGC():
    "Dumps the GC: object (whatever that is!)"
    ob = ADsGetObject("GC:", IID_IADsContainer)
    for sub_ob in ob:
        print(f"GC ob: {sub_ob.Name} ({sub_ob.ADsPath})")


def DumpLocalUsers():
    "Dumps the local machine users"
    path = f"WinNT://{local_name},computer"
    ob = ADsGetObject(path, IID_IADsContainer)
    ob.put_Filter(["User", "Group"])
    for sub_ob in ob:
        print(f"User/Group: {sub_ob.Name} ({sub_ob.ADsPath})")


def DumpLocalGroups():
    "Dumps the local machine groups"
    path = f"WinNT://{local_name},computer"
    ob = ADsGetObject(path, IID_IADsContainer)

    ob.put_Filter(["Group"])
    for sub_ob in ob:
        print(f"Group: {sub_ob.Name} ({sub_ob.ADsPath})")
        # 050712.python.test.line209.comment get the members
        members = sub_ob.Members()
        for member in members:
            print(f"  Group member: {member.Name} ({member.ADsPath})")


def usage(tests):
    import os

    print("Usage: %s [-s server ] [-v] [Test ...]" % os.path.basename(sys.argv[0]))
    print("  -v : Verbose - print more information")
    print("  -s : server - execute the tests against the named server")
    print("where Test is one of:")
    for t in tests:
        print(t.__name__, ":", t.__doc__)
    print()
    print("If not tests are specified, all tests are run")
    sys.exit(1)


def main():
    import getopt
    import traceback

    tests = []
    for ob in globals().values():
        if isinstance(ob, Callable) and ob.__doc__:
            tests.append(ob)
    opts, args = getopt.getopt(sys.argv[1:], "s:hv")
    for opt, val in opts:
        if opt == "-s":
            if val[-1] not in "\\/":
                val += "/"
            global server
            server = val
        if opt == "-h":
            usage(tests)
        if opt == "-v":
            global verbose_level
            verbose_level += 1

    if len(args) == 0:
        print("Running all tests - use '-h' to see command-line options...")
        dotests = tests
    else:
        dotests = []
        for arg in args:
            for t in tests:
                if t.__name__ == arg:
                    dotests.append(t)
                    break
            else:
                print("Test '%s' unknown - skipping" % arg)
    if not len(dotests):
        print("Nothing to do!")
        usage(tests)
    for test in dotests:
        try:
            test()
        except:
            print("Test %s failed" % test.__name__)
            traceback.print_exc()


if __name__ == "__main__":
    main()
