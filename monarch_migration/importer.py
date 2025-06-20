#!/usr/bin/python

import csv
from pathlib import Path
from sys import argv,stdout
from operator import attrgetter
import datetime
from bisect import bisect, bisect_left
from collections import defaultdict, namedtuple
import argparse

Transaction = namedtuple('Transaction', ['Amount', 'Date', 'Merchant', 'Notes', 'Category', 'Tags', 'Account', 'Keep'])

# TODO: Not sure I can use this since some imports do not have merchant info on some CSV imports
# so there will be some null fields.
# TODO: I want to compare ordered tokens, not unordered tokens
def string_overlap(s1 : str, s2 : str):
    return set(s1.upper().split()) & set(s2.upper().split())

def scan_range(transactions : list[Transaction], transaction_idx : int):
    lhs_idx = rhs_idx = transaction_idx
    transaction = transactions[transaction_idx]

    # Slide left until we are N days from start point or at array end
    while lhs_idx > 0 and (transaction.Date - transactions[lhs_idx].Date <= datetime.timedelta(days=args.window_size_days)):
        lhs_idx -= 1

    # Slide right until we are N days from start point or at array end
    while rhs_idx < len(transactions) and (transactions[rhs_idx].Date - transaction.Date <= datetime.timedelta(days=args.window_size_days)):
        rhs_idx += 1

    return lhs_idx, rhs_idx

def are_dups(t1 : Transaction, t2 : Transaction):
    equalish_amount = abs(transactions[comparison_idx].Amount - transaction.Amount) < .01
    return equalish_amount \
        and filter_nonfreq_trans(transaction) \
        and string_overlap(transactions[comparison_idx].Merchant, transaction.Merchant) \
        and string_overlap(transactions[comparison_idx].Account, transaction.Account)


def filter_nonfreq_trans(transaction : Transaction):
    if 'SEPTA' in transaction.Merchant.upper():
        return False
    if 'MTA*NYCT' in transaction.Merchant.upper():
        return False
    if 'Coffee Tree'.upper() in transaction.Merchant.upper():
        return False

    return True

def binary_search(l, value):
    low = 0
    high = len(l)-1
    while low <= high: 
        mid = (low+high)//2
        if l[mid] > value: high = mid-1
        elif l[mid] < value: low = mid+1
        else: return mid
    return -1

def format_transaction(row):
    d = row._asdict()
    d['Notes'] = row.Notes.replace('\n', ' ').replace('\r', '')
    d['Date'] = row.Date.strftime('%Y-%m-%d')
    return d

argparser = argparse.ArgumentParser(prog='DedupScript', description='Dedup script for finance apps')
argparser.add_argument('--discover', action='append')
argparser.add_argument('--firsttech', action='append')
argparser.add_argument('--capitalone', action='append')
argparser.add_argument('--fidelity-401k', action='append')
argparser.add_argument('--fidelity-non-401k', action='append')
argparser.add_argument('--pocketsmith', action='append')
argparser.add_argument('--monarch', action='append')
argparser.add_argument('--cap1creditcard', action='append')
argparser.add_argument('--discoverit', action='append')
argparser.add_argument('--window-size-days', default=3, type=int)

group = argparser.add_mutually_exclusive_group(required=True)
group.add_argument('--dups', action='store_true')
group.add_argument('--nondups', action='store_true')
group.add_argument('--mondups', action='store_true')

args = argparser.parse_args()


transactions = []
monarch_transactions = []

for filename in (args.discover or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Transaction Date'], '%m/%d/%Y'), 
                                      Merchant= None,
                                      Amount= float(row['Credit']) if row['Transaction Type'] == 'Credit' else -float(row['Debit']),
                                      Category= None,
                                      Account= possible_account,
                                      Tags= 'Discover Import, CSV Import',
                                      Notes= repr(row),
                                      Keep=True)
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
                                      Notes= repr(row),
                                      Keep=True)
            transactions.append(transaction)

for filename in (args.capitalone or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Transaction Date'], '%m/%d/%y'), 
                                      Merchant= row['Transaction Description'],
                                      Amount= float(row['Transaction Amount']) if row['Transaction Type'] == 'Credit' else -float(row['Transaction Amount']),
                                      Category= None,
                                      Account= possible_account,
                                      Tags= 'Capital One Import, CSV Import',
                                      Notes= repr(row),
                                      Keep=True)
            transactions.append(transaction)

# TODO: How can I combine investment account CSV import and importing holding information?

for filename in (args.fidelity_non_401k or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Run Date'], '%m/%d/%y'), 
                                      Merchant= f"{row['Action']}",
                                      Amount= float(row['Amount ($)']),
                                      Category= None,
                                      Account= possible_account,
                                      Tags= 'Fidelity Non 401k Import, CSV Import',
                                      Notes= repr(row),
                                      Keep=True)
            transactions.append(transaction)

