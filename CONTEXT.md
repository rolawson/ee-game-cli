# Elemental Elephants Prototype: Codebase Overview

This document provides a high-level overview of the architecture for the Python-based command-line prototype of Elemental Elephants. Its purpose is to help developers understand how the different components of the game engine work together.

## Core Design Philosophy

The engine is built on a few key principles:
1.  **Data-Driven:** All card logic (effects, conditions, targets) is defined in `spells.json`. The code is a generic interpreter for this data. To change a card, you only need to change the JSON.
2.  **State-View Separation:** The `GameState` object holds all the raw data of the game. The `DashboardDisplay` class is solely responsible for reading that state and drawing it to the screen. They are kept separate.
3.  **Event-Driven Logic:** For complex conditional effects (like `Response` spells), the engine uses an `event_log`. The `ActionHandler` fires events (e.g., `player_damaged`), and the `ConditionChecker` queries this log to see if conditions are met. This decouples rules from the immediate board state.
4.  **Turn-Based Loop:** The game is managed by a main `GameEngine` that progresses through a structured loop: `Game -> Round -> Clash -> Phase`.
5.  **Modular AI System:** AI logic is separated into its own module (`ai/`) with different difficulty levels implemented as distinct classes inheriting from a common base.

## Key Classes and Their Responsibilities

### 1. Data Model Classes

These classes are simple containers for holding game information. They have very little logic of their own.

-   **`Card`**: Represents a single, static spell card. It's created by loading one entry from the `SPELL_JSON_DATA`. It knows its name, priority, effects, etc., but doesn't *do* anything.
-   **`PlayedCard`**: Represents an instance of a card that is physically on the board. It links a `Card` object to an `owner` (a `Player`) and tracks its current `status` (`prepared`, `active`, `cancelled`).
-   **`Player`**: Holds all the state for a single player: `name`, `health`, `max_health`, `hand`, `discard_pile`, and their `board`. The `board` is a list of four lists `[[], [], [], []]`, where each inner list represents a clash slot and can hold multiple `PlayedCard` objects.
-   **`GameState`**: The master object that holds the entire state of the game at any given moment. It contains the list of `players`, the `main_deck` of un-drafted spell sets, the current `round_num` and `clash_num`, and the `event_log`.

### 2. The Main `GameEngine` Class

This is the "conductor" of the game. It owns the `GameState` and all the helper classes and is responsible for managing the overall flow.

-   **`run_game()`**: The main entry point. It contains the top-level `while` loop that continues as long as there is more than one player with trunks.
-   **`_run_round()`**: Manages the flow of a single round. It contains a `try...except` block that runs the four clashes and an `_run_end_of_round` phase. It listens for the `RoundOverException` to end the clashes early.
-   **`_run_clash()`**: Manages the flow of a single clash, calling the phase methods in the correct order: `Prepare` -> `Cast` -> `Resolve` -> `Advance`.
-   **`_run_..._phase()` methods**: Each phase method is responsible for a specific part of the turn structure (e.g., `_run_prepare_phase` handles prompting players to play cards).
-   **`_handle_trunk_loss()`**: Contains the logic for what happens when a player's health reaches zero.
-   **`_prompt_for_choice()`**: The central user-input function. It displays options to the human player and safely handles their input.

### 3. Logic and Helper Classes

These are the "worker" classes that the `GameEngine` delegates tasks to.

-   **`DashboardDisplay`**: The game's entire user interface. Its only job is to take the current `GameState` and draw it to the console in a readable format.
-   **`ConditionChecker`**: The "rules lawyer." Its `check()` method takes a condition from a spell's JSON and evaluates it against the current `GameState` (primarily the `event_log`) to see if it's `True` or `False`. This is how `Turbulence` and other `Response` spells work.
-   **`ActionHandler`**: The "muscle" of the engine. Its `execute()` method takes an action from a spell's JSON and makes the corresponding changes to the `GameState` (e.g., reducing a `Player`'s `health`). It is also responsible for firing events into the `event_log`.

### 4. Element Category System

