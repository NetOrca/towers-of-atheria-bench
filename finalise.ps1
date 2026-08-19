# Tidy up and get the build scripts into the repo so they are backed up too.
$ErrorActionPreference = "Stop"
$GIT  = "D:\Git\cmd\git.exe"
$ROOT = "D:\GameDevelopment\_TowersOfAtheria"
$DST  = "$ROOT\bench"

# the packaging + audio scripts live above the repo; copy them in so a lost
# PC does not take them with it
foreach ($f in @("package_itch.ps1","stage_music.ps1","audio_roundtrip.ps1")) {
    if (Test-Path "$ROOT\$f") { Copy-Item "$ROOT\$f" "$DST\$f" -Force; Write-Host "  backed up $f" }
}

# scratch files from this session
foreach ($f in @("$ROOT\probe_music.ps1","$DST\check_push.ps1")) {
    if (Test-Path $f) { Remove-Item $f -Force; Write-Host "  removed $(Split-Path $f -Leaf)" }
}

Set-Location $DST
& $GIT add -A
& $GIT -c core.safecrlf=false commit -q -m "Back up packaging and audio scripts in the repo" 2>&1 | Out-Null
& $GIT push origin main 2>&1 | Out-Null
Write-Host ""
& $GIT log --oneline -4
Write-Host ""
& $GIT status -sb