for filename in (args.fidelity_401k or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='', encoding='utf-8-sig') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Date'], '%m/%d/%y'), 
                                      Merchant= row['Investment'],
                                      Amount= float(row['Amount ($)']),
                                      Category= row['Transaction Type'],
                                      Account= possible_account,
                                      Tags= 'Fidelity 401k Import, CSV Import',
                                      Notes= repr(row),
                                      Keep=True)
            transactions.append(transaction)

for filename in (args.monarch or []):
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                                      Merchant= row['Original Statement'],
                                      Amount= float(row['Amount']),
                                      Category= row['Category'],
                                      Account= row['Account'],
                                      Tags= row['Tags'],
                                      Notes= row['Notes'],
                                      Keep=False)
            monarch_transactions.append(transaction)

for filename in (args.pocketsmith or []):
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                                      Merchant= row['Memo'],
                                      Amount= float(row['Amount'].replace('$', '').replace(',', '')),
                                      Category= row['Category'],
                                      Account= row['Account'],
                                      Tags= 'Pocketsmith Import, CSV Import',
                                      Notes= row['Note'].replace('\n', ' ').replace('\r', ' '),
                                      Keep=True)
            transactions.append(transaction)

for filename in (args.cap1creditcard or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Transaction Date'], '%Y-%m-%d'), 
                                      Merchant= row['Description'],
                                      Amount= -float(row['Debit']) if row['Debit'] else float(row['Credit']),
                                      Category= row['Category'],
                                      Account= possible_account,
                                      Tags= 'Capital One Card Import, CSV Import',
                                      Notes= repr(row),
                                      Keep=True)
            transactions.append(transaction)

for filename in (args.discoverit or []):
    possible_account = Path(filename).stem
    with open(filename, mode='r', newline='') as infile:
        for row in csv.DictReader(infile):
            transaction = Transaction(Date= datetime.datetime.strptime(row['Trans. Date'], '%m/%d/%Y'), 
                                      Merchant= row['Description'],
                                      Amount= float(row['Amount']),
                                      Category= row['Category'],
                                      Account= possible_account,
                                      Tags= 'Discover it Card Import, CSV Import',
                                      Notes= repr(row),
                                      Keep=True)
            transactions.append(transaction)

if not transactions:
    argparser.error("Must provide at least one input")

# TODO: Normalize all account names, between monarch, pocketsmith, and the file names

transactions.sort(key = lambda row: row.Amount)
transactions.sort(key = lambda row: row.Date)

monarch_transactions.sort(key = lambda row: row.Amount)
monarch_transactions.sort(key = lambda row: row.Date)

# key is idx, value is set of dups
dups_by_idx = defaultdict(set)
# key is transaction idx, value is monarch transaction idx
monarch_dups_by_idx = defaultdict(set)

for transaction_idx, transaction in enumerate(transactions):
    for comparison_idx in range(*scan_range(transactions, transaction_idx)):
        if comparison_idx == transaction_idx:
            continue
        
        if are_dups(transactions[comparison_idx], transaction):
            dups_by_idx[comparison_idx].add(transaction_idx)
            dups_by_idx[transaction_idx].add(comparison_idx)

    monarch_lhs = bisect_left(monarch_transactions, transaction.Date, key= attrgetter('Date'))
    for mon_comparison_idx in range(*scan_range(monarch_transactions, monarch_lhs)):
        if comparison_idx == transaction_idx:
            continue
        if are_dups(monarch_transactions[mon_comparison_idx], transaction):
            monarch_dups_by_idx[transaction_idx].add(mon_comparison_idx)

# Now I should have 2 groups of multisets:
# One holds all duplicates in the general transactions
# The other maps monarch indexes to the set of things they replace
notmatch_writer = csv.DictWriter(stdout, fieldnames, quoting=csv.QUOTE_ALL)
notmatch_writer.writeheader()

for transaction_idx, transaction in enumerate(transactions):
    if args.mondups and transaction_idx in monarch_dups_by_idx:
        notmatch_writer.writerow(format_transaction(transaction))
    if args.nondups and transaction_idx not in dups_by_idx:
        notmatch_writer.writerow(format_transaction(transaction))
    if args.dups and transaction_idx in dups_by_idx:
        notmatch_writer.writerow(format_transaction(transaction))

# TODO: Handle unknown merchants, unknown category

# Define stdout writer logic, sanitize to remove excess whitespace in notes and turn datetimes to strings, etc

# TODO: Handle fields as None, esp. Merchant, Description
