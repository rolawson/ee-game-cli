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