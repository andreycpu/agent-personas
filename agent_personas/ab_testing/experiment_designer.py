"""
Experiment designer for creating controlled persona A/B tests.
"""

from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
import random
from datetime import datetime, timedelta

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """Types of persona experiments."""
    AB_TEST = "ab_test"  # Compare two personas
    MULTIVARIATE = "multivariate"  # Compare multiple variables
    SEQUENTIAL = "sequential"  # Test personas in sequence
    ADAPTIVE = "adaptive"  # Adaptive allocation based on performance
    FACTORIAL = "factorial"  # Test combinations of traits
    SPLIT_TEST = "split_test"  # Split traffic between personas
    COHORT = "cohort"  # Test with specific user cohorts


class ExperimentStatus(Enum):
    """Status of experiments."""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ANALYZING = "analyzing"


class AllocationStrategy(Enum):
    """Strategies for allocating users to test groups."""
    RANDOM = "random"
    BALANCED = "balanced"
    WEIGHTED = "weighted"
    ADAPTIVE = "adaptive"
    STRATIFIED = "stratified"


@dataclass
class TestGroup:
    """Defines a test group in an experiment."""
    id: str
    name: str
    persona: Persona
    allocation_weight: float = 1.0  # Relative weight for allocation
    target_sample_size: Optional[int] = None
    current_sample_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_allocation_ratio(self, total_weight: float) -> float:
        """Get the allocation ratio for this group."""
        return self.allocation_weight / total_weight if total_weight > 0 else 0.0


@dataclass 
class ExperimentMetric:
    """Defines a metric to track during experiments."""
    name: str
    description: str
    metric_type: str  # "counter", "gauge", "histogram", "rate"
    goal: str  # "maximize", "minimize", "target"
    target_value: Optional[float] = None
    primary: bool = False  # Primary metric for decision making
    collection_method: str = "automatic"  # "automatic", "manual", "calculated"
    aggregation_window: Optional[str] = None  # "session", "daily", "total"
    
    def __post_init__(self):
        """Validate metric configuration."""
        if self.goal == "target" and self.target_value is None:
            raise ValueError("Target value required when goal is 'target'")


