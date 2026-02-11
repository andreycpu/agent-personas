"""
Tests for agent_personas.utils.helpers module.
"""

import pytest
from datetime import datetime

from agent_personas.utils.helpers import (
    generate_persona_id,
    normalize_trait_name,
    clamp_value,
    weighted_average,
    fuzzy_match,
    levenshtein_distance,
    deep_merge_dicts,
    safe_divide,
    interpolate_value,
    get_trait_category,
    create_trait_range_description,
    format_duration,
    truncate_text,
    batch_items,
    ensure_list,
    get_nested_value,
    set_nested_value,
)


class TestGeneratePersonaId:
    def test_generate_persona_id_default(self):
        persona_id = generate_persona_id()
        assert persona_id.startswith("persona_")
        assert len(persona_id.split("_")) == 3
        
    def test_generate_persona_id_custom_prefix(self):
        persona_id = generate_persona_id(prefix="test")
        assert persona_id.startswith("test_")
        
    def test_generate_persona_id_custom_length(self):
        persona_id = generate_persona_id(length=12)
        suffix = persona_id.split("_")[-1]
        assert len(suffix) == 12


class TestNormalizeTraitName:
    def test_normalize_basic(self):
        assert normalize_trait_name("Extraversion") == "extraversion"
        
    def test_normalize_with_spaces(self):
        assert normalize_trait_name("Big Five") == "big_five"
        
    def test_normalize_with_dashes(self):
        assert normalize_trait_name("test-trait") == "test_trait"
        
    def test_normalize_with_special_chars(self):
        assert normalize_trait_name("trait@#$%name") == "traitname"
        
    def test_normalize_starts_with_number(self):
        assert normalize_trait_name("5trait") == "trait_5trait"
        
    def test_normalize_empty_string(self):
        assert normalize_trait_name("") == ""


class TestClampValue:
    def test_clamp_within_range(self):
        assert clamp_value(0.5) == 0.5
        
    def test_clamp_below_min(self):
        assert clamp_value(-0.1) == 0.0
        
    def test_clamp_above_max(self):
        assert clamp_value(1.1) == 1.0
        
    def test_clamp_custom_range(self):
        assert clamp_value(5, min_val=2, max_val=4) == 4


class TestWeightedAverage:
    def test_weighted_average_no_weights(self):
        values = {"a": 1.0, "b": 3.0}
        assert weighted_average(values) == 2.0
        
    def test_weighted_average_with_weights(self):
        values = {"a": 1.0, "b": 3.0}
        weights = {"a": 1.0, "b": 2.0}
        result = weighted_average(values, weights)
        expected = (1.0 * 1.0 + 3.0 * 2.0) / (1.0 + 2.0)
        assert result == expected
        
    def test_weighted_average_empty(self):
        assert weighted_average({}) == 0.0


class TestFuzzyMatch:
    def test_fuzzy_match_exact(self):
        assert fuzzy_match("hello", ["hello"]) == True
        
    def test_fuzzy_match_substring(self):
        assert fuzzy_match("hello world", ["world"]) == True
        
    def test_fuzzy_match_no_match(self):
        assert fuzzy_match("hello", ["goodbye"]) == False
        
    def test_fuzzy_match_similarity(self):
        assert fuzzy_match("hello", ["helo"], threshold=0.8) == True


class TestLevenshteinDistance:
    def test_levenshtein_identical(self):
        assert levenshtein_distance("hello", "hello") == 0
        
    def test_levenshtein_one_char_diff(self):
        assert levenshtein_distance("hello", "hallo") == 1
        
    def test_levenshtein_empty_strings(self):
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("hello", "") == 5
        assert levenshtein_distance("", "hello") == 5


class TestDeepMergeDicts:
    def test_deep_merge_simple(self):
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3}
        result = deep_merge_dicts(dict1, dict2)
        assert result == {"a": 1, "b": 2, "c": 3}
        
    def test_deep_merge_nested(self):
        dict1 = {"a": {"x": 1, "y": 2}}
        dict2 = {"a": {"y": 3, "z": 4}}
        result = deep_merge_dicts(dict1, dict2)
        assert result == {"a": {"x": 1, "y": 3, "z": 4}}
        
    def test_deep_merge_override(self):
        dict1 = {"a": 1}
        dict2 = {"a": 2}
        result = deep_merge_dicts(dict1, dict2)
        assert result == {"a": 2}


class TestSafeDivide:
    def test_safe_divide_normal(self):
        assert safe_divide(6, 2) == 3.0
        
    def test_safe_divide_by_zero(self):
        assert safe_divide(6, 0) == 0.0
        
    def test_safe_divide_by_zero_custom_default(self):
        assert safe_divide(6, 0, default=1.0) == 1.0


