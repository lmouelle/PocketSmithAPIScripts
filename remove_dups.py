#!/usr/bin/python

import csv
from sys import argv,stdout
import datetime

pocketsmith_transactions = []
monarch_transactions = []
fieldnames = ['Date', 'Merchant', 'Category', 'Account', 'Original Statement', 'Notes', 'Amount', 'Tags']

with open(argv[1], mode='r', newline='') as pocketsmith_infile:
    d_reader = csv.DictReader(pocketsmith_infile)
    for row in d_reader:
        transaction = { 'Date': datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                        'Merchant': row['Merchant'],
                        'Category': row['Category'],
                        'Account': row['Account'],
                        'Original Statement': row['Memo'],
                        'Notes': row['Note'],
                        'Amount': float(row['Amount']),
                        'Tags': 'Pocketsmith Import' }
        pocketsmith_transactions.append(transaction)

with open(argv[2], mode='r', newline='') as monarch_infile:
    d_reader = csv.DictReader(monarch_infile)
    for row in d_reader:
        transaction = { 'Date': datetime.datetime.strptime(row['Date'], '%Y-%m-%d'), 
                        'Merchant': row['Merchant'],
                        'Category': row['Category'],
                        'Account': row['Account'],
                        'Notes': row['Notes'],
                        'Amount': float(row['Amount']),
                        'Tags': 'Monarch Duplicate' }
        monarch_transactions.append(transaction)

def format_transaction(transaction):
    return f"Date={transaction['Date']}`Merchant={transaction['Merchant']}`Category={transaction['Category']}`Account={transaction['Account']}`Original Statement={transaction['Original Statement']}`Notes={transaction['Notes']}`Amount={transaction['Amount']}`Tags={transaction['Tags']}"

def normalize(transaction, column, name):
    if name.upper() in transaction[column].upper():
        transaction[column] = name

# TODO: Update all the pocketsmith categories and merchants to match up with new monarch categories

pocket_min = min(pocketsmith_transactions, key= lambda transaction: transaction['Date'])
monarch_min = min(monarch_transactions, key= lambda transaction: transaction['Date'])

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
    boa_card_writer = csv.DictWriter('boa_credit_card.csv', fieldnames, extrasaction='raise', quoting=csv.QUOTE_ALL)
    boa_checking_writer = csv.DictWriter('boa_checking.csv', fieldnames, extrasaction='raise', quoting=csv.QUOTE_ALL)
    first_tech_checking_writer = csv.DictWriter('first_tech_checking.csv', fieldnames, extrasaction='raise', quoting=csv.QUOTE_ALL)
    first_tech_member_writer = csv.DictWriter('first_tech_member.csv', fieldnames, extrasaction='raise', quoting=csv.QUOTE_ALL)
    first_tech_savings_writer = csv.DictWriter('first_tech_savings.csv', fieldnames, extrasaction='raise', quoting=csv.QUOTE_ALL)
    first_tech_mortgage_writer = csv.DictWriter('first_tech_mortgage.csv', fieldnames, extrasaction='raise', quoting=csv.QUOTE_ALL)

    boa_checking_writer.writeheader()

    for transaction in pocketsmith_transactions:
        if pocket_min['Date'] < transaction['Date'] < monarch_min['Date']:

            # Output to monarch time format
            transaction['Date'] = transaction['Date'].strftime('%Y-%m-%d')
            # Weak dedup attempt
            normalize(transaction,'Merchant', 'Uber')
            normalize(transaction,'Merchant', 'OkCupid')
            normalize(transaction,'Merchant', 'Venmo')
            normalize(transaction,'Merchant', 'UMCP')
            normalize(transaction,'Merchant', 'TING')
            normalize(transaction,'Merchant', 'Steam')

            #writer.writerow(transaction)
            print(transaction['Account'], file=stdout)
except BrokenPipeError:
    exit(0)