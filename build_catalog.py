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

THIS IS THE COLLECTION, NOT A PAIR OF DECKS.
Every unique card that exists in the game lives here, once. Decks are CURATED
out of the collection in the deck builder and saved there - they are lists of
ids, not a property of a card. This follows ToA_Effect_Design_Rules.md section 7:
build the Release, then select the decks from it. A card being in no deck yet
is normal, not an error - that is what booster-only cards are.

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
  status    "final"   = fully designed, safe to balance-test.
            "partial" = tier/rarity/attack known, SKILL still missing.
            "stub"    = NAME ONLY, every stat is a placeholder.
            Anything not "final" renders and plays as a body but must not be
            treated as balanced.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------
# ART NOTES - visual briefs from ASHVSHNR_CardPool (Google Drive).
# Keyed by card name so the card() calls stay readable. These ARE the
# modelling brief for the Blender library, so they live with the data
# rather than in a document that has already been duplicated twice.
# ----------------------------------------------------------------------
DECK_ART_DIRECTION = {
 "ASH": "Boss room outward, the deck plays like descending into a dungeon in "
        "REVERSE - effects weaken and vanilla bodies multiply toward the front "
        "door. Low tiers pull from Dark Souls and Diablo early rosters: classical "
        "bats and rats, headless undead with missing limbs. Grounded, unglamorous.",
 "HNR": "White-gold tower armour from Oblivion is the base reference. A lot of "
        "silver, gold, shine and white across plate, shields and heraldry.",
}

ART_NOTES = {
 "Aegis the Unbroken":"Minotaur boss; plaid/gold/white armour, tower shield, battle mace.",
 "Ironhide Sentinel":"Armoured grizzly bear.",
 "Alexia, the Silver Sword":"Elf; full plate, dark brown ponytail with bangs, green eyes, pale Norse complexion, thin fast two-handed blade.",
 "Alfred the Noble Knight":"Cavalry on a lean painted mare, bright white gold-trim plate, diamond cavalry shield, short silver sword raised.",
 "Garrek, the Steel Wind":"Dual-wielding steel longswords; brown trench coat over leather, light armour over gold-white plate; grizzled mercenary.",
 "Steadfast Warden":"Templar in cloth robes, silver kite shield, flanged mace with gold hilt and blue gem.",
 "Elven Outrider":"Mounted on a reindeer/caribou; silver hair, green hood, leather cloak; scout-tracker.",
 "Valen, the Bear Brawler":"Male elf; twin wooden axes carved from his home forest; bear companion in art only.",
 "Vale Huntress":"Bow plus big-cat companion (jaguar or tiger).",
 "Elvish Sniper":"Golden hair with silver sheen, white cloak with gold or red highlights, crouched fully-drawn stance.",
 "Wooden Catapult":"Basic wooden siege weapon.",
 "Standard Bearer":"Unarmoured, ragged military coat, large white flag with golden cross emblem.",
 "Honored Drummer":"Unarmoured drummer.",
 "Forest Tiger":"Vanilla stat-stick, tribute/evolution fodder.",
 "Great Brown Bear":"Vanilla stat-stick, tribute/evolution fodder.",
 "Bog-Dwelling Stalker":"Black jaguar/panther, tribute/evolution fodder.",
 "Elvish Beast Caller":"Elf with a whip.",
 "Monastery Protector":"Friar bodyguard: brown robes, white and gold trim, tonsure, giant two-handed white mace.",
 "Monastery Scholar":"Black clerical robes, glasses, seated reading a black tome with the Honor sigil on its spine.",
 "Silverlight Dancer":"Ethereal night-fairy: iridescent silhouette, big yellow eyes, green lunar moth wings with white accents, silver hair.",
 "Wolf Pup":"Cute wolf pup - the first wolf in the game.",
 "Makeshift Catapult":"Basic improvised siege weapon.",
 "Makeshift Wall":"Improvised wall/barricade.",
 "Makeshift Ballista":"Improvised siege weapon.",
 "Orion's Blessing":"Herald descending from the god Orion; gold-trimmed robes with red feather accents, ceremonial spear, robes billowing upward mid-descent.",
 "Makeshift Tower":"Banged-together improvised archer tower.",
 "Honored Spearman":"Chainmail and white sigil cloak, Solaire-style bucket great helm, forward stance with spear thrust out.",
 "City Guard":"Cropped Skyrim-style guard helm (jaw visible), torch, chainmail under white sigil cloak, at a city gate.",
 "Honor Archer":"Lighter scout variant of the City Guard look.",
 "Forest Squirrel":"Side profile, munching a nut, red or grey squirrel.",
 "Forest Caiman":"Swamp predator; forest counterpart to Bog-Dwelling Stalker.",
 "Forest Rabbit":"White fur, red eyes, caught mid-scratch with a back foot.",
 "Foraging Foxes":"Two red foxes in underbrush, one nose-down foraging, one nose-up on watch.",
 "Bear Cave":"Simple cave-mouth structure.",
 "Forest Maple":"Simple tree, squirrel peeking from a knot in the trunk.",
 "Charging Buck":"Buck leaping a fallen log, front legs tucked, back legs extended.",
 "Doe":"Timid watchful doe, matching Charging Buck's family.",
 "Shepherd":"Male elf in a wolfskin or deer-hide cloak tending a free-range herd; weathered, practical.",
 "City Guard Dog":"Slightly goofy Great Dane in city-guard-adjacent gear.",
 "Town Crier":"On a soapbox, scroll held out, drab robes, chubby, red-faced with passionate energy.",
 "Flaming Jack Rabbit":"Small fast lava-critter jackrabbit.",
 "Dungeon Door":"Ornate dungeon door/archway, part of the back-of-dungeon wall lineup.",
 "Lavagoyle":"Ferro-imp brute, no wings, white cracked molten-rock skin with lava glowing beneath the cracks. Lava counterpart to Gargoyle.",
}

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
                      movable=movable, skill=skill, fx=fx, status=status,
                      art_note=ART_NOTES.get(name, "")))

