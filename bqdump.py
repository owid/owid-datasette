"""Dump data from BigQuery to a SQLite database. Note that it is
currently not used anywhere.

Note that since this drops & recreates the tables, it is not suitable
for large tables like `data_values`. We'd have to load it in chunks to
make that work.

Usage:
> python bqdump.py users tags --target owid.db
"""

import typer
import os
import pandas as pd
from pathlib import Path
from typing import List
from sqlalchemy import create_engine


def main(tables: List[str], target: Path=Path('owid.db')):
    assert str(target).endswith('.db')
    assert 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ, 'Missing GOOGLE_APPLICATION_CREDENTIALS'
    engine = create_engine(f'sqlite:///{target}', echo=False)
    for table in tables:
        q = f"""
        select * from owid-analytics.prod_mysql.{table}
        """
        df = pd.read_gbq(q)

        df.to_sql(table, con=engine, if_exists='replace', index=False)


if __name__ == "__main__":
    typer.run(main)
