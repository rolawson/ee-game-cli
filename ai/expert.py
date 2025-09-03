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
            
            # 1. Immediate tactical evaluation
            score += self._evaluate_immediate_tactics(card, player, gs) * 0.3
            
            # 2. Multi-turn strategic value
            score += self._evaluate_strategic_value(card, player, gs, game_plan) * 0.4
            
            # 3. Future combo potential
            score += self._evaluate_future_combos(card, player, gs) * 0.3
            
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
        
        return best_index
    
    def _build_multi_turn_plan(self, player, gs):
        """Build a comprehensive multi-turn strategy"""
        plan = {
            'win_condition': self._identify_win_condition(player, gs),
            'enemy_threats': self._analyze_all_enemy_threats(player, gs),
            'combo_sequences': self._identify_combo_sequences(player, gs),
            'resource_management': self._plan_resource_usage(player, gs),
            'timing_windows': self._identify_critical_timings(player, gs)
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
        """Detailed tactical evaluation of immediate play value"""
        score = 0
        
        # Basic type values with context
        if 'attack' in card.types:
            # Value attacks based on enemy health and defenses
            enemy = next(p for p in gs.players if p != player)
            damage = self._estimate_card_damage(card)
            
            if enemy.health <= damage:
                score += 200  # Lethal
            elif enemy.health <= damage * 2:
                score += 100  # Near lethal
            else:
                score += 30 + (damage * 10)
            
            # Check for enemy responses
            enemy_responses = self._count_enemy_responses(enemy, gs)
            score -= enemy_responses * 15
        
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
    
    def _assess_threat_level(self, spell, clash_idx, gs):
        """Assess threat level of an enemy spell"""
        threat = 0
        
        # Immediate threats
        if 'attack' in spell.card.types:
            threat += self._estimate_card_damage(spell.card) * 20
        if spell.card.is_conjury:
            threat += 40
        if 'cancel' in str(spell.card.resolve_effects):
            threat += 35
        
        # Timing multiplier
        if clash_idx == gs.clash_num - 1:
            threat *= 1.5  # Immediate threats
        elif clash_idx == gs.clash_num:
            threat *= 1.2  # Next turn threats
        
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
            # Advancing is complex - depends on the spell
            value += 40 * (4 - gs.clash_num)
        
        elif option.get('type') == 'cancel':
            # Canceling high-priority spells is valuable
            value += 60
        
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
        
        # Analyze opponent's likely draft choices
        opponent_analysis = self._analyze_opponent_drafting_patterns()
        
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
    
    def _analyze_opponent_drafting_patterns(self):
        """Predict opponent draft choices"""
        # In a real implementation, this would track history
        # For now, return common patterns
        return {
            'likely_elements': ['Fire', 'Sunbeam', 'Thunder'],  # High win rate elements
            'likely_types': ['attack', 'remedy'],
            'aggression_level': 0.6
        }
    
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
        
        for enemy_element in opponent_analysis['likely_elements']:
            enemy_category = self.get_element_category(enemy_element)
            
            # Simple category advantages
            if our_category == 'defense' and enemy_category == 'offense':
                counter_score += 20
            elif our_category == 'mobility' and enemy_category == 'defense':
                counter_score += 15
            elif our_category == 'offense' and enemy_category == 'mobility':
                counter_score += 15
        
        return counter_score
    
    def choose_cards_to_keep(self, player, gs):
        """Expert end-of-round hand management"""
        if not player.hand:
            return []
        
        # Build comprehensive retention strategy
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