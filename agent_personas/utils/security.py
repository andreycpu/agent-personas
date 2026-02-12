"""
Security utilities for the persona framework.
"""

from typing import Dict, Any, Optional, List, Union
import hashlib
import hmac
import secrets
import base64
import json
import time
import logging
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration."""
    
    def __init__(self):
        self.encryption_enabled = False
        self.api_key_required = False
        self.rate_limiting_enabled = True
        self.session_timeout_minutes = 60
        self.max_login_attempts = 5
        self.password_min_length = 8
        self.require_strong_passwords = True


class EncryptionManager:
    """Manages data encryption and decryption."""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize with encryption key."""
        if key:
            self.key = key
        else:
            self.key = Fernet.generate_key()
        
        self.fernet = Fernet(self.key)
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_password(cls, password: str, salt: Optional[bytes] = None) -> 'EncryptionManager':
        """Create encryption manager from password."""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return cls(key)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64 encoded string."""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.fernet.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted data."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary as JSON."""
        json_data = json.dumps(data)
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt dictionary from JSON."""
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)
    
    def get_key_b64(self) -> str:
        """Get encryption key as base64 string."""
        return base64.b64encode(self.key).decode('utf-8')


class APIKeyManager:
    """Manages API key generation and validation."""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def generate_api_key(self, name: str, permissions: List[str] = None,
                        expires_in_days: Optional[int] = None) -> str:
        """Generate a new API key."""
        api_key = secrets.token_urlsafe(32)
        
        key_data = {
            "name": name,
            "permissions": permissions or [],
            "created_at": datetime.now().isoformat(),
            "expires_at": None,
            "last_used": None,
            "usage_count": 0,
            "active": True
        }
        
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            key_data["expires_at"] = expires_at.isoformat()
        
        self.api_keys[api_key] = key_data
        
        self.logger.info(f"Generated API key for: {name}")
        return api_key
    
    def validate_api_key(self, api_key: str, required_permission: str = None) -> bool:
        """Validate API key and check permissions."""
        if api_key not in self.api_keys:
            self.logger.warning(f"Invalid API key used")
            return False
        
        key_data = self.api_keys[api_key]
        
        # Check if key is active
        if not key_data.get("active", True):
            self.logger.warning(f"Inactive API key used: {key_data['name']}")
            return False
        
        # Check expiration
        if key_data.get("expires_at"):
            expires_at = datetime.fromisoformat(key_data["expires_at"])
            if datetime.now() > expires_at:
                self.logger.warning(f"Expired API key used: {key_data['name']}")
                return False
        
        # Check permissions
        if required_permission:
            permissions = key_data.get("permissions", [])
            if required_permission not in permissions and "*" not in permissions:
                self.logger.warning(f"API key lacks permission '{required_permission}': {key_data['name']}")
                return False
        
        # Update usage tracking
        key_data["last_used"] = datetime.now().isoformat()
        key_data["usage_count"] += 1
        
        return True
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]["active"] = False
            self.logger.info(f"Revoked API key: {self.api_keys[api_key]['name']}")
            return True
        return False
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys (without the actual key values)."""
        return [
            {
                "name": data["name"],
                "permissions": data["permissions"],
                "created_at": data["created_at"],
                "expires_at": data.get("expires_at"),
                "last_used": data.get("last_used"),
                "usage_count": data["usage_count"],
                "active": data["active"]
            }
            for data in self.api_keys.values()
        ]


class RateLimiter:
    """Rate limiting functionality."""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for given identifier."""
        current_time = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        request_times = self.requests[identifier]
        
        # Remove old requests outside window
        cutoff_time = current_time - self.window_seconds
        request_times[:] = [t for t in request_times if t > cutoff_time]
        
        # Check if under limit
        if len(request_times) >= self.max_requests:
            self.logger.warning(f"Rate limit exceeded for: {identifier}")
            return False
        
        # Add current request
        request_times.append(current_time)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        current_time = time.time()
        
        if identifier not in self.requests:
            return self.max_requests
        
        request_times = self.requests[identifier]
        cutoff_time = current_time - self.window_seconds
        recent_requests = len([t for t in request_times if t > cutoff_time])
        
        return max(0, self.max_requests - recent_requests)
    
    def reset_limit(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        if identifier in self.requests:
            del self.requests[identifier]


class SessionManager:
    """Manages user sessions."""
    
    def __init__(self, timeout_minutes: int = 60):
        self.timeout_seconds = timeout_minutes * 60
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_session(self, user_id: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id] = session_data
        
        self.logger.info(f"Created session for user: {user_id}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return session data if valid."""
        if session_id not in self.sessions:
            return None
        
        session_data = self.sessions[session_id]
        current_time = time.time()
        
        # Check timeout
        if current_time - session_data["last_accessed"] > self.timeout_seconds:
            self.logger.info(f"Session expired: {session_id}")
            del self.sessions[session_id]
            return None
        
        # Update last accessed
        session_data["last_accessed"] = current_time
        
        return session_data
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Destroyed session: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data["last_accessed"] > self.timeout_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)


