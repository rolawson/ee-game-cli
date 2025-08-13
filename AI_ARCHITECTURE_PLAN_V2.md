# AI Architecture Plan V2 for Elemental Elephants

## Current State

The game currently has a basic `AI_Player` class with simple heuristics:
- Prioritizes healing when health is low (<=2)
- Targets low-health enemies with attacks
- Considers card timing restrictions (notfirst/notlast)
- Makes mostly random choices for complex decisions

## Proposed Modular AI System

### 1. Quick Implementation Path

Start with a simple strategy selector that can be configured at game start:

```python
class GameEngine:
    def __init__(self, player_names, ai_difficulty='medium'):
        # ... existing code ...
        self.ai_difficulty = ai_difficulty
        
        # Create AI players with appropriate strategies
        for i, name in enumerate(player_names):
            if i > 0:  # AI players
                if ai_difficulty == 'easy':
                    self.ai_strategies[i] = EasyAI()
                elif ai_difficulty == 'medium':
                    self.ai_strategies[i] = MediumAI()
                elif ai_difficulty == 'hard':
                    self.ai_strategies[i] = HardAI()
                elif ai_difficulty == 'random':
                    self.ai_strategies[i] = RandomAI()
```

### 2. AI Strategy Classes

#### Base AI Class
```python
class BaseAI:
    """Base class for all AI strategies"""
    
    def choose_card_to_play(self, player, gs):
        # Get valid cards considering clash restrictions
        valid_indices = self._get_valid_card_indices(player, gs)
        if not valid_indices:
            return None
            
        # Strategy-specific selection
        return self._select_card(player, gs, valid_indices)
    
    def _get_valid_card_indices(self, player, gs):
        """Common method to filter cards by clash rules"""
        valid = list(range(len(player.hand)))
        if gs.clash_num == 1:
            valid = [i for i in valid if player.hand[i].notfirst < 2]
        if gs.clash_num == 4:
            valid = [i for i in valid if player.hand[i].notlast < 2]
        return valid
    
    def _select_card(self, player, gs, valid_indices):
        """Override in subclasses"""
        raise NotImplementedError
    
    def make_choice(self, options, context=None):
        """Make decisions for player_choice actions"""
        raise NotImplementedError
```

#### Easy AI (Random)
```python
class EasyAI(BaseAI):
    """Completely random decisions"""
    
    def _select_card(self, player, gs, valid_indices):
        return random.choice(valid_indices)
    
    def make_choice(self, options, context=None):
        return random.choice(list(options.keys()))
```

#### Medium AI (Current Behavior)
```python
class MediumAI(BaseAI):
    """Current AI logic - basic survival and targeting"""
    
    def _select_card(self, player, gs, valid_indices):
        # Port existing logic from AI_Player.choose_card_to_play
        # Includes heal when low, attack when enemy is low, etc.
        pass
    
    def make_choice(self, options, context=None):
        # Smart choices for Blood spells based on health
        # Prefer damage over heal when healthy, etc.
        pass
```

#### Hard AI (Strategic)
```python
class HardAI(BaseAI):
    """Advanced strategic play"""
    
    def _select_card(self, player, gs, valid_indices):
        # Evaluate each valid card
        scores = {}
        for idx in valid_indices:
            card = player.hand[idx]
            score = self._evaluate_card(card, player, gs)
            scores[idx] = score
        
        # Return highest scoring card
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _evaluate_card(self, card, player, gs):
        score = 0
        
        # Priority scoring (faster is better early)
        if gs.clash_num <= 2:
            score += (5 - int(card.priority)) * 10 if card.priority != 'A' else 0
        
        # Type scoring based on game state
        if player.health <= 2 and 'remedy' in card.types:
            score += 100
        elif self._has_low_health_enemy(gs) and 'attack' in card.types:
            score += 80
        elif 'boost' in card.types and self._has_synergy(card, player):
            score += 60
            
        # Response spell bonus if conditions are met
        if 'response' in card.types and self._response_will_trigger(card, gs):
            score += 40
            
        return score
```

### 3. Integration Points

#### In ActionHandler for choices:
```python
def _execute_single_action(self, action_data, gs, caster, current_card):
    # ... existing code ...
    
    if action_type == 'player_choice':
        if caster.is_human:
            # ... existing human logic ...
        else:
            # Use AI strategy for choice
            ai_strategy = self.engine.get_ai_strategy(caster)
            choice_context = {
                'caster_health': caster.health,
                'card': current_card,
                'options': action_data.get('options', [])
            }
            choice = ai_strategy.make_choice(options_dict, choice_context)
```

### 4. Configuration Options

Add to game start menu:
```
Choose AI Difficulty:
[1] Easy (Random)
[2] Medium (Balanced)
[3] Hard (Strategic)
[4] Custom (Mix of strategies)
```

For custom mode:
```python
# Allow different AI personalities for multiple AI opponents
ai_configs = {
    "AI Opponent 1": "aggressive",
    "AI Opponent 2": "defensive",
    "AI Opponent 3": "combo"
}
```

### 5. Future Personality Types

#### Aggressive AI
- Prioritizes attack spells
- Takes risks with Blood spells
- Targets highest threat enemies

#### Defensive AI
- Prioritizes remedy and bolster
- Avoids self-damage
- Uses cancel/discard defensively

#### Combo AI
- Looks for spell synergies
- Sets up response spells
- Maximizes advance effects

### 6. Implementation Steps

1. **Phase 1** (Immediate):
   - Create BaseAI class
   - Move current logic to MediumAI
   - Add EasyAI (random)
   - Add difficulty selection at game start

2. **Phase 2** (Next):
   - Implement HardAI with card evaluation
   - Add smarter choice-making for complex spells
   - Improve target selection logic

3. **Phase 3** (Future):
   - Add personality types (Aggressive, Defensive, Combo)
   - Implement learning from player patterns
   - Add AI vs AI testing mode

### 7. Testing Framework

```python
class AITester:
    """Test different AI strategies against each other"""
    
    def run_ai_battle(self, ai1_type, ai2_type, num_games=100):
        results = {'ai1_wins': 0, 'ai2_wins': 0}
        
        for _ in range(num_games):
            engine = GameEngine(
                player_names=["AI 1", "AI 2"],
                ai_strategies={'AI 1': ai1_type, 'AI 2': ai2_type}
            )
            winner = engine.run_game(headless=True)
            if winner == "AI 1":
                results['ai1_wins'] += 1
            else:
                results['ai2_wins'] += 1
                
        return results
```

## Benefits of This Approach

1. **Minimal Refactoring**: Works with existing code structure
2. **Gradual Enhancement**: Can improve AI incrementally
3. **Easy Testing**: Can A/B test strategies
4. **Player Choice**: Multiple difficulty levels
5. **Extensible**: Easy to add new strategies
6. **Maintainable**: Each strategy is self-contained