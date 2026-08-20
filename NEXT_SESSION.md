# Where we left off — v0.02, music and card view

## Upload this
`D:\GameDevelopment\_TowersOfAtheria\TowersOfAtheria_bench_v0.02.zip` — 3.01 MB.

Contents: `index.html` at the root plus `music/calm.mp3` and `music/battle.mp3`.
It is no longer a single file, and that is deliberate — see below.

## Done this session
- **Sprites moved off the tier badge.** They were overlapping it on hand cards
  and builder tiles. Tier badge owns the top-right corner now, sprite sits clear.
- **Card view.** The skill sheet is now a card-shaped panel with the sprite
  centred — tier and rarity top-left, Dweller top-right, art box, name banner,
  then attack / movement / die across the bottom. Same information hierarchy as
  the printed card without showing any final art.
- **Your two tracks are in.** Calm covers the menu, the deck builder and the
  Recruitment Phase; battle covers the Battle Phase. It crossfades on the phase
  change.
- **Audio dock**, top-left, on every screen — music and effects toggle
  separately, keys `M` and `N`, and the choice is remembered between visits.

## Three things I changed that you should know about
1. **The music is not inlined.** Base64 would have added megabytes to the first
   byte of the page and nothing would render until it downloaded. As separate
   files the game opens instantly and the music arrives behind it. The battle
   track is `preload="none"` so it is not even requested until someone fights.
2. **Both tracks were trimmed and re-encoded.** They had ~500 ms of dead air at
   the top and tail, which on a 30-second loop is a silence you hear every half
   minute. Now zero. Also dropped 256 kbps to 128 kbps — inaudible at 30% volume
   and it halved the download, 5.9 MB to 2.9 MB.
3. **The calm loop is gapless.** It is decoded once and looped through Web Audio,
   which is sample-accurate. Battle streams instead — decoding 2:41 would cost
   ~60 MB of RAM to remove a seam heard once every three minutes.

If the tracks are ever missing, the game falls back to the synthesised loops
rather than going silent.

## Swapping a track later
Drop the new file in `D:\GameDevelopment\_TowersOfAtheria\Music\PlaceHolder`,
update the name map in `stage_music.ps1`, then run `stage_music.ps1` and
`package_itch.ps1`. No code changes — same discipline as the sprite folder.

## Licence — do this before anything is sold
Both tracks came from Pixabay, which permits commercial use, but
`bench\music\SOURCES.txt` records the original filenames so it can be confirmed
and credited. Worth settling before money is involved, not after.

## Why the battle music never played
The calm track worked and the battle track did not, because they were on two
different code paths. Calm went through Web Audio, which needs the
AudioContext resumed **once** on the first click and is allowed forever after.
Battle was an `<audio>` element, and media elements sit behind a **separate**
autoplay gate that needs user activation **at the moment `play()` is called**.
`toBattle()` is usually reached from a timer during the opponent's turn, not
straight off a click, so activation had expired and `play()` rejected with
`NotAllowedError` — silently, because the rejection was being swallowed.

Fixed by deleting every media element. Both tracks now decode into buffers and
loop through the audio graph. That also makes both loops sample-accurate.

## Grand campaign format — your idea, parked
You raised testing the fundamental movement rules over a longer arc. Worth
doing, and the bench is the right place for it, but after the physical game is
sellable. Noted here so it does not get lost.

## Two bugs worth remembering
- **`save()` collision.** I added a preference saver called `save()` — there was
  already a `save()` persisting the deck store. The second declaration would
  have silently replaced the first and stopped decks saving, with no error.
  Renamed to `savePref()`. Same class of bug as the `F` shadowing earlier.
- **Backslash zip entries.** `Compress-Archive` writes `music\calm.mp3`. The ZIP
  spec requires forward slashes and itch extracts on Linux, so the tracks would
  have landed as a literal file named `music\calm.mp3` in the root, the fetch
  would 404, and the music would have silently fallen back with no error
  anywhere. `package_itch.ps1` now writes entries by hand and asserts on it.

## Still open
- **Screenshots for the itch page.** Still the only thing outstanding on release.
- Phone layouts were verified by forcing breakpoints and measuring geometry, not
  on a real device.
- Task #12 Blender library, #22 GameCrafter product line, #23 rulebook relayout,
  #28 Poker Folio quickstart, #30 printable playmat, #33 branding swap,
  #34 verify `class_number` live.
- Async multiplayer — on the back burner by your call.

## The two threads you named
1. **Modelling pipeline + Blender library.** You want to talk through your ideas
   first. Still the critical path for the physical product; 66 art notes and the
   deck-wide direction already live in `build_catalog.py`.
2. **New archetypes**, including the **lizard men deck**. Better after the
   pipeline so new cards can be modelled rather than just written.

## Your question about dropping Godot
Worth taking seriously — but the honest split is that the bench is already
excellent at being a bench, and "full release video game" is a different job.
The browser will hold up fine for this game specifically: it is turn-based, the
board is 30 squares, there are no physics and no realtime rendering. What it
does not give you is a Steam build, controller support, or a storefront that
takes payment for a download. Those are the questions to answer before choosing,
not the rendering.

## The one thing not to lose
Your playtest finding: **Alfred's +3 aura is safe because the tribute economy
eats the Tier 1s he needs standing next to him.** That came from playing, not
from maths.
