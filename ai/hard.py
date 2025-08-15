"""Hard AI - Advanced strategic decision making"""

import random
from .base import BaseAI


class HardAI(BaseAI):
    """Hard AI - strategic play with card evaluation"""
    
    def _select_card(self, player, gs, valid_indices):
        """Evaluate each card and pick the best one"""
        if not valid_indices:
            return None
        
        # Update opponent tracking
        self.update_opponent_history(gs)
        
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
        
        # Check for combo potential
        combo_score = self._check_combo_potential(card, player, gs)
        score += combo_score
        
        # Opponent-aware scoring
        opponent_score = self._score_against_opponents(card, player, gs)
        score += opponent_score
        
        # Timing-based scoring
        timing_score = self._evaluate_timing(card, player, gs)
        score += timing_score
        
        return score
    
    def _evaluate_timing(self, card, player, gs):
        """Evaluate if this is the right time to play this card"""
        score = 0
        
        # Response spell timing
        if 'response' in card.types:
            # Check if response conditions are likely to be met
            if self._check_response_timing(card, player, gs):
                score += 60
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-TIMING] {card.name} response conditions likely to trigger\033[0m"
                    )
            else:
                score -= 40  # Responses are weak if they won't trigger
        
        # Advance-priority spells in early clashes
        if card.priority == 'A':
            if gs.clash_num <= 2:
                score += 30  # Can advance multiple times
            elif gs.clash_num == 4:
                score -= 20  # Won't advance at all
        
        # Save disruption for when it matters
        if 'cancel' in str(card.resolve_effects) or 'discard' in str(card.resolve_effects):
            # Check if opponents have been playing many spells
            total_opponent_spells = 0
            for p in gs.players:
                if p != player:
                    for clash in p.board[:gs.clash_num]:
                        total_opponent_spells += len([s for s in clash if s.status == 'revealed'])
            
            if total_opponent_spells < gs.clash_num:  # Less than 1 spell per clash
                score -= 30  # Save disruption for later
            else:
                score += 20  # Good time for disruption
        
        # Boost spells - better when we have cards to play
        if 'boost' in card.types:
            future_clashes = 4 - gs.clash_num
            cards_in_hand = len(player.hand) - 1  # Excluding this card
            
            if cards_in_hand >= future_clashes:
                score += 30  # We have cards for future clashes
            else:
                score -= 20  # Running low on cards
        
        # Conjury timing - earlier is generally better
        if card.is_conjury:
            if gs.clash_num == 1:
                score += 40  # Maximum value
            elif gs.clash_num == 2:
                score += 20
            elif gs.clash_num == 3:
                score -= 10
            else:
                score -= 30  # Very late for a conjury
        
        # Cards with "if previously resolved" conditions
        if 'if_spell_previously_resolved_this_round' in str(card.resolve_effects):
            if gs.clash_num >= 3:
                score += 50  # More likely to have resolved before
            else:
                score -= 30  # Unlikely to trigger early
        
        return score
    
    def _check_response_timing(self, card, player, gs):
        """Check if a response spell is likely to trigger"""
        # Analyze the response conditions
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            cond_type = condition.get('type', '')
            
            if cond_type == 'if_caster_damaged_last_turn':
                # Check recent damage
                if gs.round_num > 1 or gs.clash_num > 1:
                    return True  # Likely been damaged
                    
            elif cond_type == 'if_enemy_has_active_spell_of_type':
                # Check if enemies typically play this type
                spell_type = condition.get('parameters', {}).get('spell_type', 'any')
                for opponent in gs.players:
                    if opponent != player:
                        analysis = self.analyze_opponent_patterns(opponent.name)
                        if analysis:
                            type_usage = dict(analysis.get('preferred_types', []))
                            if spell_type in type_usage and type_usage[spell_type] > 0:
                                return True
        
        return False
    
    def _score_against_opponents(self, card, player, gs):
        """Score card based on opponent analysis"""
        score = 0
        
        # Analyze each opponent
        for opponent in gs.players:
            if opponent == player:
                continue
                
            analysis = self.analyze_opponent_patterns(opponent.name)
            if not analysis:
                continue
            
            # Counter opponent's preferred strategy
            if analysis['aggression_level'] > 0.5:
                # Opponent is aggressive - value defense and healing
                if 'response' in card.types:
                    score += 40
                if 'remedy' in card.types:
                    score += 30
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-COUNTER] {opponent.name} is aggressive - valuing defensive cards\033[0m"
                    )
            
            elif analysis['support_level'] > 0.5:
                # Opponent likes support spells - value disruption
                if 'cancel' in str(card.resolve_effects) or 'discard' in str(card.resolve_effects):
                    score += 50
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-COUNTER] {opponent.name} uses support - valuing disruption\033[0m"
                    )
            
            # Check opponent's recent spells for specific counters
            recent_elements = [spell['element'] for spell in analysis.get('recent_spells', [])]
            recent_types = []
            for spell in analysis.get('recent_spells', []):
                recent_types.extend(spell['types'])
            
            # If opponent recently played attack spells, responses are more valuable
            if 'attack' in recent_types and 'response' in card.types:
                score += 35
            
            # If opponent has been playing same element, element-specific counters may exist
            preferred_elements = analysis.get('preferred_elements', [])
            if preferred_elements and len(preferred_elements) > 0:
                top_element = preferred_elements[0][0]
                # Some cards might be good against specific elements (future feature)
                
        return score
    
    def _check_combo_potential(self, card, player, gs):
        """Check if this card has combo potential with current board state"""
        combo_score = 0
        
        # Get active spells in current clash
        my_active_spells = []
        for spell in player.board[gs.clash_num - 1]:
            if spell.status == 'revealed':
                my_active_spells.append(spell)
        
        # Check card's conditions for combo potential
        if card.resolve_effects:
            for effect in card.resolve_effects:
                condition = effect.get('condition', {})
                cond_type = condition.get('type', '')
                
                # Cards that check for other active spells benefit from having them
                if cond_type == 'if_caster_has_active_spell_of_type':
                    params = condition.get('parameters', {})
                    spell_type = params.get('spell_type', 'any')
                    exclude_self = params.get('exclude_self', False)
                    required_count = params.get('count', 1)
                    
                    # Count matching spells in hand and board
                    matching_in_hand = sum(1 for c in player.hand 
                                         if c != card and (spell_type == 'any' or spell_type in c.types))
                    matching_on_board = sum(1 for s in my_active_spells 
                                          if spell_type == 'any' or spell_type in s.card.types)
                    
                    if matching_in_hand + matching_on_board >= required_count:
                        combo_score += 60  # Condition will be met
                        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                            self.engine.ai_decision_logs.append(
                                f"\033[90m[AI-COMBO] {card.name} synergizes with {spell_type} spells!\033[0m"
                            )
        
        # Check if this card enables other cards' conditions
        for other_card in player.hand:
            if other_card == card:
                continue
                
            if other_card.resolve_effects:
                for effect in other_card.resolve_effects:
                    condition = effect.get('condition', {})
                    if condition.get('type') == 'if_caster_has_active_spell_of_type':
                        params = condition.get('parameters', {})
                        spell_type = params.get('spell_type', 'any')
                        if spell_type == 'any' or spell_type in card.types:
                            combo_score += 40  # This card enables another
                            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                                self.engine.ai_decision_logs.append(
                                    f"\033[90m[AI-COMBO] {card.name} enables {other_card.name}!\033[0m"
                                )
        
        # Check for passive effect synergies
        for spell in my_active_spells:
            # Coalesce changes OR to AND - powerful with choice cards
            if spell.card.passive_effects:
                for passive in spell.card.passive_effects:
                    if passive.get('type') == 'modify_spell_logic':
                        if 'player_choice' in str(card.resolve_effects):
                            combo_score += 100  # Very powerful combo
                            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                                self.engine.ai_decision_logs.append(
                                    f"\033[90m[AI-COMBO] {card.name} enhanced by spell logic modifier!\033[0m"
                                )
        
        # Type synergies - cards of the same type often work well together
        type_counts = {}
        for spell in my_active_spells:
            for spell_type in spell.card.types:
                type_counts[spell_type] = type_counts.get(spell_type, 0) + 1
        
        for card_type in card.types:
            if card_type in type_counts:
                combo_score += 20 * type_counts[card_type]
        
        # Element synergies
        element_count = sum(1 for s in my_active_spells if s.card.element == card.element)
        if element_count > 0:
            combo_score += 15 * element_count
        
        return combo_score
    
    def make_choice(self, valid_options, caster, gs, current_card):
        """Make strategic choices based on detailed game state analysis"""
        if not valid_options:
            return None
            
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-HARD] {caster.name} analyzing {len(valid_options)} options strategically\033[0m"
            )
        
        # Score each option
        option_scores = {}
        for i, option in enumerate(valid_options):
            score = self._evaluate_option(option, caster, gs, current_card)
            option_scores[i] = score
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                option_desc = self._describe_option(option)
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-HARD]   Option {i+1} ({option_desc}): score = {score}\033[0m"
                )
        
        # Final safety check - never choose lethal self-damage
        safe_options = {}
        for idx, score in option_scores.items():
            option = valid_options[idx]
            self_damage = self._get_self_damage_amount(option)
            if self_damage >= caster.health:
                # Skip lethal options entirely
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-SAFETY] Removing lethal option {idx+1} from consideration\033[0m"
                    )
                continue
            safe_options[idx] = score
        
        # If no safe options, choose the least bad option
        if not safe_options:
            best_idx = max(option_scores.items(), key=lambda x: x[1])[0]
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-HARD] WARNING: All options are lethal! Choosing least bad option.\033[0m"
                )
        else:
            best_idx = max(safe_options.items(), key=lambda x: x[1])[0]
        
        choice = valid_options[best_idx]
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-HARD] {caster.name} chose option {best_idx+1} (score: {option_scores[best_idx]})\033[0m"
            )
        
        return choice
    
    def _evaluate_option(self, option, caster, gs, current_card):
        """Score an option based on strategic value"""
        score = 0
        
        # Check if it's a risky option (self-damage)
        has_self_damage = self._has_self_damage(option)
        if has_self_damage:
            # Calculate risk/reward
            self_damage = self._get_self_damage_amount(option)
            if caster.health <= self_damage:
                # This would kill us - NEVER choose this
                score -= 10000  # Essentially impossible to choose
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-SAFETY] LETHAL self-damage detected! Health: {caster.health}, Damage: {self_damage}\033[0m"
                    )
            elif caster.health <= self_damage + 1:
                score -= 500  # Extremely dangerous
            elif caster.health <= 3:
                score -= 200  # Be very cautious at low health
            else:
                score -= self_damage * 20  # Increased penalty
        
        # Evaluate offensive options
        if self._is_attack_option(option):
            damage = self._get_option_damage(option)
            
            # Check enemy states
            enemies = [p for p in gs.players if p != caster]
            for enemy in enemies:
                if enemy.health <= damage:
                    score += 200  # Lethal damage
                elif enemy.health <= damage + 1:
                    score += 150  # Near-lethal damage
                else:
                    score += damage * 20  # General damage value
                
                # Bonus for attacking enemies with empty hands
                if len(enemy.hand) == 0:
                    score += 50
                    
            # Consider timing - early damage is often better
            if gs.clash_num <= 2:
                score += 30
        
        # Evaluate healing options
        if self._is_remedy_option(option):
            healing = self._get_option_healing(option)
            
            # Scale healing value based on health
            if caster.health <= 2:
                score += healing * 50  # Critical need
            elif caster.health <= 3:
                score += healing * 30  # High value
            elif caster.health <= 4:
                score += healing * 15  # Moderate value
            else:
                score += healing * 5   # Low priority when healthy
                
            # Avoid overhealing
            if caster.health + healing > caster.max_health:
                overheal = (caster.health + healing) - caster.max_health
                score -= overheal * 10
        
        # Evaluate advance options
        if self._is_advance_option(option):
            # Advancing is generally good for card advantage
            score += 60
            
            # Better in later rounds when we have more spells played
            if gs.round_num >= 2:
                score += 30
                
            # Check if we're advancing our own spell vs others
            if option.get('target') == 'this_spell':
                # Self-advance is reliable
                score += 20
            elif option.get('target') == 'friendly_spell':
                # Check if we have good spells to advance
                active_spells = [s for s in caster.board[gs.clash_num-1] if s.status == 'active']
                if active_spells:
                    score += 40
        
        # Special handling for Gust-like choices (advance self vs other)
        if current_card.name == 'Gust' and option.get('type') == 'advance':
            if option.get('target') == 'this_spell':
                # Self-advance for Gust - good for card advantage
                if len(caster.hand) <= 3:
                    score += 80  # High value when low on cards
                else:
                    score += 40
            else:
                # Advance other spell - situational
                active_spells = [s for s in caster.board[gs.clash_num-1] 
                               if s.status == 'active' and s.card.name != 'Gust']
                if active_spells:
                    # Bonus for advancing high-value spells
                    for spell in active_spells:
                        if 'attack' in spell.card.types:
                            score += 70
                        elif 'remedy' in spell.card.types:
                            score += 60
                        else:
                            score += 50
        
        # Add some randomness to prevent predictability
        score += random.randint(-15, 15)
        
        return score
    
    def _has_self_damage(self, option):
        """Check if an option involves self-damage"""
        if option.get('type') == 'sequence':
            for act in option.get('actions', []):
                if act.get('type') == 'damage' and act.get('target') == 'self':
                    return True
        elif option.get('type') == 'damage' and option.get('target') == 'self':
            return True
        return False
    
    def _get_self_damage_amount(self, option):
        """Get the amount of self-damage from an option"""
        if option.get('type') == 'damage' and option.get('target') == 'self':
            return option.get('parameters', {}).get('value', 0)
        elif option.get('type') == 'sequence':
            total = 0
            for act in option.get('actions', []):
                if act.get('type') == 'damage' and act.get('target') == 'self':
                    total += act.get('parameters', {}).get('value', 0)
            return total
        return 0
    
    def _is_attack_option(self, option):
        """Check if an option is primarily offensive"""
        attack_types = ['damage', 'weaken', 'damage_per_spell']
        if option.get('type') in attack_types:
            return True
        if option.get('type') == 'sequence':
            for act in option.get('actions', []):
                if act.get('type') in attack_types:
                    return True
        return False
    
    def _is_remedy_option(self, option):
        """Check if an option is primarily healing/defensive"""
        remedy_types = ['heal', 'bolster']
        if option.get('type') in remedy_types:
            return True
        if option.get('type') == 'sequence':
            for act in option.get('actions', []):
                if act.get('type') in remedy_types:
                    return True
        return False
    
    def _is_advance_option(self, option):
        """Check if an option involves advancing spells"""
        if option.get('type') == 'advance':
            return True
        if option.get('type') == 'sequence':
            for act in option.get('actions', []):
                if act.get('type') == 'advance':
                    return True
        return False
    
    def _get_option_damage(self, option):
        """Extract total damage value from an option"""
        if option.get('type') == 'damage':
            return option.get('parameters', {}).get('value', 0)
        elif option.get('type') == 'damage_per_spell':
            # Estimate based on typical board state
            active_spells = 2  # Conservative estimate
            return option.get('parameters', {}).get('value', 0) * active_spells
        elif option.get('type') == 'sequence':
            total_damage = 0
            for act in option.get('actions', []):
                if act.get('type') == 'damage':
                    total_damage += act.get('parameters', {}).get('value', 0)
            return total_damage
        return 0
    
    def _get_option_healing(self, option):
        """Extract total healing value from an option"""
        if option.get('type') == 'heal':
            return option.get('parameters', {}).get('value', 0)
        elif option.get('type') == 'sequence':
            total_healing = 0
            for act in option.get('actions', []):
                if act.get('type') == 'heal':
                    total_healing += act.get('parameters', {}).get('value', 0)
            return total_healing
        return 0
    
    def _describe_option(self, option):
        """Generate a description of the option for logging"""
        if option.get('type') == 'sequence':
            actions = []
            for act in option.get('actions', []):
                action_type = act.get('type', 'unknown')
                if action_type in ['damage', 'heal']:
                    value = act.get('parameters', {}).get('value', '')
                    target = act.get('target', '')
                    actions.append(f"{action_type} {value} to {target}")
                else:
                    actions.append(action_type)
            return f"[{' then '.join(actions)}]"
        else:
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