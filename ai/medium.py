"""Medium AI - Basic strategic decision making"""

import random
from .base import BaseAI


class MediumAI(BaseAI):
    """Current AI logic - medium difficulty"""
    
    def _select_card(self, player, gs, valid_indices):
        """Select card based on basic heuristics"""
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-MEDIUM] {player.name} analyzed options\033[0m"
            )
        
        # Categorize cards by preference based on clash timing
        preferred_indices = []
        acceptable_indices = []
        
        for i in valid_indices:
            card = player.hand[i]
            # Cards with notfirst/notlast = 1 are less preferred in those clashes
            if gs.clash_num == 1 and card.notfirst == 1:
                acceptable_indices.append(i)
            elif gs.clash_num == 4 and card.notlast == 1:
                acceptable_indices.append(i)
            else:
                preferred_indices.append(i)
        
        # Use preferred cards if available, otherwise use acceptable ones
        candidate_indices = preferred_indices if preferred_indices else acceptable_indices

        # High-level situational logic
        low_health_enemies = [p for p in gs.players if p != player and p.health <= 2]
        empty_hand_enemies = [p for p in gs.players if p != player and len(p.hand) == 0]
        
        # Survival: Find the best heal card among candidates
        if player.health <= 2:
            heal_options = [(i, player.hand[i]) for i in candidate_indices 
                          if 'remedy' in player.hand[i].types]
            if heal_options:
                # Sort by priority (lower is better)
                heal_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                chosen = heal_options[0]
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MEDIUM] {player.name} chose healing due to low health ({player.health}): {chosen[1].name}\033[0m"
                    )
                return chosen[0]

        # Finisher: Find the best damage card among candidates
        if low_health_enemies:
            damage_options = [(i, player.hand[i]) for i in candidate_indices 
                            if 'attack' in player.hand[i].types]
            if damage_options:
                # Sort by priority (lower is better for faster resolution)
                damage_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                chosen = damage_options[0]
                enemy_names = ", ".join([e.name for e in low_health_enemies])
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MEDIUM] {player.name} chose attack (enemy low health): {chosen[1].name}\033[0m"
                    )
                return chosen[0]
        
        # Aggression: Be aggressive when enemy has empty hand
        if empty_hand_enemies:
            # Prefer attack or control spells when enemy can't respond
            aggressive_options = [(i, player.hand[i]) for i in candidate_indices 
                                if 'attack' in player.hand[i].types or 
                                   'discard' in str(player.hand[i].resolve_effects) or
                                   'cancel' in str(player.hand[i].resolve_effects)]
            if aggressive_options:
                aggressive_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                chosen = aggressive_options[0]
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\033[90m[AI-MEDIUM] {player.name} chose aggressive play (enemy hand empty): {chosen[1].name}\033[0m"
                    )
                return chosen[0]
        
        # Default to a random candidate card
        choice = random.choice(candidate_indices)
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-MEDIUM] {player.name} chose: {player.hand[choice].name}\033[0m"
            )
        return choice
    
    def make_choice(self, valid_options, caster, gs, current_card):
        """Make choices based on basic game state heuristics"""
        if not valid_options:
            return None
            
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-MEDIUM] {caster.name} evaluating {len(valid_options)} options\033[0m"
            )
        
        # Categorize options
        attack_options = []
        remedy_options = []
        safe_options = []
        risky_options = []
        advance_options = []
        
        for option in valid_options:
            # Check if option involves self-damage
            has_self_damage = self._has_self_damage(option)
            
            if has_self_damage:
                risky_options.append(option)
            elif self._is_attack_option(option):
                attack_options.append(option)
            elif self._is_remedy_option(option):
                remedy_options.append(option)
            elif self._is_advance_option(option):
                advance_options.append(option)
            else:
                safe_options.append(option)
        
        # Decision logic based on game state
        
        # Critical health - prioritize healing
        if caster.health <= 2 and remedy_options:
            choice = remedy_options[0]
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-MEDIUM] {caster.name} chose healing (low health)\033[0m"
                )
            return choice
        
        # Avoid risky options at low health
        if caster.health <= 3 and risky_options and len(valid_options) > len(risky_options):
            # Remove risky options if we have other choices
            valid_options = [opt for opt in valid_options if opt not in risky_options]
        
        # Enemy at low health - prioritize damage
        low_health_enemies = [p for p in gs.players if p != caster and p.health <= 2]
        if low_health_enemies and attack_options:
            # Pick the highest damage attack option
            best_attack = self._get_best_attack_option(attack_options)
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-MEDIUM] {caster.name} chose attack (enemy low health)\033[0m"
                )
            return best_attack
        
        # High health - prefer attacks over healing
        if caster.health >= 4 and attack_options:
            choice = self._get_best_attack_option(attack_options)
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-MEDIUM] {caster.name} chose attack (high health)\033[0m"
                )
            return choice
        
        # Advance options are generally good in mid-game
        if gs.round_num >= 2 and advance_options:
            choice = advance_options[0]
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\033[90m[AI-MEDIUM] {caster.name} chose advance option\033[0m"
                )
            return choice
        
        # Default to first valid option that's not risky
        non_risky = [opt for opt in valid_options if opt not in risky_options]
        if non_risky:
            choice = non_risky[0]
        else:
            choice = valid_options[0]
            
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            option_desc = self._describe_option(choice)
            self.engine.ai_decision_logs.append(
                f"\033[90m[AI-MEDIUM] {caster.name} chose: {option_desc}\033[0m"
            )
        
        return choice
    
    def _has_self_damage(self, option):
        """Check if an option involves self-damage"""
        if option.get('type') == 'sequence':
            # Check sequence for self-damage
            for act in option.get('actions', []):
                if act.get('type') == 'damage' and act.get('target') == 'self':
                    return True
        elif option.get('type') == 'damage' and option.get('target') == 'self':
            return True
        return False
    
    def _is_attack_option(self, option):
        """Check if an option is primarily offensive"""
        attack_types = ['damage', 'weaken', 'damage_per_spell']
        if option.get('type') in attack_types:
            return True
        if option.get('type') == 'sequence':
            # Check if sequence contains attacks
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
            # Check if sequence contains healing
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
    
    def _get_best_attack_option(self, attack_options):
        """Select the best attack option based on damage value"""
        if not attack_options:
            return None
            
        # Try to find the highest damage option
        best_option = attack_options[0]
        best_damage = 0
        
        for option in attack_options:
            damage = self._get_option_damage(option)
            if damage > best_damage:
                best_damage = damage
                best_option = option
        
        return best_option
    
    def _get_option_damage(self, option):
        """Extract damage value from an option"""
        if option.get('type') == 'damage':
            return option.get('parameters', {}).get('value', 0)
        elif option.get('type') == 'damage_per_spell':
            # Estimate 2 spells on average
            return option.get('parameters', {}).get('value', 0) * 2
        elif option.get('type') == 'sequence':
            total_damage = 0
            for act in option.get('actions', []):
                if act.get('type') == 'damage':
                    total_damage += act.get('parameters', {}).get('value', 0)
            return total_damage
        return 0
    
    def _describe_option(self, option):
        """Generate a description of the option for logging"""
        if option.get('type') == 'sequence':
            actions = []
            for act in option.get('actions', []):
                actions.append(act.get('type', 'unknown'))
            return f"sequence: {' then '.join(actions)}"
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
        """Medium AI drafting - balanced approach with some strategy"""
        if not available_sets:
            return None
        
        # Analyze what we already have (if this is second draft)
        current_cards = player.discard_pile
        
        set_scores = {}
        
        for idx, spell_set in enumerate(available_sets):
            score = random.randint(0, 20)  # Some randomness
            
            # Count spell types in this set
            type_counts = {}
            has_conjury = False
            priority_variety = set()
            
            for spell in spell_set:
                # Count types
                for spell_type in spell.types:
                    type_counts[spell_type] = type_counts.get(spell_type, 0) + 1
                
                # Track priorities
                priority_variety.add(spell.priority)
                
                # Check for conjury
                if spell.is_conjury:
                    has_conjury = True
            
            # Medium AI likes balanced sets
            if 'attack' in type_counts:
                score += 40  # Need damage
            if 'remedy' in type_counts:
                score += 35  # Need healing
            if 'response' in type_counts:
                score += 25  # Responses are good
            if has_conjury:
                score += 20  # Conjuries are powerful
            
            # Variety is good
            score += len(type_counts) * 15
            score += len(priority_variety) * 10
            
            # Element category bonus
            element = spell_set[0].element
            category = self.get_element_category(element)
            
            # Simple category preferences
            if category == 'offense':
                score += 25  # Good for damage
            elif category == 'defense':
                score += 30  # Always useful
            elif category == 'mobility':
                score += 35  # Flexibility is great
            elif category == 'balanced':
                score += 20  # Solid choice
            
            # If second draft, consider what we have
            if current_cards:
                # Check if this fills gaps
                current_has_attack = any('attack' in c.types for c in current_cards)
                current_has_remedy = any('remedy' in c.types for c in current_cards)
                
                if not current_has_attack and 'attack' in type_counts:
                    score += 50  # Really need damage
                if not current_has_remedy and 'remedy' in type_counts:
                    score += 40  # Really need healing
            
            set_scores[idx] = score
        
        # Pick highest scoring set
        best_idx = max(set_scores.items(), key=lambda x: x[1])[0]
        chosen_set = available_sets[best_idx]
        
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            self.engine.ai_decision_logs.append(
                f"\\033[90m[AI-MEDIUM] Drafted {chosen_set[0].elephant} ({chosen_set[0].element})\\033[0m"
            )
        
        return chosen_set