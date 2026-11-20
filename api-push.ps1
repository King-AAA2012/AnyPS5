# API-based push to King-AAA2012/AnyPS5 using the GitHub REST API.
# Pushes via blob -> tree -> commit -> ref, bypassing git password auth (token lacks repo
# scope for git transport but works via REST). Usage:
#   ./api-push.ps1 -Branch <name> -CommitMessage <msg> -FileChanges @{ "<path>" = "<content>" }
# Returns the new branch SHA.

param(
    [Parameter(Mandatory)] [string]$Branch,
    [Parameter(Mandatory)] [string]$CommitMessage,
    [Parameter(Mandatory)] [hashtable]$FileChanges,   # path -> content
    [string]$CommitSha = "4fa81a86fb835e72a6bdca3057424b677dbb44fb"
)

$ErrorActionPreference = "Stop"
$token = $env:GH_TOKEN  # the token Anvil gives agents (Settings -> GitHub). Never write a token into a file.
$hdr = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json"; "Accept" = "application/vnd.github+json" }
$api = "https://api.github.com/repos/King-AAA2012/AnyPS5"

function Invoke-ApiPost($path, $rawJson) {
    $resp = Invoke-WebRequest -Uri "$api$path" -Method Post -Headers $hdr -ContentType "application/json" -Body $rawJson -UseBasicParsing -ErrorAction Stop
    return $resp
}

function To-B64($text) {
    $enc = [System.Text.Encoding]::UTF8.GetBytes($text)
    return [Convert]::ToBase64String($enc)
}

# 1. Get base commit / tree
$base = (Invoke-WebRequest -Uri "$api/commits/$CommitSha" -Headers $hdr -UseBasicParsing).Content | ConvertFrom-Json
$baseTree = (Invoke-WebRequest -Uri "$api/git/commits/$CommitSha" -Headers $hdr -UseBasicParsing).Content | ConvertFrom-Json
$baseTree = $baseTree.tree.sha

# 2. Create blobs
$blobs = foreach ($path in $FileChanges.Keys) {
    $b64 = To-B64($FileChanges[$path])
    $payload = '{"content":"' + $b64.Replace('"', '\"') + '","encoding":"base64"}'
    $r = Invoke-ApiPost "/git/blobs" $payload
    $obj = $r.Content | ConvertFrom-Json
    [pscustomobject]@{ path = $path; sha = $obj.sha }
}

# 3. Create tree (raw JSON array of objects)
$treeJson = '['
foreach ($b in $blobs) {
    $p = $b.path.Replace('\','\\/').Replace('"','\"')
    $treeJson += '{"path":"' + $p + '","mode":"100644","type":"blob","sha":"' + $b.sha + '"}'
}
$treeJson += ']'
$treeBody = '{"base_tree":"' + $baseTree + '","tree":' + $treeJson + '}'
$tr = Invoke-ApiPost "/git/trees" $treeBody
$treeSha = ($tr.Content | ConvertFrom-Json).sha

# 4. Create commit
$cm = $CommitMessage.Replace('"', '\"')
$commitBody = '{"message":"' + $cm + '","tree":"' + $treeSha + '","parents":["' + $CommitSha + '"]}'
$cr = Invoke-ApiPost "/git/commits" $commitBody
$commitSha = ($cr.Content | ConvertFrom-Json).sha

# 5. Update ref (create branch)
$br = $Branch.Replace('"','\"')
$refBody = '{"ref":"refs/heads/' + $br + '","sha":"' + $commitSha + '","force":true}'
$rr = Invoke-ApiPost "/git/refs" $refBody
echo "REF STATUS: $($rr.StatusCode)"
echo "Branch $Branch now at: $commitSha"
echo "DONE"
