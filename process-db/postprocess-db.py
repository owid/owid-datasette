import sqlite3
import sys
from contextlib import closing

def postprocess(args):
    if len(args) != 1:
        print("Usage: postprocess-db.py DBNAME")
        return
    with closing(sqlite3.connect(args[0])) as connection:
        with closing(connection.cursor()) as cursor:
            # drop column is only supported in SQLite >= 3.35.0 which is not yet available in many common python envs
            #cursor.execute("ALTER TABLE users DROP COLUMN password")
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

            print("Create charts_view")
            cursor.execute("""
            CREATE VIEW charts_view AS
            SELECT *,
                JSON_EXTRACT(config, '$.title') as title,
                JSON_EXTRACT(config, '$.subtitle') as subtitle,
                JSON_EXTRACT(config, '$.note') as note,
                JSON_EXTRACT(config, '$.slug') as slug,
                JSON_EXTRACT(config, '$.type') as type
            FROM charts
                """)

            print("Create sources_view")
            cursor.execute("""
            CREATE VIEW sources_view AS
            SELECT *,
                JSON_EXTRACT(description, '$.additionalInfo') as additionalInfo,
                JSON_EXTRACT(description, '$.link') as link,
                JSON_EXTRACT(description, '$.dataPublishedBy') as dataPublishedBy
            FROM sources
                """)

            connection.commit()
            print("done")


if __name__ == "__main__":
   postprocess(sys.argv[1:])
