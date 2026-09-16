# 049928.python.testAccess.line1.comment
# 049929.python.testAccess.line2.comment This assumes that you have MSAccess and DAO installed.
# 049930.python.testAccess.line3.comment You need to run makepy.py over "msaccess.tlb" and
# 049931.python.testAccess.line4.comment "dao3032.dll", and ensure the generated files are on the
# 049932.python.testAccess.line5.comment path.

# 049933.python.testAccess.line7.comment You can run this with no args, and a test database will be generated.
# 049934.python.testAccess.line8.comment You can optionally pass a dbname on the command line, in which case it will be dumped.

import os
import sys

import pythoncom
import win32api
from win32com.client import Dispatch, constants, gencache


def CreateTestAccessDatabase(dbname=None):
    # 049935.python.testAccess.line19.comment Creates a test access database - returns the filename.
    if dbname is None:
        dbname = os.path.join(win32api.GetTempPath(), "COMTestSuiteTempDatabase.mdb")

    access = Dispatch("Access.Application")
    dbEngine = access.DBEngine
    workspace = dbEngine.Workspaces(0)

    try:
        os.unlink(dbname)
    except OSError:
        print(
            "WARNING - Unable to delete old test database - expect a COM exception RSN!"
        )

    newdb = workspace.CreateDatabase(
        dbname, constants.dbLangGeneral, constants.dbEncrypt
    )

    # 049936.python.testAccess.line38.comment Create one test table.
    table = newdb.CreateTableDef("Test Table 1")
    table.Fields.Append(table.CreateField("First Name", constants.dbText))
    table.Fields.Append(table.CreateField("Last Name", constants.dbText))

    index = table.CreateIndex("UniqueIndex")
    index.Fields.Append(index.CreateField("First Name"))
    index.Fields.Append(index.CreateField("Last Name"))
    index.Unique = -1
    table.Indexes.Append(index)

    newdb.TableDefs.Append(table)

    # 049937.python.testAccess.line51.comment Create a second test table.
    table = newdb.CreateTableDef("Test Table 2")
    table.Fields.Append(table.CreateField("First Name", constants.dbText))
    table.Fields.Append(table.CreateField("Last Name", constants.dbText))

    newdb.TableDefs.Append(table)

    # 049938.python.testAccess.line58.comment Create a relationship between them
    relation = newdb.CreateRelation("TestRelationship")
    relation.Table = "Test Table 1"
    relation.ForeignTable = "Test Table 2"

    field = relation.CreateField("First Name")
    field.ForeignName = "First Name"
    relation.Fields.Append(field)

    field = relation.CreateField("Last Name")
    field.ForeignName = "Last Name"
    relation.Fields.Append(field)

    relation.Attributes = (
        constants.dbRelationDeleteCascade + constants.dbRelationUpdateCascade
    )

    newdb.Relations.Append(relation)

    # 049939.python.testAccess.line77.comment Finally we can add some data to the table.
    tab1 = newdb.OpenRecordset("Test Table 1")
    tab1.AddNew()
    tab1.Fields("First Name").Value = "Mark"
    tab1.Fields("Last Name").Value = "Hammond"
    tab1.Update()

    tab1.MoveFirst()
    # 049940.python.testAccess.line85.comment We do a simple bookmark test which tests our optimized VT_SAFEARRAY|VT_UI1 support.
    # 049941.python.testAccess.line86.comment The bookmark will be a buffer object - remember it for later.
    bk = tab1.Bookmark

    # 049942.python.testAccess.line89.comment Add a second record.
    tab1.AddNew()
    tab1.Fields("First Name").Value = "Second"
    tab1.Fields("Last Name").Value = "Person"
    tab1.Update()

    # 049943.python.testAccess.line95.comment Reset the bookmark to the one we saved.
    # 049944.python.testAccess.line96.comment But first check the test is actually doing something!
    tab1.MoveLast()
    assert tab1.Fields("First Name").Value == "Second", (
        "Unexpected record is last - makes bookmark test pointless!"
    )

    tab1.Bookmark = bk
    assert tab1.Bookmark == bk, "The bookmark data is not the same"
    assert tab1.Fields("First Name").Value == "Mark", (
        "The bookmark did not reset the record pointer correctly"
    )

    return dbname


def DoDumpAccessInfo(dbname):
    from . import daodump

    a = forms = None
    try:
        sys.stderr.write("Creating Access Application...\n")
        a = Dispatch("Access.Application")
        print("Opening database %s" % dbname)
        a.OpenCurrentDatabase(dbname)
        db = a.CurrentDb()
        daodump.DumpDB(db, 1)
        forms = a.Forms
        print("There are %d forms open." % (len(forms)))
        # 049945.python.testAccess.line124.comment Uncommenting these lines means Access remains open.
        # 049946.python.testAccess.line125.comment for form in forms:
        # 049947.python.testAccess.line126.comment print(f" {form.Name}")
        reports = a.Reports
        print("There are %d reports open" % (len(reports)))
    finally:
        if not a is None:
            sys.stderr.write("Closing database\n")
            try:
                a.CloseCurrentDatabase()
            except pythoncom.com_error:
                pass


# 049948.python.testAccess.line138.comment Generate all the support we can.
def GenerateSupport():
    # 049949.python.testAccess.line140.comment dao
    gencache.EnsureModule("{00025E01-0000-0000-C000-000000000046}", 0, 4, 0)
    # 049950.python.testAccess.line142.comment Access
    # 049951.python.testAccess.line143.comment gencache.EnsureModule("{4AFFC9A0-5F99-101B-AF4E-00AA003F0F07}", 0, 8, 0)
    gencache.EnsureDispatch("Access.Application")


def DumpAccessInfo(dbname):
    amod = gencache.GetModuleForProgID("Access.Application")
    dmod = gencache.GetModuleForProgID("DAO.DBEngine.35")
    if amod is None and dmod is None:
        DoDumpAccessInfo(dbname)
        # 049952.python.testAccess.line152.comment Now generate all the support we can.
        GenerateSupport()
    else:
        sys.stderr.write(
            "testAccess not doing dynamic test, as generated code already exists\n"
        )
    # 049953.python.testAccess.line158.comment Now a generated version.
    DoDumpAccessInfo(dbname)


def test(dbname=None):
    if dbname is None:
        # 049954.python.testAccess.line164.comment We need makepy support to create a database (just for the constants!)
        try:
            GenerateSupport()
        except pythoncom.com_error:
            print("*** Can not import the MSAccess type libraries - tests skipped")
            return
        dbname = CreateTestAccessDatabase()
        print("A test database at '%s' was created" % dbname)

    DumpAccessInfo(dbname)


if __name__ == "__main__":
    from .util import CheckClean

    dbname = None
    if len(sys.argv) > 1:
        dbname = sys.argv[1]

    test(dbname)

    CheckClean()