def partial(name, set_, tier, dweller, rarity, attack, movable=True):
    """Tier and rarity are decided; the Skill is not."""
    card(name, set_, tier, dweller, rarity, attack, movable,
         "(skill not yet written)", None, status="partial")

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
# Corrected Aug 2026: this said "your opponent's Tower", which had him
# defending the enemy. He is a gatekeeper - he protects the Tower behind him.
card("Ironhide Sentinel", S, 4, "forest", "epic", "melee", True,
     "While this Unit is on the field, your Tower cannot be attacked.",
     "protect_own_tower")
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
# DESIGN INTENT (AJ): lifted from Yu-Gi-Oh's Honest, and the 3-copy deck limit
# is the whole point - it forces the "save a small Unit now, or hold it as a
# trap for something worse later" decision. Deliberately triggers too-good-to-use
# syndrome.
# ONE DIFFERENCE FROM HONEST, worth keeping in mind: Honest is deterministic and
# always wins the fight. A REROLL can land lower than the roll it replaced, so
# this version is a gamble, not a guarantee. It also rewards reading die sizes -
# with a d12 on 4 against a d6 on 5, rerolling YOUR die wins 58% while rerolling
# THEIRS wins 50%, and swapping the die sizes reverses that.
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

ART_NOTES.update({
 "Crypt Caller":"Death Knight riding an Undead Drake. Tattered undead wyvern, all bark and decrepit menace with genuine bite. Reuses the Death Knight and Drake models rather than a new capstone sculpt.",
 "Undead Drake":"Flying Drake, explicitly NOT a true dragon. Tattered wings, looks weak and decrepit but is stronger than it looks. Same asset as Crypt Caller's mount.",
 "Undead Cavalry":"Death Knight riding the Undead Mare. A combination card reusing two existing models, not a new sculpt.",
 "Lich King":"Skyrim's Dragon Lich crossed with the Overlord anime lead.",
 "Death Knight":"Armoured undead knight. Boss-room guard for the Lich King.",
 "Corrupted Paladin":"Working title Dark Knight. NOT undead - a human paladin corrupted by dark arts. Wings/ornament on shoulder pauldrons, not the helm, to keep a grounded melee silhouette.",
 "Skeleton":"Bare-bones skeleton, unarmed, no weapon. Deliberately the weakest undead grunt.",
 "Crypt Bat":"Cave-dwelling dungeon bat. Flying is flavour only, no mechanic.",
 "Cinder Bat":"Charred remains: cracked ashen skin, embers through the gaps, blocky and elemental. Grounded, not floating.",
 "Ash Skink":"Charred remains aesthetic, same language as Cinder Bat. Classic FF earth/fire elemental blockiness.",
 "Ember Wisp":"Small floating ember spirit. Ties to Molten Field's tokens and Ash Golem's payoff.",
 "Immovable Bog":"A swamp/bog - terrain, not a creature. Borders dungeon and forest biomes.",
 "Molten Field":"Field of molten terrain. Lava counterpart to Immovable Bog.",
 "Magma Mine":"A spiked naval mine, but molten, drifting in a sea of lava instead of water.",
 "Shallow Grave":"A cracked headstone with a hand already clawing up through the dirt beside it.",
 "Undead Mare":"Undead horse. The mount Ashen Lancer rides.",
 "Goblin Bomb Carrier":"Small goblin carrying a mine far too heavy for him. Comic-relief fodder.",
 "Flesh Collector":"Lean hunched emaciated zombie golem stitched from corpses, tattered leather, dragging a big battle axe. Necromancer-conscript, not the bulky zombie trope.",
 "Gargoyle":"Stone dungeon muscle. Perched with Dungeon Door guarding the boss-room approach.",
 "Charnel Warden":"Necromancer figure - an enchanted summon built to protect an area.",
 "Ashen Lancer":"Mounted on an Undead Mare, double-headed lance with blue flame, tattered dark purple and black armour.",
 "Ashlands":"Scorched ashen wasteland terrain, not a creature.",
 "Bone Diviner":"Name suggests a bone-reading scryer. Never discussed on record.",
})

