"""
Persistence Module

Database and file-based persistence layer for personas,
versions, templates, and analytics data.
"""

from .database_adapter import DatabaseAdapter, DatabaseType
from .file_storage import FileStorage, StorageFormat
from .persona_repository import PersonaRepository
from .version_repository import VersionRepository
from .template_repository import TemplateRepository

__all__ = [
    "DatabaseAdapter",
    "DatabaseType",
    "FileStorage",
    "StorageFormat",
    "PersonaRepository",
    "VersionRepository",
    "TemplateRepository"
]