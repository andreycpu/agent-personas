"""
Settings management for persona framework configuration.
"""

import json
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class PersonaSettings:
    """Configuration settings for the persona framework."""
    
    # Core settings
    default_persona: Optional[str] = None
    auto_save: bool = True
    max_history_size: int = 100
    
    # Trait settings
    trait_validation: bool = True
    allow_trait_conflicts: bool = False
    auto_resolve_conflicts: bool = True
    default_trait_value: float = 0.5
    
    # Behavior settings
    behavior_rules_enabled: bool = True
    max_behavior_rules: int = 50
    rule_execution_timeout: float = 1.0
    
    # Emotion settings
    emotional_processing: bool = True
    emotion_decay_rate: float = 0.1
    emotion_sensitivity: float = 0.5
    auto_emotion_decay: bool = True
    
    # Conversation settings
    adaptive_style: bool = True
    context_memory_size: int = 20
    auto_style_adaptation: bool = True
    
    # Switching settings
    allow_persona_switching: bool = True
    switch_validation: bool = True
    preserve_context_on_switch: bool = True
    max_switches_per_hour: int = 20
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    structured_logging: bool = False
    
    # Performance settings
    cache_size: int = 100
    async_processing: bool = False
    batch_size: int = 10
    
    # Storage settings
    data_directory: str = "./persona_data"
    backup_enabled: bool = True
    backup_frequency: int = 24  # hours
    compression_enabled: bool = True
    
    # Development settings
    debug_mode: bool = False
    verbose_errors: bool = False
    profile_performance: bool = False
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, **kwargs) -> None:
        """Update settings with keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.custom_settings[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value with optional default."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.custom_settings.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonaSettings":
        """Create settings from dictionary."""
        # Extract known fields
        known_fields = {
            field.name for field in cls.__dataclass_fields__.values()
            if field.name != "custom_settings"
        }
        
        kwargs = {}
        custom = {}
        
        for key, value in data.items():
            if key in known_fields:
                kwargs[key] = value
            else:
                custom[key] = value
        
        if custom:
            kwargs["custom_settings"] = custom
        
        return cls(**kwargs)
    
    def validate(self) -> list[str]:
        """Validate settings and return list of errors."""
        errors = []
        
        # Validate numeric ranges
        if not 0.0 <= self.emotion_decay_rate <= 1.0:
            errors.append("emotion_decay_rate must be between 0.0 and 1.0")
        
        if not 0.0 <= self.emotion_sensitivity <= 1.0:
            errors.append("emotion_sensitivity must be between 0.0 and 1.0")
        
        if not 0.0 <= self.default_trait_value <= 1.0:
            errors.append("default_trait_value must be between 0.0 and 1.0")
        
        if self.max_history_size <= 0:
            errors.append("max_history_size must be positive")
        
        if self.context_memory_size <= 0:
            errors.append("context_memory_size must be positive")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of {valid_log_levels}")
        
        # Validate paths
        if self.log_to_file and self.log_file_path:
            log_path = Path(self.log_file_path)
            if not log_path.parent.exists():
                errors.append(f"Log file directory does not exist: {log_path.parent}")
        
        return errors
    
    def create_directories(self) -> None:
        """Create necessary directories for the settings."""
        # Create data directory
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)
        
        # Create log directory if needed
        if self.log_to_file and self.log_file_path:
            log_path = Path(self.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)


def load_settings(config_path: Union[str, Path] = None) -> PersonaSettings:
    """
    Load settings from configuration file.
    
    Args:
        config_path: Path to configuration file. If None, searches standard locations.
        
    Returns:
        PersonaSettings instance
    """
    if config_path is None:
        # Search standard configuration locations
        search_paths = [
            "agent_personas.json",
            "config/agent_personas.json", 
            os.path.expanduser("~/.agent_personas/config.json"),
            "/etc/agent_personas/config.json"
        ]
        
        config_path = None
        for path in search_paths:
            if Path(path).exists():
                config_path = path
                break
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return PersonaSettings.from_dict(config_data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
    
    # Return default settings if no config found
    return PersonaSettings()


def save_settings(settings: PersonaSettings, config_path: Union[str, Path]) -> None:
    """
    Save settings to configuration file.
    
    Args:
        settings: Settings to save
        config_path: Path to save configuration file
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(settings.to_dict(), f, indent=2)


