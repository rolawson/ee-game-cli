#!/usr/bin/env python3
"""Enhanced spell analytics with damage potential calculator and real-world results"""

import json
import os
from collections import defaultdict
import statistics
import glob

class EnhancedSpellAnalyzer:
    """Analyze spell balance with both theoretical potential and real-world data"""
    
    def __init__(self):
        # Load spell data
        with open('spells.json', 'r') as f:
            self.spells = json.load(f)
        
        # Load element categories
        if os.path.exists('element_categories.json'):
            with open('element_categories.json', 'r') as f:
                self.element_categories = json.load(f)
        else:
            self.element_categories = None
            
        # Load test results for real-world data
        self.test_results = []
        for filename in glob.glob('test_results/*.json'):
            try:
                with open(filename, 'r') as f:
                    self.test_results.append(json.load(f))
            except:
                pass
    
    def analyze_all(self):
        """Run all analyses"""
        print("ELEMENTAL ELEPHANTS - ENHANCED SPELL ANALYTICS V2")
        print("=" * 60)
        
        # Theoretical analysis
        print("\n=== THEORETICAL DAMAGE POTENTIAL ===")
        self.analyze_damage_potential()
        
        print("\n=== THEORETICAL HEALING POTENTIAL ===")
        self.analyze_healing_potential()
        
        # Real-world analysis
        if self.test_results:
            print("\n=== REAL-WORLD SPELL PERFORMANCE ===")
            self.analyze_real_world_performance()
        else:
            print("\n=== REAL-WORLD SPELL PERFORMANCE ===")
            print("No test results found in test_results/ directory")
        
        print("\n=== SPELL TYPE DISTRIBUTION ===")
        self.analyze_spell_types_by_element()
        
        print("\n=== SPECIAL EFFECTS BY ELEMENT ===")
        self.analyze_special_effects()
    
    def calculate_damage_potential(self, spell):
        """Calculate theoretical damage potential for a spell"""
        potentials = {
            'min': 0,
            'max': 0,
            'typical': 0,  # Realistic expectation
            'conditions': []
        }
        
        # Analyze resolve effects
        for effect in spell.get('resolve_effects', []):
            damage_info = self._analyze_effect_damage(effect, spell)
            if damage_info:
                potentials['conditions'].append(damage_info)
        
        # Analyze advance effects
        for effect in spell.get('advance_effects', []):
            damage_info = self._analyze_effect_damage(effect, spell)
            if damage_info:
                damage_info['source'] = 'advance'
                potentials['conditions'].append(damage_info)
        
        # Calculate totals
        if potentials['conditions']:
            # For conditional effects, determine min/max/typical
            self._calculate_conditional_totals(potentials, spell)
        else:
            # No conditions found, set all to 0
            potentials['min'] = 0
            potentials['max'] = 0
            potentials['typical'] = 0
        
        return potentials
    
    def _analyze_effect_damage(self, effect, spell):
        """Analyze damage from a single effect"""
        condition = effect.get('condition', {})
        action = effect.get('action', {})
        
        damage_info = {
            'condition_type': condition.get('type', 'always'),
            'damage': 0,
            'scaling': False,
            'notes': []
        }
        
        # Handle different action types
        if isinstance(action, dict):
            action_type = action.get('type', '')
            
            if action_type == 'damage':
                damage_info['damage'] = action.get('parameters', {}).get('value', 0)
                
            elif action_type == 'damage_per_spell':
                damage_info['damage'] = 1  # Base multiplier
                damage_info['scaling'] = True
                damage_info['scaling_type'] = 'per_spell'
                spell_type = action.get('parameters', {}).get('spell_type', 'any')
                damage_info['notes'].append(f"Scales with {spell_type} spells")
                
            elif action_type == 'damage_per_spell_from_other_clashes':
                damage_info['damage'] = 1
                damage_info['scaling'] = True
                damage_info['scaling_type'] = 'per_spell_other_clashes'
                damage_info['notes'].append("Scales with spells from other clashes")
                
            elif action_type == 'damage_multi_target':
                damage_info['damage'] = action.get('parameters', {}).get('value', 0)
                damage_info['notes'].append("Hits all enemies")
                
            elif action_type == 'player_choice':
                # Analyze all options
                options_damage = []
                for option in action.get('options', []):
                    opt_damage = self._analyze_option_damage(option)
                    if opt_damage > 0:
                        options_damage.append(opt_damage)
                if options_damage:
                    damage_info['damage'] = max(options_damage)  # Best case
                    damage_info['notes'].append(f"Choice between {len(action.get('options', []))} options")
                    
            elif action_type == 'auto_optimal_choice':
                # Similar to player_choice but automatic
                options_damage = []
                for option in action.get('options', []):
                    opt_damage = self._analyze_option_damage(option)
                    if opt_damage > 0:
                        options_damage.append(opt_damage)
                if options_damage:
                    damage_info['damage'] = max(options_damage)
                    damage_info['notes'].append("Auto-selects optimal choice")
                    
            elif action_type == 'sequence':
                # Sum all damage in sequence
                total_damage = 0
                for seq_action in action.get('actions', []):
                    if seq_action.get('type') == 'damage':
                        total_damage += seq_action.get('parameters', {}).get('value', 0)
                damage_info['damage'] = total_damage
                
        elif isinstance(action, list):
            # Multiple actions
            total_damage = 0
            for act in action:
                if act.get('type') == 'damage':
                    total_damage += act.get('parameters', {}).get('value', 0)
            damage_info['damage'] = total_damage
        
        # Only return if there's damage
        if damage_info['damage'] > 0 or damage_info['scaling']:
            return damage_info
        return None
    
    def _analyze_option_damage(self, option):
        """Get damage from a choice option"""
        if option.get('type') == 'damage':
            return option.get('parameters', {}).get('value', 0)
        elif option.get('type') == 'damage_per_spell':
            return 3  # Assume 3 spells typical
        elif option.get('type') == 'sequence':
            total = 0
            for act in option.get('actions', []):
                if act.get('type') == 'damage':
                    total += act.get('parameters', {}).get('value', 0)
            return total
        return 0
    
    def _calculate_conditional_totals(self, potentials, spell):
        """Calculate min/max/typical damage considering conditions"""
        # Group by condition type
        always_damage = 0
        conditional_damages = []
        advance_damages = []
        
        # Special handling for spells with explicit conditions
        spell_name = spell.get('card_name', '')
        
        for cond in potentials['conditions']:
            if cond['condition_type'] == 'always':
                if cond.get('source') == 'advance':
                    advance_damages.append(cond['damage'])
                else:
                    always_damage += cond['damage']
            elif cond['condition_type'] == 'if_not':
                # This is an "otherwise" condition - mutually exclusive with others
                conditional_damages.append(('otherwise', cond['damage']))
            else:
                conditional_damages.append(('conditional', cond['damage']))
        
        # Calculate minimum (worst case)
        potentials['min'] = always_damage
        
        # Calculate maximum (best case)
        max_damage = always_damage
        
        # Handle conditional damages
        if conditional_damages:
            # If there's an "otherwise", it's either/or
            otherwise_damages = [d for t, d in conditional_damages if t == 'otherwise']
            regular_conditionals = [d for t, d in conditional_damages if t == 'conditional']
            
            if otherwise_damages and regular_conditionals:
                # Either the conditional OR the otherwise
                max_damage += max(max(regular_conditionals), max(otherwise_damages))
                potentials['typical'] = always_damage + min(max(regular_conditionals), max(otherwise_damages))
            elif regular_conditionals:
                max_damage += sum(regular_conditionals)
                potentials['typical'] = always_damage + (sum(regular_conditionals) // 2)  # Assume half trigger
            else:
                max_damage += sum(otherwise_damages)
                potentials['typical'] = always_damage + sum(otherwise_damages)
        else:
            potentials['typical'] = always_damage
        
        # Add advance damage potential
        if advance_damages:
            # Can potentially trigger multiple times
            advance_total = sum(advance_damages)
            if spell.get('card_name') in ['Ignite', 'Flow', 'Gust']:  # Self-advancing spells
                max_damage += advance_total * 3  # Could advance 3 times
                potentials['typical'] += advance_total  # Typically once
            else:
                max_damage += advance_total
        
        potentials['max'] = max_damage
        
        # Handle scaling damage
        for cond in potentials['conditions']:
            if cond.get('scaling'):
                if cond['scaling_type'] == 'per_spell':
                    potentials['max'] *= 6  # Could have 6 spells
                    potentials['typical'] *= 3  # Typically 3 spells
                elif cond['scaling_type'] == 'per_spell_other_clashes':
                    potentials['max'] *= 9  # 3 other clashes * 3 spells each
                    potentials['typical'] *= 3  # Typically 3-4 spells
    
    def analyze_damage_potential(self):
        """Analyze theoretical damage potential by element"""
        print("\nDAMAGE POTENTIAL BY ELEMENT")
        print("-" * 60)
        
        element_potentials = defaultdict(list)
        
        for spell in self.spells:
            element = spell['element']
            potential = self.calculate_damage_potential(spell)
            
            if potential['max'] > 0:
                element_potentials[element].append({
                    'name': spell['card_name'],
                    'min': potential['min'],
                    'max': potential['max'],
                    'typical': potential['typical'],
                    'notes': potential.get('conditions', [])
                })
        
        # Calculate and display statistics
        results = []
        for element, spells in element_potentials.items():
            if spells:
                avg_typical = statistics.mean(s['typical'] for s in spells)
                max_potential = max(s['max'] for s in spells)
                spell_count = len(spells)
                
                results.append({
                    'element': element,
                    'avg_typical': avg_typical,
                    'max_potential': max_potential,
                    'spell_count': spell_count,
                    'spells': spells
                })
        
        # Sort by average typical damage
        results.sort(key=lambda x: x['avg_typical'], reverse=True)
        
        # Display summary
        print(f"{'Element':<15} {'Avg Typical':<12} {'Max Potential':<15} {'# Damage Spells':<15}")
        print("-" * 60)
        for result in results:
            category = self.get_element_category(result['element'])
            print(f"{result['element']:<15} {result['avg_typical']:>10.1f} {result['max_potential']:>13} {result['spell_count']:>15} [{category}]")
        
        # Show details for high-damage elements
        print("\nHIGH DAMAGE POTENTIAL SPELLS:")
        for result in results:
            for spell in result['spells']:
                if spell['max'] >= 5:
                    print(f"\n{result['element']} - {spell['name']}:")
                    print(f"  Damage Range: {spell['min']}-{spell['max']} (typical: {spell['typical']})")
                    for note in spell['notes']:
                        if note.get('notes'):
                            print(f"  Notes: {', '.join(note['notes'])}")
    
    def analyze_healing_potential(self):
        """Analyze theoretical healing potential"""
        print("\nHEALING POTENTIAL BY ELEMENT")
        print("-" * 40)
        
        # Similar structure to damage analysis but for healing
        element_healing = defaultdict(list)
        
        for spell in self.spells:
            element = spell['element']
            healing_found = False
            
            # Check all effects for healing
            all_effects_str = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
            
            if 'heal' in all_effects_str:
                # Simple detection for now
                if 'heal_per_spell' in all_effects_str:
                    element_healing[element].append({
                        'name': spell['card_name'],
                        'potential': 'Scales with spells'
                    })
                else:
                    element_healing[element].append({
                        'name': spell['card_name'],
                        'potential': 'Fixed healing'
                    })
        
        # Display results
        for element in sorted(element_healing.keys()):
            spells = element_healing[element]
            category = self.get_element_category(element)
            print(f"\n{element} [{category}] ({len(spells)} healing spells):")
            for spell in spells:
                print(f"  - {spell['name']}: {spell['potential']}")
    
    def analyze_real_world_performance(self):
        """Analyze actual spell usage and damage from test results"""
        print("\nREAL-WORLD PERFORMANCE DATA")
        print("-" * 40)
        
        # Aggregate spell usage data
        spell_usage = defaultdict(lambda: {
            'times_played': 0,
            'total_damage': 0,
            'total_healing': 0,
            'times_advanced': 0,
            'times_cancelled': 0
        })
        
        element_performance = defaultdict(lambda: {
            'games_drafted': 0,
            'games_won': 0,
            'total_damage': 0,
            'total_healing': 0
        })
        
        # Process test results
        for test in self.test_results:
            for game in test.get('games', []):
                # Track element drafting and wins
                for player in ['player1', 'player2']:
                    player_data = game.get(player, {})
                    for element in player_data.get('elements_drafted', []):
                        element_performance[element]['games_drafted'] += 1
                        if player_data.get('won', False):
                            element_performance[element]['games_won'] += 1
                
                # Track spell events
                for event in game.get('events', []):
                    if event['type'] == 'spell_resolved':
                        spell_name = event.get('spell_name', '')
                        spell_usage[spell_name]['times_played'] += 1
                    
                    elif event['type'] == 'damage_dealt':
                        spell_name = event.get('source_spell', '')
                        damage = event.get('amount', 0)
                        spell_usage[spell_name]['total_damage'] += damage
                        
                        # Track by element
                        element = event.get('element', '')
                        if element:
                            element_performance[element]['total_damage'] += damage
                    
                    elif event['type'] == 'healing_done':
                        spell_name = event.get('source_spell', '')
                        healing = event.get('amount', 0)
                        spell_usage[spell_name]['total_healing'] += healing
                        
                        # Track by element
                        element = event.get('element', '')
                        if element:
                            element_performance[element]['total_healing'] += healing
                    
                    elif event['type'] == 'spell_advanced':
                        spell_name = event.get('spell_name', '')
                        spell_usage[spell_name]['times_advanced'] += 1
                    
                    elif event['type'] == 'spell_cancelled':
                        spell_name = event.get('spell_name', '')
                        spell_usage[spell_name]['times_cancelled'] += 1
        
        # Display element performance
        print("\nELEMENT WIN RATES AND DAMAGE OUTPUT:")
        print(f"{'Element':<15} {'Games':<8} {'Win %':<8} {'Avg Damage/Game':<18} {'Category'}")
        print("-" * 70)
        
        for element in sorted(element_performance.keys()):
            data = element_performance[element]
            if data['games_drafted'] > 0:
                win_rate = (data['games_won'] / data['games_drafted']) * 100
                avg_damage = data['total_damage'] / data['games_drafted']
                category = self.get_element_category(element)
                print(f"{element:<15} {data['games_drafted']:<8} {win_rate:<7.1f}% {avg_damage:<17.1f} [{category}]")
        
        # Display top damage dealing spells
        print("\nTOP DAMAGE DEALING SPELLS (ACTUAL):")
        damage_spells = [(name, data) for name, data in spell_usage.items() if data['total_damage'] > 0]
        damage_spells.sort(key=lambda x: x[1]['total_damage'], reverse=True)
        
        for i, (spell_name, data) in enumerate(damage_spells[:10]):
            if data['times_played'] > 0:
                avg_damage = data['total_damage'] / data['times_played']
                print(f"{i+1}. {spell_name}: {data['total_damage']} total damage ({avg_damage:.1f} avg per play)")
    
    def analyze_spell_types_by_element(self):
        """Analyze spell type distribution"""
        print("\nSPELL TYPE DISTRIBUTION BY ELEMENT")
        print("-" * 60)
        
        element_types = defaultdict(lambda: defaultdict(int))
        element_totals = defaultdict(int)
        
        for spell in self.spells:
            element = spell['element']
            element_totals[element] += 1
            
            for spell_type in spell.get('spell_types', []):
                element_types[element][spell_type] += 1
        
        # Display compact results
        spell_types = ['attack', 'response', 'remedy', 'boost', 'conjury']
        
        for element in sorted(element_totals.keys()):
            category = self.get_element_category(element)
            type_summary = []
            for spell_type in spell_types:
                count = element_types[element].get(spell_type, 0)
                if count > 0:
                    type_summary.append(f"{spell_type[0].upper()}{count}")
            
            print(f"{element:<12} [{category:<8}]: {' '.join(type_summary):<20} (Total: {element_totals[element]})")
    
    def analyze_special_effects(self):
        """Analyze special effects distribution"""
        print("\nKEY MECHANICS BY ELEMENT")
        print("-" * 40)
        
        element_effects = defaultdict(set)
        
        key_effects = ['advance', 'recall', 'cancel', 'discard', 'weaken', 'bolster', 
                      'move_to_future_clash', 'cast_extra_spell']
        
        for spell in self.spells:
            element = spell['element']
            effects_str = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
            
            for effect in key_effects:
                if effect in effects_str:
                    element_effects[element].add(effect)
        
        # Group by category
        categories = ['offense', 'defense', 'mobility', 'balanced']
        for category in categories:
            print(f"\n{category.upper()}:")
            for element in sorted(element_effects.keys()):
                if self.get_element_category(element) == category:
                    effects = sorted(element_effects[element])
                    if effects:
                        print(f"  {element}: {', '.join(effects)}")
    
    def get_element_category(self, element):
        """Get category for an element"""
        if not self.element_categories:
            return "unknown"
        
        for category, data in self.element_categories.get('categories', {}).items():
            if element in data.get('elements', []):
                return category
        return "unknown"


def main():
    analyzer = EnhancedSpellAnalyzer()
    analyzer.analyze_all()


if __name__ == "__main__":
    main()