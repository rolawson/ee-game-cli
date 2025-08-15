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

### Normal Game (Human vs AI)
```bash
python elephants_prototype.py
```
Play against an AI opponent with full interactive controls. You'll be prompted to make choices for drafting, playing cards, and resolving effects.

### AI vs AI Testing

#### Spectator Mode (Visual, Auto-advancing)
```bash
# Watch AI games with automatic progression
python ai_spectator.py [ai1_type] [ai2_type] [delay] [num_games]

# Examples:
python ai_spectator.py                    # Default: hard vs medium, 1s delay
python ai_spectator.py hard easy 0.5      # Fast game: hard vs easy, 0.5s delay
python ai_spectator.py hard medium 2.0 5  # 5 slower games with 2s delay
python ai_spectator.py hard hard 0        # Maximum speed (no delay)
```

#### Automated Battles (No Display)
```bash
# Run fast AI battles for statistics
python ai_battle.py [num_games]

# Examples:
python ai_battle.py quick     # Run one test game
python ai_battle.py 10        # Run tournament with 10 games per matchup
python ai_battle.py           # Default: 5 games per matchup
```

#### Tournament Mode
```bash
# Run full tournament between all AI types
python ai_vs_ai.py tournament [games_per_matchup]

# Examples:
python ai_vs_ai.py tournament 20   # 20 games per matchup
python ai_vs_ai.py hard medium 10  # 10 games of hard vs medium
```

### AI Difficulty Levels
- **easy**: Random decisions with simple preferences
- **medium**: Basic strategy and situational awareness
- **hard**: Advanced strategy with combo awareness and card counting

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

### Core Game Files
- `elephants_prototype.py` - Main game engine and logic
- `spells.json` - Complete spell database
- `element_categories.json` - Element type classifications

### AI System
- `ai/` - AI module directory
  - `base.py` - Base AI class with common functionality
  - `easy.py` - Easy difficulty AI (random with simple preferences)
  - `medium.py` - Medium difficulty AI (basic strategy)
  - `hard.py` - Hard difficulty AI (advanced strategy)

### Testing Tools
- `ai_spectator.py` - Watch AI vs AI games with visual display
- `ai_battle.py` - Run automated AI battles for statistics
- `ai_vs_ai.py` - Run AI tournaments with detailed analysis
- `ai_test.py` - Basic AI testing framework

### Documentation
- `HOWTOPLAY.md` - Detailed game rules and mechanics
- `CONTEXT.md` - Technical architecture overview
- `CLARIFICATIONS.md` - Rule clarifications and edge cases

### Results
- `test_results/` - Directory containing AI battle statistics (JSON files)