# ----------------------------------------------------------------------
# ASHFALL CRYPTS. From the FULL MASTER CARD LIST (Drive, Aug 2026).
#
# Structure philosophy, in AJ's words: the deck plays like descending into
# a dungeon in REVERSE. Boss room outward - Lich King anchored by Death
# Knight, through vanilla Gargoyle muscle propped up by Dungeon Door's
# aura, down through utility Tier 2/3 doing mill and recursion, into
# face-down trap-style Tier 1s as the front-line trigger layer. The closer
# to the front door, the weaker and more numerous the bodies.
#
# Low-tier look: Dark Souls and Diablo early tiers. Bats, rats, headless
# undead with missing limbs. Grounded and unglamorous on purpose.
#
# COUNT: 41 unique, accepted deliberately. Tier 1 holds 21 names, and
# Tier 3 holds 6 names because GARGOYLE PRINTS AS 2 COPIES to fill the
# 7th physical slot. That is a deck quantity, not a second card.
# ----------------------------------------------------------------------

# --- Tier 1 -----------------------------------------------------------
card("Hellhound", S, 1, "lava", "common", "melee", True, "", "vanilla")
card("Dungeon Rat", S, 1, "dungeon", "common", "melee", True, "", "vanilla")
card("Rummaging Rodent", S, 1, "dungeon", "common", "melee", True,
     "On Normal Summon: draw 1 card.", "on_normal_summon_draw1")
card("Crypt Bat", S, 1, "dungeon", "common", "melee", True,
     "Swap places with any Unit you control on the board.", "swap_friendly")
card("Flaming Jack Rabbit", S, 1, "lava", "common", "melee", True,
     "If this card would be discarded or destroyed, shuffle it into your deck "
     "instead of sending it to the Discard pile.", "recycle_self")
card("Cinder Bat", S, 1, "lava", "common", "melee", True,
     "On Death: adjacent Lava Dwellers add +1 to their next roll this turn; "
     "adjacent non-Lava Dwellers subtract 1 from their next roll this turn.",
     "death_lava_swing")
card("Disembodied Hand", S, 1, "dungeon", "common", "melee", True,
     "Roll this Unit's die. On a 1, 3 or 5, look at the top card of your "
     "opponent's deck and return it to the top.", "peek_top")