class DataSanitizer:
    """Sanitizes and validates input data."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = None, 
                       allowed_chars: str = None) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Strip whitespace
        value = value.strip()
        
        # Check length
        if max_length and len(value) > max_length:
            raise ValueError(f"String too long (max {max_length} characters)")
        
        # Check allowed characters
        if allowed_chars:
            for char in value:
                if char not in allowed_chars:
                    raise ValueError(f"Invalid character: {char}")
        
        return value
    
    @staticmethod
    def sanitize_persona_name(name: str) -> str:
        """Sanitize persona name."""
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- "
        return DataSanitizer.sanitize_string(name, max_length=100, allowed_chars=allowed_chars)
    
    @staticmethod
    def sanitize_trait_value(value: Union[int, float]) -> float:
        """Sanitize trait value."""
        if not isinstance(value, (int, float)):
            raise ValueError("Trait value must be numeric")
        
        value = float(value)
        
        if not 0.0 <= value <= 1.0:
            raise ValueError("Trait value must be between 0.0 and 1.0")
        
        return value
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], allowed_keys: List[str] = None) -> Dict[str, Any]:
        """Sanitize dictionary input."""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        if allowed_keys:
            sanitized = {}
            for key in allowed_keys:
                if key in data:
                    sanitized[key] = data[key]
            return sanitized
        
        return data


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """Hash password with salt."""
    if salt is None:
        salt = secrets.token_bytes(32)
    
    # Use PBKDF2 with SHA256
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    # Return base64 encoded hash and salt
    return (
        base64.b64encode(pwdhash).decode('utf-8'),
        base64.b64encode(salt).decode('utf-8')
    )


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt = base64.b64decode(stored_salt.encode('utf-8'))
        stored_hash_bytes = base64.b64decode(stored_hash.encode('utf-8'))
        
        # Hash the provided password
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        
        # Compare hashes using constant-time comparison
        return hmac.compare_digest(pwdhash, stored_hash_bytes)
        
    except Exception:
        return False


def create_signature(data: str, secret_key: str) -> str:
    """Create HMAC signature for data."""
    signature = hmac.new(
        secret_key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signature(data: str, signature: str, secret_key: str) -> bool:
    """Verify HMAC signature."""
    expected_signature = create_signature(data, secret_key)
    return hmac.compare_digest(signature, expected_signature)


class SecurityManager:
    """Central security manager."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.encryption_manager = None
        self.api_key_manager = APIKeyManager()
        self.rate_limiter = RateLimiter()
        self.session_manager = SessionManager(config.session_timeout_minutes)
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption if enabled
        if config.encryption_enabled:
            self.encryption_manager = EncryptionManager()
    
    def encrypt_sensitive_data(self, data: Any) -> str:
        """Encrypt sensitive data if encryption is enabled."""
        if not self.config.encryption_enabled or not self.encryption_manager:
            return data
        
        if isinstance(data, dict):
            return self.encryption_manager.encrypt_dict(data)
        else:
            return self.encryption_manager.encrypt(str(data))
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Any:
        """Decrypt sensitive data if encryption is enabled."""
        if not self.config.encryption_enabled or not self.encryption_manager:
            return encrypted_data
        
        try:
            # Try to decrypt as dict first
            return self.encryption_manager.decrypt_dict(encrypted_data)
        except (json.JSONDecodeError, ValueError):
            # Fall back to string decryption
            return self.encryption_manager.decrypt(encrypted_data)
    
    def validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize request data."""
        validated_data = {}
        
        # Sanitize common fields
        if "name" in request_data:
            validated_data["name"] = DataSanitizer.sanitize_persona_name(request_data["name"])
        
        if "description" in request_data:
            validated_data["description"] = DataSanitizer.sanitize_string(
                request_data["description"], max_length=1000
            )
        
        if "traits" in request_data and isinstance(request_data["traits"], dict):
            validated_traits = {}
            for trait_name, trait_value in request_data["traits"].items():
                sanitized_name = DataSanitizer.sanitize_string(trait_name, max_length=50)
                sanitized_value = DataSanitizer.sanitize_trait_value(trait_value)
                validated_traits[sanitized_name] = sanitized_value
            validated_data["traits"] = validated_traits
        
        return validated_data
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security system statistics."""
        return {
            "encryption_enabled": self.config.encryption_enabled,
            "api_key_required": self.config.api_key_required,
            "rate_limiting_enabled": self.config.rate_limiting_enabled,
            "active_sessions": len(self.session_manager.sessions),
            "api_keys_count": len(self.api_key_manager.api_keys),
            "rate_limit_window": self.rate_limiter.window_seconds,
            "max_requests_per_window": self.rate_limiter.max_requests
        }