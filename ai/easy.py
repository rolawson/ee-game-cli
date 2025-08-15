"""Easy AI - Random decision making"""

import random
from .base import BaseAI


class EasyAI(BaseAI):
    """Easy AI - completely random decisions"""
    
    def __init__(self):
        super().__init__()
        print("[EasyAI initialized]")
    
    def _select_card(self, player, gs, valid_indices):
        """Just pick a random valid card"""
        if not valid_indices:
            return None
        choice = random.choice(valid_indices)
        
        # Debug logging
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EASY] {player.name} randomly picked: {player.hand[choice].name}\033[0m"
            )
        return choice
    
    def make_choice(self, valid_options, caster, gs, current_card):
        """Just pick a random option"""
        if not valid_options:
            return None
            
        choice = random.choice(valid_options)
        
        # Debug logging
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            # Format option description for logging
            option_desc = self._describe_option(choice)
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EASY] {caster.name} randomly chose: {option_desc}\033[0m"
            )
        
        return choice
    
    def _describe_option(self, option):
        """Generate a simple description of the option for logging"""
        if option.get('type') == 'sequence':
            # For sequence actions, describe all actions
            actions = []
            for act in option.get('actions', []):
                actions.append(act.get('type', 'unknown'))
            return f"sequence: {' then '.join(actions)}"
        else:
            # Single action
            action_type = option.get('type', 'unknown')
            target = option.get('target', '')
            params = option.get('parameters', {})
            value = params.get('value', '')
            
            if action_type in ['damage', 'heal', 'bolster', 'weaken']:
                return f"{action_type} {value} to {target}"
            elif action_type in ['advance', 'cancel', 'discard']:
                return f"{action_type} {target}"
            else:
                return action_type
    
    def choose_draft_set(self, player, gs, available_sets):
        """Easy AI drafting - very simple heuristics"""
        if not available_sets:
            return None
        
        # Easy AI uses simple preferences
        set_scores = {}
        
        for idx, spell_set in enumerate(available_sets):
            score = random.randint(0, 50)  # High randomness
            
            # Simple preferences
            has_damage = False
            has_healing = False
            
            for spell in spell_set:
                effects_str = str(spell.resolve_effects)
                if 'damage' in effects_str:
                    has_damage = True
                if 'heal' in effects_str:
                    has_healing = True
            
            # Easy AI likes damage and healing
            if has_damage:
                score += 30
            if has_healing:
                score += 20
            
            set_scores[idx] = score
        
        # Pick highest scoring (but still quite random)
        best_idx = max(set_scores.items(), key=lambda x: x[1])[0]
        return available_sets[best_idx]