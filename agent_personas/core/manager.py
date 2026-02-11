"""
Persona manager for orchestrating persona operations.
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import logging

from .persona import Persona
from .registry import PersonaRegistry


class PersonaManager:
    """
    High-level manager for persona operations including activation and switching.
    """
    
    def __init__(
        self,
        registry: Optional[PersonaRegistry] = None,
        default_persona: Optional[str] = None
    ):
        """
        Initialize the persona manager.
        
        Args:
            registry: PersonaRegistry instance (creates new if None)
            default_persona: Name of default persona to activate
        """
        self.registry = registry or PersonaRegistry()
        self._active_persona: Optional[Persona] = None
        self._persona_history: List[str] = []
        self._switch_callbacks: List[Callable[[Optional[Persona], Optional[Persona]], None]] = []
        
        self.logger = logging.getLogger(__name__)
        
        if default_persona and self.registry.exists(default_persona):
            self.activate_persona(default_persona)
            
    @property
    def active_persona(self) -> Optional[Persona]:
        """Get the currently active persona."""
        return self._active_persona
        
    @property
    def active_persona_name(self) -> Optional[str]:
        """Get the name of the currently active persona."""
        return self._active_persona.name if self._active_persona else None
        
    def register_persona(self, persona: Persona) -> None:
        """Register a new persona."""
        self.registry.register(persona)
        self.logger.info(f"Registered persona: {persona.name}")
        
    def create_persona(
        self,
        name: str,
        description: str = "",
        traits: Optional[Dict[str, float]] = None,
        conversation_style: str = "neutral",
        emotional_baseline: str = "calm",
        metadata: Optional[Dict[str, Any]] = None,
        activate: bool = False
    ) -> Persona:
        """
        Create and register a new persona.
        
        Args:
            name: Persona name
            description: Persona description
            traits: Trait dictionary
            conversation_style: Conversation style
            emotional_baseline: Emotional baseline
            metadata: Additional metadata
            activate: Whether to activate the persona after creation
            
        Returns:
            Created persona instance
        """
        persona = Persona(
            name=name,
            description=description,
            traits=traits,
            conversation_style=conversation_style,
            emotional_baseline=emotional_baseline,
            metadata=metadata
        )
        
        self.register_persona(persona)
        
        if activate:
            self.activate_persona(name)
            
        return persona
        
    def activate_persona(self, name: str) -> bool:
        """
        Activate a persona by name.
        
        Args:
            name: Name of persona to activate
            
        Returns:
            True if successfully activated, False otherwise
        """
        if not self.registry.exists(name):
            self.logger.warning(f"Persona '{name}' not found")
            return False
            
        previous_persona = self._active_persona
        self._active_persona = self.registry.get(name)
        
        if previous_persona:
            self._persona_history.append(previous_persona.name)
            
        self.logger.info(f"Activated persona: {name}")
        
        # Notify callbacks
        for callback in self._switch_callbacks:
            callback(previous_persona, self._active_persona)
            
        return True
        
    def deactivate_persona(self) -> Optional[Persona]:
        """Deactivate the current persona."""
        if not self._active_persona:
            return None
            
        previous_persona = self._active_persona
        self._active_persona = None
        
        self.logger.info(f"Deactivated persona: {previous_persona.name}")
        
        # Notify callbacks
        for callback in self._switch_callbacks:
            callback(previous_persona, None)
            
        return previous_persona
        
    def switch_persona(self, name: str) -> bool:
        """Switch to a different persona."""
        return self.activate_persona(name)
        
    def revert_persona(self) -> bool:
        """Revert to the previous persona in history."""
        if not self._persona_history:
            return False
            
        previous_name = self._persona_history.pop()
        return self.activate_persona(previous_name)
        
    def add_switch_callback(
        self, 
        callback: Callable[[Optional[Persona], Optional[Persona]], None]
    ) -> None:
        """Add a callback to be called when personas are switched."""
        self._switch_callbacks.append(callback)
        
    def remove_switch_callback(
        self, 
        callback: Callable[[Optional[Persona], Optional[Persona]], None]
    ) -> None:
        """Remove a switch callback."""
        if callback in self._switch_callbacks:
            self._switch_callbacks.remove(callback)
            
    def get_persona_history(self) -> List[str]:
        """Get the history of activated personas."""
        return self._persona_history.copy()
        
    def clear_history(self) -> None:
        """Clear the persona activation history."""
        self._persona_history.clear()
        
    def list_personas(self) -> List[str]:
        """List all available persona names."""
        return self.registry.list_names()
        
    def search_personas(self, query: str) -> List[Persona]:
        """Search for personas by query."""
        return self.registry.search(query)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current manager status."""
        return {
            "active_persona": self.active_persona_name,
            "total_personas": self.registry.size(),
            "history_length": len(self._persona_history),
            "callbacks_registered": len(self._switch_callbacks)
        }