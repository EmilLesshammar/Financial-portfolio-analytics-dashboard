# Synthetic sample data

All files in this directory are fictional and contain no personal financial information.

- `sample_seed.sql` inserts a small demo portfolio into the public schema.
- The CSV files mirror the main database entities and are included for inspection/testing.
- The sample assets intentionally have no Yahoo Finance symbols, so running market-data refreshes will not overwrite the fictional prices.

To reset a demo database, recreate the schema and then run `sample_seed.sql`.
