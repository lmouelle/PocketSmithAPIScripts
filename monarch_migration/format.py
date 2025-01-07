#!/usr/bin/env python

import csv
from sys import stdin, stdout

fieldnames = ["Date","Merchant","Merchant Changed From","Amount","Currency","Transaction Type","Account","Closing Balance","Category","Parent Categories","Labels","Memo","Note","ID","Bank","Account Number"]

reader = csv.DictReader(stdin, fieldnames)
writer = csv.DictWriter(stdout, fieldnames, delimiter='`', quoting=csv.QUOTE_ALL)

try:
    writer.writeheader()
    _ = next(reader) # Ignore the header from reader when writingz
    for row in reader:
        row['Note'] = row['Note'].replace('\n', ' ').replace('\r', ' ')

        if row.get('Labels', '') == '':
            row['Labels'] = 'PocketsmithImport'
        else:
            row["Labels"] += ',PocketsmithImport'

        writer.writerow(row)
except BrokenPipeError:
    exit(0)
    
