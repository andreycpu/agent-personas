"""
Helper utilities and convenience functions.
"""

import random
import string
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


def generate_persona_id(prefix: str = "persona", length: int = 8) -> str:
    """
    Generate a unique persona ID.
    
    Args:
        prefix: ID prefix
        length: Random suffix length
        
    Returns:
        Generated ID
    """
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{prefix}_{timestamp}_{suffix}"


def normalize_trait_name(name: str) -> str:
    """
    Normalize a trait name to standard format.
    
    Args:
        name: Raw trait name
        
    Returns:
        Normalized trait name
    """
    # Convert to lowercase, replace spaces and dashes with underscores
    normalized = name.lower().replace(" ", "_").replace("-", "_")
    
    # Remove non-alphanumeric characters except underscores
    normalized = ''.join(c for c in normalized if c.isalnum() or c == '_')
    
    # Ensure it starts with a letter
    if normalized and not normalized[0].isalpha():
        normalized = "trait_" + normalized
    
    return normalized


def clamp_value(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp a value to a specified range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def weighted_average(values: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate weighted average of values.
    
    Args:
        values: Values to average
        weights: Optional weights (defaults to equal weights)
        
    Returns:
        Weighted average
    """
    if not values:
        return 0.0
    
    if weights is None:
        return sum(values.values()) / len(values)
    
    total_weighted = sum(values[key] * weights.get(key, 1.0) for key in values)
    total_weights = sum(weights.get(key, 1.0) for key in values)
    
    return total_weighted / total_weights if total_weights > 0 else 0.0


def fuzzy_match(text: str, patterns: List[str], threshold: float = 0.6) -> bool:
    """
    Perform fuzzy matching of text against patterns.
    
    Args:
        text: Text to match
        patterns: List of patterns to match against
        threshold: Match threshold (0.0-1.0)
        
    Returns:
        True if any pattern matches above threshold
    """
    text_lower = text.lower()
    
    for pattern in patterns:
        pattern_lower = pattern.lower()
        
        # Simple substring matching
        if pattern_lower in text_lower:
            return True
        
        # Levenshtein distance-based matching
        distance = levenshtein_distance(text_lower, pattern_lower)
        max_len = max(len(text_lower), len(pattern_lower))
        
        if max_len > 0:
            similarity = 1.0 - (distance / max_len)
            if similarity >= threshold:
                return True
    
    return False


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default
    """
    return numerator / denominator if denominator != 0 else default


def interpolate_value(value1: float, value2: float, factor: float) -> float:
    """
    Interpolate between two values.
    
    Args:
        value1: Start value
        value2: End value
        factor: Interpolation factor (0.0-1.0)
        
    Returns:
        Interpolated value
    """
    factor = clamp_value(factor, 0.0, 1.0)
    return value1 + (value2 - value1) * factor


def get_trait_category(trait_name: str) -> str:
    """
    Guess the category of a trait based on its name.
    
    Args:
        trait_name: Trait name
        
    Returns:
        Estimated category
    """
    name_lower = trait_name.lower()
    
    # Personality traits
    personality_keywords = ['extra', 'intro', 'agree', 'conscient', 'neurot', 'open']
    if any(keyword in name_lower for keyword in personality_keywords):
        return "personality"
    
    # Emotional traits
    emotional_keywords = ['empath', 'emotion', 'feel', 'mood', 'sentiment']
    if any(keyword in name_lower for keyword in emotional_keywords):
        return "emotional"
    
    # Cognitive traits
    cognitive_keywords = ['think', 'cognit', 'intellect', 'reason', 'logic', 'analyt']
    if any(keyword in name_lower for keyword in cognitive_keywords):
        return "cognitive"
    
    # Social traits
    social_keywords = ['social', 'friend', 'leader', 'team', 'cooperat']
    if any(keyword in name_lower for keyword in social_keywords):
        return "social"
    
    # Communication traits
    communication_keywords = ['talk', 'speak', 'verbal', 'communicate', 'formal']
    if any(keyword in name_lower for keyword in communication_keywords):
        return "communication"
    
    # Behavioral traits
    behavioral_keywords = ['behav', 'action', 'response', 'react', 'assertiv']
    if any(keyword in name_lower for keyword in behavioral_keywords):
        return "behavioral"
    
    return "general"


def create_trait_range_description(min_val: float, max_val: float, current_val: float) -> str:
    """
    Create a descriptive string for a trait value within a range.
    
    Args:
        min_val: Minimum possible value
        max_val: Maximum possible value
        current_val: Current value
        
    Returns:
        Descriptive string
    """
    if max_val <= min_val:
        return "invalid range"
    
    normalized = (current_val - min_val) / (max_val - min_val)
    
    if normalized < 0.1:
        return "very low"
    elif normalized < 0.3:
        return "low"
    elif normalized < 0.7:
        return "moderate"
    elif normalized < 0.9:
        return "high"
    else:
        return "very high"


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split items into batches.
    
    Args:
        items: Items to batch
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches


def ensure_list(value: Union[Any, List[Any]]) -> List[Any]:
    """
    Ensure value is a list.
    
    Args:
        value: Value to convert to list
        
    Returns:
        List containing the value(s)
    """
    if isinstance(value, list):
        return value
    return [value]


def get_nested_value(data: Dict[str, Any], path: str, default: Any = None, separator: str = ".") -> Any:
    """
    Get a nested value from a dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path to value
        default: Default value if not found
        separator: Path separator
        
    Returns:
        Found value or default
    """
    keys = path.split(separator)
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_nested_value(data: Dict[str, Any], path: str, value: Any, separator: str = ".") -> None:
    """
    Set a nested value in a dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        path: Dot-separated path to set
        value: Value to set
        separator: Path separator
    """
    keys = path.split(separator)
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value