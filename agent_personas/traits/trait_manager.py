"""
Trait manager for coordinating trait operations across personas.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import json
from pathlib import Path

from .trait import Trait, TraitType
from .trait_group import TraitGroup


class TraitManager:
    """
    Manages trait definitions, groups, and validation across the system.
    """
    
    def __init__(self):
        self._traits: Dict[str, Trait] = {}
        self._groups: Dict[str, TraitGroup] = {}
        self._trait_to_groups: Dict[str, Set[str]] = {}
        
        # Load default traits
        self._load_default_traits()
        
    def add_trait(self, trait: Trait) -> None:
        """Add a trait definition."""
        if trait.name in self._traits:
            raise ValueError(f"Trait '{trait.name}' already exists")
        self._traits[trait.name] = trait
        self._trait_to_groups[trait.name] = set()
        
    def get_trait(self, name: str) -> Optional[Trait]:
        """Get a trait definition by name."""
        return self._traits.get(name)
        
    def list_traits(self) -> List[Trait]:
        """Get all trait definitions."""
        return list(self._traits.values())
        
    def list_traits_by_type(self, trait_type: TraitType) -> List[Trait]:
        """Get traits of a specific type."""
        return [
            trait for trait in self._traits.values()
            if trait.trait_type == trait_type
        ]
        
    def add_group(self, group: TraitGroup) -> None:
        """Add a trait group."""
        if group.name in self._groups:
            raise ValueError(f"Group '{group.name}' already exists")
            
        # Validate that all traits in group exist
        for trait_name in group.list_trait_names():
            if trait_name not in self._traits:
                raise ValueError(f"Trait '{trait_name}' not found")
                
        self._groups[group.name] = group
        
        # Update trait-to-groups mapping
        for trait_name in group.list_trait_names():
            self._trait_to_groups[trait_name].add(group.name)
            
    def get_group(self, name: str) -> Optional[TraitGroup]:
        """Get a trait group by name."""
        return self._groups.get(name)
        
    def list_groups(self) -> List[TraitGroup]:
        """Get all trait groups."""
        return list(self._groups.values())
        
    def get_groups_for_trait(self, trait_name: str) -> List[TraitGroup]:
        """Get all groups containing a specific trait."""
        group_names = self._trait_to_groups.get(trait_name, set())
        return [self._groups[name] for name in group_names if name in self._groups]
        
    def validate_trait_values(
        self, 
        trait_values: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Validate trait values against all constraints.
        
        Args:
            trait_values: Dictionary of trait name -> value
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate individual traits
        for trait_name, value in trait_values.items():
            trait = self.get_trait(trait_name)
            if trait and not trait.validate_value(value):
                errors.append(
                    f"Invalid value {value} for trait '{trait_name}'"
                )
        
        # Validate against all relevant groups
        processed_groups = set()
        for trait_name in trait_values.keys():
            for group in self.get_groups_for_trait(trait_name):
                if group.name not in processed_groups:
                    group_errors = group.validate_trait_values(trait_values)
                    errors.extend(group_errors)
                    processed_groups.add(group.name)
        
        return len(errors) == 0, errors
        
    def suggest_trait_adjustments(
        self, 
        trait_values: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Suggest adjusted trait values that satisfy all constraints.
        
        Args:
            trait_values: Current trait values
            
        Returns:
            Suggested adjusted values
        """
        adjusted = trait_values.copy()
        
        # Apply group suggestions
        processed_groups = set()
        for trait_name in trait_values.keys():
            for group in self.get_groups_for_trait(trait_name):
                if group.name not in processed_groups:
                    group_suggestions = group.suggest_adjustments(adjusted)
                    adjusted.update(group_suggestions)
                    processed_groups.add(group.name)
        
        # Normalize individual trait values
        for trait_name, value in adjusted.items():
            trait = self.get_trait(trait_name)
            if trait:
                adjusted[trait_name] = trait.normalize_value(value)
        
        return adjusted
        
    def analyze_trait_profile(self, trait_values: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze a trait profile and provide insights.
        
        Args:
            trait_values: Trait values to analyze
            
        Returns:
            Analysis results with insights and recommendations
        """
        analysis = {
            "trait_count": len(trait_values),
            "dominant_traits": [],
            "weak_traits": [],
            "trait_types": {},
            "conflicts": [],
            "suggestions": []
        }
        
        # Categorize traits by strength
        for trait_name, value in trait_values.items():
            trait = self.get_trait(trait_name)
            if not trait:
                continue
                
            # Track by type
            type_name = trait.trait_type.value
            if type_name not in analysis["trait_types"]:
                analysis["trait_types"][type_name] = []
            analysis["trait_types"][type_name].append((trait_name, value))
            
            # Categorize by strength
            if value >= 0.8:
                analysis["dominant_traits"].append(trait_name)
            elif value <= 0.2:
                analysis["weak_traits"].append(trait_name)
        
        # Check for conflicts
        is_valid, errors = self.validate_trait_values(trait_values)
        if not is_valid:
            analysis["conflicts"] = errors
            
        # Generate suggestions
        if analysis["conflicts"]:
            suggestions = self.suggest_trait_adjustments(trait_values)
            analysis["suggestions"].append({
                "type": "conflict_resolution",
                "adjusted_values": suggestions
            })
            
        # Balance suggestions
        type_strengths = {}
        for type_name, traits in analysis["trait_types"].items():
            avg_strength = sum(value for _, value in traits) / len(traits)
            type_strengths[type_name] = avg_strength
            
        if type_strengths:
            max_type = max(type_strengths, key=type_strengths.get)
            min_type = min(type_strengths, key=type_strengths.get)
            
            if type_strengths[max_type] - type_strengths[min_type] > 0.4:
                analysis["suggestions"].append({
                    "type": "balance",
                    "description": f"Consider strengthening {min_type} traits or "
                                 f"reducing {max_type} traits for better balance"
                })
        
        return analysis
        
    def export_trait_definitions(self, filepath: str) -> None:
        """Export all trait definitions to a JSON file."""
        data = {
            "traits": [trait.to_dict() for trait in self._traits.values()],
            "groups": [group.to_dict() for group in self._groups.values()]
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def import_trait_definitions(self, filepath: str) -> None:
        """Import trait definitions from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Import traits first
        for trait_data in data.get("traits", []):
            trait = Trait.from_dict(trait_data)
            if trait.name not in self._traits:
                self.add_trait(trait)
                
        # Then import groups
        for group_data in data.get("groups", []):
            group = TraitGroup.from_dict(group_data)
            if group.name not in self._groups:
                self.add_group(group)
                
    def _load_default_traits(self) -> None:
        """Load default trait definitions."""
        default_traits = [
            # Personality traits
            Trait("extraversion", "Tendency to be outgoing and social", TraitType.PERSONALITY),
            Trait("agreeableness", "Tendency to be cooperative and trusting", TraitType.PERSONALITY),
            Trait("conscientiousness", "Tendency to be organized and responsible", TraitType.PERSONALITY),
            Trait("neuroticism", "Tendency toward negative emotions", TraitType.PERSONALITY),
            Trait("openness", "Openness to experience and new ideas", TraitType.PERSONALITY),
            
            # Behavioral traits
            Trait("assertiveness", "Tendency to be direct and forceful", TraitType.BEHAVIORAL),
            Trait("patience", "Ability to wait calmly", TraitType.BEHAVIORAL),
            Trait("curiosity", "Desire to learn and explore", TraitType.BEHAVIORAL),
            Trait("risk_taking", "Willingness to take risks", TraitType.BEHAVIORAL),
            
            # Communication traits
            Trait("verbosity", "Tendency to use many words", TraitType.COMMUNICATION),
            Trait("formality", "Preference for formal language", TraitType.COMMUNICATION),
            Trait("humor", "Use of humor in communication", TraitType.COMMUNICATION),
            Trait("empathy", "Understanding others' emotions", TraitType.EMOTIONAL),
        ]
        
        for trait in default_traits:
            self._traits[trait.name] = trait
            self._trait_to_groups[trait.name] = set()