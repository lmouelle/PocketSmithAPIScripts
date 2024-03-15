function Resolve-Categories($obj)
{
    $results = @{$obj.title = $obj.id}

    if ($obj.children) 
    {
        foreach ($child in $obj.children) 
        {
            $results += (Resolve-categories $child)
        }
    }

    return $results
}

set-strictmode -version 3.0

$me = invoke-restmethod -uri 'https://api.pocketsmith.com/v2/me' -headers @{ 
    'X-Developer-Key' = '';
    accept = 'application/json'
}

$top_level_catories = invoke-restmethod -uri "https://api.pocketsmith.com/v2/users/$($me.id)/categories" -headers @{ 
    'X-Developer-Key' = '';
    accept = 'application/json'
}

$categories = Resolve-Categories $top_level_catories 

$accounts = invoke-restmethod -uri  "https://api.pocketsmith.com/v2/users/$($me.id)/transaction_accounts" -headers @{ 'X-Developer-Key' = ''; 'accept' = 'application/json' }

$content = import-csv .\filewithoutdups.csv

foreach ($row in $content) 
{
    $category = $categories[$row.category]
    Write-Host "Found category $($category) for row $($row)"
    $account = ($accounts | ? {$_.name -match $row.account})
    if ($account) {
        $account = $account[0]
        $body = @{amount = $row.amount; date = $row.date; labels = $row.labels; note = $row.note; memo = $row.memo; needs_review = 'false'; payee = $row.merchant; is_transfer = 'false'; category_id = $category}

        # where to get category id for request body?
        $response = invoke-restmethod -method Post -uri "https://api.pocketsmith.com/v2/transaction_accounts/$($account.id)/transactions" -headers @{ 'X-Developer-Key' = ''; 'accept' = 'application/json'; 'content-type' = 'application/json'} -body (convertto-json $body)
        WRite-output $response
    }
    else {
        Write-Host "Find no account for row $($row)"
    }
}
