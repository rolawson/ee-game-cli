#!/usr/bin/env python3
"""Comprehensive spell analyzer that properly counts all damage spells"""

import json
from collections import defaultdict

def analyze_all_damage_spells():
    """Analyze all spells and identify damage dealers"""
    
    with open('spells.json', 'r') as f:
        spells = json.load(f)
    
    with open('element_categories.json', 'r') as f:
        element_categories = json.load(f)
    
    # Manual damage data for complex spells
    known_damage_spells = {
        # Fire
        'Combust': {'element': 'Fire', 'min': 1, 'max': 1, 'typical': 1},
        'Blaze': {'element': 'Fire', 'min': 2, 'max': 2, 'typical': 2},
        'Ignite': {'element': 'Fire', 'min': 1, 'max': 4, 'typical': 2},
        
        # Water
        'Flow': {'element': 'Water', 'min': 1, 'max': 1, 'typical': 1},
        
        # Wind
        'Turbulence': {'element': 'Wind', 'min': 1, 'max': 2, 'typical': 1.5},
        
        # Earth
        'Rumble': {'element': 'Earth', 'min': 1, 'max': 1, 'typical': 1},
        'Aftershocks': {'element': 'Earth', 'min': 2, 'max': 2, 'typical': 2},
        
        # Wood
        'Seed': {'element': 'Wood', 'min': 1, 'max': 1, 'typical': 1},
        'Prickle': {'element': 'Wood', 'min': 1, 'max': 6, 'typical': 3},
        
        # Metal
        'Defend': {'element': 'Metal', 'min': 1, 'max': 1, 'typical': 1},
        
        # Time
        'Quickshot': {'element': 'Time', 'min': 1, 'max': 1, 'typical': 1},
        'Impact': {'element': 'Time', 'min': 0, 'max': 9, 'typical': 2},
        
        # Space
        'Void': {'element': 'Space', 'min': 1, 'max': 1, 'typical': 1},
        
        # Sunbeam
        'Shine': {'element': 'Sunbeam', 'min': 1, 'max': 1, 'typical': 1},
        'Illuminate': {'element': 'Sunbeam', 'min': 1, 'max': 3, 'typical': 2},
        'Glare': {'element': 'Sunbeam', 'min': 1, 'max': 1, 'typical': 1},
        
        # Moonshine
        'Slumber': {'element': 'Moonshine', 'min': 1, 'max': 1, 'typical': 1},
        
        # Shadow
        'Obscure': {'element': 'Shadow', 'min': 1, 'max': 1, 'typical': 1},
        
        # Aster
        'Meteorite': {'element': 'Aster', 'min': 1, 'max': 1, 'typical': 1},
        
        # Blood
        'Offering': {'element': 'Blood', 'min': 2, 'max': 2, 'typical': 2},
        'Ritual': {'element': 'Blood', 'min': 1, 'max': 6, 'typical': 3},
        'Overexert': {'element': 'Blood', 'min': 4, 'max': 4, 'typical': 4},
        
        # Ichor
        # No damage spells
        
        # Venom
        'Sting': {'element': 'Venom', 'min': 1, 'max': 1, 'typical': 1},
        'Poison': {'element': 'Venom', 'min': 1, 'max': 1, 'typical': 1},
        
        # Nectar
        'Absorb': {'element': 'Nectar', 'min': 1, 'max': 1, 'typical': 1},
        
        # Lightning
        'Bolt': {'element': 'Lightning', 'min': 1, 'max': 1, 'typical': 1},
        
        # Thunder
        'Stun': {'element': 'Thunder', 'min': 1, 'max': 1, 'typical': 1},
        
        # Twilight
        'Dusk': {'element': 'Twilight', 'min': 2, 'max': 2, 'typical': 2},
        'Crepuscule': {'element': 'Twilight', 'min': 1, 'max': 2, 'typical': 1.5},
    }
    
    # Check all spells to ensure we have complete data
    element_damage = defaultdict(list)
    
    for spell in spells:
        spell_name = spell['card_name']
        element = spell['element']
        
        # Check if it's a known damage spell
        if spell_name in known_damage_spells:
            damage_data = known_damage_spells[spell_name]
            element_damage[element].append({
                'name': spell_name,
                'min': damage_data['min'],
                'max': damage_data['max'],
                'typical': damage_data['typical']
            })
        else:
            # Check if spell has damage in its effects
            effects_str = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
            if "'type': 'damage'" in effects_str and 'self-damage' not in spell_name.lower():
                # Unknown damage spell - should investigate
                print(f"WARNING: Unknown damage spell found: {spell_name} ({element})")
    
    # Calculate statistics
    print("\nELEMENTAL ELEPHANTS - COMPREHENSIVE SPELL ANALYSIS")
    print("=" * 80)
    print("\nDAMAGE OUTPUT BY ELEMENT")
    print("-" * 80)
    print(f"{'Element':<15} {'Avg Damage':<12} {'Max Potential':<15} {'# Damage Spells':<20} {'Category'}")
    print("-" * 80)
    
    element_stats = []
    for element, damage_spells in element_damage.items():
        if damage_spells:
            avg_typical = sum(s['typical'] for s in damage_spells) / len(damage_spells)
            max_potential = max(s['max'] for s in damage_spells)
            
            # Get category
            category = None
            for cat, data in element_categories['categories'].items():
                if element in data['elements']:
                    category = cat
                    break
            
            element_stats.append({
                'element': element,
                'category': category,
                'avg_typical': avg_typical,
                'max_potential': max_potential,
                'spell_count': len(damage_spells),
                'spells': damage_spells
            })
    
    # Sort by average damage
    element_stats.sort(key=lambda x: x['avg_typical'], reverse=True)
    
    for stat in element_stats:
        print(f"{stat['element']:<15} {stat['avg_typical']:>10.1f} {stat['max_potential']:>13} {stat['spell_count']:>15} [{stat['category']}]")
    
    # Show spell details
    print("\n\nDAMAGE SPELL DETAILS BY ELEMENT")
    print("-" * 80)
    
    for stat in element_stats:
        print(f"\n{stat['element'].upper()} [{stat['category']}] - {stat['spell_count']} damage spells:")
        for spell in stat['spells']:
            print(f"  • {spell['name']}: {spell['min']}-{spell['max']} damage (typical: {spell['typical']})")
    
    # Category summary
    print("\n\nDAMAGE BY ELEMENT CATEGORY")
    print("-" * 80)
    
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
    
    # Count total spells by element for completeness check
    print("\n\nTOTAL SPELL COUNT BY ELEMENT")
    print("-" * 80)
    
    element_total_spells = defaultdict(int)
    for spell in spells:
        element_total_spells[spell['element']] += 1
    
    print(f"{'Element':<15} {'Total Spells':<15} {'Damage Spells':<15} {'% Damage'}")
    print("-" * 80)
    
    for element in sorted(element_total_spells.keys()):
        total = element_total_spells[element]
        damage_count = len([s for s in element_damage.get(element, []) if s])
        percentage = (damage_count / total * 100) if total > 0 else 0
        print(f"{element:<15} {total:<15} {damage_count:<15} {percentage:>6.1f}%")


if __name__ == "__main__":
    analyze_all_damage_spells()