# data_reconcilation_framework

This repository provides a small utility to compare two data sources and
highlight differences at the row and column level.  It generates a summary of
pass and fail counts and can email the failing records.  Sources may be
delimited text files or results from SQLite database queries.

## Usage

```sh
./compare_files.sh old_file.csv new_file.csv [recipient@example.com]
```

The wrapper script invokes the Python program `compare.py` which performs the
actual comparison.  If an email address is supplied and differences are found,
the tool will send the failing records using the SMTP server defined by the
`SMTP_SERVER` environment variable (default `localhost`).  The sender address
can be customised with `MAIL_SENDER`.

The Python script can also be executed directly.  Besides files, it can pull
data from SQLite databases:

```sh
# compare two files
python3 compare.py old_file.csv new_file.csv

# compare a file with a query result
python3 compare.py data.csv --db2 data.db --query2 "SELECT * FROM table"

# email only the failing records
python3 compare.py old.csv new.csv --email recipient@example.com
```

The report printed to standard output lists per-column statistics, counts of
extra rows and numbers of passing and failing records.  Processing is streamed
row by row so datasets of 10GB or more can be handled without exhausting
memory.  The email feature is optional so the tool can still be used in
environments without email configuration.
