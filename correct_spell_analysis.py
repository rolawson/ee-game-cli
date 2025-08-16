#!/usr/bin/env python3
"""Correct spell analysis with manually verified data"""

import json

# Manually verified damage spell data
DAMAGE_SPELLS = {
    'Fire': [
        ('Fireball', 1, 1),  # Deals 1 damage
        ('Blaze', 2, 2),     # Deals 2 damage
        ('Ignite', 1, 4)     # Can advance 3 times for 4 total
    ],
    'Water': [
        ('Flow', 1, 1)       # Deals 1 damage
    ],
    'Wind': [
        ('Turbulence', 1, 2) # 1-2 damage based on condition
    ],
    'Earth': [
        ('Rumble', 1, 1),    # Deals 1 damage
        ('Aftershocks', 2, 2) # Deals 2 damage
    ],
    'Wood': [
        ('Seed', 1, 1),      # Deals 1 damage
        ('Grow', 0, 0),      # Healing only
        ('Prickle', 1, 6)    # 1 or up to 6 damage
    ],
    'Metal': [
        ('Defend', 1, 1),    # Deals 1 damage
        ('Besiege', 1, 1)    # Deals 1 damage
    ],
    'Time': [
        ('Quickshot', 1, 1), # Deals 1 damage
        ('Impact', 0, 9)     # 0-9 based on other clashes
    ],
    'Space': [
        ('Void', 1, 1)       # Deals 1 damage
    ],
    'Sunbeam': [
        ('Illuminate', 1, 3), # 1 or 3 damage
        ('Glare', 1, 1)      # Deals 1 damage to all
    ],
    'Moonshine': [
        ('Slumber', 1, 1),   # Deals 1 damage
        ('Bedim', 1, 1)      # Deals 1 damage
    ],
    'Shadow': [
        ('Obscure', 1, 1)    # Deals 1 damage
    ],
    'Aster': [
        ('Meteorite', 1, 1), # Deals 1 damage
        ('Starfall', 1, 2)   # Deals 1 or 2 damage
    ],
    'Blood': [
        ('Offering', 2, 2),  # Deals 2 damage
        ('Ritual', 1, 6),    # 1-6 damage
        ('Overexert', 4, 4)  # Deals 4 damage
    ],
    'Ichor': [
        ('Dominion', 1, 3)   # Damage per enemy boost spell
    ],
    'Venom': [
        ('Sting', 1, 1),     # Deals 1 damage
        ('Poison', 1, 1),    # Deals 1 damage
        ('Enfeeble', 1, 2)   # Deals 1 or 2 damage
    ],
    'Nectar': [
        ('Absorb', 1, 1)     # Deals 1 damage
    ],
    'Lightning': [
        ('Bolt', 1, 1),      # Deals 1 damage
        ('Surge', 1, 1)      # Deals 1 damage
    ],
    'Thunder': [
        ('Stupefy', 1, 2)    # Deals 1 or 2 damage
    ],
    'Twilight': [
        ('Dusk', 2, 2),      # Deals 2 damage
        ('Crepuscule', 1, 2) # 1-2 damage
    ]
}

def generate_correct_report():
    """Generate report with correct data"""
    
    with open('element_categories.json', 'r') as f:
        element_categories = json.load(f)
    
    print("ELEMENTAL ELEPHANTS - CORRECTED SPELL ANALYSIS")
    print("=" * 80)
    print("\nDAMAGE OUTPUT BY ELEMENT")
    print("-" * 80)
    print(f"{'Element':<15} {'Avg Damage':<12} {'Max Potential':<15} {'# Damage Spells':<20} {'Category'}")
    print("-" * 80)
    
    element_stats = []
    
    for element, spells in DAMAGE_SPELLS.items():
        if spells:
            # Filter out non-damage spells (like Grow)
            damage_spells = [(name, min_d, max_d) for name, min_d, max_d in spells if max_d > 0]
            
            if damage_spells:
                avg_damage = sum((min_d + max_d) / 2 for _, min_d, max_d in damage_spells) / len(damage_spells)
                max_potential = max(max_d for _, _, max_d in damage_spells)
                
                # Get category
                category = None
                for cat, data in element_categories['categories'].items():
                    if element in data['elements']:
                        category = cat
                        break
                
                element_stats.append({
                    'element': element,
                    'category': category,
                    'avg_damage': avg_damage,
                    'max_potential': max_potential,
                    'spell_count': len(damage_spells),
                    'spells': damage_spells
                })
    
    # Sort by average damage
    element_stats.sort(key=lambda x: x['avg_damage'], reverse=True)
    
    for stat in element_stats:
        print(f"{stat['element']:<15} {stat['avg_damage']:>10.1f} {stat['max_potential']:>13} {stat['spell_count']:>15} [{stat['category']}]")
    
    # Show details
    print("\n\nDAMAGE SPELL DETAILS")
    print("-" * 80)
    
    for stat in element_stats:
        print(f"\n{stat['element']} [{stat['category']}] - {stat['spell_count']} damage spell(s):")
        for name, min_d, max_d in stat['spells']:
            if min_d == max_d:
                print(f"  • {name}: {min_d} damage")
            else:
                print(f"  • {name}: {min_d}-{max_d} damage")
    
    # Category summary
    print("\n\nCATEGORY SUMMARY")
    print("-" * 80)
    
    category_totals = {
        'offense': {'count': 0, 'elements': []},
        'defense': {'count': 0, 'elements': []},
        'mobility': {'count': 0, 'elements': []},
        'balanced': {'count': 0, 'elements': []}
    }
    
    for stat in element_stats:
        cat = stat['category']
        if cat:
            category_totals[cat]['count'] += stat['spell_count']
            category_totals[cat]['elements'].append(stat['element'])
    
    for cat, data in category_totals.items():
        print(f"\n{cat.upper()}: {data['count']} damage spells")
        print(f"Elements: {', '.join(data['elements'])}")


if __name__ == "__main__":
    generate_correct_report()