"""
Unit tests for persona versioning and migration systems.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from ...versioning.version_manager import VersionManager, PersonaVersion, VersionType, VersionStatus, PersonaChange
from ...core.persona import Persona
from .. import create_test_persona


class TestPersonaChange(unittest.TestCase):
    """Test cases for PersonaChange class."""
    
    def test_change_creation(self):
        """Test basic change creation."""
        change = PersonaChange(
            change_type="trait_added",
            field_path="traits.helpful",
            old_value=None,
            new_value=0.8,
            reason="Added helpful trait"
        )
        
        self.assertEqual(change.change_type, "trait_added")
        self.assertEqual(change.field_path, "traits.helpful")
        self.assertIsNone(change.old_value)
        self.assertEqual(change.new_value, 0.8)
        self.assertIsInstance(change.timestamp, datetime)
        self.assertIsNotNone(change.change_id)
    
    def test_change_id_uniqueness(self):
        """Test that change IDs are unique."""
        change1 = PersonaChange(
            change_type="trait_added",
            field_path="traits.helpful",
            old_value=None,
            new_value=0.8
        )
        
        change2 = PersonaChange(
            change_type="trait_added",
            field_path="traits.creative", 
            old_value=None,
            new_value=0.7
        )
        
        self.assertNotEqual(change1.change_id, change2.change_id)


class TestPersonaVersion(unittest.TestCase):
    """Test cases for PersonaVersion class."""
    
    def setUp(self):
        self.test_persona = create_test_persona("test_persona")
        self.persona_data = self.test_persona.to_dict()
    
    def test_version_creation(self):
        """Test basic version creation."""
        version = PersonaVersion(
            version_number="1.0.0",
            persona_data=self.persona_data,
            version_type=VersionType.MAJOR,
            description="Initial version"
        )
        
        self.assertEqual(version.version_number, "1.0.0")
        self.assertEqual(version.version_type, VersionType.MAJOR)
        self.assertIsInstance(version.created_at, datetime)
        self.assertIsNotNone(version.version_hash)
    
    def test_invalid_version_number(self):
        """Test validation of version number format."""
        with self.assertRaises(ValueError):
            PersonaVersion(
                version_number="invalid_version",
                persona_data=self.persona_data,
                version_type=VersionType.MAJOR
            )
    
    def test_get_persona(self):
        """Test recreating persona from version data."""
        version = PersonaVersion(
            version_number="1.0.0",
            persona_data=self.persona_data,
            version_type=VersionType.MAJOR
        )
        
        recreated_persona = version.get_persona()
        
        self.assertIsInstance(recreated_persona, Persona)
        self.assertEqual(recreated_persona.name, self.test_persona.name)
        self.assertEqual(recreated_persona.description, self.test_persona.description)
        self.assertEqual(recreated_persona.traits, self.test_persona.traits)
    
    def test_version_compatibility(self):
        """Test version compatibility checking."""
        version = PersonaVersion(
            version_number="2.1.0",
            persona_data=self.persona_data,
            version_type=VersionType.MINOR
        )
        
        # Same major version should be compatible
        self.assertTrue(version.is_compatible_with("2.0.0"))
        self.assertTrue(version.is_compatible_with("2.5.3"))
        
        # Different major version should not be compatible
        self.assertFalse(version.is_compatible_with("1.0.0"))
        self.assertFalse(version.is_compatible_with("3.0.0"))


class TestVersionManager(unittest.TestCase):
    """Test cases for VersionManager class."""
    
    def setUp(self):
        self.version_manager = VersionManager()
        self.test_persona = create_test_persona("test_persona")
    
    def test_create_initial_version(self):
        """Test creating initial version for a persona."""
        version = self.version_manager.create_initial_version(
            self.test_persona,
            initial_version="1.0.0",
            description="Initial test version"
        )
        
        self.assertIsInstance(version, PersonaVersion)
        self.assertEqual(version.version_number, "1.0.0")
        self.assertEqual(version.status, VersionStatus.ACTIVE)
        
        # Check that persona is registered in manager
        self.assertIn(self.test_persona.name, self.version_manager.versions)
        self.assertIn(self.test_persona.name, self.version_manager.active_versions)
    
    def test_duplicate_initial_version(self):
        """Test that creating duplicate initial version fails."""
        self.version_manager.create_initial_version(self.test_persona)
        
        with self.assertRaises(ValueError):
            self.version_manager.create_initial_version(self.test_persona)
    
    def test_create_new_version(self):
        """Test creating new version with changes."""
        # Create initial version
        self.version_manager.create_initial_version(self.test_persona)
        
        # Modify persona
        updated_persona = Persona(
            name=self.test_persona.name,
            description="Updated description",
            traits={**self.test_persona.traits, "helpful": 0.9, "creative": 0.8},
            conversation_style=self.test_persona.conversation_style,
            emotional_baseline=self.test_persona.emotional_baseline
        )
        
        # Create new version
        new_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR,
            "Added helpful and creative traits",
            "test_author"
        )
        
        self.assertIsInstance(new_version, PersonaVersion)
        self.assertEqual(new_version.version_type, VersionType.MINOR)
        self.assertEqual(new_version.created_by, "test_author")
        self.assertGreater(len(new_version.changes), 0)
        
        # Check that active version was updated
        active_version = self.version_manager.active_versions[self.test_persona.name]
        self.assertEqual(active_version, new_version.version_number)
    
    def test_change_calculation(self):
        """Test that changes are properly calculated."""
        # Create initial version
        self.version_manager.create_initial_version(self.test_persona)
        
        # Create modified persona
        updated_persona = create_test_persona(
            self.test_persona.name,
            traits={"helpful": 0.9},  # Changed from original
            description="New description"  # Changed
        )
        
        # Create new version
        new_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        
        # Check that changes were detected
        changes = new_version.changes
        self.assertGreater(len(changes), 0)
        
        # Should have changes for modified traits and description
        change_types = [change.change_type for change in changes]
        self.assertIn("description_changed", change_types)
    
    def test_version_number_calculation(self):
        """Test that version numbers are calculated correctly."""
        # Create initial version
        initial = self.version_manager.create_initial_version(self.test_persona, "1.0.0")
        
        # Test different version types
        updated_persona = create_test_persona(self.test_persona.name, description="Updated")
        
        # Minor version
        minor_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        self.assertEqual(minor_version.version_number, "1.1.0")
        
        # Patch version
        patch_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.PATCH
        )
        self.assertEqual(patch_version.version_number, "1.1.1")
        
        # Major version
        major_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MAJOR
        )
        self.assertEqual(major_version.version_number, "2.0.0")
    
    def test_get_version(self):
        """Test retrieving specific versions."""
        # Create initial version
        initial = self.version_manager.create_initial_version(self.test_persona)
        
        # Get version by number
        retrieved = self.version_manager.get_version(
            self.test_persona.name,
            initial.version_number
        )
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.version_number, initial.version_number)
        
        # Get active version (no version number specified)
        active = self.version_manager.get_version(self.test_persona.name)
        self.assertIsNotNone(active)
        self.assertEqual(active.version_number, initial.version_number)
        
        # Test non-existent version
        non_existent = self.version_manager.get_version(
            self.test_persona.name,
            "999.0.0"
        )
        self.assertIsNone(non_existent)
    
    def test_list_versions(self):
        """Test listing versions with filtering."""
        # Create initial version
        self.version_manager.create_initial_version(self.test_persona)
        
        # Create additional versions
        updated_persona = create_test_persona(self.test_persona.name, description="Updated")
        
        self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        
        # List all versions
        all_versions = self.version_manager.list_versions(self.test_persona.name)
        self.assertEqual(len(all_versions), 2)
        
        # List with status filter
        active_versions = self.version_manager.list_versions(
            self.test_persona.name,
            status_filter=VersionStatus.ACTIVE
        )
        self.assertEqual(len(active_versions), 1)
        
        # List with limit
        limited_versions = self.version_manager.list_versions(
            self.test_persona.name,
            limit=1
        )
        self.assertEqual(len(limited_versions), 1)
    
    def test_rollback_to_version(self):
        """Test rolling back to a previous version."""
        # Create initial version
        initial = self.version_manager.create_initial_version(self.test_persona, "1.0.0")
        
        # Create new version
        updated_persona = create_test_persona(self.test_persona.name, description="Updated")
        new_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        
        # Rollback to initial version
        success = self.version_manager.rollback_to_version(
            self.test_persona.name,
            initial.version_number,
            "Testing rollback"
        )
        
        self.assertTrue(success)
        
        # Check that active version is now the initial version
        active_version = self.version_manager.active_versions[self.test_persona.name]
        self.assertEqual(active_version, initial.version_number)
        
        # Check that initial version is active again
        initial_version_obj = self.version_manager.get_version(
            self.test_persona.name,
            initial.version_number
        )
        self.assertEqual(initial_version_obj.status, VersionStatus.ACTIVE)
    
    def test_compare_versions(self):
        """Test comparing two versions."""
        # Create initial version
        initial = self.version_manager.create_initial_version(self.test_persona, "1.0.0")
        
        # Create modified version
        updated_persona = create_test_persona(
            self.test_persona.name,
            traits={"helpful": 0.9, "new_trait": 0.6},  # Modified + added
            description="New description"
        )
        
        new_version = self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        
        # Compare versions
        comparison = self.version_manager.compare_versions(
            self.test_persona.name,
            initial.version_number,
            new_version.version_number
        )
        
        self.assertIn("trait_differences", comparison)
        self.assertIn("field_differences", comparison)
        self.assertIn("summary", comparison)
        
        # Check summary counts
        summary = comparison["summary"]
        self.assertGreater(summary["traits_added"] + summary["traits_modified"], 0)
    
    def test_version_timeline(self):
        """Test getting version timeline."""
        # Create multiple versions
        self.version_manager.create_initial_version(self.test_persona, "1.0.0")
        
        updated_persona = create_test_persona(self.test_persona.name, description="Updated")
        
        self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        
        self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.PATCH
        )
        
        # Get timeline
        timeline = self.version_manager.get_version_timeline(self.test_persona.name)
        
        self.assertEqual(len(timeline), 3)
        
        # Check timeline structure
        for entry in timeline:
            self.assertIn("version", entry)
            self.assertIn("type", entry)
            self.assertIn("status", entry)
            self.assertIn("created_at", entry)
    
    def test_archive_old_versions(self):
        """Test archiving old versions."""
        # Create multiple versions
        self.version_manager.create_initial_version(self.test_persona, "1.0.0")
        
        updated_persona = create_test_persona(self.test_persona.name)
        
        for i in range(8):  # Create 8 additional versions
            self.version_manager.create_new_version(
                self.test_persona.name,
                updated_persona,
                VersionType.PATCH,
                f"Version {i+1}"
            )
        
        # Archive old versions, keeping 3 most recent
        archived_count = self.version_manager.archive_old_versions(
            self.test_persona.name,
            keep_recent=3
        )
        
        self.assertGreater(archived_count, 0)
        
        # Check that some versions are archived
        all_versions = self.version_manager.list_versions(self.test_persona.name)
        archived_versions = [v for v in all_versions if v.status == VersionStatus.ARCHIVED]
        self.assertGreater(len(archived_versions), 0)
    
    def test_version_manager_statistics(self):
        """Test getting version manager statistics."""
        # Create some versions
        self.version_manager.create_initial_version(self.test_persona)
        
        updated_persona = create_test_persona(self.test_persona.name, description="Updated")
        self.version_manager.create_new_version(
            self.test_persona.name,
            updated_persona,
            VersionType.MINOR
        )
        
        # Get statistics
        stats = self.version_manager.get_statistics()
        
        self.assertIn("total_personas", stats)
        self.assertIn("total_versions", stats)
        self.assertIn("average_versions_per_persona", stats)
        self.assertIn("status_distribution", stats)
        self.assertIn("version_type_distribution", stats)
        
        self.assertEqual(stats["total_personas"], 1)
        self.assertEqual(stats["total_versions"], 2)
        self.assertEqual(stats["average_versions_per_persona"], 2.0)


if __name__ == "__main__":
    unittest.main()