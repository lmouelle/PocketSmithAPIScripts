#!/usr/bin/python

import csv
from sys import stdin, stdout

reader = csv.reader(stdin)
writer = csv.writer(stdout, delimiter='`')

try:
    for row in reader:
        writer.writerow(row)
except BrokenPipeError:
    exit(0)
    
