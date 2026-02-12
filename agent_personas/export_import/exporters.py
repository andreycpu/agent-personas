"""
Data exporters for personas, templates, and analytics.
"""

from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
import zipfile
import tempfile

from ..core.persona import Persona
from ..templates.template import PersonaTemplate

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def export(self, data: Any, output_path: str, **options) -> bool:
        """Export data to specified path."""
        pass


class PersonaExporter(BaseExporter):
    """Exporter for persona data."""
    
    def export_persona(self, persona: Persona, output_path: str, format: str = "json") -> bool:
        """Export a single persona."""
        try:
            data = persona.to_dict()
            
            if format.lower() == "json":
                return self._export_json(data, output_path)
            elif format.lower() == "yaml":
                return self._export_yaml(data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export persona {persona.name}: {e}")
            return False
    
    def export_personas_bulk(self, personas: List[Persona], output_path: str, 
                            format: str = "json", include_metadata: bool = True) -> bool:
        """Export multiple personas."""
        try:
            export_data = {
                "export_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "persona_count": len(personas),
                    "format": format,
                    "exporter_version": "1.0.0"
                } if include_metadata else {},
                "personas": [persona.to_dict() for persona in personas]
            }
            
            if format.lower() == "json":
                return self._export_json(export_data, output_path)
            elif format.lower() == "yaml":
                return self._export_yaml(export_data, output_path)
            elif format.lower() == "csv":
                return self._export_personas_csv(personas, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export {len(personas)} personas: {e}")
            return False
    
    def export_personas_archive(self, personas: List[Persona], output_path: str) -> bool:
        """Export personas as a zip archive with individual files."""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                metadata = {
                    "export_timestamp": datetime.now().isoformat(),
                    "persona_count": len(personas),
                    "personas": [{"name": p.name, "description": p.description} for p in personas]
                }
                zipf.writestr("export_metadata.json", json.dumps(metadata, indent=2))
                
                # Add individual persona files
                for persona in personas:
                    filename = f"personas/{persona.name}.json"
                    persona_data = json.dumps(persona.to_dict(), indent=2)
                    zipf.writestr(filename, persona_data)
            
            self.logger.info(f"Exported {len(personas)} personas to archive: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create personas archive: {e}")
            return False
    
    def _export_json(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export data as JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    
    def _export_yaml(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export data as YAML."""
        import yaml
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    
    def _export_personas_csv(self, personas: List[Persona], output_path: str) -> bool:
        """Export personas as CSV."""
        if not personas:
            return False
        
        # Get all unique traits across all personas
        all_traits = set()
        for persona in personas:
            all_traits.update(persona.traits.keys())
        
        trait_columns = sorted(list(all_traits))
        
        # Define CSV headers
        headers = ["name", "description", "conversation_style", "emotional_baseline"] + [f"trait_{trait}" for trait in trait_columns]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for persona in personas:
                row = [
                    persona.name,
                    persona.description,
                    persona.conversation_style,
                    persona.emotional_baseline
                ]
                
                # Add trait values
                for trait in trait_columns:
                    row.append(persona.get_trait(trait))
                
                writer.writerow(row)
        
        return True


class TemplateExporter(BaseExporter):
    """Exporter for template data."""
    
    def export_template(self, template: PersonaTemplate, output_path: str, format: str = "json") -> bool:
        """Export a single template."""
        try:
            data = template.to_dict()
            
            if format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format.lower() == "yaml":
                import yaml
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported template {template.name} to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export template {template.name}: {e}")
            return False
    
    def export_templates_bulk(self, templates: List[PersonaTemplate], 
                             output_path: str, format: str = "json") -> bool:
        """Export multiple templates."""
        try:
            export_data = {
                "export_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "template_count": len(templates),
                    "format": format
                },
                "templates": [template.to_dict() for template in templates]
            }
            
            if format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            elif format.lower() == "yaml":
                import yaml
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported {len(templates)} templates to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export templates: {e}")
            return False


class AnalyticsExporter(BaseExporter):
    """Exporter for analytics data."""
    
    def export_usage_data(self, usage_data: List[Dict[str, Any]], 
                         output_path: str, format: str = "csv") -> bool:
        """Export usage analytics data."""
        try:
            if format.lower() == "csv":
                return self._export_usage_csv(usage_data, output_path)
            elif format.lower() == "json":
                return self._export_usage_json(usage_data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export usage data: {e}")
            return False
    
    def _export_usage_csv(self, usage_data: List[Dict[str, Any]], output_path: str) -> bool:
        """Export usage data as CSV."""
        if not usage_data:
            return False
        
        # Get all unique keys for headers
        all_keys = set()
        for item in usage_data:
            all_keys.update(item.keys())
        
        headers = sorted(list(all_keys))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for item in usage_data:
                row = [item.get(key, '') for key in headers]
                writer.writerow(row)
        
        return True
    
    def _export_usage_json(self, usage_data: List[Dict[str, Any]], output_path: str) -> bool:
        """Export usage data as JSON."""
        export_data = {
            "export_metadata": {
                "timestamp": datetime.now().isoformat(),
                "record_count": len(usage_data),
                "data_type": "usage_analytics"
            },
            "data": usage_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def export_performance_report(self, performance_data: Dict[str, Any], 
                                 output_path: str, format: str = "json") -> bool:
        """Export performance report."""
        try:
            report_data = {
                "report_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "report_type": "performance",
                    "format": format
                },
                "performance_data": performance_data
            }
            
            if format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            elif format.lower() == "yaml":
                import yaml
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(report_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported performance report to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export performance report: {e}")
            return False


def create_export_package(personas: List[Persona], templates: List[PersonaTemplate],
                         analytics_data: Optional[List[Dict[str, Any]]], 
                         output_path: str) -> bool:
    """Create a complete export package with all data."""
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Export metadata
            package_metadata = {
                "package_type": "persona_framework_export",
                "export_timestamp": datetime.now().isoformat(),
                "contents": {
                    "personas": len(personas),
                    "templates": len(templates),
                    "analytics": len(analytics_data) if analytics_data else 0
                },
                "format_version": "1.0.0"
            }
            zipf.writestr("package_metadata.json", json.dumps(package_metadata, indent=2))
            
            # Export personas
            if personas:
                persona_exporter = PersonaExporter()
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    persona_exporter.export_personas_bulk(personas, temp_file.name)
                    zipf.write(temp_file.name, "personas.json")
                    Path(temp_file.name).unlink()
            
            # Export templates
            if templates:
                template_exporter = TemplateExporter()
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    template_exporter.export_templates_bulk(templates, temp_file.name)
                    zipf.write(temp_file.name, "templates.json")
                    Path(temp_file.name).unlink()
            
            # Export analytics
            if analytics_data:
                analytics_exporter = AnalyticsExporter()
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    analytics_exporter.export_usage_data(analytics_data, temp_file.name, "json")
                    zipf.write(temp_file.name, "analytics.json")
                    Path(temp_file.name).unlink()
        
        logger.info(f"Created export package: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create export package: {e}")
        return False