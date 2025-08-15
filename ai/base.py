"""Base AI class for all AI strategies"""

from abc import ABC, abstractmethod


class BaseAI(ABC):
    """Base class for all AI strategies"""
    
    def __init__(self):
        self.engine = None  # Will be set by GameEngine
        self.opponent_history = {}  # Track what opponents have played
    
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
    
    def update_opponent_history(self, gs):
        """Track what opponents have played this clash"""
        for player in gs.players:
            if player.name not in self.opponent_history:
                self.opponent_history[player.name] = {
                    'spells_played': [],
                    'elements_used': {},
                    'spell_types_used': {},
                    'total_damage_dealt': 0,
                    'total_healing_done': 0,
                    'cards_discarded': 0
                }
            
            # Track spells revealed this clash
            for spell in player.board[gs.clash_num - 1]:
                if spell.status == 'revealed':
                    history = self.opponent_history[player.name]
                    
                    # Track spell
                    spell_info = {
                        'name': spell.card.name,
                        'element': spell.card.element,
                        'types': spell.card.types,
                        'round': gs.round_num,
                        'clash': gs.clash_num
                    }
                    history['spells_played'].append(spell_info)
                    
                    # Track element usage
                    element = spell.card.element
                    history['elements_used'][element] = history['elements_used'].get(element, 0) + 1
                    
                    # Track spell type usage
                    for spell_type in spell.card.types:
                        history['spell_types_used'][spell_type] = history['spell_types_used'].get(spell_type, 0) + 1
    
    def analyze_opponent_patterns(self, opponent_name):
        """Analyze an opponent's play patterns"""
        if opponent_name not in self.opponent_history:
            return {}
        
        history = self.opponent_history[opponent_name]
        
        # Calculate preferences
        total_spells = len(history['spells_played'])
        if total_spells == 0:
            return {}
        
        analysis = {
            'preferred_elements': sorted(history['elements_used'].items(), 
                                       key=lambda x: x[1], reverse=True),
            'preferred_types': sorted(history['spell_types_used'].items(), 
                                    key=lambda x: x[1], reverse=True),
            'aggression_level': history['spell_types_used'].get('attack', 0) / total_spells,
            'defensive_level': history['spell_types_used'].get('response', 0) / total_spells,
            'support_level': (history['spell_types_used'].get('remedy', 0) + 
                            history['spell_types_used'].get('boost', 0)) / total_spells,
            'recent_spells': history['spells_played'][-3:]  # Last 3 spells
        }
        
        return analysis