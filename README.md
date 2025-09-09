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

To play against Claude AI:
1. Make sure `ANTHROPIC_API_KEY` is set in your environment
2. Run `python elephants_prototype.py`
3. When prompted "Choose AI Difficulty", select option 5 for Claude

### AI vs AI Testing

#### Spectator Mode (Visual, Auto-advancing)
```bash
# Watch AI games with automatic progression
python ai_spectator.py [ai1_type] [ai2_type] [delay] [num_games]

# Examples:
python ai_spectator.py                    # Default: expert vs expert, 1s delay
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

#### AI Win Rate Testing
```bash
# Test AI win rates with full game rules
python ai_winrate_test.py [games_per_matchup]
python ai_winrate_test.py [ai1] [ai2] [num_games]

# Examples:
python ai_winrate_test.py              # Quick test with 5 games per matchup
python ai_winrate_test.py 20           # 20 games per matchup
python ai_winrate_test.py hard expert 30  # 30 games of hard vs expert
```


### Analytics and Data Generation
The game includes comprehensive analytics tracking for balance testing:

#### Unified Analytics System
```bash
# Run games with specific AI matchups
python analytics.py 100                           # 100 games of expert vs expert
python analytics.py 50 --ai1 hard --ai2 medium   # 50 games of hard vs medium
python analytics.py 200 --ai1 expert --ai2 easy  # 200 games of expert vs easy

# Quick test mode (10 games)
python analytics.py quick --ai1 medium --ai2 hard

# Tournament mode (all AI types play each other)
python analytics.py tournament --games 30         # 30 games per matchup

# Silent mode (suppress progress messages)
python analytics.py 100 --ai1 expert --ai2 hard --silent
```

Available AI types: `easy`, `medium`, `hard`, `expert`

#### Legacy Analytics Tools
```bash
# Generate Analytics Data (older tool)
python generate_analytics_data.py quick
python generate_analytics_data.py 100              # 100 hard vs hard games
python generate_analytics_data.py 50 medium easy   # 50 medium vs easy games
python generate_analytics_data.py tournament 20    # 20 games per matchup

# Interactive analytics tournament
python run_analytics_tournament.py                 # Prompts for settings
```

#### View Analytics Reports
```bash
# Generate report from existing game logs
python analyze_real_world_data.py

# View the generated report
cat real_world_analysis.txt
```

The analytics system tracks:
- Real-world damage dealt by each spell
- Average damage per element
- Spell usage frequency
- Comparison of theoretical vs actual damage
- Win rates and game lengths
- Weighted damage analysis (weaken effects count as 2x)

### AI Difficulty Levels
- **easy**: Random decisions with simple preferences
- **medium**: Basic strategy and situational awareness
- **hard**: Advanced strategy with solid fundamentals and tactical play
- **expert**: Complex multi-turn planning, combo recognition, and overthinking everything
- **claude**: LLM-powered AI that uses natural language reasoning (requires ANTHROPIC_API_KEY environment variable)

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
  - `expert.py` - Expert difficulty AI (complex planning and overthinking)

### Testing Tools
- `ai_spectator.py` - Watch AI vs AI games with visual display
- `ai_battle.py` - Run automated AI battles for statistics
- `ai_vs_ai.py` - Run AI tournaments with detailed analysis
- `ai_test.py` - Basic AI testing framework
- `ai_winrate_test.py` - Test AI win rates using full game engine

### Analytics Tools
- `analytics.py` - Unified analytics system for running AI games with specific matchups
- `game_logger.py` - Game event logging system for analytics
- `generate_analytics_data.py` - Generate game data for analysis (legacy)
- `run_analytics_tournament.py` - Interactive tournament runner for analytics
- `analyze_real_world_data.py` - Generate comprehensive analytics reports

### Documentation
- `HOWTOPLAY.md` - Detailed game rules and mechanics
- `CONTEXT.md` - Technical architecture overview
- `CLARIFICATIONS.md` - Rule clarifications and edge cases

### Results
- `test_results/` - Directory containing AI battle statistics (JSON files)
- `game_logs/` - Directory containing detailed game logs for analytics (JSON files)
- `real_world_analysis.txt` - Generated analytics report