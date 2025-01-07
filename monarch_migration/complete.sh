#!/usr/bin/bash

#                        'Tags': 'Pocketsmith Import' }

# 1. Use backtick as delimiter and quote all
# 2. Rename relevant fields
# 3. Select/project fields I will use
# 4. Reorder fields
# 5. Trim space in notes section
# 6. Add 'pocketsmith import' label/tag
# 7. Output to same formm as monarch file in tmp file
# 8. Concat all into large file
# 9. Sort by amount, then date, then desc/merchant and eyecheck for dups // after this unsure, python script that understands datetime?

ps_file=/home/luouelle/Nextcloud/Archive/finance_app/pocketsmith-transactions-2024-12-22.csv 
/var/home/luouelle/Code/PocketSmithAPIScripts/monarch_migration/format_backtick.py < $ps_file | sed 's/Merchant/Description/1' | sed 's/Memo/Original Description/1' | sed 's/Note/Notes/1' | sed 's/Account/Account Name/1' | cut -d\` -f1,2,4,6,7,9,11,12,13 | awk -F \` -v OFS='`' '{print $1,$2,$8,$3,$4,$6,$5,$7,$9}'
