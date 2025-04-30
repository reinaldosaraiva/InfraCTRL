"""Base adapter interface for MCP Server tool integrations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class CapabilityType(Enum):
    """Types of capabilities that an adapter can support."""
    
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    EXECUTE = "execute"
    MONITOR = "monitor"


class Capability:
    """Representation of a specific capability provided by an adapter."""
    
    def __init__(
        self,
        name: str,
        description: str,
        capability_type: CapabilityType,
        resource_types: List[str],
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a capability.
        
        Args:
            name: Unique name for this capability
            description: Human-readable description
            capability_type: Type of capability (read, write, etc.)
            resource_types: List of resource types this capability applies to
            parameters: Optional parameters for this capability
        """
        self.name = name
        self.description = description
        self.capability_type = capability_type
        self.resource_types = resource_types
        self.parameters = parameters or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert capability to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.capability_type.value,
            "resource_types": self.resource_types,
            "parameters": self.parameters,
        }


class CommandStatus(Enum):
    """Status of a command execution."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Command:
    """Representation of a command to be executed by an adapter."""
    
    def __init__(
        self,
        capability: str,
        parameters: Dict[str, Any],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        """
        Initialize a command.
        
        Args:
            capability: Name of the capability to execute
            parameters: Parameters for the capability
            resource_type: Optional resource type
            resource_id: Optional resource ID
        """
        self.capability = capability
        self.parameters = parameters
        self.resource_type = resource_type
        self.resource_id = resource_id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary representation."""
        result = {
            "capability": self.capability,
            "parameters": self.parameters,
        }
        
        if self.resource_type:
            result["resource_type"] = self.resource_type
            
        if self.resource_id:
            result["resource_id"] = self.resource_id
            
        return result


class CommandResult:
    """Result of a command execution."""
    
    def __init__(
        self,
        status: CommandStatus,
        data: Optional[Any] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize a command result.
        
        Args:
            status: Status of the command execution
            data: Optional data returned by the command
            message: Optional message
            error: Optional error message
        """
        self.status = status
        self.data = data
        self.message = message
        self.error = error
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert command result to dictionary representation."""
        result = {
            "status": self.status.value,
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if self.message:
            result["message"] = self.message
            
        if self.error:
            result["error"] = self.error
            
        return result


class ToolAdapter(ABC):
    """Abstract base class for all tool adapters."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the adapter.
        
        Args:
            name: Unique name for this adapter instance
            config: Configuration for this adapter
        """
        self.name = name
        self.config = config
        self._capabilities: List[Capability] = []
        
    @property
    def capabilities(self) -> List[Capability]:
        """Get the capabilities supported by this adapter."""
        if not self._capabilities:
            self._capabilities = self._get_capabilities()
        return self._capabilities
    
    @abstractmethod
    def _get_capabilities(self) -> List[Capability]:
        """
        Get the capabilities supported by this adapter.
        
        This must be implemented by subclasses.
        
        Returns:
            List of capabilities
        """
        pass
    
    def has_capability(self, capability_name: str) -> bool:
        """
        Check if the adapter supports a specific capability.
        
        Args:
            capability_name: Name of the capability to check
            
        Returns:
            True if the adapter supports the capability, False otherwise
        """
        return any(c.name == capability_name for c in self.capabilities)
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the tool.
        
        Returns:
            True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the tool."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to the tool.
        
        Returns:
            True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(self, command: Command) -> CommandResult:
        """
        Execute a command on the tool.
        
        Args:
            command: Command to execute
            
        Returns:
            Result of the command execution
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this adapter.
        
        Returns:
            Configuration schema as a dictionary
        """
        return {
            "type": "object",
            "properties": self._get_config_schema_properties(),
            "required": self._get_config_schema_required(),
        }
    
    @abstractmethod
    def _get_config_schema_properties(self) -> Dict[str, Any]:
        """
        Get the configuration schema properties for this adapter.
        
        This must be implemented by subclasses.
        
        Returns:
            Configuration schema properties as a dictionary
        """
        pass
    
    @abstractmethod
    def _get_config_schema_required(self) -> List[str]:
        """
        Get the required configuration properties for this adapter.
        
        This must be implemented by subclasses.
        
        Returns:
            List of required configuration property names
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration for this adapter.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required fields
        required_fields = self._get_config_schema_required()
        for field in required_fields:
            if field not in config:
                return False
        
        # Subclasses can override this method to add more validation
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert adapter to dictionary representation."""
        return {
            "name": self.name,
            "capabilities": [c.to_dict() for c in self.capabilities],
        }