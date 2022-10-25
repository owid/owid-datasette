import sqlite3
import sys
from contextlib import closing

import functools
import threading
import json
import rure

# Below taken from datasette-rure so we can use sqlite regexes when building our sqlite file
@functools.lru_cache(maxsize=128)
def _compiled_regex(threadid, pattern):
    return rure.compile(pattern)


def compiled_regex(pattern):
    return _compiled_regex(threading.get_ident(), pattern)


def none_on_exception(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    return inner


@none_on_exception
def regexp(pattern, input):
    return 1 if compiled_regex(pattern).search(input) else 0


@none_on_exception
def regexp_match(pattern, input, index=1):
    return compiled_regex(pattern).match(input).group(index)


@none_on_exception
def regexp_matches(pattern, input):
    return json.dumps([m.groupdict() for m in compiled_regex(pattern).finditer(input)])

def postprocess(args):
    if len(args) != 1:
        print("Usage: postprocess-db.py DBNAME")
        return
    with closing(sqlite3.connect(args[0])) as connection:
        connection.create_function("regexp", 2, regexp)
        connection.create_function("regexp_match", 2, regexp_match)
        connection.create_function("regexp_match", 3, regexp_match)
        connection.create_function("regexp_matches", 2, regexp_matches)
        with closing(connection.cursor()) as cursor:
            print("Ensuring no passwords are published")
            cursor.execute("UPDATE users set password=''")

            print("Mask out email addresses of non-owid emails")
            cursor.execute("UPDATE users SET email=((replace(fullName, ' ', '.') || '@former-contributor.org')) WHERE email NOT LIKE '%ourworldindata.org'")

            print("Remove all posts that are not published (draft, private)")
            cursor.execute("DELETE FROM posts WHERE status!='publish'")

            print("Create relationship table charts_variables")
            cursor.execute("""-- sql
            CREATE table chart_variables
            (
                `chartId` integer NOT NULL,
                `variableId` integer NOT NULL,
                PRIMARY KEY (`chartId`, `variableId`),
                CONSTRAINT `FK_chart_variables_chartId` FOREIGN KEY (`chartId`) REFERENCES `charts` (`id`) ON DELETE CASCADE,
                CONSTRAINT `FK_chart_variables_variableId` FOREIGN KEY (`variableId`) REFERENCES `variables` (`id`) ON DELETE CASCADE
            );""")

            cursor.execute("""-- sql
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


            print("Create helper table post_html_tags")
            cursor.execute("""-- sql
            CREATE table post_html_tags
            (
                `id` integer PRIMARY KEY,
                `postId` integer NOT NULL,
                `tag` TEXT NOT NULL,
                'attribute' TEXT NOT NULL,
                CONSTRAINT `FK_post_html_tags_post_id` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE
            );""")

            cursor.execute("""-- sql
                with posts_with_tags as (
                    select
                        id,
                        regexp_matches('<(?P<tag>[^!>\\s]+)(?P<attributes>[^>]*)>', content) as tags
                    from
                        posts
                ), id_and_tag as (
                    select
                        posts_with_tags.id as id,
                        JSON_EXTRACT(json_each.value, '$.tag') as tag,
                        JSON_EXTRACT(json_each.value, '$.attributes') as attribute
                    from
                        posts_with_tags,
                        json_each(posts_with_tags.tags)
                )
                INSERT INTO post_html_tags (postId, tag, attribute)
                select
                    id as postId,
                    tag,
                    attribute
                from
                    id_and_tag
            """)

            print("Create helper table post_wp_tags")
            cursor.execute("""-- sql
            CREATE table post_wp_tags
            (
                `id` integer PRIMARY KEY,
                `postId` integer NOT NULL,
                `tag` TEXT NOT NULL,
                CONSTRAINT `FK_post_wp_tags_post_id` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE
            );""")

            cursor.execute("""-- sql
                with posts_with_tags as (
                    select
                        id,
                        regexp_matches('(?P<tag>wp:[^\\s]+)(?P<dummy>[\\s])', content) as tags
                    from
                        posts
                ), id_and_tag as (
                    select
                        posts_with_tags.id as id,
                        JSON_EXTRACT(json_each.value, '$.tag') as tag
                    from
                        posts_with_tags,
                        json_each(posts_with_tags.tags)
                )
                INSERT INTO post_wp_tags (postId, tag)
                select
                    id as postId,
                    tag
                from
                    id_and_tag
            """)

            print("Add useful columns to charts")
            cursor.executescript("""-- sql
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
            cursor.executescript("""-- sql
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
