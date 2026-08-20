# Towers of Atheria — Dweller Clash Bench
## How it works, for whoever picks this up next

This exists so the bench can be understood without the chat it was built in.
If you are a fresh session reading this: everything you need is here plus the
comments in `index.html`. Read this first, then the file.

---

## 1. What this is

A browser prototype of the physical card game, doing five jobs at once:

1. **Audience testing** — send people a link, watch them play.
2. **Advertisement** — it is the shop window for the printed game.
3. **Game testing** — every card's effect is simulated, so rules can be
   proved before anything goes to print.
4. **Catalog** — all 98 playable cards in one browsable place.
5. **Starter deck generator** — build, save, export and import decks.

It is **not** the finished video game. The full release is planned for Godot
(exe + Android, Steam and Google Play), because the browser cannot give you
controller support or a paid download. The bench buys time and gathers
feedback while the physical game is finished.

**No final card art appears here, ever.** That is deliberate — the art sells
the printed product. The bench uses generated placeholder sprites instead.

---

## 2. Files and the one rule that matters

```
index.html          the entire game - one self-contained file
toa_catalog.json    the card data (generated)
toa_catalog.js      same data, as a script (generated)
build_catalog.py    THE SOURCE OF TRUTH for all card data
build_stamps.py     packs the real printed stamps into index.html
build_sprites.py    generates placeholder sprites into index.html
music/calm.mp3      menu + deck builder
music/battle.mp3    every match
```

### The rule: generated content is never hand-edited

`index.html` contains three generated `<script>` blocks:

| id | written by | contains |
|---|---|---|
| `catalog` | `build_catalog.py` | all 98 cards |
| `stamps`  | `build_stamps.py`  | the real printed stamp art, base64 |
| `sprites` | `build_sprites.py` | placeholder unit sprites, base64 |

Each script finds its block by regex and replaces it. **Edit the Python, then
re-run it.** Editing those blocks by hand means the next build silently wipes
your change. Card text, tiers, effects, attack types — all of it lives in
`build_catalog.py`.

Card IDs are stable slugs (`hnr_wooden_catapult`). **Never renumber them** —
saved decks and the sprite folder key off them.

---

## 3. Build and ship

All scripts live in the repo (`D:\GameDevelopment\_TowersOfAtheria\bench`).

```powershell
.\sync_bench.ps1 "commit message"   # copy from Claude's folder, commit, push
.\stage_music.ps1                   # copy + rename the music into music/
.\package_itch.ps1                  # build the itch zip and assert it is valid
.\audio_roundtrip.ps1 out|in        # move audio for ffmpeg processing
```

`package_itch.ps1` does **not** use `Compress-Archive`. On Windows that writes
zip entries with backslashes (`music\calm.mp3`); the ZIP spec requires forward
slashes and itch extracts on Linux, so the music would land as a literal file
named `music\calm.mp3` in the root and 404 with no error anywhere. Entries are
written by hand and the script asserts on it.

Music is **not** inlined. Base64 would add megabytes before first paint. As
separate files the game opens instantly and the music streams behind it.

`.gitattributes` puts `*.mp3` on Git LFS — placeholder tracks get replaced and
each swap would otherwise live in the repo history forever.

---

## 4. Architecture

### Screens
`show(id)` toggles `.screen.on` and drives the music. Screens are `start`,
`builder`, `game`. `SCREEN` holds the current one.

### Game state
One global `G`:
```js
G = { board: 6x5 array, P:{1:{deck,hand,disc,banish,name}, 2:{...}},
      cur, phase, turn, sel, mode, over }
```
Rows 0–2 are P2, rows 3–5 are P1. `NPC_ON` is the AI flag; **the AI is always
player 2**. `unitsOf(p)` walks the board.

### Effects
Every card has an `fx` key. `runActive(card, ctx)` is a big `switch` on it.
Death and combat triggers hook separately. If an `fx` is not handled the card
is marked and nothing is silently faked.

### Choosers — the important pattern
Any time a card says the player picks something, it must **ask**:

| helper | use |
|---|---|
| `pickSquare(prompt, filter, cb)` | choose square(s) on the board |
| `pickFromZones(title, player, zones, filter, cb)` | take ONE card, with zone tabs |
| `pickCards(title, player, zone, n, note, cb, filter)` | choose EXACTLY n cards |

`zrow()` renders every chooser row with art, name, tier, Dweller, attack type,
movable and full Skill text. Picking blind from names is a guess, not a
decision.

**When adding a card that takes cards from a zone, use these.** Do not
`pop()`, `splice(0,1)` or pick at random unless the card text literally says
"random" or "the top card". Check the text first — Elven Outrider really does
say "1 random card", and Bear Cave really does say "the top card".

