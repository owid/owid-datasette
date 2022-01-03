import sqlite3
from contextlib import closing

with closing(sqlite3.connect("owid.db")) as connection:
    with closing(connection.cursor()) as cursor:
        # drop column is only supported in SQLite >= 3.35.0 which is not yet available in many common python envs
        #cursor.execute("ALTER TABLE users DROP COLUMN password")
        cursor.execute("UPDATE users set password=''")
