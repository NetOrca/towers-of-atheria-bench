# Copy the bench files from the Claude working folder into the git repo on D:,
# then commit and push. Written as a file because the shell bridge eats $ signs.
$ErrorActionPreference = "Stop"
$GIT = "D:\Git\cmd\git.exe"
$SRC = "C:\Users\wolfh\AppData\Roaming\Claude\local-agent-mode-sessions\28467292-3a92-4fa3-8581-b2e328bfcdbb\ede9003d-efff-4f68-b1e2-653667ab6345\local_55c9a24b-585c-4a23-9001-db7759b707bb\outputs"
$DST = "D:\GameDevelopment\_TowersOfAtheria\bench"
$MSG = $args[0]
if (-not $MSG) { $MSG = "bench update" }

$files = @("index.html","toa_catalog.js","toa_catalog.json","build_catalog.py",
           "build_stamps.py","build_sprites.py","cards_ASH.csv","cards_HNR.csv")
foreach ($f in $files) {
    $p = Join-Path $SRC $f
    if (Test-Path $p) { Copy-Item $p -Destination $DST -Force; Write-Host "  copied $f" }
    else { Write-Host "  MISSING $f" -ForegroundColor Yellow }
}

Set-Location $DST
& $GIT add -A
& $GIT -c core.safecrlf=false commit -q -m $MSG 2>&1 | Out-Null
Write-Host ""
& $GIT push origin main 2>&1 | Select-Object -Last 3
Write-Host ""
& $GIT log --oneline -3
