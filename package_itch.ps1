# Package the bench for itch.io.
#
# The zip holds index.html PLUS a music folder.
#
# The card catalog, every stamp and every sprite are still injected into
# index.html, so the game is playable the instant that one file lands. The
# music is deliberately NOT inlined: the battle track would bolt megabytes
# onto the first byte of the page and nothing would render until it
# finished. As separate files the game opens immediately and the music
# streams in behind it.
#
# NOT built with Compress-Archive. On Windows that writes entry names with
# BACKSLASHES (music\calm.mp3). The ZIP spec requires forward slashes, and
# itch extracts on Linux - so the tracks would land at a literal filename
# "music\calm.mp3" in the root, the game's fetch of "music/calm.mp3" would
# 404, and the music would silently fall back to the synthesised loops with
# no error anywhere. Entries are written by hand with forward slashes.

$ErrorActionPreference = "Stop"
$bench = "D:\GameDevelopment\_TowersOfAtheria\bench"
$zip   = "D:\GameDevelopment\_TowersOfAtheria\TowersOfAtheria_bench_v0.02.zip"

if (-not (Test-Path "$bench\index.html")) { throw "index.html not found in $bench" }

# entry name in the zip  ->  file on disk
$plan = [ordered]@{ "index.html" = "$bench\index.html" }
foreach ($n in @("calm.mp3","battle.mp3")) {
    $p = "$bench\music\$n"
    if (Test-Path $p) { $plan["music/$n"] = $p }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path $zip) { Remove-Item $zip -Force }

$fs = [System.IO.File]::Open($zip, [System.IO.FileMode]::CreateNew)
$ar = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
foreach ($entryName in $plan.Keys) {
    $entry  = $ar.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
    $out    = $entry.Open()
    $bytes  = [System.IO.File]::ReadAllBytes($plan[$entryName])
    $out.Write($bytes, 0, $bytes.Length)
    $out.Dispose()
}
$ar.Dispose(); $fs.Dispose()

$item = Get-Item $zip
Write-Host ""
Write-Host "  ZIP   $($item.FullName)"
Write-Host "  SIZE  $([math]::Round($item.Length / 1MB, 2)) MB"
Write-Host ""

$check = [System.IO.Compression.ZipFile]::OpenRead($zip)
Write-Host "  contents:"
$names = @()
foreach ($e in $check.Entries) {
    $names += $e.FullName
    Write-Host ("    {0,-24} {1,7} KB" -f $e.FullName, [math]::Round($e.Length / 1KB))
}
$check.Dispose()

Write-Host ""
$bad = $names | Where-Object { $_ -like "*\*" }
if ($bad) { Write-Host "  FAIL backslash entries: $($bad -join ', ')" -ForegroundColor Red }
else      { Write-Host "  OK   all entries use forward slashes" -ForegroundColor Green }

if ($names -contains "index.html") { Write-Host "  OK   index.html is at the zip root" -ForegroundColor Green }
else { Write-Host "  FAIL index.html is NOT at the zip root" -ForegroundColor Red }

if (($names -contains "music/calm.mp3") -and ($names -contains "music/battle.mp3")) {
    Write-Host "  OK   both tracks present at music/" -ForegroundColor Green
} else {
    Write-Host "  WARN music missing - game falls back to synthesised loops" -ForegroundColor Yellow
}
Write-Host ""