card("Skeleton", S, 1, "dungeon", "common", "melee", True, "", "vanilla")
card("Skeletal Archer", S, 1, "dungeon", "common", "ranged", True, "", "vanilla")
card("Graveyard Wraith", S, 1, "dungeon", "common", "melee", True,
     "Dungeon Dwellers in the 8 adjacent squares add +1 to their rolls.",
     "aura_plus1_dungeon")
card("Ash Skink", S, 1, "lava", "common", "melee", True,
     "On Normal Summon: draw 1 card.", "on_normal_summon_draw1")
card("Undead Hound", S, 1, "dungeon", "common", "melee", True,
     "When destroyed: search your deck for a Tier 1 or Tier 2 Dungeon Dweller "
     "and add it to your hand.", "death_search_dungeon")
card("Ember Wisp", S, 1, "lava", "common", "ranged", True,
     "When destroyed: search your deck for a Tier 1 or Tier 2 Lava Dweller "
     "and add it to your hand.", "death_search_lava")
card("Grave Snare", S, 1, "dungeon", "common", "melee", True,
     "When this Unit is attacked while face down: after the battle resolves, "
     "the attacking Unit subtracts 2 from its next roll this turn.",
     "trap_debuff2")
card("Immolation Trap", S, 1, "lava", "common", "melee", True,
     "When this Unit is attacked while face down: after the battle resolves, "
     "destroy both this Unit and the attacking Unit.",
     "trap_mutual_destruct")
card("Grave Shifter", S, 1, "dungeon", "uncommon", "melee", True,
     "Swap places with any Unit on the board, yours or your opponent's.",
     "swap_any")
card("Immovable Bog", S, 1, "dungeon", "common", "melee", False,
     "Dungeon and Forest Dwellers in the 8 adjacent squares add +1 to their "
     "rolls. All other Dweller Types in those squares subtract 3.",
     "aura_bog")
card("Molten Field", S, 1, "lava", "common", "melee", False,
     "Lava Dwellers in the 8 adjacent squares add +1 to their rolls. At the "
     "start of your Recruitment Phase, Special Summon 1 Wisp Token to your Barracks.",
     "aura_lava_and_wisp")
card("Cinder Skeleton", S, 1, "lava", "common", "ranged", True,
     "During your Recruitment Phase: you may attach this card from your hand to "
     "an adjacent Lava Dweller you control as a Ride. This does not use your "
     "Normal Summon.", "ride_from_hand_lava")
# Twin of Magma Mine: same roll, same tier mapping, debuff instead of destroy.
# Hits EVERY Unit of that Tier, so it is broader and weaker per Unit.
card("Bone Diviner", S, 1, "dungeon", "uncommon", "ranged", True,
     "Discard this card from your hand, then roll a d6. On 1 to 4, every Unit your "
     "opponent controls of the corresponding Tier subtracts 2 from its rolls until "
     "the end of their next turn. On 5 or 6, nothing happens.", "bone_diviner")
card("Magma Mine", S, 1, "lava", "uncommon", "ranged", True,
     "Discard this card from your hand, then roll a d6. On 1 to 4, destroy 1 Unit "
     "your opponent controls of the corresponding Tier. On 5 or 6, nothing happens.",
     "magma_mine")

# --- Tier 2 -----------------------------------------------------------
card("Armored Skeleton", S, 2, "dungeon", "common", "melee", True, "", "vanilla")
card("Skeleton Archer", S, 2, "dungeon", "common", "ranged", True, "", "vanilla")
# Doc flag 3: wording never confirmed. Written to the deck's stated identity -
# "utility Tier 2s and 3s doing mill, discard-to-activate, hand disruption".
card("Skeletal Mage", S, 2, "dungeon", "common", "ranged", True,
     "Once per turn: roll this Unit's die. On a 7 or 8, mill the top 2 cards of "
     "your opponent's deck.", "mage_mill")
card("Shallow Grave", S, 2, "dungeon", "common", "melee", False,
     "Mandatory. Every Recruitment Phase: Special Summon 1 Zombie Token to your "
     "Barracks. This is not optional.", "spawn_zombie_mandatory")
