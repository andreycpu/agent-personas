"""
Serialization utilities for persona data persistence and transfer.
"""

import json
import pickle
import base64
import gzip
from typing import Dict, Any, List, Optional, Union, IO
from pathlib import Path
from datetime import datetime

from ..core.persona import Persona


class PersonaEncoder(json.JSONEncoder):
    """Custom JSON encoder for persona-related objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return {
                "__type__": "datetime",
                "isoformat": obj.isoformat()
            }
        elif isinstance(obj, Persona):
            return {
                "__type__": "Persona",
                "data": obj.to_dict()
            }
        elif hasattr(obj, "to_dict"):
            return {
                "__type__": obj.__class__.__name__,
                "data": obj.to_dict()
            }
        return super().default(obj)


def persona_decoder(dct: Dict[str, Any]) -> Any:
    """Custom JSON decoder for persona-related objects."""
    if "__type__" in dct:
        obj_type = dct["__type__"]
        
        if obj_type == "datetime":
            return datetime.fromisoformat(dct["isoformat"])
        elif obj_type == "Persona":
            return Persona.from_dict(dct["data"])
        # Add more object types as needed
        
    return dct


def serialize_persona(persona: Persona, format: str = "json") -> str:
    """
    Serialize a persona to string format.
    
    Args:
        persona: Persona instance to serialize
        format: Serialization format ("json", "pickle", "compressed")
        
    Returns:
        Serialized persona as string
    """
    if format == "json":
        return json.dumps(persona, cls=PersonaEncoder, indent=2)
    
    elif format == "pickle":
        # Serialize to pickle and encode as base64
        pickled_data = pickle.dumps(persona)
        return base64.b64encode(pickled_data).decode('utf-8')
    
    elif format == "compressed":
        # JSON compressed with gzip
        json_data = json.dumps(persona, cls=PersonaEncoder)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        return base64.b64encode(compressed_data).decode('utf-8')
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def deserialize_persona(data: str, format: str = "json") -> Persona:
    """
    Deserialize a persona from string format.
    
    Args:
        data: Serialized persona data
        format: Serialization format ("json", "pickle", "compressed")
        
    Returns:
        Deserialized Persona instance
    """
    if format == "json":
        return json.loads(data, object_hook=persona_decoder)
    
    elif format == "pickle":
        # Decode base64 and unpickle
        pickled_data = base64.b64decode(data.encode('utf-8'))
        return pickle.loads(pickled_data)
    
    elif format == "compressed":
        # Decode base64, decompress, and parse JSON
        compressed_data = base64.b64decode(data.encode('utf-8'))
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_data, object_hook=persona_decoder)
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def save_persona_to_file(persona: Persona, filepath: Union[str, Path], format: str = "json") -> None:
    """
    Save a persona to a file.
    
    Args:
        persona: Persona to save
        filepath: Path to save file
        format: File format ("json", "pickle", "compressed")
    """
    filepath = Path(filepath)
    
    # Create directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(persona, f, cls=PersonaEncoder, indent=2)
    
    elif format == "pickle":
        with open(filepath, 'wb') as f:
            pickle.dump(persona, f)
    
    elif format == "compressed":
        json_data = json.dumps(persona, cls=PersonaEncoder)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        with open(filepath, 'wb') as f:
            f.write(compressed_data)
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def load_persona_from_file(filepath: Union[str, Path], format: str = "auto") -> Persona:
    """
    Load a persona from a file.
    
    Args:
        filepath: Path to file
        format: File format ("json", "pickle", "compressed", "auto")
        
    Returns:
        Loaded Persona instance
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Persona file not found: {filepath}")
    
    # Auto-detect format from extension
    if format == "auto":
        suffix = filepath.suffix.lower()
        if suffix == ".json":
            format = "json"
        elif suffix == ".pickle" or suffix == ".pkl":
            format = "pickle"
        elif suffix == ".gz":
            format = "compressed"
        else:
            # Try to detect by content
            with open(filepath, 'rb') as f:
                header = f.read(2)
                if header == b'\x1f\x8b':  # gzip magic number
                    format = "compressed"
                elif header[0:1] == b'{':  # likely JSON
                    format = "json"
                else:
                    format = "pickle"
    
    if format == "json":
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f, object_hook=persona_decoder)
    
    elif format == "pickle":
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    elif format == "compressed":
        with open(filepath, 'rb') as f:
            compressed_data = f.read()
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            return json.loads(json_data, object_hook=persona_decoder)
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_personas_collection(
    personas: List[Persona], 
    filepath: Union[str, Path],
    format: str = "json",
    include_metadata: bool = True
) -> None:
    """
    Export a collection of personas to a single file.
    
    Args:
        personas: List of personas to export
        filepath: Output file path
        format: Export format
        include_metadata: Whether to include export metadata
    """
    export_data = {
        "personas": personas,
        "count": len(personas)
    }
    
    if include_metadata:
        export_data["metadata"] = {
            "export_timestamp": datetime.now(),
            "export_version": "1.0",
            "framework_version": "0.1.0"
        }
    
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, cls=PersonaEncoder, indent=2)
    else:
        raise ValueError(f"Unsupported collection format: {format}")


