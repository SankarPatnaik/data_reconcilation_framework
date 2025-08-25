#!/bin/sh
# Simple wrapper around compare.py
# Usage: ./compare_files.sh file1 file2 [recipient_email]
set -e

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 file1 file2 [recipient_email]" >&2
  exit 1
fi

FILE1=$1
FILE2=$2
RECIPIENT=$3

if [ -n "$RECIPIENT" ]; then
  python3 compare.py "$FILE1" "$FILE2" --email "$RECIPIENT"
else
  python3 compare.py "$FILE1" "$FILE2"
fi
