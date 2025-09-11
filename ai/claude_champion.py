"""Claude Champion AI - A snarky, all-knowing champion of Elemental Elephants"""

import os
import json
from typing import Dict, Any, Optional
import anthropic
from anthropic import AsyncAnthropic

from .llm_base import LLMBaseAI
from .claude_base_context import get_base_game_context
from .expert import ExpertAI

# Import Colors for debugging
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'


class ClaudeChampionAI(LLMBaseAI):
    """Claude Champion - A snarky, all-knowing AI player"""
    VERSION = "3.1-priority-fixed"  # Version check
    
    def __init__(self):
        super().__init__()
        print(f"[ClaudeChampion] Initialized version {self.VERSION}")
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Set fallback to Expert AI
        self.fallback_ai = ExpertAI()
        
        # Load spells data for system prompt
        spells_data = self._load_spells_data()
        
        # Build spell database for quick lookups
        self.spell_database = self._build_spell_database()
        
        # Element tracking (from ExpertAI)
        self._element_tracking = {}  # Track opponent drafted elements
        
        # System prompt for Claude Champion with full game knowledge
        self.system_prompt = f"""You are Claude Champion - an arrogant, cocky AI who thinks they're the best Elemental Elephants player ever.

{get_base_game_context()}

SPELL DATABASE:
{spells_data}

PERSONALITY: You're overconfident, make grandiose claims, reference past "championships" you've won, and always have excuses when things go wrong. But you DO understand the game deeply.

For game decisions: Respond with JSON.
For anything else: Just respond naturally."""
    
    def _load_spells_data(self) -> str:
        """Load and format spells data for the system prompt"""
        try:
            # Get the path to spells.json
            import os
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            spells_path = os.path.join(current_dir, 'spells.json')
            
            with open(spells_path, 'r') as f:
                spells = json.load(f)
            
            # Format key spell information for easy reference
            formatted = []
            elements = {}
            
            for spell in spells:
                # Group by element
                element = spell.get('element', 'Unknown')
                if element not in elements:
                    elements[element] = []
                
                spell_info = {
                    'name': spell.get('card_name'),
                    'priority': spell.get('priority'),
                    'types': spell.get('spell_types', []),
                    'conjury': spell.get('is_conjury', False),
                    'effect': spell.get('instruction', '')
                }
                elements[element].append(spell_info)
            
            # Format by element
            for element, spell_list in sorted(elements.items()):
                formatted.append(f"\n{element} Element:")
                for spell in spell_list[:5]:  # Show first 5 spells per element
                    types = ', '.join(spell['types']) if spell['types'] else 'no types'
                    conjury = " [CONJURY]" if spell['conjury'] else ""
                    formatted.append(f"  - {spell['name']} (P{spell['priority']}, {types}){conjury}: {spell['effect'][:60]}...")
                if len(spell_list) > 5:
                    formatted.append(f"  ...and {len(spell_list) - 5} more {element} spells!")
            
            return '\n'.join(formatted)
        except Exception:
            # Fallback if can't load spells
            return """
Fire: Fireball, Scorch, Ignite (damage and burn)
Water: Nourish, Flow, Cleanse (healing)
Earth: Crush, Aftershocks, Quake (control)
Wind: Turbulence, Blow, Gust (movement)
Wood: Seed, Grow, Prickle (growth)
Metal: Reinforce, Besiege, Defend (defense)
...and many more elements and spells!"""
    
    async def _get_llm_decision(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Get a decision from Claude Champion"""
        try:
            # Build the appropriate prompt based on decision type
            if decision_type == "select_card":
                prompt = self._build_card_selection_prompt(context)
            elif decision_type == "make_choice":
                prompt = self._build_choice_prompt(context)
            elif decision_type == "draft":
                prompt = self._build_draft_prompt(context)
            elif decision_type == "round_analysis":
                prompt = self._build_round_analysis_prompt(context)
                # Debug log the prompt
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\\033[90m[Claude-Champion] Round prompt preview: {prompt[:150]}...\\033[0m"
                    )
            elif decision_type == "game_end":
                prompt = self._build_game_end_prompt(context)
            else:
                return None
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=1.0,  # Max temperature for maximum variety
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Debug: Log the raw response
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[Claude-Champion] Raw response: {content[:200]}...\\033[0m"
                )
            
            # For round analysis, return raw text
            if decision_type == "round_analysis":
                print(f"\n{Colors.CYAN}>>> Raw AI response: {content[:100]}...{Colors.ENDC}")  # Direct print
                # Write full response to debug file
                import os
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug_logs')
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, 'claude_debug.txt')
                with open(debug_file, 'a') as f:
                    f.write(f"\nAI Response:\n{content}\n{'='*50}\n")
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"\\033[90m[Claude-Champion] Round analysis raw: {content}\\033[0m"
                    )
                return {"analysis": content}
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # If no valid JSON, try to parse as structured text
            return self._parse_text_response(content, decision_type)
            
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[Claude-Champion] API error: {str(e)}\\033[0m"
                )
            return None
    
    def _build_card_selection_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for card selection"""
        prompt_parts = [
            f"Round {context['round']}, Clash {context['clash']} - Time to dominate!",
            f"",
            f"The Champion's Status: {context['player']['health']}/{context['player']['max_health']} HP, {context['player']['trunks']} glorious trunks",
            f""
        ]
        
        # Add enemy status with snarky potential
        for enemy in context['enemies']:
            prompt_parts.append(f"My victim ({enemy['name']}): {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks left to lose")
            # Add their tracked elements
            enemy_elements = self.get_opponent_elements(enemy['name'])
            if enemy_elements:
                prompt_parts.append(f"  Elements: {', '.join(enemy_elements)} (I know all their spells!)")
                # Mention key threats
                dangerous_spells = []
                for element in enemy_elements:
                    element_responses = [name for name, data in self.spell_database.items() 
                                       if data.get('element') == element and 'response' in data.get('types', [])]
                    dangerous_spells.extend(element_responses[:2])
                if dangerous_spells:
                    prompt_parts.append(f"  Watch for: {', '.join(dangerous_spells)} (not that The Champion fears anything!)")
        
        prompt_parts.append("")
        
        # Add recent game events
        if 'recent_actions' in context and context['recent_actions']:
            prompt_parts.append("Recent happenings (The Champion sees all!):")
            for action in context['recent_actions'][-8:]:  # Last 8 actions
                # Clean up color codes
                clean_action = action
                for color in ['[90m', '[0m', '[91m', '[93m', '[94m', '[92m', '[1m']:
                    clean_action = clean_action.replace(f'\033{color}', '')
                prompt_parts.append(f"  - {clean_action}")
        
        prompt_parts.append("")
        
        # Add board state
        if context['board']['player']:
            prompt_parts.append("My masterful board presence:")
            for spell in context['board']['player']:
                prompt_parts.append(f"  - {spell['name']} ({spell['element']} - obviously the best element)")
        
        if context['board']['enemies']:
            prompt_parts.append("Their pitiful attempts:")
            for spell in context['board']['enemies']:
                prompt_parts.append(f"  - {spell['name']} (how... quaint)")
        
        prompt_parts.append("")
        prompt_parts.append("My arsenal of destruction:")
        
        for card in context['valid_cards']:
            priority_str = f"Priority {card['priority']}" if card['priority'] != 'A' else "ADVANCE PRIORITY!"
            priority_note = ""
            if card['priority'] == '1':
                priority_note = " (FASTEST!)"
            elif card['priority'] == '2':
                priority_note = " (very fast)"
            elif card['priority'] == '5':
                priority_note = " (slow)"
            elif card['priority'] == 'A':
                priority_note = " (slowest, but advances)"
            conjury_str = " (CONJURY - my favorite!)" if card['is_conjury'] else ""
            prompt_parts.append(
                f"{card['index']}: {card['name']} - {card['element']} - {priority_str}{priority_note}{conjury_str}"
            )
            prompt_parts.append(f"   Effect: {card['description']}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose your weapon and mock your opponent using specific spell/element names!")
        prompt_parts.append('{"card_index": <index>, "reasoning": "<brief champion logic>", "message": "<snarky taunt with spell names>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_choice_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for player_choice decisions"""
        prompt_parts = [
            f"Ah yes, {context['card_name']} - one of my signature moves!",
            f"Champion's health: {context['player_health']}/{context['player_max_health']}",
            f"",
            "My glorious options:"
        ]
        
        for option in context['options']:
            prompt_parts.append(f"{option['index']}: {option['description']}")
        
        prompt_parts.append("")
        prompt_parts.append("Make your champion's choice:")
        prompt_parts.append('{"choice_index": <index>, "message": "<witty comment about this specific choice>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_draft_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for drafting decisions"""
        prompt_parts = [
            f"Round {context['round']} Draft - Time to show why I'm UNDEFEATED!",
            ""
        ]
        
        # Add opponent elements tracked
        gs = context.get('game_state')
        if gs:
            self._update_element_tracking(gs)
            for player in gs.players:
                if player.name != context['player']['name']:
                    enemy_elements = self.get_opponent_elements(player.name)
                    if enemy_elements:
                        prompt_parts.append(f"My victim {player.name} foolishly chose: {', '.join(enemy_elements)} - how predictable!")
                        # Add specific spell knowledge
                        for element in enemy_elements:
                            key_spells = [name for name, data in self.spell_database.items() 
                                        if data.get('element') == element and 
                                        ('response' in data.get('types', []) or data.get('damage', 0) >= 3)][:3]
                            if key_spells:
                                prompt_parts.append(f"  (They probably have {', '.join(key_spells)}... not that it matters!)")
        
        prompt_parts.append("")
        prompt_parts.append("Sets worthy of The Champion:")
        
        for set_info in context['available_sets']:
            prompt_parts.append(f"\n{set_info['index']}: {set_info['element']} Element")
            for card in set_info['cards']:
                types_str = ', '.join(card['types']) if card['types'] else "pure chaos"
                priority_str = f"P{card['priority']}" if card['priority'] != 'A' else "Advance!"
                conjury_str = " (Conjury!)" if card['is_conjury'] else ""
                prompt_parts.append(f"  - {card['name']} ({priority_str}){conjury_str}")
        
        prompt_parts.append("")
        prompt_parts.append("Draft with champion swagger - reference specific spells by name:")
        prompt_parts.append("Consider their elements when boasting about counters!")
        prompt_parts.append('{"set_index": <index>, "message": "<boast about these specific spells and mock other elements>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_round_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for end-of-round taunting"""
        import random
        
        # Debug what we received
        print(f"\n>>> [CHAMPION DEBUG] Building round analysis prompt")
        print(f">>> Action log entries: {len(context.get('action_log', []))}")
        print(f">>> Round plays: {len(context.get('round_plays', []))}")
        print(f">>> Player health: {context.get('player_health', [])}")
        print(f">>> Has player state: {'player' in context}")
        print(f">>> Has enemies: {len(context.get('enemies', []))}")
        
        # Build comprehensive round summary
        prompt_parts = [
            f"=== ROUND {context['round']} COMPLETE ===",
            ""
        ]
        
        # Add current status
        if 'player' in context:
            p = context['player']
            prompt_parts.append(f"CHAMPION STATUS: {p['health']}/{p['max_health']} HP, {p['trunks']} trunks, {p['hand_size']} cards in hand")
        
        # Add enemy status
        if 'enemies' in context:
            prompt_parts.append("ENEMY STATUS:")
            for enemy in context['enemies']:
                prompt_parts.append(f"  {enemy['name']}: {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks, {enemy['hand_size']} cards")
                # Add their tracked elements
                enemy_elements = self.get_opponent_elements(enemy['name'])
                if enemy_elements:
                    prompt_parts.append(f"    Known elements: {', '.join(enemy_elements)}")
        
        prompt_parts.append("")
        
        # Add what the AI played this round
        if 'round_plays' in context and context['round_plays']:
            prompt_parts.append(f"YOUR PLAYS THIS ROUND (as {context.get('player', {}).get('name', 'Claude Champion')}):")
            for play in context['round_plays']:
                prompt_parts.append(f"  Clash {play['clash']}: YOU played {play['card']}")
                if play.get('reasoning'):
                    prompt_parts.append(f"    Your strategy: {play['reasoning']}")
        
        prompt_parts.append("")
        
        # Add board state
        if 'board' in context:
            if context['board'].get('player'):
                prompt_parts.append(f"YOUR ACTIVE SPELLS (spells YOU played):")
                for spell in context['board']['player']:
                    prompt_parts.append(f"  - YOUR {spell['name']} ({spell['element']})")
            
            if context['board'].get('enemies'):
                prompt_parts.append(f"OPPONENT'S ACTIVE SPELLS (spells THEY played):")
                for spell in context['board']['enemies']:
                    prompt_parts.append(f"  - THEIR {spell['name']} ({spell['element']})")
        
        prompt_parts.append("")
        
        # Process action log for key events
        action_log_text = []
        if 'action_log' in context and context['action_log']:
            for action in context['action_log']:
                # Clean up color codes
                clean_action = action
                for color in ['[90m', '[0m', '[91m', '[93m', '[94m', '[92m', '[1m', '[95m']:
                    clean_action = clean_action.replace(f'\033{color}', '')
                action_log_text.append(clean_action)
        
        # Extract key events from action log
        key_events = []
        for log in action_log_text:
            if any(word in log for word in ["dealt", "healed", "CANCELLED", "lost a trunk", "bolstered", "weakened", "advanced", "recalled", "discarded"]):
                key_events.append(log)
        
        if key_events:
            prompt_parts.append("KEY BATTLE EVENTS:")
            for event in key_events:
                prompt_parts.append(f"  - {event}")
            prompt_parts.append("")
        
        # Now add varied prompting styles
        if True:  # Always use varied styles now
            # Randomly choose a prompt style to encourage variety
            prompt_styles = [
                # Strategic analysis
                lambda: prompt_parts + [
                    "Analyze this round from The Champion's perspective. Reference specific spells and outcomes."
                ],
                
                # Salty about specific plays
                lambda: prompt_parts + [
                    "You're salty about how this round went. Complain about specific spells and RNG."
                ],
                
                # Sports commentator
                lambda: prompt_parts + [
                    "COMMENTATE THIS ROUND LIKE IT'S THE WORLD FINALS! Name specific spells and damage!"
                ],
                
                # Boastful champion
                lambda: prompt_parts + [
                    "Boast about your brilliant plays this round. Mock their choices. Be specific!"
                ],
                
                # Technical breakdown
                lambda: prompt_parts + [
                    "Give a technical breakdown of the spell interactions this round."
                ],
                
                # Trash talk
                lambda: prompt_parts + [
                    "Trash talk based on what actually happened. Reference their spells by name!"
                ],
                
                # Excuses with details
                lambda: prompt_parts + [
                    "Make excuses for why specific spells didn't work out as planned."
                ]
            ]
            
            # Pick a random style
            style_names = ["Strategic analysis", "Salty", "Commentator", "Boastful", "Technical", "Trash talk", "Excuses"]
            chosen_index = random.randint(0, len(prompt_styles) - 1)
            chosen_style = prompt_styles[chosen_index]
            prompt_parts = chosen_style()
            
            # Add debug info about which style was chosen
            debug_msg = f"[DEBUG: Using {style_names[chosen_index]} style]"
            prompt_parts.insert(0, debug_msg)
            
            # Also log it
            print(f"\n{Colors.YELLOW}>>> {debug_msg}{Colors.ENDC}")  # Direct print
            # Write to debug file in logs directory
            import os
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug_logs')
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, 'claude_debug.txt')
            with open(debug_file, 'a') as f:
                f.write(f"\n{debug_msg}\n")
                f.write(f"Full prompt:\n{chr(10).join(prompt_parts[:10])}...\n")
            if hasattr(self, 'engine') and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(f"\\033[90m{debug_msg}\\033[0m")
        
        # For round analysis, skip JSON and just get raw response
        return "\n".join(prompt_parts)
    
    def _build_game_end_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for game end commentary"""
        import random
        
        winner = context['winner']
        i_won = winner == context['player_name']
        
        if i_won:
            # Victory prompts
            prompts = [
                f"YOU WON! {winner} is victorious with {context['winner_health']} HP and {context['winner_trunks']} trunks! Give us your victory speech!",
                f"CHAMPION VICTORIOUS! Final score: {winner} wins in {context['total_rounds']} rounds. Gloat time!",
                f"Game over. You won. Drop the mic.",
                f"{winner} WINS! Your moment of glory has arrived. Make it memorable."
            ]
        else:
            # Defeat prompts (but Champion never admits defeat)
            prompts = [
                f"{winner} won? IMPOSSIBLE! The game must be broken. Explain this travesty!",
                f"Game ended. {winner} claims victory. You have thoughts about this 'victory'...",
                f"{winner} destroyed your last trunk. React to this... situation.",
                f"Final score: {winner} wins. The Champion demands a recount!"
            ]
        
        chosen_prompt = random.choice(prompts)
        
        return f"""{chosen_prompt}

Final stats:
{chr(10).join(f"- {name}: {health}/{max_health} HP, {trunks} trunks" for name, health, max_health, trunks in context['all_players'])}

Total rounds: {context['total_rounds']}

JSON required:
{{"final_words": "<your final message>"}}"""
    
    def _parse_text_response(self, content: str, decision_type: str) -> Optional[Dict[str, Any]]:
        """Parse non-JSON text responses as fallback"""
        # Try to extract numbers from the response
        import re
        numbers = re.findall(r'\d+', content)
        
        if decision_type == "select_card" and numbers:
            return {
                "card_index": int(numbers[0]),
                "reasoning": "The Champion knows best!",
                "message": "Too easy! Another flawless play by The Champion!"
            }
        elif decision_type == "make_choice" and numbers:
            return {
                "choice_index": int(numbers[0]),
                "message": "Obviously the optimal choice!"
            }
        elif decision_type == "draft" and numbers:
            return {
                "set_index": int(numbers[0]),
                "message": "The Champion chooses perfection, as always!"
            }
        elif decision_type == "round_analysis":
            # Don't use a fallback - return the actual content
            return {
                "analysis": content if content else "..."
            }
        elif decision_type == "game_end":
            return {
                "final_words": "The Champion's legacy continues!"
            }
        
        return None
    
    def _build_spell_database(self):
        """Build a database of all spells with their properties (from ExpertAI)"""
        spell_db = {}
        
        try:
            spells_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spells.json')
            if os.path.exists(spells_file):
                with open(spells_file, 'r') as f:
                    spell_data = json.load(f)
                    
                for spell in spell_data:
                    spell_name = spell.get('card_name')
                    if spell_name:
                        spell_db[spell_name] = {
                            'element': spell.get('element'),
                            'priority': spell.get('priority'),
                            'types': spell.get('spell_types', []),
                            'is_conjury': spell.get('is_conjury', False),
                            'damage': self._extract_spell_damage(spell),
                            'healing': self._extract_spell_healing(spell),
                            'effects': self._extract_spell_effects(spell)
                        }
        except Exception:
            pass
        
        return spell_db
    
    def _extract_spell_damage(self, spell_data):
        """Extract damage values from spell data"""
        total_damage = 0
        
        for effect in spell_data.get('resolve_effects', []):
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'damage':
                total_damage += action.get('parameters', {}).get('value', 0)
        
        return total_damage
    
    def _extract_spell_healing(self, spell_data):
        """Extract healing values from spell data"""
        total_healing = 0
        
        for effect in spell_data.get('resolve_effects', []):
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'heal':
                total_healing += action.get('parameters', {}).get('value', 0)
        
        return total_healing
    
    def _extract_spell_effects(self, spell_data):
        """Extract effect types from spell data"""
        effects = []
        
        for effect in spell_data.get('resolve_effects', []):
            action = effect.get('action', {})
            if isinstance(action, dict):
                effects.append(action.get('type'))
        
        return effects
    
    def choose_draft_set(self, player, gs, available_sets):
        """Track opponent elements during draft and pass to LLM"""
        # Update element tracking for all players
        self._update_element_tracking(gs)
        
        # Call parent method which will use LLM
        return super().choose_draft_set(player, gs, available_sets)
    
    def _update_element_tracking(self, gs):
        """Track what elements each player has drafted"""
        for player in gs.players:
            if player.name not in self._element_tracking:
                self._element_tracking[player.name] = set()
            
            # Check their board and hand for elements
            for clash_list in player.board:
                for spell in clash_list:
                    if spell.status == 'revealed':
                        self._element_tracking[player.name].add(spell.card.element)
            
            for card in player.hand:
                self._element_tracking[player.name].add(card.element)
    
    def get_opponent_elements(self, opponent_name):
        """Get tracked elements for an opponent"""
        return list(self._element_tracking.get(opponent_name, set()))
    
    def get_remaining_spells(self, opponent_name):
        """Estimate remaining spells for opponent based on what they've played"""
        if opponent_name not in self._element_tracking:
            return []
        
        opponent_elements = self._element_tracking[opponent_name]
        remaining = []
        
        # For each element they've drafted, add spells they might have
        for element in opponent_elements:
            element_spells = [name for name, data in self.spell_database.items() 
                            if data.get('element') == element]
            remaining.extend(element_spells)
        
        return remaining