@dataclass
class Experiment:
    """
    Defines a complete persona experiment.
    """
    id: str
    name: str
    description: str
    experiment_type: ExperimentType
    test_groups: List[TestGroup]
    metrics: List[ExperimentMetric]
    
    # Experiment parameters
    allocation_strategy: AllocationStrategy = AllocationStrategy.BALANCED
    min_sample_size_per_group: int = 100
    max_duration_days: int = 30
    confidence_level: float = 0.95
    statistical_power: float = 0.8
    min_effect_size: float = 0.05  # Minimum detectable effect
    
    # Control parameters
    traffic_allocation: float = 1.0  # Fraction of traffic to include
    user_filters: List[str] = field(default_factory=list)  # User filtering criteria
    context_filters: List[str] = field(default_factory=list)  # Context filtering
    
    # Status and metadata
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate experiment configuration."""
        self._validate_experiment()
    
    def _validate_experiment(self):
        """Validate experiment parameters."""
        if len(self.test_groups) < 2:
            raise ValueError("Experiment must have at least 2 test groups")
        
        if not self.metrics:
            raise ValueError("Experiment must have at least one metric")
        
        if not 0.5 <= self.confidence_level <= 0.99:
            raise ValueError("Confidence level must be between 0.5 and 0.99")
        
        if not 0.1 <= self.statistical_power <= 0.99:
            raise ValueError("Statistical power must be between 0.1 and 0.99")
        
        # Validate allocation weights
        total_weight = sum(group.allocation_weight for group in self.test_groups)
        if total_weight <= 0:
            raise ValueError("Total allocation weight must be positive")
        
        # Validate unique group IDs
        group_ids = [group.id for group in self.test_groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("Test group IDs must be unique")
        
        # Validate primary metrics
        primary_metrics = [metric for metric in self.metrics if metric.primary]
        if len(primary_metrics) != 1:
            raise ValueError("Experiment must have exactly one primary metric")
    
    def get_group_by_id(self, group_id: str) -> Optional[TestGroup]:
        """Get test group by ID."""
        for group in self.test_groups:
            if group.id == group_id:
                return group
        return None
    
    def get_primary_metric(self) -> Optional[ExperimentMetric]:
        """Get the primary metric for the experiment."""
        for metric in self.metrics:
            if metric.primary:
                return metric
        return None
    
    def calculate_required_sample_size(self) -> int:
        """Calculate required sample size for statistical significance."""
        # Simplified calculation - in practice would use proper statistical formulas
        primary_metric = self.get_primary_metric()
        if not primary_metric:
            return self.min_sample_size_per_group * len(self.test_groups)
        
        # Basic formula for sample size calculation
        # This is simplified - proper implementation would use statistical libraries
        z_alpha = 1.96 if self.confidence_level == 0.95 else 2.58  # for 95% or 99%
        z_beta = 0.84 if self.statistical_power == 0.8 else 1.28   # for 80% or 90%
        
        # Assumed baseline conversion rate and effect size
        baseline_rate = 0.1  # 10% baseline
        effect_size = self.min_effect_size
        
        numerator = 2 * ((z_alpha + z_beta) ** 2) * baseline_rate * (1 - baseline_rate)
        denominator = (effect_size ** 2)
        
        sample_size_per_group = int(numerator / denominator)
        
        return max(sample_size_per_group, self.min_sample_size_per_group)
    
    def get_allocation_ratios(self) -> Dict[str, float]:
        """Get allocation ratios for all test groups."""
        total_weight = sum(group.allocation_weight for group in self.test_groups)
        
        ratios = {}
        for group in self.test_groups:
            ratios[group.id] = group.get_allocation_ratio(total_weight)
        
        return ratios
    
    def is_ready_to_start(self) -> Tuple[bool, List[str]]:
        """Check if experiment is ready to start."""
        issues = []
        
        # Check experiment status
        if self.status != ExperimentStatus.READY:
            issues.append(f"Experiment status is {self.status.value}, must be 'ready'")
        
        # Check test groups have personas
        for group in self.test_groups:
            if not group.persona:
                issues.append(f"Test group {group.id} has no persona assigned")
        
        # Check metrics are properly defined
        for metric in self.metrics:
            if not metric.name:
                issues.append("All metrics must have names")
        
        return len(issues) == 0, issues
    
    def can_stop_early(self, current_results: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if experiment can be stopped early due to statistical significance."""
        # This would implement early stopping rules
        # For now, return False (no early stopping)
        return False, "Early stopping not implemented"


