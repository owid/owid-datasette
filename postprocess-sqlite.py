import sqlite3
from contextlib import closing

with closing(sqlite3.connect("owid.sqlite")) as connection:
    with closing(connection.cursor()) as cursor:
        pass
