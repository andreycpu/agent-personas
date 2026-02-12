"""
Comprehensive persona evaluation system for assessing persona quality and performance.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import math
import statistics
from datetime import datetime, timedelta

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class EvaluationDimension(Enum):
    """Dimensions for persona evaluation."""
    CONSISTENCY = "consistency"
    COHERENCE = "coherence"
    DISTINCTIVENESS = "distinctiveness"
    COMPLETENESS = "completeness"
    BEHAVIORAL_ALIGNMENT = "behavioral_alignment"
    EMOTIONAL_AUTHENTICITY = "emotional_authenticity"
    COMMUNICATION_EFFECTIVENESS = "communication_effectiveness"
    ADAPTABILITY = "adaptability"
    MEMORABILITY = "memorability"
    ENGAGEMENT = "engagement"


class EvaluationMethod(Enum):
    """Methods for evaluation."""
    AUTOMATED = "automated"
    HUMAN_RATING = "human_rating"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    COMPARATIVE = "comparative"
    LONGITUDINAL = "longitudinal"


@dataclass
class EvaluationResult:
    """Result of a persona evaluation."""
    dimension: EvaluationDimension
    score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    method: EvaluationMethod
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    evaluator_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate evaluation result."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics for a persona."""
    persona_id: str
    persona_name: str
    evaluation_date: datetime
    overall_score: float
    dimension_scores: Dict[EvaluationDimension, EvaluationResult] = field(default_factory=dict)
    comparative_rankings: Dict[str, int] = field(default_factory=dict)  # vs other personas
    historical_trend: List[float] = field(default_factory=list)  # score over time
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_weighted_score(self, weights: Optional[Dict[EvaluationDimension, float]] = None) -> float:
        """Calculate weighted overall score."""
        if not self.dimension_scores:
            return 0.0
        
        if weights is None:
            # Default weights
            weights = {
                EvaluationDimension.CONSISTENCY: 0.15,
                EvaluationDimension.COHERENCE: 0.15,
                EvaluationDimension.DISTINCTIVENESS: 0.10,
                EvaluationDimension.COMPLETENESS: 0.10,
                EvaluationDimension.BEHAVIORAL_ALIGNMENT: 0.15,
                EvaluationDimension.EMOTIONAL_AUTHENTICITY: 0.10,
                EvaluationDimension.COMMUNICATION_EFFECTIVENESS: 0.10,
                EvaluationDimension.ADAPTABILITY: 0.05,
                EvaluationDimension.MEMORABILITY: 0.05,
                EvaluationDimension.ENGAGEMENT: 0.05
            }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for dimension, result in self.dimension_scores.items():
            if dimension in weights:
                weight = weights[dimension]
                weighted_sum += result.score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def get_strength_areas(self, top_n: int = 3) -> List[Tuple[EvaluationDimension, float]]:
        """Get top strength areas."""
        sorted_scores = sorted(
            [(dim, result.score) for dim, result in self.dimension_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_scores[:top_n]
    
    def get_improvement_areas(self, bottom_n: int = 3) -> List[Tuple[EvaluationDimension, float]]:
        """Get areas needing improvement."""
        sorted_scores = sorted(
            [(dim, result.score) for dim, result in self.dimension_scores.items()],
            key=lambda x: x[1]
        )
        return sorted_scores[:bottom_n]


class PersonaEvaluator:
    """
    Comprehensive evaluator for assessing persona quality across multiple dimensions.
    
    Provides automated evaluation methods, comparative analysis, and
    detailed reporting for persona effectiveness and authenticity.
    """
    
    def __init__(self):
        self.evaluation_history: Dict[str, List[EvaluationMetrics]] = {}
        self.evaluation_functions = {
            EvaluationDimension.CONSISTENCY: self._evaluate_consistency,
            EvaluationDimension.COHERENCE: self._evaluate_coherence,
            EvaluationDimension.DISTINCTIVENESS: self._evaluate_distinctiveness,
            EvaluationDimension.COMPLETENESS: self._evaluate_completeness,
            EvaluationDimension.BEHAVIORAL_ALIGNMENT: self._evaluate_behavioral_alignment,
            EvaluationDimension.EMOTIONAL_AUTHENTICITY: self._evaluate_emotional_authenticity,
            EvaluationDimension.COMMUNICATION_EFFECTIVENESS: self._evaluate_communication_effectiveness,
            EvaluationDimension.ADAPTABILITY: self._evaluate_adaptability,
            EvaluationDimension.MEMORABILITY: self._evaluate_memorability,
            EvaluationDimension.ENGAGEMENT: self._evaluate_engagement
        }
        self.logger = logging.getLogger(__name__)
    
    def evaluate_persona(
        self,
        persona: Persona,
        dimensions: Optional[List[EvaluationDimension]] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> EvaluationMetrics:
        """
        Perform comprehensive evaluation of a persona.
        
        Args:
            persona: The persona to evaluate
            dimensions: Specific dimensions to evaluate (all if None)
            context_data: Additional context data for evaluation
            
        Returns:
            Complete evaluation metrics
        """
        if dimensions is None:
            dimensions = list(EvaluationDimension)
        
        if context_data is None:
            context_data = {}
        
        # Perform evaluations for each dimension
        dimension_scores = {}
        
        for dimension in dimensions:
            evaluation_function = self.evaluation_functions.get(dimension)
            if evaluation_function:
                try:
                    result = evaluation_function(persona, context_data)
                    dimension_scores[dimension] = result
                    self.logger.debug(f"Evaluated {dimension.value}: {result.score}")
                except Exception as e:
                    self.logger.error(f"Error evaluating {dimension.value}: {e}")
                    # Create a low-confidence neutral result
                    dimension_scores[dimension] = EvaluationResult(
                        dimension=dimension,
                        score=0.5,
                        confidence=0.1,
                        method=EvaluationMethod.AUTOMATED,
                        details={"error": str(e)}
                    )
        
        # Calculate overall score
        overall_score = sum(result.score for result in dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0.0
        
        # Create evaluation metrics
        metrics = EvaluationMetrics(
            persona_id=persona.name,  # Using name as ID for simplicity
            persona_name=persona.name,
            evaluation_date=datetime.now(),
            overall_score=overall_score,
            dimension_scores=dimension_scores
        )
        
        # Generate recommendations
        metrics.recommendations = self._generate_recommendations(metrics)
        
        # Store in history
        if persona.name not in self.evaluation_history:
            self.evaluation_history[persona.name] = []
        self.evaluation_history[persona.name].append(metrics)
        
        # Update historical trend
        scores = [m.overall_score for m in self.evaluation_history[persona.name]]
        metrics.historical_trend = scores
        
        self.logger.info(f"Completed evaluation of persona '{persona.name}' with overall score: {overall_score:.3f}")
        return metrics
    
    def _evaluate_consistency(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate persona consistency."""
        # Check trait consistency (no contradictory traits)
        trait_conflicts = self._detect_trait_conflicts(persona.traits)
        consistency_score = 1.0 - (len(trait_conflicts) * 0.1)  # Reduce score for each conflict
        
        # Check description-trait alignment
        description_alignment = self._check_description_trait_alignment(persona)
        
        # Combine scores
        final_score = (consistency_score + description_alignment) / 2
        
        return EvaluationResult(
            dimension=EvaluationDimension.CONSISTENCY,
            score=max(0.0, min(1.0, final_score)),
            confidence=0.8,
            method=EvaluationMethod.AUTOMATED,
            details={
                "trait_conflicts": trait_conflicts,
                "description_alignment": description_alignment,
                "trait_count": len(persona.traits)
            }
        )
    
    def _evaluate_coherence(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate persona coherence (how well elements fit together)."""
        # Check trait clustering (related traits should have similar values)
        trait_coherence = self._analyze_trait_coherence(persona.traits)
        
        # Check style-trait alignment
        style_coherence = self._check_style_coherence(persona)
        
        # Check emotional baseline alignment
        emotional_coherence = self._check_emotional_coherence(persona)
        
        overall_coherence = (trait_coherence + style_coherence + emotional_coherence) / 3
        
        return EvaluationResult(
            dimension=EvaluationDimension.COHERENCE,
            score=overall_coherence,
            confidence=0.75,
            method=EvaluationMethod.AUTOMATED,
            details={
                "trait_coherence": trait_coherence,
                "style_coherence": style_coherence,
                "emotional_coherence": emotional_coherence
            }
        )
    
    def _evaluate_distinctiveness(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate how distinctive/unique the persona is."""
        # Check trait uniqueness (not all common values)
        trait_uniqueness = self._analyze_trait_uniqueness(persona.traits)
        
        # Check description uniqueness
        description_uniqueness = self._analyze_description_uniqueness(persona.description)
        
        # Check for distinctive combinations
        combination_uniqueness = self._analyze_trait_combinations(persona.traits)
        
        distinctiveness_score = (trait_uniqueness + description_uniqueness + combination_uniqueness) / 3
        
        return EvaluationResult(
            dimension=EvaluationDimension.DISTINCTIVENESS,
            score=distinctiveness_score,
            confidence=0.7,
            method=EvaluationMethod.AUTOMATED,
            details={
                "trait_uniqueness": trait_uniqueness,
                "description_uniqueness": description_uniqueness,
                "combination_uniqueness": combination_uniqueness
            }
        )
    
    def _evaluate_completeness(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate persona completeness."""
        completeness_factors = []
        
        # Check for core personality dimensions
        big_five_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        big_five_coverage = sum(1 for trait in big_five_traits if any(t.lower().startswith(trait[:4]) for t in persona.traits.keys()))
        completeness_factors.append(big_five_coverage / len(big_five_traits))
        
        # Check trait count (more traits generally = more complete)
        trait_completeness = min(1.0, len(persona.traits) / 10)  # Ideal around 10 traits
        completeness_factors.append(trait_completeness)
        
        # Check description quality
        description_completeness = min(1.0, len(persona.description.split()) / 20)  # Ideal around 20 words
        completeness_factors.append(description_completeness)
        
        # Check metadata richness
        metadata_completeness = min(1.0, len(persona.metadata) / 5)  # Ideal around 5 metadata fields
        completeness_factors.append(metadata_completeness)
        
        overall_completeness = sum(completeness_factors) / len(completeness_factors)
        
        return EvaluationResult(
            dimension=EvaluationDimension.COMPLETENESS,
            score=overall_completeness,
            confidence=0.8,
            method=EvaluationMethod.AUTOMATED,
            details={
                "big_five_coverage": big_five_coverage,
                "trait_count": len(persona.traits),
                "description_length": len(persona.description.split()),
                "metadata_richness": len(persona.metadata)
            }
        )
    
    def _evaluate_behavioral_alignment(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate alignment between traits and expected behaviors."""
        # This would ideally use behavioral data from context
        behavioral_data = context.get("behavioral_data", {})
        
        if not behavioral_data:
            # Use trait-based heuristics
            alignment_score = self._estimate_behavioral_alignment_from_traits(persona.traits)
            confidence = 0.5  # Low confidence without actual behavioral data
        else:
            # Analyze actual behaviors vs expected behaviors
            alignment_score = self._analyze_behavior_trait_alignment(persona.traits, behavioral_data)
            confidence = 0.9
        
        return EvaluationResult(
            dimension=EvaluationDimension.BEHAVIORAL_ALIGNMENT,
            score=alignment_score,
            confidence=confidence,
            method=EvaluationMethod.BEHAVIORAL_ANALYSIS if behavioral_data else EvaluationMethod.AUTOMATED,
            details={
                "has_behavioral_data": bool(behavioral_data),
                "analyzed_behaviors": list(behavioral_data.keys()) if behavioral_data else []
            }
        )
    
    def _evaluate_emotional_authenticity(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate emotional authenticity of the persona."""
        # Check emotional baseline alignment with traits
        emotional_alignment = self._check_emotional_trait_alignment(persona)
        
        # Check emotional complexity (realistic emotional range)
        emotional_complexity = self._analyze_emotional_complexity(persona)
        
        # Check for emotional contradictions
        emotional_consistency = self._check_emotional_consistency(persona)
        
        authenticity_score = (emotional_alignment + emotional_complexity + emotional_consistency) / 3
        
        return EvaluationResult(
            dimension=EvaluationDimension.EMOTIONAL_AUTHENTICITY,
            score=authenticity_score,
            confidence=0.75,
            method=EvaluationMethod.AUTOMATED,
            details={
                "emotional_baseline": persona.emotional_baseline,
                "emotional_alignment": emotional_alignment,
                "emotional_complexity": emotional_complexity,
                "emotional_consistency": emotional_consistency
            }
        )
    
    def _evaluate_communication_effectiveness(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate communication effectiveness."""
        communication_data = context.get("communication_data", {})
        
        if communication_data:
            # Analyze actual communication patterns
            effectiveness_score = self._analyze_communication_patterns(communication_data)
            confidence = 0.9
        else:
            # Estimate from conversation style and traits
            effectiveness_score = self._estimate_communication_effectiveness(persona)
            confidence = 0.6
        
        return EvaluationResult(
            dimension=EvaluationDimension.COMMUNICATION_EFFECTIVENESS,
            score=effectiveness_score,
            confidence=confidence,
            method=EvaluationMethod.AUTOMATED,
            details={
                "conversation_style": persona.conversation_style,
                "has_communication_data": bool(communication_data)
            }
        )
    
    def _evaluate_adaptability(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate persona adaptability."""
        # Check trait balance (not too extreme in any direction)
        trait_balance = self._analyze_trait_balance(persona.traits)
        
        # Check for adaptability-related traits
        adaptability_traits = ["flexible", "adaptable", "open_minded", "curious", "tolerant"]
        adaptability_score = sum(persona.get_trait(trait) for trait in adaptability_traits) / len(adaptability_traits)
        
        overall_adaptability = (trait_balance + adaptability_score) / 2
        
        return EvaluationResult(
            dimension=EvaluationDimension.ADAPTABILITY,
            score=overall_adaptability,
            confidence=0.7,
            method=EvaluationMethod.AUTOMATED,
            details={
                "trait_balance": trait_balance,
                "adaptability_traits": {trait: persona.get_trait(trait) for trait in adaptability_traits}
            }
        )
    
    def _evaluate_memorability(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate how memorable the persona is."""
        # Check for distinctive features
        memorable_traits = self._identify_memorable_traits(persona.traits)
        
        # Check description memorability
        description_memorability = self._analyze_description_memorability(persona.description)
        
        # Check for unique combinations
        unique_combinations = self._find_unique_trait_combinations(persona.traits)
        
        memorability_score = (len(memorable_traits) / 10 + description_memorability + unique_combinations) / 3
        
        return EvaluationResult(
            dimension=EvaluationDimension.MEMORABILITY,
            score=min(1.0, memorability_score),
            confidence=0.65,
            method=EvaluationMethod.AUTOMATED,
            details={
                "memorable_traits": memorable_traits,
                "description_memorability": description_memorability,
                "unique_combinations": unique_combinations
            }
        )
    
    def _evaluate_engagement(self, persona: Persona, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate persona engagement potential."""
        engagement_data = context.get("engagement_data", {})
        
        if engagement_data:
            # Use actual engagement metrics
            engagement_score = self._analyze_engagement_metrics(engagement_data)
            confidence = 0.95
        else:
            # Estimate from traits and style
            engagement_score = self._estimate_engagement_potential(persona)
            confidence = 0.6
        
        return EvaluationResult(
            dimension=EvaluationDimension.ENGAGEMENT,
            score=engagement_score,
            confidence=confidence,
            method=EvaluationMethod.AUTOMATED,
            details={
                "conversation_style": persona.conversation_style,
                "has_engagement_data": bool(engagement_data),
                "estimated_engagement_factors": self._get_engagement_factors(persona)
            }
        )
    
    # Helper methods for specific evaluations
    
    def _detect_trait_conflicts(self, traits: Dict[str, float]) -> List[str]:
        """Detect conflicting traits."""
        conflicts = []
        
        # Define conflicting trait pairs
        conflict_pairs = [
            ("introverted", "extroverted"),
            ("calm", "anxious"),
            ("organized", "chaotic"),
            ("confident", "insecure"),
            ("trusting", "suspicious"),
            ("optimistic", "pessimistic")
        ]
        
        for trait1, trait2 in conflict_pairs:
            val1 = traits.get(trait1, 0)
            val2 = traits.get(trait2, 0)
            
            # Both traits are significantly high
            if val1 > 0.6 and val2 > 0.6:
                conflicts.append(f"{trait1} vs {trait2}")
        
        return conflicts
    
    def _check_description_trait_alignment(self, persona: Persona) -> float:
        """Check how well description aligns with traits."""
        description_lower = persona.description.lower()
        
        # Simple keyword matching
        alignment_score = 0.0
        total_traits = len(persona.traits)
        
        if total_traits == 0:
            return 0.5  # Neutral if no traits
        
        matched_traits = 0
        for trait_name, trait_value in persona.traits.items():
            if trait_value > 0.5:  # Only check significant traits
                # Look for trait or related words in description
                trait_words = [trait_name.lower(), trait_name.replace("_", " ").lower()]
                
                if any(word in description_lower for word in trait_words):
                    matched_traits += 1
        
        return matched_traits / total_traits if total_traits > 0 else 0.5
    
    def _analyze_trait_coherence(self, traits: Dict[str, float]) -> float:
        """Analyze how coherently traits cluster together."""
        # Group related traits and check for similar values
        trait_groups = {
            "social": ["friendly", "outgoing", "social", "extroverted", "charismatic"],
            "analytical": ["analytical", "logical", "systematic", "precise", "methodical"],
            "emotional": ["empathetic", "emotional", "compassionate", "sensitive", "caring"],
            "creative": ["creative", "imaginative", "artistic", "innovative", "original"],
            "stable": ["calm", "stable", "patient", "reliable", "consistent"]
        }
        
        coherence_scores = []
        
        for group_name, group_traits in trait_groups.items():
            group_values = [traits.get(trait, 0) for trait in group_traits if trait in traits]
            
            if len(group_values) > 1:
                # Calculate variance (lower variance = higher coherence)
                variance = statistics.variance(group_values)
                coherence = 1.0 - min(1.0, variance)  # Convert variance to coherence score
                coherence_scores.append(coherence)
        
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.7
    
    def _check_style_coherence(self, persona: Persona) -> float:
        """Check coherence between conversation style and traits."""
        style = persona.conversation_style.lower()
        traits = persona.traits
        
        # Define expected traits for different styles
        style_trait_expectations = {
            "professional": {"formal": 0.7, "precise": 0.6, "reliable": 0.7},
            "friendly": {"friendly": 0.8, "warm": 0.7, "approachable": 0.6},
            "analytical": {"analytical": 0.8, "logical": 0.7, "methodical": 0.6},
            "creative": {"creative": 0.8, "imaginative": 0.7, "original": 0.6},
            "supportive": {"supportive": 0.8, "empathetic": 0.7, "caring": 0.6}
        }
        
        expected_traits = {}
        for style_key, style_traits in style_trait_expectations.items():
            if style_key in style:
                expected_traits.update(style_traits)
        
        if not expected_traits:
            return 0.7  # Neutral for unknown styles
        
        # Check alignment
        alignment_scores = []
        for expected_trait, expected_value in expected_traits.items():
            actual_value = traits.get(expected_trait, 0)
            # Score based on how close actual is to expected
            alignment = 1.0 - abs(actual_value - expected_value)
            alignment_scores.append(alignment)
        
        return sum(alignment_scores) / len(alignment_scores)
    
    def _check_emotional_coherence(self, persona: Persona) -> float:
        """Check coherence of emotional baseline with traits."""
        baseline = persona.emotional_baseline.lower()
        traits = persona.traits
        
        # Expected traits for emotional baselines
        baseline_expectations = {
            "calm": {"calm": 0.8, "stable": 0.7, "patient": 0.6},
            "enthusiastic": {"enthusiastic": 0.8, "energetic": 0.7, "optimistic": 0.6},
            "serious": {"serious": 0.7, "focused": 0.6, "professional": 0.6},
            "compassionate": {"compassionate": 0.8, "empathetic": 0.7, "caring": 0.6}
        }
        
        expected_traits = {}
        for baseline_key, baseline_traits in baseline_expectations.items():
            if baseline_key in baseline:
                expected_traits.update(baseline_traits)
        
        if not expected_traits:
            return 0.7  # Neutral for unknown baselines
        
        alignment_scores = []
        for expected_trait, expected_value in expected_traits.items():
            actual_value = traits.get(expected_trait, 0)
            alignment = 1.0 - abs(actual_value - expected_value)
            alignment_scores.append(alignment)
        
        return sum(alignment_scores) / len(alignment_scores)
    
    def _generate_recommendations(self, metrics: EvaluationMetrics) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        # Get improvement areas
        improvement_areas = metrics.get_improvement_areas(3)
        
        for dimension, score in improvement_areas:
            if score < 0.5:
                if dimension == EvaluationDimension.CONSISTENCY:
                    recommendations.append("Review traits for conflicts and ensure description aligns with personality")
                elif dimension == EvaluationDimension.COHERENCE:
                    recommendations.append("Group related traits with similar values for better coherence")
                elif dimension == EvaluationDimension.DISTINCTIVENESS:
                    recommendations.append("Add unique trait combinations or distinctive characteristics")
                elif dimension == EvaluationDimension.COMPLETENESS:
                    recommendations.append("Add more traits and expand description for completeness")
                elif dimension == EvaluationDimension.BEHAVIORAL_ALIGNMENT:
                    recommendations.append("Collect behavioral data to verify trait-behavior alignment")
                elif dimension == EvaluationDimension.EMOTIONAL_AUTHENTICITY:
                    recommendations.append("Ensure emotional baseline matches personality traits")
        
        # General recommendations based on overall score
        if metrics.overall_score < 0.6:
            recommendations.append("Consider major revision of persona structure and traits")
        elif metrics.overall_score < 0.75:
            recommendations.append("Fine-tune specific dimensions to improve overall effectiveness")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def compare_personas(self, personas: List[Persona]) -> Dict[str, Any]:
        """Compare multiple personas across evaluation dimensions."""
        if len(personas) < 2:
            raise ValueError("At least 2 personas required for comparison")
        
        # Evaluate all personas
        evaluations = {}
        for persona in personas:
            metrics = self.evaluate_persona(persona)
            evaluations[persona.name] = metrics
        
        # Generate comparative analysis
        comparison_results = {
            "persona_count": len(personas),
            "evaluation_date": datetime.now(),
            "overall_rankings": [],
            "dimension_leaders": {},
            "relative_strengths": {},
            "similarity_matrix": {}
        }
        
        # Overall rankings
        ranked_personas = sorted(
            evaluations.items(),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        for rank, (persona_name, metrics) in enumerate(ranked_personas, 1):
            comparison_results["overall_rankings"].append({
                "rank": rank,
                "persona": persona_name,
                "score": metrics.overall_score
            })
        
        # Dimension leaders
        for dimension in EvaluationDimension:
            dimension_scores = []
            for persona_name, metrics in evaluations.items():
                if dimension in metrics.dimension_scores:
                    dimension_scores.append((persona_name, metrics.dimension_scores[dimension].score))
            
            if dimension_scores:
                leader = max(dimension_scores, key=lambda x: x[1])
                comparison_results["dimension_leaders"][dimension.value] = {
                    "persona": leader[0],
                    "score": leader[1]
                }
        
        return comparison_results
    
    def get_evaluation_summary(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """Get evaluation summary for a specific persona."""
        if persona_name not in self.evaluation_history:
            return None
        
        evaluations = self.evaluation_history[persona_name]
        latest = evaluations[-1]
        
        return {
            "persona_name": persona_name,
            "latest_score": latest.overall_score,
            "evaluation_count": len(evaluations),
            "trend": "improving" if len(evaluations) > 1 and latest.overall_score > evaluations[-2].overall_score else "stable",
            "strengths": [dim.value for dim, score in latest.get_strength_areas()],
            "improvements_needed": [dim.value for dim, score in latest.get_improvement_areas()],
            "recommendations": latest.recommendations,
            "last_evaluated": latest.evaluation_date
        }