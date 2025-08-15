#!/usr/bin/env python3
"""Analyze spell and element statistics from the game data"""

import json
import os
from collections import defaultdict
import statistics

class SpellAnalyzer:
    """Analyze spell balance and element statistics"""
    
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
    
    def analyze_all(self):
        """Run all analyses"""
        print("ELEMENTAL ELEPHANTS - SPELL & ELEMENT ANALYTICS")
        print("=" * 60)
        
        self.analyze_damage_by_element()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_healing_by_element()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_spell_types_by_element()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_priorities_by_element()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_special_effects_by_element()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_conjuries_by_element()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_element_categories()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_self_damage()
        print("\n" + "=" * 60 + "\n")
        
        self.analyze_card_advantage()
    
    def get_damage_value(self, action):
        """Extract damage value from an action"""
        if not isinstance(action, dict):
            return 0
        
        action_type = action.get('type', '')
        if action_type == 'damage':
            return action.get('parameters', {}).get('value', 0)
        elif action_type == 'damage_per_spell':
            # Estimate average case (2 spells)
            return action.get('parameters', {}).get('value', 0) * 2
        elif action_type == 'damage_multi_target':
            # Multi-target damage
            return action.get('parameters', {}).get('value', 0)
        return 0
    
    def get_healing_value(self, action):
        """Extract healing value from an action"""
        if not isinstance(action, dict):
            return 0
        
        if action.get('type') == 'heal':
            return action.get('parameters', {}).get('value', 0)
        return 0
    
    def analyze_damage_by_element(self):
        """Analyze average damage output by element"""
        print("DAMAGE OUTPUT BY ELEMENT")
        print("-" * 40)
        
        element_damage = defaultdict(list)
        
        for spell in self.spells:
            element = spell['element']
            total_damage = 0
            
            # Check resolve effects
            for effect in spell.get('resolve_effects', []):
                action = effect.get('action', {})
                total_damage += self.get_damage_value(action)
                
                # Check player choice options
                if isinstance(action, dict) and action.get('type') == 'player_choice':
                    for option in action.get('options', []):
                        if option.get('type') == 'damage':
                            total_damage += self.get_damage_value(option)
                        elif option.get('type') == 'sequence':
                            for seq_action in option.get('actions', []):
                                total_damage += self.get_damage_value(seq_action)
            
            # Check advance effects
            for effect in spell.get('advance_effects', []):
                action = effect.get('action', {})
                total_damage += self.get_damage_value(action)
            
            if total_damage > 0:
                element_damage[element].append(total_damage)
        
        # Calculate statistics
        results = []
        for element, damages in element_damage.items():
            if damages:
                avg_damage = statistics.mean(damages)
                max_damage = max(damages)
                spell_count = len(damages)
                results.append((element, avg_damage, max_damage, spell_count))
        
        # Sort by average damage
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        print(f"{'Element':<15} {'Avg Damage':<12} {'Max Damage':<12} {'# Spells':<10}")
        for element, avg_dmg, max_dmg, count in results:
            category = self.get_element_category(element)
            print(f"{element:<15} {avg_dmg:>10.1f} {max_dmg:>12} {count:>10} [{category}]")
    
    def analyze_healing_by_element(self):
        """Analyze average healing output by element"""
        print("HEALING OUTPUT BY ELEMENT")
        print("-" * 40)
        
        element_healing = defaultdict(list)
        
        for spell in self.spells:
            element = spell['element']
            total_healing = 0
            
            # Check resolve effects
            for effect in spell.get('resolve_effects', []):
                action = effect.get('action', {})
                total_healing += self.get_healing_value(action)
                
                # Check player choice options
                if isinstance(action, dict) and action.get('type') == 'player_choice':
                    for option in action.get('options', []):
                        if option.get('type') == 'heal':
                            total_healing += self.get_healing_value(option)
                        elif option.get('type') == 'sequence':
                            for seq_action in option.get('actions', []):
                                total_healing += self.get_healing_value(seq_action)
            
            # Check advance effects
            for effect in spell.get('advance_effects', []):
                action = effect.get('action', {})
                total_healing += self.get_healing_value(action)
            
            if total_healing > 0:
                element_healing[element].append(total_healing)
        
        # Calculate statistics
        results = []
        for element, healings in element_healing.items():
            if healings:
                avg_healing = statistics.mean(healings)
                max_healing = max(healings)
                spell_count = len(healings)
                results.append((element, avg_healing, max_healing, spell_count))
        
        # Sort by average healing
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        print(f"{'Element':<15} {'Avg Healing':<12} {'Max Healing':<12} {'# Spells':<10}")
        for element, avg_heal, max_heal, count in results:
            category = self.get_element_category(element)
            print(f"{element:<15} {avg_heal:>11.1f} {max_heal:>12} {count:>10} [{category}]")
    
    def analyze_spell_types_by_element(self):
        """Analyze spell type distribution by element"""
        print("SPELL TYPE DISTRIBUTION BY ELEMENT")
        print("-" * 40)
        
        element_types = defaultdict(lambda: defaultdict(int))
        element_totals = defaultdict(int)
        
        for spell in self.spells:
            element = spell['element']
            element_totals[element] += 1
            
            for spell_type in spell.get('spell_types', []):
                element_types[element][spell_type] += 1
        
        # Display results
        spell_types = ['attack', 'response', 'remedy', 'boost', 'conjury']
        
        print(f"{'Element':<15}", end='')
        for spell_type in spell_types:
            print(f"{spell_type:<10}", end='')
        print("Total")
        print("-" * 70)
        
        for element in sorted(element_totals.keys()):
            print(f"{element:<15}", end='')
            for spell_type in spell_types:
                count = element_types[element].get(spell_type, 0)
                percentage = (count / element_totals[element]) * 100 if element_totals[element] > 0 else 0
                print(f"{count:>2} ({percentage:>3.0f}%)", end='  ')
            print(f"{element_totals[element]:>5}")
    
    def analyze_priorities_by_element(self):
        """Analyze priority distribution by element"""
        print("PRIORITY DISTRIBUTION BY ELEMENT")
        print("-" * 40)
        
        element_priorities = defaultdict(lambda: defaultdict(int))
        
        for spell in self.spells:
            element = spell['element']
            priority = str(spell.get('priority', '?'))
            element_priorities[element][priority] += 1
        
        # Get all unique priorities
        all_priorities = set()
        for priorities in element_priorities.values():
            all_priorities.update(priorities.keys())
        all_priorities = sorted(all_priorities)
        
        # Display results
        print(f"{'Element':<15}", end='')
        for priority in all_priorities:
            print(f"P{priority:<4}", end='')
        print()
        print("-" * (15 + len(all_priorities) * 5))
        
        for element in sorted(element_priorities.keys()):
            print(f"{element:<15}", end='')
            for priority in all_priorities:
                count = element_priorities[element].get(priority, 0)
                print(f"{count:>5}", end='')
            print()
    
    def analyze_special_effects_by_element(self):
        """Analyze special effects distribution by element"""
        print("SPECIAL EFFECTS BY ELEMENT")
        print("-" * 40)
        
        element_effects = defaultdict(lambda: defaultdict(int))
        
        special_effects = [
            'cancel', 'discard', 'advance', 'recall', 'move_to_future_clash',
            'bolster', 'weaken', 'draw', 'cast_extra_spell'
        ]
        
        for spell in self.spells:
            element = spell['element']
            
            # Convert to string for searching
            all_effects = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
            
            for effect in special_effects:
                if effect in all_effects:
                    element_effects[element][effect] += 1
        
        # Display results
        print(f"{'Element':<15}", end='')
        for effect in special_effects[:5]:
            print(f"{effect[:6]:<7}", end='')
        print()
        
        for element in sorted(element_effects.keys()):
            category = self.get_element_category(element)
            print(f"{element:<15}", end='')
            for effect in special_effects[:5]:
                count = element_effects[element].get(effect, 0)
                print(f"{count:>7}", end='')
            print(f"  [{category}]")
        
        print("\nContinued...")
        print(f"{'Element':<15}", end='')
        for effect in special_effects[5:]:
            print(f"{effect[:6]:<7}", end='')
        print()
        
        for element in sorted(element_effects.keys()):
            print(f"{element:<15}", end='')
            for effect in special_effects[5:]:
                count = element_effects[element].get(effect, 0)
                print(f"{count:>7}", end='')
            print()
    
    def analyze_conjuries_by_element(self):
        """Analyze conjury distribution by element"""
        print("CONJURY SPELLS BY ELEMENT")
        print("-" * 40)
        
        element_conjuries = defaultdict(list)
        
        for spell in self.spells:
            if spell.get('is_conjury', False):
                element = spell['element']
                name = spell['card_name']
                element_conjuries[element].append(name)
        
        # Display results
        for element in sorted(element_conjuries.keys()):
            conjuries = element_conjuries[element]
            category = self.get_element_category(element)
            print(f"{element:<15} ({len(conjuries)} conjuries) [{category}]")
            for conjury in conjuries:
                print(f"  - {conjury}")
    
    def get_element_category(self, element):
        """Get category for an element"""
        if not self.element_categories:
            return "unknown"
        
        for category, data in self.element_categories.get('categories', {}).items():
            if element in data.get('elements', []):
                return category
        return "unknown"
    
    def analyze_element_categories(self):
        """Analyze spell distribution by element category"""
        if not self.element_categories:
            print("ELEMENT CATEGORIES (not configured)")
            return
        
        print("SPELL DISTRIBUTION BY ELEMENT CATEGORY")
        print("-" * 40)
        
        category_stats = defaultdict(lambda: {
            'elements': [],
            'spell_count': 0,
            'damage_spells': 0,
            'healing_spells': 0,
            'total_damage': 0,
            'total_healing': 0
        })
        
        for spell in self.spells:
            element = spell['element']
            category = self.get_element_category(element)
            
            if category != "unknown":
                stats = category_stats[category]
                if element not in stats['elements']:
                    stats['elements'].append(element)
                
                stats['spell_count'] += 1
                
                # Check for damage/healing
                all_effects = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
                
                if 'damage' in all_effects:
                    stats['damage_spells'] += 1
                if 'heal' in all_effects:
                    stats['healing_spells'] += 1
        
        # Display results
        for category in ['offense', 'defense', 'mobility', 'balanced']:
            if category in category_stats:
                stats = category_stats[category]
                print(f"\n{category.upper()}")
                print(f"Elements: {', '.join(sorted(stats['elements']))}")
                print(f"Total Spells: {stats['spell_count']}")
                print(f"Damage Spells: {stats['damage_spells']} ({stats['damage_spells']/stats['spell_count']*100:.1f}%)")
                print(f"Healing Spells: {stats['healing_spells']} ({stats['healing_spells']/stats['spell_count']*100:.1f}%)")
    
    def analyze_self_damage(self):
        """Analyze self-damage spells by element"""
        print("SELF-DAMAGE SPELLS BY ELEMENT")
        print("-" * 40)
        
        element_self_damage = defaultdict(list)
        
        for spell in self.spells:
            element = spell['element']
            spell_name = spell['card_name']
            
            # Check all effects for self-damage
            all_effects = spell.get('resolve_effects', []) + spell.get('advance_effects', [])
            
            for effect in all_effects:
                action = effect.get('action', {})
                
                # Direct self-damage
                if isinstance(action, dict) and action.get('type') == 'damage' and action.get('target') == 'self':
                    damage = action.get('parameters', {}).get('value', 0)
                    element_self_damage[element].append((spell_name, damage))
                
                # Player choice with self-damage option
                if isinstance(action, dict) and action.get('type') == 'player_choice':
                    for option in action.get('options', []):
                        if option.get('type') == 'damage' and option.get('target') == 'self':
                            damage = option.get('parameters', {}).get('value', 0)
                            element_self_damage[element].append((spell_name, damage))
                        elif option.get('type') == 'sequence':
                            for seq_action in option.get('actions', []):
                                if seq_action.get('type') == 'damage' and seq_action.get('target') == 'self':
                                    damage = seq_action.get('parameters', {}).get('value', 0)
                                    element_self_damage[element].append((spell_name, damage))
        
        # Display results
        for element in sorted(element_self_damage.keys()):
            spells = element_self_damage[element]
            category = self.get_element_category(element)
            print(f"\n{element} [{category}]:")
            for spell_name, damage in spells:
                print(f"  - {spell_name}: {damage} self-damage")
    
    def analyze_card_advantage(self):
        """Analyze card advantage mechanics by element"""
        print("CARD ADVANTAGE MECHANICS BY ELEMENT")
        print("-" * 40)
        
        element_card_advantage = defaultdict(list)
        
        for spell in self.spells:
            element = spell['element']
            spell_name = spell['card_name']
            
            all_effects = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
            
            advantages = []
            
            if 'draw' in all_effects:
                advantages.append("draw")
            if 'discard' in all_effects and 'enemy' in all_effects:
                advantages.append("enemy discard")
            if 'recall' in all_effects:
                advantages.append("recall")
            if 'cast_extra_spell' in all_effects:
                advantages.append("extra cast")
            if 'advance' in all_effects and 'this_spell' in all_effects:
                advantages.append("self-advance")
            
            if advantages:
                element_card_advantage[element].append((spell_name, advantages))
        
        # Display results
        for element in sorted(element_card_advantage.keys()):
            spells = element_card_advantage[element]
            category = self.get_element_category(element)
            print(f"\n{element} [{category}] ({len(spells)} spells):")
            for spell_name, advantages in spells:
                print(f"  - {spell_name}: {', '.join(advantages)}")


def main():
    analyzer = SpellAnalyzer()
    analyzer.analyze_all()


if __name__ == "__main__":
    main()