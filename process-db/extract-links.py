import re
import sqlite3
import sys
from contextlib import closing
from typing import Dict

from bs4 import BeautifulSoup
from rich import print
from rich.progress import track

grapherUrlRegex = re.compile(
    "^http(s)?://(www\\.)?ourworldindata.org/grapher/(?P<slug>[^?]+)"
)
internalUrlRegex = re.compile("^http(s)?://(www\\.)?ourworldindata.org/")


def extract_chart_references(
    links: list[str],
    kind: str,
    post_id: int,
    chart_slugs_to_ids: Dict[str, int],
    cursor: sqlite3.Cursor,
):
    grapher_links = [
        match.groupdict()["slug"].lower()
        for match in (grapherUrlRegex.match(link) for link in links)
        if match is not None
    ]
    grapher_ids = {
        chart_slugs_to_ids.get(slug)
        for slug in grapher_links
        if slug in chart_slugs_to_ids
    }
    unresolved_grapher_slugs = [
        slug for slug in grapher_links if slug not in chart_slugs_to_ids
    ]

    if unresolved_grapher_slugs:
        print(
            f"[yellow]The following slugs could not be resolved for chart references of kind {kind}: {', '.join(unresolved_grapher_slugs)}"
        )

    params = [
        {
            "postId": post_id,
            "chartId": id,
            "kind": kind,
            "through_redirect": is_redirect,
        }
        for (id, is_redirect) in grapher_ids
    ]
    cursor.executemany(
        """
    INSERT INTO post_charts(postId, chartId, kind, through_redirect)
    VALUES (:postId, :chartId, :kind, :through_redirect)
    """,
        params,
    )


def postprocess(args):
    if len(args) != 1:
        print("Usage: extract-links.py DBNAME")
        return
    with closing(sqlite3.connect(args[0])) as connection:
        connection.row_factory = sqlite3.Row
        with closing(connection.cursor()) as cursor:
            print("Fetching redirects")
            grapher_rows = cursor.execute(
                """
            SELECT chart_id as id, slug, TRUE as is_redirect FROM chart_slug_redirects
            UNION
            SELECT id, JSON_EXTRACT(config, '$.slug') as slug, FALSE as is_redirect FROM charts
            """
            )
            chart_slugs_to_ids = {
                row["slug"].lower(): (row["id"], bool(row["is_redirect"]))
                for row in grapher_rows
            }

            print("Creating new link tables")
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS post_links (
                `id` integer NOT NULL PRIMARY KEY,
                `postId` integer NOT NULL,
                `link` TEXT,
                `kind` TEXT,
                CONSTRAINT `FK_post_links_postId` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE
            )  ;
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS post_charts  (
                `postId` integer NOT NULL,
                `chartId` integer NOT NULL,
                `kind` TEXT NOT NULL,
                `through_redirect` integer NOT NULL,
                PRIMARY KEY (`postId`, `chartId`, `kind`),
                CONSTRAINT `FK_post_charts_chartId` FOREIGN KEY (`chartId`) REFERENCES `charts` (`id`) ON DELETE CASCADE,
                CONSTRAINT `FK_post_charts_postId` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE
            ) ;
            """
            )

            rows = cursor.execute("SELECT id, title, content from posts").fetchall()
            for row in track(rows, description="Processing posts..."):
                soup = BeautifulSoup(row["content"], "html.parser")

                links = list(
                    filter(
                        lambda link: link is not None,
                        map(lambda link: link.get("href"), soup.find_all("a")),
                    )
                )
                internal_links = [
                    link for link in links if internalUrlRegex.match(link)
                ]
                params = [
                    {"postId": row["id"], "link": link, "kind": "internal-link"}
                    for link in internal_links
                ]
                cursor.executemany(
                    """
                INSERT INTO post_links(postId, link, kind) VALUES (:postId, :link, :kind)
                """,
                    params,
                )

                external_links = [
                    link for link in links if internalUrlRegex.match(link) is None
                ]
                params = [
                    {"postId": row["id"], "link": link, "kind": "external-link"}
                    for link in external_links
                ]
                cursor.executemany(
                    """
                INSERT INTO post_links(postId, link, kind) VALUES (:postId, :link, :kind)
                """,
                    params,
                )

                images = map(lambda img: img.get("src"), soup.find_all("img"))
                params = [
                    {"postId": row["id"], "link": image, "kind": "image"}
                    for image in images
                ]
                cursor.executemany(
                    """
                INSERT INTO post_links(postId,
                link, kind) VALUES (:postId, :link, :kind)
                """,
                    params,
                )

                iframe_links = [
                    iframe.get("src")
                    for iframe in soup.find_all("iframe")
                    if iframe.get("src")
                ]
                extract_chart_references(
                    iframe_links, "embed", row["id"], chart_slugs_to_ids, cursor
                )

                link_hrefs = [
                    link.get("href") for link in soup.find_all("a") if link.get("href")
                ]
                extract_chart_references(
                    link_hrefs, "link", row["id"], chart_slugs_to_ids, cursor
                )

            print("[green]All done")
            connection.commit()


if __name__ == "__main__":
    postprocess(sys.argv[1:])
