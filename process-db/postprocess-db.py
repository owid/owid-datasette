import sqlite3
import sys
from contextlib import closing

def postprocess(args):
    if len(args) != 1:
        print("Usage: postprocess-db.py DBNAME")
        return
    with closing(sqlite3.connect(args[0])) as connection:
        with closing(connection.cursor()) as cursor:
            print("Ensuring no passwords are published")
            cursor.execute("UPDATE users set password=''")

            print("Mask out email addresses of non-owid emails")
            cursor.execute("UPDATE users SET email=((replace(fullName, ' ', '.') || '@former-contributor.org')) WHERE email NOT LIKE '%ourworldindata.org'")

            print("Remove all posts that are not published (draft, private)")
            cursor.execute("DELETE FROM posts WHERE status!='publish'")

            print("Create relationship table charts_variables")
            cursor.execute("""
            CREATE table chart_variables
            (
                `chartId` integer NOT NULL,
                `variableId` integer NOT NULL,
                PRIMARY KEY (`chartId`, `variableId`),
                CONSTRAINT `FK_chart_variables_chartId` FOREIGN KEY (`chartId`) REFERENCES `charts` (`id`) ON DELETE CASCADE,
                CONSTRAINT `FK_chart_variables_variableId` FOREIGN KEY (`variableId`) REFERENCES `variables` (`id`) ON DELETE CASCADE
            );""")

            cursor.execute("""
            INSERT INTO chart_variables

            -- get the map variables that are not null
            SELECT
                id as chartId,
                JSON_EXTRACT(config, '$.map.variableId') as variableId
            FROM charts
            WHERE variableId is not null

            UNION

            -- and union it together with all the variables hidden in the dimensions json array, extracted with json_each
            SELECT
                charts.id as chartId,
                JSON_EXTRACT(dimension.value, '$.variableId') as variableId
            from charts,
            json_each(config, '$.dimensions') as dimension;
            """)

            print("Add useful columns to charts")
            cursor.executescript("""
            ALTER TABLE charts
                ADD COLUMN title TEXT GENERATED ALWAYS as (JSON_EXTRACT(config, '$.title'))  VIRTUAL;
            ALTER TABLE charts
                ADD COLUMN subtitle TEXT GENERATED ALWAYS as (JSON_EXTRACT(config, '$.subtitle'))  VIRTUAL;
            ALTER TABLE charts
                ADD COLUMN note TEXT GENERATED ALWAYS as (JSON_EXTRACT(config, '$.note'))  VIRTUAL;
            ALTER TABLE charts
                ADD COLUMN slug TEXT GENERATED ALWAYS as (JSON_EXTRACT(config, '$.slug'))  VIRTUAL;
            ALTER TABLE charts
                ADD COLUMN type TEXT GENERATED ALWAYS as (JSON_EXTRACT(config, '$.type'))  VIRTUAL;
                """)

            print("Add useful columns to sources")
            cursor.executescript("""
            ALTER TABLE sources
                ADD COLUMN additionalInfo TEXT GENERATED ALWAYS as (JSON_EXTRACT(description, '$.additionalInfo')) VIRTUAL;
            ALTER TABLE sources
                ADD COLUMN link TEXT GENERATED ALWAYS as (JSON_EXTRACT(description, '$.link')) VIRTUAL;
            ALTER TABLE sources
                ADD COLUMN dataPublishedBy TEXT GENERATED ALWAYS as (JSON_EXTRACT(description, '$.dataPublishedBy')) VIRTUAL;
                """)

            connection.commit()
            print("done")


if __name__ == "__main__":
   postprocess(sys.argv[1:])
