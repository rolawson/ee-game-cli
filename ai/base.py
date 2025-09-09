"""Base AI class for all AI strategies"""

from abc import ABC, abstractmethod
import json
import os


class BaseAI(ABC):
    """Base class for all AI strategies"""
    
    # Class variable to store element categories (loaded once)
    _element_categories = None
    
    def __init__(self):
        self.engine = None  # Will be set by GameEngine
        self.opponent_history = {}  # Track what opponents have played
        self.opponent_drafted_elements = {}  # Track which elements opponents drafted
        self._load_element_categories()
        self.element_win_rates = self._load_element_win_rates()
    
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
                    'cards_discarded': 0,
                    'known_sets': [],  # Track which complete sets they have
                    'remaining_spells': {}  # Track unplayed spells by elephant
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
                        'clash': gs.clash_num,
                        'elephant': spell.card.elephant  # Add elephant for card counting
                    }
                    history['spells_played'].append(spell_info)
                    
                    # Update card counting
                    self.update_card_counting(player.name, spell.card.name)
                    
                    # Track element usage
                    element = spell.card.element
                    history['elements_used'][element] = history['elements_used'].get(element, 0) + 1
                    
                    # Track spell type usage
                    for spell_type in spell.card.types:
                        history['spell_types_used'][spell_type] = history['spell_types_used'].get(spell_type, 0) + 1
                    
                    # Card counting - identify complete sets
                    elephant = spell.card.elephant
                    if elephant not in history['known_sets']:
                        # Check if we've seen enough spells from this elephant to confirm they have the set
                        elephant_spells_seen = [s for s in history['spells_played'] 
                                               if 'elephant' in s and s['elephant'] == elephant]
                        if len(elephant_spells_seen) >= 2:  # Seen 2+ spells = they have the whole set
                            history['known_sets'].append(elephant)
                            # Initialize remaining spells for this set
                            self._initialize_remaining_spells(history, elephant, gs)
    
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
    
    def _initialize_remaining_spells(self, history, elephant, gs):
        """Initialize the list of remaining spells for a known elephant set"""
        # Get all spells from this elephant from the game data
        all_spells_in_set = []
        for card_id, card in gs.all_cards.items():
            if card.elephant == elephant:
                all_spells_in_set.append(card.name)
        
        # Track which spells have been played
        played_spells = [s['name'] for s in history['spells_played'] 
                        if s.get('elephant') == elephant]
        
        # Calculate remaining spells
        history['remaining_spells'][elephant] = [spell for spell in all_spells_in_set 
                                                if spell not in played_spells]
    
    def get_remaining_spells(self, opponent_name, elephant=None):
        """Get list of spells opponent hasn't played yet"""
        if opponent_name not in self.opponent_history:
            return []
        
        history = self.opponent_history[opponent_name]
        
        if elephant:
            return history['remaining_spells'].get(elephant, [])
        else:
            # Return all remaining spells
            all_remaining = []
            for spells in history['remaining_spells'].values():
                all_remaining.extend(spells)
            return all_remaining
    
    def update_card_counting(self, opponent_name, played_spell_name):
        """Update card counting when a spell is played"""
        if opponent_name in self.opponent_history:
            history = self.opponent_history[opponent_name]
            # Remove from remaining spells
            for elephant, remaining in history['remaining_spells'].items():
                if played_spell_name in remaining:
                    remaining.remove(played_spell_name)
                    break
    
    def _load_element_categories(self):
        """Load element category data from JSON file"""
        if BaseAI._element_categories is None:
            try:
                # Try to find the element categories file
                current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                categories_path = os.path.join(current_dir, 'element_categories.json')
                
                if os.path.exists(categories_path):
                    with open(categories_path, 'r') as f:
                        BaseAI._element_categories = json.load(f)
                else:
                    # Fallback if file not found
                    BaseAI._element_categories = {"categories": {}}
            except Exception as e:
                # If loading fails, use empty categories
                BaseAI._element_categories = {"categories": {}}
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\\033[90m[AI-WARNING] Could not load element categories: {e}\\033[0m"
                    )
    
    def get_element_category(self, element):
        """Get the strategic category of an element"""
        for category_name, category_data in BaseAI._element_categories.get('categories', {}).items():
            if element in category_data.get('elements', []):
                return category_name
        return 'unknown'
    
    def get_element_synergy(self, element, spell_type):
        """Get synergy multiplier for element-spell type combination"""
        category = self.get_element_category(element)
        if category == 'unknown':
            return 1.0
        
        category_data = BaseAI._element_categories['categories'].get(category, {})
        synergies = category_data.get('synergies', {})
        return synergies.get(spell_type, 1.0)
    
    def get_element_draft_priority(self, element):
        """Get draft priority multiplier for an element's category"""
        category = self.get_element_category(element)
        if category == 'unknown':
            return 1.0
            
        category_data = BaseAI._element_categories['categories'].get(category, {})
        return category_data.get('draft_priority', 1.0)
    
    def _load_element_win_rates(self):
        """Load element win rate data from analytics"""
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            win_rates_path = os.path.join(current_dir, 'element_win_rates.json')
            
            if os.path.exists(win_rates_path):
                with open(win_rates_path, 'r') as f:
                    data = json.load(f)
                    return data
            else:
                return {'win_rates': {}, 'selection_rates': {}, 'total_games': 0}
        except Exception:
            return {'win_rates': {}, 'selection_rates': {}, 'total_games': 0}
    
    def get_element_win_rate(self, element):
        """Get win rate for an element from analytics data"""
        return self.element_win_rates.get('win_rates', {}).get(element, 0.5)
    
    def choose_draft_set(self, player, gs, available_sets):
        """Choose a spell set during drafting phase
        
        Args:
            player: The AI player drafting
            gs: Current game state
            available_sets: List of available spell sets to draft from
            
        Returns:
            The chosen spell set
        """
        # Track what elements other players have drafted
        self._update_opponent_draft_tracking(gs)
        
        # Default implementation - random choice
        # Subclasses should override with strategic choices
        import random
        return random.choice(available_sets)
    
    def choose_cards_to_keep(self, player, gs):
        """Choose which cards to keep at end of round
        
        Args:
            player: The AI player
            gs: Current game state
            
        Returns:
            List of cards to keep (empty list means discard all for new set)
        """
        # Default implementation - keep remedy cards if hurt, otherwise keep all
        if player.health / player.max_health < 0.7:
            # Keep remedy cards when hurt
            return [c for c in player.hand if 'remedy' in c.types]
        return player.hand  # Keep all cards by default
    
    def _update_opponent_draft_tracking(self, gs):
        """Track which elements opponents have drafted"""
        for p in gs.players:
            if p.name not in self.opponent_drafted_elements:
                self.opponent_drafted_elements[p.name] = []
            
            # Check discard pile for drafted elements
            drafted_elements = set()
            for card in p.discard_pile:
                drafted_elements.add(card.element)
            
            # Update tracked elements
            for element in drafted_elements:
                if element not in self.opponent_drafted_elements[p.name]:
                    self.opponent_drafted_elements[p.name].append(element)
    
    def get_opponent_elements(self, player_name):
        """Get list of elements an opponent has drafted"""
        return self.opponent_drafted_elements.get(player_name, [])
    
    def choose_cancellation_target(self, potential_targets, caster, gs, current_card):
        """Choose which spell to cancel from a list of potential targets
        
        Args:
            potential_targets: List of PlayedCard objects that can be cancelled
            caster: The player doing the cancelling
            gs: Current game state
            current_card: The card with the cancel effect
            
        Returns:
            The chosen target to cancel, or None if no good target
        """
        if not potential_targets:
            return None
            
        # Default implementation - pick highest priority enemy spell
        # Subclasses should override with smarter logic
        enemy_targets = [t for t in potential_targets if t.owner != caster]
        if enemy_targets:
            # Sort by priority (lower number = higher priority)
            priority_sorted = sorted(enemy_targets, 
                                   key=lambda s: int(s.card.priority) if str(s.card.priority).isdigit() else 99)
            return priority_sorted[0]
        return potential_targets[0] if potential_targets else None
    
    def _evaluate_spell_threat(self, spell, caster, gs):
        """Evaluate the threat level of a spell
        
        Returns a numeric threat score (higher = more threatening)
        """
        threat_score = 0
        card = spell.card
        owner = spell.owner
        
        # Priority gives base threat (lower priority = higher threat)
        priority = int(card.priority) if str(card.priority).isdigit() else 99
        threat_score += (10 - priority) * 2
        
        # Conjuries are more threatening (ongoing effects)
        if card.is_conjury:
            threat_score += 15
        
        # Calculate damage potential
        damage = self._calculate_spell_damage(card, owner, gs)
        threat_score += damage * 10
        
        # Spell types affect threat level
        if 'attack' in card.types:
            threat_score += 10
        if 'remedy' in card.types and owner.health < owner.max_health * 0.5:
            threat_score += 15  # High threat if they're low health
        if 'boost' in card.types:
            threat_score += 5
        
        # Check for weaken effects
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'weaken':
                value = action.get('parameters', {}).get('value', 0)
                threat_score += value * 15  # Weaken is very threatening
            elif isinstance(action, dict) and action.get('type') == 'bolster':
                value = action.get('parameters', {}).get('value', 0)
                threat_score += value * 8
        
        return threat_score
    
    def _calculate_spell_damage(self, card, owner, gs):
        """Calculate the potential damage from a spell"""
        damage = 0
        
        # Check resolve effects for damage
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict):
                if action.get('type') == 'damage':
                    damage += action.get('parameters', {}).get('value', 0)
                elif action.get('type') == 'damage_multi_target':
                    damage += action.get('parameters', {}).get('value', 0)
                elif action.get('type') == 'player_choice':
                    # Check choices for damage options
                    for option in action.get('options', []):
                        if option.get('type') == 'damage':
                            option_damage = option.get('parameters', {}).get('value', 0)
                            damage = max(damage, option_damage)
                elif action.get('type') == 'damage_per_spell':
                    # Estimate based on active spells
                    active_spells = [s for s in owner.board[gs.clash_num-1] if s.status == 'revealed']
                    spell_type = action.get('parameters', {}).get('spell_type', 'any')
                    if spell_type == 'any':
                        damage += len(active_spells)
                    else:
                        damage += len([s for s in active_spells if spell_type in s.card.types])
        
        return damage
    
    def _calculate_conditional_value(self, card, owner, gs):
        """Calculate the potential value including conditional effects"""
        base_value = self._calculate_spell_damage(card, owner, gs)
        
        # Check each effect's condition
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            cond_type = condition.get('type')
            
            if cond_type == 'spell_clashes_count':
                # For Turbulence-like spells
                required = condition.get('parameters', {}).get('count', 3)
                current_clashes = self._count_spell_clashes(card, owner, gs)
                turns_to_condition = required - current_clashes
                
                if turns_to_condition <= (4 - gs.clash_num):
                    # Can potentially meet condition
                    conditional_damage = self._extract_action_value(effect.get('action'))
                    value_modifier = 1.0 / (turns_to_condition + 1)  # Closer = better
                    base_value += conditional_damage * value_modifier
                    
            elif cond_type == 'if_caster_has_active_spell_of_type':
                # For Flow, Ignite, Defend, Besiege
                spell_type = condition.get('parameters', {}).get('spell_type', 'any')
                count_needed = condition.get('parameters', {}).get('count', 1)
                
                # Check if we can meet this condition
                type_cards_in_hand = sum(1 for c in owner.hand if spell_type in c.types or spell_type == 'any')
                if type_cards_in_hand >= count_needed:
                    conditional_value = self._extract_action_value(effect.get('action'))
                    base_value += conditional_value * 0.8  # High probability
                    
            elif cond_type == 'if_spell_previously_resolved_this_round':
                # For Flow's past clash bonus
                if gs.clash_num > 1:  # Not first clash
                    conditional_value = self._extract_action_value(effect.get('action'))
                    # Check if this spell could have been played earlier
                    if card.notfirst == 0 or gs.clash_num > 2:
                        base_value += conditional_value * 0.6
                        
        return base_value
    
    def _count_spell_clashes(self, card, owner, gs):
        """Count how many clashes this spell has been in"""
        clash_count = 0
        
        # Check current board
        for player in gs.players:
            if player.name == owner.name:
                for clash_idx, clash_spells in enumerate(player.board):
                    for spell in clash_spells:
                        if spell.card.id == card.id:
                            clash_count += 1
                            break
        
        return clash_count
    
    def _extract_action_value(self, action):
        """Extract numeric value from an action (damage, heal, etc)"""
        if isinstance(action, dict):
            action_type = action.get('type')
            if action_type == 'damage':
                return action.get('parameters', {}).get('value', 0)
            elif action_type == 'heal':
                return action.get('parameters', {}).get('value', 0)
            elif action_type == 'bolster':
                return action.get('parameters', {}).get('value', 0) * 0.5  # Less valuable than damage
            elif action_type == 'weaken':
                return action.get('parameters', {}).get('value', 0) * 0.7
            elif action_type == 'player_choice':
                # Return the best option value
                max_value = 0
                for option in action.get('options', []):
                    option_value = self._extract_action_value(option)
                    max_value = max(max_value, option_value)
                return max_value
        elif isinstance(action, list):
            # Multiple actions
            total = 0
            for sub_action in action:
                total += self._extract_action_value(sub_action)
            return total
        return 0