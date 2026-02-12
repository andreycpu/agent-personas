"""
Advanced configuration management with environment-aware settings.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import os
import json
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "personas.db"
    username: str = ""
    password: str = ""
    pool_size: int = 5
    timeout: int = 30
    ssl_enabled: bool = False


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    backend: str = "memory"  # memory, redis, file
    ttl_seconds: int = 3600
    max_size: int = 1000
    redis_url: str = "redis://localhost:6379/0"
    file_cache_dir: str = "./cache"


@dataclass
class SecurityConfig:
    """Security configuration."""
    encryption_enabled: bool = False
    encryption_key: str = ""
    api_keys_enabled: bool = False
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    session_timeout_minutes: int = 60
    allowed_hosts: List[str] = field(default_factory=list)


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    max_concurrent_operations: int = 10
    request_timeout_seconds: int = 30
    batch_size: int = 100
    memory_limit_mb: int = 512
    gc_threshold: int = 1000
    profiling_enabled: bool = False


@dataclass
class AdvancedSettings:
    """Advanced configuration settings."""
    environment: Environment = Environment.DEVELOPMENT
    debug_mode: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_file: str = "persona_framework.log"
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "analytics_enabled": True,
        "versioning_enabled": True,
        "multilingual_support": True,
        "a_b_testing": True,
        "advanced_caching": True,
        "background_tasks": True,
        "api_server": False,
        "web_interface": False,
        "real_time_updates": False,
        "machine_learning_insights": False
    })
    
    # Integration settings
    integrations: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "openai": {"enabled": False, "api_key": "", "model": "gpt-3.5-turbo"},
        "anthropic": {"enabled": False, "api_key": "", "model": "claude-2"},
        "elasticsearch": {"enabled": False, "hosts": ["localhost:9200"]},
        "prometheus": {"enabled": False, "host": "localhost", "port": 9090},
        "webhook": {"enabled": False, "endpoints": []}
    })
    
    # Storage settings
    storage: Dict[str, Any] = field(default_factory=lambda: {
        "primary_backend": "file",
        "backup_enabled": True,
        "backup_interval_hours": 24,
        "retention_days": 90,
        "compression_enabled": True,
        "encryption_at_rest": False
    })
    
    # Notification settings
    notifications: Dict[str, Any] = field(default_factory=lambda: {
        "email_enabled": False,
        "slack_enabled": False,
        "webhook_enabled": False,
        "alert_thresholds": {
            "error_rate": 0.05,
            "memory_usage": 0.8,
            "disk_usage": 0.9
        }
    })


class ConfigurationManager:
    """
    Advanced configuration manager with environment-aware settings.
    """
    
    def __init__(self, config_file: Optional[str] = None, env_prefix: str = "PERSONA_"):
        self.config_file = config_file
        self.env_prefix = env_prefix
        self.settings = AdvancedSettings()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file and environment variables."""
        # 1. Load from file if specified
        if self.config_file:
            self._load_from_file(self.config_file)
        
        # 2. Load from environment variables
        self._load_from_environment()
        
        # 3. Apply environment-specific overrides
        self._apply_environment_overrides()
        
        # 4. Validate configuration
        self._validate_configuration()
        
        self.logger.info(f"Configuration loaded for environment: {self.settings.environment.value}")
    
    def _load_from_file(self, config_file: str):
        """Load configuration from file."""
        try:
            file_path = Path(config_file)
            
            if not file_path.exists():
                self.logger.warning(f"Configuration file not found: {config_file}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            self._apply_config_data(config_data)
            self.logger.info(f"Configuration loaded from: {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        try:
            # Environment
            if env_val := os.getenv(f"{self.env_prefix}ENVIRONMENT"):
                try:
                    self.settings.environment = Environment(env_val.lower())
                except ValueError:
                    self.logger.warning(f"Invalid environment value: {env_val}")
            
            # Debug mode
            if env_val := os.getenv(f"{self.env_prefix}DEBUG"):
                self.settings.debug_mode = env_val.lower() in ('true', '1', 'yes', 'on')
            
            # Log level
            if env_val := os.getenv(f"{self.env_prefix}LOG_LEVEL"):
                try:
                    self.settings.log_level = LogLevel(env_val.upper())
                except ValueError:
                    self.logger.warning(f"Invalid log level: {env_val}")
            
            # Database settings
            if env_val := os.getenv(f"{self.env_prefix}DATABASE_URL"):
                self._parse_database_url(env_val)
            
            # Cache settings
            if env_val := os.getenv(f"{self.env_prefix}CACHE_BACKEND"):
                self.settings.cache.backend = env_val
            
            if env_val := os.getenv(f"{self.env_prefix}REDIS_URL"):
                self.settings.cache.redis_url = env_val
            
            # Security settings
            if env_val := os.getenv(f"{self.env_prefix}ENCRYPTION_KEY"):
                self.settings.security.encryption_key = env_val
                self.settings.security.encryption_enabled = True
            
            # Feature flags from environment
            for feature_name in self.settings.features:
                env_key = f"{self.env_prefix}FEATURE_{feature_name.upper()}"
                if env_val := os.getenv(env_key):
                    self.settings.features[feature_name] = env_val.lower() in ('true', '1', 'yes', 'on')
            
            # Integration API keys
            for integration in self.settings.integrations:
                api_key_env = f"{self.env_prefix}{integration.upper()}_API_KEY"
                if env_val := os.getenv(api_key_env):
                    self.settings.integrations[integration]["api_key"] = env_val
                    self.settings.integrations[integration]["enabled"] = True
            
        except Exception as e:
            self.logger.error(f"Failed to load environment configuration: {e}")
    
    def _parse_database_url(self, database_url: str):
        """Parse database URL and update database config."""
        try:
            # Simple URL parsing for common database formats
            # Format: type://username:password@host:port/database
            
            if "://" in database_url:
                type_part, rest = database_url.split("://", 1)
                self.settings.database.type = type_part
                
                if "@" in rest:
                    auth_part, host_part = rest.rsplit("@", 1)
                    if ":" in auth_part:
                        username, password = auth_part.split(":", 1)
                        self.settings.database.username = username
                        self.settings.database.password = password
                else:
                    host_part = rest
                
                if "/" in host_part:
                    host_port, database = host_part.split("/", 1)
                    self.settings.database.database = database
                else:
                    host_port = host_part
                
                if ":" in host_port:
                    host, port = host_port.split(":", 1)
                    self.settings.database.host = host
                    self.settings.database.port = int(port)
                else:
                    self.settings.database.host = host_port
        
        except Exception as e:
            self.logger.error(f"Failed to parse database URL: {e}")
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides."""
        env = self.settings.environment
        
        if env == Environment.DEVELOPMENT:
            self.settings.debug_mode = True
            self.settings.log_level = LogLevel.DEBUG
            self.settings.security.encryption_enabled = False
            self.settings.performance.profiling_enabled = True
            self.settings.cache.ttl_seconds = 300  # Shorter TTL for development
        
        elif env == Environment.TESTING:
            self.settings.debug_mode = True
            self.settings.log_level = LogLevel.WARNING
            self.settings.database.database = "test_personas.db"
            self.settings.cache.backend = "memory"
            self.settings.storage["backup_enabled"] = False
        
        elif env == Environment.STAGING:
            self.settings.debug_mode = False
            self.settings.log_level = LogLevel.INFO
            self.settings.security.encryption_enabled = True
            self.settings.performance.profiling_enabled = False
        
        elif env == Environment.PRODUCTION:
            self.settings.debug_mode = False
            self.settings.log_level = LogLevel.WARNING
            self.settings.security.encryption_enabled = True
            self.settings.security.api_keys_enabled = True
            self.settings.security.rate_limiting_enabled = True
            self.settings.performance.profiling_enabled = False
            self.settings.cache.ttl_seconds = 7200  # Longer TTL for production
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to settings."""
        try:
            # Handle nested configuration updates
            for key, value in config_data.items():
                if hasattr(self.settings, key):
                    if isinstance(value, dict):
                        current_attr = getattr(self.settings, key)
                        if hasattr(current_attr, '__dict__'):
                            # Update dataclass fields
                            for sub_key, sub_value in value.items():
                                if hasattr(current_attr, sub_key):
                                    setattr(current_attr, sub_key, sub_value)
                        else:
                            # Update dictionary
                            current_attr.update(value)
                    else:
                        setattr(self.settings, key, value)
        
        except Exception as e:
            self.logger.error(f"Failed to apply configuration data: {e}")
    
    def _validate_configuration(self):
        """Validate configuration settings."""
        errors = []
        warnings = []
        
        # Validate database configuration
        if self.settings.database.type not in ["sqlite", "postgresql", "mysql"]:
            errors.append(f"Unsupported database type: {self.settings.database.type}")
        
        if self.settings.database.port <= 0 or self.settings.database.port > 65535:
            errors.append(f"Invalid database port: {self.settings.database.port}")
        
        # Validate cache configuration
        if self.settings.cache.backend not in ["memory", "redis", "file"]:
            errors.append(f"Unsupported cache backend: {self.settings.cache.backend}")
        
        if self.settings.cache.ttl_seconds <= 0:
            warnings.append("Cache TTL is zero or negative")
        
        # Validate security configuration
        if self.settings.security.encryption_enabled and not self.settings.security.encryption_key:
            errors.append("Encryption enabled but no encryption key provided")
        
        if self.settings.security.max_requests_per_minute <= 0:
            errors.append("Rate limit must be positive")
        
        # Validate performance configuration
        if self.settings.performance.max_concurrent_operations <= 0:
            errors.append("Max concurrent operations must be positive")
        
        if self.settings.performance.memory_limit_mb <= 0:
            warnings.append("Memory limit is zero or negative")
        
        # Log validation results
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        if warnings:
            for warning in warnings:
                self.logger.warning(f"Configuration warning: {warning}")
    
    def get_setting(self, setting_path: str, default: Any = None) -> Any:
        """Get a configuration setting using dot notation."""
        try:
            parts = setting_path.split('.')
            current = self.settings
            
            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
        
        except Exception:
            return default
    
    def set_setting(self, setting_path: str, value: Any) -> bool:
        """Set a configuration setting using dot notation."""
        try:
            parts = setting_path.split('.')
            current = self.settings
            
            for part in parts[:-1]:
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                else:
                    return False
            
            final_part = parts[-1]
            
            if hasattr(current, final_part):
                setattr(current, final_part, value)
                return True
            elif isinstance(current, dict):
                current[final_part] = value
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to set setting {setting_path}: {e}")
            return False
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.settings.features.get(feature_name, False)
    
    def is_integration_enabled(self, integration_name: str) -> bool:
        """Check if an integration is enabled."""
        return self.settings.integrations.get(integration_name, {}).get("enabled", False)
    
    def get_integration_config(self, integration_name: str) -> Dict[str, Any]:
        """Get configuration for a specific integration."""
        return self.settings.integrations.get(integration_name, {})
    
    def save_configuration(self, output_file: str):
        """Save current configuration to file."""
        try:
            config_dict = self._settings_to_dict()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.endswith('.yaml') or output_file.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False)
                else:
                    json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuration saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _settings_to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        def convert_value(value):
            if hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, Enum):
                return value.value
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            else:
                return value
        
        return convert_value(self.settings)
    
    def reload_configuration(self):
        """Reload configuration from sources."""
        self.logger.info("Reloading configuration...")
        self._load_configuration()
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            "environment": self.settings.environment.value,
            "debug_mode": self.settings.debug_mode,
            "log_level": self.settings.log_level.value,
            "database_type": self.settings.database.type,
            "cache_backend": self.settings.cache.backend,
            "security_enabled": self.settings.security.encryption_enabled,
            "enabled_features": [k for k, v in self.settings.features.items() if v],
            "enabled_integrations": [k for k, v in self.settings.integrations.items() if v.get("enabled", False)],
            "storage_backend": self.settings.storage["primary_backend"]
        }