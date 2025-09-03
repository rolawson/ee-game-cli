#!/usr/bin/env python3
"""
Detailed analysis of response spell trigger rates to identify why they seem too high
"""

import json
from collections import defaultdict

def analyze_response_triggers_detailed():
    """Deep dive into response spell trigger mechanics"""
    
    # Load game logs
    game_logs = []
    try:
        with open('game_logs.json', 'r') as f:
            game_logs = json.load(f)
    except:
        print("No game logs found. Run analytics first.")
        return
    
    # Load spell data
    response_spells = {}
    spell_conditions = {}
    try:
        with open('spells.json', 'r') as f:
            spell_data = json.load(f)
            for spell in spell_data:
                spell_name = spell.get('card_name')
                types = spell.get('spell_types', [])
                
                if 'response' in types:
                    response_spells[spell_name] = spell
                    
                    # Extract exact conditions
                    conditions = []
                    
                    # Check resolve effects
                    for effect in spell.get('resolve_effects', []):
                        cond = effect.get('condition', {})
                        if cond.get('type') and cond.get('type') != 'always':
                            conditions.append({
                                'type': cond.get('type'),
                                'parameters': cond.get('parameters', {}),
                                'phase': 'resolve'
                            })
                    
                    # Check advance effects
                    for effect in spell.get('advance_effects', []):
                        cond = effect.get('condition', {})
                        if cond.get('type') and 'if_' in cond.get('type'):
                            conditions.append({
                                'type': cond.get('type'),
                                'parameters': cond.get('parameters', {}),
                                'phase': 'advance'
                            })
                    
                    spell_conditions[spell_name] = conditions
    except:
        print("Could not load spell data")
        return
    
    # Focus on specific suspicious spells
    suspicious_spells = ['Nightglow', 'Grow', 'Absorb', 'Ritual', 'Agonize']
    
    print("=== DETAILED RESPONSE SPELL ANALYSIS ===\n")
    
    for spell_name in suspicious_spells:
        if spell_name not in response_spells:
            continue
            
        print(f"\n{'='*60}")
        print(f"ANALYZING: {spell_name}")
        print(f"{'='*60}")
        
        # Get conditions
        conditions = spell_conditions.get(spell_name, [])
        if conditions:
            print("\nConditions:")
            for cond in conditions:
                print(f"  - {cond['type']} (phase: {cond['phase']})")
                if cond['parameters']:
                    print(f"    Parameters: {cond['parameters']}")
        else:
            print("\nConditions: Always triggers")
        
        # Track detailed stats
        spell_plays = []
        
        # Analyze each game
        for game_idx, game in enumerate(game_logs):
            # Track game state
            player_boards = defaultdict(lambda: defaultdict(list))  # player -> clash -> spells
            
            for event in game.get('events', []):
                clash_num = event.get('clash', 1)
                round_num = event.get('round', 1)
                
                if event['type'] == 'spell_played':
                    played_spell = event.get('spell', event.get('spell_name'))
                    player = event.get('player')
                    
                    # Track board state
                    player_boards[player][clash_num].append(played_spell)
                    
                    if played_spell == spell_name:
                        # Record detailed play info
                        play_info = {
                            'game': game_idx,
                            'round': round_num,
                            'clash': clash_num,
                            'player': player,
                            'triggered': False,
                            'board_state': dict(player_boards[player]),
                            'conditions_checked': []
                        }
                        
                        # Check if conditions were met
                        if spell_name == 'Nightglow':
                            # Need active spells in current clash
                            active_in_clash = len([s for s in player_boards[player][clash_num] if s != spell_name])
                            play_info['conditions_checked'].append(f"Active spells in clash: {active_in_clash}")
                            
                        spell_plays.append(play_info)
                
                # Check if spell triggered
                elif event['type'] in ['damage_dealt', 'healing_done', 'spell_advanced']:
                    source_spell = event.get('spell', event.get('spell_name'))
                    if source_spell == spell_name:
                        # Find the corresponding play
                        for play in reversed(spell_plays):
                            if (play['player'] == event.get('source_player', event.get('player')) and
                                play['round'] == event.get('round', 1) and
                                not play['triggered']):
                                play['triggered'] = True
                                break
        
        # Analyze results
        total_plays = len(spell_plays)
        triggered_plays = sum(1 for p in spell_plays if p['triggered'])
        
        print(f"\nTotal plays: {total_plays}")
        print(f"Triggered: {triggered_plays} ({triggered_plays/total_plays*100:.1f}%)" if total_plays > 0 else "No plays")
        
        # Sample some plays to see patterns
        if spell_plays:
            print("\nSample plays (first 5):")
            for i, play in enumerate(spell_plays[:5]):
                print(f"\n  Play {i+1}:")
                print(f"    Round {play['round']}, Clash {play['clash']}")
                print(f"    Triggered: {play['triggered']}")
                if play['conditions_checked']:
                    for check in play['conditions_checked']:
                        print(f"    {check}")
                print(f"    Board state: {play['board_state']}")

