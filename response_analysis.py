#!/usr/bin/env python3
"""
Analyze response spell interactions and test the Agonize hypothesis
"""

import json
import sys
from collections import defaultdict

def analyze_response_interactions():
    """Analyze which spells trigger which responses"""
    
    # Load game logs
    game_logs = []
    try:
        with open('game_logs.json', 'r') as f:
            game_logs = json.load(f)
    except:
        print("No game logs found. Run analytics first.")
        return
    
    # Load spell data to identify response spells
    response_spells = set()
    spell_types = {}
    try:
        with open('spells.json', 'r') as f:
            spell_data = json.load(f)
            for spell in spell_data:
                spell_name = spell.get('card_name')
                types = spell.get('spell_types', [])
                spell_types[spell_name] = types
                if 'response' in types:
                    response_spells.add(spell_name)
    except:
        print("Could not load spell data")
        return
    
    # Track interactions
    spell_play_counts = defaultdict(int)
    response_trigger_counts = defaultdict(int)
    spell_before_response = defaultdict(lambda: defaultdict(int))
    response_conditions_met = defaultdict(lambda: {'played': 0, 'triggered': 0})
    
    print(f"Found {len(response_spells)} response spells")
    
    # Analyze each game
    for game in game_logs:
        # Track spells played in each round
        round_spells = defaultdict(list)
        
        for event in game.get('events', []):
            round_num = event.get('round', 1)
            
            if event['type'] == 'spell_played':
                spell_name = event.get('spell', event.get('spell_name'))
                player = event.get('player')
                spell_play_counts[spell_name] += 1
                
                # Track all spells played this round
                round_spells[round_num].append({
                    'spell': spell_name,
                    'player': player,
                    'types': spell_types.get(spell_name, [])
                })
                
                if spell_name in response_spells:
                    response_conditions_met[spell_name]['played'] += 1
            
            # Track when responses deal damage/heal
            elif event['type'] in ['damage_dealt', 'healing_done']:
                spell_name = event.get('spell', event.get('spell_name'))
                if spell_name in response_spells:
                    response_trigger_counts[spell_name] += 1
                    response_conditions_met[spell_name]['triggered'] += 1
                    
                    # Look at what was played before this response
                    for spell_info in round_spells.get(round_num, []):
                        if spell_info['spell'] != spell_name:
                            spell_before_response[spell_name][spell_info['spell']] += 1
    
    # Print results
    print("\n=== SPELL PLAY FREQUENCY ===")
    sorted_plays = sorted(spell_play_counts.items(), key=lambda x: x[1], reverse=True)
    for spell, count in sorted_plays[:20]:
        types = spell_types.get(spell, [])
        print(f"{spell:20} - {count:4} plays ({', '.join(types)})")
    
    print("\n=== RESPONSE SPELL EFFECTIVENESS ===")
    for response in sorted(response_spells):
        data = response_conditions_met.get(response, {'played': 0, 'triggered': 0})
        if data['played'] > 0:
            rate = data['triggered'] / data['played'] * 100
            print(f"{response:20} - {rate:5.1f}% trigger rate ({data['triggered']}/{data['played']})")
    
    print("\n=== SPELLS COMMONLY PLAYED BEFORE RESPONSES ===")
    # Focus on responses with high trigger rates
    high_trigger_responses = []
    for response, data in response_conditions_met.items():
        if data['played'] > 20 and data['triggered'] / data['played'] > 0.7:
            high_trigger_responses.append(response)
    
    for response in sorted(high_trigger_responses):
        print(f"\n{response} (high trigger rate):")
        before_spells = spell_before_response[response]
        sorted_before = sorted(before_spells.items(), key=lambda x: x[1], reverse=True)
        for spell, count in sorted_before[:5]:
            print(f"  - {spell}: {count} times")
    
    # Test Agonize hypothesis
    print("\n=== AGONIZE ANALYSIS ===")
    agonize_plays = spell_play_counts.get('Agonize', 0)
    print(f"Agonize played: {agonize_plays} times")
    
    # Look for responses that counter Agonize
    print("\nResponses played after Agonize:")
    for response, spells in spell_before_response.items():
        agonize_count = spells.get('Agonize', 0)
        if agonize_count > 0:
            print(f"  {response}: {agonize_count} times")

if __name__ == "__main__":
    analyze_response_interactions()