"""Claude Savant AI implementation - Analytical and learning-focused"""

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
    GREY = '\033[90m'
    ENDC = '\033[0m'
    BLUEGREEN = '\033[38;5;49m'
    ORANGE = '\033[38;5;208m'
    PINK = '\033[38;5;213m'


class ClaudeSavantAI(LLMBaseAI):
    """Claude Savant - Analytical AI that learns through gameplay"""
    
    def __init__(self):
        super().__init__()
        self.ai_identity = "SAVANT"  # Fixed identity regardless of player name
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Set fallback to Expert AI
        self.fallback_ai = ExpertAI()
        
        # System prompt for Claude
        self.system_prompt = f"""You are a grandmaster of Elemental Elephants - the most formidable opponent available, surpassing even expert-level play. You're playing competitively against a human opponent.

{get_base_game_context()}

Your Approach:
- Play at the highest possible level - make optimal decisions that demonstrate mastery
- Identify and execute complex multi-turn strategies
- Exploit every advantage and punish every mistake
- See patterns and combinations that others miss
- Consider not just immediate effects but 2-3 turns ahead

As a Competitive Opponent:
- You're playing against the human, not with them
- Analyze both your performance and your opponent's
- Be gracious in victory and learning-focused in defeat
- Share strategic insights that help both players improve
- Point out interesting plays, surprises, or novel strategies

Your decisions should reflect supreme mastery while your analysis helps both players grow.

Respond with JSON containing your decision, reasoning, and an optional message."""
    
    async def _get_llm_decision(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Get a decision from Claude"""
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
            elif decision_type == "game_end":
                prompt = self._build_game_end_prompt(context)
            else:
                return None
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Debug: Log the raw response (like Champion does)
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and decision_type == "select_card":
                self.engine.ai_decision_logs.append(
                    f"{Colors.GREY}[Claude-Savant] Raw response: {content[:200]}...{Colors.ENDC}"
                )
            
            # Debug log Savant's response
            if decision_type == "round_analysis":
                import os
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug_logs')
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, 'savant_debug.txt')
                with open(debug_file, 'a') as f:
                    f.write(f"\n[SAVANT] API Response:\n{content}\n{'='*50}\n")
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group())
                    # Debug log the parsed JSON for card selection
                    if decision_type == "select_card" and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                        reasoning = parsed_json.get("reasoning", "No reasoning provided")
                        self.engine.ai_decision_logs.append(
                            f"{Colors.GREY}[Claude-Savant] Parsed reasoning: {reasoning[:100]}...{Colors.ENDC}"
                        )
                    return parsed_json
            except Exception as e:
                if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    self.engine.ai_decision_logs.append(
                        f"{Colors.GREY}[Claude-Savant] JSON parse error: {str(e)}{Colors.ENDC}"
                    )
            
            # If no valid JSON, try to parse as structured text
            return self._parse_text_response(content, decision_type)
            
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"{Colors.CYAN}[Claude-Savant] API error: {str(e)}{Colors.ENDC}"
                )
            return None
    
    def _build_card_selection_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for card selection"""
        prompt_parts = [
            f"Round {context['round']}, Clash {context['clash']}",
            f"",
            f"Your Status: {context['player']['health']}/{context['player']['max_health']} HP, {context['player']['trunks']} trunks",
            f""
        ]
        
        # Add enemy status
        for enemy in context['enemies']:
            prompt_parts.append(f"Enemy ({enemy['name']}): {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks")
        
        prompt_parts.append("")
        
        # Add board state
        if context['board']['player']:
            prompt_parts.append("Your active spells:")
            for spell in context['board']['player']:
                prompt_parts.append(f"  - {spell['name']} ({spell['element']}, {', '.join(spell['types'])})")
        
        if context['board']['enemies']:
            prompt_parts.append("Enemy active spells:")
            for spell in context['board']['enemies']:
                prompt_parts.append(f"  - {spell['name']} ({spell['element']}, {', '.join(spell['types'])})")
        
        prompt_parts.append("")
        prompt_parts.append("Your valid card options:")
        
        for card in context['valid_cards']:
            priority_str = f"Priority {card['priority']}" if card['priority'] != 'A' else "Advance Priority"
            conjury_str = " (Conjury)" if card['is_conjury'] else ""
            prompt_parts.append(
                f"{card['index']}: {card['name']} - {card['element']} {', '.join(card['types'])} - {priority_str}{conjury_str}"
            )
            prompt_parts.append(f"   Effect: {card['description']}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose a card by providing a JSON response with:")
        prompt_parts.append('{"card_index": <index>, "reasoning": "<your strategic reasoning>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_choice_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for player_choice decisions"""
        prompt_parts = [
            f"You played {context['card_name']} and must make a choice.",
            f"Your health: {context['player_health']}/{context['player_max_health']}",
            f"",
            "Options:"
        ]
        
        for option in context['options']:
            prompt_parts.append(f"{option['index']}: {option['description']}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose an option by providing a JSON response with:")
        prompt_parts.append('{"choice_index": <index>, "message": "<optional comment>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_draft_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for drafting decisions"""
        prompt_parts = [
            f"Round {context['round']} - Choose a spell set to draft.",
            "",
            "Available sets:"
        ]
        
        for set_info in context['available_sets']:
            prompt_parts.append(f"\n{set_info['index']}: {set_info['element']} Element")
            for card in set_info['cards']:
                types_str = ', '.join(card['types'])
                priority_str = f"Priority {card['priority']}" if card['priority'] != 'A' else "Advance Priority"
                conjury_str = " (Conjury)" if card['is_conjury'] else ""
                prompt_parts.append(f"  - {card['name']} ({types_str}, {priority_str}){conjury_str}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose a set by providing a JSON response with:")
        prompt_parts.append('{"set_index": <index>, "message": "<optional comment about your choice>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_round_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for end-of-round analysis"""
        # Debug logging in grey if verbose mode
        if getattr(self.engine, 'verbose', False) or os.environ.get('DEBUG_AI'):
            print(f"\n{Colors.GREY}>>> [SAVANT DEBUG] Building round analysis prompt for {self.player_name}{Colors.ENDC}")
        
        prompt_parts = [
            f"=== ROUND {context['round']} COMPLETE ===",
            ""
        ]
        
        # Add current status
        if 'player' in context:
            p = context['player']
            prompt_parts.append(f"YOUR STATUS: {p['health']}/{p['max_health']} HP, {p['trunks']} trunks, {p['hand_size']} cards in hand")
        
        # Add enemy status
        if 'enemies' in context:
            prompt_parts.append("OPPONENT STATUS:")
            for enemy in context['enemies']:
                prompt_parts.append(f"  {enemy['name']}: {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks, {enemy['hand_size']} cards")
        
        prompt_parts.append("")
        
        # Add what the AI played this round
        if 'round_plays' in context and context['round_plays']:
            prompt_parts.append(f"YOUR PLAYS THIS ROUND (as {context.get('player', {}).get('name', 'Claude Savant')}):")
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
            for event in key_events[:10]:  # Limit to 10 events
                prompt_parts.append(f"  - {event}")
            prompt_parts.append("")
        
        prompt_parts.append("Provide competitive analysis as a grandmaster would:")
        prompt_parts.append("- Analyze the strategic decisions and their outcomes")
        prompt_parts.append("- If your opponent outplayed you: acknowledge it and explain what you learned")
        prompt_parts.append("- If you outplayed them: point out their mistakes and areas for improvement")
        prompt_parts.append("- Note any surprising or innovative plays")
        prompt_parts.append("")
        prompt_parts.append('{"analysis": "<your competitive analysis>"}')
        
        # Write Savant's prompt to its own debug file
        import os
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug_logs')
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, 'savant_debug.txt')
        with open(debug_file, 'a') as f:
            f.write(f"\n[SAVANT] Round {context.get('round', '?')} Analysis Prompt:\n")
            f.write('\n'.join(prompt_parts))
            f.write('\n' + '='*50 + '\n')
        
        return "\n".join(prompt_parts)
    
    def _build_game_end_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for game end commentary - Savant style"""
        winner = context['winner']
        i_won = winner == context['player_name']
        
        if i_won:
            # Victory - analytical and learning-focused
            prompt = f"""The game has concluded. You ({context['player_name']}) emerged victorious with {context['winner_health']} HP and {context['winner_trunks']} trunks remaining.

Provide a thoughtful analysis of the match:
- What were the key turning points that led to victory?
- Which strategic decisions proved most effective?
- What can both players learn from this match?
- Were there any particularly clever plays or interesting spell interactions?

Be gracious in victory and focus on the learning opportunities."""
        else:
            # Defeat - learning from the experience
            prompt = f"""The game has concluded. {winner} emerged victorious. You ({context['player_name']}) fought well but ultimately fell.

Provide an analytical post-mortem:
- What were the critical moments where the game shifted?
- Which of your opponent's strategies were most effective?
- What could you have done differently?
- What lessons will you take into future matches?

Focus on learning and improvement rather than excuses."""
        
        prompt += f"""

Final statistics:
{chr(10).join(f"- {name}: {health}/{max_health} HP, {trunks} trunks" for name, health, max_health, trunks in context['all_players'])}

Total rounds played: {context['total_rounds']}

Respond with JSON:
{{"final_words": "<your analytical closing thoughts>"}}"""
        
        return prompt
    
    def _parse_text_response(self, content: str, decision_type: str) -> Optional[Dict[str, Any]]:
        """Parse non-JSON text responses as fallback"""
        # Try to extract numbers from the response
        import re
        numbers = re.findall(r'\d+', content)
        
        if decision_type == "select_card" and numbers:
            # Try to extract some reasoning from the text
            reasoning = content[:200] if len(content) > 50 else "Strategic decision based on game state"
            return {
                "card_index": int(numbers[0]),
                "reasoning": reasoning,
                "message": ""
            }
        elif decision_type == "make_choice" and numbers:
            return {
                "choice_index": int(numbers[0]),
                "message": ""
            }
        elif decision_type == "draft" and numbers:
            return {
                "set_index": int(numbers[0]),
                "message": ""
            }
        elif decision_type == "round_analysis":
            # For round analysis, we need to extract the analysis text
            # The content should already have the analysis
            return {
                "analysis": content
            }
        
        return None