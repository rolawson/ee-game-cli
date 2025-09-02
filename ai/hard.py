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
        """Score a card based on game state - simplified and rebalanced"""
        score = 0
        
        # === CORE SCORING (High Priority) ===
        
        # 1. Health-based decisions (most critical)
        health_ratio = player.health / player.max_health
        if health_ratio <= 0.4:  # Below 40% health
            if 'remedy' in card.types:
                score += 100  # High priority
            if 'response' in card.types:
                score += 60   # Defense is good
            if 'attack' in card.types and health_ratio > 0.2:
                score += 40   # Still need offense unless critical
        elif health_ratio >= 0.7:  # Above 70% health
            if 'attack' in card.types:
                score += 60   # Prioritize offense when healthy
            if 'boost' in card.types:
                score += 50   # Support spells are good
                
        # 2. Enemy vulnerability (capitalize on weakness)
        for enemy in gs.players:
            if enemy != player:
                enemy_health_ratio = enemy.health / enemy.max_health
                if enemy_health_ratio <= 0.4 and 'attack' in card.types:
                    score += 80  # Push for the kill
                if len(enemy.hand) == 0:
                    # Enemy can't play - be aggressive
                    if 'attack' in card.types:
                        score += 70
                    if 'boost' in card.types:
                        score += 60  # Safe to set up
                        
        # 3. Priority/Speed (simplified)
        if card.priority != 'A':
            priority_val = int(card.priority)
            if gs.clash_num <= 2:
                # Early game - faster is better
                score += (6 - priority_val) * 8
            else:
                # Late game - power matters more
                score += (6 - priority_val) * 4
        else:
            # Advance priority - best early
            if gs.clash_num <= 2:
                score += 40
            elif gs.clash_num == 3:
                score += 20
                
        # === SECONDARY SCORING (Medium Priority) ===
        
        # 4. Basic type scoring
        if 'response' in card.types and gs.clash_num >= 2:
            score += 35  # Responses better after turn 1
        if 'conjury' in card.types and gs.clash_num <= 2:
            score += 45  # Conjuries best early
        if 'boost' in card.types and len(player.hand) >= 3:
            score += 30  # Boosts when we have cards to play
            
        # 5. Combo check (simplified - only immediate combos)
        immediate_combo_score = self._check_immediate_combos(card, player, gs)
        score += immediate_combo_score
        
        # 6. Card advantage
        effects_str = str(card.resolve_effects) + str(card.advance_effects)
        if 'recall' in effects_str or 'cast_extra_spell' in effects_str:
            score += 40  # Card advantage is valuable
        if 'advance' in effects_str and 'this_spell' in effects_str:
            score += 35  # Self-advancing is good
            
        # === MINOR ADJUSTMENTS ===
        
        # 7. Hand size bonus
        if len(player.hand) <= 2:
            if card.priority == 'A':
                score += 20  # Cards that come back
            if 'remedy' in card.types:
                score += 15  # Stay alive
                
        # 8. Element bonus (simplified)
        element_bonus = self._get_simple_element_bonus(card.element, player, gs)
        score += element_bonus
        
        # 9. Restrictions
        if gs.clash_num == 1 and card.notfirst == 1:
            score -= 30
        elif gs.clash_num == 4 and card.notlast == 1:
            score -= 30
            
        # 10. Small random factor
        score += random.randint(-5, 5)
        
        return score
    
    def _check_immediate_combos(self, card, player, gs):
        """Check for combos that can trigger THIS turn only"""
        score = 0
        
        # Get my active spells in current clash
        my_active_spells = [s for s in player.board[gs.clash_num - 1] 
                           if s.status == 'revealed']
        
        # Check if this card's conditions are already met
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            if condition.get('type') == 'if_caster_has_active_spell_of_type':
                params = condition.get('parameters', {})
                spell_type = params.get('spell_type', 'any')
                required = params.get('count', 1)
                exclude_self = params.get('exclude_self', False)
                
                # Count matching spells already on board
                matches = 0
                for spell in my_active_spells:
                    if spell_type == 'any' or spell_type in spell.card.types:
                        matches += 1
                
                # Will the condition be met when we play this?
                if not exclude_self and (spell_type == 'any' or spell_type in card.types):
                    matches += 1  # This card counts too
                    
                if matches >= required:
                    score += 50  # Condition WILL trigger
                    if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                        self.engine.ai_decision_logs.append(
                            f"\033[90m[AI-COMBO] {card.name} combo ready with {spell_type} spells!\033[0m"
                        )
                        
            elif condition.get('type') == 'if_enemy_has_active_spell_of_type':
                # Response spells that trigger off enemy spells
                params = condition.get('parameters', {})
                spell_type = params.get('spell_type', 'any')
                required = params.get('count', 1)
                
                # Count enemy spells across ALL clashes
                enemy_matches = 0
                for enemy in gs.players:
                    if enemy != player:
                        for clash_idx in range(gs.clash_num):
                            for spell in enemy.board[clash_idx]:
                                if spell.status == 'revealed':
                                    if spell_type == 'any' or spell_type in spell.card.types:
                                        enemy_matches += 1
                
                if enemy_matches >= required:
                    # This is a GREAT time to play this response spell
                    if 'response' in card.types:
                        score += 80  # High value for guaranteed response trigger
                    else:
                        score += 60
                    if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                        self.engine.ai_decision_logs.append(
                            f"\033[90m[AI-RESPONSE] {card.name} will trigger - enemies have {enemy_matches} {spell_type} spells!\033[0m"
                        )
        
        # Special synergies with specific active spells
        for spell in my_active_spells:
            # Coalesce turns OR to AND
            if spell.card.name == 'Coalesce' and 'player_choice' in str(card.resolve_effects):
                score += 80  # Very powerful combo
                
        return score
    
    def _get_simple_element_bonus(self, element, player, gs):
        """Simple element-based bonus"""
        score = 0
        
        # Count same element already played
        same_element_count = 0
        for i in range(gs.clash_num):
            for spell in player.board[i]:
                if spell.card.element == element:
                    same_element_count += 1
                    
        # Small bonus for element synergy
        if same_element_count > 0:
            score += min(same_element_count * 10, 30)  # Cap at 30
            
        # Category-based bonus (simplified)
        category = self.get_element_category(element)
        if category == 'offense' and any(p.health <= 3 for p in gs.players if p != player):
            score += 15  # Offense good when enemies are weak
        elif category == 'defense' and player.health <= 3:
            score += 15  # Defense good when we're weak
        elif category == 'mobility' and 2 <= gs.clash_num <= 3:
            score += 10  # Mobility good mid-game
            
        return score
    
    def _evaluate_card_mobility(self, card, player, gs):
        """Evaluate cards based on their movement/positioning capabilities"""
        score = 0
        
        # Check card's own mobility features
        effects_str = str(card.resolve_effects) + str(card.advance_effects)
        
        # Self-advancing cards (like Flow)
        if 'advance' in effects_str and 'this_spell' in effects_str:
            if gs.clash_num < 3:  # Can advance at least once
                score += 40
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MOBILITY] {card.name} can self-advance for future value\033[0m"
                    )
        
        # Cards that move other spells (like Gravitate)
        if 'move_to_future_clash' in effects_str:
            # Valuable for disrupting enemy plans or saving own spells
            score += 35
            if gs.clash_num < 3:  # More valuable early
                score += 20
        
        # Cards that recall spells
        if 'recall' in effects_str:
            if 'from_board' in effects_str:
                # Can steal enemy spells from board
                score += 45
            elif 'friendly_past_spells' in effects_str:
                # Can reuse own spells - check if we have valid targets
                past_spells_count = self._count_past_spells(player, gs, include_cancelled=True)
                if past_spells_count > 0:
                    score += 30 + (10 * min(past_spells_count, 3))
                else:
                    score -= 50  # No targets - bad play
                    if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                        self.engine.ai_decision_logs.append(
                            f"\033[90m[AI-MOBILITY] {card.name} has no past spells to recall!\033[0m"
                        )
            elif 'from_enemy_hand' in effects_str:
                # Hand disruption + gain
                score += 50
        
        # Cards that allow extra spell casting
        if 'cast_extra_spell' in effects_str:
            extra_cards = len(player.hand) - 1
            if extra_cards > 0:
                score += 30 * min(extra_cards, 2)  # Value capped at 2 extra
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MOBILITY] {card.name} enables spell burst with {extra_cards} options\033[0m"
                    )
        
        # Cards that advance other spells
        if 'advance' in effects_str and 'prompt' in effects_str:
            # Check if we have good targets to advance
            advance_targets = 0
            for i in range(gs.clash_num):
                for spell in player.board[i]:
                    if spell.status == 'revealed':
                        # High-value advance targets
                        if spell.card.is_conjury or 'boost' in spell.card.types:
                            advance_targets += 1
            
            if advance_targets > 0:
                score += 25 * advance_targets
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MOBILITY] {card.name} can advance {advance_targets} high-value targets\033[0m"
                    )
        
        # Evaluate positioning strategy
        position_score = self._evaluate_positioning(card, player, gs)
        score += position_score
        
        return score
    
    def _evaluate_positioning(self, card, player, gs):
        """Evaluate strategic positioning of this card"""
        score = 0
        
        # Cards that benefit from being in future clashes
        if card.advance_effects and gs.clash_num < 4:
            # This card wants to advance
            if 'advance_from_hand' in str(card.resolve_effects):
                # Can place itself in future - very flexible
                score += 30
            
        # Cards vulnerable to movement/cancellation
        if card.is_conjury:
            # Conjuries are vulnerable to being moved/cancelled
            # Less valuable if opponent has movement cards
            for opponent in gs.players:
                if opponent != player:
                    remaining = self.get_remaining_spells(opponent.name)
                    if any('gravitate' in spell.lower() or 'move' in spell.lower() 
                          for spell in remaining):
                        score -= 20
                        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                            self.engine.ai_decision_logs.append(
                                f"\033[90m[AI-MOBILITY] {card.name} vulnerable to opponent's movement spells\033[0m"
                            )
        
        # Priority-based positioning
        if card.priority == 'A':
            # Advance priority cards benefit from early placement
            if gs.clash_num <= 2:
                score += 20  # Can advance multiple times
        elif card.priority in ['1', '2']:
            # Fast cards good for getting effects off early
            score += 10
        
        return score
    
    def _count_past_spells(self, player, gs, include_cancelled=False):
        """Count spells in past clashes that could be recalled"""
        count = 0
        for i in range(gs.clash_num - 1):  # Only past clashes
            for spell in player.board[i]:
                if spell.status == 'revealed' or (include_cancelled and spell.status == 'cancelled'):
                    count += 1
        return count
    
    def _evaluate_hand_synergies(self, card, player, gs):
        """Evaluate synergies between cards in hand for multi-turn planning"""
        score = 0
        # Handle case where card is None (evaluating whole hand)
        if card is None:
            other_cards = player.hand
        else:
            other_cards = [c for c in player.hand if c != card]
        
        if not other_cards:
            return 0
        
        # Check if this card enables future cards
        future_enablement_score = 0
        for future_card in other_cards:
            if future_card.resolve_effects:
                for effect in future_card.resolve_effects:
                    condition = effect.get('condition', {})
                    if condition.get('type') == 'if_caster_has_active_spell_of_type':
                        params = condition.get('parameters', {})
                        spell_type = params.get('spell_type', 'any')
                        
                        # This card enables the future card
                        if card and (spell_type == 'any' or spell_type in card.types):
                            future_enablement_score += 50
                            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                                self.engine.ai_decision_logs.append(
                                    f"\033[90m[AI-SYNERGY] {card.name} enables {future_card.name} next turn!\033[0m"
                                )
                    
                    elif condition.get('type') == 'if_spell_previously_resolved_this_round':
                        # Playing this card early enables the condition later
                        if gs.clash_num <= 2:
                            future_enablement_score += 40
        
        # Check if holding this card enables better combos later
        hold_value = 0
        if card and card.resolve_effects:
            for effect in card.resolve_effects:
                condition = effect.get('condition', {})
                if condition.get('type') == 'if_caster_has_active_spell_of_type':
                    # This card needs other spells - check if we can play them first
                    params = condition.get('parameters', {})
                    spell_type = params.get('spell_type', 'any')
                    required_count = params.get('count', 1)
                    
                    enablers_in_hand = sum(1 for c in other_cards 
                                         if spell_type == 'any' or spell_type in c.types)
                    
                    if enablers_in_hand >= required_count and gs.clash_num < 3:
                        # We have enablers - maybe wait to play this card
                        hold_value -= 30  # Negative score encourages waiting
                        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                            self.engine.ai_decision_logs.append(
                                f"\033[90m[AI-SYNERGY] {card.name} could wait for {spell_type} enablers\033[0m"
                            )
        
        # Multi-card combo detection
        combo_chains = self._detect_combo_chains(card, other_cards, gs)
        chain_score = len(combo_chains) * 40
        if combo_chains and self.engine and hasattr(self.engine, 'ai_decision_logs'):
            chain_names = [c.name for c in combo_chains]
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-SYNERGY] Combo chain detected: {card.name if card else 'Hand'} -> {' -> '.join(chain_names)}\033[0m"
            )
        
        # Element/type clustering bonus
        same_element_count = 0
        same_type_overlap = 0
        if card:
            same_element_count = sum(1 for c in other_cards if c.element == card.element)
            for c in other_cards:
                same_type_overlap += len(set(card.types) & set(c.types))
        
        clustering_score = (same_element_count * 10) + (same_type_overlap * 15)
        
        return future_enablement_score + hold_value + chain_score + clustering_score
    
    def _detect_combo_chains(self, start_card, other_cards, gs):
        """Detect multi-card combo chains starting with this card"""
        chains = []
        
        # Handle None card
        if not start_card:
            return chains
        
        # Simple 2-card chains for now
        for next_card in other_cards:
            # Check if start_card enables next_card
            enables = False
            
            if next_card.resolve_effects:
                for effect in next_card.resolve_effects:
                    condition = effect.get('condition', {})
                    if condition.get('type') == 'if_caster_has_active_spell_of_type':
                        params = condition.get('parameters', {})
                        spell_type = params.get('spell_type', 'any')
                        if spell_type == 'any' or spell_type in start_card.types:
                            enables = True
                            break
            
            if enables:
                chains.append(next_card)
        
        return chains
    
    def _evaluate_card_counting(self, card, player, gs):
        """Use card counting to make strategic decisions"""
        score = 0
        
        for opponent in gs.players:
            if opponent == player:
                continue
            
            # Get remaining spells for this opponent
            remaining_spells = self.get_remaining_spells(opponent.name)
            history = self.opponent_history.get(opponent.name, {})
            known_sets = history.get('known_sets', [])
            
            if not known_sets:
                continue
                
            # Analyze threats in opponent's remaining cards
            remaining_threats = self._analyze_remaining_threats(remaining_spells, gs)
            
            # Adjust strategy based on what's coming
            if remaining_threats['high_damage_count'] > 0:
                # Opponent has big damage spells left
                if 'remedy' in card.types:
                    score += 40
                if 'response' in card.types and 'damage' in str(card.resolve_effects):
                    score += 35  # Retaliation is good
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-COUNTING] {opponent.name} has {remaining_threats['high_damage_count']} high damage spells remaining\033[0m"
                    )
            
            if remaining_threats['cancel_count'] > 0:
                # Opponent has cancellation left
                if card.is_conjury:
                    score -= 20  # Conjuries are risky
                if 'response' in card.types:
                    score += 15  # Responses are harder to cancel
                    
            if remaining_threats['discard_count'] > 0 and len(player.hand) <= 3:
                # Low on cards and opponent has discard
                if card.priority == 'A':
                    score += 20  # Play cards that can come back
                    
            # Element-specific strategies
            for elephant in known_sets:
                remaining_for_set = self.get_remaining_spells(opponent.name, elephant)
                if len(remaining_for_set) == 1:
                    # We know their last card from this set!
                    if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                        self.engine.ai_decision_logs.append(
                            f"\033[90m[AI-COUNTING] {opponent.name}'s last {elephant} spell must be: {remaining_for_set[0]}\033[0m"
                        )
                    # Could add specific counters here
        
        return score
    
    def _analyze_remaining_threats(self, spell_names, gs):
        """Analyze what threats remain in opponent's unplayed spells"""
        threats = {
            'high_damage_count': 0,
            'cancel_count': 0,
            'discard_count': 0,
            'heal_count': 0,
            'weaken_count': 0
        }
        
        # Look up each spell in game data
        for spell_name in spell_names:
            # Find the card data
            for card_id, card in gs.all_cards.items():
                if card.name == spell_name:
                    # Analyze the spell's effects
                    effects_str = str(card.resolve_effects)
                    if 'damage' in effects_str and 'value": 2' in effects_str:
                        threats['high_damage_count'] += 1
                    if 'cancel' in effects_str:
                        threats['cancel_count'] += 1
                    if 'discard' in effects_str:
                        threats['discard_count'] += 1
                    if 'heal' in effects_str:
                        threats['heal_count'] += 1
                    if 'weaken' in effects_str:
                        threats['weaken_count'] += 1
                    break
        
        return threats
    
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
    
    def _evaluate_response_counterplay(self, card, player, gs):
        """Evaluate response spells for counter-play potential"""
        score = 0
        
        # Check what this response counters
        for effect in card.resolve_effects:
            condition = effect.get('condition', {})
            cond_type = condition.get('type', '')
            
            # Damage-based responses (like Reflect)
            if cond_type == 'if_caster_damaged_last_turn':
                # Check if we've been taking damage
                if gs.round_num > 1 or gs.clash_num > 1:
                    score += 40  # Likely to trigger
                    
                    # Extra value if opponent is aggressive
                    for opponent in gs.players:
                        if opponent != player:
                            analysis = self.analyze_opponent_patterns(opponent.name)
                            if analysis and analysis.get('aggression_level', 0) > 0.5:
                                score += 30
                                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                                    self.engine.ai_decision_logs.append(
                                        f"\033[90m[AI-COUNTER] {card.name} counters aggressive opponent\033[0m"
                                    )
                else:
                    score -= 30  # Early game, less likely
            
            # Enemy spell responses
            elif cond_type == 'if_enemy_has_active_spell_of_type':
                params = condition.get('parameters', {})
                spell_type = params.get('spell_type', 'any')
                
                # Check if enemies are likely to play this type
                likely_to_trigger = False
                for opponent in gs.players:
                    if opponent != player:
                        remaining = self.get_remaining_spells(opponent.name)
                        type_count = sum(1 for spell in remaining 
                                       if spell_type == 'any' or spell_type in str(spell).lower())
                        if type_count > 0:
                            likely_to_trigger = True
                            score += 20
                
                if not likely_to_trigger:
                    score -= 40  # Won't trigger
        
        # Response spells are great for baiting
        if gs.clash_num >= 2:
            score += 20  # More value as game progresses
        
        return score
    
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
        """Score an option based on strategic value - simplified"""
        score = 0
        
        # 1. Self-damage evaluation (reduced penalties)
        self_damage = self._get_self_damage_amount(option)
        if self_damage > 0:
            health_after = caster.health - self_damage
            if health_after <= 0:
                score -= 1000  # Still avoid lethal
            elif health_after == 1:
                score -= 100   # Very risky
            elif health_after <= 2:
                score -= 50    # Risky
            else:
                score -= self_damage * 10  # Moderate penalty
                
            # But if the payoff is good, it might be worth it
            if self._is_attack_option(option):
                damage = self._get_option_damage(option)
                if damage >= 3:  # High damage output
                    score += damage * 15  # Offset some penalty
        
        # 2. Attack options
        if self._is_attack_option(option):
            damage = self._get_option_damage(option)
            
            # Base damage value
            score += damage * 25
            
            # Bonus for potentially lethal damage
            enemies = [p for p in gs.players if p != caster]
            for enemy in enemies:
                if enemy.health <= damage:
                    score += 100  # Lethal
                elif enemy.health <= damage + 1:
                    score += 50   # Near-lethal
        
        # 3. Healing options
        if self._is_remedy_option(option):
            healing = self._get_option_healing(option)
            health_ratio = caster.health / caster.max_health
            
            if health_ratio <= 0.3:
                score += healing * 40  # Critical
            elif health_ratio <= 0.5:
                score += healing * 25  # Important
            else:
                score += healing * 10  # Nice to have
                
            # Small penalty for overhealing
            if caster.health + healing > caster.max_health:
                overheal = (caster.health + healing) - caster.max_health
                score -= overheal * 5
        
        # 4. Other beneficial effects
        if option.get('type') == 'advance':
            score += 40  # Card advantage
            if option.get('target') == 'this_spell':
                score += 10  # Reliable
                
        if option.get('type') == 'bolster':
            score += 30  # Max health increase
            
        if option.get('type') == 'weaken':
            score += 35  # Enemy debuff
            
        if option.get('type') == 'cancel' or option.get('type') == 'discard':
            score += 45  # Disruption
            
        # 5. Pass option (doing nothing)
        if option.get('type') == 'pass':
            score -= 20  # Generally want to do something
            
        # Small random factor
        score += random.randint(-10, 10)
        
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
    
    def choose_draft_set(self, player, gs, available_sets):
        """Strategic drafting for Hard AI with opponent awareness
        
        Evaluates each available set based on:
        - Spell type balance
        - Element synergies  
        - Priority distribution
        - Combo potential
        - Counter-play options
        - Opponent element tracking
        - Exploration incentives
        """
        if not available_sets:
            return None
        
        # Analyze what we already have (if this is second draft)
        current_cards = player.discard_pile  # Cards from first draft
        
        # Track opponent elements if they drafted first
        opponent_elements = []
        for p in gs.players:
            if p != player and p.discard_pile:
                # Get elements from their drafted cards
                for card in p.discard_pile:
                    if card.element not in opponent_elements:
                        opponent_elements.append(card.element)
        
        # Track our element pick history for variety
        if not hasattr(self, 'element_pick_history'):
            self.element_pick_history = []
        if not hasattr(self, 'strategy_mode'):
            # Randomly choose a strategy for this game
            self.strategy_mode = random.choice(['aggressive', 'defensive', 'balanced', 'experimental'])
        
        # Calculate weights for each set based on multiple factors
        set_weights = {}
        
        for set_idx, spell_set in enumerate(available_sets):
            element = spell_set[0].element
            category = self.get_element_category(element)
            
            # Start with base weight of 1.0
            weight = 1.0
            
            # 1. PRIMARY FACTOR: Win rate (if we have data)
            if self.element_win_rates.get('total_games', 0) >= 50:
                win_rate = self.get_element_win_rate(element)
                # Adjust weight based on win rate (0.5 to 2.0 range)
                weight *= (0.5 + win_rate * 1.5)
                
                # Penalize overselected elements
                selection_rate = self.element_win_rates.get('selection_rates', {}).get(element, 0)
                if selection_rate > 0.15:  # Over 15%
                    weight *= 0.3  # Strong penalty
                elif selection_rate > 0.10:  # Over 10%
                    weight *= 0.6  # Moderate penalty
            
            # 2. Skip counter-selection - should use real data, not hardcoded relationships
            
            # 3. Basic category preference (small factor)
            if self.strategy_mode == 'aggressive' and category == 'offense':
                weight *= 1.2
            elif self.strategy_mode == 'defensive' and category == 'defense':
                weight *= 1.2
            elif category == 'mobility':
                weight *= 1.1  # Slight preference for mobility
            
            # 4. Variety bonus (avoid repeating recent picks)
            if element in self.element_pick_history[-6:]:
                weight *= 0.7  # Discourage recent repeats
            
            # Store normalized weight
            set_weights[set_idx] = max(weight, 0.1)  # Minimum weight of 0.1
            
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                win_rate = self.get_element_win_rate(element) if self.element_win_rates.get('total_games', 0) >= 50 else 0.5
                selection_rate = self.element_win_rates.get('selection_rates', {}).get(element, 0)
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[AI-DRAFT] {element}: weight={weight:.2f}, win_rate={win_rate:.1%}, selection_rate={selection_rate:.1%}\\033[0m"
                )
        
        # Use weighted random selection
        total_weight = sum(set_weights.values())
        if total_weight == 0:
            # Fallback to equal weights if something went wrong
            best_idx = random.choice(list(range(len(available_sets))))
        else:
            # Weighted random choice
            rand_val = random.random() * total_weight
            cumulative = 0
            best_idx = 0
            
            for idx, weight in set_weights.items():
                cumulative += weight
                if rand_val <= cumulative:
                    best_idx = idx
                    break
        
        chosen_set = available_sets[best_idx]
        
        # Track our pick
        self.element_pick_history.append(chosen_set[0].element)
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            element = chosen_set[0].element
            final_weight = set_weights[best_idx]
            win_rate = self.get_element_win_rate(element) if self.element_win_rates.get('total_games', 0) >= 50 else 0.5
            self.engine.ai_decision_logs.append(
                f"\\033[90m[AI-DRAFT] Chose {chosen_set[0].elephant} ({element}) "
                f"with weight {final_weight:.2f} (win_rate: {win_rate:.1%})\\033[0m"
            )
        
        return chosen_set
    
    def _analyze_spell_set(self, spell_set, gs):
        """Analyze a spell set's composition"""
        analysis = {
            'types': {},
            'priorities': {},
            'has_conjury': False,
            'element': spell_set[0].element if spell_set else None,
            'elephant': spell_set[0].elephant if spell_set else None,
            'effects': []
        }
        
        for spell in spell_set:
            # Count types
            for spell_type in spell.types:
                analysis['types'][spell_type] = analysis['types'].get(spell_type, 0) + 1
            
            # Count priorities
            priority = spell.priority
            analysis['priorities'][priority] = analysis['priorities'].get(priority, 0) + 1
            
            # Check for conjury
            if spell.is_conjury:
                analysis['has_conjury'] = True
            
            # Collect effects
            effects_str = str(spell.resolve_effects) + str(spell.advance_effects)
            if 'damage' in effects_str:
                analysis['effects'].append('damage')
            if 'heal' in effects_str:
                analysis['effects'].append('heal')
            if 'cancel' in effects_str:
                analysis['effects'].append('cancel')
            if 'discard' in effects_str:
                analysis['effects'].append('discard')
            if 'advance' in effects_str:
                analysis['effects'].append('advance')
            if 'recall' in effects_str:
                analysis['effects'].append('recall')
        
        return analysis
    
    def _evaluate_type_balance(self, set_analysis, current_cards):
        """Evaluate type balance for a well-rounded deck"""
        score = 0
        
        # Count current types
        current_types = {}
        for card in current_cards:
            for spell_type in card.types:
                current_types[spell_type] = current_types.get(spell_type, 0) + 1
        
        # Ideal distribution (rough guidelines)
        ideal_ratios = {
            'attack': 0.3,    # 30% damage dealers
            'response': 0.2,  # 20% counter-play
            'remedy': 0.2,    # 20% healing/defense
            'boost': 0.15,    # 15% support
            'conjury': 0.15   # 15% persistent effects
        }
        
        # Calculate how this set helps balance
        total_cards = len(current_cards) + 6  # Assuming 6 cards per set
        
        for spell_type, count in set_analysis['types'].items():
            current_count = current_types.get(spell_type, 0)
            new_ratio = (current_count + count) / total_cards
            ideal_ratio = ideal_ratios.get(spell_type, 0.1)
            
            # Score based on how close to ideal
            deviation = abs(new_ratio - ideal_ratio)
            if deviation < 0.1:
                score += 50  # Very close to ideal
            elif deviation < 0.2:
                score += 30  # Reasonably close
            else:
                score += 10  # Still adds diversity
        
        # Penalty for missing important types
        combined_types = set(current_types.keys()) | set(set_analysis['types'].keys())
        if 'attack' not in combined_types:
            score -= 100  # Need damage
        if 'remedy' not in combined_types:
            score -= 80   # Need healing
        if 'response' not in combined_types:
            score -= 40   # Responses are valuable
        
        return score
    
    def _evaluate_priority_distribution(self, set_analysis, current_cards):
        """Evaluate priority distribution for tactical flexibility"""
        score = 0
        
        # Count current priorities
        current_priorities = {}
        for card in current_cards:
            priority = card.priority
            current_priorities[priority] = current_priorities.get(priority, 0) + 1
        
        # Good to have mix of speeds
        priorities = set_analysis['priorities']
        
        # Reward variety
        unique_priorities = len(priorities)
        score += unique_priorities * 20
        
        # Check for good distribution
        if 'A' in priorities:
            score += 40  # Advance priority is valuable
        if '1' in priorities or '2' in priorities:
            score += 30  # Fast spells are good
        if '4' in priorities or '5' in priorities:
            score += 20  # Some slow spells for power
        
        # Penalty for too many of same priority
        for priority, count in priorities.items():
            if count > 3:
                score -= (count - 3) * 20
        
        return score
    
    def _evaluate_set_combos(self, spell_set, gs):
        """Evaluate internal combo potential within the set"""
        score = 0
        
        # Check each spell against others in set
        for i, spell1 in enumerate(spell_set):
            for j, spell2 in enumerate(spell_set):
                if i >= j:
                    continue
                
                # Check if spell1 enables spell2
                if spell2.resolve_effects:
                    for effect in spell2.resolve_effects:
                        condition = effect.get('condition', {})
                        if condition.get('type') == 'if_caster_has_active_spell_of_type':
                            params = condition.get('parameters', {})
                            spell_type = params.get('spell_type', 'any')
                            if spell_type == 'any' or spell_type in spell1.types:
                                score += 60  # Strong combo
                
                # Element synergy
                if spell1.element == spell2.element:
                    score += 10
                
                # Type synergy - don't reward just having multiple types
                # Only reward meaningful synergies
                pass
        
        # Check for self-sufficient combos
        has_enablers = False
        has_payoffs = False
        
        for spell in spell_set:
            effects_str = str(spell.resolve_effects)
            if 'if_caster_has_active_spell' in effects_str:
                has_payoffs = True
            if any(t in spell.types for t in ['boost', 'remedy']):
                has_enablers = True
        
        if has_enablers and has_payoffs:
            score += 80  # Self-sufficient combo potential
        
        return score
    
    def _evaluate_element_synergy(self, spell_set, current_cards):
        """Evaluate element synergy with existing cards"""
        score = 0
        
        set_element = spell_set[0].element
        
        # Count elements in current cards
        element_counts = {}
        for card in current_cards:
            element = card.element
            element_counts[element] = element_counts.get(element, 0) + 1
        
        # Some diversity is good, but some concentration enables combos
        if set_element in element_counts:
            # Adding to existing element
            current_count = element_counts[set_element]
            if current_count <= 3:
                score += 40  # Good concentration
            else:
                score += 20  # Still okay but diminishing returns
        else:
            # New element
            if len(element_counts) < 2:
                score += 60  # First diversity is valuable
            else:
                score += 30  # More diversity still good
        
        return score
    
    def _evaluate_counter_potential(self, set_analysis):
        """Evaluate ability to counter opponent strategies"""
        score = 0
        
        # Response spells are great counters
        if 'response' in set_analysis['types']:
            score += set_analysis['types']['response'] * 40
        
        # Disruption effects
        if 'cancel' in set_analysis['effects']:
            score += 60
        if 'discard' in set_analysis['effects']:
            score += 50
        
        # Conjury disruption
        if set_analysis['has_conjury']:
            score += 30  # Conjuries can be disruptive
        
        # Fast spells can disrupt timing
        fast_count = (set_analysis['priorities'].get('1', 0) + 
                     set_analysis['priorities'].get('2', 0))
        if fast_count > 0:
            score += fast_count * 20
        
        return score
    
    def _evaluate_special_abilities(self, spell_set):
        """Evaluate unique and powerful abilities"""
        score = 0
        
        for spell in spell_set:
            effects_str = str(spell.resolve_effects) + str(spell.advance_effects)
            
            # Movement abilities
            if 'move_to_future_clash' in effects_str:
                score += 40
            if 'recall' in effects_str:
                score += 50
            if 'advance' in effects_str:
                score += 35
            
            # Card advantage
            if 'cast_extra_spell' in effects_str:
                score += 60
            if 'draw' in effects_str:
                score += 40
            
            # Powerful effects
            if 'damage_per_spell' in effects_str:
                score += 45
            if 'modify_spell_logic' in str(spell.passive_effects):
                score += 80  # Very powerful
            
            # Flexibility
            if 'player_choice' in effects_str:
                score += 30
        
        return score
    
    def _evaluate_element_category(self, spell_set, current_cards, gs):
        """Evaluate spell set based on element category strategy"""
        score = 0
        
        if not spell_set:
            return 0
            
        set_element = spell_set[0].element
        set_category = self.get_element_category(set_element)
        
        # Base score from real-world win rates instead of draft priority
        # Use win rate data if we have enough games
        if self.element_win_rates.get('total_games', 0) >= 50:
            win_rate = self.get_element_win_rate(set_element)
            # Convert win rate to score: 50% = 0, 75% = +50, 25% = -50
            win_rate_score = (win_rate - 0.5) * 200
            score += win_rate_score
            
            # Also penalize overselected elements to encourage variety
            selection_rate = self.element_win_rates.get('selection_rates', {}).get(set_element, 0)
            expected_rate = 1.0 / 19  # ~5.3% for 19 elements
            if selection_rate > expected_rate * 2:  # Over 10%
                score -= 30  # Penalty for overselection
        else:
            # Fallback to original draft priority if not enough data
            draft_priority = self.get_element_draft_priority(set_element)
            score += (draft_priority - 1.0) * 100
        
        # Evaluate synergies with spell types in the set
        type_synergy_score = 0
        for spell in spell_set:
            for spell_type in spell.types:
                synergy = self.get_element_synergy(set_element, spell_type)
                if synergy > 1.0:
                    type_synergy_score += (synergy - 1.0) * 50
        score += type_synergy_score
        
        # Check current deck composition
        if current_cards:
            current_categories = {}
            for card in current_cards:
                category = self.get_element_category(card.element)
                current_categories[category] = current_categories.get(category, 0) + 1
            
            # Strategic category balancing
            if set_category == 'offense':
                # Offense is good, but needs defense backup
                if current_categories.get('defense', 0) == 0:
                    score -= 30  # Penalty for all offense
                else:
                    score += 40  # Good to have offense
                    
            elif set_category == 'defense':
                # Defense is valuable but needs offense
                if current_categories.get('offense', 0) == 0:
                    score -= 20  # Need some offense
                else:
                    score += 50  # Defense is valuable
                    
            elif set_category == 'mobility':
                # Mobility is excellent for flexibility
                score += 60
                # Even better if we have good offense/defense base
                if current_categories.get('offense', 0) > 0 and current_categories.get('defense', 0) > 0:
                    score += 30  # Great complement
                    
            elif set_category == 'balanced':
                # Balanced elements are always solid choices
                score += 45
                # Especially good for first pick
                if len(current_cards) == 0:
                    score += 20
        
        # Log decision
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            if self.element_win_rates.get('total_games', 0) >= 50:
                win_rate = self.get_element_win_rate(set_element)
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[AI-DRAFT] {set_element} ({set_category}): "
                    f"win_rate={win_rate:.1%}, score={score:.0f}\\033[0m"
                )
            else:
                draft_priority = self.get_element_draft_priority(set_element)
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[AI-DRAFT] {set_element} ({set_category}): "
                    f"priority={draft_priority:.1f}, score={score:.0f}\\033[0m"
                )
        
        return score
    
    def _evaluate_element_play(self, card, player, gs):
        """Evaluate card based on element category during gameplay"""
        score = 0
        
        element = card.element
        category = self.get_element_category(element)
        
        # Situational bonuses based on element category
        if category == 'offense':
            # Offense elements excel when enemies are vulnerable
            enemies = [p for p in gs.players if p != player]
            for enemy in enemies:
                if enemy.health <= 3:
                    score += 15  # Push advantage
                if len(enemy.hand) <= 1:
                    score += 10  # They can't defend well
                    
        elif category == 'defense':
            # Defense elements shine when we need protection
            if player.health <= 3:
                score += 20  # Critical timing
            # Also good when enemies are aggressive
            for opponent in gs.players:
                if opponent != player:
                    analysis = self.analyze_opponent_patterns(opponent.name)
                    if analysis and analysis.get('aggression_level', 0) > 0.6:
                        score += 15
                        
        elif category == 'mobility':
            # Mobility excels in mid-game for positioning
            if 2 <= gs.clash_num <= 3:
                score += 15
            # Extra value if we have cards to move/advance
            if len(player.hand) >= 2:
                score += 10
                
        elif category == 'balanced':
            # Balanced elements are consistently good
            score += 10
            # Especially in early game
            if gs.clash_num == 1:
                score += 10
        
        # Check for element-type synergies
        for spell_type in card.types:
            synergy = self.get_element_synergy(element, spell_type)
            if synergy > 1.0:
                score += (synergy - 1.0) * 30
        
        return score
    
    def _evaluate_counter_play_potential(self, spell_set, opponent_elements):
        """Evaluate how well this set counters known opponent elements"""
        score = 0
        
        for spell in spell_set:
            effects_str = str(spell.resolve_effects) + str(spell.advance_effects)
            
            # Check for specific counters to opponent elements
            for opp_elem in opponent_elements:
                opp_category = self.get_element_category(opp_elem)
                
                # Counter strategies
                if opp_category == 'offense':
                    # Counter offense with healing/defense
                    if 'remedy' in spell.types:
                        score += 15
                    if 'bolster' in effects_str:
                        score += 10
                        
                elif opp_category == 'defense':
                    # Counter defense with disruption
                    if 'cancel' in effects_str or 'discard' in effects_str:
                        score += 15
                    if 'weaken' in effects_str:
                        score += 20
                        
                elif opp_category == 'mobility':
                    # Counter mobility with control
                    if 'cancel' in effects_str:
                        score += 20
                    if spell.priority in ['1', '2']:  # Fast spells
                        score += 10
                        
            # Element-specific counters should use real data, not assumptions
                
        return score
    
    def choose_cards_to_keep(self, player, gs):
        """Strategically choose which cards to keep at end of round
        
        May choose to discard entire hand if:
        - Hand quality is poor
        - Elements don't match well against opponent
        - Better sets are likely available
        """
        # If hand is empty or very low health, use default logic
        if not player.hand or player.health <= 1:
            return super().choose_cards_to_keep(player, gs)
        
        # Evaluate current hand quality
        hand_score = self._evaluate_hand_quality(player, gs)
        
        # Get information about available sets
        available_sets_count = len(gs.main_deck) if hasattr(gs, 'main_deck') else 0
        
        # Decision factors for clearing hand
        should_clear_hand = False
        reasons = []
        
        # Factor 1: Poor hand quality
        if hand_score < -50:
            should_clear_hand = True
            reasons.append("poor hand quality")
        
        # Factor 2: Bad element matchup
        opponent_elements = self._get_opponent_elements(gs)
        if opponent_elements:
            bad_matchup_count = sum(1 for card in player.hand 
                                    if self._is_bad_element_matchup(card.element, opponent_elements))
            if bad_matchup_count >= len(player.hand) * 0.75:  # 75% or more bad matchups
                should_clear_hand = True
                reasons.append("bad element matchups")
        
        # Factor 3: All high priority (slow) spells
        avg_priority = sum(int(c.priority) if c.priority != 'A' else 99 
                          for c in player.hand) / len(player.hand)
        if avg_priority >= 4:
            should_clear_hand = True
            reasons.append("too many slow spells")
        
        # Factor 4: No damage spells when opponent is low health
        opponents = [p for p in gs.players if p != player]
        if opponents and min(p.health for p in opponents) <= 2:
            has_damage = any('attack' in card.types or 
                           any('damage' in str(effect) for effect in card.resolve_effects)
                           for card in player.hand)
            if not has_damage:
                should_clear_hand = True
                reasons.append("no damage spells vs low health opponent")
        
        # Factor 5: Health is good and sets are available
        if player.health >= player.max_health * 0.8 and available_sets_count >= 3:
            # More willing to take risks when healthy
            if hand_score < 0:
                should_clear_hand = True
                reasons.append("healthy and better sets available")
        
        # Log decision if in debug mode
        if should_clear_hand and self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\\033[90m[AI-HARD] {player.name} clearing entire hand: {', '.join(reasons)}\\033[0m"
            )
        
        # If clearing hand, return empty list
        if should_clear_hand:
            return []
        
        # Otherwise, selectively keep good cards
        cards_to_keep = []
        for card in player.hand:
            keep_score = self._evaluate_card(card, player, gs)
            
            # Always keep high-value cards
            if keep_score >= 100:
                cards_to_keep.append(card)
            # Keep remedy if hurt
            elif 'remedy' in card.types and player.health < player.max_health * 0.7:
                cards_to_keep.append(card)
            # Keep cards that match well against opponent
            elif opponent_elements and not self._is_bad_element_matchup(card.element, opponent_elements):
                if keep_score >= 0:  # At least neutral value
                    cards_to_keep.append(card)
            # Keep if score is positive and we don't have many cards yet
            elif keep_score > 20 and len(cards_to_keep) < 3:
                cards_to_keep.append(card)
        
        # If we're keeping very few cards, might as well clear for new set
        if len(cards_to_keep) <= 1 and available_sets_count >= 2:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[AI-HARD] {player.name} clearing hand - only {len(cards_to_keep)} cards worth keeping\\033[0m"
                )
            return []
        
        return cards_to_keep
    
    def _evaluate_hand_quality(self, player, gs):
        """Evaluate overall quality of current hand"""
        if not player.hand:
            return -1000
        
        total_score = 0
        
        # Score each card
        for card in player.hand:
            total_score += self._evaluate_card(card, player, gs)
        
        # Bonus for synergies
        total_score += self._evaluate_hand_synergies(None, player, gs) * 10
        
        # Penalty for too many similar types
        type_counts = {}
        for card in player.hand:
            for spell_type in card.types:
                type_counts[spell_type] = type_counts.get(spell_type, 0) + 1
        
        # Penalty for imbalance
        max_type_count = max(type_counts.values()) if type_counts else 0
        if max_type_count >= 3:
            total_score -= (max_type_count - 2) * 20
        
        return total_score
    
    def _get_opponent_elements(self, gs):
        """Get list of elements opponents have shown"""
        opponent_elements = set()
        
        for name, history in self.opponent_history.items():
            # Don't include our own history
            if any(p.name == name and p in gs.players for p in gs.players):
                player = next(p for p in gs.players if p.name == name)
                if player != gs.players[0]:  # Assuming AI is not player 0
                    for element, count in history['elements_used'].items():
                        if count > 0:
                            opponent_elements.add(element)
        
        return list(opponent_elements)
    
    def _is_bad_element_matchup(self, my_element, opponent_elements):
        """Check if my element is weak against opponent elements"""
        # TODO: Should use real win rate data instead of hardcoded relationships
        # For now, return False to avoid using incorrect assumptions
        return False