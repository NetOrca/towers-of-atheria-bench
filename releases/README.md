# Release archive

**GitHub keeps every version. itch.io only ever carries the current one.**

That is the rule, and these two halves depend on each other: the old build is
deleted from itch on every update, so if it is not committed here first, it is
gone. Nothing is archived anywhere else — the zips are not on itch, not in a
backup, not in a drive folder.

Zips are stored through Git LFS (see `../.gitattributes`). They are ~3 MB each
and not diffable, so keeping them in the tree would bloat every clone forever.

## What is in a release zip

    index.html        the whole game, catalog and art inlined
    music/calm.mp3    background track
    music/battle.mp3  battle track

Built by `../package_itch.ps1`, which also checks the zip uses forward-slash
entry names — Windows writes backslashes and itch extracts on Linux, so a
backslash entry silently 404s the music.

## Versions

    v0.01  first playable bench
    v0.02  music, audio dock
    v0.03  smarter opponents, every effect asks before it resolves
    v0.04  Master opponent, Autoplay, Flip Summon, four dead cards fixed
