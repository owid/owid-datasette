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

create_variable_statistics_with_values = """
            CREATE TABLE IF NOT EXISTS variable_statistics (
                `id` integer NOT NULL PRIMARY KEY,
                `variableId` integer NOT NULL,
                `num_data_points` integer,
                `year_min` integer,
                `year_max` integer,
                `all_numeric` BOOLEAN,
                `all_text` BOOLEAN,
                `value_average` REAL,
                `value_min` REAL,
                `value_max` REAL,
                `value_stddev` REAL,
                CONSTRAINT `FK_variable_statistics_variableId` FOREIGN KEY (`variableId`) REFERENCES `variables` (`id`) ON DELETE CASCADE
            )  ;
            """

select_variable_statistics_with_values = """
select
    variableId,
    count(*) as num_data_points,
    min(year) as year_min,
    max(year) as year_max,
    count(*) = sum(isNumeric) as all_numeric,
    sum(isNumeric) = 0 as all_text,
    avg(numericValue) as value_average,
    min(numericValue) as value_min,
    max(numericValue) as value_max
    STDDEV(numericValue) as value_stddev
from
    (
    select
        *,
        CASE
            -- Unfortunately you can't cast to float - I hope DECIMAL(30, 10) is good enough
            isNumeric WHEN 1 THEN CAST(value as DECIMAL(30, 10))
            WHEN 0 then NULL
        END as numericValue
    FROM
        (
        select
            *,
            -- Unfortunately there isn't a TRY_CAST in Mysql and I know of no other way to test for numeric-ness
            value REGEXP '^[-+]?(([0-9]*[.]?[0-9]+([ed][-+]?[0-9]+)?)|(inf)|(nan)|())$' AS isNumeric
        from
            data_values) as withIsNumeric) as withNumericValue
group by
    variableId
order by variableId
LIMIT %s
OFFSET %s
"""

insert_variable_statistics_with_values = """
INSERT INTO
variable_statistics(variableId, num_data_points, year_min, year_max, all_numeric, all_text,  value_min, value_max)
VALUES(:variableId, :num_data_points, :year_min, :year_max, :all_numeric, :all_text, :value_min, :value_max)
"""

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
                    # current_offset = 0
                    # page_size = 100
                    # with Progress() as progress:
                    #     task = progress.add_task("Calculating variable statistics", total=variable_count)
                    #     while current_offset < variable_count:
                    #         mysql_cursor.execute(variable_statistics_sql, (page_size, current_offset))
                    #         for row in mysql_cursor:
                    #             row_with_floats = { k: (float(v) if type(v) is Decimal else v ) for k, v in row.items() }
                    #             sqlite_cursor.execute(insert_variable_statistics_with_values, row_with_floats)
                    #         current_offset = current_offset + page_size
                    #         progress.advance(task, advance=page_size)
                    mysql_cursor.execute(select_variable_statistics_without_values)
                    for row in mysql_cursor:
                        # row_with_floats = { k: (float(v) if type(v) is Decimal else v ) for k, v in row.items() }
                        sqlite_cursor.execute(insert_variable_statistics_without_values, row)
            sqlite_connection.commit()
            print("done")

if __name__ == "__main__":
   add_variable_statistics(sys.argv[1:])