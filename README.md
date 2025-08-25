# data_reconcilation_framework

This repository provides a small utility to compare two delimited text files
and highlight differences at the row and column level.  It can also generate a
simple diff report and send it to a recipient via email.

## Usage

```sh
./compare_files.sh old_file.csv new_file.csv [recipient@example.com]
```

The wrapper script invokes the Python program `compare.py` which performs the
actual comparison.  If an email address is supplied, the tool will attempt to
send the report using the SMTP server defined by the `SMTP_SERVER` environment
variable (default `localhost`).  The sender address can be customised with
`MAIL_SENDER`.

The Python script can also be executed directly:

```sh
python3 compare.py old_file.csv new_file.csv --email recipient@example.com
```

The report printed to standard output lists mismatched rows, per-column
statistics and counts of extra rows.  The email feature is optional so the tool
can still be used in environments without email configuration.
