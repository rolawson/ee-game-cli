"""AI module for Elemental Elephants"""

from .base import BaseAI
from .easy import EasyAI
from .medium import MediumAI
from .hard import HardAI
from .expert import ExpertAI
from .llm_base import LLMBaseAI
from .claude_savant import ClaudeSavantAI
from .claude_champion import ClaudeChampionAI
from .claude_daredevil import ClaudeDaredevilAI
from .claude_chevalier import ClaudeChevalierAI

__all__ = ['BaseAI', 'EasyAI', 'MediumAI', 'HardAI', 'ExpertAI', 'LLMBaseAI', 
           'ClaudeSavantAI', 'ClaudeChampionAI', 'ClaudeDaredevilAI', 'ClaudeChevalierAI']