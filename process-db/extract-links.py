import sqlite3
import sys
from bs4 import BeautifulSoup
from contextlib import closing
from rich import print
from rich.progress import track
import re

grapherUrlRegex = re.compile("^http(s)?://(www\\.)?ourworldindata.org/grapher/(?P<slug>[^?]+)")
internalUrlRegex = re.compile("^http(s)?://(www\\.)?ourworldindata.org/")

def postprocess(args):
    if len(args) != 1:
        print("Usage: extract-links.py DBNAME")
        return
    with closing(sqlite3.connect(args[0])) as connection:
        connection.row_factory = sqlite3.Row
        with closing(connection.cursor()) as cursor:
            print("Fetching redirects")
            grapher_rows = cursor.execute("""
            SELECT chart_id as id, slug FROM chart_slug_redirects
            UNION
            SELECT id, JSON_EXTRACT(config, '$.slug') as slug FROM charts
            """)
            chart_slugs_to_ids = { row["slug"] : row["id"] for row in grapher_rows }

            print("Creating new link tables")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_links (
                `id` integer NOT NULL PRIMARY KEY,
                `postId` integer NOT NULL,
                `link` TEXT,
                `kind` TEXT,
                CONSTRAINT `FK_post_links_postId` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE
            )  ;
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_charts  (
                `postId` integer NOT NULL,
                `chartId` integer NOT NULL,
                PRIMARY KEY (`postId`, `chartId`),
                CONSTRAINT `FK_post_charts_chartId` FOREIGN KEY (`chartId`) REFERENCES `charts` (`id`) ON DELETE CASCADE,
                CONSTRAINT `FK_post_charts_postId` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE
            ) ;
            """)

            rows = cursor.execute("SELECT id, title, content from posts").fetchall()
            for row in track(rows, description="Processing posts..."):
                soup = BeautifulSoup(row["content"], "html.parser")

                links = filter(lambda link: link is not None, map(lambda link: link.get("href"), soup.find_all("a")))
                internal_links = [ link for link in links if internalUrlRegex.match(link) ]
                params = [ {"postId": row["id"], "link": link, "kind": "internal-link" } for link in internal_links ]
                cursor.executemany("""
                INSERT INTO post_links(postId, link, kind) VALUES (:postId, :link, :kind)
                """, params)

                external_links = [ link for link in links if not internalUrlRegex.match(link) ]
                params = [ {"postId": row["id"], "link": link, "kind": "external-link" } for link in external_links ]
                cursor.executemany("""
                INSERT INTO post_links(postId, link, kind) VALUES (:postId, :link, :kind)
                """, params)


                images = map(lambda img: img.get("src"), soup.find_all("img"))
                params = [ {"postId": row["id"], "link": image, "kind": "image" } for image in images ]
                cursor.executemany("""
                INSERT INTO post_links(postId,
                link, kind) VALUES (:postId, :link, :kind)
                """, params)


                iframes = map(lambda iframe: iframe.get("src"), soup.find_all("iframe"))
                grapher_links = [ match.groupdict()["slug"] for match in ( grapherUrlRegex.match(iframe) for iframe in iframes ) if match is not None]
                grapher_ids = { chart_slugs_to_ids.get(slug) for slug in grapher_links if slug in chart_slugs_to_ids }
                unresolved_grapher_slugs = [ slug for slug in grapher_links if slug not in chart_slugs_to_ids]

                if unresolved_grapher_slugs:
                    print(f"[yellow]The following slugs could not be resolved: {', '.join(unresolved_grapher_slugs)}")

                params = [ {"postId": row["id"], "chartId": id } for id in grapher_ids ]
                cursor.executemany("""
                INSERT INTO post_charts(postId, chartId) VALUES (:postId, :chartId)
                """, params)
            print("[green]All done")
            connection.commit()


if __name__ == "__main__":
   postprocess(sys.argv[1:])