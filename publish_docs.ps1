# Copy the handoff docs into the repo and push them, so the knowledge survives
# any single chat session.
$ErrorActionPreference = "Stop"
$GIT = "D:\Git\cmd\git.exe"
$SRC = "C:\Users\wolfh\AppData\Roaming\Claude\local-agent-mode-sessions\28467292-3a92-4fa3-8581-b2e328bfcdbb\ede9003d-efff-4f68-b1e2-653667ab6345\local_55c9a24b-585c-4a23-9001-db7759b707bb\outputs"
$DST = "D:\GameDevelopment\_TowersOfAtheria\bench"

foreach ($f in @("BENCH_ARCHITECTURE.md","NEXT_SESSION.md")) {
    $p = Join-Path $SRC $f
    if (Test-Path $p) {
        Copy-Item $p (Join-Path $DST $f) -Force
        Write-Host ("  copied {0}  ({1} KB)" -f $f, [math]::Round((Get-Item $p).Length/1KB,1))
    } else { Write-Host "  MISSING $f" -ForegroundColor Yellow }
}

Set-Location $DST
& $GIT add -A
& $GIT -c core.safecrlf=false commit -q -m "Add BENCH_ARCHITECTURE.md so a fresh session can pick this up without the chat" 2>&1 | Out-Null
& $GIT push origin main 2>&1 | Out-Null
Write-Host ""
& $GIT log --oneline -3
Write-Host ""
& $GIT status -sb
