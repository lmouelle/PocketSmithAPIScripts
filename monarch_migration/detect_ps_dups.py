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
"""
with open(argv[2], mode='r', newline='') as monarch_infile:
    d_reader = csv.DictReader(monarch_infile)
    for row in d_reader:
        transaction = { 'Date': datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                        'Description': row['Merchant'],
                        'Original Description': row['Original Statement'],
                        'Amount': float(row['Amount']),
                        'Category': row['Category'],
                        'Account Name': row['Account'] }
        monarch_transactions.append(transaction)
"""

"""
luouelle@desktop ~/N/A/finance_app> python ~/Code/PocketSmithAPIScripts/remove_dups.py ./pocketsmith-transactions-2024-12-22.csv monarch-money-transactions-2024-12-29.csv | sort -u
Bank of America Checking
Bank Of America Credit Card
Discover Crisis Fund
Discover it Credit Card
First Tech Checking (Rewards)
First Tech Member Savings (ATM)
First Tech Mortgage
"""

pocketsmith_transactions.sort(key = lambda row: row['Amount'])
pocketsmith_transactions.sort(key = lambda row: row['Date'])

known_dup_idx = set()

def final_transform(transaction):
    transaction['Date'] = datetime.datetime.strftime(transaction['Date'], '%Y-%m-%d')
    transaction['Notes'] = transaction['Notes'].replace('\n', ' ').replace('\r', '')
    return transaction

try:
    for transaction_idx, transaction in enumerate(pocketsmith_transactions):
        """
        Sliding window. Grow window from right till size N (3 days).
        Check if contains possible dups, if so print all of them.
            Then constrict window from left until no dups exist or is size 0
        if no dups and size == n, then slide window right

        """
        lhs_idx, rhs_idx = transaction_idx, transaction_idx

        # Slide left until we are N days from start point or at array end
        while lhs_idx > 0 and (transaction['Date'] - pocketsmith_transactions[lhs_idx]['Date'] <= datetime.timedelta(days=WINDOW_SZ)):
            lhs_idx -= 1

        # Slide right until we are N days from start point or at array end
        while rhs_idx < len(pocketsmith_transactions) and (pocketsmith_transactions[rhs_idx]['Date'] - transaction['Date'] <= datetime.timedelta(days=WINDOW_SZ)):
            rhs_idx += 1

        # Now we have our window defined, check if dups exist in this range
        for comp_idx in range(lhs_idx, rhs_idx):
            # Don't worry about merchants for now
            if comp_idx in known_dup_idx:
                continue

            if comp_idx == transaction_idx:
                continue

            if abs(pocketsmith_transactions[comp_idx]['Amount'] - transaction['Amount']) < .01:
                known_dup_idx.add(comp_idx)
                known_dup_idx.add(transaction_idx)

    d_writer = csv.DictWriter(stdout, fieldnames, quoting=csv.QUOTE_ALL)
    d_writer.writeheader()
    d_writer.writerows(final_transform(x) for i, x in enumerate(pocketsmith_transactions) if i not in known_dup_idx)

except BrokenPipeError:
    pass
