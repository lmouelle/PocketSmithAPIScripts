#!/usr/bin/python

import csv
from sys import argv,stdout
import datetime
from collections import defaultdict

WINDOW_SZ = 3

pocketsmith_transactions = []
monarch_transactions = defaultdict(list)
fieldnames = ['Date', 'Description', 'Original Description', 'Amount', 'Transaction Type', 'Category', 'Account Name', 'Labels', 'Notes']

with open(argv[1], mode='r', newline='') as pocketsmith_infile:
    d_reader = csv.DictReader(pocketsmith_infile)
    for row in d_reader:
        transaction = { 'Date': datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                        'Description': row['Merchant'],
                        'Original Description': row['Memo'],
                        'Amount': float(row['Amount'].replace('$', '').replace(',', '')),
                        'Transaction Type': row['Transaction Type'],
                        'Category': row['Category'],
                        'Account Name': row['Account'],
                        'Labels': 'Pocketsmith Import',
                        'Notes': row['Note']}
        pocketsmith_transactions.append(transaction)

with open(argv[2], mode='r', newline='') as monarch_infile:
    d_reader = csv.DictReader(monarch_infile)
    for row in d_reader:
        transaction = { 'Date': datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                        'Description': row['Merchant'],
                        'Original Description': row['Original Statement'],
                        'Amount': float(row['Amount'].replace('$', '').replace(',', '')),
                        'Category': row['Category'],
                        'Account Name': row['Account'],
                        'Labels': 'Monarch Dup From Pocketsmith Import',
                        'Notes': row['Notes']}
                        
        monarch_transactions[transaction['Date'].timetuple().tm_yday].append(transaction)

pocketsmith_transactions.sort(key = lambda row: row['Amount'])
pocketsmith_transactions.sort(key = lambda row: row['Date'])

known_dup_idxs = set()

"""
Public transit commonly is multiple equal transactions within days
so remove that as a false positive

Also Too Good To Go

Coffee Tree is where I got multiple of the same order every day
"""
def filter_nonfreq_trans(transaction):
    if 'SEPTA' in transaction['Description'].upper():
        return False
    if 'MTA*NYCT' in transaction['Description'].upper():
        return False
    if 'Coffee Tree'.upper() in transaction['Description'].upper():
        return False

    return True

def string_overlap(s1, s2):
    return set(s1.upper().split()) & set(s2.upper().split())

def scan_range(pocketsmith_transactions, transaction_idx):
    lhs_idx = rhs_idx = transaction_idx
    transaction = pocketsmith_transactions[transaction_idx]

    # Slide left until we are N days from start point or at array end
    while lhs_idx > 0 and (transaction['Date'] - pocketsmith_transactions[lhs_idx]['Date'] <= datetime.timedelta(days=WINDOW_SZ)):
        lhs_idx -= 1

    # Slide right until we are N days from start point or at array end
    while rhs_idx < len(pocketsmith_transactions) and (pocketsmith_transactions[rhs_idx]['Date'] - transaction['Date'] <= datetime.timedelta(days=WINDOW_SZ)):
        rhs_idx += 1

    return lhs_idx, rhs_idx

def run_loop(pocketsmith_transactions):
    for transaction_idx, transaction in enumerate(pocketsmith_transactions):
        """
        Sliding window. Grow window from right till size N (3 days).
        Check if contains possible dups, if so print all of them.
            Then constrict window from left until no dups exist or is size 0
        if no dups and size == n, then slide window right

        """
        lhs_idx, rhs_idx = scan_range(pocketsmith_transactions, transaction_idx)

        # Now we have our window defined, check if dups exist in this range
        for comp_idx in range(lhs_idx, rhs_idx):
            # Don't worry about merchants for now
            if comp_idx in known_dup_idxs:
                continue

            if comp_idx == transaction_idx:
                continue
            
            equalish_amount = abs(pocketsmith_transactions[comp_idx]['Amount'] - transaction['Amount']) < .009
            if equalish_amount and filter_nonfreq_trans(transaction) \
                and string_overlap(pocketsmith_transactions[comp_idx]['Description'], transaction['Description']) \
                and string_overlap(pocketsmith_transactions[comp_idx]['Account Name'], transaction['Account Name']):
                known_dup_idxs.add(comp_idx)
                known_dup_idxs.add(transaction_idx)

    # Skipping every other transaction does mangle things like transfers on some accounts,
    # but eh good enough
    removed_dups = [x for i, x in enumerate(pocketsmith_transactions) if i not in known_dup_idxs or i % 2 == 0]
    
    removed_dups.sort(key=lambda row: row['Date'])
    removed_dups.sort(key=lambda row: row['Amount'])

    return removed_dups


def mon_trans_overlap(ps_transaction, mon_transactions_day):
    for transaction in mon_transactions_day:
        equalish_amount = abs(transaction['Amount'] - ps_transaction['Amount']) < .01
        if equalish_amount and filter_nonfreq_trans(transaction) \
            and string_overlap(ps_transaction['Description'], transaction['Description']) \
            and string_overlap(ps_transaction['Account Name'], transaction['Account Name']):
            
            return True

    return False

try:
    ps_transactions_deduped = run_loop(pocketsmith_transactions)

    # Everything in the monarch file is by def already there
    # Do not bother with dedup logic, check check if it exists there and omit it
    # if it already is in the pocketsmith transactions
    output = []
    for transaction in ps_transactions_deduped:
        lower, upper = transaction['Date'].timetuple().tm_yday - WINDOW_SZ, transaction['Date'].timetuple().tm_yday + WINDOW_SZ
        
        for j in range(lower, upper + 1):
            if not mon_trans_overlap(transaction, monarch_transactions[j]):
                output.append(transaction)

    notmatch_writer = csv.DictWriter(stdout, fieldnames, quoting=csv.QUOTE_ALL)
    notmatch_writer.writeheader()
    for row in output:
        row['Date'] = row['Date'].strftime('%Y-%m-%d')
        row['Notes'] = row['Notes'].replace('\n', ' ').replace('\r', '')
        notmatch_writer.writerow(row)

except BrokenPipeError:
    pass
