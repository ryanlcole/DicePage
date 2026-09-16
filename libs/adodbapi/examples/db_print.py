"""db_print.py -- a simple demo for ADO database reads."""

import sys

import adodbapi.ado_consts as adc

cmd_args = ("filename", "table_name")
if "help" in sys.argv:
    print("possible settings keywords are:", cmd_args)
    sys.exit()

kw_args = {}  # pick up filename and proxy address from command line (optionally)
for arg in sys.argv:
    s = arg.split("=")
    if len(s) > 1:
        if s[0] in cmd_args:
            kw_args[s[0]] = s[1]

kw_args.setdefault(
    "filename", "test.mdb"
)  # assumes server is running from examples folder
kw_args.setdefault("table_name", "Products")  # the name of the demo table

# 020802.python.db_print.line24.comment the server needs to select the provider based on his Python installation
provider_switch = ["provider", "Microsoft.ACE.OLEDB.12.0", "Microsoft.Jet.OLEDB.4.0"]

# 020803.python.db_print.line27.comment ------------------------ START HERE -------------------------------------
# 020804.python.db_print.line28.comment create the connection
constr = "Provider=%(provider)s;Data Source=%(filename)s"
import adodbapi as db

con = db.connect(constr, kw_args, macro_is64bit=provider_switch)

if kw_args["table_name"] == "?":
    print("The tables in your database are:")
    for name in con.get_table_names():
        print(name)
else:
    # 020805.python.db_print.line39.comment make a cursor on the connection
    with con.cursor() as c:
        # 020806.python.db_print.line41.comment run an SQL statement on the cursor
        sql = "select * from %s" % kw_args["table_name"]
        print('performing query="%s"' % sql)
        c.execute(sql)

        # 020807.python.db_print.line46.comment check the results
        print(
            'result rowcount shows as= %d. (Note: -1 means "not known")' % (c.rowcount,)
        )
        print("")
        print("result data description is:")
        print("            NAME Type         DispSize IntrnlSz Prec Scale Null?")
        for d in c.description:
            print(
                ("%16s %-12s %8s %8d %4d %5d %s")
                % (d[0], adc.adTypeNames[d[1]], d[2], d[3], d[4], d[5], bool(d[6]))
            )
        print("")
        print("str() of first five records are...")

        # 020808.python.db_print.line61.comment get the results
        db = c.fetchmany(5)

        # 020809.python.db_print.line64.comment print them
        for rec in db:
            print(rec)

        print("")
        print("repr() of next row is...")
        print(repr(c.fetchone()))
        print("")
con.close()
