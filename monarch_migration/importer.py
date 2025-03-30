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

# TODO: How can I combine investment account CSV import and importing holding information?

for filename in (args.fidelity_non_401k or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Run Date'], '%m/%d/%y'), 
                                      Merchant= f"{row['Action']}",
                                      Amount= float(row['Amount ($)']),
                                      Category= 'Unknown',
                                      Account= possible_account,
                                      Tags= 'Fidelity Non 401k Import, CSV Import',
                                      Notes= f"Extended Description: {row['Description']}, Symbol: {row['Symbol']}, Type: {row['Type']}")
            transactions.append(transaction)

for filename in (args.fidelity_401k or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='', encoding='utf-8-sig') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Date'], '%m/%d/%y'), 
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

transactions.sort(key = lambda row: row.Amount)
transactions.sort(key = lambda row: row.Date)
known_dup_idxs = set()

def filter_nonfreq_trans(transaction):
    if 'SEPTA' in transaction['Description'].upper():
        return False
    if 'MTA*NYCT' in transaction['Description'].upper():
        return False
    if 'Coffee Tree'.upper() in transaction['Description'].upper():
        return False

    return True

# TODO: Not sure I can use this since some imports do not have merchant info on some CSV imports
# TODO: I want to compare ordered tokens, not unordered tokens
def string_overlap(s1, s2):
    return set(s1.upper().split()) & set(s2.upper().split())

def scan_range(transactions, transaction_idx):
    lhs_idx = rhs_idx = transaction_idx
    transaction = transactions[transaction_idx]

    # Slide left until we are N days from start point or at array end
    while lhs_idx > 0 and (transaction.Date - transactions[lhs_idx].Date <= datetime.timedelta(days=args.window_size_days)):
        lhs_idx -= 1

    # Slide right until we are N days from start point or at array end
    while rhs_idx < len(transactions) and (transactions[rhs_idx].Date - transaction.Date <= datetime.timedelta(days=args.window_size_days)):
        rhs_idx += 1

    return lhs_idx, rhs_idx

def are_dups(t1, t2):
    equalish_amount = abs(transactions[comparison_idx].Amount - transaction.Amount) < .01
    return equalish_amount \
        and filter_nonfreq_trans(transaction) \
        and string_overlap(transactions[comparison_idx].Merchant, transaction.Merchant) \
        and string_overlap(transactions[comparison_idx].Account, transaction.Account)

for transaction_idx, transaction in enumerate(transactions):
    for comparison_idx in range(*scan_range(transactions, transaction_idx)):
        if comparison_idx in known_dup_idxs:
            continue

        if comparison_idx == transaction_idx:
            continue
        
        if are_dups(transactions[comparison_idx], transactions[transaction_idx]):
            known_dup_idxs.add(comparison_idx)
            known_dup_idxs.add(transaction_idx)

# TODO: Handle unknown merchants, unknown category

# Define stdout writer logic, sanitize to remove excess whitespace in notes and turn datetimes to strings, etc
