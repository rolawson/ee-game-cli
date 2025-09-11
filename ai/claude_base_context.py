"""Shared game context for all Claude AI personas"""

def get_base_game_context():
    """Returns the fundamental game rules and context that all Claude AIs need"""
    return """
ELEMENTAL ELEPHANTS - COMPLETE RULES:

PRIORITY SYSTEM: Lower numbers resolve FIRST! P1 > P2 > P3 > P4 > P5 > PA
- P1 spells resolve before everything (very powerful, fast)
- P2-P3 are fast to moderate speed  
- P4-P5 are slower, often defensive or setup spells
- PA (Advance) spells resolve last, then move to next clash
- Same priority? Turn order from Ringleader breaks ties

GAME FLOW:
1. Round = 4 clashes
2. Each clash: Prepare → Cast (reveal) → Resolve → Advance
3. Players simultaneously reveal spells
4. Spells resolve in priority order
5. Some spells advance to next clash
6. After round: keep/discard cards, recall from discard

SPELL TYPES:
- ATTACK: Deals damage, often has bonus effects
- RESPONSE: Conditional effects (if enemy has X, do Y)
- REMEDY: Heals or bolsters (increases max health)
- BOOST: Ongoing effects or advances other spells
- CONJURY: Powerful spells that can be targeted by damage/weaken to cancel (marked with ⚠️)

CORE EFFECTS:
- Damage: Reduces health (can't go below 0)
- Heal: Restores health (can't exceed max)
- Weaken: Reduces MAX health permanently
- Bolster: Increases MAX health permanently
- Cancel: Removes spell before it resolves
- Discard: Forces cards from hand to discard
- Recall: Brings cards from discard to hand
- Advance: Moves spell to next clash

TRUNKS & WINNING:
- Start with 3 trunks each
- Health drops to 0 → lose a trunk, become invulnerable for round
- Invulnerable players can't play spells
- Lose all trunks = lose game
- Trunk loss changes max health:
  - Max ≤3 → becomes 4
  - Max ≥7 → becomes 6
  - Otherwise unchanged

ADVANCED INTERACTIONS:
- Multiple damage sources hit simultaneously
- Conjuries: 1 damage or any weaken cancels them (makes them vulnerable)
- Some spells protect others from enemy effects
- Spells can have passive effects while active
- "This clash" = current clash only
- "Other" spells = excludes the spell itself
- Past spells = from previous clashes
- Cancelled spells don't resolve their effects

STRATEGY NOTES:
- Turn 1 advantage: Ringleader plays first each clash
- Hand management: Balance immediate needs vs future rounds
- Element tracking: Remember what opponents drafted
- Priority manipulation: Some spells change resolution order
- Clash positioning: Where you play matters for advance effects

IMPORTANT: When analyzing rounds, remember which spells are YOURS vs your OPPONENT'S. Don't complain about your own successful plays!
"""

def get_priority_notes():
    """Returns priority explanations for card displays"""
    return {
        '1': '(FASTEST!)',
        '2': '(very fast)',
        '3': '(moderate)',
        '4': '(slow)',
        '5': '(very slow)',
        'A': '(slowest, but advances)'
    }

def get_spell_type_emojis():
    """Returns spell type emojis for consistent display"""
    return {
        'conjury': '⚠️',
        'attack': '🪓',
        'response': '🛡️',
        'remedy': '⛑️',
        'boost': '➡️'
    }

def get_element_emojis():
    """Returns element emojis for consistent display"""
    return {
        'Fire': '🔥', 'Water': '💧', 'Wind': '🌪️', 'Earth': '🗿',
        'Wood': '🌳', 'Metal': '⚔️', 'Time': '⌛', 'Space': '🪐',
        'Sunbeam': '☀️', 'Moonshine': '🌙', 'Shadow': '🌑', 'Aster': '🌟',
        'Blood': '🩸', 'Ichor': '🪽', 'Venom': '☠️', 'Nectar': '🍯',
        'Lightning': '⚡️', 'Thunder': '🫨', 'Twilight': '☯️'
    }