def import_personas_collection(filepath: Union[str, Path]) -> List[Persona]:
    """
    Import a collection of personas from a file.
    
    Args:
        filepath: Path to collection file
        
    Returns:
        List of imported personas
    """
    filepath = Path(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f, object_hook=persona_decoder)
    
    return data.get("personas", [])


def serialize_persona_state(
    persona: Persona,
    emotional_state: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Serialize a complete persona state including emotional and contextual data.
    
    Args:
        persona: Persona instance
        emotional_state: Current emotional state
        context: Current context data
        
    Returns:
        Serialized state dictionary
    """
    state_data = {
        "persona": persona.to_dict(),
        "timestamp": datetime.now().isoformat(),
        "state_version": "1.0"
    }
    
    if emotional_state:
        if hasattr(emotional_state, "to_dict"):
            state_data["emotional_state"] = emotional_state.to_dict()
        else:
            state_data["emotional_state"] = emotional_state
    
    if context:
        state_data["context"] = context
    
    return state_data


def deserialize_persona_state(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserialize a complete persona state.
    
    Args:
        state_data: Serialized state data
        
    Returns:
        Dictionary with deserialized components
    """
    result = {}
    
    if "persona" in state_data:
        result["persona"] = Persona.from_dict(state_data["persona"])
    
    if "emotional_state" in state_data:
        # Emotional state deserialization would depend on the specific implementation
        result["emotional_state"] = state_data["emotional_state"]
    
    if "context" in state_data:
        result["context"] = state_data["context"]
    
    if "timestamp" in state_data:
        result["timestamp"] = datetime.fromisoformat(state_data["timestamp"])
    
    return result


def create_persona_backup(
    personas: List[Persona],
    backup_path: Union[str, Path],
    compress: bool = True
) -> str:
    """
    Create a backup of personas with optional compression.
    
    Args:
        personas: List of personas to backup
        backup_path: Base backup path
        compress: Whether to compress the backup
        
    Returns:
        Path to created backup file
    """
    backup_path = Path(backup_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if compress:
        backup_file = backup_path / f"persona_backup_{timestamp}.json.gz"
        format_type = "compressed"
    else:
        backup_file = backup_path / f"persona_backup_{timestamp}.json"
        format_type = "json"
    
    export_personas_collection(personas, backup_file, format_type)
    return str(backup_file)


def restore_persona_backup(backup_path: Union[str, Path]) -> List[Persona]:
    """
    Restore personas from a backup file.
    
    Args:
        backup_path: Path to backup file
        
    Returns:
        List of restored personas
    """
    return import_personas_collection(backup_path)


def calculate_serialization_size(persona: Persona, format: str = "json") -> Dict[str, int]:
    """
    Calculate serialization sizes for different formats.
    
    Args:
        persona: Persona to analyze
        format: Primary format to calculate
        
    Returns:
        Dictionary with size information in bytes
    """
    sizes = {}
    
    # JSON size
    json_data = serialize_persona(persona, "json")
    sizes["json"] = len(json_data.encode('utf-8'))
    
    # Compressed size
    compressed_data = serialize_persona(persona, "compressed")
    sizes["compressed"] = len(base64.b64decode(compressed_data))
    
    # Pickle size
    pickle_data = serialize_persona(persona, "pickle")
    sizes["pickle"] = len(base64.b64decode(pickle_data))
    
    # Compression ratio
    sizes["compression_ratio"] = sizes["json"] / sizes["compressed"] if sizes["compressed"] > 0 else 0
    
    return sizes


def migrate_persona_format(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    input_format: str = "auto",
    output_format: str = "json"
) -> None:
    """
    Migrate a persona file from one format to another.
    
    Args:
        input_path: Source file path
        output_path: Destination file path  
        input_format: Source format
        output_format: Target format
    """
    # Load persona
    persona = load_persona_from_file(input_path, input_format)
    
    # Save in new format
    save_persona_to_file(persona, output_path, output_format)


def validate_serialized_data(data: str, format: str = "json") -> bool:
    """
    Validate serialized persona data without full deserialization.
    
    Args:
        data: Serialized data to validate
        format: Data format
        
    Returns:
        True if data appears valid
    """
    try:
        if format == "json":
            # Parse JSON and check for required fields
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                # Check if it's a persona or contains persona
                if "name" in parsed:
                    return True
                elif "__type__" in parsed and parsed["__type__"] == "Persona":
                    return "data" in parsed and "name" in parsed["data"]
            return False
        
        elif format == "compressed":
            # Try to decompress and validate JSON
            try:
                compressed_data = base64.b64decode(data)
                json_data = gzip.decompress(compressed_data).decode('utf-8')
                return validate_serialized_data(json_data, "json")
            except:
                return False
        
        elif format == "pickle":
            # Basic validation for pickle data
            try:
                pickle_data = base64.b64decode(data)
                # Check pickle header
                return pickle_data[:2] == b'\x80\x03' or pickle_data[:2] == b'\x80\x04'
            except:
                return False
        
        return False
    
    except Exception:
        return False