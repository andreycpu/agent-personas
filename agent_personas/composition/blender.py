"""
Advanced persona blending system for creating composite personalities.
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import logging
from statistics import mean, median

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class BlendStrategy(Enum):
    """Strategies for blending persona traits."""
    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    DOMINANT = "dominant"
    HARMONIC_MEAN = "harmonic_mean"
    GEOMETRIC_MEAN = "geometric_mean"
    MIN_MAX = "min_max"
    SELECTIVE = "selective"
    EXPONENTIAL_DECAY = "exponential_decay"


@dataclass
class BlendConfig:
    """Configuration for persona blending operations."""
    strategy: BlendStrategy = BlendStrategy.WEIGHTED_AVERAGE
    weights: Optional[Dict[str, float]] = None
    trait_priorities: Optional[Dict[str, float]] = None
    preserve_dominant_traits: bool = True
    dominant_threshold: float = 0.8
    smoothing_factor: float = 0.1
    conflict_resolution: str = "average"  # "average", "max", "min", "first", "last"
    metadata_merge_strategy: str = "combine"  # "combine", "first", "last", "deepmerge"


class PersonaBlender:
    """
    Advanced blending system for combining multiple personas into composite personalities.
    
    Supports various mathematical blending strategies and sophisticated
    conflict resolution for creating coherent merged personas.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._strategy_functions = {
            BlendStrategy.AVERAGE: self._average_blend,
            BlendStrategy.WEIGHTED_AVERAGE: self._weighted_average_blend,
            BlendStrategy.DOMINANT: self._dominant_blend,
            BlendStrategy.HARMONIC_MEAN: self._harmonic_mean_blend,
            BlendStrategy.GEOMETRIC_MEAN: self._geometric_mean_blend,
            BlendStrategy.MIN_MAX: self._min_max_blend,
            BlendStrategy.SELECTIVE: self._selective_blend,
            BlendStrategy.EXPONENTIAL_DECAY: self._exponential_decay_blend
        }
    
    def blend_personas(
        self,
        personas: List[Persona],
        target_name: str,
        config: Optional[BlendConfig] = None
    ) -> Persona:
        """
        Blend multiple personas into a single composite persona.
        
        Args:
            personas: List of personas to blend
            target_name: Name for the resulting blended persona
            config: Blending configuration
        
        Returns:
            A new persona with blended characteristics
        """
        if len(personas) < 2:
            raise ValueError("At least 2 personas required for blending")
        
        if not config:
            config = BlendConfig()
        
        # Validate personas
        for persona in personas:
            if not isinstance(persona, Persona):
                raise TypeError("All items must be Persona instances")
        
        # Extract and blend traits
        blended_traits = self._blend_traits(personas, config)
        
        # Blend conversation styles
        blended_conversation_style = self._blend_conversation_styles(personas, config)
        
        # Blend emotional baselines
        blended_emotional_baseline = self._blend_emotional_baselines(personas, config)
        
        # Merge descriptions
        blended_description = self._blend_descriptions(personas)
        
        # Merge metadata
        blended_metadata = self._blend_metadata(personas, config)
        
        # Create the blended persona
        blended_persona = Persona(
            name=target_name,
            description=blended_description,
            traits=blended_traits,
            conversation_style=blended_conversation_style,
            emotional_baseline=blended_emotional_baseline,
            metadata=blended_metadata
        )
        
        # Add blend information to metadata
        blended_persona.metadata.update({
            "blend_source_personas": [p.name for p in personas],
            "blend_strategy": config.strategy.value,
            "blend_timestamp": blended_persona.created_at.isoformat(),
            "is_blended_persona": True
        })
        
        self.logger.info(f"Successfully blended {len(personas)} personas into '{target_name}'")
        return blended_persona
    
    def _blend_traits(self, personas: List[Persona], config: BlendConfig) -> Dict[str, float]:
        """Blend traits from multiple personas."""
        # Collect all unique traits
        all_traits = set()
        for persona in personas:
            all_traits.update(persona.traits.keys())
        
        # Get blend function
        blend_func = self._strategy_functions.get(config.strategy, self._weighted_average_blend)
        
        blended_traits = {}
        for trait in all_traits:
            values = [persona.get_trait(trait) for persona in personas]
            
            # Remove zero values if preserve_dominant_traits is True
            if config.preserve_dominant_traits:
                non_zero_values = [v for v in values if v > 0]
                if non_zero_values:
                    values = non_zero_values
            
            # Apply blending strategy
            blended_value = blend_func(values, config, trait)
            
            # Apply trait priority adjustments
            if config.trait_priorities and trait in config.trait_priorities:
                priority = config.trait_priorities[trait]
                blended_value = min(1.0, blended_value * priority)
            
            # Only include non-zero traits
            if blended_value > 0.01:  # Threshold to avoid noise
                blended_traits[trait] = round(blended_value, 3)
        
        return blended_traits
    
    def _average_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Simple arithmetic mean blending."""
        return mean(values) if values else 0.0
    
    def _weighted_average_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Weighted average blending."""
        if not values:
            return 0.0
        
        if config.weights:
            # Use provided weights
            weights = [config.weights.get(f"persona_{i}", 1.0) for i in range(len(values))]
        else:
            # Equal weights
            weights = [1.0] * len(values)
        
        if len(weights) != len(values):
            weights = [1.0] * len(values)  # Fallback to equal weights
        
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def _dominant_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Use the highest value with smoothing."""
        if not values:
            return 0.0
        
        max_value = max(values)
        
        # If maximum value is above threshold, use it with slight smoothing
        if max_value >= config.dominant_threshold:
            # Smooth with mean of other values
            other_values = [v for v in values if v != max_value]
            if other_values:
                smoothing = mean(other_values) * config.smoothing_factor
                return min(1.0, max_value + smoothing)
            return max_value
        
        # Otherwise, use weighted average
        return self._weighted_average_blend(values, config, trait)
    
    def _harmonic_mean_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Harmonic mean blending (emphasizes lower values)."""
        if not values:
            return 0.0
        
        # Filter out zero values for harmonic mean
        non_zero_values = [v for v in values if v > 0]
        if not non_zero_values:
            return 0.0
        
        harmonic_sum = sum(1.0 / v for v in non_zero_values)
        return len(non_zero_values) / harmonic_sum
    
    def _geometric_mean_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Geometric mean blending (balanced, but emphasizes consistency)."""
        if not values:
            return 0.0
        
        # Filter out zero values
        non_zero_values = [v for v in values if v > 0]
        if not non_zero_values:
            return 0.0
        
        product = 1.0
        for value in non_zero_values:
            product *= value
        
        return product ** (1.0 / len(non_zero_values))
    
    def _min_max_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Blend using min-max normalization and averaging."""
        if not values:
            return 0.0
        
        min_val, max_val = min(values), max(values)
        
        if max_val == min_val:
            return max_val
        
        # Normalize and then average
        normalized = [(v - min_val) / (max_val - min_val) for v in values]
        avg_normalized = mean(normalized)
        
        # Scale back to original range
        return min_val + avg_normalized * (max_val - min_val)
    
    def _selective_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Selective blending based on trait priorities."""
        if not values:
            return 0.0
        
        # Use median for balance, but weight by priority if available
        if config.trait_priorities and trait in config.trait_priorities:
            priority = config.trait_priorities[trait]
            if priority > 0.8:
                return max(values)  # Use highest for high priority
            elif priority < 0.3:
                return min(values)  # Use lowest for low priority
        
        return median(values)
    
    def _exponential_decay_blend(self, values: List[float], config: BlendConfig, trait: str) -> float:
        """Exponential decay blending (recent values weighted more)."""
        if not values:
            return 0.0
        
        decay_factor = 0.7  # Higher values give more weight to later personas
        weights = [decay_factor ** (len(values) - i - 1) for i in range(len(values))]
        
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def _blend_conversation_styles(self, personas: List[Persona], config: BlendConfig) -> str:
        """Blend conversation styles from multiple personas."""
        styles = [p.conversation_style for p in personas]
        
        if config.conflict_resolution == "first":
            return styles[0]
        elif config.conflict_resolution == "last":
            return styles[-1]
        else:
            # Use most common style, or first if tie
            style_counts = {}
            for style in styles:
                style_counts[style] = style_counts.get(style, 0) + 1
            
            return max(style_counts.items(), key=lambda x: x[1])[0]
    
    def _blend_emotional_baselines(self, personas: List[Persona], config: BlendConfig) -> str:
        """Blend emotional baselines from multiple personas."""
        baselines = [p.emotional_baseline for p in personas]
        
        if config.conflict_resolution == "first":
            return baselines[0]
        elif config.conflict_resolution == "last":
            return baselines[-1]
        else:
            # Use most common baseline, or first if tie
            baseline_counts = {}
            for baseline in baselines:
                baseline_counts[baseline] = baseline_counts.get(baseline, 0) + 1
            
            return max(baseline_counts.items(), key=lambda x: x[1])[0]
    
    def _blend_descriptions(self, personas: List[Persona]) -> str:
        """Create a blended description from multiple personas."""
        descriptions = [p.description for p in personas if p.description.strip()]
        
        if not descriptions:
            return f"Blended persona created from {len(personas)} source personas"
        
        # Create a summary description
        if len(descriptions) == 1:
            return descriptions[0]
        
        # Extract key phrases and combine
        combined = f"Composite persona combining elements from {len(personas)} personalities: "
        
        # Take first sentence from each description
        sentences = []
        for desc in descriptions[:3]:  # Limit to first 3 to avoid too long descriptions
            first_sentence = desc.split('.')[0]
            if first_sentence and len(first_sentence) < 100:
                sentences.append(first_sentence)
        
        if sentences:
            combined += '. '.join(sentences) + '.'
        else:
            combined += 'Merged characteristics create a unique balanced personality.'
        
        return combined
    
    def _blend_metadata(self, personas: List[Persona], config: BlendConfig) -> Dict[str, Any]:
        """Merge metadata from multiple personas."""
        if config.metadata_merge_strategy == "first":
            return personas[0].metadata.copy()
        elif config.metadata_merge_strategy == "last":
            return personas[-1].metadata.copy()
        
        # Combine strategy (default)
        merged_metadata = {}
        
        for persona in personas:
            for key, value in persona.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
                elif isinstance(value, list) and isinstance(merged_metadata[key], list):
                    # Combine lists
                    merged_metadata[key].extend(value)
                elif isinstance(value, dict) and isinstance(merged_metadata[key], dict):
                    # Merge dictionaries
                    merged_metadata[key].update(value)
                # For other types, keep the first value
        
        # Add source information
        merged_metadata["source_personas"] = [p.name for p in personas]
        merged_metadata["blend_count"] = len(personas)
        
        return merged_metadata
    
    def analyze_blend_compatibility(self, personas: List[Persona]) -> Dict[str, Any]:
        """
        Analyze how well personas will blend together.
        
        Returns:
            Analysis report with compatibility scores and recommendations
        """
        if len(personas) < 2:
            return {"error": "At least 2 personas required for analysis"}
        
        # Calculate trait overlap
        all_traits = set()
        for persona in personas:
            all_traits.update(persona.traits.keys())
        
        trait_overlap_scores = []
        for i, persona1 in enumerate(personas):
            for persona2 in personas[i+1:]:
                common_traits = set(persona1.traits.keys()) & set(persona2.traits.keys())
                overlap_ratio = len(common_traits) / len(all_traits) if all_traits else 0
                trait_overlap_scores.append(overlap_ratio)
        
        # Calculate trait similarity
        similarity_scores = []
        for trait in all_traits:
            values = [p.get_trait(trait) for p in personas]
            non_zero_values = [v for v in values if v > 0]
            if len(non_zero_values) > 1:
                # Calculate variance (lower = more similar)
                mean_val = mean(non_zero_values)
                variance = sum((v - mean_val) ** 2 for v in non_zero_values) / len(non_zero_values)
                similarity = 1.0 - min(1.0, variance)  # Convert variance to similarity
                similarity_scores.append(similarity)
        
        # Overall compatibility score
        avg_overlap = mean(trait_overlap_scores) if trait_overlap_scores else 0
        avg_similarity = mean(similarity_scores) if similarity_scores else 0
        compatibility_score = (avg_overlap + avg_similarity) / 2
        
        # Identify potential conflicts
        conflicts = []
        for trait in all_traits:
            values = [p.get_trait(trait) for p in personas]
            non_zero_values = [v for v in values if v > 0]
            if len(non_zero_values) > 1:
                range_span = max(non_zero_values) - min(non_zero_values)
                if range_span > 0.6:  # Large difference in trait values
                    conflicts.append({
                        "trait": trait,
                        "range": range_span,
                        "values": dict(zip([p.name for p in personas], values))
                    })
        
        return {
            "compatibility_score": round(compatibility_score, 3),
            "trait_overlap": round(avg_overlap, 3),
            "trait_similarity": round(avg_similarity, 3),
            "total_unique_traits": len(all_traits),
            "potential_conflicts": conflicts,
            "recommended_strategies": self._get_blend_recommendations(compatibility_score, conflicts)
        }
    
    def _get_blend_recommendations(self, compatibility_score: float, conflicts: List[Dict]) -> List[str]:
        """Get blending strategy recommendations based on analysis."""
        recommendations = []
        
        if compatibility_score > 0.8:
            recommendations.append("High compatibility - AVERAGE or WEIGHTED_AVERAGE strategies recommended")
        elif compatibility_score > 0.6:
            recommendations.append("Moderate compatibility - SELECTIVE or DOMINANT strategies may work well")
        else:
            recommendations.append("Low compatibility - Consider HARMONIC_MEAN or careful SELECTIVE blending")
        
        if len(conflicts) > 3:
            recommendations.append("Many trait conflicts detected - use DOMINANT strategy with high threshold")
        
        if len(conflicts) == 0:
            recommendations.append("No major conflicts - any blending strategy should work well")
        
        return recommendations