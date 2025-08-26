#!/usr/bin/env python3
"""
Data comparison tool.

Compares two delimited text files or database queries and reports differences
at the row and column level. Generates a summary with pass/fail counts and can
optionally email only the failing records.
"""

import argparse
import csv
import os
import smtplib
import sqlite3
from email.message import EmailMessage
from itertools import zip_longest


def iter_table(path, delimiter):
    """Yield rows from the delimited file at *path*."""
    with open(path, newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for row in reader:
            yield row


def iter_db(db_path, query):
    """Yield rows resulting from executing *query* on the SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        for row in cur.execute(query):
            yield [str(col) for col in row]
    finally:
        conn.close()


def compare_iterators(rows1, rows2):
    """Compare two row iterators and return diff metrics."""
    column_diffs = []
    mismatched_rows = []
    failed_records = []
    pass_count = 0
    fail_count = 0
    rows_file1 = 0
    rows_file2 = 0

    for idx, (row1, row2) in enumerate(zip_longest(rows1, rows2, fillvalue=None)):
        if row1 is not None:
            rows_file1 += 1
        else:
            row1 = []
        if row2 is not None:
            rows_file2 += 1
        else:
            row2 = []

        max_cols = max(len(row1), len(row2))
        if len(column_diffs) < max_cols:
            column_diffs.extend([0] * (max_cols - len(column_diffs)))

        row_mismatch = False
        for j in range(max_cols):
            v1 = row1[j] if j < len(row1) else ""
            v2 = row2[j] if j < len(row2) else ""
            if v1 != v2:
                column_diffs[j] += 1
                row_mismatch = True

        if row_mismatch:
            fail_count += 1
            mismatched_rows.append(idx + 1)  # 1-indexed
            failed_records.append((idx + 1, row1, row2))
        else:
            pass_count += 1

    extra_rows_file1 = max(0, rows_file1 - rows_file2)
    extra_rows_file2 = max(0, rows_file2 - rows_file1)
    cell_differences = sum(column_diffs)

    return {
        "rows_file1": rows_file1,
        "rows_file2": rows_file2,
        "extra_rows_file1": extra_rows_file1,
        "extra_rows_file2": extra_rows_file2,
        "cell_differences": cell_differences,
        "column_differences": {
            f"col{idx + 1}": diff for idx, diff in enumerate(column_diffs) if diff
        },
        "mismatched_rows": mismatched_rows,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "failed_records": failed_records,
    }


def format_summary(source1, source2, metrics):
    """Format diff *metrics* into a human readable report."""
    lines = [
        "Comparison Report",
        "=================",
        f"Source 1: {source1}",
        f"Source 2: {source2}",
        "",
        f"Rows in Source 1: {metrics['rows_file1']}",
        f"Rows in Source 2: {metrics['rows_file2']}",
        f"Extra rows in Source 1: {metrics['extra_rows_file1']}",
        f"Extra rows in Source 2: {metrics['extra_rows_file2']}",
        f"Cell differences: {metrics['cell_differences']}",
        f"Pass records: {metrics['pass_count']}",
        f"Fail records: {metrics['fail_count']}",
    ]
    if metrics["column_differences"]:
        lines.append("Column differences:")
        for col, diff in metrics["column_differences"].items():
            lines.append(f"  {col}: {diff}")
    if metrics["mismatched_rows"]:
        lines.append(
            "Rows with differences: " + ", ".join(map(str, metrics["mismatched_rows"]))
        )
    return "\n".join(lines)


def format_failed_records(failed_records):
    """Format the list of *failed_records* for output or email."""
    if not failed_records:
        return "No failing records"
    lines = ["Failed Records", "=============="]
    for row_no, row1, row2 in failed_records:
        lines.append(f"Row {row_no}:")
        lines.append(f"  source1: {','.join(row1)}")
        lines.append(f"  source2: {','.join(row2)}")
    return "\n".join(lines)


def send_email(recipient, subject, body):
    """Send *body* to *recipient* using SMTP settings from the environment."""
    sender = os.getenv("MAIL_SENDER", "noreply@example.com")
    smtp_server = os.getenv("SMTP_SERVER", "localhost")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)
    with smtplib.SMTP(smtp_server) as server:
        server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two delimited text files or database queries and report differences."
    )
    parser.add_argument("file1", nargs="?", help="first file to compare")
    parser.add_argument("file2", nargs="?", help="second file to compare")
    parser.add_argument(
        "--delimiter",
        default=",",
        help="field delimiter used in the files (default: comma)",
    )
    parser.add_argument("--db1", help="path to SQLite database for first dataset")
    parser.add_argument("--query1", help="SQL query for first dataset")
    parser.add_argument("--db2", help="path to SQLite database for second dataset")
    parser.add_argument("--query2", help="SQL query for second dataset")
    parser.add_argument(
        "--email", help="send failed records to this email address", metavar="ADDRESS"
    )
    args = parser.parse_args()

    if args.db1:
        if not args.query1:
            parser.error("--db1 requires --query1")
        iter1 = iter_db(args.db1, args.query1)
        source1 = f"{args.db1}:{args.query1}"
    else:
        if not args.file1:
            parser.error("file1 or --db1 must be specified")
        iter1 = iter_table(args.file1, args.delimiter)
        source1 = args.file1

    if args.db2:
        if not args.query2:
            parser.error("--db2 requires --query2")
        iter2 = iter_db(args.db2, args.query2)
        source2 = f"{args.db2}:{args.query2}"
    else:
        if not args.file2:
            parser.error("file2 or --db2 must be specified")
        iter2 = iter_table(args.file2, args.delimiter)
        source2 = args.file2

    metrics = compare_iterators(iter1, iter2)
    summary = format_summary(source1, source2, metrics)
    print(summary)

    if metrics["fail_count"]:
        print("\n" + format_failed_records(metrics["failed_records"]))

    if args.email and metrics["fail_count"]:
        try:
            body = format_failed_records(metrics["failed_records"])
            send_email(args.email, "Failed records report", body)
            print(f"\nEmail sent to {args.email}")
        except Exception as exc:
            print(f"\nFailed to send email: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())

