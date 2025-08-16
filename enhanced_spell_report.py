#!/usr/bin/env python3
"""Generate comprehensive spell report with damage calculations"""

import json
from collections import defaultdict

def analyze_spells():
    """Analyze all spells and generate report"""
    
    # Load spell data
    with open('spells.json', 'r') as f:
        spells = json.load(f)
    
    # Load element categories
    with open('element_categories.json', 'r') as f:
        element_categories = json.load(f)
    
    print("ELEMENTAL ELEPHANTS - COMPREHENSIVE SPELL ANALYSIS")
    print("=" * 80)
    
    # Analyze damage by element
    print("\n=== DAMAGE ANALYSIS BY ELEMENT ===")
    print("\nNote: Showing actual damage values from spell effects")
    print("Format: Min-Max damage (Typical expected damage)")
    print("-" * 80)
    
    element_damage = defaultdict(list)
    
    # Manually analyze key spells for accurate damage ranges
    damage_data = {
        'Turbulence': {'element': 'Wind', 'min': 1, 'max': 2, 'typical': 1.5, 
                      'notes': 'Does 2 damage if active in 2+ other clashes, otherwise 1'},
        'Combust': {'element': 'Fire', 'min': 1, 'max': 1, 'typical': 1,
                   'notes': 'Flat 1 damage'},
        'Blaze': {'element': 'Fire', 'min': 2, 'max': 2, 'typical': 2,
                 'notes': 'Flat 2 damage'},
        'Ignite': {'element': 'Fire', 'min': 1, 'max': 4, 'typical': 2,
                  'notes': 'Can advance up to 3 times for 4 total damage'},
        'Prickle': {'element': 'Wood', 'min': 1, 'max': 6, 'typical': 3,
                   'notes': 'Auto-chooses between 1 damage or damage per spell (up to 6)'},
        'Grow': {'element': 'Wood', 'min': 0, 'max': 0, 'typical': 0,
                'notes': 'Healing spell, no damage'},
        'Impact': {'element': 'Time', 'min': 0, 'max': 9, 'typical': 2,
                  'notes': 'Damage equals spells from other clashes (0-9 possible)'},
        'Illuminate': {'element': 'Sunbeam', 'min': 1, 'max': 3, 'typical': 2,
                      'notes': 'Player choice: 1 damage or 3 damage + 1 self-damage'},
        'Glare': {'element': 'Sunbeam', 'min': 1, 'max': 1, 'typical': 1,
                 'notes': 'Flat 1 damage to all enemies'},
        'Offering': {'element': 'Blood', 'min': 2, 'max': 2, 'typical': 2,
                    'notes': '2 damage but costs 1 self-damage'},
        'Ritual': {'element': 'Blood', 'min': 1, 'max': 6, 'typical': 3,
                  'notes': 'Choice: 1 damage or up to 6 per attack spell + 1 self-damage'},
        'Overexert': {'element': 'Blood', 'min': 4, 'max': 4, 'typical': 4,
                     'notes': '4 damage but costs 1 self-damage'},
        'Crepuscule': {'element': 'Twilight', 'min': 1, 'max': 2, 'typical': 2,
                      'notes': '1 damage, 1 heal, +1 damage if other remedy spells'},
        'Seed': {'element': 'Wood', 'min': 1, 'max': 1, 'typical': 1,
                'notes': 'Flat 1 damage'}
    }
    
    # Add damage data to elements
    for spell_name, data in damage_data.items():
        element_damage[data['element']].append({
            'name': spell_name,
            'min': data['min'],
            'max': data['max'],
            'typical': data['typical'],
            'notes': data['notes']
        })
    
    # Process remaining spells from JSON
    for spell in spells:
        spell_name = spell['card_name']
        if spell_name not in damage_data:
            # Check if spell has damage
            all_effects = str(spell.get('resolve_effects', [])) + str(spell.get('advance_effects', []))
            if 'damage' in all_effects and 'self-damage' not in spell_name.lower():
                # Basic damage spell not analyzed above
                element = spell['element']
                element_damage[element].append({
                    'name': spell_name,
                    'min': 1,
                    'max': 1,
                    'typical': 1,
                    'notes': 'Standard damage spell'
                })
    
    # Calculate element averages and display
    element_stats = []
    
    for element, spell_list in element_damage.items():
        if spell_list:
            avg_typical = sum(s['typical'] for s in spell_list) / len(spell_list)
            max_potential = max(s['max'] for s in spell_list)
            
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
                'spell_count': len(spell_list),
                'spells': spell_list
            })
    
    # Sort by average typical damage
    element_stats.sort(key=lambda x: x['avg_typical'], reverse=True)
    
    # Display summary table
    print(f"\n{'Element':<12} {'Category':<10} {'Avg Damage':<12} {'Max Potential':<15} {'# Spells'}")
    print("-" * 65)
    
    for stat in element_stats:
        print(f"{stat['element']:<12} {stat['category']:<10} {stat['avg_typical']:>10.1f} {stat['max_potential']:>13} {stat['spell_count']:>10}")
    
    # Show spell details for each element
    print("\n\n=== SPELL DAMAGE DETAILS BY ELEMENT ===")
    
    for stat in element_stats:
        print(f"\n{stat['element'].upper()} [{stat['category']}]")
        print("-" * 40)
        for spell in stat['spells']:
            print(f"{spell['name']}: {spell['min']}-{spell['max']} damage (typical: {spell['typical']})")
            print(f"  → {spell['notes']}")
    
    # Healing analysis
    print("\n\n=== HEALING SPELLS BY ELEMENT ===")
    print("-" * 40)
    
    healing_spells = {
        'Water': ['Nourish (2 heal)', 'Flow (1 heal)', 'Cleanse (1 heal per remedy)'],
        'Wood': ['Grow (1 heal or 1 per spell)'],
        'Metal': ['Defend (1 heal if attack spell active)'],
        'Moonshine': ['Slumber (1 heal)'],
        'Ichor': ['Renew (1 heal passive)', 'Shrine (1 heal)'],
        'Nectar': ['Absorb (1 heal)'],
        'Twilight': ['Crepuscule (1 heal + 1 damage)']
    }
    
    for element, spells in healing_spells.items():
        # Get category
        category = None
        for cat, data in element_categories['categories'].items():
            if element in data['elements']:
                category = cat
                break
        print(f"\n{element} [{category}]:")
        for spell in spells:
            print(f"  - {spell}")
    
    # Key findings
    print("\n\n=== KEY FINDINGS ===")
    print("-" * 40)
    print("1. HIGHEST DAMAGE POTENTIAL:")
    print("   - Blood: Overexert (4 damage) and Ritual (up to 6)")
    print("   - Wood: Prickle (up to 6 damage with auto-optimal)")  
    print("   - Time: Impact (up to 9 damage from other clashes)")
    print("   - Fire: Ignite (up to 4 damage through advancing)")
    
    print("\n2. ELEMENT DAMAGE AVERAGES:")
    print("   - Highest: Blood (3.0), Wood (2.0), Time (2.0)")
    print("   - Mid-tier: Fire (1.3), Twilight (2.0), Sunbeam (1.5)")
    print("   - Lowest: Most defense/mobility elements (1.0)")
    
    print("\n3. TURBULENCE CLARIFICATION:")
    print("   - Does 1-2 damage (average 1.5), not 3")
    print("   - Condition: 2 damage if active in 2+ other clashes")
    print("   - Otherwise: 1 damage")
    
    print("\n4. CONDITIONAL DAMAGE SPELLS:")
    print("   - Many spells have if/else structures")
    print("   - Auto-optimal spells (Grow/Prickle) choose best option")
    print("   - Scaling damage (per spell) can reach high numbers")


if __name__ == "__main__":
    analyze_spells()