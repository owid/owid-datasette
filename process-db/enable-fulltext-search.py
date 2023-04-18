from sqlite_utils import Database
import sys

def enable_fts(args):
    if len(args) != 1:
        print(f"Usage: enable-fulltext-search.py DBNAME")
        return
    db = Database(args[0])
    db["variables"].enable_fts(["name", "description"], tokenize="porter")
    db["charts"].enable_fts(["title", "subtitle"], tokenize="porter")


if __name__ == "__main__":
    enable_fts(sys.argv[1:])
