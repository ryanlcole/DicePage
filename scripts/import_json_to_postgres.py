from shaelvien_lite.db_admin import main


if __name__ == "__main__":
    raise SystemExit(main(["import-json", *(__import__("sys").argv[1:])]))