def get_environment_settings() -> Dict[str, Any]:
    """
    Get settings from environment variables.
    
    Returns:
        Dictionary of settings from environment
    """
    env_settings = {}
    
    # Environment variable mapping
    env_mapping = {
        "AGENT_PERSONAS_DEFAULT_PERSONA": "default_persona",
        "AGENT_PERSONAS_AUTO_SAVE": "auto_save",
        "AGENT_PERSONAS_LOG_LEVEL": "log_level",
        "AGENT_PERSONAS_DEBUG": "debug_mode",
        "AGENT_PERSONAS_DATA_DIR": "data_directory",
        "AGENT_PERSONAS_LOG_FILE": "log_file_path",
        "AGENT_PERSONAS_CACHE_SIZE": "cache_size",
        "AGENT_PERSONAS_MAX_HISTORY": "max_history_size"
    }
    
    for env_var, setting_name in env_mapping.items():
        value = os.getenv(env_var)
        if value is not None:
            # Type conversion
            if setting_name in ["auto_save", "debug_mode"]:
                env_settings[setting_name] = value.lower() in ("true", "1", "yes")
            elif setting_name in ["cache_size", "max_history_size"]:
                try:
                    env_settings[setting_name] = int(value)
                except ValueError:
                    continue
            else:
                env_settings[setting_name] = value
    
    return env_settings


def merge_settings(*settings_list: PersonaSettings) -> PersonaSettings:
    """
    Merge multiple settings objects, with later ones taking precedence.
    
    Args:
        *settings_list: Settings objects to merge
        
    Returns:
        Merged settings object
    """
    if not settings_list:
        return PersonaSettings()
    
    base_settings = settings_list[0]
    merged_dict = base_settings.to_dict()
    
    for settings in settings_list[1:]:
        settings_dict = settings.to_dict()
        merged_dict.update(settings_dict)
        
        # Merge custom settings separately
        if "custom_settings" in settings_dict:
            if "custom_settings" not in merged_dict:
                merged_dict["custom_settings"] = {}
            merged_dict["custom_settings"].update(settings_dict["custom_settings"])
    
    return PersonaSettings.from_dict(merged_dict)


def apply_environment_overrides(settings: PersonaSettings) -> PersonaSettings:
    """
    Apply environment variable overrides to settings.
    
    Args:
        settings: Base settings object
        
    Returns:
        Settings with environment overrides applied
    """
    env_settings = get_environment_settings()
    if env_settings:
        settings.update(**env_settings)
    return settings


def create_config_template(output_path: Union[str, Path]) -> None:
    """
    Create a configuration file template.
    
    Args:
        output_path: Path to create template file
    """
    template_settings = PersonaSettings()
    
    # Add comments to the template
    config_data = template_settings.to_dict()
    
    template_with_comments = {
        "_comments": {
            "default_persona": "Name of persona to activate by default",
            "auto_save": "Whether to automatically save changes",
            "trait_validation": "Whether to validate trait values and constraints",
            "emotional_processing": "Whether to enable emotional state processing",
            "log_level": "Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
            "data_directory": "Directory to store persona data files"
        },
        **config_data
    }
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(template_with_comments, f, indent=2)


class SettingsManager:
    """Manages settings loading, saving, and updates."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = config_path
        self.settings = self.load()
    
    def load(self) -> PersonaSettings:
        """Load settings from file and environment."""
        # Load base settings from file
        file_settings = load_settings(self.config_path)
        
        # Apply environment overrides
        final_settings = apply_environment_overrides(file_settings)
        
        return final_settings
    
    def save(self, settings: Optional[PersonaSettings] = None) -> None:
        """Save settings to file."""
        if settings is None:
            settings = self.settings
        
        if self.config_path:
            save_settings(settings, self.config_path)
        else:
            # Save to default location
            default_path = Path("agent_personas.json")
            save_settings(settings, default_path)
            self.config_path = default_path
    
    def update(self, **kwargs) -> None:
        """Update and save settings."""
        self.settings.update(**kwargs)
        if self.settings.auto_save:
            self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset settings to defaults."""
        self.settings = PersonaSettings()
        if self.settings.auto_save:
            self.save()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.settings.get(key, default)
    
    def validate_settings(self) -> list[str]:
        """Validate current settings."""
        return self.settings.validate()


# Global settings manager instance
global_settings = SettingsManager()