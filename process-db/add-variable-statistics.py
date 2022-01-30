import sqlite3
import sys
import os
from contextlib import closing
from rich import print
from rich.progress import Progress
import pymysql
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

def get_connection() -> pymysql.Connection:
    "Connect to the Grapher database."
    return pymysql.connect(
        db=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),  # type: ignore
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWD"), # type: ignore
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

create_variable_statistics_without_values = """
            CREATE TABLE IF NOT EXISTS variable_statistics (
                `id` integer NOT NULL PRIMARY KEY,
                `variableId` integer NOT NULL,
                `num_data_points` integer,
                `year_min` integer,
                `year_max` integer,
                CONSTRAINT `FK_variable_statistics_variableId` FOREIGN KEY (`variableId`) REFERENCES `variables` (`id`) ON DELETE CASCADE
            )  ;
            """

select_variable_statistics_without_values = """
select
    variableId,
    count(*) as num_data_points,
    min(year) as year_min,
    max(year) as year_max
from
data_values
group by
    variableId
"""

insert_variable_statistics_without_values = """
INSERT INTO
variable_statistics(variableId, num_data_points, year_min, year_max)
VALUES(:variableId, :num_data_points, :year_min, :year_max)
"""

def add_variable_statistics(args):
    if len(args) != 1:
        print("Usage: add-variable-statistics.py DBNAME")
        return
    with closing(sqlite3.connect(args[0])) as sqlite_connection:
        with closing(sqlite_connection.cursor()) as sqlite_cursor:
            print("Creating variable_statistics")
            sqlite_cursor.execute(create_variable_statistics_without_values)
            with closing(get_connection()) as mysql_connection:
                with closing(mysql_connection.cursor()) as mysql_cursor:
                    mysql_cursor.execute("select count(distinct variableId) as count from data_values")
                    variable_count = mysql_cursor.fetchone()["count"]
                    print(f"Executing query for {variable_count} variables")
                    mysql_cursor.execute(select_variable_statistics_without_values)
                    for row in mysql_cursor:
                        sqlite_cursor.execute(insert_variable_statistics_without_values, row)
            sqlite_connection.commit()
            print("done")

if __name__ == "__main__":
   add_variable_statistics(sys.argv[1:])