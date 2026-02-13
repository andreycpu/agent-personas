"""
Input sanitization and security utilities.
"""

import re
import html
import unicodedata
from typing import Any, Dict, List, Optional, Pattern, Union
from ..exceptions import PersonaValidationError


# Common PII patterns
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'(\+?1[-.\s]?)?(\()?([0-9]{3})(\))?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
    'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
    'url': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
    'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
}

# Injection attack patterns
INJECTION_PATTERNS = {
    'sql_injection': re.compile(r'(\'|\")?;\s*(drop|alter|delete|insert|update|select|union|exec|execute)\s+', re.IGNORECASE),
    'script_injection': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    'command_injection': re.compile(r'[\|\&\;\$\>\<\`\!]', re.IGNORECASE),
    'path_traversal': re.compile(r'(\.\./|\.\.\|\.\.\\\)'),
    'xss': re.compile(r'<[^>]*on\w+\s*=', re.IGNORECASE),
}

# Dangerous content patterns
DANGEROUS_PATTERNS = {
    'violence': re.compile(r'\b(kill|murder|assault|attack|harm|hurt|violence|weapon|gun|bomb|explosive)\b', re.IGNORECASE),
    'self_harm': re.compile(r'\b(suicide|self-harm|cut myself|end my life|hurt myself)\b', re.IGNORECASE),
    'hate_speech': re.compile(r'\b(racist|sexist|homophobic|transphobic|bigot|nazi|supremacist)\b', re.IGNORECASE),
    'illegal_activity': re.compile(r'\b(drug dealing|illegal|fraud|scam|money laundering|terrorism)\b', re.IGNORECASE),
}


def sanitize_input(
    text: str,
    max_length: int = 10000,
    remove_html: bool = True,
    normalize_unicode: bool = True,
    filter_control_chars: bool = True,
    escape_special_chars: bool = False
) -> str:
    """
    Sanitize input text to remove potentially harmful content.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        remove_html: Remove HTML tags
        normalize_unicode: Normalize unicode characters
        filter_control_chars: Remove control characters
        escape_special_chars: Escape HTML special characters
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Normalize unicode
    if normalize_unicode:
        text = unicodedata.normalize('NFKC', text)
    
    # Remove control characters
    if filter_control_chars:
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Remove HTML tags
    if remove_html:
        text = re.sub(r'<[^>]+>', '', text)
    
    # Escape special characters
    if escape_special_chars:
        text = html.escape(text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def validate_safe_content(text: str, strict_mode: bool = False) -> bool:
    """
    Validate that content is safe and appropriate.
    
    Args:
        text: Text to validate
        strict_mode: Enable stricter validation rules
    
    Returns:
        True if content is safe
    
    Raises:
        PersonaValidationError: If unsafe content is detected
    """
    # Check for injection attempts
    for pattern_name, pattern in INJECTION_PATTERNS.items():
        if pattern.search(text):
            raise PersonaValidationError(f"Potential {pattern_name} detected in input")
    
    # Check for dangerous content
    for content_type, pattern in DANGEROUS_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            if strict_mode or content_type in ['self_harm', 'illegal_activity']:
                raise PersonaValidationError(f"Dangerous content detected: {content_type}")
    
    # Check for excessive repetition (potential spam)
    words = text.split()
    if len(words) > 10:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # If any word appears more than 30% of the time, it's suspicious
        for word, count in word_counts.items():
            if count / len(words) > 0.3:
                raise PersonaValidationError("Excessive repetition detected (potential spam)")
    
    return True


def filter_pii(text: str, replacement: str = "[REDACTED]", keep_types: Optional[List[str]] = None) -> str:
    """
    Filter personally identifiable information from text.
    
    Args:
        text: Input text
        replacement: Replacement string for PII
        keep_types: List of PII types to keep (not filter)
    
    Returns:
        Text with PII filtered out
    """
    result = text
    keep_types = keep_types or []
    
    for pii_type, pattern in PII_PATTERNS.items():
        if pii_type not in keep_types:
            result = pattern.sub(replacement, result)
    
    return result


def detect_injection_attempts(text: str) -> List[str]:
    """
    Detect potential injection attempts in input.
    
    Args:
        text: Input text to analyze
    
    Returns:
        List of detected injection types
    """
    detected = []
    
    for injection_type, pattern in INJECTION_PATTERNS.items():
        if pattern.search(text):
            detected.append(injection_type)
    
    return detected


def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Detect personally identifiable information in text.
    
    Args:
        text: Input text to analyze
    
    Returns:
        Dictionary mapping PII types to found instances
    """
    detected_pii = {}
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            # Convert tuples to strings for phone numbers
            if pii_type == 'phone' and matches:
                matches = [''.join(match) for match in matches]
            detected_pii[pii_type] = matches
    
    return detected_pii


def validate_input_length(text: str, min_length: int = 0, max_length: int = 10000) -> bool:
    """
    Validate input length constraints.
    
    Args:
        text: Input text
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    
    Returns:
        True if length is valid
    
    Raises:
        PersonaValidationError: If length constraints are violated
    """
    length = len(text)
    
    if length < min_length:
        raise PersonaValidationError(f"Input too short: {length} < {min_length}")
    
    if length > max_length:
        raise PersonaValidationError(f"Input too long: {length} > {max_length}")
    
    return True


def validate_character_set(text: str, allowed_chars: Optional[Pattern] = None) -> bool:
    """
    Validate that text contains only allowed characters.
    
    Args:
        text: Input text
        allowed_chars: Regex pattern for allowed characters
    
    Returns:
        True if characters are valid
    
    Raises:
        PersonaValidationError: If invalid characters are found
    """
    if allowed_chars is None:
        # Default: alphanumeric, punctuation, and whitespace
        allowed_chars = re.compile(r'^[\w\s\.\,\!\?\;\:\'\"\-\(\)]+$')
    
    if not allowed_chars.match(text):
        raise PersonaValidationError("Input contains invalid characters")
    
    return True


def clean_whitespace(text: str) -> str:
    """
    Clean and normalize whitespace in text.
    
    Args:
        text: Input text
    
    Returns:
        Text with normalized whitespace
    """
    # Replace various whitespace characters with regular spaces
    text = re.sub(r'[\t\r\n\f\v]+', ' ', text)
    
    # Remove excessive whitespace
    text = re.sub(r' +', ' ', text)
    
    # Trim leading and trailing whitespace
    text = text.strip()
    
    return text


def validate_encoding(text: str, encoding: str = 'utf-8') -> bool:
    """
    Validate that text is properly encoded.
    
    Args:
        text: Input text
        encoding: Expected encoding
    
    Returns:
        True if encoding is valid
    
    Raises:
        PersonaValidationError: If encoding is invalid
    """
    try:
        text.encode(encoding)
        return True
    except UnicodeEncodeError:
        raise PersonaValidationError(f"Invalid {encoding} encoding in input")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Input filename
    
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    # Ensure it's not empty or just dots
    if not filename or filename in ['.', '..']:
        filename = 'sanitized_file'
    
    return filename