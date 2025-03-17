#!/usr/bin/bash

ps_file=/home/luouelle/Nextcloud/Archive/finance_app/pocketsmith-transactions-2024-12-22.csv
mon_file=/var/home/luouelle/Nextcloud/Archive/finance_app/monarch-money-transactions-2024-12-29.csv
tmp_name=tmp.txt

./detect_ps_dups.py ~/Nextcloud/Archive/finance_app/pocketsmith-transactions-2024-12-22.csv \
| grep -v SEPTA \
| grep -v TGTG \
| grep -v "MTA\*NYCT" \
| grep -v "Transfer & Card Payments"