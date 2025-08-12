# Elemental Elephants

A strategic card game where magical elephants battle using elemental spells.

## Overview

Elemental Elephants is a turn-based strategy game featuring elephants who wield the powers of Fire, Water, Wind, and Earth. Players duel by playing spell cards in strategic combinations to damage opponents while protecting themselves.

## Game Features

- **Several Elemental Elephants**: Each with unique spell types

- **Strategic Combat**: Spells have different priorities, types, and effects
- **Conjury System**: Powerful spells that are also susceptible to attack
- **Response & Boost Mechanics**: Chain spells together for powerful combos

## How to Play

```bash
python elephants_prototype.py
```

## Game Rules

- Each player starts with 5 health and 3 trunks
- Draw cards and play spells to damage your opponent
- Spells resolve based on priority (higher numbers go first)
- When health reaches 0, lose a trunk and reset health
- First player to lose all trunks loses the game

## Requirements

- Python 3.6+
- No external dependencies

## Files

- `elephants_prototype.py` - Main game engine and logic
- `spells.json` - Complete spell database