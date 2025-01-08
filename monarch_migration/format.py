#!/usr/bin/env python

import csv
from sys import stdin, stdout

fieldnames = ["Date","Merchant","Merchant Changed From","Amount","Currency","Transaction Type","Account","Closing Balance","Category","Parent Categories","Labels","Memo","Note","ID","Bank","Account Number"]

reader = csv.DictReader(stdin, fieldnames)
writer = csv.DictWriter(stdout, fieldnames, delimiter='`')

try:
    writer.writeheader()
    _ = next(reader) # Ignore the header from reader when writingz
    for row in reader:
        if row.get('Labels', '') == '':
            row['Labels'] = 'PocketsmithImport'
        else:
            row["Labels"] += ',PocketsmithImport'

        row = {k:(v.replace('\n', ' ').replace('\r', ' ')) for k, v in row.items()}

        writer.writerow(row)
except BrokenPipeError:
    exit(0)
    
