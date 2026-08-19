$GIT = "D:\Git\cmd\git.exe"
Set-Location "D:\GameDevelopment\_TowersOfAtheria\bench"
Write-Host "--- log ---";        & $GIT log --oneline -3
Write-Host "--- status ---";     & $GIT status -sb
Write-Host "--- lfs files ---";  & $GIT lfs ls-files
Write-Host "--- push retry ---"; & $GIT push origin main 2>&1 | ForEach-Object { $_.ToString() }
Write-Host "--- exit $LASTEXITCODE ---"
