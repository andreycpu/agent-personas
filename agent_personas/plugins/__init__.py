"""
Plugin System Module

Extensible plugin architecture for adding custom functionality
to the persona framework.
"""

from .plugin_manager import PluginManager, Plugin
from .plugin_loader import PluginLoader, PluginConfig
from .hooks import HookManager, Hook, HookPriority
from .registry import PluginRegistry

__all__ = [
    "PluginManager",
    "Plugin",
    "PluginLoader", 
    "PluginConfig",
    "HookManager",
    "Hook",
    "HookPriority",
    "PluginRegistry"
]