class TestInterpolateValue:
    def test_interpolate_start(self):
        assert interpolate_value(10, 20, 0.0) == 10
        
    def test_interpolate_end(self):
        assert interpolate_value(10, 20, 1.0) == 20
        
    def test_interpolate_middle(self):
        assert interpolate_value(10, 20, 0.5) == 15
        
    def test_interpolate_clamp(self):
        assert interpolate_value(10, 20, 1.5) == 20


class TestGetTraitCategory:
    def test_personality_traits(self):
        assert get_trait_category("extraversion") == "personality"
        assert get_trait_category("agreeableness") == "personality"
        
    def test_emotional_traits(self):
        assert get_trait_category("empathy") == "emotional"
        assert get_trait_category("emotional_stability") == "emotional"
        
    def test_cognitive_traits(self):
        assert get_trait_category("analytical_thinking") == "cognitive"
        assert get_trait_category("logic") == "cognitive"
        
    def test_social_traits(self):
        assert get_trait_category("social_skills") == "social"
        assert get_trait_category("leadership") == "social"
        
    def test_communication_traits(self):
        assert get_trait_category("verbal_skills") == "communication"
        assert get_trait_category("formal_speech") == "communication"
        
    def test_behavioral_traits(self):
        assert get_trait_category("assertiveness") == "behavioral"
        assert get_trait_category("reactive") == "behavioral"
        
    def test_general_traits(self):
        assert get_trait_category("unknown_trait") == "general"


class TestCreateTraitRangeDescription:
    def test_very_low(self):
        assert create_trait_range_description(0, 10, 0.5) == "very low"
        
    def test_low(self):
        assert create_trait_range_description(0, 10, 2) == "low"
        
    def test_moderate(self):
        assert create_trait_range_description(0, 10, 5) == "moderate"
        
    def test_high(self):
        assert create_trait_range_description(0, 10, 8) == "high"
        
    def test_very_high(self):
        assert create_trait_range_description(0, 10, 9.5) == "very high"
        
    def test_invalid_range(self):
        assert create_trait_range_description(10, 5, 7) == "invalid range"


class TestFormatDuration:
    def test_format_seconds(self):
        assert format_duration(30.5) == "30.5s"
        
    def test_format_minutes(self):
        assert format_duration(90) == "1.5m"
        
    def test_format_hours(self):
        assert format_duration(7200) == "2.0h"


class TestTruncateText:
    def test_truncate_no_truncation(self):
        text = "short"
        assert truncate_text(text, 100) == text
        
    def test_truncate_with_truncation(self):
        text = "this is a very long text"
        result = truncate_text(text, 10)
        assert len(result) == 10
        assert result.endswith("...")
        
    def test_truncate_custom_suffix(self):
        text = "long text"
        result = truncate_text(text, 5, suffix="!!")
        assert result.endswith("!!")


class TestBatchItems:
    def test_batch_items_even(self):
        items = [1, 2, 3, 4, 5, 6]
        batches = batch_items(items, 2)
        assert batches == [[1, 2], [3, 4], [5, 6]]
        
    def test_batch_items_uneven(self):
        items = [1, 2, 3, 4, 5]
        batches = batch_items(items, 2)
        assert batches == [[1, 2], [3, 4], [5]]
        
    def test_batch_items_empty(self):
        assert batch_items([], 2) == []


class TestEnsureList:
    def test_ensure_list_single_item(self):
        assert ensure_list("item") == ["item"]
        
    def test_ensure_list_already_list(self):
        items = ["a", "b"]
        assert ensure_list(items) == items
        
    def test_ensure_list_none(self):
        assert ensure_list(None) == [None]


class TestGetNestedValue:
    def test_get_nested_value_simple(self):
        data = {"a": {"b": {"c": 123}}}
        assert get_nested_value(data, "a.b.c") == 123
        
    def test_get_nested_value_not_found(self):
        data = {"a": {"b": {"c": 123}}}
        assert get_nested_value(data, "a.b.d") is None
        
    def test_get_nested_value_default(self):
        data = {"a": {"b": {"c": 123}}}
        assert get_nested_value(data, "a.b.d", default="missing") == "missing"
        
    def test_get_nested_value_custom_separator(self):
        data = {"a": {"b": {"c": 123}}}
        assert get_nested_value(data, "a/b/c", separator="/") == 123


class TestSetNestedValue:
    def test_set_nested_value_new(self):
        data = {}
        set_nested_value(data, "a.b.c", 123)
        assert data == {"a": {"b": {"c": 123}}}
        
    def test_set_nested_value_existing(self):
        data = {"a": {"b": {"c": 123}}}
        set_nested_value(data, "a.b.c", 456)
        assert data["a"]["b"]["c"] == 456
        
    def test_set_nested_value_custom_separator(self):
        data = {}
        set_nested_value(data, "a/b/c", 123, separator="/")
        assert data == {"a": {"b": {"c": 123}}}