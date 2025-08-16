#!/usr/bin/env python3
"""Damage potential calculator for accurate spell analysis"""

import json
from collections import defaultdict

class DamagePotentialCalculator:
    """Calculate damage potential for spells with proper conditional handling"""
    
    def __init__(self):
        with open('spells.json', 'r') as f:
            self.spells = json.load(f)
        
        with open('element_categories.json', 'r') as f:
            self.element_categories = json.load(f)
    
    def calculate_spell_damage(self, spell):
        """Calculate min/max/typical damage for a spell"""
        spell_name = spell['card_name']
        
        # Special case handling for known complex spells
        if spell_name == 'Turbulence':
            return {'min': 1, 'max': 2, 'typical': 1.5, 
                   'notes': '2 damage if active in 2+ other clashes, else 1'}
        
        elif spell_name == 'Impact':
            return {'min': 0, 'max': 9, 'typical': 2,
                   'notes': '1 damage per spell from other clashes (0-9)'}
        
        elif spell_name == 'Ignite':
            return {'min': 1, 'max': 4, 'typical': 2,
                   'notes': 'Can advance up to 3 times for 4 total damage'}
        
        elif spell_name == 'Prickle':
            return {'min': 1, 'max': 6, 'typical': 3,
                   'notes': 'Auto-optimal: 1 damage or 1 per active spell'}
        
        elif spell_name == 'Ritual':
            return {'min': 1, 'max': 6, 'typical': 3,
                   'notes': 'Choice: 1 damage or up to 6 (1 per attack spell)'}
        
        elif spell_name == 'Illuminate':
            return {'min': 1, 'max': 3, 'typical': 2,
                   'notes': 'Choice: 1 damage or 3 damage + 1 self-damage'}
        
        elif spell_name == 'Crepuscule':
            return {'min': 1, 'max': 2, 'typical': 2,
                   'notes': '1 damage + 1 heal, +1 damage if other remedy'}
        
        # Standard damage detection for simpler spells
        damage_found = False
        base_damage = 0
        
        # Check resolve effects
        for effect in spell.get('resolve_effects', []):
            damage = self._extract_damage_from_effect(effect)
            if damage > 0:
                damage_found = True
                base_damage = max(base_damage, damage)
        
        # Check advance effects
        advance_damage = 0
        for effect in spell.get('advance_effects', []):
            damage = self._extract_damage_from_effect(effect)
            if damage > 0:
                advance_damage = max(advance_damage, damage)
        
        if damage_found or advance_damage > 0:
            total = base_damage + advance_damage
            return {'min': total, 'max': total, 'typical': total,
                   'notes': 'Flat damage'}
        
        return {'min': 0, 'max': 0, 'typical': 0, 'notes': 'No damage'}
    
    def _extract_damage_from_effect(self, effect):
        """Extract damage value from a single effect"""
        action = effect.get('action', {})
        
        if isinstance(action, dict):
            if action.get('type') == 'damage' and action.get('target') != 'self':
                return action.get('parameters', {}).get('value', 0)
            elif action.get('type') == 'damage_multi_target':
                return action.get('parameters', {}).get('value', 0)
        
        return 0
    
    def analyze_all_spells(self):
        """Analyze damage potential for all spells"""
        element_damage = defaultdict(list)
        
        for spell in self.spells:
            damage_info = self.calculate_spell_damage(spell)
            
            if damage_info['max'] > 0:
                element_damage[spell['element']].append({
                    'name': spell['card_name'],
                    'min': damage_info['min'],
                    'max': damage_info['max'],
                    'typical': damage_info['typical'],
                    'notes': damage_info['notes']
                })
        
        return element_damage
    
    def generate_report(self):
        """Generate comprehensive damage report"""
        print("ELEMENTAL ELEPHANTS - DAMAGE POTENTIAL CALCULATOR")
        print("=" * 60)
        
        element_damage = self.analyze_all_spells()
        
        # Calculate averages and sort
        element_stats = []
        for element, spells in element_damage.items():
            if spells:
                avg_typical = sum(s['typical'] for s in spells) / len(spells)
                max_potential = max(s['max'] for s in spells)
                
                # Get category
                category = None
                for cat, data in self.element_categories['categories'].items():
                    if element in data['elements']:
                        category = cat
                        break
                
                element_stats.append({
                    'element': element,
                    'category': category,
                    'avg_typical': avg_typical,
                    'max_potential': max_potential,
                    'spell_count': len(spells),
                    'spells': spells
                })
        
        # Sort by average typical damage
        element_stats.sort(key=lambda x: x['avg_typical'], reverse=True)
        
        # Display summary
        print("\nDAMAGE SUMMARY BY ELEMENT")
        print("-" * 60)
        print(f"{'Element':<12} {'Category':<10} {'Avg Damage':<12} {'Max Potential':<15} {'# Spells'}")
        print("-" * 60)
        
        for stat in element_stats:
            print(f"{stat['element']:<12} {stat['category']:<10} {stat['avg_typical']:>10.1f} {stat['max_potential']:>13} {stat['spell_count']:>10}")
        
        # Show details for high-damage elements
        print("\n\nHIGH DAMAGE SPELLS (Max ≥ 4)")
        print("-" * 60)
        
        for stat in element_stats:
            high_damage_spells = [s for s in stat['spells'] if s['max'] >= 4]
            if high_damage_spells:
                print(f"\n{stat['element']} [{stat['category']}]:")
                for spell in high_damage_spells:
                    print(f"  {spell['name']}: {spell['min']}-{spell['max']} damage (typical: {spell['typical']})")
                    print(f"    → {spell['notes']}")
        
        # Show conditional damage spells
        print("\n\nCONDITIONAL DAMAGE SPELLS")
        print("-" * 60)
        
        for stat in element_stats:
            conditional_spells = [s for s in stat['spells'] if s['min'] != s['max']]
            if conditional_spells:
                print(f"\n{stat['element']} [{stat['category']}]:")
                for spell in conditional_spells:
                    print(f"  {spell['name']}: {spell['min']}-{spell['max']} damage (typical: {spell['typical']})")
                    print(f"    → {spell['notes']}")
        
        # Category analysis
        print("\n\nDAMAGE BY ELEMENT CATEGORY")
        print("-" * 60)
        
        category_stats = defaultdict(lambda: {'elements': [], 'total_spells': 0, 'total_typical': 0})
        
        for stat in element_stats:
            cat = stat['category']
            if cat:
                category_stats[cat]['elements'].append(stat['element'])
                category_stats[cat]['total_spells'] += stat['spell_count']
                category_stats[cat]['total_typical'] += sum(s['typical'] for s in stat['spells'])
        
        for category in ['offense', 'defense', 'mobility', 'balanced']:
            if category in category_stats:
                data = category_stats[category]
                avg_damage = data['total_typical'] / data['total_spells'] if data['total_spells'] > 0 else 0
                print(f"\n{category.upper()}:")
                print(f"  Elements: {', '.join(data['elements'])}")
                print(f"  Total damage spells: {data['total_spells']}")
                print(f"  Average damage per spell: {avg_damage:.2f}")


if __name__ == "__main__":
    calculator = DamagePotentialCalculator()
    calculator.generate_report()