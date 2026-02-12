"""
Version manager for persona versioning and lifecycle management.
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import hashlib
import semantic_version
from datetime import datetime
from copy import deepcopy

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class VersionType(Enum):
    """Types of version changes."""
    MAJOR = "major"  # Breaking changes, incompatible updates
    MINOR = "minor"  # New features, backward compatible
    PATCH = "patch"  # Bug fixes, small improvements
    HOTFIX = "hotfix"  # Critical fixes
    EXPERIMENTAL = "experimental"  # Experimental features


class VersionStatus(Enum):
    """Status of persona versions."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    EXPERIMENTAL = "experimental"


@dataclass
class PersonaChange:
    """Represents a change made to a persona."""
    change_type: str  # "trait_added", "trait_modified", "trait_removed", "description_changed", etc.
    field_path: str  # Path to the changed field (e.g., "traits.helpful", "description")
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    reason: Optional[str] = None
    author: Optional[str] = None
    
    def __post_init__(self):
        """Generate a hash for the change."""
        self.change_id = self._generate_change_id()
    
    def _generate_change_id(self) -> str:
        """Generate a unique ID for the change."""
        content = f"{self.change_type}:{self.field_path}:{self.old_value}:{self.new_value}:{self.timestamp.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class PersonaVersion:
    """Represents a specific version of a persona."""
    version_number: str  # Semantic version (e.g., "1.2.3")
    persona_data: Dict[str, Any]  # Serialized persona data
    version_type: VersionType
    status: VersionStatus = VersionStatus.DRAFT
    
    # Version metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    description: str = ""
    changes: List[PersonaChange] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Migration info
    parent_version: Optional[str] = None
    schema_version: str = "1.0.0"
    compatibility_info: Dict[str, Any] = field(default_factory=dict)
    
    # Validation and metrics
    validation_errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate version number format."""
        try:
            semantic_version.Version(self.version_number)
        except ValueError:
            raise ValueError(f"Invalid semantic version: {self.version_number}")
        
        self.version_hash = self._generate_version_hash()
    
    def _generate_version_hash(self) -> str:
        """Generate a hash for the version."""
        content = json.dumps(self.persona_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_persona(self) -> Persona:
        """Recreate persona from version data."""
        return Persona.from_dict(self.persona_data)
    
    def is_compatible_with(self, target_version: str) -> bool:
        """Check if this version is compatible with a target version."""
        try:
            current = semantic_version.Version(self.version_number)
            target = semantic_version.Version(target_version)
            
            # Same major version means compatible
            return current.major == target.major
        except ValueError:
            return False


class VersionManager:
    """
    Manages versioning for personas with full lifecycle support.
    
    Provides version creation, migration, rollback, and lifecycle management
    with semantic versioning and change tracking.
    """
    
    def __init__(self):
        self.versions: Dict[str, Dict[str, PersonaVersion]] = {}  # persona_name -> version -> PersonaVersion
        self.version_index: Dict[str, List[str]] = {}  # persona_name -> sorted version list
        self.active_versions: Dict[str, str] = {}  # persona_name -> active version
        self.change_history: Dict[str, List[PersonaChange]] = {}  # persona_name -> changes
        self.logger = logging.getLogger(__name__)
        
        # Version policies
        self.auto_archive_after_versions = 10  # Archive old versions after N versions
        self.max_versions_per_persona = 50  # Maximum versions to keep
        self.deprecation_period_days = 30  # Days before deprecated versions are archived
    
    def create_initial_version(
        self,
        persona: Persona,
        initial_version: str = "1.0.0",
        description: str = "Initial version"
    ) -> PersonaVersion:
        """Create the initial version for a persona."""
        if persona.name in self.versions:
            raise ValueError(f"Persona {persona.name} already has versions")
        
        # Validate persona
        persona.validate()
        
        version = PersonaVersion(
            version_number=initial_version,
            persona_data=persona.to_dict(),
            version_type=VersionType.MAJOR,
            status=VersionStatus.ACTIVE,
            description=description,
            schema_version=self._get_current_schema_version()
        )
        
        # Initialize version storage
        self.versions[persona.name] = {initial_version: version}
        self.version_index[persona.name] = [initial_version]
        self.active_versions[persona.name] = initial_version
        self.change_history[persona.name] = []
        
        self.logger.info(f"Created initial version {initial_version} for persona {persona.name}")
        return version
    
    def create_new_version(
        self,
        persona_name: str,
        updated_persona: Persona,
        version_type: VersionType,
        description: str = "",
        author: Optional[str] = None
    ) -> PersonaVersion:
        """Create a new version of an existing persona."""
        if persona_name not in self.versions:
            raise ValueError(f"Persona {persona_name} not found")
        
        # Get current version
        current_version_number = self.active_versions[persona_name]
        current_version = self.versions[persona_name][current_version_number]
        current_persona = current_version.get_persona()
        
        # Calculate changes
        changes = self._calculate_changes(current_persona, updated_persona, author)
        
        # Calculate new version number
        new_version_number = self._calculate_next_version(current_version_number, version_type)
        
        # Validate new persona
        updated_persona.validate()
        
        # Create new version
        new_version = PersonaVersion(
            version_number=new_version_number,
            persona_data=updated_persona.to_dict(),
            version_type=version_type,
            status=VersionStatus.ACTIVE,
            description=description,
            changes=changes,
            created_by=author or "system",
            parent_version=current_version_number,
            schema_version=self._get_current_schema_version()
        )
        
        # Store new version
        self.versions[persona_name][new_version_number] = new_version
        self.version_index[persona_name].append(new_version_number)
        self._sort_version_index(persona_name)
        
        # Update active version
        self.active_versions[persona_name] = new_version_number
        
        # Update change history
        self.change_history[persona_name].extend(changes)
        
        # Mark previous version as deprecated if major change
        if version_type == VersionType.MAJOR:
            current_version.status = VersionStatus.DEPRECATED
        
        # Cleanup old versions if needed
        self._cleanup_old_versions(persona_name)
        
        self.logger.info(f"Created version {new_version_number} for persona {persona_name}")
        return new_version
    
    def _calculate_changes(
        self,
        old_persona: Persona,
        new_persona: Persona,
        author: Optional[str]
    ) -> List[PersonaChange]:
        """Calculate changes between two persona versions."""
        changes = []
        
        # Compare traits
        old_traits = old_persona.traits
        new_traits = new_persona.traits
        
        # Added traits
        for trait, value in new_traits.items():
            if trait not in old_traits:
                changes.append(PersonaChange(
                    change_type="trait_added",
                    field_path=f"traits.{trait}",
                    old_value=None,
                    new_value=value,
                    author=author
                ))
        
        # Modified traits
        for trait, new_value in new_traits.items():
            if trait in old_traits and old_traits[trait] != new_value:
                changes.append(PersonaChange(
                    change_type="trait_modified",
                    field_path=f"traits.{trait}",
                    old_value=old_traits[trait],
                    new_value=new_value,
                    author=author
                ))
        
        # Removed traits
        for trait, value in old_traits.items():
            if trait not in new_traits:
                changes.append(PersonaChange(
                    change_type="trait_removed",
                    field_path=f"traits.{trait}",
                    old_value=value,
                    new_value=None,
                    author=author
                ))
        
        # Compare other fields
        field_comparisons = [
            ("description", "description_changed"),
            ("conversation_style", "conversation_style_changed"),
            ("emotional_baseline", "emotional_baseline_changed")
        ]
        
        for field, change_type in field_comparisons:
            old_value = getattr(old_persona, field)
            new_value = getattr(new_persona, field)
            
            if old_value != new_value:
                changes.append(PersonaChange(
                    change_type=change_type,
                    field_path=field,
                    old_value=old_value,
                    new_value=new_value,
                    author=author
                ))
        
        return changes
    
    def _calculate_next_version(self, current_version: str, version_type: VersionType) -> str:
        """Calculate the next version number based on version type."""
        current = semantic_version.Version(current_version)
        
        if version_type == VersionType.MAJOR:
            next_version = current.next_major()
        elif version_type == VersionType.MINOR:
            next_version = current.next_minor()
        elif version_type == VersionType.PATCH:
            next_version = current.next_patch()
        elif version_type == VersionType.HOTFIX:
            next_version = current.next_patch()
        elif version_type == VersionType.EXPERIMENTAL:
            # Use prerelease for experimental
            prerelease = f"exp.{datetime.now().strftime('%Y%m%d')}"
            next_version = semantic_version.Version(f"{current.major}.{current.minor}.{current.patch}-{prerelease}")
        else:
            next_version = current.next_patch()
        
        return str(next_version)
    
    def get_version(self, persona_name: str, version_number: Optional[str] = None) -> Optional[PersonaVersion]:
        """Get a specific version of a persona (active version if not specified)."""
        if persona_name not in self.versions:
            return None
        
        if version_number is None:
            version_number = self.active_versions.get(persona_name)
        
        return self.versions[persona_name].get(version_number)
    
    def get_persona(self, persona_name: str, version_number: Optional[str] = None) -> Optional[Persona]:
        """Get a persona instance for a specific version."""
        version = self.get_version(persona_name, version_number)
        return version.get_persona() if version else None
    
    def list_versions(
        self,
        persona_name: str,
        status_filter: Optional[VersionStatus] = None,
        limit: Optional[int] = None
    ) -> List[PersonaVersion]:
        """List all versions for a persona."""
        if persona_name not in self.versions:
            return []
        
        versions = []
        for version_number in reversed(self.version_index[persona_name]):  # Most recent first
            version = self.versions[persona_name][version_number]
            
            if status_filter and version.status != status_filter:
                continue
            
            versions.append(version)
            
            if limit and len(versions) >= limit:
                break
        
        return versions
    
    def rollback_to_version(
        self,
        persona_name: str,
        target_version: str,
        reason: str = ""
    ) -> bool:
        """Rollback to a previous version."""
        if persona_name not in self.versions:
            self.logger.error(f"Persona {persona_name} not found")
            return False
        
        if target_version not in self.versions[persona_name]:
            self.logger.error(f"Version {target_version} not found for persona {persona_name}")
            return False
        
        target_version_obj = self.versions[persona_name][target_version]
        
        if target_version_obj.status == VersionStatus.ARCHIVED:
            self.logger.error(f"Cannot rollback to archived version {target_version}")
            return False
        
        # Mark current version as deprecated
        current_version = self.active_versions[persona_name]
        if current_version != target_version:
            self.versions[persona_name][current_version].status = VersionStatus.DEPRECATED
        
        # Set target as active
        target_version_obj.status = VersionStatus.ACTIVE
        self.active_versions[persona_name] = target_version
        
        # Log the rollback
        rollback_change = PersonaChange(
            change_type="rollback",
            field_path="version",
            old_value=current_version,
            new_value=target_version,
            reason=reason,
            author="system"
        )
        
        self.change_history[persona_name].append(rollback_change)
        
        self.logger.info(f"Rolled back persona {persona_name} from {current_version} to {target_version}")
        return True
    
    def compare_versions(
        self,
        persona_name: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two versions and return differences."""
        if persona_name not in self.versions:
            raise ValueError(f"Persona {persona_name} not found")
        
        v1 = self.versions[persona_name].get(version1)
        v2 = self.versions[persona_name].get(version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        persona1 = v1.get_persona()
        persona2 = v2.get_persona()
        
        # Calculate differences
        differences = {
            "version_comparison": f"{version1} vs {version2}",
            "trait_differences": {},
            "field_differences": {},
            "summary": {
                "traits_added": 0,
                "traits_removed": 0,
                "traits_modified": 0,
                "fields_changed": 0
            }
        }
        
        # Compare traits
        traits1 = persona1.traits
        traits2 = persona2.traits
        all_traits = set(traits1.keys()) | set(traits2.keys())
        
        for trait in all_traits:
            val1 = traits1.get(trait)
            val2 = traits2.get(trait)
            
            if val1 is None and val2 is not None:
                differences["trait_differences"][trait] = {"status": "added", "old": None, "new": val2}
                differences["summary"]["traits_added"] += 1
            elif val1 is not None and val2 is None:
                differences["trait_differences"][trait] = {"status": "removed", "old": val1, "new": None}
                differences["summary"]["traits_removed"] += 1
            elif val1 != val2:
                differences["trait_differences"][trait] = {"status": "modified", "old": val1, "new": val2}
                differences["summary"]["traits_modified"] += 1
        
        # Compare other fields
        fields_to_compare = ["description", "conversation_style", "emotional_baseline"]
        
        for field in fields_to_compare:
            val1 = getattr(persona1, field)
            val2 = getattr(persona2, field)
            
            if val1 != val2:
                differences["field_differences"][field] = {"old": val1, "new": val2}
                differences["summary"]["fields_changed"] += 1
        
        return differences
    
    def get_version_timeline(self, persona_name: str) -> List[Dict[str, Any]]:
        """Get a timeline of all versions for a persona."""
        if persona_name not in self.versions:
            return []
        
        timeline = []
        
        for version_number in self.version_index[persona_name]:
            version = self.versions[persona_name][version_number]
            
            timeline.append({
                "version": version_number,
                "type": version.version_type.value,
                "status": version.status.value,
                "created_at": version.created_at,
                "created_by": version.created_by,
                "description": version.description,
                "changes_count": len(version.changes),
                "major_changes": [c.change_type for c in version.changes if c.change_type in ["trait_added", "trait_removed", "description_changed"]]
            })
        
        return timeline
    
    def archive_old_versions(self, persona_name: str, keep_recent: int = 5) -> int:
        """Archive old versions, keeping only recent ones."""
        if persona_name not in self.versions:
            return 0
        
        versions_list = self.version_index[persona_name]
        if len(versions_list) <= keep_recent:
            return 0
        
        # Archive older versions (keep the most recent ones)
        to_archive = versions_list[:-keep_recent]
        archived_count = 0
        
        for version_number in to_archive:
            version = self.versions[persona_name][version_number]
            if version.status not in [VersionStatus.ACTIVE, VersionStatus.ARCHIVED]:
                version.status = VersionStatus.ARCHIVED
                archived_count += 1
        
        self.logger.info(f"Archived {archived_count} old versions for persona {persona_name}")
        return archived_count
    
    def _sort_version_index(self, persona_name: str):
        """Sort version index by semantic version."""
        try:
            self.version_index[persona_name].sort(
                key=lambda v: semantic_version.Version(v)
            )
        except ValueError:
            # Fallback to string sort if semantic version fails
            self.version_index[persona_name].sort()
    
    def _cleanup_old_versions(self, persona_name: str):
        """Clean up old versions according to policies."""
        if len(self.version_index[persona_name]) > self.auto_archive_after_versions:
            self.archive_old_versions(persona_name, self.auto_archive_after_versions)
        
        # Remove excess versions if over the limit
        if len(self.version_index[persona_name]) > self.max_versions_per_persona:
            versions_to_remove = len(self.version_index[persona_name]) - self.max_versions_per_persona
            oldest_versions = self.version_index[persona_name][:versions_to_remove]
            
            for version_number in oldest_versions:
                if self.versions[persona_name][version_number].status == VersionStatus.ARCHIVED:
                    del self.versions[persona_name][version_number]
                    self.version_index[persona_name].remove(version_number)
    
    def _get_current_schema_version(self) -> str:
        """Get current schema version."""
        # This would track schema evolution
        return "1.0.0"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about version management."""
        total_personas = len(self.versions)
        total_versions = sum(len(versions) for versions in self.versions.values())
        
        # Status distribution
        status_counts = {}
        version_type_counts = {}
        
        for persona_versions in self.versions.values():
            for version in persona_versions.values():
                status = version.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                version_type = version.version_type.value
                version_type_counts[version_type] = version_type_counts.get(version_type, 0) + 1
        
        # Average versions per persona
        avg_versions = total_versions / total_personas if total_personas > 0 else 0
        
        return {
            "total_personas": total_personas,
            "total_versions": total_versions,
            "average_versions_per_persona": round(avg_versions, 2),
            "status_distribution": status_counts,
            "version_type_distribution": version_type_counts,
            "active_personas": len(self.active_versions)
        }