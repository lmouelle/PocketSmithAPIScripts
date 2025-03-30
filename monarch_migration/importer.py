#!/usr/bin/python

import csv
from pathlib import Path
from sys import argv,stdout
import datetime
from collections import defaultdict, namedtuple
import argparse

argparser = argparse.ArgumentParser(prog='DedupScript', description='Dedup script for finance apps')
argparser.add_argument('--discover', action='append')
argparser.add_argument('--firsttech', action='append')
argparser.add_argument('--capitalone', action='append')
argparser.add_argument('--fidelity-401k', action='append')
argparser.add_argument('--fidelity-non-401k', action='append')
argparser.add_argument('--pocketsmith', action='append')
argparser.add_argument('--monarch', action='append')
argparser.add_argument('--window-size-days', default=3, type=int)
args = argparser.parse_args()

Transaction = namedtuple('Transaction', ['Amount', 'Date', 'Merchant', 'Notes', 'Category', 'Tags', 'Account'])

transactions = []

for filename in (args.discover or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Transaction Date'], '%m/%d/%Y'), 
                                      Merchant= 'Unknown',
                                      Amount= float(row['Credit']) if row['Transaction Type'] == 'Credit' else -float(row['Debit']),
                                      Category= 'Unknown',
                                      Account= possible_account,
                                      Tags= 'Discover Import, CSV Import',
                                      Notes= f"Discover CSV Import from {possible_account} has no merchant or category info")
            transactions.append(transaction)

for filename in (args.firsttech or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Posting Date'], '%m/%d/%Y'), 
                                      Merchant= row['Extended Description'],
                                      Amount= float(row['Amount']),
                                      Category= row['Transaction Category'] or 'Unknown',
                                      Account= possible_account,
                                      Tags= 'First Tech Import, CSV Import',
                                      Notes= f"{row['Memo']}")
            transactions.append(transaction)

for filename in (args.capitalone or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Transaction Date'], '%m/%d/%y'), 
                                      Merchant= row['Transaction Description'],
                                      Amount= float(row['Transaction Amount']) if row['Transaction Type'] == 'Credit' else -float(row['Transaction Amount']),
                                      Category= 'Unknown',
                                      Account= possible_account,
                                      Tags= 'Capital One Import, CSV Import',
                                      Notes= '')
            transactions.append(transaction)

# TODO: I need some preprocessing for all fidelity CSVs to strip leading 2-3 rows of whitespace and last few lines of legal notice
# before consuming it into the CSV reader
# TODO: How can I combine investment account CSV import and importing holding information?
# TODO: Define merging script to combine the multiple years of files for fidelity brokerage, 401k since
# I could not download them all in one batch

for filename in (args.fidelity_non_401k or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Run Date'], '%m/%d/%Y'), 
                                      Merchant= f"{row['Action']}",
                                      Amount= float(row['Amount ($)']),
                                      Category= 'Unknown',
                                      Account= possible_account,
                                      Tags= 'Fidelity Non 401k Import, CSV Import',
                                      Notes= f"Extended Description: {row['Description']}, Symbol: {row['Symbol']}, Type: {row['Type']}")
            transactions.append(transaction)

for filename in (args.fidelity_401k or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Date'], '%m/%d/%Y'), 
                                      Merchant= row['Investment'],
                                      Amount= float(row['Amount ($)']),
                                      Category= row['Transaction Type'] or 'Unknown',
                                      Account= possible_account,
                                      Tags= 'Fidelity 401k Import, CSV Import',
                                      Notes= '')
            transactions.append(transaction)

if not transactions:
    argparser.error("Must provide at least one input")

# Define dedup logic (big single array sorted by time, growing window by num days, accounts eq and amounts similar and merchants similar)

# Define stdout writer logic, sanitize to remove excess whitespace in notes and turn datetimes to strings, etc