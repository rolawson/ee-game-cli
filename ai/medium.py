"""Medium AI - Basic strategic decision making"""

import random
from .base import BaseAI


class MediumAI(BaseAI):
    """Current AI logic - medium difficulty"""
    
    def _select_card(self, player, gs, valid_indices):
        """Select card based on basic heuristics"""
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-MEDIUM] {player.name} analyzed options\033[0m"
            )
        
        # Categorize cards by preference based on clash timing
        preferred_indices = []
        acceptable_indices = []
        
        for i in valid_indices:
            card = player.hand[i]
            # Cards with notfirst/notlast = 1 are less preferred in those clashes
            if gs.clash_num == 1 and card.notfirst == 1:
                acceptable_indices.append(i)
            elif gs.clash_num == 4 and card.notlast == 1:
                acceptable_indices.append(i)
            else:
                preferred_indices.append(i)
        
        # Use preferred cards if available, otherwise use acceptable ones
        candidate_indices = preferred_indices if preferred_indices else acceptable_indices

        # High-level situational logic
        low_health_enemies = [p for p in gs.players if p != player and p.health <= 2]
        empty_hand_enemies = [p for p in gs.players if p != player and len(p.hand) == 0]
        
        # Survival: Find the best heal card among candidates
        if player.health <= 2:
            heal_options = [(i, player.hand[i]) for i in candidate_indices 
                          if 'remedy' in player.hand[i].types]
            if heal_options:
                # Sort by priority (lower is better)
                heal_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                chosen = heal_options[0]
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MEDIUM] {player.name} chose healing due to low health ({player.health}): {chosen[1].name}\033[0m"
                    )
                return chosen[0]

        # Finisher: Find the best damage card among candidates
        if low_health_enemies:
            damage_options = [(i, player.hand[i]) for i in candidate_indices 
                            if 'attack' in player.hand[i].types]
            if damage_options:
                # Sort by priority (lower is better for faster resolution)
                damage_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                chosen = damage_options[0]
                enemy_names = ", ".join([e.name for e in low_health_enemies])
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MEDIUM] {player.name} chose attack (enemy low health): {chosen[1].name}\033[0m"
                    )
                return chosen[0]
        
        # Aggression: Be aggressive when enemy has empty hand
        if empty_hand_enemies:
            # Prefer attack or control spells when enemy can't respond
            aggressive_options = [(i, player.hand[i]) for i in candidate_indices 
                                if 'attack' in player.hand[i].types or 
                                   'discard' in str(player.hand[i].resolve_effects) or
                                   'cancel' in str(player.hand[i].resolve_effects)]
            if aggressive_options:
                aggressive_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                chosen = aggressive_options[0]
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MEDIUM] {player.name} chose aggressive play (enemy hand empty): {chosen[1].name}\033[0m"
                    )
                return chosen[0]
        
        # Default to a random candidate card
        choice = random.choice(candidate_indices)
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-MEDIUM] {player.name} chose: {player.hand[choice].name}\033[0m"
            )
        return choice