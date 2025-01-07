#!/usr/bin/bash

ps_file=/home/luouelle/Nextcloud/Archive/finance_app/pocketsmith-transactions-2024-12-22.csv
mon_file=/var/home/luouelle/Nextcloud/Archive/finance_app/monarch-money-transactions-2024-12-29.csv
tmp_name=tmp.txt

/var/home/luouelle/Code/PocketSmithAPIScripts/monarch_migration/format.py < $ps_file \
| sed 's/Memo/Original Statement/1' \
| sed 's/Note/Notes/1' \
| sed 's/Labels/Tags/1' \
| cut -d\` -f1,2,4,7,9,11,12,13 \
| awk -F \` -v OFS='`' '{print $1,$2,$5,$4,$7,$8,$3,$6}' \
| cat - <(/var/home/luouelle/Code/PocketSmithAPIScripts/monarch_migration/backtickize.py < $mon_file) \
| sort --stable -t\` -k1,1 \

# 9. Sort by amount, then date, then desc/merchant and eyecheck for dups // after this unsure, python script that understands datetime?
# N. tr backtick into comma again

# use split by the account name to create different files then turn backtick into comma again