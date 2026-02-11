"""
Metrics and analysis utilities for persona behavior and performance.
"""

import math
import statistics
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from ..core.persona import Persona


def calculate_persona_similarity(persona1: Persona, persona2: Persona) -> float:
    """
    Calculate similarity score between two personas.
    
    Args:
        persona1: First persona
        persona2: Second persona
        
    Returns:
        Similarity score between 0.0 (completely different) and 1.0 (identical)
    """
    # Get traits from both personas
    traits1 = persona1.traits
    traits2 = persona2.traits
    
    # Get all unique trait names
    all_traits = set(traits1.keys()) | set(traits2.keys())
    
    if not all_traits:
        return 1.0  # Both have no traits, consider them identical
    
    # Calculate trait differences
    trait_differences = []
    for trait in all_traits:
        value1 = traits1.get(trait, 0.5)  # Default to neutral
        value2 = traits2.get(trait, 0.5)
        diff = abs(value1 - value2)
        trait_differences.append(diff)
    
    # Calculate average difference and convert to similarity
    avg_difference = statistics.mean(trait_differences)
    similarity = 1.0 - avg_difference
    
    # Factor in conversation style similarity
    style_similarity = 1.0 if persona1.conversation_style == persona2.conversation_style else 0.8
    
    # Factor in emotional baseline similarity
    emotional_similarity = 1.0 if persona1.emotional_baseline == persona2.emotional_baseline else 0.9
    
    # Weighted combination
    final_similarity = (
        similarity * 0.7 +  # Traits weight 70%
        style_similarity * 0.2 +  # Style weight 20%
        emotional_similarity * 0.1  # Emotion weight 10%
    )
    
    return max(0.0, min(1.0, final_similarity))


def analyze_trait_distribution(personas: List[Persona]) -> Dict[str, Any]:
    """
    Analyze trait distribution across a collection of personas.
    
    Args:
        personas: List of personas to analyze
        
    Returns:
        Analysis results with statistics and insights
    """
    if not personas:
        return {"error": "No personas provided for analysis"}
    
    # Collect all traits
    all_trait_values = defaultdict(list)
    for persona in personas:
        for trait, value in persona.traits.items():
            all_trait_values[trait].append(value)
    
    # Calculate statistics for each trait
    trait_stats = {}
    for trait, values in all_trait_values.items():
        trait_stats[trait] = {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values)
        }
    
    # Find most/least variable traits
    trait_variability = {trait: stats["std_dev"] for trait, stats in trait_stats.items()}
    most_variable = max(trait_variability.items(), key=lambda x: x[1]) if trait_variability else None
    least_variable = min(trait_variability.items(), key=lambda x: x[1]) if trait_variability else None
    
    # Analyze trait coverage
    total_possible_traits = len(all_trait_values)
    persona_coverage = {}
    for persona in personas:
        coverage = len(persona.traits) / total_possible_traits if total_possible_traits > 0 else 0
        persona_coverage[persona.name] = coverage
    
    # Find trait correlations (simplified)
    trait_correlations = {}
    traits_list = list(all_trait_values.keys())
    for i, trait1 in enumerate(traits_list):
        for trait2 in traits_list[i+1:]:
            values1 = all_trait_values[trait1]
            values2 = all_trait_values[trait2]
            
            # Only calculate correlation if both traits appear in same personas
            common_personas = []
            for persona in personas:
                if trait1 in persona.traits and trait2 in persona.traits:
                    common_personas.append((persona.traits[trait1], persona.traits[trait2]))
            
            if len(common_personas) >= 2:
                # Calculate Pearson correlation coefficient
                correlation = calculate_correlation(
                    [x[0] for x in common_personas],
                    [x[1] for x in common_personas]
                )
                trait_correlations[f"{trait1}_{trait2}"] = correlation
    
    return {
        "total_personas": len(personas),
        "total_unique_traits": len(all_trait_values),
        "trait_statistics": trait_stats,
        "most_variable_trait": most_variable,
        "least_variable_trait": least_variable,
        "persona_trait_coverage": persona_coverage,
        "average_traits_per_persona": statistics.mean([len(p.traits) for p in personas]),
        "trait_correlations": trait_correlations
    }


