"""
Trait groups for organizing related traits.
"""

from typing import Dict, List, Set, Optional, Any
from .trait import Trait, TraitType


class TraitGroup:
    """
    Groups related traits together with shared constraints and relationships.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        traits: Optional[List[Trait]] = None,
        max_total_strength: Optional[float] = None,
        mutual_exclusions: Optional[List[Set[str]]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize a trait group.
        
        Args:
            name: Group name
            description: Group description
            traits: List of traits in this group
            max_total_strength: Maximum combined strength for all traits
            mutual_exclusions: Sets of trait names that cannot be high together
            dependencies: Trait name -> list of required traits
        """
        self.name = name
        self.description = description
        self._traits: Dict[str, Trait] = {}
        self.max_total_strength = max_total_strength
        self.mutual_exclusions = mutual_exclusions or []
        self.dependencies = dependencies or {}
        
        if traits:
            for trait in traits:
                self.add_trait(trait)
                
    def add_trait(self, trait: Trait) -> None:
        """Add a trait to the group."""
        if trait.name in self._traits:
            raise ValueError(f"Trait '{trait.name}' already exists in group")
        self._traits[trait.name] = trait
        
    def remove_trait(self, trait_name: str) -> Optional[Trait]:
        """Remove a trait from the group."""
        return self._traits.pop(trait_name, None)
        
    def get_trait(self, trait_name: str) -> Optional[Trait]:
        """Get a trait by name."""
        return self._traits.get(trait_name)
        
    def has_trait(self, trait_name: str) -> bool:
        """Check if trait exists in group."""
        return trait_name in self._traits
        
    def list_traits(self) -> List[Trait]:
        """Get all traits in the group."""
        return list(self._traits.values())
        
    def list_trait_names(self) -> List[str]:
        """Get all trait names in the group."""
        return list(self._traits.keys())
        
    def validate_trait_values(self, trait_values: Dict[str, float]) -> List[str]:
        """
        Validate a set of trait values against group constraints.
        
        Args:
            trait_values: Dictionary of trait name -> value
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check individual trait value validity
        for trait_name, value in trait_values.items():
            if trait_name in self._traits:
                trait = self._traits[trait_name]
                if not trait.validate_value(value):
                    errors.append(
                        f"Invalid value {value} for trait '{trait_name}' "
                        f"(must be between {trait.min_value} and {trait.max_value})"
                    )
        
        # Check total strength constraint
        if self.max_total_strength is not None:
            relevant_values = {
                name: value for name, value in trait_values.items()
                if name in self._traits
            }
            total_strength = sum(relevant_values.values())
            if total_strength > self.max_total_strength:
                errors.append(
                    f"Total trait strength {total_strength:.2f} exceeds "
                    f"group maximum {self.max_total_strength}"
                )
        
        # Check mutual exclusions
        for exclusion_set in self.mutual_exclusions:
            high_traits = [
                name for name in exclusion_set
                if trait_values.get(name, 0) > 0.7  # High threshold
            ]
            if len(high_traits) > 1:
                errors.append(
                    f"Mutually exclusive traits cannot both be high: "
                    f"{', '.join(high_traits)}"
                )
        
        # Check dependencies
        for trait_name, required_traits in self.dependencies.items():
            if trait_values.get(trait_name, 0) > 0.3:  # If trait is present
                for required in required_traits:
                    if trait_values.get(required, 0) < 0.3:  # Required trait is low
                        errors.append(
                            f"Trait '{trait_name}' requires '{required}' to be present"
                        )
        
        return errors
        
    def suggest_adjustments(self, trait_values: Dict[str, float]) -> Dict[str, float]:
        """
        Suggest adjusted trait values that satisfy group constraints.
        
        Args:
            trait_values: Current trait values
            
        Returns:
            Suggested adjusted values
        """
        adjusted = trait_values.copy()
        
        # Handle total strength constraint by proportional reduction
        if self.max_total_strength is not None:
            relevant_values = {
                name: value for name, value in adjusted.items()
                if name in self._traits
            }
            total_strength = sum(relevant_values.values())
            
            if total_strength > self.max_total_strength:
                scale_factor = self.max_total_strength / total_strength
                for name in relevant_values:
                    adjusted[name] = adjusted[name] * scale_factor
        
        # Handle mutual exclusions by reducing weaker traits
        for exclusion_set in self.mutual_exclusions:
            high_traits = [
                (name, adjusted.get(name, 0)) for name in exclusion_set
                if adjusted.get(name, 0) > 0.7
            ]
            
            if len(high_traits) > 1:
                # Keep the strongest, reduce others
                high_traits.sort(key=lambda x: x[1], reverse=True)
                for name, _ in high_traits[1:]:
                    adjusted[name] = min(adjusted[name], 0.6)
        
        return adjusted
        
    def get_trait_conflicts(self, trait_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Get detailed information about trait conflicts.
        
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # Check mutual exclusions
        for exclusion_set in self.mutual_exclusions:
            high_traits = [
                name for name in exclusion_set
                if trait_values.get(name, 0) > 0.7
            ]
            
            if len(high_traits) > 1:
                conflicts.append({
                    "type": "mutual_exclusion",
                    "traits": high_traits,
                    "description": f"Traits {', '.join(high_traits)} are mutually exclusive"
                })
        
        return conflicts
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "traits": [trait.to_dict() for trait in self._traits.values()],
            "max_total_strength": self.max_total_strength,
            "mutual_exclusions": [list(s) for s in self.mutual_exclusions],
            "dependencies": self.dependencies
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraitGroup":
        """Create group from dictionary."""
        traits = [Trait.from_dict(t) for t in data.get("traits", [])]
        exclusions = [set(s) for s in data.get("mutual_exclusions", [])]
        
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            traits=traits,
            max_total_strength=data.get("max_total_strength"),
            mutual_exclusions=exclusions,
            dependencies=data.get("dependencies", {})
        )
        
    def __len__(self) -> int:
        return len(self._traits)
        
    def __contains__(self, trait_name: str) -> bool:
        return trait_name in self._traits