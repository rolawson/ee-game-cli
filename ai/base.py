"""Base AI class for all AI strategies"""

from abc import ABC, abstractmethod


class BaseAI(ABC):
    """Base class for all AI strategies"""
    
    def __init__(self):
        self.engine = None  # Will be set by GameEngine
    
    def choose_card_to_play(self, player, gs):
        """Main entry point for AI card selection"""
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
    
    @abstractmethod
    def _select_card(self, player, gs, valid_indices):
        """Override in subclasses to implement selection strategy"""
        raise NotImplementedError
    
    @abstractmethod
    def make_choice(self, valid_options, caster, gs, current_card):
        """Make decisions for player_choice actions
        
        Args:
            valid_options: List of valid action options to choose from
            caster: The player making the choice
            gs: Current game state
            current_card: The card with the player_choice effect
            
        Returns:
            The chosen option from valid_options
        """
        raise NotImplementedError