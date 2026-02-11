"""
Tests for agent_personas.config.validators module.
"""

import pytest

from agent_personas.config.validators import (
    ConfigValidationError,
    validate_config,
    validate_framework_config,
    validate_personas_config,
    validate_traits_config,
    validate_behaviors_config,
    validate_emotions_config,
    validate_conversation_config,
    validate_switching_config,
    validate_performance_config,
    validate_logging_config,
    validate_storage_config,
    validate_security_config,
    validate_persona_definition,
    validate_behavior_rule,
    get_validation_summary,
)


class TestConfigValidationError:
    def test_basic_error(self):
        error = ConfigValidationError("Test error")
        assert error.message == "Test error"
        assert error.field is None
        assert error.errors == []
        
    def test_error_with_field(self):
        error = ConfigValidationError("Test error", field="test_field")
        assert error.field == "test_field"
        
    def test_error_with_errors_list(self):
        errors = ["error1", "error2"]
        error = ConfigValidationError("Test error", errors=errors)
        assert error.errors == errors


class TestValidateFrameworkConfig:
    def test_valid_framework_config(self):
        config = {
            "version": "1.0.0",
            "max_history_size": 1000
        }
        assert validate_framework_config(config) == True
        
    def test_invalid_version_format(self):
        config = {"version": "invalid"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_framework_config(config)
        assert "version must follow semantic versioning" in exc_info.value.errors[0]
        
    def test_invalid_version_type(self):
        config = {"version": 123}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_framework_config(config)
        assert "version must be a string" in exc_info.value.errors[0]
        
    def test_invalid_max_history_size(self):
        config = {"max_history_size": -1}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_framework_config(config)
        assert "max_history_size must be a positive integer" in exc_info.value.errors[0]


class TestValidatePersonasConfig:
    def test_valid_personas_config(self):
        config = {
            "min_traits": 1,
            "max_traits": 10
        }
        assert validate_personas_config(config) == True
        
    def test_invalid_min_traits(self):
        config = {"min_traits": -1}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_personas_config(config)
        assert "min_traits must be a non-negative integer" in exc_info.value.errors[0]
        
    def test_min_greater_than_max(self):
        config = {
            "min_traits": 10,
            "max_traits": 5
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_personas_config(config)
        assert "min_traits cannot be greater than max_traits" in exc_info.value.errors[0]


class TestValidateTraitsConfig:
    def test_valid_traits_config(self):
        config = {
            "default_trait_value": 0.5,
            "trait_bounds": {"min": 0.0, "max": 1.0}
        }
        assert validate_traits_config(config) == True
        
    def test_invalid_default_trait_value(self):
        config = {"default_trait_value": 1.5}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_traits_config(config)
        assert "default_trait_value must be a number between 0.0 and 1.0" in exc_info.value.errors[0]
        
    def test_invalid_trait_bounds(self):
        config = {
            "trait_bounds": {"min": 0.8, "max": 0.2}
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_traits_config(config)
        assert "trait_bounds.min must be less than trait_bounds.max" in exc_info.value.errors[0]


class TestValidateBehaviorsConfig:
    def test_valid_behaviors_config(self):
        config = {
            "max_rules": 100,
            "execution_timeout": 30.0,
            "priority_range": [1, 10]
        }
        assert validate_behaviors_config(config) == True
        
    def test_invalid_max_rules(self):
        config = {"max_rules": 0}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_behaviors_config(config)
        assert "max_rules must be a positive integer" in exc_info.value.errors[0]
        
    def test_invalid_priority_range(self):
        config = {"priority_range": [10, 1]}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_behaviors_config(config)
        assert "priority_range[0] must be less than priority_range[1]" in exc_info.value.errors[0]


class TestValidateEmotionsConfig:
    def test_valid_emotions_config(self):
        config = {
            "decay_rate": 0.1,
            "sensitivity": 0.8,
            "decay_interval_minutes": 5.0,
            "max_intensity": 10.0
        }
        assert validate_emotions_config(config) == True
        
    def test_invalid_decay_rate(self):
        config = {"decay_rate": 1.5}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_emotions_config(config)
        assert "decay_rate must be a number between 0.0 and 1.0" in exc_info.value.errors[0]


class TestValidateConversationConfig:
    def test_valid_conversation_config(self):
        config = {
            "context_memory_size": 100,
            "max_conversation_length": 1000,
            "response_timeout": 30.0
        }
        assert validate_conversation_config(config) == True
        
    def test_invalid_context_memory_size(self):
        config = {"context_memory_size": 0}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_conversation_config(config)
        assert "context_memory_size must be a positive integer" in exc_info.value.errors[0]


class TestValidateSwitchingConfig:
    def test_valid_switching_config(self):
        config = {
            "max_switches_per_hour": 5,
            "cooldown_seconds": 60.0
        }
        assert validate_switching_config(config) == True
        
    def test_invalid_max_switches(self):
        config = {"max_switches_per_hour": 0}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_switching_config(config)
        assert "max_switches_per_hour must be a positive integer" in exc_info.value.errors[0]


class TestValidatePerformanceConfig:
    def test_valid_performance_config(self):
        config = {
            "cache_size": 1000,
            "batch_size": 50,
            "memory_limit_mb": 256.0,
            "timeout_seconds": 30.0
        }
        assert validate_performance_config(config) == True
        
    def test_invalid_cache_size(self):
        config = {"cache_size": -1}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_performance_config(config)
        assert "cache_size must be a positive integer" in exc_info.value.errors[0]


class TestValidateLoggingConfig:
    def test_valid_logging_config(self):
        config = {
            "level": "INFO",
            "max_file_size_mb": 10.0,
            "backup_count": 5
        }
        assert validate_logging_config(config) == True
        
    def test_invalid_log_level(self):
        config = {"level": "INVALID"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_logging_config(config)
        assert "level must be one of" in exc_info.value.errors[0]
        
    def test_case_insensitive_log_level(self):
        config = {"level": "info"}
        assert validate_logging_config(config) == True


class TestValidateStorageConfig:
    def test_valid_storage_config(self):
        config = {
            "backup_frequency_hours": 24.0,
            "format": "json"
        }
        assert validate_storage_config(config) == True
        
    def test_invalid_format(self):
        config = {"format": "invalid"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_storage_config(config)
        assert "format must be one of" in exc_info.value.errors[0]


class TestValidateSecurityConfig:
    def test_valid_security_config(self):
        config = {
            "max_input_length": 1000,
            "allowed_file_types": [".json", ".yaml", ".txt"]
        }
        assert validate_security_config(config) == True
        
    def test_invalid_file_types(self):
        config = {"allowed_file_types": ["json", "yaml"]}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_security_config(config)
        assert "file extensions starting with '.'" in exc_info.value.errors[0]


class TestValidatePersonaDefinition:
    def test_valid_persona_definition(self):
        persona_data = {
            "name": "test_persona",
            "description": "A test persona",
            "traits": {
                "extraversion": 0.8,
                "agreeableness": 0.6
            },
            "conversation_style": "friendly",
            "emotional_baseline": "calm",
            "metadata": {"version": "1.0"}
        }
        assert validate_persona_definition(persona_data) == True
        
    def test_missing_name(self):
        persona_data = {"description": "A test persona"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_persona_definition(persona_data)
        assert "name is required" in exc_info.value.errors[0]
        
    def test_invalid_trait_name(self):
        persona_data = {
            "name": "test",
            "traits": {"123invalid": 0.5}
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_persona_definition(persona_data)
        assert "contains invalid characters" in exc_info.value.errors[0]
        
    def test_invalid_trait_value(self):
        persona_data = {
            "name": "test",
            "traits": {"valid_trait": 1.5}
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_persona_definition(persona_data)
        assert "must be between 0.0 and 1.0" in exc_info.value.errors[0]
        
    def test_long_description(self):
        persona_data = {
            "name": "test",
            "description": "x" * 1001
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_persona_definition(persona_data)
        assert "cannot exceed 1000 characters" in exc_info.value.errors[0]


class TestValidateBehaviorRule:
    def test_valid_behavior_rule(self):
        rule_data = {
            "name": "test_rule",
            "conditions": [
                {"type": "trait_condition", "trait": "extraversion", "operator": "gt", "value": 0.5}
            ],
            "actions": [
                {"type": "response_action", "template": "Hello!"}
            ],
            "priority": 5
        }
        assert validate_behavior_rule(rule_data) == True
        
    def test_missing_name(self):
        rule_data = {"conditions": []}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_behavior_rule(rule_data)
        assert "name is required" in exc_info.value.errors[0]
        
    def test_invalid_conditions(self):
        rule_data = {
            "name": "test",
            "conditions": [{"missing_type": "value"}]
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_behavior_rule(rule_data)
        assert "must have a 'type' field" in exc_info.value.errors[0]
        
    def test_invalid_actions(self):
        rule_data = {
            "name": "test",
            "actions": [{"missing_type": "value"}]
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_behavior_rule(rule_data)
        assert "must have a 'type' field" in exc_info.value.errors[0]


class TestValidateConfig:
    def test_valid_complete_config(self):
        config = {
            "framework": {"version": "1.0.0"},
            "personas": {"min_traits": 1, "max_traits": 10},
            "traits": {"default_trait_value": 0.5},
            "behaviors": {"max_rules": 100},
            "emotions": {"decay_rate": 0.1},
            "conversation": {"context_memory_size": 100},
            "switching": {"max_switches_per_hour": 5},
            "performance": {"cache_size": 1000},
            "logging": {"level": "INFO"},
            "storage": {"format": "json"},
            "security": {"max_input_length": 1000}
        }
        assert validate_config(config) == True
        
    def test_invalid_config_multiple_sections(self):
        config = {
            "framework": {"version": 123},  # Invalid
            "personas": {"min_traits": -1}  # Invalid
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert len(exc_info.value.errors) >= 2
        
    def test_partial_config(self):
        config = {"framework": {"version": "1.0.0"}}
        assert validate_config(config) == True


class TestGetValidationSummary:
    def test_valid_config_summary(self):
        config = {
            "framework": {"version": "1.0.0"},
            "personas": {"min_traits": 1},
            "traits": {"default_trait_value": 0.5}
        }
        summary = get_validation_summary(config)
        
        assert summary["valid"] == True
        assert summary["errors"] == []
        assert summary["completeness_score"] > 0.0
        assert "framework" in summary["sections"]
        assert summary["sections"]["framework"]["present"] == True
        assert summary["sections"]["framework"]["valid"] == True
        
    def test_invalid_config_summary(self):
        config = {
            "framework": {"version": 123}  # Invalid
        }
        summary = get_validation_summary(config)
        
        assert summary["valid"] == False
        assert len(summary["errors"]) > 0
        assert summary["sections"]["framework"]["valid"] == False
        
    def test_empty_config_summary(self):
        summary = get_validation_summary({})
        
        assert summary["completeness_score"] == 0.0
        assert "Consider adding missing configuration sections" in summary["recommendations"]