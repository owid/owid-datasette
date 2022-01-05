import sqlite3
from contextlib import closing

with closing(sqlite3.connect("owid.db")) as connection:
    with closing(connection.cursor()) as cursor:
        # drop column is only supported in SQLite >= 3.35.0 which is not yet available in many common python envs
        #cursor.execute("ALTER TABLE users DROP COLUMN password")
        cursor.execute("UPDATE users set password=''")
        cursor.execute("""CREATE VIEW charts_view AS
        SELECT *,
            JSON_EXTRACT(config, '$.title') as title,
            JSON_EXTRACT(config, '$.subtitle') as subtitle,
            JSON_EXTRACT(config, '$.note') as note,
            JSON_EXTRACT(config, '$.slug') as slug,
            JSON_EXTRACT(config, '$.type') as type
        FROM charts
            """)
        cursor.execute("""CREATE VIEW sources_view AS
        SELECT *,
            JSON_EXTRACT(description, '$.additionalInfo') as additionalInfo,
            JSON_EXTRACT(description, '$.link') as link,
            JSON_EXTRACT(description, '$.dataPublishedBy') as dataPublishedBy
        FROM sources
            """)
