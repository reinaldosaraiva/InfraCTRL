"""Registry for tool adapters in the MCP Server."""

from typing import Dict, List, Optional, Type, Any
import logging

from mcp_server.adapters.base import ToolAdapter, Capability

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry for managing tool adapters."""
    
    def __init__(self):
        """Initialize the adapter registry."""
        self._adapter_classes: Dict[str, Type[ToolAdapter]] = {}
        self._adapter_instances: Dict[str, ToolAdapter] = {}
        
    def register_adapter_class(self, adapter_type: str, adapter_class: Type[ToolAdapter]) -> None:
        """
        Register an adapter class.
        
        Args:
            adapter_type: Unique type identifier for the adapter
            adapter_class: Class for the adapter
        """
        if adapter_type in self._adapter_classes:
            logger.warning(f"Overriding existing adapter class: {adapter_type}")
            
        self._adapter_classes[adapter_type] = adapter_class
        logger.info(f"Registered adapter class: {adapter_type}")
        
    def create_adapter_instance(
        self, 
        adapter_type: str, 
        instance_name: str, 
        config: Dict[str, Any]
    ) -> Optional[ToolAdapter]:
        """
        Create and register an adapter instance.
        
        Args:
            adapter_type: Type of adapter to create
            instance_name: Unique name for this instance
            config: Configuration for the adapter
            
        Returns:
            Created adapter instance or None if creation failed
        """
        if adapter_type not in self._adapter_classes:
            logger.error(f"Adapter type not found: {adapter_type}")
            return None
            
        if instance_name in self._adapter_instances:
            logger.warning(f"Overriding existing adapter instance: {instance_name}")
            
        adapter_class = self._adapter_classes[adapter_type]
        
        try:
            adapter = adapter_class(instance_name, config)
            self._adapter_instances[instance_name] = adapter
            logger.info(f"Created adapter instance: {instance_name} (type: {adapter_type})")
            return adapter
        except Exception as e:
            logger.error(f"Failed to create adapter instance: {e}")
            return None
            
    def get_adapter_instance(self, instance_name: str) -> Optional[ToolAdapter]:
        """
        Get an adapter instance by name.
        
        Args:
            instance_name: Name of the adapter instance
            
        Returns:
            Adapter instance or None if not found
        """
        return self._adapter_instances.get(instance_name)
        
    def get_all_adapter_instances(self) -> Dict[str, ToolAdapter]:
        """
        Get all registered adapter instances.
        
        Returns:
            Dictionary of adapter instances by name
        """
        return self._adapter_instances.copy()
        
    def get_available_adapter_types(self) -> List[str]:
        """
        Get the list of available adapter types.
        
        Returns:
            List of adapter type identifiers
        """
        return list(self._adapter_classes.keys())
        
    def get_adapter_class(self, adapter_type: str) -> Optional[Type[ToolAdapter]]:
        """
        Get an adapter class by type.
        
        Args:
            adapter_type: Type of adapter
            
        Returns:
            Adapter class or None if not found
        """
        return self._adapter_classes.get(adapter_type)
        
    def remove_adapter_instance(self, instance_name: str) -> bool:
        """
        Remove an adapter instance.
        
        Args:
            instance_name: Name of the adapter instance
            
        Returns:
            True if removed, False if not found
        """
        if instance_name in self._adapter_instances:
            del self._adapter_instances[instance_name]
            logger.info(f"Removed adapter instance: {instance_name}")
            return True
        else:
            logger.warning(f"Adapter instance not found: {instance_name}")
            return False
            
    def find_adapters_with_capability(self, capability_name: str) -> List[str]:
        """
        Find adapters that support a specific capability.
        
        Args:
            capability_name: Name of the capability
            
        Returns:
            List of adapter instance names
        """
        result = []
        for name, adapter in self._adapter_instances.items():
            if adapter.has_capability(capability_name):
                result.append(name)
        return result
        
    def find_adapters_by_resource_type(self, resource_type: str) -> List[str]:
        """
        Find adapters that support a specific resource type.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            List of adapter instance names
        """
        result = []
        for name, adapter in self._adapter_instances.items():
            for capability in adapter.capabilities:
                if resource_type in capability.resource_types:
                    result.append(name)
                    break
        return result


# Singleton instance
adapter_registry = AdapterRegistry()