card("Fire Imp", S, 2, "lava", "common", "ranged", True, "", "vanilla")
card("Undead Mare", S, 2, "dungeon", "common", "melee", True,
     "If a Tier 1 Unit Rides this card, the stack adds +2 to its roll in battle.",
     "ridden_by_t1_plus2")
card("Ghoul Rider", S, 2, "dungeon", "common", "melee", True,
     "Sacrifice a Ride stack you control: Special Summon a Unit one Tier higher "
     "than the stack's highest Tier from your hand.", "ascend_hand")
card("Slagborn", S, 2, "lava", "common", "melee", True,
     "Sacrifice a Ride stack you control: Special Summon a Unit one Tier higher "
     "than the stack's highest Tier from your hand.", "ascend_hand")
card("Goblin Bomb Carrier", S, 2, "lava", "uncommon", "melee", True,
     "When this Unit is destroyed by an opponent's card: add 1 Magma Mine from "
     "your deck to your hand.", "death_fetch_mine")
card("Flesh Collector", S, 2, "dungeon", "epic", "melee", True,
     "Cleave - when this Unit wins a combat roll, also destroy 1 enemy Unit "
     "orthogonally adjacent to the Unit it defeated.",
     "cleave")

# --- Tier 3 (6 names; Gargoyle prints x2 for the 7th slot) -------------
card("Gargoyle", S, 3, "dungeon", "uncommon", "melee", True, "", "vanilla")
# Tier 2 confirmed by AJ, which also resolves the old d8 conflict: Tier 2 IS
# d8, so the source doc was right about the die and the placeholder Tier was
# wrong. No Taunt by design - the Units around it are meant to be protecting
# IT, rather than it forcing itself to be attacked first.
card("Dungeon Door", S, 2, "dungeon", "uncommon", "melee", False,
     "This Unit and adjacent Units you control add +1 to their rolls, "
     "regardless of Dweller Type.", "aura_plus1_any_incl_self")

card("Charnel Warden", S, 3, "dungeon", "uncommon", "ranged", True,
     "Once per turn during your Recruitment Phase: banish 1 card from your Discard "
     "pile to Special Summon 1 Zombie Token.", "banish_for_zombie")
card("Ashen Lancer", S, 3, "dungeon", "rare", "melee", True,
     "When this Unit moves during the Battle Phase, every Unit you control adjacent "
     "to it moves the same number of squares in the same direction. This does not "
     "use those Units' own movement.", "formation_move")
card("Ash Golem", S, 3, "lava", "rare", "melee", True,
     "This Unit adds +1 to its roll for each Wisp Token adjacent to it.",
     "wisp_scaling")
card("Ashlands", S, 3, "lava", "rare", "melee", False,
     "Dungeon and Lava Dwellers in the 8 adjacent squares add +2 to their rolls. "
     "No penalty to anything else.", "aura_plus2_dungeon_lava")
card("Lavagoyle", S, 3, "lava", "common", "melee", True, "", "vanilla")

# --- Tier 4 -----------------------------------------------------------
# NOTE: the Drive doc lists Lich King as MELEE with unconfirmed text. In
# conversation AJ chose RANGED and settled the skill below. Conversation
# wins, but this is a live discrepancy - see open flags.
card("Lich King", S, 4, "dungeon", "legendary", "ranged", True,
     "Once per turn during your Recruitment Phase: Special Summon 1 Tier 1 "
     "Dungeon Dweller from your Discard pile to an empty Barracks square.",
     "raise_t1_from_discard")
card("Death Knight", S, 4, "dungeon", "rare", "melee", True, "", "vanilla")
card("Corrupted Paladin", S, 4, "dungeon", "epic", "melee", True,
     "Once per turn: roll this Unit's die. On an even result, destroy 1 Unit your "
     "opponent controls. On an odd result, banish 1 Unit from your opponent's "
     "Discard pile.", "paladin_even_odd")

# --- Tokens -----------------------------------------------------------
card("Zombie Token", S, 1, "dungeon", "token", "melee", True,
     "Token. Not part of your deck. Cannot be Set face-down. Cannot be Tributed.",
     "token")
card("Wisp Token", S, 1, "lava", "token", "ranged", True,
     "Token. Not part of your deck. Cannot be Set face-down. Cannot be Tributed.",
     "token")
