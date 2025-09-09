"""Expert AI - Extreme strategic planning and multi-turn analysis"""

import json
import os
import random
from collections import defaultdict
from .base import BaseAI


class ExpertAI(BaseAI):
    """Expert difficulty - overthinks everything, plans multiple turns ahead"""
    
    def __init__(self):
        super().__init__()
        self.win_rate_data = self._load_win_rate_data()
        self.current_player = None  # Track current player for analysis
        self.threat_data = self._load_threat_data()
        self.spell_database = self._build_spell_database()
    
    def _load_win_rate_data(self):
        """Load win rate data from JSON file"""
        try:
            data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'element_win_rates.json')
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return None
    
    def _select_card(self, player, gs, valid_indices):
        """Select card with extreme analysis and future planning"""
        self.current_player = player  # Set current player for analysis
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] {player.name} initiating deep analysis...\033[0m"
            )
        
        # Build a comprehensive game plan
        game_plan = self._build_multi_turn_plan(player, gs)
        
        best_score = float('-inf')
        best_index = valid_indices[0]
        
        for idx in valid_indices:
            card = player.hand[idx]
            score = 0
            
            # 1. Immediate tactical evaluation (now with context-aware damage)
            score += self._evaluate_immediate_tactics(card, player, gs) * 0.15
            
            # 2. Multi-turn strategic value
            score += self._evaluate_strategic_value(card, player, gs, game_plan) * 0.15
            
            # 3. Future combo potential
            score += self._evaluate_future_combos(card, player, gs) * 0.15
            
            # 4. Same-clash combo potential
            score += self._evaluate_clash_combo_potential(card, player, gs) * 0.15
            
            # 5. Context-aware damage efficiency
            score += self._evaluate_damage_efficiency(card, player, gs) * 0.10
            
            # 6. Response threat evaluation (NEW)
            # Increase weight when health is low or card is extra vulnerable
            response_weight = 0.20
            if player.health <= 5:
                response_weight = 0.30
            if card.is_conjury:
                response_weight += 0.15  # Conjuries need extra caution
            if 'attack' in card.types and 'boost' in card.types:
                response_weight += 0.10  # Multi-type cards are risky
                
            response_threat = self._evaluate_response_threat_for_attack(card, player, gs)
            score += response_threat * response_weight
            
            # Log if we're avoiding due to responses
            if response_threat < -50 and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {card.name} has high response risk ({response_threat:.0f})\033[0m"
                )
            
            # 7. Board state synergy evaluation (NEW)
            score += self._evaluate_board_state_synergy(card, player, gs) * 0.15
            
            # 8. Conditional spell timing evaluation
            if self._has_conditional_effects(card):
                condition_score = self._evaluate_condition_timing(card, player, gs)
                score += condition_score * 0.10
                if condition_score > 50 and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-EXPERT] {card.name} has good condition timing (+{condition_score})\033[0m"
                    )
            
            # Log extensive analysis
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {card.name} - Total Score: {score:.1f}\033[0m"
                )
            
            if score > best_score:
                best_score = score
                best_index = idx
        
        chosen_card = player.hand[best_index]
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Final choice: {chosen_card.name} (Score: {best_score:.1f})\033[0m"
            )
            
            # Log if we avoided attacks due to response threats
            if player.health <= 5 and 'attack' not in chosen_card.types:
                attack_options = [player.hand[i] for i in valid_indices if 'attack' in player.hand[i].types]
                if attack_options:
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-EXPERT] Avoided {len(attack_options)} attack options due to low health ({player.health} HP) and response threats\033[0m"
                    )
        
        return best_index
    
    def _build_multi_turn_plan(self, player, gs):
        """Build a comprehensive multi-turn strategy"""
        plan = {
            'win_condition': self._identify_win_condition(player, gs),
            'enemy_threats': self._analyze_all_enemy_threats(player, gs),
            'combo_sequences': self._identify_combo_sequences(player, gs),
            'resource_management': self._plan_resource_usage(player, gs),
            'timing_windows': self._identify_critical_timings(player, gs),
            'condition_setups': self._plan_condition_setups(player, gs)
        }
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Win condition: {plan['win_condition']}\033[0m"
            )
        
        return plan
    
    def _identify_win_condition(self, player, gs):
        """Determine the primary path to victory"""
        # Analyze both players' states
        enemy = next(p for p in gs.players if p != player)
        
        # Calculate damage potential
        damage_potential = sum(self._estimate_card_damage(c) for c in player.hand)
        healing_potential = sum(self._estimate_card_healing(c) for c in player.hand)
        
        # Determine win condition
        if enemy.health <= damage_potential * 0.5:
            return 'rush'  # Can win quickly
        elif player.health < enemy.health and damage_potential > healing_potential:
            return 'aggressive_tempo'  # Need to pressure
        elif player.health <= player.max_health * 0.4:
            return 'stabilize_first'  # Must heal and defend
        elif any(c.is_conjury for c in player.hand) and gs.clash_num <= 2:
            return 'conjury_control'  # Establish board control
        else:
            return 'value_grind'  # Win through card advantage
    
    def _analyze_all_enemy_threats(self, player, gs):
        """Deep analysis of all potential enemy threats"""
        threats = {
            'immediate': [],
            'next_turn': [],
            'future': [],
            'combo_potential': []
        }
        
        # Analyze visible enemy spells
        for enemy in gs.players:
            if enemy == player:
                continue
                
            # Check board state
            for clash_idx, clash_spells in enumerate(enemy.board):
                for spell in clash_spells:
                    if spell.status == 'revealed':
                        threat_level = self._assess_threat_level(spell, clash_idx, gs)
                        if clash_idx == gs.clash_num - 1:
                            threats['immediate'].append((spell, threat_level))
                        elif clash_idx == gs.clash_num:
                            threats['next_turn'].append((spell, threat_level))
                        else:
                            threats['future'].append((spell, threat_level))
        
        # Predict enemy hand threats based on remaining cards
        remaining_enemy_cards = self.get_remaining_spells(enemy.name)
        for card_name in remaining_enemy_cards:
            # Estimate threat based on known spell data
            estimated_threat = self._estimate_spell_threat(card_name)
            if estimated_threat > 50:
                threats['combo_potential'].append(card_name)
        
        return threats
    
    def _identify_combo_sequences(self, player, gs):
        """Identify all possible combo sequences across multiple turns"""
        combos = []
        
        # Check every possible 2-3 card sequence
        hand_cards = player.hand[:]
        board_cards = []
        
        for clash_list in player.board:
            for spell in clash_list:
                if spell.status == 'revealed':
                    board_cards.append(spell.card)
        
        all_available = hand_cards + board_cards
        
        # 2-card combos
        for i, card1 in enumerate(all_available):
            for j, card2 in enumerate(all_available):
                if i != j:
                    synergy = self._calculate_synergy(card1, card2, gs)
                    if synergy > 50:
                        combos.append({
                            'cards': [card1.name, card2.name],
                            'synergy': synergy,
                            'timing': self._optimal_combo_timing(card1, card2, gs)
                        })
        
        # 3-card combos (limit to avoid exponential complexity)
        if len(all_available) <= 6:
            for i, card1 in enumerate(all_available):
                for j, card2 in enumerate(all_available):
                    for k, card3 in enumerate(all_available):
                        if i != j and i != k and j != k:
                            synergy = self._calculate_triple_synergy(card1, card2, card3, gs)
                            if synergy > 80:
                                combos.append({
                                    'cards': [card1.name, card2.name, card3.name],
                                    'synergy': synergy,
                                    'timing': 'complex'
                                })
        
        return sorted(combos, key=lambda x: x['synergy'], reverse=True)[:5]
    
    def _plan_resource_usage(self, player, gs):
        """Plan optimal resource usage across the game"""
        return {
            'hand_size_targets': {
                'current': len(player.hand),
                'ideal_by_round': max(2, 5 - gs.round_num),
                'discard_priority': self._rank_cards_for_discard(player.hand)
            },
            'health_thresholds': {
                'danger': 2,
                'caution': player.max_health * 0.4,
                'comfortable': player.max_health * 0.7
            },
            'spell_slot_allocation': {
                'clash_1': 'setup/conjury',
                'clash_2': 'pressure/response',
                'clash_3': 'combo/advance',
                'clash_4': 'finisher/cleanup'
            }
        }
    
    def _identify_critical_timings(self, player, gs):
        """Identify key timing windows for optimal play"""
        timings = []
        
        # Check for "must act now" situations
        if any(p.health <= 3 for p in gs.players):
            timings.append('lethal_window')
        
        if gs.clash_num == 1 and any(c.is_conjury for c in player.hand):
            timings.append('conjury_opportunity')
        
        if gs.clash_num <= 2 and self._has_advance_combo(player):
            timings.append('advance_setup_window')
        
        if len(player.hand) <= 2 and gs.clash_num >= 3:
            timings.append('resource_critical')
        
        return timings
    
    def _evaluate_immediate_tactics(self, card, player, gs):
        """Enhanced tactical evaluation with context-aware damage assessment"""
        score = 0
        
        # Basic type values with context
        if 'attack' in card.types:
            # Value attacks based on enemy health and defenses
            enemy = next(p for p in gs.players if p != player)
            
            # Use context-aware damage calculation including conditional effects
            damage = self._calculate_conditional_value(card, player, gs)
            static_damage = self._estimate_card_damage(card)
            
            # Log if context damage differs significantly
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and abs(damage - static_damage) > 1:
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {card.name} - Static DMG: {static_damage}, Context DMG: {damage:.1f}\033[0m"
                )
            
            if enemy.health <= damage:
                score += 200  # Lethal
            elif enemy.health <= damage * 2:
                score += 100  # Near lethal
            else:
                score += 30 + (damage * 10)
            
            # Consider weakening as pseudo-damage for long-term value
            weaken = self._estimate_card_weaken(card, player, gs)
            if weaken > 0:
                score += self._evaluate_weaken_timing(weaken, enemy, gs)
            
            # Bonus for multi-turn damage (advance effects)
            if card.advance_effects and gs.clash_num < 4:
                future_damage = self._estimate_card_damage_in_context(card, player, gs, gs.clash_num + 1)
                score += future_damage * 5
            
            # Check for enemy responses with higher penalty for vulnerable cards
            enemy_responses = self._count_enemy_responses(enemy, gs)
            response_penalty = enemy_responses * 15
            
            # Extra penalty for conjuries and multi-type cards
            if card.is_conjury:
                response_penalty *= 2
            if 'boost' in card.types:  # Attack + Boost
                response_penalty *= 1.5
                
            score -= response_penalty
        
        if 'remedy' in card.types:
            healing = self._estimate_card_healing(card)
            health_deficit = player.max_health - player.health
            
            if player.health <= 2:
                score += 150  # Critical healing
            elif health_deficit >= healing:
                score += healing * 20  # Efficient healing
            else:
                score += health_deficit * 10  # Overhealing penalty
        
        if 'response' in card.types:
            # Complex response evaluation
            trigger_chance = self._calculate_response_trigger_chance(card, player, gs)
            score += trigger_chance
        
        if card.is_conjury:
            # Conjuries are complex - consider protection and timing
            if gs.clash_num <= 2:
                score += 80
            else:
                score += 40
            
            # Check if we can protect it
            if self._has_protection(player):
                score += 30
        
        
        # Priority considerations
        if card.priority == 'A':
            score += 10 * (4 - gs.clash_num)  # Advance priority scales with remaining clashes
        elif str(card.priority).isdigit():
            priority_val = int(card.priority)
            if priority_val <= 2:
                score += 30  # Fast spells are valuable
        
        return score
    
    def _evaluate_strategic_value(self, card, player, gs, game_plan):
        """Evaluate card's fit into overall strategy"""
        score = 0
        
        # Match card to win condition
        win_con = game_plan['win_condition']
        
        if win_con == 'rush' and 'attack' in card.types:
            score += 100
        elif win_con == 'stabilize_first' and 'remedy' in card.types:
            score += 120
        elif win_con == 'conjury_control' and card.is_conjury:
            score += 110
        elif win_con == 'aggressive_tempo' and card.priority in ['1', '2']:
            score += 90
        elif win_con == 'value_grind' and ('boost' in card.types or 'recall' in str(card.resolve_effects)):
            score += 95
        
        # Check combo participation
        for combo in game_plan['combo_sequences']:
            if card.name in combo['cards']:
                score += combo['synergy'] * 0.5
                if combo['timing'] == gs.clash_num:
                    score += 50  # Perfect timing
        
        # Resource management alignment
        resource_plan = game_plan['resource_management']
        if len(player.hand) > resource_plan['hand_size_targets']['ideal_by_round']:
            # We have excess cards - value expensive/powerful plays
            if card.priority in ['3', '4', 'A']:
                score += 30
        
        # Threat interaction
        immediate_threats = game_plan['enemy_threats']['immediate']
        if immediate_threats:
            if 'cancel' in str(card.resolve_effects):
                score += 60
            if 'response' in card.types and self._counters_threat(card, immediate_threats[0][0]):
                score += 80
        
        return score
    
    def _evaluate_future_combos(self, card, player, gs):
        """Evaluate future combo potential in extreme detail"""
        score = 0
        
        # Check what this enables next turn
        for other_card in player.hand:
            if other_card == card:
                continue
                
            # Direct synergies
            synergy = self._calculate_synergy(card, other_card, gs)
            if synergy > 30:
                score += synergy * 0.7
                
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-EXPERT] {card.name} → {other_card.name} synergy: {synergy}\033[0m"
                    )
        
        # Check advance patterns
        if 'advance' in str(card.advance_effects):
            # This card will advance - check if we have advance synergies
            advance_payoffs = sum(1 for c in player.hand 
                                if 'if_spell_advanced' in str(c.resolve_effects))
            score += advance_payoffs * 40
        
        if 'if_spell_advanced' in str(card.resolve_effects):
            # This card needs to advance - check if we can enable it
            advance_enablers = sum(1 for c in player.hand 
                                 if 'advance' in str(c.resolve_effects + c.advance_effects))
            if gs.clash_num < 3:  # Still time to advance
                score += advance_enablers * 45
        
        # Element stacking bonuses
        same_element_count = sum(1 for c in player.hand if c.element == card.element)
        if same_element_count >= 2:
            score += same_element_count * 15
        
        return score
    
    def _calculate_synergy(self, card1, card2, gs):
        """Calculate synergy between two cards"""
        synergy = 0
        
        # Type synergies
        if 'boost' in card1.types and 'attack' in card2.types:
            synergy += 40
        if 'response' in card1.types and 'attack' in card2.types:
            synergy += 35
        if 'remedy' in card1.types and 'boost' in card2.types:
            synergy += 30
        
        # Specific effect synergies
        effects1 = str(card1.resolve_effects) + str(card1.advance_effects)
        effects2 = str(card2.resolve_effects) + str(card2.advance_effects)
        
        # Advance synergies
        if 'advance' in effects1 and 'if_spell_advanced' in effects2:
            synergy += 60
        if 'advance' in effects2 and 'if_spell_advanced' in effects1:
            synergy += 60
        
        # Spell type requirements
        if 'if_caster_has_active_spell_of_type' in effects2:
            for spell_type in card1.types:
                if spell_type in effects2:
                    synergy += 50
        
        # Element synergies
        if card1.element == card2.element:
            synergy += 20
        
        # Priority synergies (fast + slow can be good)
        if str(card1.priority).isdigit() and str(card2.priority).isdigit():
            p1 = int(card1.priority)
            p2 = int(card2.priority)
            if abs(p1 - p2) >= 2:
                synergy += 15  # Speed differential can be tactical
        
        return synergy
    
    def _calculate_triple_synergy(self, card1, card2, card3, gs):
        """Calculate three-card combo synergy"""
        # Pairwise synergies
        synergy = 0
        synergy += self._calculate_synergy(card1, card2, gs) * 0.5
        synergy += self._calculate_synergy(card2, card3, gs) * 0.5
        synergy += self._calculate_synergy(card1, card3, gs) * 0.5
        
        # Triple combo bonuses
        types = set()
        types.update(card1.types)
        types.update(card2.types)
        types.update(card3.types)
        
        if len(types) >= 4:  # Diverse combo
            synergy += 30
        
        # All same element mega-combo
        if card1.element == card2.element == card3.element:
            synergy += 40
        
        return synergy
    
    def _optimal_combo_timing(self, card1, card2, gs):
        """Determine optimal timing for a two-card combo"""
        # Check priority order
        p1 = 99 if card1.priority == 'A' else int(card1.priority)
        p2 = 99 if card2.priority == 'A' else int(card2.priority)
        
        if p1 < p2:
            # card1 resolves first - good for setup
            return gs.clash_num
        elif p2 < p1:
            # card2 resolves first - might need to play card2 first
            return max(1, gs.clash_num - 1)
        else:
            # Same priority - check for advance patterns
            if 'advance' in str(card1.advance_effects):
                return gs.clash_num  # Play now to advance later
            return gs.clash_num + 1
    
    def _estimate_card_damage(self, card):
        """Estimate damage output of a card"""
        damage = 0
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'damage':
                damage += action.get('parameters', {}).get('value', 0)
        return damage
    
    def _estimate_card_healing(self, card):
        """Estimate healing output of a card"""
        healing = 0
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'heal':
                healing += action.get('parameters', {}).get('value', 0)
        return healing
    
    def _estimate_card_damage_in_context(self, card, player, gs, clash_num=None):
        """Estimate damage with board state context"""
        if clash_num is None:
            clash_num = gs.clash_num
        
        damage = 0
        
        # Calculate damage from resolve effects
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict):
                damage += self._calculate_action_damage(action, card, player, gs, clash_num)
            elif isinstance(action, list):
                # Handle action arrays
                for sub_action in action:
                    if isinstance(sub_action, dict):
                        damage += self._calculate_action_damage(sub_action, card, player, gs, clash_num)
        
        # Also check advance effects if we expect to advance
        if clash_num < 4 and card.advance_effects:
            for effect in card.advance_effects:
                action = effect.get('action', {})
                if isinstance(action, dict):
                    # Only count if we expect to advance (70% confidence)
                    damage += self._calculate_action_damage(action, card, player, gs, clash_num + 1) * 0.7
        
        return damage
    
    def _calculate_action_damage(self, action, card, player, gs, clash_num):
        """Calculate damage for a specific action considering board state"""
        action_type = action.get('type')
        params = action.get('parameters', {})
        
        if action_type == 'damage':
            return params.get('value', 0)
        
        elif action_type == 'damage_multi_target':
            # Multi-target damage
            return params.get('value', 0)
        
        elif action_type == 'damage_per_spell':
            # Count expected active spells
            spell_type = params.get('spell_type', 'any')
            exclude_self = params.get('exclude_self', False)
            
            # Current active spells
            active_count = 0
            if player and hasattr(player, 'board'):
                for spell in player.board[clash_num - 1]:
                    if spell.status == 'revealed':
                        if spell_type == 'any' or spell_type in spell.card.types:
                            active_count += 1
            
            # Estimate additional spells we might play
            if clash_num == gs.clash_num and player and hasattr(player, 'hand'):
                # Current clash - add expected plays from hand
                for other_card in player.hand:
                    if other_card != card:  # Don't count self twice
                        if spell_type == 'any' or spell_type in other_card.types:
                            # 50% chance we play it
                            active_count += 0.5
            
            if exclude_self:
                active_count = max(0, active_count - 1)
            
            return active_count
        
        elif action_type == 'damage_per_enemy_spell_type':
            # Estimate enemy spells
            spell_type = params.get('spell_type', 'any')
            enemy_count = 0
            
            for enemy in gs.players:
                if enemy != player:
                    # Count current enemy spells
                    for spell in enemy.board[clash_num - 1]:
                        if spell.status == 'revealed' and spell_type in spell.card.types:
                            enemy_count += 1
                    
                    # Predict future enemy spells based on history
                    if clash_num == gs.clash_num and hasattr(self, 'opponent_history'):
                        history = self.analyze_opponent_patterns(enemy.name)
                        type_preference = dict(history.get('preferred_types', []))
                        if spell_type in type_preference:
                            # Add expected value based on preference
                            enemy_count += type_preference[spell_type] * 0.3
            
            return enemy_count
        
        elif action_type == 'damage_per_spell_from_other_clashes':
            # Count spells in other clashes (like Impact)
            count = 0
            for i in range(4):
                if i != clash_num - 1:
                    for p in gs.players:
                        for spell in p.board[i]:
                            if spell.status == 'revealed':
                                count += 1
            return count
        
        elif action_type == 'damage_equal_to_enemy_attack_damage':
            # Familiar - calculate enemy attack spell damage
            total_damage = 0
            for enemy in gs.players:
                if enemy != player:
                    for spell in enemy.board[clash_num - 1]:
                        if spell.status == 'revealed' and 'attack' in spell.card.types:
                            # Recursively calculate that spell's damage
                            total_damage += self._estimate_card_damage(spell.card)
            return total_damage
        
        elif action_type == 'player_choice':
            # For choices, evaluate the best damage option
            max_damage = 0
            for option in action.get('options', []):
                if isinstance(option, dict):
                    option_damage = self._calculate_action_damage(option, card, player, gs, clash_num)
                    max_damage = max(max_damage, option_damage)
            return max_damage
        
        elif action_type == 'sequence':
            # For sequences, sum up all damage actions
            total_damage = 0
            for seq_action in action.get('actions', []):
                if isinstance(seq_action, dict):
                    total_damage += self._calculate_action_damage(seq_action, card, player, gs, clash_num)
            return total_damage
        
        return 0
    
    def _estimate_card_weaken(self, card, player, gs, clash_num=None):
        """Estimate weakening potential of a card"""
        if clash_num is None:
            clash_num = gs.clash_num
        
        weaken = 0
        
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict):
                weaken += self._calculate_action_weaken(action, card, player, gs, clash_num)
            elif isinstance(action, list):
                for sub_action in action:
                    if isinstance(sub_action, dict):
                        weaken += self._calculate_action_weaken(sub_action, card, player, gs, clash_num)
        
        return weaken
    
    def _calculate_action_weaken(self, action, card, player, gs, clash_num):
        """Calculate weakening for a specific action"""
        action_type = action.get('type')
        params = action.get('parameters', {})
        
        if action_type == 'weaken':
            return params.get('value', 0)
        
        elif action_type == 'weaken_per_spell':
            # Similar calculation to damage_per_spell
            spell_type = params.get('spell_type', 'any')
            exclude_self = params.get('exclude_self', False)
            
            # Use same logic as damage_per_spell
            return self._calculate_action_damage(
                {'type': 'damage_per_spell', 'parameters': params}, 
                card, player, gs, clash_num
            )
        
        elif action_type == 'player_choice':
            # Check options for weaken
            max_weaken = 0
            for option in action.get('options', []):
                if isinstance(option, dict):
                    option_weaken = self._calculate_action_weaken(option, card, player, gs, clash_num)
                    max_weaken = max(max_weaken, option_weaken)
            return max_weaken
        
        elif action_type == 'sequence':
            # Sum up weaken in sequences
            total_weaken = 0
            for seq_action in action.get('actions', []):
                if isinstance(seq_action, dict):
                    total_weaken += self._calculate_action_weaken(seq_action, card, player, gs, clash_num)
            return total_weaken
        
        return 0
    
    def _evaluate_weaken_timing(self, weaken_amount, enemy, gs):
        """Evaluate how valuable weakening is at this point"""
        score = 0
        
        # Weakening is more valuable when:
        # 1. Enemy has high max health
        if enemy.max_health > 5:
            score += weaken_amount * 15
        else:
            score += weaken_amount * 10
        
        # 2. We're planning a longer game
        if hasattr(self, 'win_condition') and self.win_condition == 'value_grind':
            score += weaken_amount * 10
        
        # 3. Enemy is at full health (reduces their effective healing)
        if enemy.health == enemy.max_health:
            score += weaken_amount * 5
        
        # 4. Early in the round (more time to benefit)
        score += weaken_amount * (5 - gs.clash_num)
        
        return score
    
    def _rank_cards_for_discard(self, hand):
        """Rank cards by discard priority (lower = discard first)"""
        rankings = []
        for card in hand:
            priority = 50  # Base priority
            
            # Adjust based on card quality
            if 'attack' in card.types:
                priority += 20
            if 'remedy' in card.types:
                priority += 25
            if card.is_conjury:
                priority += 30
            if 'response' in card.types:
                priority += 15
            
            # Low priority cards are more discardable
            if card.priority in ['4', 'A']:
                priority -= 10
            
            rankings.append((card, priority))
        
        return sorted(rankings, key=lambda x: x[1])
    
    
    def _has_advance_combo(self, player):
        """Check if player has cards that combo with advancing"""
        advance_enablers = any('advance' in str(c.resolve_effects + c.advance_effects) 
                             for c in player.hand)
        advance_payoffs = any('if_spell_advanced' in str(c.resolve_effects)
                            for c in player.hand)
        return advance_enablers and advance_payoffs
    
    def _count_enemy_responses(self, enemy, gs):
        """Count potential enemy response spells"""
        count = 0
        for clash_list in enemy.board:
            for spell in clash_list:
                if spell.status == 'revealed' and 'response' in spell.card.types:
                    count += 1
        return count
    
    def _calculate_response_trigger_chance(self, card, player, gs):
        """Calculate likelihood of response trigger"""
        score = 0
        
        # Analyze response conditions
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            cond_type = condition.get('type')
            
            if cond_type == 'if_enemy_has_active_spell_of_type':
                # Check current enemy board
                params = condition.get('parameters', {})
                spell_type = params.get('spell_type')
                enemy_has = self._enemy_has_spell_type(spell_type, gs)
                if enemy_has:
                    score += 80
                else:
                    # Predict likelihood
                    score += self._predict_enemy_spell_type(spell_type) * 0.5
            
            elif cond_type == 'if_spell_advanced_this_turn':
                # Check our advance capability
                if gs.clash_num < 4:
                    score += 60
            
            elif cond_type == 'if_caster_has_active_spell_of_type':
                # Check our board and hand
                params = condition.get('parameters', {})
                spell_type = params.get('spell_type')
                if self._we_have_spell_type(spell_type, player, gs):
                    score += 90
        
        return score
    
    def _has_protection(self, player):
        """Check if we have protection spells available"""
        protection_keywords = ['protect', 'prevent', 'cancel', 'immune']
        for card in player.hand:
            effects_str = str(card.resolve_effects) + str(card.advance_effects)
            if any(keyword in effects_str.lower() for keyword in protection_keywords):
                return True
        return False
    
    def _evaluate_clash_combo_potential(self, card, player, gs):
        """Evaluate how well this card combos with other cards we might play this clash"""
        score = 0
        
        # Check other cards in hand for same-clash combos
        for other_card in player.hand:
            if other_card == card:
                continue
            
            # Check if other_card boosts this card's damage
            if 'boost' in other_card.types and 'attack' in card.types:
                # Estimate bonus damage from having a boost spell active
                base_damage = self._estimate_card_damage(card)
                context_damage = self._estimate_card_damage_in_context(card, player, gs)
                bonus_damage = max(0, context_damage - base_damage) * 0.3
                score += bonus_damage * 10
            
            # Check if this card has damage_per_spell and other card matches
            for effect in card.resolve_effects:
                action = effect.get('action', {})
                if isinstance(action, dict) and action.get('type') == 'damage_per_spell':
                    params = action.get('parameters', {})
                    spell_type = params.get('spell_type', 'any')
                    if spell_type == 'any' or spell_type in other_card.types:
                        score += 15  # Bonus for each potential combo piece
                elif isinstance(action, dict) and action.get('type') == 'weaken_per_spell':
                    params = action.get('parameters', {})
                    spell_type = params.get('spell_type', 'any')
                    if spell_type == 'any' or spell_type in other_card.types:
                        score += 12  # Weaken combos are valuable too
            
            # Check condition synergies
            if self._cards_have_condition_synergy(card, other_card):
                score += 25
            
            # Check for protection synergies (protect our valuable spells)
            if card.is_conjury and self._provides_protection(other_card):
                score += 30
            
            # Check for advance synergies within same clash
            if 'advance' in str(other_card.resolve_effects) and card.advance_effects:
                score += 20
        
        # Bonus if we have multiple cards that work together
        synergistic_cards = 0
        for other_card in player.hand:
            if other_card != card and self._cards_have_any_synergy(card, other_card):
                synergistic_cards += 1
        
        if synergistic_cards >= 2:
            score += 20  # Multi-card combo bonus
        
        return score
    
    def _cards_have_condition_synergy(self, card1, card2):
        """Check if two cards have conditions that work well together"""
        c1_str = str(card1.resolve_effects) + str(card1.advance_effects)
        c2_str = str(card2.resolve_effects) + str(card2.advance_effects)
        
        # Advance synergies
        if 'advance' in c1_str and 'if_spell_advanced' in c2_str:
            return True
        if 'advance' in c2_str and 'if_spell_advanced' in c1_str:
            return True
        
        # Spell type synergies
        if 'if_caster_has_active_spell_of_type' in c1_str:
            for spell_type in card2.types:
                if spell_type in c1_str:
                    return True
        if 'if_caster_has_active_spell_of_type' in c2_str:
            for spell_type in card1.types:
                if spell_type in c2_str:
                    return True
        
        # Protection synergies
        if card1.is_conjury and 'protect' in c2_str.lower():
            return True
        if card2.is_conjury and 'protect' in c1_str.lower():
            return True
        
        return False
    
    def _cards_have_any_synergy(self, card1, card2):
        """Quick check if cards have any synergy"""
        # Type combinations
        type_synergies = [
            ('boost', 'attack'),
            ('response', 'attack'),
            ('remedy', 'boost'),
            ('attack', 'attack')  # Multiple attacks can overwhelm
        ]
        
        for type1, type2 in type_synergies:
            if (type1 in card1.types and type2 in card2.types) or \
               (type2 in card1.types and type1 in card2.types):
                return True
        
        # Same element synergy
        if card1.element == card2.element:
            return True
        
        # Condition synergies
        return self._cards_have_condition_synergy(card1, card2)
    
    def _provides_protection(self, card):
        """Check if a card provides protection effects"""
        effects_str = str(card.resolve_effects) + str(card.advance_effects) + str(card.passive_effects)
        protection_keywords = ['protect', 'prevent', 'cancel', 'immune']
        return any(keyword in effects_str.lower() for keyword in protection_keywords)
    
    def _evaluate_damage_efficiency(self, card, player, gs):
        """Evaluate damage efficiency considering context vs static damage"""
        score = 0
        
        # Calculate both static and context damage
        static_damage = self._estimate_card_damage(card)
        context_damage = self._estimate_card_damage_in_context(card, player, gs)
        
        # Also consider weaken effects
        static_weaken = 0
        context_weaken = self._estimate_card_weaken(card, player, gs)
        
        # Combined effectiveness
        static_total = static_damage + (static_weaken * 0.7)  # Weaken is worth ~70% of damage
        context_total = context_damage + (context_weaken * 0.7)
        
        if static_total > 0:
            # Efficiency ratio - how much better is context damage?
            efficiency_ratio = context_total / static_total
            
            # Highly efficient cards get bonus points
            if efficiency_ratio > 2.0:  # More than double effectiveness
                score += 50
            elif efficiency_ratio > 1.5:  # 50% more effective
                score += 30
            elif efficiency_ratio > 1.2:  # 20% more effective
                score += 15
            
            # Log significant differences
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and efficiency_ratio > 1.3:
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {card.name} - Efficiency: {efficiency_ratio:.1f}x (Static: {static_total}, Context: {context_total:.1f})\033[0m"
                )
        
        # Bonus for scaling damage (damage_per_spell, etc)
        effects_str = str(card.resolve_effects) + str(card.advance_effects)
        if 'damage_per_spell' in effects_str or 'weaken_per_spell' in effects_str:
            score += 20
        
        # Bonus for multi-target damage
        if 'damage_multi_target' in effects_str:
            score += 15
        
        return score
    
    def _load_threat_data(self):
        """Load threat evaluation data from JSON"""
        try:
            threat_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spell_threats.json')
            if os.path.exists(threat_file):
                with open(threat_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        
        # Fallback to basic threat data
        return {
            'response_threats': {},
            'element_archetypes': {},
            'threat_evaluation_weights': {
                'damage_per_point': 10,
                'healing_reduction': 5,
                'cancel_threat': 50,
                'priority_advantage': 15,
                'lethal_threshold_multiplier': 3
            }
        }
    
    def _build_spell_database(self):
        """Build a database of all spells with their properties"""
        spell_db = {}
        
        # Load spell data
        try:
            spells_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spells.json')
            if os.path.exists(spells_file):
                with open(spells_file, 'r') as f:
                    spell_data = json.load(f)
                    
                for spell in spell_data:
                    spell_name = spell.get('card_name')
                    if spell_name:
                        # Extract key properties
                        spell_db[spell_name] = {
                            'element': spell.get('element'),
                            'priority': spell.get('priority'),
                            'types': spell.get('spell_types', []),
                            'is_conjury': spell.get('is_conjury', False),
                            'damage': self._extract_spell_damage(spell),
                            'healing': self._extract_spell_healing(spell),
                            'conditions': self._extract_spell_conditions(spell),
                            'effects': self._extract_spell_effects(spell)
                        }
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] Warning: Could not load spell database: {e}\033[0m"
                )
        
        return spell_db
    
    def _extract_spell_damage(self, spell_data):
        """Extract damage values from spell data"""
        total_damage = 0
        
        for effect in spell_data.get('resolve_effects', []):
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'damage':
                total_damage += action.get('parameters', {}).get('value', 0)
        
        return total_damage
    
    def _extract_spell_healing(self, spell_data):
        """Extract healing values from spell data"""
        total_healing = 0
        
        for effect in spell_data.get('resolve_effects', []):
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'heal':
                total_healing += action.get('parameters', {}).get('value', 0)
        
        return total_healing
    
    def _extract_spell_conditions(self, spell_data):
        """Extract condition types from spell data"""
        conditions = []
        
        for effect in spell_data.get('resolve_effects', []):
            condition = effect.get('condition', {})
            if condition:
                conditions.append(condition.get('type'))
        
        return conditions
    
    def _extract_spell_effects(self, spell_data):
        """Extract effect types from spell data"""
        effects = []
        
        for effect in spell_data.get('resolve_effects', []):
            action = effect.get('action', {})
            if isinstance(action, dict):
                effects.append(action.get('type'))
        
        return effects
    
    def _evaluate_response_threat_for_attack(self, card, player, gs):
        """Evaluate how dangerous enemy responses are to this attack spell"""
        # Check if card is vulnerable (attack, boost, or conjury)
        vulnerable_types = {'attack', 'boost'}
        is_vulnerable = bool(vulnerable_types.intersection(card.types)) or card.is_conjury
        
        if not is_vulnerable:
            return 0
        
        threat_score = 0
        weights = self.threat_data.get('threat_evaluation_weights', {})
        
        # Vulnerability multiplier based on card properties
        vulnerability_multiplier = 1.0
        if card.is_conjury:
            vulnerability_multiplier *= 2.0  # Conjuries are prime targets
        if 'attack' in card.types and 'boost' in card.types:
            vulnerability_multiplier *= 1.5  # Multi-type cards are extra vulnerable
        
        # Health-based multiplier for threat perception
        health_multiplier = 1.0
        if player.health <= 3:
            health_multiplier = 3.0  # Triple threat concern when we could die
        elif player.health <= 5:
            health_multiplier = 2.0  # Double threat concern when vulnerable
        
        # CRITICAL: Check already revealed enemy responses
        for enemy in gs.players:
            if enemy == player:
                continue
            
            # Check visible responses on the board
            for clash_idx, clash_list in enumerate(enemy.board):
                for spell in clash_list:
                    if spell.status == 'revealed' and 'response' in spell.card.types:
                        # This response is already on the board and will trigger!
                        immediate_threat = 50  # Base threat for visible response
                        
                        # Extra threat if it's in the current clash
                        if clash_idx == gs.clash_num - 1:
                            immediate_threat *= 2
                        
                        # Check if it specifically targets our card type
                        spell_str = str(spell.card.resolve_effects).lower()
                        if any(t in spell_str for t in card.types):
                            immediate_threat *= 1.5
                        
                        threat_score += immediate_threat * vulnerability_multiplier
                        
                        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                            self.engine.ai_decision_logs.append(
                                f"\033[90m[AI-EXPERT] WARNING: {spell.card.name} is already revealed! "
                                f"Threat to {card.name}: {immediate_threat * vulnerability_multiplier:.0f}\033[0m"
                            )
        
        # Then check potential responses from hand (existing logic)
        for enemy in gs.players:
            if enemy == player:
                continue
            
            # Get opponent's drafted elements
            enemy_elements = self.get_opponent_elements(enemy.name)
            
            # Analyze potential response threats from those elements
            for element in enemy_elements:
                element_threats = self._analyze_element_response_threats(element)
                
                for threat_info in element_threats:
                    # Check if this response could trigger against our attack
                    if self._could_response_trigger_against_attack(threat_info, card):
                        # Calculate threat impact
                        impact = self._calculate_generic_threat_impact(
                            threat_info, card, player, weights
                        )
                        
                        # Estimate likelihood based on game state
                        likelihood = self._estimate_threat_likelihood(
                            threat_info, enemy, gs
                        )
                        
                        threat_score += impact * likelihood
                        
                        if self.engine and hasattr(self.engine, 'ai_decision_logs') and impact > 20:
                            self.engine.ai_decision_logs.append(
                                f"\033[90m[AI-EXPERT] {card.name} vulnerable to {element} response "
                                f"(Impact: {impact:.1f}, Likelihood: {likelihood:.1%})\033[0m"
                            )
        
        # Apply health multiplier to the threat score
        threat_score *= health_multiplier
        
        # Check if our attack would be lethal to the enemy
        our_damage = self._estimate_card_damage_in_context(card, player, gs)
        for enemy in gs.players:
            if enemy != player and enemy.health <= our_damage:
                # If we can kill them, reduce threat concern by 50%
                threat_score *= 0.5
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-EXPERT] {card.name} could be lethal ({our_damage} dmg vs {enemy.health} hp) - accepting risk\033[0m"
                    )
                break
        
        return -threat_score  # Negative because threats reduce desirability
    
    def _analyze_element_response_threats(self, element):
        """Analyze what response threats an element might have"""
        threats = []
        
        # Look up all spells for this element in our database
        for spell_name, spell_info in self.spell_database.items():
            if spell_info.get('element') == element and 'response' in spell_info.get('types', []):
                # Classify the threat level based on properties
                threat_level = self._classify_response_threat(spell_info)
                
                if threat_level:
                    threats.append({
                        'spell_name': spell_name,
                        'spell_info': spell_info,
                        'threat_level': threat_level
                    })
        
        return threats
    
    def _classify_response_threat(self, spell_info):
        """Classify how threatening a response spell is"""
        response_threats = self.threat_data.get('response_threats', {})
        
        # Check each threat category
        for category, criteria in response_threats.items():
            features = criteria.get('identifying_features', {})
            
            # Check if spell matches this threat category
            matches = True
            
            # Check damage threshold
            if 'min_damage' in features:
                if spell_info.get('damage', 0) < features['min_damage']:
                    matches = False
            
            # Check spell types
            if 'spell_types' in features:
                spell_types = spell_info.get('types', [])
                if not any(t in spell_types for t in features['spell_types']):
                    matches = False
            
            # Check conditions
            if 'trigger_conditions' in features:
                conditions = spell_info.get('conditions', [])
                if not any(c in conditions for c in features['trigger_conditions']):
                    matches = False
            
            # Check effects
            if 'effects' in features:
                effects = spell_info.get('effects', [])
                if not any(e in effects for e in features['effects']):
                    matches = False
            
            if matches:
                return criteria.get('threat_level', 'medium')
        
        return None
    
    def _could_response_trigger_against_attack(self, threat_info, our_card):
        """Check if a response could trigger against our attack"""
        spell_info = threat_info.get('spell_info', {})
        conditions = spell_info.get('conditions', [])
        
        # Common response conditions that trigger on attacks
        attack_triggers = [
            'if_enemy_has_active_spell_of_type',  # Often checks for 'attack'
            'if_enemy_played_spell_this_clash',
            'if_any_spell_dealt_damage'
        ]
        
        # If it has attack-related conditions, it might trigger
        for condition in conditions:
            if any(trigger in condition for trigger in attack_triggers):
                return True
        
        # If it's a response with no conditions, it might be always active
        if not conditions and 'response' in spell_info.get('types', []):
            return True
        
        return False
    
    def _calculate_generic_threat_impact(self, threat_info, our_card, player, weights):
        """Calculate impact of a threat without hardcoding specific spells"""
        impact = 0
        spell_info = threat_info.get('spell_info', {})
        threat_level = threat_info.get('threat_level', 'medium')
        
        # Base impact from threat level
        level_impacts = {'high': 50, 'medium': 30, 'low': 10}
        impact += level_impacts.get(threat_level, 20)
        
        # Damage threat - use spell database info
        damage = spell_info.get('damage', 0)
        
        # For response spells, also check if they have conditional damage
        if 'response' in spell_info.get('types', []):
            # Response spells often have higher damage than regular attacks
            # Give them extra weight since they're reactive
            damage_multiplier = 1.5
        else:
            damage_multiplier = 1.0
            
        if damage > 0:
            damage_impact = damage * weights.get('damage_per_point', 10) * damage_multiplier
            
            # Extra impact if we're low health
            if player.health <= damage:
                damage_impact *= weights.get('lethal_threshold_multiplier', 3)
            elif player.health <= damage * 2:
                damage_impact *= 1.5
            
            impact += damage_impact
        
        # Healing reduction (enemy healing reduces our damage effectiveness)
        healing = spell_info.get('healing', 0)
        if healing > 0:
            impact += healing * weights.get('healing_reduction', 5)
        
        # Cancel/negate effects
        if any(e in spell_info.get('effects', []) for e in ['cancel', 'prevent', 'negate']):
            impact += weights.get('cancel_threat', 50)
        
        # Priority consideration
        their_priority = spell_info.get('priority', 99)
        our_priority = our_card.priority
        
        # Convert to comparable values
        their_p = 99 if their_priority == 'A' else int(their_priority)
        our_p = 99 if our_priority == 'A' else int(our_priority)
        
        if their_p < our_p:
            # They resolve first, more dangerous
            impact += weights.get('priority_advantage', 15)
        
        return impact
    
    def _estimate_threat_likelihood(self, threat_info, enemy, gs):
        """Estimate likelihood of enemy having/playing a threat"""
        spell_name = threat_info.get('spell_name')
        spell_info = threat_info.get('spell_info', {})
        
        # Base likelihood
        likelihood = 0.4  # 40% base chance
        
        # Increase if we've seen this spell before
        if self._has_played_spell(enemy.name, spell_name):
            likelihood = 0.7
        
        # Response spells are more likely to be saved for the right moment
        if 'response' in spell_info.get('types', []):
            # Players tend to hold response spells when facing attack-heavy opponents
            our_attack_count = sum(1 for c in self.current_player.hand if 'attack' in c.types)
            if our_attack_count >= 3:
                likelihood *= 1.3  # More likely to have responses ready
        
        # Adjust based on hand size
        if len(enemy.hand) >= 4:
            likelihood *= 1.2
        elif len(enemy.hand) <= 2:
            likelihood *= 0.7
        
        # Adjust based on game state
        if gs.clash_num >= 3:
            # Late game, more likely to have key spells
            likelihood *= 1.1
        
        # If we're low health, enemies are more likely to save damage responses
        if self.current_player and self.current_player.health <= 3:
            likelihood *= 1.2
        
        # Cap at reasonable bounds
        return min(0.9, max(0.1, likelihood))
    
    def _response_could_trigger(self, threat, our_card, us, enemy, gs):
        """Check if a response threat could trigger against our card"""
        condition = threat['condition']
        
        if condition == 'if_enemy_has_active_spell_of_type_attack':
            return 'attack' in our_card.types
        elif condition == 'if_enemy_has_active_spell_of_type_any':
            return True
        elif condition == 'if_caster_has_active_spell_of_type_response':
            # Check if enemy has response spells
            for spell in enemy.board[gs.clash_num - 1]:
                if spell.status == 'revealed' and 'response' in spell.card.types:
                    return True
        elif condition == 'if_caster_has_active_spell_of_type_remedy':
            # Check if enemy has remedy spells
            for spell in enemy.board[gs.clash_num - 1]:
                if spell.status == 'revealed' and 'remedy' in spell.card.types:
                    return True
        
        return False
    
    def _calculate_response_impact(self, threat, our_card, player):
        """Calculate how much impact a response threat has"""
        impact = 0
        
        # Direct damage to us
        damage = threat.get('damage', 0)
        if damage > 0:
            # More impact if we're low health
            if player.health <= damage:
                impact += 100  # Could be lethal
            elif player.health <= damage * 2:
                impact += 50  # Very dangerous
            else:
                impact += damage * 10
        
        # Enemy healing (reduces our damage effectiveness)
        healing = threat.get('healing', 0)
        if healing > 0:
            impact += healing * 5
        
        # Priority comparison
        threat_priority = threat['priority']
        our_priority = our_card.priority
        
        # Convert to comparable values
        threat_p_val = 99 if threat_priority == 'A' else int(threat_priority)
        our_p_val = 99 if our_priority == 'A' else int(our_priority)
        
        # If response resolves before us, it might cancel us
        if threat_p_val < our_p_val and 'cancel' in threat.get('effect', ''):
            impact += 50
        
        return impact
    
    def _has_played_spell(self, opponent_name, spell_name):
        """Check if opponent has played a specific spell before"""
        if opponent_name not in self.opponent_history:
            return False
        
        history = self.opponent_history[opponent_name]
        for spell_info in history['spells_played']:
            if spell_info['name'] == spell_name:
                return True
        
        return False
    
    def _assess_threat_level(self, spell, clash_idx, gs):
        """Assess threat level of an enemy spell"""
        threat = 0
        
        # Get the spell's owner for context
        spell_owner = None
        for player in gs.players:
            for board_spell in player.board[clash_idx]:
                if board_spell == spell:
                    spell_owner = player
                    break
        
        # Immediate threats with context-aware damage
        if 'attack' in spell.card.types:
            # Use context-aware damage for accurate threat assessment
            if spell_owner:
                damage = self._estimate_card_damage_in_context(spell.card, spell_owner, gs, clash_idx + 1)
            else:
                damage = self._estimate_card_damage(spell.card)
            
            threat += damage * 20
            
            # Extra threat if attack-boost that has advanced
            if 'boost' in spell.card.types and clash_idx < gs.clash_num - 1:
                # This is an advanced attack-boost, very dangerous
                threat += 30
        
        if spell.card.is_conjury:
            threat += 40
        
        if 'cancel' in str(spell.card.resolve_effects):
            threat += 35
        
        # Response threats
        if 'response' in spell.card.types:
            threat += 25
        
        # Boost threats (enemy setup)
        if 'boost' in spell.card.types and 'attack' not in spell.card.types:
            threat += 20
        
        # Timing multiplier
        if clash_idx == gs.clash_num - 1:
            threat *= 1.5  # Immediate threats
        elif clash_idx == gs.clash_num:
            threat *= 1.2  # Next turn threats
        
        # Advanced spell multiplier
        if spell.card.advance_effects and clash_idx < gs.clash_num - 1:
            threat *= 1.3  # Advanced spells are more threatening
        
        return threat
    
    def _estimate_spell_threat(self, spell_name):
        """Estimate threat level of a spell by name"""
        # This would need spell data, so we'll use heuristics
        threat_keywords = {
            'damage': 50,
            'destroy': 80,
            'cancel': 60,
            'discard': 40,
            'weaken': 45
        }
        
        threat = 0
        name_lower = spell_name.lower()
        for keyword, value in threat_keywords.items():
            if keyword in name_lower:
                threat += value
        
        return threat
    
    def _counters_threat(self, card, threat_spell):
        """Check if our card counters the threat"""
        # Response spells often counter attacks
        if 'response' in card.types and 'attack' in threat_spell.card.types:
            return True
        
        # Cancel effects counter anything
        if 'cancel' in str(card.resolve_effects):
            return True
        
        # Healing counters damage
        if 'remedy' in card.types and 'attack' in threat_spell.card.types:
            return True
        
        return False
    
    def _enemy_has_spell_type(self, spell_type, gs):
        """Check if enemy has active spells of given type"""
        for player in gs.players:
            if player == self.current_player:
                continue
            for clash_list in player.board:
                for spell in clash_list:
                    if spell.status == 'revealed' and spell_type in spell.card.types:
                        return True
        return False
    
    def _predict_enemy_spell_type(self, spell_type):
        """Predict likelihood of enemy playing spell type"""
        # Base predictions
        predictions = {
            'attack': 70,
            'boost': 60,
            'remedy': 40,
            'response': 50,
            'any': 95
        }
        return predictions.get(spell_type, 30)
    
    def _we_have_spell_type(self, spell_type, player, gs):
        """Check if we have spells of given type"""
        # Check board
        for clash_list in player.board:
            for spell in clash_list:
                if spell.status == 'revealed' and (spell_type == 'any' or spell_type in spell.card.types):
                    return True
        
        # Check hand
        for card in player.hand:
            if spell_type == 'any' or spell_type in card.types:
                return True
        
        return False
    
    def make_choice(self, valid_options, caster, gs, current_card):
        """Make choices with extreme analysis"""
        if not valid_options:
            return None
        
        # Analyze each option in extreme detail
        option_scores = []
        
        for option in valid_options:
            score = 0
            
            # Immediate value
            score += self._evaluate_option_immediate_value(option, caster, gs) * 0.4
            
            # Future impact
            score += self._evaluate_option_future_impact(option, caster, gs) * 0.3
            
            # Risk assessment
            score -= self._evaluate_option_risk(option, caster, gs) * 0.3
            
            option_scores.append((option, score))
        
        # Sort by score
        option_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_option = option_scores[0][0]
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Chose option with score {option_scores[0][1]:.1f}\033[0m"
            )
        
        return best_option
    
    def _evaluate_option_immediate_value(self, option, caster, gs):
        """Evaluate immediate tactical value of an option"""
        value = 0
        
        if option.get('type') == 'damage':
            damage = option.get('parameters', {}).get('value', 0)
            # Check if lethal
            for player in gs.players:
                if player != caster and player.health <= damage:
                    value += 200
                    break
            else:
                value += damage * 15
        
        elif option.get('type') == 'heal':
            healing = option.get('parameters', {}).get('value', 0)
            if caster.health <= 2:
                value += healing * 50
            else:
                value += healing * 20
        
        elif option.get('type') == 'advance':
            # Advancing is complex - evaluate based on the target spell
            target_spell = self._identify_advance_target(option, caster, gs)
            if target_spell:
                advance_value = self._evaluate_advance_value(target_spell, caster, gs)
                value += advance_value
            else:
                # Generic advance value if we can't identify the target
                value += 40 * (4 - gs.clash_num)
        
        elif option.get('type') == 'move':
            # Moving spells (Space element) - evaluate based on target spells
            move_value = self._evaluate_move_value(option, caster, gs)
            value += move_value
        
        elif option.get('type') == 'cast':
            # Casting extra spells (Illuminate, Overexert) - very valuable
            cast_value = self._evaluate_cast_value(option, caster, gs)
            value += cast_value
        
        elif option.get('type') == 'cancel':
            # Canceling high-priority spells is valuable
            value += 60
        
        elif option.get('type') == 'protect_from_enemy_effects':
            # Protection is very valuable when health is low
            protect_value = 30
            if caster.health <= 3:
                protect_value *= 2
            value += protect_value
        
        elif option.get('type') == 'damage_per_spell':
            # Scaling damage based on active spells
            params = option.get('parameters', {})
            spell_type = params.get('spell_type', 'any')
            active_count = self._count_active_spells_of_type(caster, gs, spell_type)
            value += active_count * 15
        
        elif option.get('type') == 'heal_per_spell':
            # Scaling healing based on active spells
            params = option.get('parameters', {})
            spell_type = params.get('spell_type', 'any')
            active_count = self._count_active_spells_of_type(caster, gs, spell_type)
            healing_value = active_count * 20
            if caster.health <= 2:
                healing_value *= 2
            value += healing_value
        
        elif option.get('type') == 'weaken_per_spell':
            # Scaling weaken based on active spells
            params = option.get('parameters', {})
            spell_type = params.get('spell_type', 'any')
            active_count = self._count_active_spells_of_type(caster, gs, spell_type)
            value += active_count * 25  # Weaken is valuable long-term
        
        elif option.get('type') == 'copy_spell':
            # Copying spells is complex - depends on what's available
            value += 50  # Base value for flexibility
        
        return value
    
    def _evaluate_option_future_impact(self, option, caster, gs):
        """Evaluate long-term impact of an option"""
        impact = 0
        
        # Actions that affect future turns
        if option.get('type') == 'weaken':
            # Permanent health reduction is very valuable
            weaken_amount = option.get('parameters', {}).get('value', 0)
            impact += weaken_amount * 30
        
        elif option.get('type') == 'bolster':
            # Permanent health increase
            bolster_amount = option.get('parameters', {}).get('value', 0)
            impact += bolster_amount * 25
        
        elif option.get('type') == 'discard':
            # Reducing enemy options
            impact += 35
        
        elif option.get('type') == 'recall':
            # Gaining card advantage
            impact += 40
        
        return impact
    
    def _evaluate_option_risk(self, option, caster, gs):
        """Evaluate risks associated with an option"""
        risk = 0
        
        # Self-damage is risky
        if option.get('type') == 'damage' and option.get('target') == 'self':
            damage = option.get('parameters', {}).get('value', 0)
            if caster.health <= damage + 1:
                risk += 200  # Could be lethal
            else:
                risk += damage * 10
        
        # Discarding can be risky if low on cards
        if option.get('type') == 'discard' and option.get('target') == 'self':
            if len(caster.hand) <= 2:
                risk += 50
        
        # Advancing leaves us vulnerable this turn
        if option.get('type') == 'advance' and option.get('target') == 'this_spell':
            risk += 20
        
        return risk
    
    def choose_draft_set(self, player, gs, available_sets):
        """Expert drafting with extreme analysis"""
        if not available_sets:
            return None
        
        # Track what elements other players have drafted
        self._update_opponent_draft_tracking(gs)
        
        # Analyze opponent's actual draft choices
        opponent_analysis = self._analyze_opponent_drafting_patterns(gs)
        
        set_evaluations = []
        
        for spell_set in available_sets:
            evaluation = {
                'set': spell_set,
                'score': 0,
                'strengths': [],
                'weaknesses': [],
                'synergies': 0,
                'counter_potential': 0
            }
            
            # Deep set analysis
            element = spell_set[0].element
            
            # Win rate data
            if hasattr(self, 'win_rate_data') and self.win_rate_data:
                win_rate = self.win_rate_data.get('win_rates', {}).get(element, 0.5)
                evaluation['score'] += win_rate * 100
            
            # Analyze each spell in detail
            for spell in spell_set:
                # Type composition
                for spell_type in spell.types:
                    if spell_type == 'attack':
                        evaluation['strengths'].append('damage')
                        evaluation['score'] += 30
                    elif spell_type == 'remedy':
                        evaluation['strengths'].append('sustain')
                        evaluation['score'] += 35
                    elif spell_type == 'response':
                        evaluation['strengths'].append('reactive')
                        evaluation['score'] += 40
                    elif spell_type == 'boost':
                        evaluation['strengths'].append('scaling')
                        evaluation['score'] += 25
                
                # Conjury value
                if spell.is_conjury:
                    evaluation['strengths'].append('board_control')
                    evaluation['score'] += 45
                
                # Priority diversity
                if spell.priority == 'A':
                    evaluation['strengths'].append('advance_priority')
                elif str(spell.priority).isdigit() and int(spell.priority) <= 2:
                    evaluation['strengths'].append('fast')
            
            # Internal synergies
            evaluation['synergies'] = self._calculate_set_synergies(spell_set)
            evaluation['score'] += evaluation['synergies']
            
            # Counter potential against likely enemy elements
            evaluation['counter_potential'] = self._calculate_counter_potential(element, opponent_analysis)
            evaluation['score'] += evaluation['counter_potential']
            
            set_evaluations.append(evaluation)
        
        # Sort by score
        set_evaluations.sort(key=lambda x: x['score'], reverse=True)
        
        # Use weighted randomization to avoid always picking the same elements
        # Convert scores to weights (ensure all positive)
        min_score = min(e['score'] for e in set_evaluations)
        weights = [(e['score'] - min_score + 1) for e in set_evaluations]
        
        # Select randomly based on weights
        import random
        total_weight = sum(weights)
        r = random.uniform(0, total_weight)
        
        upto = 0
        chosen_eval = set_evaluations[0]  # fallback
        for i, weight in enumerate(weights):
            if upto + weight >= r:
                chosen_eval = set_evaluations[i]
                break
            upto += weight
        
        # Log extensive analysis
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Drafted {chosen_eval['set'][0].elephant} (Score: {chosen_eval['score']:.1f})\033[0m"
            )
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Strengths: {', '.join(set(chosen_eval['strengths']))}\033[0m"
            )
        
        return chosen_eval['set']
    
    def _analyze_opponent_drafting_patterns(self, gs):
        """Analyze opponent draft choices based on what they've actually drafted"""
        analysis = {
            'drafted_elements': [],
            'likely_types': [],
            'aggression_level': 0.5,
            'has_responses': False
        }
        
        # Check all opponents
        for player in gs.players:
            if player == self.current_player:
                continue
            
            opponent_elements = self.get_opponent_elements(player.name)
            analysis['drafted_elements'].extend(opponent_elements)
            
            # Check for response-heavy elements
            for element in opponent_elements:
                response_count = self._count_element_response_spells(element)
                if response_count > 0:
                    analysis['has_responses'] = True
                    
                    # Check for high-threat responses
                    element_threats = self._analyze_element_response_threats(element)
                    high_threats = [t for t in element_threats if t.get('threat_level') == 'high']
                    if high_threats:
                        analysis['aggression_level'] = 0.3  # Be more cautious
        
        # If no elements tracked yet (early draft), use win rate data
        if not analysis['drafted_elements']:
            # Use elements with highest win rates as likely choices
            if hasattr(self, 'win_rate_data') and self.win_rate_data:
                win_rates = self.win_rate_data.get('win_rates', {})
                sorted_elements = sorted(win_rates.items(), key=lambda x: x[1], reverse=True)
                analysis['drafted_elements'] = [elem[0] for elem in sorted_elements[:3]]
            else:
                analysis['drafted_elements'] = []  # No assumptions
            
            analysis['likely_types'] = ['attack', 'remedy']  # Common types
        else:
            # Analyze likely spell types based on element archetypes
            for element in analysis['drafted_elements']:
                archetype = self._get_element_archetype(element)
                if archetype == 'defensive':
                    analysis['likely_types'].append('response')
                    analysis['likely_types'].append('remedy')
                elif archetype == 'aggressive':
                    analysis['likely_types'].append('attack')
                elif archetype == 'control':
                    analysis['likely_types'].append('response')
                    analysis['likely_types'].append('boost')
        
        return analysis
    
    def _calculate_set_synergies(self, spell_set):
        """Calculate internal synergies within a set"""
        synergy = 0
        
        # Check each pair of spells
        for i, spell1 in enumerate(spell_set):
            for j, spell2 in enumerate(spell_set[i+1:], i+1):
                pair_synergy = self._calculate_synergy(spell1, spell2, None)
                synergy += pair_synergy * 0.5
        
        # Bonus for cohesive themes
        all_types = set()
        for spell in spell_set:
            all_types.update(spell.types)
        
        if len(all_types) >= 3:  # Diverse toolkit
            synergy += 30
        
        return synergy
    
    def _calculate_counter_potential(self, element, opponent_analysis):
        """Calculate how well this element counters expected opponents"""
        counter_score = 0
        
        # Element category matchups
        our_category = self.get_element_category(element)
        our_archetype = self._get_element_archetype(element)
        
        # Use actual drafted elements
        enemy_elements = opponent_analysis.get('drafted_elements', [])
        
        for enemy_element in enemy_elements:
            enemy_category = self.get_element_category(enemy_element)
            enemy_archetype = self._get_element_archetype(enemy_element)
            
            # Category-based advantages
            if our_category == 'defense' and enemy_category == 'offense':
                counter_score += 20
            elif our_category == 'mobility' and enemy_category == 'defense':
                counter_score += 15
            elif our_category == 'offense' and enemy_category == 'mobility':
                counter_score += 15
            
            # Archetype-based matchups
            if enemy_archetype == 'defensive' and our_archetype == 'aggressive':
                # Aggressive vs defensive with strong responses
                counter_score -= 15
            elif enemy_archetype == 'defensive' and our_archetype == 'control':
                # Control can handle defensive strategies
                counter_score += 10
            
            # If enemy has response threats, adjust our preference
            enemy_response_count = self._count_element_response_spells(enemy_element)
            if enemy_response_count > 0:
                # Penalize attack-heavy strategies
                if our_archetype == 'aggressive':
                    counter_score -= enemy_response_count * 10
                # Favor control/defensive strategies
                elif our_archetype in ['control', 'defensive']:
                    counter_score += enemy_response_count * 5
        
        return counter_score
    
    def _get_element_archetype(self, element):
        """Get the strategic archetype of an element based on its spells"""
        # Count spell types for this element
        type_counts = defaultdict(int)
        spell_count = 0
        
        for spell_name, spell_info in self.spell_database.items():
            if spell_info.get('element') == element:
                spell_count += 1
                for spell_type in spell_info.get('types', []):
                    type_counts[spell_type] += 1
        
        if spell_count == 0:
            return 'balanced'  # Default if no data
        
        # Determine archetype based on spell type distribution
        attack_ratio = type_counts.get('attack', 0) / spell_count
        response_ratio = type_counts.get('response', 0) / spell_count
        remedy_ratio = type_counts.get('remedy', 0) / spell_count
        
        if attack_ratio > 0.5:
            return 'aggressive'
        elif response_ratio > 0.3 or remedy_ratio > 0.3:
            return 'defensive'
        elif response_ratio > 0.2 and type_counts.get('boost', 0) > 0:
            return 'control'
        else:
            return 'balanced'
    
    def _count_element_response_spells(self, element):
        """Count how many response spells an element has"""
        count = 0
        
        for spell_name, spell_info in self.spell_database.items():
            if spell_info.get('element') == element and 'response' in spell_info.get('types', []):
                count += 1
        
        return count
    
    def _evaluate_board_state_synergy(self, card, player, gs):
        """Evaluate how well this card synergizes with the current board state"""
        score = 0
        
        # Check our own board for synergies
        our_active_spells = self._get_active_spells(player, gs)
        enemy_active_spells = self._get_active_spells_for_enemies(player, gs)
        
        # 1. Evaluate synergies with our active spells
        for spell in our_active_spells:
            # Check if this card benefits from the active spell
            synergy = self._calculate_active_spell_synergy(card, spell.card, gs)
            score += synergy
            
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and synergy > 20:
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {card.name} synergizes with active {spell.card.name} (+{synergy})\033[0m"
                )
        
        # 2. Evaluate against enemy active spells
        for enemy_spell in enemy_active_spells:
            # Check if this card counters or is countered by enemy spell
            interaction = self._evaluate_spell_interaction(card, enemy_spell, player, gs)
            score += interaction
            
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and abs(interaction) > 20:
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {card.name} vs enemy {enemy_spell.card.name} ({interaction:+.0f})\033[0m"
                )
        
        # 3. Special consideration for advancing spells
        advancing_threats = self._get_advancing_enemy_spells(gs)
        if advancing_threats:
            # Prioritize immediate answers or aggressive plays
            if 'cancel' in str(card.resolve_effects):
                score += 40  # Can potentially stop threats
            elif 'attack' in card.types and card.priority in ['1', '2']:
                score += 30  # Fast damage before threats resolve
            elif 'remedy' in card.types:
                score += 25  # Defensive preparation
                
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] {len(advancing_threats)} enemy spells advancing!\033[0m"
                )
        
        return score
    
    def _get_active_spells(self, player, gs):
        """Get all active spells for a player on current clash"""
        if gs.clash_num <= 0 or gs.clash_num > 4:
            return []
        
        active_spells = []
        for spell in player.board[gs.clash_num - 1]:
            if spell.status == 'revealed':
                active_spells.append(spell)
        
        return active_spells
    
    def _get_active_spells_for_enemies(self, player, gs):
        """Get all active enemy spells on current clash"""
        enemy_spells = []
        
        for enemy in gs.players:
            if enemy == player:
                continue
            enemy_spells.extend(self._get_active_spells(enemy, gs))
        
        return enemy_spells
    
    def _get_advancing_enemy_spells(self, gs):
        """Get enemy spells that will advance to next clash"""
        if gs.clash_num >= 4:
            return []  # No advancing on clash 4
        
        advancing = []
        for player in gs.players:
            for spell in player.board[gs.clash_num - 1]:
                if spell.status == 'revealed' and spell.card.advance_effects:
                    advancing.append(spell)
        
        return advancing
    
    def _calculate_active_spell_synergy(self, new_card, active_card, gs):
        """Calculate synergy between a new card and an active spell"""
        synergy = 0
        
        # Type-based synergies
        if 'boost' in active_card.types:
            if 'attack' in new_card.types:
                synergy += 25  # Boost enhances attacks
            elif 'remedy' in new_card.types:
                synergy += 15  # Boost can enhance healing
        
        if 'response' in active_card.types:
            if 'attack' in new_card.types:
                synergy += 20  # Response protects attackers
        
        # Check for specific condition synergies
        new_effects = str(new_card.resolve_effects) + str(new_card.advance_effects)
        
        # If new card requires active spell types
        if 'if_caster_has_active_spell_of_type' in new_effects:
            for spell_type in active_card.types:
                if spell_type in new_effects:
                    synergy += 40  # Strong synergy
        
        # If active card is advancing, value cards that benefit next turn
        if active_card.advance_effects and gs.clash_num < 4:
            if 'if_spell_advanced' in new_effects:
                synergy += 30  # Will benefit from the advancing spell
        
        # Element synergy
        if new_card.element == active_card.element:
            synergy += 10
        
        return synergy
    
    def _evaluate_spell_interaction(self, our_card, enemy_spell, player, gs):
        """Evaluate how our card interacts with an enemy's active spell"""
        interaction = 0
        enemy_card = enemy_spell.card
        enemy_owner = enemy_spell.owner
        
        # Check if enemy spell threatens us
        if 'attack' in enemy_card.types:
            enemy_damage = self._estimate_card_damage_in_context(enemy_card, enemy_owner, gs)
            
            # Our responses to enemy attacks
            if 'cancel' in str(our_card.resolve_effects):
                interaction += enemy_damage * 15  # Can cancel the damage
            elif 'remedy' in our_card.types:
                healing = self._estimate_card_healing(our_card)
                interaction += min(healing, enemy_damage) * 10  # Mitigate damage
            elif 'attack' in our_card.types:
                # Race consideration
                our_damage = self._estimate_card_damage_in_context(our_card, player, gs)
                if our_damage > enemy_damage:
                    interaction += 10  # We're winning the race
                else:
                    interaction -= 5  # We're losing the race
        
        # If enemy has boost, our attacks are less valuable
        if 'boost' in enemy_card.types and 'attack' in our_card.types:
            interaction -= 15  # They're set up better
        
        # If enemy has response, our attacks might trigger it
        if 'response' in enemy_card.types and 'attack' in our_card.types:
            # This is already handled by response threat evaluation
            # Just add a small penalty for redundancy
            interaction -= 5
        
        # If enemy spell is advancing, consider future threat
        if enemy_card.advance_effects:
            # Advancing enemy spells are more threatening
            if 'attack' in enemy_card.types:
                interaction -= 10  # Growing threat
            elif 'boost' in enemy_card.types:
                interaction -= 5  # Enemy getting stronger
        
        return interaction
    
    def choose_cards_to_keep(self, player, gs):
        """Expert end-of-round hand management with strategic drafting"""
        if not player.hand:
            return []
        
        # First, evaluate if we should draft a new set
        should_draft = self._should_draft_new_set(player, gs)
        
        if should_draft:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-EXPERT] Strategic decision: Drafting new set!\033[0m"
                )
            return []  # Discard everything to draft
        
        # Otherwise, evaluate cards to keep
        retention_scores = {}
        
        for card in player.hand:
            score = 0
            
            # Base quality
            score += self._evaluate_card_quality(card) * 0.3
            
            # Future round relevance
            score += self._evaluate_future_relevance(card, gs) * 0.4
            
            # Combo potential with discard pile
            score += self._evaluate_recall_synergies(card, player) * 0.3
            
            retention_scores[card] = score
        
        # Sort by retention score
        sorted_cards = sorted(retention_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Determine how many to keep
        ideal_keep_count = self._calculate_ideal_hand_size(player, gs)
        
        cards_to_keep = [card for card, score in sorted_cards[:ideal_keep_count]]
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            kept_names = [c.name for c in cards_to_keep]
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Keeping: {', '.join(kept_names)}\033[0m"
            )
        
        return cards_to_keep
    
    def _should_draft_new_set(self, player, gs):
        """Evaluate whether to draft a new set strategically"""
        # Don't draft if no sets available
        if not hasattr(gs, 'main_deck') or not gs.main_deck:
            return False
        
        # Calculate various factors
        hand_size = len(player.hand)
        health_ratio = player.health / player.max_health
        rounds_remaining = 10 - gs.round_num  # Estimate
        
        draft_score = 0
        
        # 1. Resource starvation (40% weight)
        if hand_size <= 2:
            draft_score += 40
        elif hand_size == 3:
            draft_score += 20
        
        # 2. Hand quality assessment (30% weight)
        hand_quality = self._evaluate_hand_quality(player.hand, player, gs)
        if hand_quality < 40:  # Poor hand
            draft_score += 30
        elif hand_quality < 60:  # Mediocre hand
            draft_score += 15
        
        # 3. Health-card mismatch (20% weight)
        mismatch_score = self._evaluate_health_card_mismatch(player)
        draft_score += mismatch_score * 0.2
        
        # 4. Late game desperation (10% weight)
        # Late game = someone has 1 trunk left
        min_trunks = min(p.trunks for p in gs.players)
        if min_trunks <= 1 and health_ratio < 0.5:
            draft_score += 10
        elif min_trunks <= 1 and player.trunks <= 1:
            # We're on our last trunk - be more willing to pivot
            draft_score += 15
        
        # 5. Enemy element counters (bonus)
        if self._current_elements_are_countered(player, gs):
            draft_score += 15
        
        # Log decision factors
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            min_trunks = min(p.trunks for p in gs.players)
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-EXPERT] Draft evaluation - Score: {draft_score}, "
                f"Hand: {hand_size}, Quality: {hand_quality:.1f}, Health: {health_ratio:.1%}, "
                f"Trunks: {player.trunks} (min: {min_trunks})\033[0m"
            )
        
        # Draft if score exceeds threshold
        return draft_score >= 50
    
    def _evaluate_hand_quality(self, hand, player, gs):
        """Evaluate overall quality of current hand"""
        if not hand:
            return 0
        
        total_score = 0
        for card in hand:
            # Use existing card quality evaluation
            card_score = self._evaluate_card_quality(card)
            
            # Adjust for current game state
            if player.health <= 3 and 'remedy' in card.types:
                card_score *= 1.5
            elif player.health >= player.max_health * 0.8 and 'attack' in card.types:
                card_score *= 1.2
            
            total_score += card_score
        
        # Average quality, normalized to 0-100
        return min(100, (total_score / len(hand)) * 0.8)
    
    def _evaluate_health_card_mismatch(self, player):
        """Check if hand composition matches health situation"""
        mismatch = 0
        
        attack_count = sum(1 for c in player.hand if 'attack' in c.types)
        remedy_count = sum(1 for c in player.hand if 'remedy' in c.types)
        
        health_ratio = player.health / player.max_health
        
        # Low health but few remedies
        if health_ratio < 0.4 and remedy_count == 0:
            mismatch += 80
        elif health_ratio < 0.6 and remedy_count <= 1:
            mismatch += 40
        
        # High health but no attacks
        if health_ratio > 0.8 and attack_count == 0:
            mismatch += 60
        
        # Mid game with no flexibility
        if len(set(c.types[0] if c.types else 'none' for c in player.hand)) == 1:
            mismatch += 30  # All cards same type
        
        return mismatch
    
    def _current_elements_are_countered(self, player, gs):
        """Check if current elements are heavily countered by opponents"""
        # Get our current elements
        our_elements = set()
        for card in player.hand:
            our_elements.add(card.element)
        
        if not our_elements:
            return False
        
        # Check if opponents have drafted elements that counter ours
        counter_score = 0
        
        for enemy in gs.players:
            if enemy == player:
                continue
            
            enemy_elements = self.get_opponent_elements(enemy.name)
            for our_elem in our_elements:
                for enemy_elem in enemy_elements:
                    # Check if enemy element counters ours
                    if self._element_counters(enemy_elem, our_elem):
                        counter_score += 1
        
        return counter_score >= 2  # Heavily countered
    
    def _element_counters(self, elem1, elem2):
        """Check if elem1 counters elem2 based on response threats"""
        # High response count means it counters attack-heavy elements
        elem1_responses = self._count_element_response_spells(elem1)
        elem2_archetype = self._get_element_archetype(elem2)
        
        return elem1_responses >= 2 and elem2_archetype == 'aggressive'
    
    def _evaluate_card_quality(self, card):
        """Base quality assessment of a card"""
        quality = 50
        
        if 'attack' in card.types:
            quality += 20
        if 'remedy' in card.types:
            quality += 25
        if 'response' in card.types:
            quality += 30
        if card.is_conjury:
            quality += 35
        
        # Complex effects are usually stronger
        effect_count = len(card.resolve_effects) + len(card.advance_effects)
        quality += effect_count * 10
        
        return quality
    
    def _evaluate_future_relevance(self, card, gs):
        """How relevant will this card be in future rounds"""
        relevance = 0
        
        # Late game favors different cards
        if gs.round_num >= 5:
            # Late game - value finishers
            if 'attack' in card.types:
                relevance += 40
            if card.priority in ['1', '2']:
                relevance += 30
        else:
            # Mid game - value flexibility
            if 'boost' in card.types:
                relevance += 35
            if 'response' in card.types:
                relevance += 30
        
        return relevance
    
    def _evaluate_recall_synergies(self, card, player):
        """Evaluate synergies with cards in discard pile"""
        synergy = 0
        
        # Check top cards in discard
        recent_discards = player.discard_pile[-10:] if len(player.discard_pile) > 10 else player.discard_pile
        
        for discard in recent_discards:
            pair_synergy = self._calculate_synergy(card, discard, None)
            if pair_synergy > 40:
                synergy += pair_synergy * 0.3
        
        return synergy
    
    def _calculate_ideal_hand_size(self, player, gs):
        """Calculate ideal number of cards to keep"""
        base_keep = 2
        
        # Keep more if healthy
        if player.health >= player.max_health * 0.7:
            base_keep += 1
        
        # Keep fewer if desperate
        if player.health <= 2:
            base_keep = 1
        
        # Never keep more than 3 (need room for new cards)
        return min(base_keep, len(player.hand), 3)
    
    def choose_cancellation_target(self, potential_targets, caster, gs, current_card):
        """Expert AI - comprehensive threat analysis with predictive modeling"""
        if not potential_targets:
            return None
        
        # Separate enemy and friendly targets
        enemy_targets = [t for t in potential_targets if t.owner != caster]
        
        if enemy_targets:
            # Comprehensive threat evaluation
            threat_analysis = {}
            
            for target in enemy_targets:
                # Base threat score
                base_score = self._evaluate_spell_threat(target, caster, gs)
                
                # Expert-level analysis
                analysis = {
                    'base_threat': base_score,
                    'immediate_damage': self._calculate_spell_damage(target.card, target.owner, gs),
                    'is_conjury': target.card.is_conjury,
                    'enables_combos': 0,
                    'future_threat': 0,
                    'defensive_value': 0,
                    'tempo_impact': 0
                }
                
                # 1. Combo enablement analysis
                other_enemy_spells = [s for s in target.owner.board[gs.clash_num-1] 
                                     if s.status == 'revealed' and s != target]
                for other_spell in other_enemy_spells:
                    for effect in other_spell.card.resolve_effects:
                        condition = effect.get('condition', {})
                        if self._spell_satisfies_condition(target.card, condition):
                            analysis['enables_combos'] += 20
                
                # 2. Future threat (advance effects, scaling damage)
                if target.card.advance_effects:
                    analysis['future_threat'] += len(target.card.advance_effects) * 15
                
                # Check for damage that scales or repeats
                for effect in target.card.resolve_effects:
                    action = effect.get('action', {})
                    if isinstance(action, dict):
                        if action.get('type') in ['damage_per_spell', 'damage_per_enemy_spell_type']:
                            analysis['future_threat'] += 25
                
                # 3. Defensive value for opponent
                if target.owner.health <= 3:
                    if 'remedy' in target.card.types:
                        analysis['defensive_value'] = 30 + (3 - target.owner.health) * 10
                    if 'bolster' in str(target.card.resolve_effects):
                        analysis['defensive_value'] += 20
                
                # 4. Tempo impact
                priority = int(target.card.priority) if str(target.card.priority).isdigit() else 99
                if priority <= 2:
                    analysis['tempo_impact'] = 25  # Fast spells have high tempo impact
                
                # Calculate total threat
                total_threat = (
                    analysis['base_threat'] +
                    analysis['enables_combos'] +
                    analysis['future_threat'] +
                    analysis['defensive_value'] +
                    analysis['tempo_impact']
                )
                
                # Context adjustments
                if gs.round_num >= 3 and target.owner.trunks == 1:
                    # Late game, low trunks - defensive spells are critical
                    if 'remedy' in target.card.types:
                        total_threat *= 1.5
                
                # Known combos from opponent history
                if hasattr(self, 'opponent_history'):
                    history = self.opponent_history.get(target.owner.name, {})
                    spell_history = history.get('spells_played', [])
                    # Check if this spell is part of known combo patterns
                    for past_spell in spell_history[-5:]:
                        if past_spell.get('element') == target.card.element:
                            total_threat += 10  # Element synergy pattern
                
                threat_analysis[target] = {
                    'total': total_threat,
                    'breakdown': analysis
                }
            
            # Make decision
            best_target = max(threat_analysis.items(), key=lambda x: x[1]['total'])[0]
            best_analysis = threat_analysis[best_target]
            
            # Log detailed analysis
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                # Summary of top threats
                sorted_threats = sorted(threat_analysis.items(), key=lambda x: x[1]['total'], reverse=True)[:3]
                for spell, data in sorted_threats:
                    self.engine.ai_decision_logs.append(
                        f"\\033[90m[AI-EXPERT] {spell.card.name}: Total={data['total']:.0f} "
                        f"(Dmg={data['breakdown']['immediate_damage']}, "
                        f"Combo={data['breakdown']['enables_combos']}, "
                        f"Future={data['breakdown']['future_threat']})\\033[0m"
                    )
                
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[AI-EXPERT] {caster.name} chose to cancel {best_target.card.name}\\033[0m"
                )
            
            return best_target
        
        # No enemy targets, use default logic
        return super().choose_cancellation_target(potential_targets, caster, gs, current_card)
    
    def _spell_satisfies_condition(self, spell_card, condition):
        """Check if a spell would satisfy a given condition"""
        cond_type = condition.get('type')
        if cond_type == 'if_caster_has_active_spell_of_type':
            params = condition.get('parameters', {})
            spell_type = params.get('spell_type', 'any')
            if spell_type == 'any':
                return True
            return spell_type in spell_card.types
        return False
    
    def _plan_condition_setups(self, player, gs):
        """Plan how to meet conditions for high-value spells"""
        setup_plans = []
        
        for card in player.hand:
            if self._has_conditional_effects(card):
                plan = {
                    'card': card,
                    'condition_type': self._get_primary_condition_type(card),
                    'setup_required': self._analyze_setup_needs(card, player, gs),
                    'optimal_timing': self._calculate_optimal_timing(card, gs),
                    'enablers': self._find_enabler_cards(card, player),
                    'value_if_met': self._calculate_conditional_value(card, player, gs)
                }
                setup_plans.append(plan)
        
        return setup_plans
    
    def _has_conditional_effects(self, card):
        """Check if a card has conditional effects worth planning for"""
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            if condition.get('type') not in ['always', None]:
                return True
        return False
    
    def _get_primary_condition_type(self, card):
        """Get the main condition type for a card"""
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            cond_type = condition.get('type')
            if cond_type and cond_type != 'always':
                return cond_type
        return None
    
    def _analyze_setup_needs(self, card, player, gs):
        """Analyze what's needed to meet a card's conditions"""
        needs = {'turns_required': 0, 'cards_required': [], 'can_meet': True}
        
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            cond_type = condition.get('type')
            
            if cond_type == 'spell_clashes_count':
                # For Turbulence
                required = condition.get('parameters', {}).get('count', 3)
                current = self._count_spell_clashes(card, player, gs)
                turns_needed = required - current
                
                if turns_needed > (4 - gs.clash_num):
                    needs['can_meet'] = False
                else:
                    needs['turns_required'] = max(needs['turns_required'], turns_needed)
                    # Check for advance cards
                    advance_cards = [c for c in player.hand if 'advance' in str(c.resolve_effects + c.advance_effects)]
                    needs['cards_required'].extend(advance_cards)
                    
            elif cond_type == 'if_caster_has_active_spell_of_type':
                # For Flow, Ignite, Defend, Besiege
                spell_type = condition.get('parameters', {}).get('spell_type', 'any')
                count_needed = condition.get('parameters', {}).get('count', 1)
                
                matching_cards = [c for c in player.hand if spell_type in c.types or spell_type == 'any']
                if len(matching_cards) < count_needed:
                    needs['can_meet'] = False
                else:
                    needs['cards_required'].extend(matching_cards[:count_needed])
                    
            elif cond_type == 'if_spell_previously_resolved_this_round':
                # For Flow's past clash bonus
                if gs.clash_num == 4:  # Last clash
                    needs['can_meet'] = False
                elif card.notfirst and gs.clash_num == 1:
                    needs['turns_required'] = 1  # Need to wait
        
        return needs
    
    def _find_enabler_cards(self, card, player):
        """Find cards that help meet conditions"""
        enablers = []
        primary_condition = self._get_primary_condition_type(card)
        
        if primary_condition == 'spell_clashes_count':
            # Find advance cards
            for c in player.hand:
                if 'advance' in str(c.resolve_effects + c.advance_effects):
                    enablers.append({'card': c, 'type': 'advance'})
                    
        elif primary_condition == 'if_caster_has_active_spell_of_type':
            # Find cards of the required type
            for effect in card.resolve_effects:
                condition = effect.get('condition', {})
                if condition.get('type') == primary_condition:
                    spell_type = condition.get('parameters', {}).get('spell_type', 'any')
                    for c in player.hand:
                        if c != card and (spell_type in c.types or spell_type == 'any'):
                            enablers.append({'card': c, 'type': 'synergy'})
        
        return enablers
    
    def _calculate_optimal_timing(self, card, gs):
        """Calculate when to play a conditional card"""
        primary_condition = self._get_primary_condition_type(card)
        
        if primary_condition == 'spell_clashes_count':
            # Play early if we have advance enablers
            if gs.clash_num <= 2:
                return 1  # High priority to play early
            else:
                return 0.3  # Less valuable late
                
        elif primary_condition == 'if_caster_has_active_spell_of_type':
            # Coordinate with other spells
            return 0.8  # Generally good to play with others
            
        elif primary_condition == 'if_spell_previously_resolved_this_round':
            # Better in later clashes
            if gs.clash_num >= 2:
                return 1.0
            else:
                return 0.2
                
        return 0.5  # Default
    
    def _evaluate_condition_timing(self, card, player, gs):
        """Determine strategic value of playing conditional cards now"""
        timing_score = 0
        primary_condition = self._get_primary_condition_type(card)
        
        # Cards that need multiple clashes (like spell_clashes_count)
        if primary_condition == 'spell_clashes_count':
            if gs.clash_num <= 2:  # Early game
                advance_cards = [c for c in player.hand if 'advance' in str(c.resolve_effects + c.advance_effects)]
                if advance_cards:
                    timing_score += 100
                    if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                        self.engine.ai_decision_logs.append(
                            f"\\033[90m[AI-EXPERT] {card.name} can be set up with {len(advance_cards)} advance cards\\033[0m"
                        )
            else:
                timing_score -= 50  # Too late to set up
                        
        # Cards that need other active spells
        elif primary_condition == 'if_caster_has_active_spell_of_type':
            setup_needs = self._analyze_setup_needs(card, player, gs)
            if setup_needs['can_meet'] and setup_needs['cards_required']:
                timing_score += 80
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    enabler_names = [c.name for c in setup_needs['cards_required'][:2]]
                    self.engine.ai_decision_logs.append(
                        f"\\033[90m[AI-EXPERT] {card.name} can combo with {enabler_names}\\033[0m"
                    )
                    
        # Cards that scale with active spells (player_choice with damage/heal per spell)
        elif self._has_scaling_choice_effects(card):
            active_count = sum(1 for s in player.board[gs.clash_num-1] if s.status == 'revealed')
            potential_count = active_count + min(2, len([c for c in player.hand if c != card]))
            if potential_count >= 2:
                timing_score += 90
                
        # Cards that need previous resolution
        elif primary_condition == 'if_spell_previously_resolved_this_round':
            if gs.clash_num >= 2:
                timing_score += 70
            else:
                timing_score -= 30
                
        return timing_score
    
    def _has_scaling_choice_effects(self, card):
        """Check if card has choice effects that scale with spell count"""
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            
            # Handle case where action is a list
            if isinstance(action, list):
                for sub_action in action:
                    if isinstance(sub_action, dict) and sub_action.get('type') == 'player_choice':
                        for option in sub_action.get('options', []):
                            if isinstance(option, dict):
                                opt_type = option.get('type', '')
                                if opt_type in ['damage_per_spell', 'heal_per_spell', 'damage_multi_target']:
                                    return True
            # Handle case where action is a dict
            elif isinstance(action, dict) and action.get('type') == 'player_choice':
                for option in action.get('options', []):
                    if isinstance(option, dict):
                        opt_type = option.get('type', '')
                        if opt_type in ['damage_per_spell', 'heal_per_spell', 'damage_multi_target']:
                            return True
        return False
    
    def _needs_active_spells(self, card):
        """Check if card needs active spells for its conditions"""
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            if condition.get('type') == 'if_caster_has_active_spell_of_type':
                return True
        return False
    
    def _evaluate_move_value(self, option, caster, gs):
        """Evaluate the value of moving spells between clashes"""
        value = 0
        params = option.get('parameters', {})
        
        # Moving spells is complex - we need to consider:
        # 1. Which spells are being moved
        # 2. From which clash to which clash
        # 3. Strategic implications
        
        # Check all spells that could be moved
        best_move_value = 0
        
        for clash_idx in range(4):
            for player in gs.players:
                for spell in player.board[clash_idx]:
                    if spell.status == 'revealed':
                        # Evaluate moving this spell
                        move_val = self._calculate_single_move_value(spell, clash_idx, caster, gs)
                        best_move_value = max(best_move_value, move_val)
                        
                        if move_val > 50 and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                            self.engine.ai_decision_logs.append(
                                f"\\033[90m[AI-EXPERT] Considering move: {spell.card.name} from clash {clash_idx+1} (+{move_val})\033[0m"
                            )
        
        return best_move_value
    
    def _calculate_single_move_value(self, spell, from_clash, caster, gs):
        """Calculate value of moving a specific spell"""
        value = 0
        
        # Moving enemy spells away from current clash is defensive
        if spell.owner != caster and from_clash == gs.clash_num - 1:
            damage_prevented = self._estimate_card_damage(spell.card)
            value += damage_prevented * 20
        
        # Moving our spells to better positions
        if spell.owner == caster:
            # Check if spell has clash count conditions
            if self._get_primary_condition_type(spell.card) == 'spell_clashes_count':
                # Moving to a new clash increases clash count
                current_clashes = self._count_spell_clashes(spell.card, caster, gs)
                for effect in spell.card.resolve_effects:
                    condition = effect.get('condition', {})
                    if condition.get('type') == 'spell_clashes_count':
                        required = condition.get('parameters', {}).get('count', 3)
                        if current_clashes < required:
                            # Moving helps meet condition
                            value += 100
        
        return value
    
    def _evaluate_cast_value(self, option, caster, gs):
        """Evaluate the value of casting extra spells"""
        # Casting extra spells is almost always valuable
        base_value = 80  # Base value for card advantage
        
        # Even better if we have good cards in hand
        if len(caster.hand) > 0:
            # Estimate average card value in hand
            avg_damage = sum(self._estimate_card_damage(c) for c in caster.hand) / len(caster.hand)
            avg_healing = sum(self._estimate_card_healing(c) for c in caster.hand) / len(caster.hand)
            
            base_value += avg_damage * 10 + avg_healing * 8
            
            # Check for specific high-value cards we could cast
            for card in caster.hand:
                # Conjuries are great to cast for free
                if card.is_conjury and gs.clash_num <= 2:
                    base_value += 40
                
                # Response spells for defense
                if 'response' in card.types and caster.health <= 5:
                    base_value += 30
                    
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[AI-EXPERT] Cast option value: {base_value} (hand size: {len(caster.hand)})\033[0m"
                )
        
        return base_value
    
    def _identify_advance_target(self, option, caster, gs):
        """Try to identify which spell would be advanced by this option"""
        # This is a simplified version - in reality we'd need to check the game's targeting system
        # For now, we'll check if the option has parameters that indicate the target
        params = option.get('parameters', {})
        target_type = params.get('target', '')
        
        if target_type == 'this_spell':
            # Current spell is advancing itself
            return None  # Can't evaluate self-advance in this context
        
        # For "prompt" type advances, we need to look at potential targets
        # We'll evaluate all possible advance targets
        return None  # Will be handled by evaluate_advance_value
    
    def _evaluate_advance_value(self, target_spell, caster, gs):
        """Evaluate the value of advancing a specific spell or any spell"""
        max_value = 0
        
        # If no specific target, evaluate all possible advance targets
        if target_spell is None:
            # Check all spells on board that could be advanced
            for clash_idx in range(gs.clash_num):  # Past clashes
                for player in gs.players:
                    if player.name == caster.name:
                        for spell in player.board[clash_idx]:
                            if spell.status == 'revealed':
                                spell_value = self._calculate_single_advance_value(spell.card, caster, gs, clash_idx)
                                max_value = max(max_value, spell_value)
                                
                                if spell_value > 100 and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                                    self.engine.ai_decision_logs.append(
                                        f"\\033[90m[AI-EXPERT] High-value advance target: {spell.card.name} (+{spell_value})\033[0m"
                                    )
        else:
            # Evaluate specific target
            max_value = self._calculate_single_advance_value(target_spell, caster, gs, None)
        
        return max_value
    
    def _calculate_single_advance_value(self, card, caster, gs, current_clash_idx):
        """Calculate value of advancing a single spell"""
        value = 0
        
        # 1. Check if spell has spell_clashes_count condition (like Turbulence)
        primary_condition = self._get_primary_condition_type(card)
        if primary_condition == 'spell_clashes_count':
            # Calculate current and potential damage
            current_clashes = self._count_spell_clashes(card, caster, gs)
            
            # Check the condition requirement
            for effect in card.resolve_effects:
                condition = effect.get('condition', {})
                if condition.get('type') == 'spell_clashes_count':
                    required = condition.get('parameters', {}).get('count', 3)
                    if current_clashes < required and current_clashes + 1 >= required:
                        # Advancing will meet the condition!
                        conditional_damage = self._extract_action_value(effect.get('action'))
                        base_damage = self._estimate_card_damage(card)
                        bonus_value = (conditional_damage - base_damage) * 50
                        value += bonus_value
                        
                        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                            self.engine.ai_decision_logs.append(
                                f"\\033[90m[AI-EXPERT] Advancing {card.name} will unlock {conditional_damage} damage!\033[0m"
                            )
        
        # 2. Base value for advancing any spell
        remaining_clashes = 4 - gs.clash_num
        if remaining_clashes > 0:
            # Value of having the spell active again
            spell_damage = self._estimate_card_damage(card)
            spell_heal = self._estimate_card_healing(card)
            value += (spell_damage * 15 + spell_heal * 20) * min(remaining_clashes, 2)
        
        # 3. Advance effects bonus
        if card.advance_effects:
            value += 30  # Spells with advance effects benefit more
        
        # 4. Priority adjustment
        if card.priority == 'A':
            value += 20  # Advance priority spells are designed to be advanced
        
        return value
    
    def _count_active_spells_of_type(self, player, gs, spell_type):
        """Count active spells of a specific type in current clash"""
        count = 0
        for spell in player.board[gs.clash_num - 1]:
            if spell.status == 'revealed':
                if spell_type == 'any' or spell_type in spell.card.types:
                    count += 1
        return count