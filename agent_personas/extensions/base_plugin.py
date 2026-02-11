"""
Base plugin interface for Agent Personas framework extensions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BasePlugin(ABC):
    """
    Base class for all Agent Personas plugins.
    """
    
    def __init__(self):
        self._enabled = False
        self._initialized = False
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Plugin information."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass
    
    def enable(self) -> None:
        """Enable the plugin."""
        if not self._initialized:
            raise RuntimeError("Plugin must be initialized before enabling")
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the plugin."""
        self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities provided by this plugin.
        
        Returns:
            List of capability names
        """
        return []
    
    def get_hooks(self) -> Dict[str, str]:
        """
        Get dictionary of hook points this plugin implements.
        
        Returns:
            Dictionary mapping hook names to method names
        """
        return {}


class TraitPlugin(BasePlugin):
    """Base class for trait-related plugins."""
    
    def process_traits(self, traits: Dict[str, float], context: Dict[str, Any]) -> Dict[str, float]:
        """
        Process and potentially modify trait values.
        
        Args:
            traits: Original trait values
            context: Processing context
            
        Returns:
            Modified trait values
        """
        return traits


class BehaviorPlugin(BasePlugin):
    """Base class for behavior-related plugins."""
    
    def process_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and potentially modify behavior data.
        
        Args:
            behavior_data: Original behavior data
            context: Processing context
            
        Returns:
            Modified behavior data
        """
        return behavior_data


class ConversationPlugin(BasePlugin):
    """Base class for conversation-related plugins."""
    
    def process_conversation(
        self, 
        conversation_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and potentially modify conversation data.
        
        Args:
            conversation_data: Original conversation data
            context: Processing context
            
        Returns:
            Modified conversation data
        """
        return conversation_data


class EmotionPlugin(BasePlugin):
    """Base class for emotion-related plugins."""
    
    def process_emotions(
        self, 
        emotional_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and potentially modify emotional data.
        
        Args:
            emotional_data: Original emotional data
            context: Processing context
            
        Returns:
            Modified emotional data
        """
        return emotional_data