# Elemental Elephants Prototype: Codebase Overview

This document provides a high-level overview of the architecture for the Python-based command-line prototype of Elemental Elephants. Its purpose is to help developers understand how the different components of the game engine work together.

## Core Design Philosophy

The engine is built on a few key principles:
1.  **Data-Driven:** All card logic (effects, conditions, targets) is defined in a single `SPELL_JSON_DATA` string. The code is a generic interpreter for this data. To change a card, you only need to change the JSON.
2.  **State-View Separation:** The `GameState` object holds all the raw data of the game. The `DashboardDisplay` class is solely responsible for reading that state and drawing it to the screen. They are kept separate.
3.  **Event-Driven Logic:** For complex conditional effects (like `Response` spells), the engine uses an `event_log`. The `ActionHandler` fires events (e.g., `player_damaged`), and the `ConditionChecker` queries this log to see if conditions are met. This decouples rules from the immediate board state.
4.  **Turn-Based Loop:** The game is managed by a main `GameEngine` that progresses through a structured loop: `Game -> Round -> Clash -> Phase`.

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
-   **`AI_Player`**: Contains the logic for how a non-human player makes decisions. Its `choose_card_to_play()` method looks at the `GameState` and the AI's hand and returns the index of the best card to play.

## The Game Flow (Simplified)

1.  `GameEngine.run_game()` starts.
2.  It calls `_setup_game()` to handle the initial draft.
3.  It enters a `while` loop that calls `_run_round()` as long as the game isn't over.
4.  `_run_round()` sets up a `try` block and then calls `_run_clash()` four times.
5.  `_run_clash()` calls `_run_prepare_phase()`, then `_run_cast_phase()`, `_run_resolve_phase()`, and `_run_advance_phase()`.
6.  During the `_run_resolve_phase()`, it gets a list of active spells and sorts them by priority.
7.  For each spell, it calls `ActionHandler.execute()` on that spell's effects.
8.  `ActionHandler.execute()` may call `ConditionChecker.check()` to see if an effect should happen. If it does, it modifies the `GameState` and fires an event into the `event_log`.
9.  If damage is dealt and a player's health drops to 0, `_handle_trunk_loss()` is called, which may trigger `_check_for_round_end()`, which may `raise RoundOverException`.
10. If the exception is raised, the clash loop in `_run_round()` is broken, and the code proceeds to `_run_end_of_round()`.
11. `_run_end_of_round()` handles hand management and prepares for the next round.
12. The `run_game()` loop checks the win condition, and either starts another round or declares a winner.