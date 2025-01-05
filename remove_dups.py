#!/usr/bin/python

"""
Usage: python __FILE__ pocketsmith.csv monarch.csv ACTION
ACTION: list [Date | Account | ...] | nil
"""

import csv
from sys import argv,stdout
import datetime
from collections import UserDict

pocketsmith_transactions = []
monarch_transactions = []
fieldnames = ['Date', 'Description', 'Original Description', 'Amount', 'Transaction Type', 'Category', 'Account Name', 'Labels', 'Notes']

def is_dup(new, old):
    # If new is dup, return true
    in_window =  datetime.timedelta(days = -7) <= new['Date'] - old['Date'] <= datetime.timedelta(days = 7)
    amount_eqish = abs(new['Amount'] - old['Amount']) < 0.01
    desc_match = set(new['Description'].upper().split()) & set(old['Description'].upper().split())

    return in_window and amount_eqish and desc_match

with open(argv[1], mode='r', newline='') as pocketsmith_infile:
    d_reader = csv.DictReader(pocketsmith_infile)
    for row in d_reader:
        transaction = { 'Date': datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                        'Description': row['Merchant'],
                        'Original Description': row['Memo'],
                        'Amount': float(row['Amount']),
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
                        'Amount': float(row['Amount']),
                        'Category': row['Category'],
                        'Account Name': row['Account'] }
        monarch_transactions.append(transaction)

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


try:
    action = argv[3]
        
    if action == 'list':
        field = argv[4]
        output = {row[field] for row in monarch_transactions} & {row[field] for row in pocketsmith_transactions}
        for elem in output:
            print(elem)

    if action == 'dedup':
        final_list = list(monarch_transactions) # deep copy
        for transaction in pocketsmith_transactions:
            if not any(is_dup(transaction, t) for t in final_list):
                final_list.append(transaction)
                print(transaction)

    if action == 'getdup':
        final_list = list(monarch_transactions) # deep copy
        for transaction in pocketsmith_transactions:
            if any(is_dup(transaction, t) for t in final_list):
                print(transaction)
            final_list.append(transaction)

except BrokenPipeError:
    exit(0)
