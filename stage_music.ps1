# Copy the placeholder music into the bench under the names index.html expects.
#
# The bench looks for music/calm.mp3 and music/battle.mp3. Renaming here
# rather than in the code means swapping a track later is a file copy, not
# a code change - the same discipline as the sprite folder.

$ErrorActionPreference = "Stop"
$src   = "D:\GameDevelopment\_TowersOfAtheria\Music\PlaceHolder"
$dest  = "D:\GameDevelopment\_TowersOfAtheria\bench\music"

$map = @{
    "universfield-serene-horizons-30s-320651.mp3" = "calm.mp3"
    "paulyudin-battle-battle-music-491417.mp3"    = "battle.mp3"
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null

foreach ($from in $map.Keys) {
    $p = Join-Path $src $from
    if (-not (Test-Path $p)) { Write-Host "  MISSING $from" -ForegroundColor Red; continue }
    $to = Join-Path $dest $map[$from]
    Copy-Item $p $to -Force
    $mb = [math]::Round((Get-Item $to).Length / 1MB, 2)
    Write-Host ("  {0,-46} -> music\{1,-12} {2} MB" -f $from, $map[$from], $mb)
}

# Keep the original filenames on record. These are placeholders sourced
# externally - confirm the licence terms before the game is sold.
@"
PLACEHOLDER MUSIC - not final, licence not yet confirmed by GridOrcaGames.

  music/calm.mp3    <- universfield-serene-horizons-30s-320651.mp3
                       menu, deck builder, Recruitment Phase
  music/battle.mp3  <- paulyudin-battle-battle-music-491417.mp3
                       Battle Phase

Before ANY paid release, confirm each track's licence permits commercial
use and record whether attribution is required. If it is, the credit goes
on the itch page and in the in-game Rules panel.
"@ | Set-Content (Join-Path $dest "SOURCES.txt") -Encoding UTF8

Write-Host ""
Write-Host "  staged to $dest" -ForegroundColor Green
