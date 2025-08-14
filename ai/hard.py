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
        
        # Choose the highest scoring option
        best_idx = max(option_scores.items(), key=lambda x: x[1])[0]
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
            if caster.health <= self_damage + 1:
                score -= 200  # Avoid potentially lethal self-damage
            elif caster.health <= 3:
                score -= 100  # Be very cautious at low health
            else:
                score -= self_damage * 10  # Minor penalty proportional to damage
        
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