# Move the placeholder music into the Claude working folder so it can be
# processed with ffmpeg, or bring the processed versions back.
#   .\audio_roundtrip.ps1 out   -> bench\music  ->  working folder
#   .\audio_roundtrip.ps1 in    -> working folder -> bench\music

$ErrorActionPreference = "Stop"
$WORK  = "C:\Users\wolfh\AppData\Roaming\Claude\local-agent-mode-sessions\28467292-3a92-4fa3-8581-b2e328bfcdbb\ede9003d-efff-4f68-b1e2-653667ab6345\local_55c9a24b-585c-4a23-9001-db7759b707bb\outputs\_audio"
$MUSIC = "D:\GameDevelopment\_TowersOfAtheria\bench\music"
$mode  = $args[0]

New-Item -ItemType Directory -Force -Path $WORK  | Out-Null
New-Item -ItemType Directory -Force -Path $MUSIC | Out-Null

if ($mode -eq "out") {
    foreach ($n in @("calm.mp3","battle.mp3")) {
        $p = Join-Path $MUSIC $n
        if (Test-Path $p) {
            Copy-Item $p (Join-Path $WORK $n) -Force
            Write-Host ("  out  {0,-12} {1} MB" -f $n, [math]::Round((Get-Item $p).Length/1MB,2))
        } else { Write-Host "  MISSING $n" -ForegroundColor Red }
    }
}
elseif ($mode -eq "in") {
    foreach ($n in @("calm.mp3","battle.mp3")) {
        $p = Join-Path $WORK $n
        if (Test-Path $p) {
            Copy-Item $p (Join-Path $MUSIC $n) -Force
            Write-Host ("  in   {0,-12} {1} MB" -f $n, [math]::Round((Get-Item $p).Length/1MB,2))
        } else { Write-Host "  MISSING $n" -ForegroundColor Red }
    }
}
else { throw "usage: audio_roundtrip.ps1 out|in" }
