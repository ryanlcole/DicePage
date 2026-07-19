from shaelvien_lite.db_admin import main


if __name__ == "__main__":
    raise SystemExit(main(["backup", *(__import__("sys").argv[1:])]))
