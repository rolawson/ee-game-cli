#!/usr/bin/env python3
"""
Check which spells are marked as response type in spells.json
"""

import json

def check_response_spells():
    """List all spells marked as response type"""
    
    with open('spells.json', 'r') as f:
        spell_data = json.load(f)
    
    response_spells = []
    
    for spell in spell_data:
        spell_name = spell.get('card_name')
        types = spell.get('spell_types', [])
        
        if 'response' in types:
            # Check if it has conditional effects
            has_conditions = False
            condition_types = []
            
            # Check resolve effects
            for effect in spell.get('resolve_effects', []):
                cond = effect.get('condition', {})
                cond_type = cond.get('type')
                if cond_type and cond_type != 'always':
                    has_conditions = True
                    condition_types.append(f"resolve: {cond_type}")
            
            # Check advance effects
            for effect in spell.get('advance_effects', []):
                cond = effect.get('condition', {})
                cond_type = cond.get('type')
                if cond_type and 'if_' in cond_type:
                    has_conditions = True
                    condition_types.append(f"advance: {cond_type}")
            
            response_spells.append({
                'name': spell_name,
                'types': types,
                'has_conditions': has_conditions,
                'conditions': condition_types,
                'element': spell.get('element')
            })
    
    # Sort by whether they have conditions
    response_spells.sort(key=lambda x: (not x['has_conditions'], x['name']))
    
    print(f"Total spells marked as 'response': {len(response_spells)}\n")
    
    print("=== RESPONSE SPELLS WITH CONDITIONS ===")
    for spell in response_spells:
        if spell['has_conditions']:
            print(f"{spell['name']:20} ({spell['element']:10}) - {', '.join(spell['conditions'])}")
    
    print("\n=== RESPONSE SPELLS WITHOUT CONDITIONS (possibly mislabeled) ===")
    for spell in response_spells:
        if not spell['has_conditions']:
            print(f"{spell['name']:20} ({spell['element']:10}) - Types: {', '.join(spell['types'])}")

if __name__ == "__main__":
    check_response_spells()