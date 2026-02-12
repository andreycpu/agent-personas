"""
Memory-Persona Integration Module

Advanced integration between persona characteristics and memory systems,
enabling personas to influence memory formation, retrieval, and emotional associations.
"""

from .persona_memory import PersonaMemory, MemoryType, MemoryImportance
from .memory_influenced_persona import MemoryInfluencedPersona
from .episodic_memory import EpisodicMemory, Episode
from .semantic_memory import SemanticMemory, ConceptualMemory
from .memory_consolidation import MemoryConsolidator, ConsolidationStrategy

__all__ = [
    "PersonaMemory",
    "MemoryType", 
    "MemoryImportance",
    "MemoryInfluencedPersona",
    "EpisodicMemory",
    "Episode",
    "SemanticMemory",
    "ConceptualMemory",
    "MemoryConsolidator",
    "ConsolidationStrategy"
]