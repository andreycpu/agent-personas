"""
File-based storage system for persona data.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import pickle
import yaml
import logging
import shutil
import hashlib
from datetime import datetime
import gzip
import os

logger = logging.getLogger(__name__)


class StorageFormat(Enum):
    """Supported storage formats."""
    JSON = "json"
    YAML = "yaml"
    PICKLE = "pickle"
    COMPRESSED_JSON = "json.gz"


class CompressionType(Enum):
    """Compression types for storage."""
    NONE = "none"
    GZIP = "gzip"


@dataclass
class StorageConfig:
    """Configuration for file storage."""
    base_path: str = "./persona_data"
    format: StorageFormat = StorageFormat.JSON
    compression: CompressionType = CompressionType.NONE
    backup_enabled: bool = True
    backup_count: int = 5
    auto_create_dirs: bool = True
    file_permissions: int = 0o644
    dir_permissions: int = 0o755


class FileStorage:
    """
    File-based storage system for persona framework data.
    
    Provides organized file storage with support for multiple formats,
    compression, backup, and data integrity verification.
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize directory structure
        if self.config.auto_create_dirs:
            self._create_directory_structure()
        
        # Format handlers
        self.format_handlers = {
            StorageFormat.JSON: (self._save_json, self._load_json),
            StorageFormat.YAML: (self._save_yaml, self._load_yaml),
            StorageFormat.PICKLE: (self._save_pickle, self._load_pickle),
            StorageFormat.COMPRESSED_JSON: (self._save_compressed_json, self._load_compressed_json)
        }
    
    def _create_directory_structure(self):
        """Create the directory structure for organized storage."""
        directories = [
            "personas",
            "versions",
            "templates", 
            "archetypes",
            "analytics",
            "backups",
            "exports",
            "cache",
            "logs"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            os.chmod(dir_path, self.config.dir_permissions)
    
    def save_persona(self, persona_data: Dict[str, Any], persona_id: str) -> bool:
        """Save persona data to storage."""
        try:
            file_path = self.base_path / "personas" / f"{persona_id}.{self.config.format.value}"
            return self._save_data(persona_data, file_path)
        except Exception as e:
            self.logger.error(f"Failed to save persona {persona_id}: {e}")
            return False
    
    def load_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Load persona data from storage."""
        try:
            file_path = self.base_path / "personas" / f"{persona_id}.{self.config.format.value}"
            return self._load_data(file_path)
        except Exception as e:
            self.logger.error(f"Failed to load persona {persona_id}: {e}")
            return None
    
    def save_version(self, version_data: Dict[str, Any], persona_id: str, version_id: str) -> bool:
        """Save version data to storage."""
        try:
            version_dir = self.base_path / "versions" / persona_id
            version_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(version_dir, self.config.dir_permissions)
            
            file_path = version_dir / f"{version_id}.{self.config.format.value}"
            return self._save_data(version_data, file_path)
        except Exception as e:
            self.logger.error(f"Failed to save version {version_id} for persona {persona_id}: {e}")
            return False
    
    def load_version(self, persona_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """Load version data from storage."""
        try:
            file_path = self.base_path / "versions" / persona_id / f"{version_id}.{self.config.format.value}"
            return self._load_data(file_path)
        except Exception as e:
            self.logger.error(f"Failed to load version {version_id} for persona {persona_id}: {e}")
            return None
    
    def save_template(self, template_data: Dict[str, Any], template_id: str) -> bool:
        """Save template data to storage."""
        try:
            file_path = self.base_path / "templates" / f"{template_id}.{self.config.format.value}"
            return self._save_data(template_data, file_path)
        except Exception as e:
            self.logger.error(f"Failed to save template {template_id}: {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Load template data from storage."""
        try:
            file_path = self.base_path / "templates" / f"{template_id}.{self.config.format.value}"
            return self._load_data(file_path)
        except Exception as e:
            self.logger.error(f"Failed to load template {template_id}: {e}")
            return None
    
    def save_analytics(self, analytics_data: Dict[str, Any], data_type: str, timestamp: Optional[str] = None) -> bool:
        """Save analytics data to storage."""
        try:
            if not timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            file_path = self.base_path / "analytics" / f"{data_type}_{timestamp}.{self.config.format.value}"
            return self._save_data(analytics_data, file_path)
        except Exception as e:
            self.logger.error(f"Failed to save analytics data {data_type}: {e}")
            return False
    
    def list_personas(self) -> List[str]:
        """List all stored persona IDs."""
        try:
            personas_dir = self.base_path / "personas"
            if not personas_dir.exists():
                return []
            
            persona_files = list(personas_dir.glob(f"*.{self.config.format.value}"))
            return [f.stem for f in persona_files]
        except Exception as e:
            self.logger.error(f"Failed to list personas: {e}")
            return []
    
    def list_versions(self, persona_id: str) -> List[str]:
        """List all versions for a persona."""
        try:
            versions_dir = self.base_path / "versions" / persona_id
            if not versions_dir.exists():
                return []
            
            version_files = list(versions_dir.glob(f"*.{self.config.format.value}"))
            return [f.stem for f in version_files]
        except Exception as e:
            self.logger.error(f"Failed to list versions for persona {persona_id}: {e}")
            return []
    
    def list_templates(self) -> List[str]:
        """List all stored template IDs."""
        try:
            templates_dir = self.base_path / "templates"
            if not templates_dir.exists():
                return []
            
            template_files = list(templates_dir.glob(f"*.{self.config.format.value}"))
            return [f.stem for f in template_files]
        except Exception as e:
            self.logger.error(f"Failed to list templates: {e}")
            return []
    
    def delete_persona(self, persona_id: str, create_backup: bool = True) -> bool:
        """Delete persona from storage."""
        try:
            file_path = self.base_path / "personas" / f"{persona_id}.{self.config.format.value}"
            
            if not file_path.exists():
                self.logger.warning(f"Persona {persona_id} not found for deletion")
                return False
            
            if create_backup and self.config.backup_enabled:
                self._create_backup(file_path, f"personas_deleted_{persona_id}")
            
            file_path.unlink()
            
            # Also delete versions directory if it exists
            versions_dir = self.base_path / "versions" / persona_id
            if versions_dir.exists():
                if create_backup and self.config.backup_enabled:
                    self._create_backup(versions_dir, f"versions_deleted_{persona_id}")
                shutil.rmtree(versions_dir)
            
            self.logger.info(f"Deleted persona {persona_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete persona {persona_id}: {e}")
            return False
    
    def export_all_data(self, export_path: str, include_analytics: bool = False) -> bool:
        """Export all data to a specified path."""
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export personas
            personas_export_dir = export_dir / "personas"
            personas_export_dir.mkdir(exist_ok=True)
            
            for persona_id in self.list_personas():
                persona_data = self.load_persona(persona_id)
                if persona_data:
                    export_file = personas_export_dir / f"{persona_id}.json"
                    with open(export_file, 'w') as f:
                        json.dump(persona_data, f, indent=2)
            
            # Export templates
            templates_export_dir = export_dir / "templates"
            templates_export_dir.mkdir(exist_ok=True)
            
            for template_id in self.list_templates():
                template_data = self.load_template(template_id)
                if template_data:
                    export_file = templates_export_dir / f"{template_id}.json"
                    with open(export_file, 'w') as f:
                        json.dump(template_data, f, indent=2)
            
            # Export versions
            versions_export_dir = export_dir / "versions"
            versions_export_dir.mkdir(exist_ok=True)
            
            for persona_id in self.list_personas():
                persona_versions_dir = versions_export_dir / persona_id
                persona_versions_dir.mkdir(exist_ok=True)
                
                for version_id in self.list_versions(persona_id):
                    version_data = self.load_version(persona_id, version_id)
                    if version_data:
                        export_file = persona_versions_dir / f"{version_id}.json"
                        with open(export_file, 'w') as f:
                            json.dump(version_data, f, indent=2)
            
            # Export analytics if requested
            if include_analytics:
                analytics_export_dir = export_dir / "analytics"
                analytics_export_dir.mkdir(exist_ok=True)
                
                analytics_dir = self.base_path / "analytics"
                if analytics_dir.exists():
                    for analytics_file in analytics_dir.glob("*"):
                        if analytics_file.is_file():
                            shutil.copy2(analytics_file, analytics_export_dir)
            
            # Create export manifest
            manifest = {
                "export_timestamp": datetime.now().isoformat(),
                "export_format": "json",
                "personas_count": len(list(personas_export_dir.glob("*.json"))),
                "templates_count": len(list(templates_export_dir.glob("*.json"))),
                "includes_analytics": include_analytics
            }
            
            manifest_file = export_dir / "export_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.logger.info(f"Successfully exported all data to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export data to {export_path}: {e}")
            return False
    
    def import_data(self, import_path: str, overwrite: bool = False) -> bool:
        """Import data from an export."""
        try:
            import_dir = Path(import_path)
            if not import_dir.exists():
                raise ValueError(f"Import path does not exist: {import_path}")
            
            # Check for manifest
            manifest_file = import_dir / "export_manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                self.logger.info(f"Importing data from export created at {manifest.get('export_timestamp')}")
            
            imported_count = 0
            
            # Import personas
            personas_import_dir = import_dir / "personas"
            if personas_import_dir.exists():
                for persona_file in personas_import_dir.glob("*.json"):
                    persona_id = persona_file.stem
                    
                    if not overwrite and self.load_persona(persona_id):
                        self.logger.warning(f"Persona {persona_id} already exists, skipping")
                        continue
                    
                    with open(persona_file, 'r') as f:
                        persona_data = json.load(f)
                    
                    if self.save_persona(persona_data, persona_id):
                        imported_count += 1
            
            # Import templates
            templates_import_dir = import_dir / "templates"
            if templates_import_dir.exists():
                for template_file in templates_import_dir.glob("*.json"):
                    template_id = template_file.stem
                    
                    if not overwrite and self.load_template(template_id):
                        self.logger.warning(f"Template {template_id} already exists, skipping")
                        continue
                    
                    with open(template_file, 'r') as f:
                        template_data = json.load(f)
                    
                    if self.save_template(template_data, template_id):
                        imported_count += 1
            
            # Import versions
            versions_import_dir = import_dir / "versions"
            if versions_import_dir.exists():
                for persona_dir in versions_import_dir.iterdir():
                    if persona_dir.is_dir():
                        persona_id = persona_dir.name
                        
                        for version_file in persona_dir.glob("*.json"):
                            version_id = version_file.stem
                            
                            if not overwrite and self.load_version(persona_id, version_id):
                                self.logger.warning(f"Version {version_id} for persona {persona_id} already exists, skipping")
                                continue
                            
                            with open(version_file, 'r') as f:
                                version_data = json.load(f)
                            
                            if self.save_version(version_data, persona_id, version_id):
                                imported_count += 1
            
            self.logger.info(f"Successfully imported {imported_count} items from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import data from {import_path}: {e}")
            return False
    
    def _save_data(self, data: Dict[str, Any], file_path: Path) -> bool:
        """Save data using the configured format."""
        try:
            if self.config.backup_enabled and file_path.exists():
                self._create_backup(file_path)
            
            save_func, _ = self.format_handlers[self.config.format]
            save_func(data, file_path)
            
            # Set file permissions
            os.chmod(file_path, self.config.file_permissions)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save data to {file_path}: {e}")
            return False
    
    def _load_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load data using the configured format."""
        if not file_path.exists():
            return None
        
        try:
            _, load_func = self.format_handlers[self.config.format]
            return load_func(file_path)
        except Exception as e:
            self.logger.error(f"Failed to load data from {file_path}: {e}")
            return None
    
    def _save_json(self, data: Dict[str, Any], file_path: Path):
        """Save data in JSON format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load data from JSON format."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_yaml(self, data: Dict[str, Any], file_path: Path):
        """Save data in YAML format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load data from YAML format."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _save_pickle(self, data: Dict[str, Any], file_path: Path):
        """Save data in pickle format."""
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    
    def _load_pickle(self, file_path: Path) -> Dict[str, Any]:
        """Load data from pickle format."""
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    
    def _save_compressed_json(self, data: Dict[str, Any], file_path: Path):
        """Save data in compressed JSON format."""
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)
    
    def _load_compressed_json(self, file_path: Path) -> Dict[str, Any]:
        """Load data from compressed JSON format."""
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_backup(self, file_path: Path, backup_prefix: str = None):
        """Create backup of a file."""
        if not file_path.exists():
            return
        
        try:
            backup_dir = self.base_path / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if backup_prefix:
                backup_name = f"{backup_prefix}_{timestamp}"
            else:
                backup_name = f"{file_path.stem}_backup_{timestamp}"
            
            backup_path = backup_dir / f"{backup_name}{file_path.suffix}"
            
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            else:
                shutil.copytree(file_path, backup_path)
            
            # Clean up old backups
            self._cleanup_old_backups(backup_dir)
            
            self.logger.debug(f"Created backup: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path):
        """Clean up old backup files."""
        try:
            backup_files = sorted(backup_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            if len(backup_files) > self.config.backup_count:
                for old_backup in backup_files[self.config.backup_count:]:
                    if old_backup.is_file():
                        old_backup.unlink()
                    elif old_backup.is_dir():
                        shutil.rmtree(old_backup)
                    self.logger.debug(f"Removed old backup: {old_backup}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            def get_dir_size(path: Path) -> int:
                """Get total size of directory."""
                total = 0
                if path.exists():
                    for item in path.rglob('*'):
                        if item.is_file():
                            total += item.stat().st_size
                return total
            
            stats = {
                "base_path": str(self.base_path),
                "storage_format": self.config.format.value,
                "compression": self.config.compression.value,
                "personas_count": len(self.list_personas()),
                "templates_count": len(self.list_templates()),
                "total_size_bytes": get_dir_size(self.base_path),
                "directory_sizes": {}
            }
            
            # Get size for each subdirectory
            for subdir in ["personas", "versions", "templates", "analytics", "backups"]:
                dir_path = self.base_path / subdir
                stats["directory_sizes"][subdir] = get_dir_size(dir_path)
            
            # Convert to MB
            stats["total_size_mb"] = round(stats["total_size_bytes"] / 1024 / 1024, 2)
            for key in stats["directory_sizes"]:
                stats["directory_sizes"][key + "_mb"] = round(stats["directory_sizes"][key] / 1024 / 1024, 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}