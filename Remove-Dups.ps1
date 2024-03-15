$csv = import-csv pocketsmith-search.csv

for ($i = 0; $i -lt $csv.Length; $i += 2)
{
    Write-Output $csv[$i]
}