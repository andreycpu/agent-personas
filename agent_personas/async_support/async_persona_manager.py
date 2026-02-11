"""
Asynchronous persona manager for non-blocking operations.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor
import logging

from ..core.persona import Persona
from ..core.manager import PersonaManager
from ..core.registry import PersonaRegistry


class AsyncPersonaManager:
    """
    Asynchronous wrapper for PersonaManager operations.
    """
    
    def __init__(
        self,
        registry: Optional[PersonaRegistry] = None,
        max_workers: int = 4,
        default_timeout: float = 30.0
    ):
        """
        Initialize async persona manager.
        
        Args:
            registry: PersonaRegistry instance
            max_workers: Maximum number of worker threads
            default_timeout: Default timeout for operations
        """
        self.manager = PersonaManager(registry)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)
        
        # Async callbacks
        self._async_switch_callbacks: List[Callable[[Optional[Persona], Optional[Persona]], Awaitable[None]]] = []
    
    async def register_persona(self, persona: Persona) -> None:
        """
        Asynchronously register a persona.
        
        Args:
            persona: Persona to register
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.manager.register_persona,
            persona
        )
        
        self.logger.info(f"Asynchronously registered persona: {persona.name}")
    
    async def create_persona(
        self,
        name: str,
        description: str = "",
        traits: Optional[Dict[str, float]] = None,
        conversation_style: str = "neutral",
        emotional_baseline: str = "calm",
        metadata: Optional[Dict[str, Any]] = None,
        activate: bool = False
    ) -> Persona:
        """
        Asynchronously create and register a persona.
        
        Args:
            name: Persona name
            description: Persona description
            traits: Trait dictionary
            conversation_style: Conversation style
            emotional_baseline: Emotional baseline
            metadata: Additional metadata
            activate: Whether to activate after creation
            
        Returns:
            Created persona
        """
        loop = asyncio.get_event_loop()
        
        def create_sync():
            return self.manager.create_persona(
                name=name,
                description=description,
                traits=traits,
                conversation_style=conversation_style,
                emotional_baseline=emotional_baseline,
                metadata=metadata,
                activate=activate
            )
        
        persona = await loop.run_in_executor(self.executor, create_sync)
        self.logger.info(f"Asynchronously created persona: {name}")
        return persona
    
    async def activate_persona(self, name: str, timeout: Optional[float] = None) -> bool:
        """
        Asynchronously activate a persona.
        
        Args:
            name: Name of persona to activate
            timeout: Operation timeout
            
        Returns:
            True if successful
        """
        timeout = timeout or self.default_timeout
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self.manager.activate_persona,
                    name
                ),
                timeout=timeout
            )
            
            if result:
                # Trigger async callbacks
                await self._trigger_async_callbacks(None, self.manager.active_persona)
                self.logger.info(f"Asynchronously activated persona: {name}")
            
            return result
        
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout activating persona: {name}")
            return False
    
    async def switch_persona(self, name: str, timeout: Optional[float] = None) -> bool:
        """
        Asynchronously switch to a different persona.
        
        Args:
            name: Name of persona to switch to
            timeout: Operation timeout
            
        Returns:
            True if successful
        """
        timeout = timeout or self.default_timeout
        
        try:
            previous_persona = self.manager.active_persona
            
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self.manager.switch_persona,
                    name
                ),
                timeout=timeout
            )
            
            if result:
                # Trigger async callbacks
                await self._trigger_async_callbacks(previous_persona, self.manager.active_persona)
                self.logger.info(f"Asynchronously switched to persona: {name}")
            
            return result
        
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout switching to persona: {name}")
            return False
    
    async def deactivate_persona(self, timeout: Optional[float] = None) -> Optional[Persona]:
        """
        Asynchronously deactivate the current persona.
        
        Args:
            timeout: Operation timeout
            
        Returns:
            Previously active persona or None
        """
        timeout = timeout or self.default_timeout
        
        try:
            previous_persona = self.manager.active_persona
            
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self.manager.deactivate_persona
                ),
                timeout=timeout
            )
            
            if result:
                # Trigger async callbacks
                await self._trigger_async_callbacks(previous_persona, None)
                self.logger.info("Asynchronously deactivated persona")
            
            return result
        
        except asyncio.TimeoutError:
            self.logger.error("Timeout deactivating persona")
            return None
    
    async def search_personas(self, query: str, timeout: Optional[float] = None) -> List[Persona]:
        """
        Asynchronously search for personas.
        
        Args:
            query: Search query
            timeout: Operation timeout
            
        Returns:
            List of matching personas
        """
        timeout = timeout or self.default_timeout
        
        try:
            loop = asyncio.get_event_loop()
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self.manager.search_personas,
                    query
                ),
                timeout=timeout
            )
            
            self.logger.debug(f"Async search for '{query}' returned {len(results)} results")
            return results
        
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout searching for personas: {query}")
            return []
    
    async def batch_register_personas(
        self,
        personas: List[Persona],
        timeout: Optional[float] = None,
        batch_size: int = 10
    ) -> List[bool]:
        """
        Register multiple personas in batches.
        
        Args:
            personas: List of personas to register
            timeout: Operation timeout per batch
            batch_size: Number of personas per batch
            
        Returns:
            List of success flags for each persona
        """
        results = []
        
        for i in range(0, len(personas), batch_size):
            batch = personas[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self.register_persona(persona) for persona in batch
            ]
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout or self.default_timeout
                )
                
                # All succeeded
                results.extend([True] * len(batch))
                
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout in batch {i//batch_size + 1}")
                results.extend([False] * len(batch))
            except Exception as e:
                self.logger.error(f"Error in batch {i//batch_size + 1}: {e}")
                results.extend([False] * len(batch))
        
        return results
    
    async def concurrent_operations(
        self,
        operations: List[Callable[[], Awaitable[Any]]],
        timeout: Optional[float] = None
    ) -> List[Any]:
        """
        Execute multiple async operations concurrently.
        
        Args:
            operations: List of async operations to execute
            timeout: Total timeout for all operations
            
        Returns:
            List of operation results
        """
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[op() for op in operations], return_exceptions=True),
                timeout=timeout or self.default_timeout
            )
            
            return results
        
        except asyncio.TimeoutError:
            self.logger.error("Timeout in concurrent operations")
            return [None] * len(operations)
    
    def add_async_switch_callback(
        self,
        callback: Callable[[Optional[Persona], Optional[Persona]], Awaitable[None]]
    ) -> None:
        """
        Add an async callback for persona switches.
        
        Args:
            callback: Async callback function
        """
        self._async_switch_callbacks.append(callback)
    
    def remove_async_switch_callback(
        self,
        callback: Callable[[Optional[Persona], Optional[Persona]], Awaitable[None]]
    ) -> None:
        """
        Remove an async switch callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._async_switch_callbacks:
            self._async_switch_callbacks.remove(callback)
    
    async def _trigger_async_callbacks(
        self,
        previous: Optional[Persona],
        current: Optional[Persona]
    ) -> None:
        """Trigger all registered async callbacks."""
        if self._async_switch_callbacks:
            tasks = [
                callback(previous, current)
                for callback in self._async_switch_callbacks
            ]
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"Error in async callback: {e}")
    
    # Sync property accessors
    @property
    def active_persona(self) -> Optional[Persona]:
        """Get currently active persona."""
        return self.manager.active_persona
    
    @property
    def active_persona_name(self) -> Optional[str]:
        """Get name of currently active persona."""
        return self.manager.active_persona_name
    
    async def list_personas(self, timeout: Optional[float] = None) -> List[str]:
        """
        Asynchronously list all persona names.
        
        Args:
            timeout: Operation timeout
            
        Returns:
            List of persona names
        """
        timeout = timeout or self.default_timeout
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self.manager.list_personas
                ),
                timeout=timeout
            )
            
            return result
        
        except asyncio.TimeoutError:
            self.logger.error("Timeout listing personas")
            return []
    
    async def get_status(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Asynchronously get manager status.
        
        Args:
            timeout: Operation timeout
            
        Returns:
            Status dictionary
        """
        timeout = timeout or self.default_timeout
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self.manager.get_status
                ),
                timeout=timeout
            )
            
            # Add async-specific status
            result["async_callbacks"] = len(self._async_switch_callbacks)
            result["executor_threads"] = self.executor._max_workers
            
            return result
        
        except asyncio.TimeoutError:
            self.logger.error("Timeout getting status")
            return {"error": "timeout"}
    
    async def close(self) -> None:
        """Clean up async resources."""
        self.executor.shutdown(wait=True)
        self.logger.info("Async persona manager closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def create_async_persona_manager(
    registry: Optional[PersonaRegistry] = None,
    max_workers: int = 4
) -> AsyncPersonaManager:
    """
    Factory function for creating async persona manager.
    
    Args:
        registry: Optional persona registry
        max_workers: Maximum worker threads
        
    Returns:
        Configured async persona manager
    """
    return AsyncPersonaManager(registry=registry, max_workers=max_workers)