def calculate_correlation(x_values: List[float], y_values: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0
    
    n = len(x_values)
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_x2 = sum(x * x for x in x_values)
    sum_y2 = sum(y * y for y in y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def calculate_persona_diversity(personas: List[Persona]) -> float:
    """
    Calculate diversity score for a collection of personas.
    
    Args:
        personas: List of personas to analyze
        
    Returns:
        Diversity score between 0.0 (no diversity) and 1.0 (maximum diversity)
    """
    if len(personas) <= 1:
        return 0.0
    
    # Calculate pairwise similarities
    similarities = []
    for i in range(len(personas)):
        for j in range(i + 1, len(personas)):
            similarity = calculate_persona_similarity(personas[i], personas[j])
            similarities.append(similarity)
    
    if not similarities:
        return 0.0
    
    # Diversity is inverse of average similarity
    avg_similarity = statistics.mean(similarities)
    diversity = 1.0 - avg_similarity
    
    return max(0.0, min(1.0, diversity))


def find_persona_clusters(personas: List[Persona], threshold: float = 0.8) -> List[List[str]]:
    """
    Find clusters of similar personas.
    
    Args:
        personas: List of personas to cluster
        threshold: Similarity threshold for clustering
        
    Returns:
        List of clusters (each cluster is a list of persona names)
    """
    clusters = []
    processed = set()
    
    for i, persona1 in enumerate(personas):
        if persona1.name in processed:
            continue
        
        # Start new cluster
        cluster = [persona1.name]
        processed.add(persona1.name)
        
        # Find similar personas
        for j, persona2 in enumerate(personas):
            if j != i and persona2.name not in processed:
                similarity = calculate_persona_similarity(persona1, persona2)
                if similarity >= threshold:
                    cluster.append(persona2.name)
                    processed.add(persona2.name)
        
        clusters.append(cluster)
    
    return clusters


def analyze_conversation_styles(personas: List[Persona]) -> Dict[str, Any]:
    """
    Analyze conversation style distribution and patterns.
    
    Args:
        personas: List of personas to analyze
        
    Returns:
        Analysis of conversation style usage
    """
    style_counts = Counter(persona.conversation_style for persona in personas)
    
    return {
        "total_personas": len(personas),
        "unique_styles": len(style_counts),
        "style_distribution": dict(style_counts),
        "most_common_style": style_counts.most_common(1)[0] if style_counts else None,
        "style_diversity": calculate_style_diversity(style_counts),
        "styles_per_persona": 1.0  # Each persona has one style
    }


def calculate_style_diversity(style_counts: Counter) -> float:
    """Calculate diversity of conversation styles using Shannon entropy."""
    total = sum(style_counts.values())
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in style_counts.values():
        if count > 0:
            probability = count / total
            entropy -= probability * math.log2(probability)
    
    # Normalize by maximum possible entropy
    max_entropy = math.log2(len(style_counts)) if len(style_counts) > 1 else 0
    diversity = entropy / max_entropy if max_entropy > 0 else 0
    
    return diversity


def generate_persona_recommendations(
    target_traits: Dict[str, float],
    available_personas: List[Persona],
    top_k: int = 5
) -> List[Tuple[str, float, str]]:
    """
    Recommend personas based on desired traits.
    
    Args:
        target_traits: Desired trait profile
        available_personas: Personas to choose from
        top_k: Number of recommendations to return
        
    Returns:
        List of (persona_name, match_score, reasoning) tuples
    """
    recommendations = []
    
    for persona in available_personas:
        # Calculate match score
        match_score = calculate_trait_match(target_traits, persona.traits)
        
        # Generate reasoning
        reasoning = generate_match_reasoning(target_traits, persona.traits)
        
        recommendations.append((persona.name, match_score, reasoning))
    
    # Sort by match score and return top K
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return recommendations[:top_k]


def calculate_trait_match(target_traits: Dict[str, float], persona_traits: Dict[str, float]) -> float:
    """Calculate how well persona traits match target traits."""
    if not target_traits:
        return 0.0
    
    total_score = 0.0
    total_weight = 0.0
    
    for trait, target_value in target_traits.items():
        persona_value = persona_traits.get(trait, 0.5)  # Default neutral
        
        # Calculate distance and convert to score
        distance = abs(target_value - persona_value)
        score = 1.0 - distance  # Closer = higher score
        
        # Weight by target trait importance (higher values = more important)
        weight = target_value
        
        total_score += score * weight
        total_weight += weight
    
    return total_score / total_weight if total_weight > 0 else 0.0


def generate_match_reasoning(target_traits: Dict[str, float], persona_traits: Dict[str, float]) -> str:
    """Generate human-readable reasoning for trait matching."""
    matches = []
    mismatches = []
    
    for trait, target_value in target_traits.items():
        persona_value = persona_traits.get(trait, 0.5)
        difference = abs(target_value - persona_value)
        
        if difference < 0.2:  # Close match
            matches.append(f"{trait} ({persona_value:.1f})")
        elif difference > 0.5:  # Significant mismatch
            mismatches.append(f"{trait} ({persona_value:.1f} vs {target_value:.1f} desired)")
    
    reasoning_parts = []
    if matches:
        reasoning_parts.append(f"Strong matches: {', '.join(matches)}")
    if mismatches:
        reasoning_parts.append(f"Gaps: {', '.join(mismatches)}")
    
    return "; ".join(reasoning_parts) if reasoning_parts else "General compatibility"


def analyze_persona_balance(persona: Persona) -> Dict[str, Any]:
    """
    Analyze balance and consistency of a persona's traits.
    
    Args:
        persona: Persona to analyze
        
    Returns:
        Analysis of persona balance and recommendations
    """
    traits = persona.traits
    
    if not traits:
        return {"error": "No traits to analyze"}
    
    trait_values = list(traits.values())
    
    analysis = {
        "trait_count": len(traits),
        "average_trait_strength": statistics.mean(trait_values),
        "trait_variance": statistics.variance(trait_values) if len(trait_values) > 1 else 0.0,
        "min_trait": min(trait_values),
        "max_trait": max(trait_values),
        "trait_range": max(trait_values) - min(trait_values),
        "extreme_traits": [],
        "moderate_traits": [],
        "weak_traits": [],
        "recommendations": []
    }
    
    # Categorize traits by strength
    for trait, value in traits.items():
        if value >= 0.8:
            analysis["extreme_traits"].append((trait, value))
        elif value <= 0.2:
            analysis["weak_traits"].append((trait, value))
        else:
            analysis["moderate_traits"].append((trait, value))
    
    # Generate balance recommendations
    if analysis["trait_variance"] > 0.3:
        analysis["recommendations"].append("Consider balancing extreme trait values for more consistency")
    
    if len(analysis["extreme_traits"]) > len(analysis["moderate_traits"]):
        analysis["recommendations"].append("Too many extreme traits may create an unrealistic personality")
    
    if analysis["average_trait_strength"] > 0.8:
        analysis["recommendations"].append("Very high trait averages may indicate an overpowered persona")
    elif analysis["average_trait_strength"] < 0.3:
        analysis["recommendations"].append("Low trait averages may result in a weak personality")
    
    return analysis


def calculate_persona_completeness(persona: Persona) -> Dict[str, Any]:
    """
    Calculate how complete a persona definition is.
    
    Args:
        persona: Persona to analyze
        
    Returns:
        Completeness analysis and score
    """
    completeness_factors = {
        "has_name": bool(persona.name and persona.name.strip()),
        "has_description": bool(persona.description and persona.description.strip()),
        "has_traits": bool(persona.traits),
        "sufficient_traits": len(persona.traits) >= 3,
        "has_conversation_style": bool(persona.conversation_style and persona.conversation_style != "neutral"),
        "has_emotional_baseline": bool(persona.emotional_baseline and persona.emotional_baseline != "calm"),
        "has_metadata": bool(persona.metadata)
    }
    
    # Calculate weighted score
    weights = {
        "has_name": 0.25,
        "has_description": 0.15,
        "has_traits": 0.20,
        "sufficient_traits": 0.15,
        "has_conversation_style": 0.10,
        "has_emotional_baseline": 0.10,
        "has_metadata": 0.05
    }
    
    weighted_score = sum(
        weights[factor] for factor, present in completeness_factors.items()
        if present
    )
    
    # Generate recommendations
    recommendations = []
    if not completeness_factors["has_description"]:
        recommendations.append("Add a description to clarify the persona's purpose")
    if not completeness_factors["sufficient_traits"]:
        recommendations.append("Add more traits to better define personality")
    if not completeness_factors["has_conversation_style"] or persona.conversation_style == "neutral":
        recommendations.append("Specify a conversation style to improve interactions")
    
    return {
        "completeness_score": weighted_score,
        "completeness_factors": completeness_factors,
        "recommendations": recommendations,
        "grade": get_completeness_grade(weighted_score)
    }


def get_completeness_grade(score: float) -> str:
    """Convert completeness score to letter grade."""
    if score >= 0.9:
        return "A"
    elif score >= 0.8:
        return "B"
    elif score >= 0.7:
        return "C"
    elif score >= 0.6:
        return "D"
    else:
        return "F"