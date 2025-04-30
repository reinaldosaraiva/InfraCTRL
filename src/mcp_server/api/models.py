"""Data models for MCP Server API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class CapabilityTypeEnum(str, Enum):
    """Types of capabilities that an adapter can support."""
    
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    EXECUTE = "execute"
    MONITOR = "monitor"


class CapabilityModel(BaseModel):
    """API model for a capability."""
    
    name: str = Field(..., description="Unique name for this capability")
    description: str = Field(..., description="Human-readable description")
    type: CapabilityTypeEnum = Field(..., description="Type of capability")
    resource_types: List[str] = Field(..., description="List of resource types this capability applies to")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for this capability")


class AdapterInfo(BaseModel):
    """API model for adapter information."""
    
    name: str = Field(..., description="Unique name for this adapter instance")
    type: str = Field(..., description="Type of adapter")
    capabilities: List[CapabilityModel] = Field(..., description="List of capabilities supported by this adapter")
    status: str = Field(..., description="Current status of the adapter")
    connected: bool = Field(..., description="Whether the adapter is connected")


class AdapterConfigSchema(BaseModel):
    """API model for adapter configuration schema."""
    
    properties: Dict[str, Any] = Field(..., description="Configuration properties")
    required: List[str] = Field(..., description="Required configuration properties")


class AdapterConfig(BaseModel):
    """API model for adapter configuration."""
    
    type: str = Field(..., description="Type of adapter")
    name: str = Field(..., description="Unique name for this instance")
    config: Dict[str, Any] = Field(..., description="Configuration for this adapter")


class CommandStatusEnum(str, Enum):
    """Status of a command execution."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandRequest(BaseModel):
    """API model for a command request."""
    
    adapter: str = Field(..., description="Adapter instance name")
    capability: str = Field(..., description="Name of the capability to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the capability")
    resource_type: Optional[str] = Field(None, description="Optional resource type")
    resource_id: Optional[str] = Field(None, description="Optional resource ID")


class CommandResponse(BaseModel):
    """API model for a command response."""
    
    id: str = Field(..., description="Unique ID for this command execution")
    adapter: str = Field(..., description="Adapter instance name")
    capability: str = Field(..., description="Name of the capability that was executed")
    status: CommandStatusEnum = Field(..., description="Status of the command execution")
    data: Optional[Any] = Field(None, description="Data returned by the command")
    message: Optional[str] = Field(None, description="Optional message")
    error: Optional[str] = Field(None, description="Optional error message")
    created_at: datetime = Field(..., description="When the command was created")
    updated_at: datetime = Field(..., description="When the command was last updated")


class ApiKeyInfo(BaseModel):
    """API model for API key information."""
    
    id: str = Field(..., description="Unique ID for this API key")
    name: str = Field(..., description="Name of this API key")
    prefix: str = Field(..., description="Prefix of the API key")
    created_at: datetime = Field(..., description="When the API key was created")
    last_used_at: Optional[datetime] = Field(None, description="When the API key was last used")


class ApiKeyCreate(BaseModel):
    """API model for creating an API key."""
    
    name: str = Field(..., description="Name of this API key")


class ApiKeyResponse(BaseModel):
    """API model for API key creation response."""
    
    id: str = Field(..., description="Unique ID for this API key")
    name: str = Field(..., description="Name of this API key")
    key: str = Field(..., description="The API key (only shown once)")
    prefix: str = Field(..., description="Prefix of the API key")
    created_at: datetime = Field(..., description="When the API key was created")


class ErrorResponse(BaseModel):
    """API model for error responses."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")