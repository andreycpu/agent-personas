"""
Persona registry for managing collections of personas.
"""

from typing import Dict, List, Optional, Iterator
import json
import os
from pathlib import Path

from .persona import Persona


class PersonaRegistry:
    """
    Registry for managing multiple personas with persistence support.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the persona registry.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self._personas: Dict[str, Persona] = {}
        self.storage_path = storage_path
        
        if storage_path and os.path.exists(storage_path):
            self.load_from_file(storage_path)
            
    def register(self, persona: Persona) -> None:
        """Register a persona in the registry."""
        if persona.name in self._personas:
            raise ValueError(f"Persona '{persona.name}' already exists")
        self._personas[persona.name] = persona
        
    def unregister(self, name: str) -> Optional[Persona]:
        """Remove a persona from the registry."""
        return self._personas.pop(name, None)
        
    def get(self, name: str) -> Optional[Persona]:
        """Get a persona by name."""
        return self._personas.get(name)
        
    def exists(self, name: str) -> bool:
        """Check if a persona exists."""
        return name in self._personas
        
    def list_names(self) -> List[str]:
        """Get list of all persona names."""
        return list(self._personas.keys())
        
    def list_personas(self) -> List[Persona]:
        """Get list of all personas."""
        return list(self._personas.values())
        
    def search(self, query: str) -> List[Persona]:
        """Search personas by name or description."""
        query = query.lower()
        results = []
        
        for persona in self._personas.values():
            if (query in persona.name.lower() or 
                query in persona.description.lower()):
                results.append(persona)
                
        return results
        
    def filter_by_trait(self, trait_name: str, min_strength: float = 0.5) -> List[Persona]:
        """Filter personas by trait strength."""
        return [
            persona for persona in self._personas.values()
            if persona.get_trait(trait_name) >= min_strength
        ]
        
    def clear(self) -> None:
        """Remove all personas from registry."""
        self._personas.clear()
        
    def size(self) -> int:
        """Get number of personas in registry."""
        return len(self._personas)
        
    def save_to_file(self, filepath: str) -> None:
        """Save all personas to JSON file."""
        data = {
            "personas": [persona.to_dict() for persona in self._personas.values()]
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_from_file(self, filepath: str) -> None:
        """Load personas from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        self._personas.clear()
        for persona_data in data.get("personas", []):
            persona = Persona.from_dict(persona_data)
            self._personas[persona.name] = persona
            
    def __iter__(self) -> Iterator[Persona]:
        """Iterate over all personas."""
        return iter(self._personas.values())
        
    def __contains__(self, name: str) -> bool:
        """Check if persona exists using 'in' operator."""
        return name in self._personas
        
    def __len__(self) -> int:
        """Get number of personas."""
        return len(self._personas)