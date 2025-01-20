#!/usr/bin/python

import csv
from sys import argv,stdout
import datetime

WINDOW_SZ = 3

pocketsmith_transactions = []
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
    if 'TGTG' in transaction['Description'].upper():
        return False
    if 'MTA*NYCT' in transaction['Description'].upper():
        return False
    if 'Coffee Tree'.upper() in transaction['Description'].upper():
        return False

    return True

def sanitize_output(sanitize_output):
    sanitize_output['Date'] = datetime.datetime.strftime(sanitize_output['Date'], '%Y-%m-%d')
    sanitize_output['Notes'] = sanitize_output['Notes'].replace('\n', ' ').replace('\r', '')
    return sanitize_output

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

try:
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
            if equalish_amount and filter_nonfreq_trans(transaction):
                known_dup_idxs.add(comp_idx)
                known_dup_idxs.add(transaction_idx)

    flagged_as_dups = [x for i, x in enumerate(pocketsmith_transactions) if i in known_dup_idxs]
    
    flagged_as_dups.sort(key=lambda row: row['Date'])
    flagged_as_dups.sort(key=lambda row: row['Amount'])

    # Ok, where is an elem not the same

    notmatch_writer = csv.DictWriter(stdout, fieldnames, quoting=csv.QUOTE_ALL)
    notmatch_writer.writeheader()
    # Dates are strings now after this!
    notmatch_writer.writerows(sanitize_output(x) for x in flagged_as_dups)

except BrokenPipeError:
    pass
