"""API key based authentication for MCP Server."""

import os
import uuid
import secrets
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API key header
X_API_KEY = APIKeyHeader(name="X-API-Key")


class ApiKeyService:
    """Service for managing API keys."""
    
    def __init__(self):
        """Initialize the API key service."""
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._key_by_prefix: Dict[str, str] = {}
        
        # Create default admin key if ADMIN_API_KEY is set
        admin_key = os.environ.get("ADMIN_API_KEY")
        if admin_key:
            # Store key with only the first 8 characters visible
            key_id = str(uuid.uuid4())
            prefix = admin_key[:8]
            self._keys[key_id] = {
                "id": key_id,
                "name": "Default Admin Key",
                "prefix": prefix,
                "key": self._hash_key(admin_key),
                "created_at": datetime.utcnow(),
                "last_used_at": None,
            }
            self._key_by_prefix[prefix] = key_id
            logger.info("Default admin API key loaded")
    
    def create_key(self, name: str) -> Dict[str, Any]:
        """
        Create a new API key.
        
        Args:
            name: Name for the API key
            
        Returns:
            API key information including the full key (only returned once)
        """
        # Generate a random key
        key = secrets.token_urlsafe(32)
        prefix = key[:8]
        
        # Create key info
        key_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Store key
        self._keys[key_id] = {
            "id": key_id,
            "name": name,
            "prefix": prefix,
            "key": self._hash_key(key),
            "created_at": now,
            "last_used_at": None,
        }
        self._key_by_prefix[prefix] = key_id
        
        # Return key info with the full key
        return {
            "id": key_id,
            "name": name,
            "key": key,  # Full key, only returned once
            "prefix": prefix,
            "created_at": now,
        }
    
    def validate_key(self, api_key: str) -> bool:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if the key is valid, False otherwise
        """
        if not api_key:
            return False
            
        # Get prefix
        prefix = api_key[:8]
        
        # Find key by prefix
        key_id = self._key_by_prefix.get(prefix)
        if not key_id:
            return False
            
        # Check key
        key_info = self._keys.get(key_id)
        if not key_info:
            return False
            
        # Update last used
        key_info["last_used_at"] = datetime.utcnow()
        
        # Compare hashed key
        return key_info["key"] == self._hash_key(api_key)
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """
        List all API keys.
        
        Returns:
            List of API key information (without the full key)
        """
        result = []
        for key_id, key_info in self._keys.items():
            # Create a copy without the hashed key
            info = {
                "id": key_info["id"],
                "name": key_info["name"],
                "prefix": key_info["prefix"],
                "created_at": key_info["created_at"],
                "last_used_at": key_info["last_used_at"],
            }
            result.append(info)
        return result
    
    def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Get API key information.
        
        Args:
            key_id: API key ID
            
        Returns:
            API key information (without the full key) or None if not found
        """
        key_info = self._keys.get(key_id)
        if not key_info:
            return None
            
        # Create a copy without the hashed key
        return {
            "id": key_info["id"],
            "name": key_info["name"],
            "prefix": key_info["prefix"],
            "created_at": key_info["created_at"],
            "last_used_at": key_info["last_used_at"],
        }
    
    def delete_key(self, key_id: str) -> bool:
        """
        Delete an API key.
        
        Args:
            key_id: API key ID
            
        Returns:
            True if the key was deleted, False if not found
        """
        key_info = self._keys.get(key_id)
        if not key_info:
            return False
            
        # Remove from both dictionaries
        prefix = key_info["prefix"]
        del self._keys[key_id]
        del self._key_by_prefix[prefix]
        
        return True
    
    def _hash_key(self, key: str) -> str:
        """
        Hash an API key for storage.
        
        In a production environment, this should use a secure hash function.
        For simplicity, we're just returning the key as-is.
        
        Args:
            key: API key to hash
            
        Returns:
            Hashed key
        """
        # In a real implementation, we would use a secure hash function
        # like bcrypt or PBKDF2
        return key


# Singleton instance
api_key_service = ApiKeyService()


async def get_api_key(api_key: str = Depends(X_API_KEY)) -> str:
    """
    Dependency for validating API key.
    
    Args:
        api_key: API key from the X-API-Key header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if not api_key_service.validate_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return api_key