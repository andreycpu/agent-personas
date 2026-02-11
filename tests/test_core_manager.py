"""
Unit tests for the PersonaManager class.
"""

import pytest
from agent_personas.core.persona import Persona
from agent_personas.core.manager import PersonaManager
from agent_personas.core.registry import PersonaRegistry


class TestPersonaManager:
    """Test cases for the PersonaManager class."""
    
    def test_manager_creation(self):
        """Test basic manager creation."""
        manager = PersonaManager()
        
        assert manager.registry is not None
        assert manager.active_persona is None
        assert manager.active_persona_name is None
        assert isinstance(manager.get_persona_history(), list)
    
    def test_manager_with_custom_registry(self):
        """Test manager creation with custom registry."""
        registry = PersonaRegistry()
        manager = PersonaManager(registry=registry)
        
        assert manager.registry is registry
    
    def test_register_persona(self):
        """Test persona registration."""
        manager = PersonaManager()
        persona = Persona(name="TestPersona", traits={"helpfulness": 0.8})
        
        manager.register_persona(persona)
        
        assert "TestPersona" in manager.list_personas()
        assert manager.registry.exists("TestPersona")
    
    def test_create_persona(self):
        """Test persona creation through manager."""
        manager = PersonaManager()
        
        persona = manager.create_persona(
            name="CreatedPersona",
            description="A dynamically created persona",
            traits={"confidence": 0.7, "empathy": 0.8},
            conversation_style="friendly",
            activate=False
        )
        
        assert persona.name == "CreatedPersona"
        assert persona.description == "A dynamically created persona"
        assert persona.traits["confidence"] == 0.7
        assert "CreatedPersona" in manager.list_personas()
        assert manager.active_persona_name != "CreatedPersona"  # Not activated
    
    def test_create_and_activate_persona(self):
        """Test persona creation with immediate activation."""
        manager = PersonaManager()
        
        persona = manager.create_persona(
            name="ActivePersona",
            description="An immediately activated persona",
            activate=True
        )
        
        assert persona.name == "ActivePersona"
        assert manager.active_persona_name == "ActivePersona"
        assert manager.active_persona is persona
    
    def test_activate_persona(self):
        """Test persona activation."""
        manager = PersonaManager()
        persona = Persona(name="TestPersona")
        manager.register_persona(persona)
        
        success = manager.activate_persona("TestPersona")
        
        assert success is True
        assert manager.active_persona_name == "TestPersona"
        assert manager.active_persona is persona
    
    def test_activate_nonexistent_persona(self):
        """Test activation of nonexistent persona."""
        manager = PersonaManager()
        
        success = manager.activate_persona("NonexistentPersona")
        
        assert success is False
        assert manager.active_persona is None
        assert manager.active_persona_name is None
    
    def test_deactivate_persona(self):
        """Test persona deactivation."""
        manager = PersonaManager()
        persona = Persona(name="TestPersona")
        manager.register_persona(persona)
        manager.activate_persona("TestPersona")
        
        previous_persona = manager.deactivate_persona()
        
        assert previous_persona is persona
        assert manager.active_persona is None
        assert manager.active_persona_name is None
    
    def test_deactivate_when_no_active_persona(self):
        """Test deactivation when no persona is active."""
        manager = PersonaManager()
        
        previous_persona = manager.deactivate_persona()
        
        assert previous_persona is None
    
    def test_switch_persona(self):
        """Test persona switching."""
        manager = PersonaManager()
        
        persona1 = Persona(name="Persona1")
        persona2 = Persona(name="Persona2")
        
        manager.register_persona(persona1)
        manager.register_persona(persona2)
        
        # Activate first persona
        manager.activate_persona("Persona1")
        assert manager.active_persona_name == "Persona1"
        
        # Switch to second persona
        success = manager.switch_persona("Persona2")
        
        assert success is True
        assert manager.active_persona_name == "Persona2"
        assert manager.active_persona is persona2
    
    def test_revert_persona(self):
        """Test reverting to previous persona."""
        manager = PersonaManager()
        
        persona1 = Persona(name="Persona1")
        persona2 = Persona(name="Persona2")
        
        manager.register_persona(persona1)
        manager.register_persona(persona2)
        
        # Activate first, then switch to second
        manager.activate_persona("Persona1")
        manager.switch_persona("Persona2")
        
        # Revert to first
        success = manager.revert_persona()
        
        assert success is True
        assert manager.active_persona_name == "Persona1"
    
    def test_revert_with_no_history(self):
        """Test reverting when there's no history."""
        manager = PersonaManager()
        
        success = manager.revert_persona()
        
        assert success is False
    
    def test_switch_callbacks(self):
        """Test persona switch callbacks."""
        manager = PersonaManager()
        callback_calls = []
        
        def test_callback(previous, current):
            callback_calls.append((
                previous.name if previous else None,
                current.name if current else None
            ))
        
        manager.add_switch_callback(test_callback)
        
        persona1 = Persona(name="Persona1")
        persona2 = Persona(name="Persona2")
        
        manager.register_persona(persona1)
        manager.register_persona(persona2)
        
        # Test activation callback
        manager.activate_persona("Persona1")
        assert len(callback_calls) == 1
        assert callback_calls[0] == (None, "Persona1")
        
        # Test switch callback
        manager.switch_persona("Persona2")
        assert len(callback_calls) == 2
        assert callback_calls[1] == ("Persona1", "Persona2")
        
        # Test deactivation callback
        manager.deactivate_persona()
        assert len(callback_calls) == 3
        assert callback_calls[2] == ("Persona2", None)
    
    def test_remove_switch_callback(self):
        """Test removing switch callbacks."""
        manager = PersonaManager()
        callback_calls = []
        
        def test_callback(previous, current):
            callback_calls.append("called")
        
        manager.add_switch_callback(test_callback)
        manager.remove_switch_callback(test_callback)
        
        persona = Persona(name="TestPersona")
        manager.register_persona(persona)
        manager.activate_persona("TestPersona")
        
        assert len(callback_calls) == 0  # Callback was removed
    
    def test_persona_history_tracking(self):
        """Test persona history tracking."""
        manager = PersonaManager()
        
        persona1 = Persona(name="Persona1")
        persona2 = Persona(name="Persona2")
        persona3 = Persona(name="Persona3")
        
        for persona in [persona1, persona2, persona3]:
            manager.register_persona(persona)
        
        # Make some switches
        manager.activate_persona("Persona1")
        manager.switch_persona("Persona2")
        manager.switch_persona("Persona3")
        
        history = manager.get_persona_history()
        
        assert len(history) == 2  # Two previous personas
        assert history == ["Persona1", "Persona2"]
    
    def test_clear_history(self):
        """Test clearing persona history."""
        manager = PersonaManager()
        
        persona1 = Persona(name="Persona1")
        persona2 = Persona(name="Persona2")
        
        manager.register_persona(persona1)
        manager.register_persona(persona2)
        
        manager.activate_persona("Persona1")
        manager.switch_persona("Persona2")
        
        assert len(manager.get_persona_history()) > 0
        
        manager.clear_history()
        
        assert len(manager.get_persona_history()) == 0
    
    def test_search_personas(self):
        """Test persona search functionality."""
        manager = PersonaManager()
        
        persona1 = Persona(name="HelpfulAssistant", description="A helpful AI assistant")
        persona2 = Persona(name="TechnicalExpert", description="A technical specialist")
        persona3 = Persona(name="CreativeWriter", description="A creative writing assistant")
        
        for persona in [persona1, persona2, persona3]:
            manager.register_persona(persona)
        
        # Search by name
        results = manager.search_personas("helpful")
        assert len(results) == 1
        assert results[0].name == "HelpfulAssistant"
        
        # Search by description
        results = manager.search_personas("technical")
        assert len(results) == 1
        assert results[0].name == "TechnicalExpert"
        
        # Search for assistant
        results = manager.search_personas("assistant")
        assert len(results) == 2  # Both HelpfulAssistant and CreativeWriter
    
    def test_get_status(self):
        """Test manager status reporting."""
        manager = PersonaManager()
        
        persona1 = Persona(name="Persona1")
        persona2 = Persona(name="Persona2")
        
        manager.register_persona(persona1)
        manager.register_persona(persona2)
        manager.activate_persona("Persona1")
        
        status = manager.get_status()
        
        assert status["active_persona"] == "Persona1"
        assert status["total_personas"] == 2
        assert status["history_length"] == 0  # No switches yet
        assert "callbacks_registered" in status
    
    def test_list_personas(self):
        """Test listing persona names."""
        manager = PersonaManager()
        
        persona1 = Persona(name="Alpha")
        persona2 = Persona(name="Beta") 
        persona3 = Persona(name="Gamma")
        
        for persona in [persona1, persona2, persona3]:
            manager.register_persona(persona)
        
        persona_names = manager.list_personas()
        
        assert len(persona_names) == 3
        assert "Alpha" in persona_names
        assert "Beta" in persona_names
        assert "Gamma" in persona_names
    
    def test_manager_with_default_persona(self):
        """Test manager initialization with default persona."""
        registry = PersonaRegistry()
        persona = Persona(name="DefaultPersona")
        registry.register(persona)
        
        manager = PersonaManager(registry=registry, default_persona="DefaultPersona")
        
        assert manager.active_persona_name == "DefaultPersona"
        assert manager.active_persona is persona
    
    def test_manager_with_invalid_default_persona(self):
        """Test manager initialization with invalid default persona."""
        registry = PersonaRegistry()
        
        manager = PersonaManager(registry=registry, default_persona="NonexistentPersona")
        
        assert manager.active_persona is None  # Should not activate invalid persona