**The AI must be able to answer every prompt.** `npcResolvePrompts()` handles
`G.pick`, `PICKZ`, `PICKN`, `SOV_STATE` and the Bone Harvester count dialog.
Add new prompt types there or the AI's turn will hang forever. `isNPC(p)`
returns true when p is the AI, used where the *opponent* chooses (Wooden
Catapult) — a prompt aimed at the AI during the human's turn never gets
answered, so the AI decides for itself immediately.

### Audio
Both tracks decode into buffers and loop through the Web Audio graph.

**Do not use `<audio>` elements.** Media elements sit behind a *separate*
autoplay gate from the AudioContext. `toBattle()` is often reached from a
timer during the AI's turn, so there is no user activation and `play()`
rejects with `NotAllowedError`. The AudioContext only needs resuming once, on
the first click. That bug cost a whole round trip; no media elements means it
cannot return.

`makeLoop()` finds the part of a track that is actually at level, discards the
fade-in and fade-out, and equal-power crossfades tail over head. Neither
placeholder track was authored as a loop — calm swells in over six seconds,
battle spends its last twenty fading out. Measured, not hardcoded, so a
swapped-in track gets the same treatment.

Tracks over 60s are downmixed to mono 24 kHz on load (~16 MB instead of ~62 MB
for a 2:41 stereo track). Inaudible at these volumes, and the difference
between comfortable and risky on a phone.

Music follows the **screen**, not the phase: calm on menu and deck builder,
battle for the whole match.

### Layout fitting — read this before touching sizing
Three functions measure at runtime instead of hardcoding: `fitBoard()`,
`fitAudioDock()`, `fitHand()`.

Hard-won rules:

- **`requestAnimationFrame` never fires in a background tab.** A game loaded
  unfocused keeps the fallback size forever. `fitBoard()` is called
  synchronously for this reason.
- **`clientWidth` during `render()` is a lie.** The hand reported 1788px for a
  bar that is really 1100px, because it had not been constrained to its
  max-width yet. Use `getBoundingClientRect()`, which forces the flush.
- **`scrollWidth` right after a CSS-variable change returns a stale value.**
  This produced phantom "overflow" readings on a layout that was fine.
- **The real fix is `ResizeObserver`**, which fires after layout with the true
  box. `fitHand()` uses one. Stop trying to guess when layout has settled.

The hand fans: cards overlap so they all fit, never covering more than 55% of
a card, and the hovered/tapped card lifts clear — which uncovers its buttons,
since later cards paint over earlier ones. Past ~14 cards it hits the cap and
drag-to-scroll takes over.

---

## 5. Traps that have already bitten

- **Name collisions silently break unrelated things.** A helper called `F`
  shadowed the foe player object. A preference saver called `save()` would
  have replaced the deck-saving `save()` and stopped decks persisting, with no
  error. Grep before naming a global.
- **The Desktop Commander PowerShell bridge strips `$`.** Write `.ps1` files
  to disk and run them with `-File`.
- **Chrome is read-only under computer-use.** Screenshots only; drive the
  browser with the Claude-in-Chrome tools instead.
- **The browser zoom-screenshot tool sets a device-metrics override.** If it
  times out mid-call the override is never cleared and the page is left
  believing it is on a ~900px display. A hard reload clears it. It cannot
  happen to a normal player.
- **Mute is remembered.** A muted bench looks exactly like a broken one. Check
  the ♫ button before debugging silence.
- **The build stamp is in the start-screen footer** (`v0.02 · build ...`). If
  a bug report and that string disagree, the build being played is not the
  build that was fixed.

---

## 6. State as of this writing

- 98/98 playable cards designed and simulated, plus 5 tokens.
- Three AI opponents: Wandering Host (no skills), Ashbound Warband (~20%),
  The Crypt Court (everything). All draft random legal decks from the pool.
- Deck builder with multiple saved decks, active deck, export/import.
- Phone portrait and landscape layouts.
- Placeholder sprites: 103 mapped from 33 archetype shapes. Drop a 32×32 PNG
  named `<card id>.png` into `sprites/` and it wins over the placeholder — one
  card at a time, no code change, no layout shift.

### Open
- Screenshots for the itch page.
- Blender monster library (#12) — critical path for the physical product.
- New archetypes, including the lizard men deck.
- GameCrafter product line (#22), rulebook relayout (#23), Poker Folio
  quickstart (#28), printable playmat (#30), branding swap (#33).
- Grand campaign format in the bench, to test movement rules over a longer arc.
- Async multiplayer — deliberately on the back burner.

### The one playtest finding not to lose
**Alfred's +3 aura is safe because the tribute economy eats the Tier 1s he
needs standing next to him.** That came from playing, not from maths.
