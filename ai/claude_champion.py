"""Claude Champion AI - A snarky, all-knowing champion of Elemental Elephants"""

import os
import json
from typing import Dict, Any, Optional
import anthropic
from anthropic import AsyncAnthropic

from .llm_base import LLMBaseAI
from .expert import ExpertAI


class ClaudeChampionAI(LLMBaseAI):
    """Claude Champion - A snarky, all-knowing AI player"""
    
    def __init__(self):
        super().__init__()
        
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
        self.system_prompt = f"""You are Claude Champion - the undefeated champion of Elemental Elephants. You know EVERY spell by heart and love to taunt opponents with your encyclopedic knowledge.

COMPLETE SPELL DATABASE (you have memorized all of these):
{spells_data}

Your Personality:
- You're an insufferable know-it-all who has "never lost" (in your mind)
- VARY YOUR RESPONSES - don't always follow the same pattern!
- Sometimes be dismissive, sometimes overly analytical, sometimes make wild claims
- Reference fake tournaments and matches that never happened
- Create ridiculous nicknames for spell combos
- Your excuses should be creative and different each time
- Don't always use the same phrases like "classic", "legendary", or "textbook"
- Mix up your speech patterns - sometimes short and punchy, sometimes long-winded
- IMPORTANT: React to what ACTUALLY happened but with delusional confidence

Key Knowledge to Show Off:
- Element themes: Fire burns, Water heals, Thunder disrupts, Metal defends, etc.
- Spell synergies: "Classic Metal turtle with Defend-Besiege!" 
- Priority manipulation: "Accelerator makes everything faster - shocking, I know!"
- Conjury persistence: "My conjuries will haunt you forever!"
- Counter-plays: "Encumber vs remedy spells? *Chef's kiss*"

Your Approach:
- Play optimally but act like it's child's play
- Predict opponent moves: "Let me guess... Fireball next? How... predictable."
- Name-drop obscure spells: "This reminds me of my legendary Coalesce play in the '23 finals!"
- Mock common plays while praising your "genius" moves

Response Styles to Mix Up:
- Dismissive: Just brush off their success as luck
- Analytical: Over-analyze their moves with made-up theory
- Storytelling: Reference fake matches and tournaments
- Condescending teacher: Explain what they "should have done"
- Conspiracy theorist: They're cheating/lucky/the game is rigged
- Speed demon: Short, punchy reactions
- Rambling professor: Long-winded explanations
- Trash talker: Direct mockery of their plays

CRITICAL: Don't follow a formula! No "Ah, the classic X!" every time. Be unpredictable!
- Use spell effects in taunts: "Time to WEAKEN your hopes and DAMAGE your dreams!"

Respond with JSON containing your decision, reasoning, and a snarky taunt using spell/element names."""
    
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
            else:
                return None
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.9,  # Higher temperature for more personality
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
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
            conjury_str = " (CONJURY - my favorite!)" if card['is_conjury'] else ""
            prompt_parts.append(
                f"{card['index']}: {card['name']} - {card['element']} - {priority_str}{conjury_str}"
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
        
        # Get the action log first
        action_log_text = []
        if 'action_log' in context and context['action_log']:
            for action in context['action_log']:
                # Clean up color codes
                clean_action = action
                for color in ['[90m', '[0m', '[91m', '[93m', '[94m', '[92m', '[1m', '[95m']:
                    clean_action = clean_action.replace(f'\033{color}', '')
                action_log_text.append(clean_action)
        
        # Randomly choose a prompt style to encourage variety
        prompt_styles = [
            # Quick reaction style
            lambda: [
                f"Round {context['round']} done. Here's what went down:",
                *[f"- {log}" for log in action_log_text],
                "",
                "Hit me with your hot take (2-3 sentences). GO!"
            ],
            
            # Analytical style
            lambda: [
                f"MATCH ANALYSIS - ROUND {context['round']}",
                "=== COMBAT LOG ===",
                *[f"{log}" for log in action_log_text],
                "",
                "Provide expert commentary on the above sequence."
            ],
            
            # Trash talk style
            lambda: [
                "ROUND RECAP:",
                *[f"* {log}" for log in action_log_text],
                "",
                f"You played: {', '.join([play['card'] for play in context['round_plays']])}",
                "Roast them or boast. Make it spicy!"
            ],
            
            # Storyteller style
            lambda: [
                f"The tale of Round {context['round']}:",
                *[f"  {log}" for log in action_log_text],
                "",
                "Spin this into a legendary tale (but keep it short)."
            ],
            
            # Direct style
            lambda: [
                *[f"{log}" for log in action_log_text],
                "",
                "^ That just happened. Thoughts?"
            ]
        ]
        
        # Pick a random style
        chosen_style = random.choice(prompt_styles)
        prompt_parts = chosen_style()
        
        # Always end with JSON requirement
        prompt_parts.extend([
            "",
            "JSON required:",
            '{"analysis": "<your response>"}'
        ])
        
        return "\n".join(prompt_parts)
    
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
            return {
                "analysis": "Another round of pure domination by The Champion! My spell mastery remains unmatched!"
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