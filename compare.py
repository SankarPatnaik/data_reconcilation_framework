#!/usr/bin/env python3
"""
Data comparison tool.

Compares two delimited text files and reports differences at the row and
column level. Optionally sends an email with the report.
"""
import argparse
import csv
import os
import smtplib
from email.message import EmailMessage


def read_table(path, delimiter):
    """Return the table at *path* as a list of rows."""
    with open(path, newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        return list(reader)


def compare_tables(table1, table2):
    """Compare two tables and return diff metrics."""
    max_rows = max(len(table1), len(table2))
    max_cols = max(len(table1[0]) if table1 else 0,
                   len(table2[0]) if table2 else 0)

    column_diffs = [0] * max_cols
    mismatched_rows = []
    cell_differences = 0

    for i in range(max_rows):
        row1 = table1[i] if i < len(table1) else [""] * max_cols
        row2 = table2[i] if i < len(table2) else [""] * max_cols

        if len(row1) < max_cols:
            row1.extend([""] * (max_cols - len(row1)))
        if len(row2) < max_cols:
            row2.extend([""] * (max_cols - len(row2)))

        row_mismatch = False
        for j in range(max_cols):
            if row1[j] != row2[j]:
                column_diffs[j] += 1
                cell_differences += 1
                row_mismatch = True
        if row_mismatch:
            mismatched_rows.append(i + 1)  # 1-indexed

    return {
        "rows_file1": len(table1),
        "rows_file2": len(table2),
        "extra_rows_file1": max(0, len(table1) - len(table2)),
        "extra_rows_file2": max(0, len(table2) - len(table1)),
        "cell_differences": cell_differences,
        "column_differences": {
            f"col{idx + 1}": diff for idx, diff in enumerate(column_diffs) if diff
        },
        "mismatched_rows": mismatched_rows,
    }


def format_report(file1, file2, metrics):
    """Format diff *metrics* into a human readable report."""
    lines = [
        "Comparison Report",
        "=================",
        f"File 1: {file1}",
        f"File 2: {file2}",
        "",
        f"Rows in File 1: {metrics['rows_file1']}",
        f"Rows in File 2: {metrics['rows_file2']}",
        f"Extra rows in File 1: {metrics['extra_rows_file1']}",
        f"Extra rows in File 2: {metrics['extra_rows_file2']}",
        f"Cell differences: {metrics['cell_differences']}",
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
        description="Compare two delimited text files and report differences."
    )
    parser.add_argument("file1", help="first file to compare")
    parser.add_argument("file2", help="second file to compare")
    parser.add_argument(
        "--delimiter",
        default=",",
        help="field delimiter used in the files (default: comma)",
    )
    parser.add_argument(
        "--email", help="send report to this email address", metavar="ADDRESS"
    )
    args = parser.parse_args()

    table1 = read_table(args.file1, args.delimiter)
    table2 = read_table(args.file2, args.delimiter)
    metrics = compare_tables(table1, table2)
    report = format_report(args.file1, args.file2, metrics)
    print(report)

    if args.email:
        try:
            send_email(args.email, "Data comparison report", report)
            print(f"\nEmail sent to {args.email}")
        except Exception as exc:
            print(f"\nFailed to send email: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
