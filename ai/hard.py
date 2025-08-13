"""Hard AI - Advanced strategic decision making"""

import random
from .base import BaseAI


class HardAI(BaseAI):
    """Hard AI - strategic play with card evaluation"""
    
    def _select_card(self, player, gs, valid_indices):
        """Evaluate each card and pick the best one"""
        if not valid_indices:
            return None
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-HARD] {player.name} evaluated {len(valid_indices)} options\033[0m"
            )
        
        # Evaluate each valid card
        scores = {}
        for idx in valid_indices:
            card = player.hand[idx]
            score = self._evaluate_card(card, player, gs)
            scores[idx] = score
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-HARD]   {card.name}: score = {score}\033[0m"
                )
        
        # Return highest scoring card
        best = max(scores.items(), key=lambda x: x[1])
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-HARD] {player.name} chose: {player.hand[best[0]].name} (score: {best[1]})\033[0m"
            )
        return best[0]
    
    def _evaluate_card(self, card, player, gs):
        """Score a card based on game state"""
        score = 0
        
        # Priority scoring - faster is better early game
        if gs.clash_num <= 2 and card.priority != 'A':
            score += (5 - int(card.priority)) * 10
        
        # Critical health - prioritize healing
        if player.health <= 2 and 'remedy' in card.types:
            score += 150
        elif player.health <= 3 and 'remedy' in card.types:
            score += 80
            
        # Enemy at low health - prioritize damage
        low_health_enemies = [p for p in gs.players if p != player and p.health <= 2]
        if low_health_enemies and 'attack' in card.types:
            score += 120
            
        # Enemy with empty hand - huge advantage
        empty_hand_enemies = [p for p in gs.players if p != player and len(p.hand) == 0]
        if empty_hand_enemies:
            # They can't play spells next clash - be very aggressive
            if 'attack' in card.types:
                score += 100  # High priority to damage
            if 'cancel' in str(card.resolve_effects) or 'discard' in str(card.resolve_effects):
                score += 80  # Control spells are also great
            # Boost spells are good when enemy can't interfere
            if 'boost' in card.types:
                score += 70
            
        # Boost spells when we have other spells
        if 'boost' in card.types and len([c for c in player.hand if 'boost' not in c.types]) >= 2:
            score += 60
            
        # Response spells based on round state
        if 'response' in card.types:
            if gs.round_num > 1:  # More likely to trigger
                score += 50
            else:
                score -= 20  # Less useful early
                
        # Conjury spells - good for board control
        if card.is_conjury:
            score += 40
            
        # Cancel/Discard when enemies have multiple spells
        if 'cancel' in str(card.resolve_effects) or 'discard' in str(card.resolve_effects):
            # This is a rough heuristic - in later clashes enemies have more spells
            if gs.clash_num >= 2:
                score += 70
                
        # Avoid cards with restrictions at wrong times
        if gs.clash_num == 1 and card.notfirst == 1:
            score -= 50
        elif gs.clash_num == 4 and card.notlast == 1:
            score -= 50
            
        # Element synergy (if we played same element before)
        if gs.clash_num > 1:
            for past_clash in range(gs.clash_num - 1):
                for spell in player.board[past_clash]:
                    if spell.card.element == card.element:
                        score += 15
                        
        # Hand size considerations
        if len(player.hand) <= 2:
            # Running low on cards - be more conservative
            if 'remedy' in card.types:
                score += 30  # Prioritize survival
            if card.priority == 'A':  # Advance priority cards can come back
                score += 25
                
        # Random factor to prevent predictability
        score += random.randint(-10, 10)
        
        return score