The game uses a data-driven element categorization system defined in `element_categories.json`:

- **Offense Elements**: Fire, Lightning, Venom, Earth, Shadow, Sunbeam, Blood - focused on damage and debilitation
- **Defense Elements**: Water, Ichor, Thunder, Moonshine, Metal, Nectar - focused on healing and protection  
- **Mobility Elements**: Wind, Space, Time, Aster - focused on movement and spell positioning
- **Balanced Elements**: Wood, Twilight - equal focus on offense and defense

The AI uses these categories for:
- Strategic drafting decisions (balancing offense/defense/mobility)
- Element-spell type synergy evaluation
- Situational play decisions based on element strengths

### 5. AI System (Modular Architecture)

The AI system is organized in a separate `ai/` module with sophisticated strategic capabilities. For detailed AI architecture information, see `AI_ARCHITECTURE.md`.

#### Module Structure:
```
ai/
├── __init__.py      # Module exports
├── base.py          # BaseAI abstract class
├── easy.py          # Random AI implementation
├── medium.py        # Basic strategic AI
└── hard.py          # Advanced strategic AI
```

#### AI Classes:
-   **`BaseAI`** (`ai/base.py`): Abstract base class that all AI strategies inherit from. Provides:
    - `choose_card_to_play()`: Main entry point for card selection
    - `_get_valid_card_indices()`: Filters cards by clash restrictions (notfirst/notlast)
    - `_select_card()`: Abstract method that subclasses must implement
    
-   **`EasyAI`** (`ai/easy.py`): Random decision making for beginners
    - Picks randomly from valid cards
    - No strategic consideration
    
-   **`MediumAI`** (`ai/medium.py`): Basic heuristics-based AI
    - Prioritizes healing when health ≤ 2
    - Attacks when enemy health ≤ 2
    - Plays aggressively when enemy hand is empty
    - Considers clash timing restrictions
    
-   **`HardAI`** (`ai/hard.py`): Advanced strategic AI with card scoring
    - Evaluates each card with a scoring system
    - Considers: health states, enemy threats, card synergies, element matching
    - Adapts strategy based on hand size and game state
    - Includes randomness to prevent predictability

#### Integration:
- The `GameEngine` accepts an `ai_difficulty` parameter ('easy', 'medium', 'hard')
- AI decision logs are stored during the prepare phase and revealed after the cast phase
- Each AI instance has a reference to the engine for logging purposes

## The Game Flow (Simplified)

1.  **Game Start**: Player selects AI difficulty, then `GameEngine.run_game()` starts.
2.  **Setup**: `_setup_game()` handles the initial draft, with AI strategies instantiated based on difficulty.
3.  **Main Loop**: Enters a `while` loop that calls `_run_round()` as long as the game isn't over.
4.  **Round Structure**: `_run_round()` sets up a `try` block and then calls `_run_clash()` four times.
5.  **Clash Phases**: `_run_clash()` calls phases in order:
    - `_run_prepare_phase()`: Players/AI select cards (AI decisions logged but hidden)
    - `_run_cast_phase()`: All cards revealed simultaneously (AI decision logs displayed)
    - `_run_resolve_phase()`: Spells resolve by priority order
    - `_run_advance_phase()`: Advance effects trigger
6.  **Resolution**: During `_run_resolve_phase()`, spells are sorted by priority and resolved.
7.  **Effects**: `ActionHandler.execute()` processes spell effects, checking conditions and modifying game state.
8.  **Events**: Actions fire events into the `event_log` for tracking and condition checking.
9.  **Trunk Loss**: If health drops to 0, `_handle_trunk_loss()` may trigger `RoundOverException`.
10. **Round End**: `_run_end_of_round()` handles hand management and ringleader rotation.
11. **Victory**: The game loop checks win conditions and declares a winner when only one player has trunks.

## Condition Types

The `ConditionChecker` class evaluates various condition types used in spell effects:

### Basic Conditions
- **`always`**: Always returns true (unconditional effects)
- **`if_not`**: Negates a sub-condition (used for "Otherwise" effects)

