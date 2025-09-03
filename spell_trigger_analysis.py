#!/usr/bin/env python3
"""
Analyze which spells trigger other spells and verify response spell classification
"""

import json
from collections import defaultdict

def analyze_spell_triggers():
    """Analyze spell trigger chains and response spell accuracy"""
    
    # Load game logs
    game_logs = []
    try:
        with open('game_logs.json', 'r') as f:
            game_logs = json.load(f)
    except:
        print("No game logs found. Run analytics first.")
        return
    
    # Load spell data to identify response spells correctly
    response_spells = set()
    spell_conditions = {}
    try:
        with open('spells.json', 'r') as f:
            spell_data = json.load(f)
            for spell in spell_data:
                spell_name = spell.get('card_name')
                types = spell.get('spell_types', [])
                
                # Only count as response if it has 'response' type
                if 'response' in types:
                    response_spells.add(spell_name)
                    
                    # Extract conditions
                    conditions = []
                    for effect in spell.get('resolve_effects', []):
                        cond = effect.get('condition', {})
                        if cond.get('type') != 'always':
                            conditions.append(cond.get('type'))
                    
                    # Also check advance effects for response conditions
                    for effect in spell.get('advance_effects', []):
                        cond = effect.get('condition', {})
                        if cond.get('type') and 'if_' in cond.get('type'):
                            conditions.append(cond.get('type') + ' (advance)')
                    
                    spell_conditions[spell_name] = conditions
    except:
        print("Could not load spell data")
        return
    
    print(f"Found {len(response_spells)} response spells")
    print("\nResponse spells and their conditions:")
    for spell in sorted(response_spells):
        conditions = spell_conditions.get(spell, [])
        print(f"  {spell:20} - {', '.join(conditions) if conditions else 'always'}")
    
    # Track what triggers what
    trigger_chains = defaultdict(lambda: defaultdict(int))
    spell_after_spell = defaultdict(lambda: defaultdict(int))
    damage_sources = defaultdict(lambda: defaultdict(int))
    
    # Analyze each game
    for game in game_logs:
        # Track spells and damage in each round
        round_events = defaultdict(list)
        
        for event in game.get('events', []):
            round_num = event.get('round', 1)
            round_events[round_num].append(event)
        
        # Analyze each round
        for round_num, events in round_events.items():
            # Track spell plays and their effects in order
            spell_sequence = []
            
            for event in events:
                if event['type'] == 'spell_played':
                    spell_name = event.get('spell', event.get('spell_name'))
                    player = event.get('player')
                    spell_sequence.append({
                        'spell': spell_name,
                        'player': player,
                        'is_response': spell_name in response_spells
                    })
                
                elif event['type'] == 'damage_dealt':
                    source_spell = event.get('spell', event.get('spell_name'))
                    target = event.get('target_player')
                    
                    # Look for what spell was played before this damage
                    if len(spell_sequence) >= 2:
                        for i in range(len(spell_sequence) - 1):
                            prior_spell = spell_sequence[i]['spell']
                            next_spell = spell_sequence[i + 1]['spell']
                            
                            # If the damage dealer is a response spell
                            if source_spell == next_spell and next_spell in response_spells:
                                # The prior spell likely triggered it
                                trigger_chains[prior_spell][next_spell] += 1
                                damage_sources[next_spell][prior_spell] += 1
            
            # Track simple spell-after-spell patterns
            for i in range(len(spell_sequence) - 1):
                current = spell_sequence[i]['spell']
                next_spell = spell_sequence[i + 1]['spell']
                spell_after_spell[current][next_spell] += 1
    
    # Print results
    print("\n=== SPELLS THAT TRIGGER RESPONSE SPELLS ===")
    # For each response spell, show what triggers it most often
    for response in sorted(response_spells):
        triggers = trigger_chains.get(response, {})
        if not triggers:
            triggers = {}
            # Use spell_after_spell as fallback
            for spell, followers in spell_after_spell.items():
                if response in followers:
                    triggers[spell] = followers[response]
        
        if triggers:
            print(f"\n{response} is most often triggered by:")
            sorted_triggers = sorted(triggers.items(), key=lambda x: x[1], reverse=True)
            total_triggers = sum(t[1] for t in sorted_triggers)
            for trigger, count in sorted_triggers[:5]:
                percentage = (count / total_triggers * 100) if total_triggers > 0 else 0
                print(f"  {trigger:20} - {count:3} times ({percentage:4.1f}%)")
    
    print("\n=== DAMAGE-DEALING RESPONSE SPELLS ===")
    # For response spells that deal damage, what triggers them
    for response in sorted(response_spells):
        if response in damage_sources and damage_sources[response]:
            print(f"\n{response} deals damage after:")
            sorted_sources = sorted(damage_sources[response].items(), 
                                  key=lambda x: x[1], reverse=True)
            for source, count in sorted_sources[:5]:
                print(f"  {source:20} - {count:3} times")
    
    # Specific analysis for spells of interest
    print("\n=== SPECIFIC SPELL ANALYSIS ===")
    
    # Check what follows Agonize
    if 'Agonize' in spell_after_spell:
        print("\nSpells played after Agonize:")
        agonize_followers = spell_after_spell['Agonize']
        sorted_followers = sorted(agonize_followers.items(), 
                                key=lambda x: x[1], reverse=True)
        for spell, count in sorted_followers[:10]:
            is_response = " (response)" if spell in response_spells else ""
            print(f"  {spell:20} - {count:3} times{is_response}")
    
    # Check what triggers Punishment
    print("\nWhat triggers Punishment:")
    punishment_triggers = {}
    for spell, followers in spell_after_spell.items():
        if 'Punishment' in followers:
            punishment_triggers[spell] = followers['Punishment']
    
    if punishment_triggers:
        sorted_triggers = sorted(punishment_triggers.items(), 
                               key=lambda x: x[1], reverse=True)
        for trigger, count in sorted_triggers[:10]:
            print(f"  {trigger:20} - {count:3} times")

if __name__ == "__main__":
    analyze_spell_triggers()