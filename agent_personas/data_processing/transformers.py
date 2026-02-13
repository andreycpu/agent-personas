"""
Data transformation utilities for processing various data formats.
"""

import json
import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from ..exceptions import PersonaError
from ..utils import sanitize_string, safe_json_loads, deep_merge_dict


class TransformationError(PersonaError):
    """Raised when data transformation fails."""
    pass


class DataTransformer(ABC):
    """Abstract base class for data transformers."""
    
    @abstractmethod
    def transform(self, data: Any) -> Any:
        """Transform input data to desired format."""
        pass
    
    @abstractmethod
    def reverse_transform(self, data: Any) -> Any:
        """Reverse transformation to original format."""
        pass


class JsonTransformer(DataTransformer):
    """Transformer for JSON data operations."""
    
    def __init__(self, pretty_print: bool = False, sort_keys: bool = True):
        """Initialize JSON transformer."""
        self.pretty_print = pretty_print
        self.sort_keys = sort_keys
    
    def transform(self, data: Any) -> str:
        """Transform data to JSON string."""
        try:
            if self.pretty_print:
                return json.dumps(
                    data,
                    indent=2,
                    sort_keys=self.sort_keys,
                    default=str,
                    ensure_ascii=False
                )
            else:
                return json.dumps(
                    data,
                    sort_keys=self.sort_keys,
                    default=str,
                    ensure_ascii=False
                )
        except (TypeError, ValueError) as e:
            raise TransformationError(f"Failed to transform to JSON: {e}")
    
    def reverse_transform(self, data: str) -> Any:
        """Transform JSON string back to data."""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError) as e:
            raise TransformationError(f"Failed to parse JSON: {e}")
    
    def minify(self, data: Union[str, Any]) -> str:
        """Minify JSON data."""
        if isinstance(data, str):
            data = self.reverse_transform(data)
        
        return json.dumps(data, separators=(',', ':'), default=str)
    
    def prettify(self, data: Union[str, Any]) -> str:
        """Prettify JSON data."""
        if isinstance(data, str):
            data = self.reverse_transform(data)
        
        return json.dumps(data, indent=2, sort_keys=True, default=str)


