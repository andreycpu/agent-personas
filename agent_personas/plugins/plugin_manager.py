"""
Plugin management system for extensible functionality.
"""

from typing import Dict, Any, List, Optional, Type, Callable, Set
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import logging
import importlib
import inspect
from pathlib import Path
import sys

logger = logging.getLogger(__name__)


class PluginState(Enum):
    """Plugin states."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginType(Enum):
    """Types of plugins."""
    CORE = "core"
    EXTENSION = "extension"
    INTEGRATION = "integration"
    TEMPLATE = "template"
    ANALYZER = "analyzer"
    EXPORTER = "exporter"
    VALIDATOR = "validator"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    homepage: str = ""
    license: str = "MIT"
    min_framework_version: str = "0.1.0"
    max_framework_version: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "plugin_type": self.plugin_type.value,
            "dependencies": self.dependencies,
            "requirements": self.requirements,
            "tags": self.tags,
            "homepage": self.homepage,
            "license": self.license,
            "min_framework_version": self.min_framework_version,
            "max_framework_version": self.max_framework_version
        }


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        self._metadata: Optional[PluginMetadata] = None
        self._state = PluginState.UNLOADED
        self._config: Dict[str, Any] = {}
        self._hooks: Dict[str, Callable] = {}
        self.logger = logging.getLogger(self.__class__.__module__)
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    def activate(self) -> bool:
        """Activate the plugin."""
        pass
    
    @abstractmethod
    def deactivate(self) -> bool:
        """Deactivate the plugin."""
        pass
    
    def cleanup(self) -> bool:
        """Cleanup plugin resources."""
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate plugin configuration."""
        return []  # No validation errors by default
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the plugin."""
        return {}
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a hook callback."""
        self._hooks[hook_name] = callback
    
    def get_hooks(self) -> Dict[str, Callable]:
        """Get registered hooks."""
        return self._hooks.copy()
    
    @property
    def state(self) -> PluginState:
        """Get plugin state."""
        return self._state
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self._config.copy()
    
    @property
    def metadata(self) -> Optional[PluginMetadata]:
        """Get plugin metadata."""
        if not self._metadata:
            self._metadata = self.get_metadata()
        return self._metadata


