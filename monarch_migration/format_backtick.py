#!/usr/bin/env python

import csv
from sys import stdin, stdout

reader = csv.reader(stdin)
writer = csv.writer(stdout, delimiter='`', quoting=csv.QUOTE_ALL)

try:
    for row in reader:
        writer.writerow(row)
except BrokenPipeError:
    exit(0)
    