### Spell State Conditions
- **`if_caster_has_active_spell_of_type`**: Checks if the caster has active spells of a specific type
  - Parameters: `spell_type` (e.g., "attack", "boost", "any"), `count` (default 1), `exclude_self` (default false)
- **`if_enemy_has_active_spell_of_type`**: Checks if any enemy has active spells of a specific type
  - Parameters: `spell_type`, `count` (default 1)
- **`if_board_has_active_spell_of_type`**: Checks if there are active spells of a type on the entire board
  - Parameters: `spell_type`, `count` (default 1), `exclude_self` (default false)

### Historical Conditions
- **`if_spell_previously_resolved_this_round`**: Checks if this spell resolved in a past clash
  - Parameters: `count` (1 = any past clash, 2+ = specific number of times)
- **`if_spell_was_active_in_other_clashes`**: Checks if this spell was active in other clashes (Impact)
  - Parameters: `count` (number of other clashes required)
- **`if_spell_advanced_this_turn`**: Checks if any spell has advanced this round

### Special Conditions
- **`if_resolve_condition_was_met`**: Checks if the resolve condition succeeded (for advance effects)

## File Structure

```
Elemental Elephants/
├── elephants_prototype.py   # Main game engine
├── ai/                      # AI module
│   ├── __init__.py
│   ├── base.py             # Abstract base AI class
│   ├── easy.py             # Random AI
│   ├── medium.py           # Heuristic-based AI
│   └── hard.py             # Strategic scoring AI
├── spells.json             # Card definitions
├── element_categories.json # Element categorization and synergies
├── HOWTOPLAY.md            # Game rules
├── CLARIFICATIONS.md       # Rules clarifications
├── CONTEXT.md              # This file
├── AI_ARCHITECTURE.md      # Consolidated AI documentation
├── spell_analytics.py      # Spell balance analysis tool
├── gameplay_analytics.py   # Game statistics tracking
└── test_results/           # AI test results
```

## Latest Updates
1. **Element Categories System** - Added element_categories.json configuration:
   - Offense (Fire, Lightning, Venom, Earth, Sunbeam, Blood)
   - Defense (Water, Ichor, Thunder, Moonshine, Metal, Nectar)
   - Mobility (Wind, Space, Time, Aster, Shadow) - Shadow moved from offense
   - Balanced (Wood, Twilight)
   - Includes draft priorities and spell type synergies

2. **AI Strategic Improvements**:
   - Added element category awareness to all AI levels
   - Enhanced drafting with category-based evaluation
   - Improved gameplay decisions using element synergies
   - Data-driven configuration for easy balance adjustments

3. **Analytics Tools** - Created comprehensive analysis tools:
   - spell_analytics.py - Analyzes damage, healing, priorities, effects by element
   - gameplay_analytics.py - Tracks win rates, game length, element usage
   - spell_analysis_report.txt - Generated comprehensive balance report

4. **Spell Updates**:
   - Turbulence: Now checks if_spell_was_active_in_other_clashes (2+)
   - Impact: damage_per_spell_from_other_clashes action
   - Grow/Prickle: auto_optimal_choice for intelligent option selection

5. **Hard AI Performance Fix** - Rebalanced Hard AI to be more competitive:
   - Simplified scoring system from 11+ factors to focused core mechanics
   - Reduced extreme penalties (lethal self-damage from -10000 to -1000)
   - Made combo evaluation immediate rather than potential-based
   - Improved health-based decision making with ratio thresholds
   - Streamlined option evaluation to encourage aggressive play

6. **AI Element Selection Bias Fix** - Eliminated heavy bias toward certain elements:
   - Replaced complex additive scoring with normalized weight-based system
   - Made win rate the primary factor in element selection (0.5x to 2.0x weight)
   - Added penalties for overselected elements (0.3x weight for >15% selection)
   - Implemented true weighted random selection instead of always picking highest score
   - Added element_win_rates.json for dynamic win rate tracking
   - Result: Selection rates now balanced between 5-8% per element (was 19.5% for Metal)