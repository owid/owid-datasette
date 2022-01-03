import sqlite3
from contextlib import closing

with closing(sqlite3.connect("owid.db")) as connection:
    with closing(connection.cursor()) as cursor:
        rows = cursor.execute("ALTER TABLE DROP COLUMN password")
