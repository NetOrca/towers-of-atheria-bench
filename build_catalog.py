#!/usr/bin/env python3
"""
Towers of Atheria - MASTER CATALOG generator.

ONE source of truth. Everything downstream is generated, so nothing can drift:

    build_catalog.py  ->  toa_catalog.json   (canonical data)
                      ->  toa_catalog.js     (for the browser bench)
                      ->  cards_ASH.csv      (for toa_cards.py / toa_upload.py)
                      ->  cards_HNR.csv

Same discipline as build_rulebook.py, and for the same reason: the day the
bench and the print files disagree about a card is the day playtest results
stop meaning anything.

FIELDS
  id        stable slug. NEVER renumber - the uploader and saved decks key off it.
  name      printed card name
  set       ASH | HNR
  tier      1-4
  dweller   dungeon | lava | honor | forest
  rarity    common | uncommon | rare | epic | legendary
  attack    melee | ranged   -- there is NO "none". AJ's rule: every Unit can
            attack or retaliate. Walls, buildings and caves are melee; siege
            weapons and archer towers are ranged. The card template therefore
            never needs a third attack stamp.
  movable   True/False
  skill     printed rules text, verbatim
  fx        machine key for the engine. None = not yet implemented.
            "vanilla" = deliberately no effect.
  status    "final" = fully designed. "stub" = NAME ONLY, stats are placeholders
            awaiting AJ. Stubs render and play as bodies but must not be treated
            as balanced.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- helpers
CARDS = []

def card(name, set_, tier, dweller, rarity, attack, movable, skill, fx, status="final"):
    assert attack in ("melee", "ranged"), (
        f"{name}: attack must be melee or ranged. Every Unit fights back - "
        "walls and caves are melee, siege and towers are ranged.")
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    CARDS.append(dict(id=f"{set_.lower()}_{slug}", name=name, set=set_, tier=tier,
                      dweller=dweller, rarity=rarity, attack=attack,
                      movable=movable, skill=skill, fx=fx, status=status))

def stub(name, set_, tier, dweller):
    """A card whose NAME is decided and whose stats are not.
    Placeholder values are deliberately boring: common, melee, movable, vanilla."""
    card(name, set_, tier, dweller, "common", "melee", True,
         "(stats not yet assigned)", None, status="stub")

# ======================================================================
# HONOR GUARD - code HNR - fully designed, 20/10/7/3
# ======================================================================
S = "HNR"

# --- Tier 4, the boss room -------------------------------------------
card("Aegis the Unbroken", S, 4, "honor", "legendary", "melee", True,
     "On Summon by any method: you may banish 5 cards from your hand to return "
     "all Units in your Discard pile to your deck. All or nothing.",
     "aegis_mass_recur")
card("Ironhide Sentinel", S, 4, "forest", "epic", "melee", True,
     "While this Unit is on the field, your opponent's Tower cannot be attacked.",
     "tower_lock")
card("Alexia, the Silver Sword", S, 4, "honor", "epic", "melee", True,
     "Multistrike - if this Unit wins a combat roll it may attack a second time "
     "this Battle Phase. Optional. Maximum 2 attacks per phase.",
     "multistrike")

# --- Tier 3 -----------------------------------------------------------
card("Alfred the Noble Knight", S, 3, "honor", "rare", "melee", True,
     "Adjacent Tier 1 and Tier 2 Units you control add +3 to their rolls. "
     "Does not buff this Unit.",
     "aura_plus3_low_tier")
card("Garrek, the Steel Wind", S, 3, "honor", "epic", "melee", True,
     "When this Unit rolls in combat, an even result destroys the enemy Unit "
     "outright regardless of its roll.",
     "even_kill")
card("Steadfast Warden", S, 3, "honor", "rare", "melee", True,
     "Once per turn: return 1 Honor Dweller Unit from your Discard pile to your deck.",
     "recur_honor_to_deck")
card("Elven Outrider", S, 3, "forest", "rare", "ranged", True,
     "When this Unit destroys an enemy Unit in combat and its roll was even, "
     "your opponent discards 1 random card from their hand.",
     "even_discard")
card("Valen, the Bear Brawler", S, 3, "forest", "epic", "melee", True,
     "Units adjacent to this Unit cannot be selected as an attack target.",
     "adjacent_untargetable")
card("Vale Huntress", S, 3, "forest", "common", "ranged", True,
     "", "vanilla")
card("Elvish Sniper", S, 3, "forest", "rare", "ranged", False,
     "Once per turn: roll this Unit's die. On an odd result, destroy 1 face-up "
     "enemy Unit regardless of its roll.",
     "odd_snipe")

# --- Tier 2 -----------------------------------------------------------
card("Wooden Catapult", S, 2, "honor", "common", "ranged", False,
     "Once per turn: roll this Unit's die. On 1 to 4, your opponent chooses 1 Unit "
     "they control and sends it to the Discard pile.",
     "catapult_d8_edict")
card("Standard Bearer", S, 2, "honor", "uncommon", "melee", True,
     "Adjacent Honor Dwellers you control add +2 to their rolls.",
     "aura_plus2_honor")
card("Honored Drummer", S, 2, "honor", "common", "melee", True,
     "Adjacent Units that are not Honor Dwellers subtract 1 from their rolls.",
     "aura_minus1_non_honor")
card("Forest Tiger", S, 2, "forest", "common", "melee", True, "", "vanilla")
card("Great Brown Bear", S, 2, "forest", "common", "melee", True, "", "vanilla")
card("Bog-Dwelling Stalker", S, 2, "forest", "common", "melee", True, "", "vanilla")
card("Elvish Beast Caller", S, 2, "forest", "rare", "melee", True,
     "On Summon by any method: search your deck for 1 Tier 1 or Tier 2 Forest "
     "Dweller and add it to your hand, then shuffle.",
     "search_forest_low")
card("Monastery Protector", S, 2, "honor", "common", "melee", True,
     "When this Unit destroys an enemy Unit in combat: return 1 card of your "
     "choice from your Discard pile to your deck.",
     "on_kill_recur_choice")
card("Monastery Scholar", S, 2, "honor", "uncommon", "ranged", True,
     "During your Recruitment Phase: add 1 card from your Discard pile to your "
     "deck, then shuffle.",
     "recruit_recur_any")
card("Silverlight Dancer", S, 2, "honor", "rare", "ranged", True,
     "During your Recruitment Phase: return 1 banished Unit to your hand.",
     "unbanish_to_hand")

# --- Tier 1 -----------------------------------------------------------
card("Wolf Pup", S, 1, "forest", "common", "melee", True, "", "vanilla")
card("Makeshift Catapult", S, 1, "honor", "common", "ranged", False,
     "Once per turn: if your opponent draws a card outside their Draw Phase, "
     "they must immediately discard that card.",
     "punish_extra_draw")
card("Makeshift Wall", S, 1, "honor", "common", "melee", False,
     "If a Unit you control adjacent to this Unit would be destroyed, "
     "destroy this Unit instead.",
     "redirect_destruction")
card("Makeshift Ballista", S, 1, "honor", "common", "ranged", False,
     "Once per turn: roll this Unit's die. Even - mill the top card of your "
     "opponent's deck. Odd - destroy this Unit.",
     "ballista_gamble")
card("Orion's Blessing", S, 1, "honor", "common", "ranged", True,
     "Discard this card from your hand: force a reroll of any one dice roll.",
     "hand_reroll")
card("Makeshift Tower", S, 1, "honor", "common", "ranged", False, "", "vanilla")
card("Honored Spearman", S, 1, "honor", "common", "melee", True, "", "vanilla")
card("City Guard", S, 1, "honor", "common", "melee", True, "", "vanilla")
card("Honor Archer", S, 1, "honor", "common", "ranged", True, "", "vanilla")
card("Forest Squirrel", S, 1, "forest", "common", "melee", True, "", "vanilla")
card("Forest Caiman", S, 1, "forest", "common", "melee", True, "", "vanilla")
card("Forest Rabbit", S, 1, "forest", "common", "melee", True, "", "vanilla")
card("Foraging Foxes", S, 1, "forest", "common", "melee", True,
     "On Summon: draw 1 card.", "on_summon_draw1")
card("Bear Cave", S, 1, "forest", "uncommon", "melee", False,
     "Once per turn during your Recruitment Phase: discard the top card of your "
     "deck to Special Summon 1 Bear Token to the square in front of this Unit.",
     "spawn_bear_token")
card("Forest Maple", S, 1, "forest", "common", "melee", False,
     "Once per turn during your Recruitment Phase: shuffle 1 card from your hand "
     "into your deck to Special Summon 1 Squirrel Token.",
     "spawn_squirrel_token")
card("Charging Buck", S, 1, "forest", "common", "melee", True,
     "While this Unit is ridden by an Honor Dweller, it adds +2 to its roll.",
     "ridden_by_honor_plus2")
card("Doe", S, 1, "forest", "common", "melee", True,
     "Once per turn: shuffle 2 cards from your hand into your deck, then draw 2 cards.",
     "cycle_two")
card("Shepherd", S, 1, "forest", "common", "melee", True,
     "When this Unit is destroyed in battle: search your Discard pile for a Tier 1 "
     "or Tier 2 Forest Dweller and add it to your hand.",
     "on_death_recur_forest")
card("City Guard Dog", S, 1, "honor", "common", "melee", True,
     "1 adjacent Unit you control adds +1 to its roll.",
     "aura_plus1_single")
card("Town Crier", S, 1, "honor", "common", "ranged", True,
     "On Summon: if you have no cards in your hand, draw 5 cards.",
     "empty_hand_draw5")

# --- Tokens (not part of any deck) ------------------------------------
card("Bear Token", S, 2, "forest", "token", "melee", True,
     "Token. Not part of your deck. Cannot be Set face-down. Cannot be Tributed. "
     "Destroyed permanently when it leaves the field.", "token")
card("Squirrel Token", S, 1, "forest", "token", "melee", True,
     "Token. Not part of your deck. Cannot be Set face-down. Cannot be Tributed. "
     "Destroyed permanently when it leaves the field.", "token")

# ======================================================================
# ASHFALL CRYPTS - code ASH
# Only 3 of these were specced. The other 38 are NAME ONLY - AJ supplies
# tier/dweller/attack/movement/rarity/skill. They are stubs until then.
# NOTE: AJ's list has 21 Tier 1 entries against a 20 target. Flagged below.
# ======================================================================
S = "ASH"

card("Flaming Jack Rabbit", S, 1, "lava", "common", "melee", True,
     "If this card would be discarded or destroyed, shuffle it into your deck instead.",
     "recycle_self")
card("Dungeon Door", S, 3, "dungeon", "common", "melee", False,
     "This Unit and adjacent Units you control add +1 to their rolls. "
     "Any Dweller Type.",
     "aura_plus1_any_incl_self")
card("Lavagoyle", S, 3, "lava", "common", "melee", True, "", "vanilla")

_ASH_STUBS = [
    # (name, tier, dweller-guess-from-name)
    ("Hellhound",1,"lava"), ("Dungeon Rat",1,"dungeon"), ("Rummaging Rodent",1,"dungeon"),
    ("Crypt Bat",1,"dungeon"), ("Cinder Bat",1,"lava"), ("Disembodied Hand",1,"dungeon"),
    ("Skeleton",1,"dungeon"), ("Skeletal Archer",1,"dungeon"), ("Graveyard Wraith",1,"dungeon"),
    ("Ash Skink",1,"lava"), ("Undead Hound",1,"dungeon"), ("Ember Wisp",1,"lava"),
    ("Grave Snare",1,"dungeon"), ("Immolation Trap",1,"lava"), ("Grave Shifter",1,"dungeon"),
    ("Immovable Bog",1,"dungeon"), ("Molten Field",1,"lava"), ("Cinder Skeleton",1,"lava"),
    ("Bone Diviner",1,"dungeon"), ("Magma Mine",1,"lava"),
    ("Armored Skeleton",2,"dungeon"), ("Skeleton Archer",2,"dungeon"), ("Skeletal Mage",2,"dungeon"),
    ("Shallow Grave",2,"dungeon"), ("Fire Imp",2,"lava"), ("Undead Mare",2,"dungeon"),
    ("Ghoul Rider",2,"dungeon"), ("Slagborn",2,"lava"), ("Goblin Bomb Carrier",2,"lava"),
    ("Flesh Collector",2,"dungeon"),
    ("Gargoyle",3,"dungeon"), ("Charnel Warden",3,"dungeon"), ("Ashen Lancer",3,"lava"),
    ("Ash Golem",3,"lava"), ("Ashlands",3,"lava"),
    ("Lich King",4,"dungeon"), ("Death Knight",4,"dungeon"), ("Corrupted Paladin",4,"dungeon"),
]
for n, t, d in _ASH_STUBS:
    stub(n, S, t, d)

# ======================================================================
# emit
# ======================================================================
def main():
    ids = [c["id"] for c in CARDS]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"  !! DUPLICATE IDS: {dupes}", file=sys.stderr)

    playable = [c for c in CARDS if c["rarity"] != "token"]
    for s in ("HNR", "ASH"):
        deck = [c for c in playable if c["set"] == s]
        counts = {t: sum(1 for c in deck if c["tier"] == t) for t in (1, 2, 3, 4)}
        total = len(deck)
        flag = "" if (counts[1], counts[2], counts[3], counts[4]) == (20, 10, 7, 3) \
               else "   <-- OFF TARGET 20/10/7/3"
        print(f"  {s}: T1={counts[1]:2} T2={counts[2]:2} T3={counts[3]} T4={counts[4]}  "
              f"total={total}{flag}")
        st = sum(1 for c in deck if c["status"] == "stub")
        if st:
            print(f"       {st} of {total} are STUBS awaiting stats")

    with open(os.path.join(HERE, "toa_catalog.json"), "w", encoding="utf-8") as f:
        json.dump(CARDS, f, indent=1)

    # Browser build: a plain global, so the bench works from file:// with no fetch.
    with open(os.path.join(HERE, "toa_catalog.js"), "w", encoding="utf-8") as f:
        f.write("/* GENERATED by build_catalog.py - do not edit by hand */\n")
        f.write("window.TOA_CATALOG=" + json.dumps(CARDS, separators=(",", ":")) + ";\n")

    # CSVs for toa_cards.py / toa_upload.py
    for s in ("ASH", "HNR"):
        rows = [c for c in CARDS if c["set"] == s]
        p = os.path.join(HERE, f"cards_{s}.csv")
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name","tier","type","attack","movable","rarity","skill",
                        "art","quantity","card_no","set_code","release_code","fx","status"])
            for i, c in enumerate(rows, 1):
                w.writerow([c["name"], c["tier"], c["dweller"],
                            c["attack"],
                            "yes" if c["movable"] else "no",
                            c["rarity"] if c["rarity"] != "token" else "common",
                            c["skill"].replace("\n", "\\n"), "", 1, i, s, s,
                            c["fx"] or "", c["status"]])
        print(f"  wrote {os.path.basename(p)}  ({len(rows)} rows)")

    print(f"\n  toa_catalog.json / toa_catalog.js  ({len(CARDS)} cards total)")

if __name__ == "__main__":
    main()