class PluginManager:
    """
    Manages plugin loading, activation, and lifecycle.
    """
    
    def __init__(self, plugin_directories: Optional[List[str]] = None):
        self.plugin_directories = plugin_directories or ["./plugins"]
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.load_order: List[str] = []
        self.logger = logging.getLogger(__name__)
        
        # Plugin discovery and loading
        self._discovered_plugins: Dict[str, str] = {}  # name -> module path
        
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in plugin directories."""
        discovered = []
        
        for directory in self.plugin_directories:
            plugin_dir = Path(directory)
            
            if not plugin_dir.exists():
                self.logger.warning(f"Plugin directory not found: {directory}")
                continue
            
            # Look for Python files and packages
            for item in plugin_dir.iterdir():
                if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                    # Python file plugin
                    plugin_name = item.stem
                    module_path = f"{directory.replace('/', '.')}.{plugin_name}"
                    self._discovered_plugins[plugin_name] = module_path
                    discovered.append(plugin_name)
                    
                elif item.is_dir() and (item / "__init__.py").exists():
                    # Package plugin
                    plugin_name = item.name
                    module_path = f"{directory.replace('/', '.')}.{plugin_name}"
                    self._discovered_plugins[plugin_name] = module_path
                    discovered.append(plugin_name)
        
        self.logger.info(f"Discovered {len(discovered)} plugins: {discovered}")
        return discovered
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Load a specific plugin."""
        try:
            if plugin_name in self.plugins:
                self.logger.warning(f"Plugin {plugin_name} already loaded")
                return True
            
            # Get module path
            if plugin_name not in self._discovered_plugins:
                self.logger.error(f"Plugin {plugin_name} not discovered")
                return False
            
            module_path = self._discovered_plugins[plugin_name]
            
            # Import plugin module
            module = importlib.import_module(module_path)
            
            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                self.logger.error(f"No plugin class found in {module_path}")
                return False
            
            # Instantiate plugin
            plugin = plugin_class()
            
            # Validate plugin
            if not isinstance(plugin, Plugin):
                self.logger.error(f"Plugin {plugin_name} does not inherit from Plugin class")
                return False
            
            # Get metadata
            metadata = plugin.get_metadata()
            
            # Validate configuration
            plugin_config = config or {}
            validation_errors = plugin.validate_config(plugin_config)
            if validation_errors:
                self.logger.error(f"Plugin {plugin_name} config validation failed: {validation_errors}")
                return False
            
            # Initialize plugin
            if not plugin.initialize(plugin_config):
                self.logger.error(f"Failed to initialize plugin {plugin_name}")
                return False
            
            # Store plugin
            self.plugins[plugin_name] = plugin
            self.plugin_configs[plugin_name] = plugin_config
            plugin._state = PluginState.LOADED
            plugin._config = plugin_config
            
            # Update dependency graph
            self._update_dependency_graph(plugin_name, metadata.dependencies)
            
            self.logger.info(f"Successfully loaded plugin: {plugin_name} v{metadata.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def _find_plugin_class(self, module) -> Optional[Type[Plugin]]:
        """Find the plugin class in a module."""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, Plugin) and 
                obj != Plugin and 
                obj.__module__ == module.__name__):
                return obj
        return None
    
    def _update_dependency_graph(self, plugin_name: str, dependencies: List[str]):
        """Update the dependency graph for load order calculation."""
        self.dependency_graph[plugin_name] = set(dependencies)
        self._calculate_load_order()
    
    def _calculate_load_order(self):
        """Calculate the correct load order based on dependencies."""
        # Topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        load_order = []
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {plugin_name}")
            
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            for dependency in self.dependency_graph.get(plugin_name, set()):
                visit(dependency)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            load_order.append(plugin_name)
        
        try:
            for plugin_name in self.dependency_graph:
                visit(plugin_name)
            
            self.load_order = load_order
            
        except ValueError as e:
            self.logger.error(f"Dependency resolution failed: {e}")
            self.load_order = list(self.plugins.keys())
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a loaded plugin."""
        try:
            if plugin_name not in self.plugins:
                self.logger.error(f"Plugin {plugin_name} not loaded")
                return False
            
            plugin = self.plugins[plugin_name]
            
            if plugin.state == PluginState.ACTIVE:
                self.logger.warning(f"Plugin {plugin_name} already active")
                return True
            
            if plugin.state != PluginState.LOADED:
                self.logger.error(f"Plugin {plugin_name} is in state {plugin.state}, cannot activate")
                return False
            
            # Check dependencies
            metadata = plugin.metadata
            if metadata:
                for dependency in metadata.dependencies:
                    if dependency not in self.plugins:
                        self.logger.error(f"Plugin {plugin_name} dependency {dependency} not loaded")
                        return False
                    
                    if self.plugins[dependency].state != PluginState.ACTIVE:
                        self.logger.error(f"Plugin {plugin_name} dependency {dependency} not active")
                        return False
            
            # Activate plugin
            if not plugin.activate():
                self.logger.error(f"Failed to activate plugin {plugin_name}")
                plugin._state = PluginState.ERROR
                return False
            
            plugin._state = PluginState.ACTIVE
            self.logger.info(f"Activated plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate plugin {plugin_name}: {e}")
            if plugin_name in self.plugins:
                self.plugins[plugin_name]._state = PluginState.ERROR
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate an active plugin."""
        try:
            if plugin_name not in self.plugins:
                self.logger.error(f"Plugin {plugin_name} not found")
                return False
            
            plugin = self.plugins[plugin_name]
            
            if plugin.state != PluginState.ACTIVE:
                self.logger.warning(f"Plugin {plugin_name} not active")
                return True
            
            # Check if other plugins depend on this one
            dependents = [
                name for name, deps in self.dependency_graph.items()
                if plugin_name in deps and name in self.plugins and self.plugins[name].state == PluginState.ACTIVE
            ]
            
            if dependents:
                self.logger.error(f"Cannot deactivate {plugin_name}, required by: {dependents}")
                return False
            
            # Deactivate plugin
            if not plugin.deactivate():
                self.logger.error(f"Failed to deactivate plugin {plugin_name}")
                return False
            
            plugin._state = PluginState.LOADED
            self.logger.info(f"Deactivated plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin completely."""
        try:
            if plugin_name not in self.plugins:
                return True
            
            plugin = self.plugins[plugin_name]
            
            # Deactivate if active
            if plugin.state == PluginState.ACTIVE:
                if not self.deactivate_plugin(plugin_name):
                    return False
            
            # Cleanup plugin
            plugin.cleanup()
            
            # Remove from tracking
            del self.plugins[plugin_name]
            if plugin_name in self.plugin_configs:
                del self.plugin_configs[plugin_name]
            if plugin_name in self.dependency_graph:
                del self.dependency_graph[plugin_name]
            
            self._calculate_load_order()
            
            self.logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, bool]:
        """Load all discovered plugins."""
        configs = configs or {}
        results = {}
        
        discovered_plugins = self.discover_plugins()
        
        for plugin_name in discovered_plugins:
            plugin_config = configs.get(plugin_name, {})
            results[plugin_name] = self.load_plugin(plugin_name, plugin_config)
        
        return results
    
    def activate_all_plugins(self) -> Dict[str, bool]:
        """Activate all loaded plugins in dependency order."""
        results = {}
        
        # Use calculated load order
        for plugin_name in self.load_order:
            if plugin_name in self.plugins:
                results[plugin_name] = self.activate_plugin(plugin_name)
        
        # Activate any remaining plugins
        for plugin_name in self.plugins:
            if plugin_name not in results:
                results[plugin_name] = self.activate_plugin(plugin_name)
        
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin instance."""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self, state_filter: Optional[PluginState] = None) -> List[Dict[str, Any]]:
        """List plugins with their information."""
        plugin_list = []
        
        for name, plugin in self.plugins.items():
            if state_filter and plugin.state != state_filter:
                continue
            
            metadata = plugin.metadata
            plugin_info = {
                "name": name,
                "state": plugin.state.value,
                "metadata": metadata.to_dict() if metadata else None
            }
            plugin_list.append(plugin_info)
        
        return plugin_list
    
    def get_active_plugins(self) -> List[str]:
        """Get list of active plugin names."""
        return [
            name for name, plugin in self.plugins.items()
            if plugin.state == PluginState.ACTIVE
        ]
    
    def call_plugin_hooks(self, hook_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Call a hook on all active plugins that have it."""
        results = {}
        
        for plugin_name, plugin in self.plugins.items():
            if plugin.state == PluginState.ACTIVE:
                hooks = plugin.get_hooks()
                if hook_name in hooks:
                    try:
                        result = hooks[hook_name](*args, **kwargs)
                        results[plugin_name] = result
                    except Exception as e:
                        self.logger.error(f"Error calling hook {hook_name} on plugin {plugin_name}: {e}")
                        results[plugin_name] = None
        
        return results
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        state_counts = {}
        type_counts = {}
        
        for plugin in self.plugins.values():
            # Count by state
            state = plugin.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
            
            # Count by type
            if plugin.metadata:
                plugin_type = plugin.metadata.plugin_type.value
                type_counts[plugin_type] = type_counts.get(plugin_type, 0) + 1
        
        return {
            "total_plugins": len(self.plugins),
            "active_plugins": len(self.get_active_plugins()),
            "discovered_plugins": len(self._discovered_plugins),
            "state_distribution": state_counts,
            "type_distribution": type_counts,
            "dependency_graph_size": len(self.dependency_graph)
        }