card("Skeleton Knight Token", S, 2, "dungeon", "token", "melee", True,
     "Token. Not part of your deck. Cannot be Set face-down. Cannot be Tributed.",
     "token")

# ----------------------------------------------------------------------
# BOOSTER-ONLY EXTRAS (17). AJ: "we won't refine those extra cards just
# yet, bank the idea for later." Missing stats here are an intentional
# design decision, not lost data.
# ----------------------------------------------------------------------
card("Charnel Reaper", S, 3, "dungeon", "rare", "ranged", True,
     "Banish 2 cards from your Discard pile: Special Summon 2 Tokens adjacent to "
     "this Unit.", "charnel_reaper")
card("Bone Harvester", S, 3, "dungeon", "epic", "melee", True,
     "Discard up to 3 cards from your hand: Special Summon that many Tokens.",
     "bone_harvester")
card("Charnel Sovereign", S, 4, "dungeon", "legendary", "melee", True,
     "Special Summon up to 4 Skeleton Knight Tokens. Pay the cost in any "
     "combination of banishing Dungeon Dwellers from your Discard pile, "
     "discarding from your hand, or milling from your deck.", "charnel_sovereign")

# ---- SEARCH FAMILY -----------------------------------------------------
# The TRIGGER moves earlier as rarity climbs - dying, then being summoned,
# then sitting in the Discard pile, then just being in hand - and the search
# RANGE widens. Every member is Tier 1; only access scales.
#   common    (Undead Hound / Ember Wisp, in the main deck) - on death, T1-T2
#   uncommon  - on Normal Summon, T1-T3
#   epic      - banish from Discard pile, T1-T4
#   legendary - discard from hand, T1-T4
card("Grave Tracker", S, 1, "dungeon", "uncommon", "ranged", True,
     "On Normal Summon: search your deck for 1 Tier 1 to Tier 3 Dungeon Dweller "
     "and add it to your hand.", "search_summon_dungeon")
card("Cinder Stalker", S, 1, "lava", "uncommon", "melee", True,
     "On Normal Summon: search your deck for 1 Tier 1 to Tier 3 Lava Dweller "
     "and add it to your hand.", "search_summon_lava")
card("Sepulcher Hunter", S, 1, "dungeon", "epic", "melee", True,
     "While this card is in your Discard pile you may banish it: search your deck "
     "for 1 Tier 1 to Tier 4 Dungeon Dweller and add it to your hand.",
     "search_banish_dungeon")
card("Magma Seeker", S, 1, "lava", "epic", "ranged", True,
     "While this card is in your Discard pile you may banish it: search your deck "
     "for 1 Tier 1 to Tier 4 Lava Dweller and add it to your hand.",
     "search_banish_lava")
card("Ossuary Warden", S, 1, "dungeon", "legendary", "melee", True,
     "Discard this card from your hand: search your deck for 1 Tier 1 to Tier 4 "
     "Dungeon Dweller and add it to your hand.", "search_discard_dungeon")
card("Pyre Warden", S, 1, "lava", "legendary", "ranged", True,
     "Discard this card from your hand: search your deck for 1 Tier 1 to Tier 4 "
     "Lava Dweller and add it to your hand.", "search_discard_lava")

# ---- ASCENSION FAMILY --------------------------------------------------
# Base effect is fixed; what scales with rarity is WHERE the summoned Unit
# comes from. Names deliberately share no suffix, so the family does not
# telegraph its own synergy.
#   common    (Ghoul Rider / Slagborn) - from hand
#   uncommon  - from hand or deck
#   epic      - from Discard pile or deck
#   legendary - Crypt Caller, straight from the Discard pile, no Tier limit
# OPEN FLAG 6: Tower of Bones and Pyre never had an attack type locked. Set
# ranged here to match their siblings and because a tower reads as ranged
# under AJ's rule, but this is unconfirmed.
card("Bonecarver", S, 2, "dungeon", "uncommon", "ranged", True,
     "Sacrifice a Ride stack you control: Special Summon a Unit one Tier higher "
     "than the stack's highest Tier from your hand or deck.", "ascend_hand_deck")
