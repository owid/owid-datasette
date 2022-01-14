This repository is a test to see if a read only SQLite copy and a [Datasette](https://datasette.io/) instance of the main Our World In Data database is useful. The SQlite DB contains the metadata on variables, datasets, namespaces and sources as well as the pages including their full markup. What is not included are all the data of the variables (i.e. you can't plot any variable with just this database but you could e.g. find all pages that mention the word "forest").

The database for now is generated with the [mysql-to-sqlite3](https://github.com/techouse/mysql-to-sqlite3/tree/master/mysql_to_sqlite3) tool, using the command in the bash script sqlite-from-mysql.sh. This could be automated. There are a few issues with the file that is generated (e.g. foreign key constraints are not correctly migrated which makes datasette not understand relations) but for now this is acceptable.

## TODO
- [ ] When iframe src links can't be linked and entered into the post_charts table then this is probably an error in the post. These should end up in the datasette db in a separate table
- [ ] Add authors information into the mysql db so we can link posts to users