class ExperimentDesigner:
    """
    Designer for creating and configuring persona experiments.
    
    Provides tools for designing controlled experiments, calculating
    sample sizes, and setting up proper statistical testing frameworks.
    """
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.experiment_templates: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize common experiment templates
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize common experiment templates."""
        self.experiment_templates = {
            "basic_ab": {
                "name": "Basic A/B Test",
                "description": "Simple A/B test comparing two personas",
                "experiment_type": ExperimentType.AB_TEST,
                "allocation_strategy": AllocationStrategy.BALANCED,
                "metrics": [
                    {
                        "name": "user_satisfaction",
                        "description": "User satisfaction score",
                        "metric_type": "gauge",
                        "goal": "maximize",
                        "primary": True
                    },
                    {
                        "name": "engagement_rate",
                        "description": "User engagement rate",
                        "metric_type": "rate", 
                        "goal": "maximize",
                        "primary": False
                    }
                ]
            },
            
            "multivariate_traits": {
                "name": "Multivariate Trait Test",
                "description": "Test multiple trait combinations",
                "experiment_type": ExperimentType.MULTIVARIATE,
                "allocation_strategy": AllocationStrategy.BALANCED,
                "metrics": [
                    {
                        "name": "effectiveness_score",
                        "description": "Overall effectiveness score",
                        "metric_type": "gauge",
                        "goal": "maximize",
                        "primary": True
                    }
                ]
            },
            
            "adaptive_optimization": {
                "name": "Adaptive Persona Optimization",
                "description": "Adaptive test that allocates more traffic to better performing personas",
                "experiment_type": ExperimentType.ADAPTIVE,
                "allocation_strategy": AllocationStrategy.ADAPTIVE,
                "metrics": [
                    {
                        "name": "success_rate",
                        "description": "Task success rate",
                        "metric_type": "rate",
                        "goal": "maximize",
                        "primary": True
                    }
                ]
            }
        }
    
    def create_experiment_from_template(
        self,
        template_name: str,
        experiment_name: str,
        personas: List[Persona],
        **overrides
    ) -> Experiment:
        """Create an experiment from a template."""
        if template_name not in self.experiment_templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.experiment_templates[template_name].copy()
        
        # Apply overrides
        template.update(overrides)
        
        # Create test groups from personas
        test_groups = []
        for i, persona in enumerate(personas):
            group = TestGroup(
                id=f"group_{i+1}",
                name=f"Persona {persona.name}",
                persona=persona
            )
            test_groups.append(group)
        
        # Convert metric dictionaries to ExperimentMetric objects
        metrics = []
        for metric_data in template.get("metrics", []):
            metric = ExperimentMetric(**metric_data)
            metrics.append(metric)
        
        # Create experiment
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=experiment_name,
            description=template.get("description", ""),
            experiment_type=template.get("experiment_type", ExperimentType.AB_TEST),
            test_groups=test_groups,
            metrics=metrics,
            allocation_strategy=template.get("allocation_strategy", AllocationStrategy.BALANCED)
        )
        
        self.experiments[experiment.id] = experiment
        self.logger.info(f"Created experiment '{experiment_name}' from template '{template_name}'")
        
        return experiment
    
    def create_custom_experiment(
        self,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        personas: List[Persona],
        metrics: List[ExperimentMetric],
        **kwargs
    ) -> Experiment:
        """Create a custom experiment with specific parameters."""
        # Create test groups
        test_groups = []
        for i, persona in enumerate(personas):
            group = TestGroup(
                id=f"group_{i+1}",
                name=f"Group {i+1}: {persona.name}",
                persona=persona
            )
            test_groups.append(group)
        
        # Create experiment
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            experiment_type=experiment_type,
            test_groups=test_groups,
            metrics=metrics,
            **kwargs
        )
        
        self.experiments[experiment.id] = experiment
        self.logger.info(f"Created custom experiment '{name}'")
        
        return experiment
    
    def create_factorial_experiment(
        self,
        name: str,
        trait_variations: Dict[str, List[float]],
        base_persona: Persona,
        primary_metric: ExperimentMetric,
        **kwargs
    ) -> Experiment:
        """Create a factorial experiment testing trait combinations."""
        if not trait_variations:
            raise ValueError("At least one trait variation required")
        
        # Generate all combinations of trait values
        trait_names = list(trait_variations.keys())
        trait_value_lists = list(trait_variations.values())
        
        import itertools
        combinations = list(itertools.product(*trait_value_lists))
        
        if len(combinations) > 16:  # Limit combinations to prevent explosion
            self.logger.warning(f"Factorial experiment would create {len(combinations)} groups. Limiting to first 16.")
            combinations = combinations[:16]
        
        # Create test groups for each combination
        test_groups = []
        for i, combination in enumerate(combinations):
            # Create persona with trait combination
            variant_persona = Persona(
                name=f"{base_persona.name}_variant_{i+1}",
                description=f"Variant of {base_persona.name}",
                traits=base_persona.traits.copy(),
                conversation_style=base_persona.conversation_style,
                emotional_baseline=base_persona.emotional_baseline,
                metadata=base_persona.metadata.copy()
            )
            
            # Apply trait variations
            for trait_name, trait_value in zip(trait_names, combination):
                variant_persona.set_trait(trait_name, trait_value)
            
            # Create test group
            group_name = "_".join(f"{name}={value}" for name, value in zip(trait_names, combination))
            group = TestGroup(
                id=f"factorial_group_{i+1}",
                name=group_name,
                persona=variant_persona,
                metadata={"trait_combination": dict(zip(trait_names, combination))}
            )
            test_groups.append(group)
        
        # Create experiment
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            description=f"Factorial experiment testing {len(trait_names)} traits with {len(combinations)} combinations",
            experiment_type=ExperimentType.FACTORIAL,
            test_groups=test_groups,
            metrics=[primary_metric],
            **kwargs
        )
        
        experiment.metadata["trait_variations"] = trait_variations
        experiment.metadata["trait_names"] = trait_names
        
        self.experiments[experiment.id] = experiment
        self.logger.info(f"Created factorial experiment '{name}' with {len(combinations)} groups")
        
        return experiment
    
    def create_sequential_experiment(
        self,
        name: str,
        personas: List[Persona],
        phase_duration_days: int,
        metrics: List[ExperimentMetric],
        **kwargs
    ) -> Experiment:
        """Create a sequential experiment testing personas in phases."""
        # Create test groups with phase information
        test_groups = []
        for i, persona in enumerate(personas):
            group = TestGroup(
                id=f"sequential_group_{i+1}",
                name=f"Phase {i+1}: {persona.name}",
                persona=persona,
                metadata={"phase": i+1, "phase_duration_days": phase_duration_days}
            )
            test_groups.append(group)
        
        total_duration = len(personas) * phase_duration_days
        
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            description=f"Sequential experiment testing {len(personas)} personas over {total_duration} days",
            experiment_type=ExperimentType.SEQUENTIAL,
            test_groups=test_groups,
            metrics=metrics,
            max_duration_days=total_duration,
            allocation_strategy=AllocationStrategy.SEQUENTIAL,
            **kwargs
        )
        
        experiment.metadata["phase_duration_days"] = phase_duration_days
        experiment.metadata["total_phases"] = len(personas)
        
        self.experiments[experiment.id] = experiment
        self.logger.info(f"Created sequential experiment '{name}' with {len(personas)} phases")
        
        return experiment
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID."""
        return self.experiments.get(experiment_id)
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None
    ) -> List[Experiment]:
        """List experiments with optional filtering."""
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [exp for exp in experiments if exp.status == status]
        
        if experiment_type:
            experiments = [exp for exp in experiments if exp.experiment_type == experiment_type]
        
        return sorted(experiments, key=lambda e: e.created_at, reverse=True)
    
    def validate_experiment(self, experiment_id: str) -> Tuple[bool, List[str]]:
        """Validate an experiment configuration."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False, [f"Experiment {experiment_id} not found"]
        
        issues = []
        
        # Check basic configuration
        try:
            experiment._validate_experiment()
        except ValueError as e:
            issues.append(str(e))
        
        # Check personas are properly configured
        for group in experiment.test_groups:
            if not group.persona:
                issues.append(f"Group {group.id} has no persona")
            else:
                try:
                    group.persona.validate()
                except Exception as e:
                    issues.append(f"Group {group.id} persona invalid: {str(e)}")
        
        # Check sample size requirements
        required_sample_size = experiment.calculate_required_sample_size()
        if required_sample_size > 10000:  # Reasonable upper limit
            issues.append(f"Required sample size ({required_sample_size}) may be too large")
        
        # Check experiment duration
        if experiment.max_duration_days > 90:
            issues.append("Experiment duration over 90 days may be too long")
        
        return len(issues) == 0, issues
    
    def prepare_experiment(self, experiment_id: str) -> bool:
        """Prepare an experiment for running."""
        is_valid, issues = self.validate_experiment(experiment_id)
        
        if not is_valid:
            self.logger.error(f"Cannot prepare experiment {experiment_id}: {issues}")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.READY
        
        # Calculate and set target sample sizes
        required_size = experiment.calculate_required_sample_size()
        for group in experiment.test_groups:
            if not group.target_sample_size:
                group.target_sample_size = required_size
        
        self.logger.info(f"Prepared experiment {experiment_id} for running")
        return True
    
    def get_experiment_statistics(self) -> Dict[str, Any]:
        """Get statistics about all experiments."""
        experiments = list(self.experiments.values())
        
        if not experiments:
            return {"total_experiments": 0}
        
        # Status distribution
        status_counts = {}
        for experiment in experiments:
            status = experiment.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Type distribution
        type_counts = {}
        for experiment in experiments:
            exp_type = experiment.experiment_type.value
            type_counts[exp_type] = type_counts.get(exp_type, 0) + 1
        
        # Average group count
        avg_groups = sum(len(exp.test_groups) for exp in experiments) / len(experiments)
        
        return {
            "total_experiments": len(experiments),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "average_groups_per_experiment": round(avg_groups, 2),
            "available_templates": len(self.experiment_templates)
        }