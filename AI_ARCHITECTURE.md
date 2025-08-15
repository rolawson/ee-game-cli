# AI Architecture Documentation for Elemental Elephants

## Overview

The Elemental Elephants AI system is built on a modular, extensible architecture that supports multiple difficulty levels and strategic approaches. The system has evolved from a simple heuristic-based AI to a sophisticated multi-strategy system with advanced capabilities.

## Current Implementation Status

### ✅ Completed Features

1. **Modular AI System**
   - Base AI class with common functionality
   - Three difficulty levels: Easy, Medium, Hard
   - Extensible architecture for new strategies

2. **Advanced Capabilities**
   - **Combo Awareness**: AI recognizes and utilizes spell synergies
   - **Opponent Tracking**: Monitors opponent patterns and card usage
   - **Card Counting**: Tracks remaining spells in opponent decks
   - **Strategic Drafting**: Element category-aware draft decisions
   - **Timing Optimization**: Contextual spell timing based on game state
   - **Hand Synergy Evaluation**: Multi-turn planning capabilities
   - **Card Mobility Understanding**: Values movement and positioning effects

3. **Element Category System**
   - Data-driven element classifications (offense/defense/mobility/balanced)
   - Element-spell type synergy evaluation
   - Strategic drafting based on element roles

## Architecture Overview

```
ai/
├── __init__.py
├── base.py           # Abstract base class with common functionality
├── easy.py           # Random decisions with simple preferences
├── medium.py         # Basic strategy and situational awareness
└── hard.py           # Advanced strategy with full feature set
```

## Core Components

### 1. BaseAI Class

The foundation for all AI strategies, providing:

```python
class BaseAI(ABC):
    # Core decision methods
    def choose_card_to_play(player, gs)
    def make_choice(valid_options, caster, gs, current_card)
    def choose_draft_set(player, gs, available_sets)
    
    # Opponent tracking
    def update_opponent_history(gs)
    def analyze_opponent_patterns(opponent_name)
    def get_remaining_spells(opponent_name, elephant=None)
    
    # Element category support
    def get_element_category(element)
    def get_element_synergy(element, spell_type)
    def get_element_draft_priority(element)
```

### 2. Difficulty Levels

#### Easy AI
- Random card selection with slight preferences
- Simple drafting (likes damage and healing)
- No complex analysis or tracking
- Suitable for beginners

#### Medium AI
- Health-based decision making
- Basic threat assessment
- Balanced drafting with type diversity
- Considers game state for choices

#### Hard AI
- Comprehensive card evaluation scoring
- Advanced features:
  - Combo potential analysis
  - Opponent pattern recognition
  - Card counting and prediction
  - Element synergy optimization
  - Positioning and timing strategies
  - Risk/reward evaluation

### 3. Decision Making Process

```
1. Card Selection
   ├── Validate legal plays (notfirst/notlast)
   ├── Evaluate each option
   │   ├── Base scoring (priority, type, element)
   │   ├── Situational modifiers
   │   ├── Combo potential
   │   ├── Opponent considerations
   │   └── Timing factors
   └── Select highest scoring option

2. Choice Actions (player_choice)
   ├── Analyze option types
   ├── Evaluate health/damage implications
   ├── Consider game state
   └── Make strategic choice

3. Drafting
   ├── Analyze available sets
   ├── Evaluate type balance
   ├── Consider element categories
   ├── Check synergies
   └── Select optimal set
```

## Key Features

### 1. Opponent Tracking System

Tracks per-opponent:
- Spells played (with round/clash timing)
- Element usage patterns
- Spell type preferences
- Known spell sets
- Remaining unplayed spells

### 2. Card Counting

- Identifies complete spell sets from partial information
- Tracks remaining spells per opponent
- Enables predictive play based on known remaining options

### 3. Element Category Integration

Uses `element_categories.json` for:
- Strategic categorization (offense/defense/mobility/balanced)
- Spell type synergy bonuses
- Draft priority multipliers
- Situational play bonuses

### 4. Combo Recognition

- Identifies spell enablers and payoffs
- Recognizes multi-card combo chains
- Values setup for future turns
- Considers passive effect synergies

### 5. Strategic Evaluation Factors

Hard AI considers:
- **Timing**: Response spell conditions, conjury vulnerability
- **Positioning**: Card mobility, advancement potential
- **Resource Management**: Hand size, card advantage
- **Risk Assessment**: Self-damage evaluation, lethal prevention
- **Adaptability**: Counter-strategies based on opponent patterns

## Testing Framework

### Available Testing Tools

1. **ai_spectator.py**: Visual AI vs AI with configurable delays
2. **ai_battle.py**: Fast automated battles for statistics
3. **ai_vs_ai.py**: Tournament system with detailed analysis
4. **ai_test.py**: Basic testing framework

All test results are saved to `test_results/` directory.

## Configuration

### Game Initialization
```python
engine = GameEngine(player_names, ai_difficulty='medium')
# ai_difficulty options: 'easy', 'medium', 'hard'
```

### Element Categories Configuration
Edit `element_categories.json` to:
- Add new elements
- Adjust category assignments
- Modify synergy values
- Change draft priorities

## Future Enhancement Opportunities

### Near-term
1. **Personality System**: Aggressive, defensive, combo-focused variants
2. **Learning Components**: Adapt to player patterns over sessions
3. **Multi-game Memory**: Track strategies across multiple games
4. **Advanced Drafting**: Counter-drafting based on opponent picks

### Long-term
1. **Machine Learning Integration**: Train on game logs
2. **Monte Carlo Tree Search**: For deeper strategic planning
3. **Neural Network Evaluation**: For complex board states
4. **Tournament Evolution**: Genetic algorithms for strategy optimization

## Integration Points

The AI system integrates with:
- `GameEngine`: AI strategy selection and initialization
- `ActionHandler`: Choice resolution for player_choice actions
- `Element Categories`: Strategic element classification
- Game state evaluation through direct access to `GameState`

## Performance Considerations

- AI decisions are made in real-time without significant delay
- Hard AI performs more calculations but remains responsive
- Opponent tracking has minimal memory overhead
- Element category loading happens once at initialization

## Debugging and Analysis

AI decision logs can be enabled to track:
- Card selection reasoning
- Choice evaluation scores
- Drafting decisions
- Combo recognition
- Risk assessments

This provides transparency into AI decision-making for balance testing and improvement.