class TextProcessor(DataTransformer):
    """Processor for text data transformations."""
    
    def __init__(self, normalize_unicode: bool = True, remove_extra_spaces: bool = True):
        """Initialize text processor."""
        self.normalize_unicode = normalize_unicode
        self.remove_extra_spaces = remove_extra_spaces
    
    def transform(self, text: str) -> str:
        """Transform text with normalization."""
        if not isinstance(text, str):
            text = str(text)
        
        # Unicode normalization
        if self.normalize_unicode:
            text = unicodedata.normalize('NFKC', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remove extra spaces
        if self.remove_extra_spaces:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def reverse_transform(self, text: str) -> str:
        """Return text as-is (no reverse transformation)."""
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_words(self, text: str) -> List[str]:
        """Extract words from text."""
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def count_tokens(self, text: str) -> int:
        """Count approximate tokens in text."""
        # Simple token counting (words + punctuation)
        tokens = re.findall(r'\w+|[^\w\s]', text)
        return len(tokens)
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to maximum tokens."""
        tokens = re.findall(r'\w+|[^\w\s]', text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return ''.join(truncated_tokens)
    
    def remove_profanity(self, text: str, replacements: Optional[Dict[str, str]] = None) -> str:
        """Remove or replace profanity in text."""
        if replacements is None:
            # Default replacements
            replacements = {
                r'\b(damn|hell|crap)\b': '[censored]',
                # Add more patterns as needed
            }
        
        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result


class PersonaDataProcessor(DataTransformer):
    """Specialized processor for persona data."""
    
    def __init__(self):
        """Initialize persona data processor."""
        self.json_transformer = JsonTransformer(pretty_print=True)
        self.text_processor = TextProcessor()
    
    def transform(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform persona data with validation and normalization."""
        if not isinstance(persona_data, dict):
            raise TransformationError("Persona data must be a dictionary")
        
        transformed = {}
        
        # Process name
        if 'name' in persona_data:
            transformed['name'] = self.text_processor.transform(persona_data['name'])
        
        # Process traits
        if 'traits' in persona_data:
            transformed['traits'] = self._transform_traits(persona_data['traits'])
        
        # Process knowledge areas
        if 'knowledge_areas' in persona_data:
            transformed['knowledge_areas'] = self._transform_knowledge_areas(
                persona_data['knowledge_areas']
            )
        
        # Add timestamp if not present
        if 'created_at' not in persona_data:
            transformed['created_at'] = datetime.now().timestamp()
        
        # Copy other fields
        for key, value in persona_data.items():
            if key not in transformed:
                transformed[key] = value
        
        return transformed
    
    def reverse_transform(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reverse transformation (minimal processing)."""
        return persona_data.copy()
    
    def _transform_traits(self, traits: Dict[str, Any]) -> Dict[str, Any]:
        """Transform traits with validation."""
        transformed_traits = {}
        
        # Process personality traits
        if 'personality' in traits:
            personality = traits['personality']
            if isinstance(personality, dict):
                transformed_traits['personality'] = {
                    key: max(0.0, min(1.0, float(value)))  # Clamp to 0-1 range
                    for key, value in personality.items()
                    if isinstance(value, (int, float))
                }
        
        # Process communication style
        if 'communication_style' in traits:
            style = traits['communication_style']
            if isinstance(style, str):
                transformed_traits['communication_style'] = self.text_processor.transform(style).lower()
        
        # Copy other trait fields
        for key, value in traits.items():
            if key not in transformed_traits:
                transformed_traits[key] = value
        
        return transformed_traits
    
    def _transform_knowledge_areas(self, knowledge_areas: List[str]) -> List[str]:
        """Transform knowledge areas with normalization."""
        if not isinstance(knowledge_areas, list):
            return []
        
        transformed = []
        for area in knowledge_areas:
            if isinstance(area, str):
                clean_area = self.text_processor.transform(area).lower()
                if clean_area and clean_area not in transformed:
                    transformed.append(clean_area)
        
        return transformed
    
    def validate_persona_data(self, persona_data: Dict[str, Any]) -> bool:
        """Validate persona data structure."""
        required_fields = ['name', 'traits']
        
        for field in required_fields:
            if field not in persona_data:
                raise TransformationError(f"Required field missing: {field}")
        
        # Validate traits structure
        traits = persona_data['traits']
        if not isinstance(traits, dict):
            raise TransformationError("Traits must be a dictionary")
        
        if 'communication_style' in traits:
            valid_styles = ['formal', 'casual', 'friendly', 'professional', 'technical', 'neutral']
            if traits['communication_style'] not in valid_styles:
                raise TransformationError(f"Invalid communication style: {traits['communication_style']}")
        
        return True
    
    def normalize_trait_values(self, traits: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize trait values to standard ranges."""
        normalized = traits.copy()
        
        if 'personality' in normalized and isinstance(normalized['personality'], dict):
            personality = normalized['personality']
            for trait, value in personality.items():
                if isinstance(value, (int, float)):
                    # Normalize to 0-1 range
                    normalized_value = max(0.0, min(1.0, float(value)))
                    personality[trait] = round(normalized_value, 2)
        
        return normalized
    
    def merge_personas(self, base_persona: Dict[str, Any], override_persona: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two persona configurations."""
        merged = deep_merge_dict(base_persona, override_persona)
        
        # Ensure trait values are still normalized after merge
        if 'traits' in merged:
            merged['traits'] = self.normalize_trait_values(merged['traits'])
        
        # Update timestamp
        merged['updated_at'] = datetime.now().timestamp()
        
        return merged
    
    def extract_persona_summary(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a summary of persona data."""
        summary = {
            'name': persona_data.get('name', 'Unknown'),
            'communication_style': persona_data.get('traits', {}).get('communication_style', 'neutral'),
            'knowledge_areas_count': len(persona_data.get('knowledge_areas', [])),
            'created_at': persona_data.get('created_at'),
            'version': persona_data.get('version', '1.0')
        }
        
        # Add personality overview
        personality = persona_data.get('traits', {}).get('personality', {})
        if personality:
            # Find dominant traits (>0.7)
            dominant_traits = [
                trait for trait, value in personality.items()
                if isinstance(value, (int, float)) and value > 0.7
            ]
            summary['dominant_traits'] = dominant_traits
            
            # Calculate average personality scores
            numeric_traits = {
                k: v for k, v in personality.items()
                if isinstance(v, (int, float))
            }
            if numeric_traits:
                summary['personality_average'] = sum(numeric_traits.values()) / len(numeric_traits)
        
        return summary


class ConversationProcessor(DataTransformer):
    """Processor for conversation data."""
    
    def __init__(self):
        """Initialize conversation processor."""
        self.text_processor = TextProcessor()
    
    def transform(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform conversation with normalization."""
        if not isinstance(conversation, list):
            raise TransformationError("Conversation must be a list")
        
        transformed = []
        for i, message in enumerate(conversation):
            if not isinstance(message, dict):
                raise TransformationError(f"Message {i} must be a dictionary")
            
            transformed_message = message.copy()
            
            # Clean message content
            if 'content' in message:
                transformed_message['content'] = self.text_processor.transform(message['content'])
            
            # Ensure required fields
            if 'timestamp' not in transformed_message:
                transformed_message['timestamp'] = datetime.now().timestamp()
            
            transformed.append(transformed_message)
        
        # Sort by timestamp
        transformed.sort(key=lambda x: x.get('timestamp', 0))
        
        return transformed
    
    def reverse_transform(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return conversation as-is."""
        return conversation.copy() if conversation else []
    
    def extract_conversation_stats(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract statistics from conversation."""
        if not conversation:
            return {'message_count': 0, 'total_tokens': 0}
        
        total_messages = len(conversation)
        total_tokens = 0
        role_counts = {}
        
        for message in conversation:
            content = message.get('content', '')
            total_tokens += self.text_processor.count_tokens(content)
            
            role = message.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            'message_count': total_messages,
            'total_tokens': total_tokens,
            'average_tokens_per_message': total_tokens / total_messages if total_messages > 0 else 0,
            'role_distribution': role_counts,
            'duration': self._calculate_duration(conversation)
        }
    
    def _calculate_duration(self, conversation: List[Dict[str, Any]]) -> float:
        """Calculate conversation duration in seconds."""
        if len(conversation) < 2:
            return 0.0
        
        timestamps = [msg.get('timestamp', 0) for msg in conversation]
        timestamps = [t for t in timestamps if t > 0]
        
        if len(timestamps) < 2:
            return 0.0
        
        return max(timestamps) - min(timestamps)