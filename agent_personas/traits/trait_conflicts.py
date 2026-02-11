"""
Trait conflict resolution system.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .trait import Trait


class ConflictType(Enum):
    """Types of trait conflicts."""
    MUTUAL_EXCLUSION = "mutual_exclusion"
    DEPENDENCY_VIOLATION = "dependency_violation"
    STRENGTH_OVERFLOW = "strength_overflow"
    VALUE_CONSTRAINT = "value_constraint"


@dataclass
class TraitConflict:
    """Represents a conflict between traits."""
    conflict_type: ConflictType
    traits_involved: List[str]
    current_values: Dict[str, float]
    description: str
    severity: float  # 0.0-1.0, higher = more severe
    suggested_resolution: Optional[Dict[str, float]] = None


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving trait conflicts."""
    PROPORTIONAL_REDUCTION = "proportional_reduction"
    PRIORITY_BASED = "priority_based"
    COMPROMISE = "compromise"
    STRONGEST_WINS = "strongest_wins"
    WEAKEST_LOSES = "weakest_loses"


class TraitConflictResolver:
    """
    Resolves conflicts between trait values using various strategies.
    """
    
    def __init__(self):
        self.trait_priorities: Dict[str, float] = {}
        self.resolution_history: List[Dict[str, Any]] = []
        
    def set_trait_priority(self, trait_name: str, priority: float) -> None:
        """Set priority for a trait (0.0-1.0, higher = more important)."""
        self.trait_priorities[trait_name] = max(0.0, min(1.0, priority))
        
    def get_trait_priority(self, trait_name: str) -> float:
        """Get priority for a trait (default 0.5)."""
        return self.trait_priorities.get(trait_name, 0.5)
        
    def detect_conflicts(
        self,
        trait_values: Dict[str, float],
        mutual_exclusions: List[Set[str]],
        dependencies: Dict[str, List[str]],
        max_total_strength: Optional[float] = None
    ) -> List[TraitConflict]:
        """
        Detect all types of conflicts in trait values.
        
        Args:
            trait_values: Current trait values
            mutual_exclusions: Sets of mutually exclusive traits
            dependencies: Trait dependencies
            max_total_strength: Maximum allowed total strength
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check mutual exclusions
        for exclusion_set in mutual_exclusions:
            high_traits = [
                trait for trait in exclusion_set
                if trait_values.get(trait, 0) > 0.7
            ]
            
            if len(high_traits) > 1:
                severity = min(trait_values.get(trait, 0) for trait in high_traits)
                conflict = TraitConflict(
                    conflict_type=ConflictType.MUTUAL_EXCLUSION,
                    traits_involved=high_traits,
                    current_values={t: trait_values.get(t, 0) for t in high_traits},
                    description=f"Mutually exclusive traits: {', '.join(high_traits)}",
                    severity=severity
                )
                conflicts.append(conflict)
        
        # Check dependencies
        for trait, required_traits in dependencies.items():
            trait_value = trait_values.get(trait, 0)
            if trait_value > 0.3:  # Trait is present
                for required in required_traits:
                    required_value = trait_values.get(required, 0)
                    if required_value < 0.3:  # Required trait is absent
                        severity = trait_value - required_value
                        conflict = TraitConflict(
                            conflict_type=ConflictType.DEPENDENCY_VIOLATION,
                            traits_involved=[trait, required],
                            current_values={trait: trait_value, required: required_value},
                            description=f"Trait '{trait}' requires '{required}'",
                            severity=severity
                        )
                        conflicts.append(conflict)
        
        # Check total strength overflow
        if max_total_strength is not None:
            total_strength = sum(trait_values.values())
            if total_strength > max_total_strength:
                overflow = total_strength - max_total_strength
                conflict = TraitConflict(
                    conflict_type=ConflictType.STRENGTH_OVERFLOW,
                    traits_involved=list(trait_values.keys()),
                    current_values=trait_values.copy(),
                    description=f"Total strength {total_strength:.2f} exceeds limit {max_total_strength}",
                    severity=overflow / max_total_strength
                )
                conflicts.append(conflict)
        
        return conflicts
        
    def resolve_conflict(
        self,
        conflict: TraitConflict,
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PROPORTIONAL_REDUCTION
    ) -> Dict[str, float]:
        """
        Resolve a single conflict using the specified strategy.
        
        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy to use
            
        Returns:
            Adjusted trait values
        """
        if strategy == ConflictResolutionStrategy.PROPORTIONAL_REDUCTION:
            return self._resolve_proportional_reduction(conflict)
        elif strategy == ConflictResolutionStrategy.PRIORITY_BASED:
            return self._resolve_priority_based(conflict)
        elif strategy == ConflictResolutionStrategy.COMPROMISE:
            return self._resolve_compromise(conflict)
        elif strategy == ConflictResolutionStrategy.STRONGEST_WINS:
            return self._resolve_strongest_wins(conflict)
        elif strategy == ConflictResolutionStrategy.WEAKEST_LOSES:
            return self._resolve_weakest_loses(conflict)
        else:
            return conflict.current_values.copy()
            
    def resolve_all_conflicts(
        self,
        trait_values: Dict[str, float],
        conflicts: List[TraitConflict],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PROPORTIONAL_REDUCTION
    ) -> Dict[str, float]:
        """
        Resolve all conflicts in order of severity.
        
        Args:
            trait_values: Original trait values
            conflicts: List of conflicts to resolve
            strategy: Resolution strategy
            
        Returns:
            Resolved trait values
        """
        resolved_values = trait_values.copy()
        
        # Sort conflicts by severity (highest first)
        sorted_conflicts = sorted(conflicts, key=lambda c: c.severity, reverse=True)
        
        resolution_steps = []
        
        for conflict in sorted_conflicts:
            # Update conflict with current values
            updated_conflict = TraitConflict(
                conflict_type=conflict.conflict_type,
                traits_involved=conflict.traits_involved,
                current_values={t: resolved_values.get(t, 0) for t in conflict.traits_involved},
                description=conflict.description,
                severity=conflict.severity
            )
            
            # Resolve the conflict
            adjusted_values = self.resolve_conflict(updated_conflict, strategy)
            
            # Apply adjustments
            for trait_name, new_value in adjusted_values.items():
                if trait_name in resolved_values:
                    resolved_values[trait_name] = new_value
                    
            resolution_steps.append({
                "conflict": updated_conflict,
                "strategy": strategy.value,
                "adjustments": adjusted_values
            })
        
        # Record resolution history
        self.resolution_history.append({
            "original_values": trait_values,
            "conflicts": [c.description for c in conflicts],
            "resolution_steps": resolution_steps,
            "final_values": resolved_values
        })
        
        return resolved_values
        
    def _resolve_proportional_reduction(self, conflict: TraitConflict) -> Dict[str, float]:
        """Resolve by proportionally reducing all involved traits."""
        adjusted = conflict.current_values.copy()
        
        if conflict.conflict_type == ConflictType.STRENGTH_OVERFLOW:
            # Calculate reduction factor
            total = sum(adjusted.values())
            # Assuming max_total_strength is encoded in description
            try:
                max_strength = float(conflict.description.split("limit ")[1])
                reduction_factor = max_strength / total
                for trait in adjusted:
                    adjusted[trait] *= reduction_factor
            except:
                # Fallback: reduce by 20%
                for trait in adjusted:
                    adjusted[trait] *= 0.8
                    
        elif conflict.conflict_type == ConflictType.MUTUAL_EXCLUSION:
            # Reduce all traits by severity factor
            reduction = 1.0 - (conflict.severity * 0.5)
            for trait in adjusted:
                adjusted[trait] *= reduction
                
        return adjusted
        
    def _resolve_priority_based(self, conflict: TraitConflict) -> Dict[str, float]:
        """Resolve based on trait priorities."""
        adjusted = conflict.current_values.copy()
        
        # Sort traits by priority (highest first)
        trait_priorities = [
            (trait, self.get_trait_priority(trait))
            for trait in conflict.traits_involved
        ]
        trait_priorities.sort(key=lambda x: x[1], reverse=True)
        
        if conflict.conflict_type == ConflictType.MUTUAL_EXCLUSION:
            # Keep highest priority trait, reduce others
            for i, (trait, _) in enumerate(trait_priorities):
                if i == 0:  # Highest priority
                    continue
                else:
                    adjusted[trait] = min(adjusted[trait], 0.6)
                    
        return adjusted
        
    def _resolve_compromise(self, conflict: TraitConflict) -> Dict[str, float]:
        """Resolve by finding a middle ground."""
        adjusted = conflict.current_values.copy()
        
        if conflict.conflict_type == ConflictType.MUTUAL_EXCLUSION:
            # Average the conflicting traits
            avg_value = sum(adjusted.values()) / len(adjusted)
            compromise_value = min(avg_value, 0.6)
            for trait in adjusted:
                adjusted[trait] = compromise_value
                
        elif conflict.conflict_type == ConflictType.DEPENDENCY_VIOLATION:
            # Boost required trait to minimum threshold
            trait, required = conflict.traits_involved
            adjusted[required] = max(adjusted.get(required, 0), 0.4)
            
        return adjusted
        
    def _resolve_strongest_wins(self, conflict: TraitConflict) -> Dict[str, float]:
        """Resolve by keeping the strongest trait."""
        adjusted = conflict.current_values.copy()
        
        if conflict.conflict_type == ConflictType.MUTUAL_EXCLUSION:
            # Find strongest trait
            strongest = max(adjusted, key=adjusted.get)
            for trait in adjusted:
                if trait != strongest:
                    adjusted[trait] = min(adjusted[trait], 0.4)
                    
        return adjusted
        
    def _resolve_weakest_loses(self, conflict: TraitConflict) -> Dict[str, float]:
        """Resolve by reducing the weakest trait."""
        adjusted = conflict.current_values.copy()
        
        if conflict.conflict_type == ConflictType.MUTUAL_EXCLUSION:
            # Find weakest trait
            weakest = min(adjusted, key=adjusted.get)
            adjusted[weakest] = min(adjusted[weakest], 0.3)
            
        return adjusted
        
    def get_resolution_history(self) -> List[Dict[str, Any]]:
        """Get history of conflict resolutions."""
        return self.resolution_history.copy()
        
    def clear_history(self) -> None:
        """Clear resolution history."""
        self.resolution_history.clear()