card("Emberwright", S, 2, "lava", "uncommon", "ranged", True,
     "Sacrifice a Ride stack you control: Special Summon a Unit one Tier higher "
     "than the stack's highest Tier from your hand or deck.", "ascend_hand_deck")
card("Tower of Bones", S, 3, "dungeon", "epic", "ranged", False,
     "Sacrifice a Ride stack you control: Special Summon a Unit one Tier higher "
     "than the stack's highest Tier from your Discard pile or deck.",
     "ascend_discard_deck")
card("Pyre", S, 3, "lava", "epic", "ranged", False,
     "Sacrifice a Ride stack you control: Special Summon a Unit one Tier higher "
     "than the stack's highest Tier from your Discard pile or deck.",
     "ascend_discard_deck")
card("Crypt Caller", S, 3, "dungeon", "legendary", "melee", True,
     "Sacrifice a Ride stack you control: Special Summon 1 Dungeon Dweller from "
     "your Discard pile to that stack's square. No Tier restriction.",
     "ascend_crypt_caller")

card("Magma Minefield", S, 3, "lava", "rare", "melee", False,
     "Once per turn: add 1 Magma Mine from your deck or Discard pile to your hand.",
     "fetch_magma_mine")

# Both signed off by AJ Aug 2026 - skills his, stats confirmed as printed.
# The Drake is the reason Riding is worth the risk: a Ride stack normally
# costs you BOTH cards when it dies, and he turns that into a one-card loss.
card("Undead Drake", S, 3, "dungeon", "rare", "melee", True,
     "Once per turn: if this Unit is part of a Ride stack, send this card to "
     "the Discard pile instead of destroying the stack.",
     "drake_saves_stack")
card("Undead Cavalry", S, 2, "dungeon", "rare", "melee", True,
     "Discard 2 cards: Special Summon this Unit from your hand or your "
     "Discard pile.",
     "cavalry_self_summon")

# ======================================================================
# emit
# ======================================================================
def main():
    ids = [c["id"] for c in CARDS]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"  !! DUPLICATE IDS: {dupes}", file=sys.stderr)

    playable = [c for c in CARDS if c["rarity"] != "token"]
    print(f"  COLLECTION: {len(CARDS)} cards ({len(playable)} playable + "
          f"{len(CARDS)-len(playable)} tokens)")
    print()
    for s_ in ("ASH", "HNR"):
        grp = [c for c in playable if c["set"] == s_]
        t = {n: sum(1 for c in grp if c["tier"] == n) for n in (1, 2, 3, 4)}
        print(f"  {s_}  T1={t[1]:2} T2={t[2]:2} T3={t[3]:2} T4={t[4]:2}   {len(grp)} cards")
        for st in ("final", "partial", "stub"):
            n = sum(1 for c in grp if c["status"] == st)
            if n:
                print(f"        {st:<8} {n}")
    print()
    art = sum(1 for c in playable if c["art_note"])
    print(f"  {art}/{len(playable)} have an art note (modelling brief)")
    ready = sum(1 for c in playable if c["status"] == "final")
    print(f"  {ready}/{len(playable)} playable cards are fully designed")

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

    # Inject straight into index.html so the game is ONE self-contained file.
    # A sibling <script src> works on itch (served over HTTP) but is blocked by
    # some browsers when index.html is opened directly from disk. Inlining works
    # in both places, and keeps this script the single source of truth.
    idx = os.path.join(HERE, "index.html")
    if os.path.exists(idx):
        html = open(idx, encoding="utf-8").read()
        import re as _re
        payload = ("<script id=\"catalog\">/* GENERATED by build_catalog.py - do not edit */\n"
                   "window.TOA_CATALOG=" + json.dumps(CARDS, separators=(",", ":")) + ";\n</script>")
        new, n = _re.subn(r'<script id="catalog">.*?</script>', payload, html, flags=_re.S)
        if n:
            open(idx, "w", encoding="utf-8").write(new)
            print(f"  injected catalog into index.html ({len(payload)//1024} KB inline)")
        else:
            print("  !! index.html has no <script id=\"catalog\"> marker", file=sys.stderr)

    print(f"\n  toa_catalog.json / toa_catalog.js  ({len(CARDS)} cards total)")

if __name__ == "__main__":
    main()