def analyze_condition_frequencies():
    """Check how often specific conditions are actually met"""
    
    # Load game logs
    game_logs = []
    try:
        with open('game_logs.json', 'r') as f:
            game_logs = json.load(f)
    except:
        print("No game logs found.")
        return
    
    print("\n\n=== CONDITION FREQUENCY ANALYSIS ===")
    
    condition_stats = {
        'caster_has_active_spells': {'checked': 0, 'met': 0},
        'enemy_has_active_spells': {'checked': 0, 'met': 0},
        'spell_advanced_this_turn': {'checked': 0, 'met': 0},
        'board_has_spell_type': {'checked': 0, 'met': 0}
    }
    
    for game in game_logs:
        # Track state
        player_active_spells = defaultdict(lambda: defaultdict(set))  # player -> clash -> spells
        spells_advanced_this_turn = defaultdict(set)  # round -> players who advanced
        
        current_round = 0
        
        for event in game.get('events', []):
            round_num = event.get('round', 1)
            clash_num = event.get('clash', 1)
            
            # New round - clear turn-based tracking
            if round_num != current_round:
                current_round = round_num
                spells_advanced_this_turn.clear()
            
            if event['type'] == 'spell_played':
                player = event.get('player')
                spell = event.get('spell', event.get('spell_name'))
                
                # Add to active spells
                player_active_spells[player][clash_num].add(spell)
                
                # Check conditions at time of play
                # Caster has active spells in this clash?
                active_count = len(player_active_spells[player][clash_num]) - 1  # Exclude the spell being played
                condition_stats['caster_has_active_spells']['checked'] += 1
                if active_count > 0:
                    condition_stats['caster_has_active_spells']['met'] += 1
                
                # Enemy has active spells?
                enemy_active = False
                for p, clashes in player_active_spells.items():
                    if p != player:
                        for c, spells in clashes.items():
                            if spells:
                                enemy_active = True
                                break
                condition_stats['enemy_has_active_spells']['checked'] += 1
                if enemy_active:
                    condition_stats['enemy_has_active_spells']['met'] += 1
                
                # Spell advanced this turn?
                condition_stats['spell_advanced_this_turn']['checked'] += 1
                if player in spells_advanced_this_turn[round_num]:
                    condition_stats['spell_advanced_this_turn']['met'] += 1
            
            elif event['type'] == 'spell_advanced':
                player = event.get('player')
                spells_advanced_this_turn[round_num].add(player)
            
            elif event['type'] == 'spell_cancelled':
                # Remove from active spells
                player = event.get('player')
                spell = event.get('spell')
                if spell and player:
                    for clash_spells in player_active_spells[player].values():
                        clash_spells.discard(spell)
    
    print("\nHow often are response conditions naturally met?")
    for condition, stats in condition_stats.items():
        if stats['checked'] > 0:
            rate = stats['met'] / stats['checked'] * 100
            print(f"\n{condition}:")
            print(f"  Checked: {stats['checked']} times")
            print(f"  Met: {stats['met']} times ({rate:.1f}%)")

if __name__ == "__main__":
    analyze_response_triggers_detailed()
    analyze_condition_frequencies()