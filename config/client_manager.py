"""Azure OpenAI Client Manager - Enhanced with proper cleanup and error handling"""

import atexit
import weakref
from typing import Optional, Dict, Any
import httpx
from langchain_openai import AzureChatOpenAI
from agno.utils.log import logger
import threading
import os
import gc

class AzureOpenAIClientManager:
    """Singleton manager for Azure OpenAI clients with enhanced lifecycle management"""
    
    _instance: Optional['AzureOpenAIClientManager'] = None
    _lock = threading.Lock()
    _clients_registry: Dict[str, Any] = {}
    _http_client: Optional[httpx.Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.azure_config = {
                "api_key": "75bGVIjxjnTYUbcK1RAhTxqgIfrZPDXRVZQHAwsGxmQ7xC2Cx4zfJQQJ99BEACYeBjFXJ3w3AAABACOGimGC",
                "endpoint": "https://gptidk.openai.azure.com/",
                "api_version": "2025-01-01-preview",
                "embedding_deployment": "text-embedding-ada-002",
                "gpt_deployment": "gpt-4o"
            }
            self._initialized = True
            # Register cleanup function
            atexit.register(self._cleanup_all_clients)
            logger.info("Azure OpenAI Client Manager initialized with enhanced cleanup")
    
    def _get_stable_http_client(self) -> httpx.Client:
        """Get or create a stable HTTP client with proper configuration"""
        if self._http_client is None:
            try:
                # Create HTTP client with configuration that works well with httpx 0.27.2
                self._http_client = httpx.Client(
                    timeout=httpx.Timeout(
                        connect=30.0,
                        read=60.0,
                        write=30.0,
                        pool=30.0
                    ),
                    limits=httpx.Limits(
                        max_connections=10,
                        max_keepalive_connections=5
                    ),
                    follow_redirects=True,
                    # Explicitly disable any proxy settings to avoid conflicts
                    # Note: In httpx 0.27.2, this is handled properly
                )
                logger.info("Stable HTTP client created successfully")
            except Exception as e:
                logger.error(f"Failed to create HTTP client: {e}")
                # Fallback to default client
                self._http_client = None
        
        return self._http_client
    
    def get_llm_client(self) -> AzureChatOpenAI:
        """Get or create the LLM client with enhanced configuration"""
        if 'llm' not in self._clients_registry:
            try:
                # Get the stable HTTP client
                http_client = self._get_stable_http_client()
                
                # Create client with enhanced configuration
                client_kwargs = {
                    "openai_api_key": self.azure_config["api_key"],
                    "azure_endpoint": self.azure_config["endpoint"],
                    "api_version": self.azure_config["api_version"],
                    "deployment_name": self.azure_config["gpt_deployment"],
                    "temperature": 0.7,
                    "max_retries": 2,
                    "timeout": 60.0,
                    "streaming": False,
                    "model_kwargs": {}
                }
                
                # Only add http_client if we successfully created one
                if http_client is not None:
                    client_kwargs["http_client"] = http_client
                
                client = AzureChatOpenAI(**client_kwargs)
                
                # Store client reference
                self._clients_registry['llm'] = client
                logger.info("Enhanced LLM client created successfully")
                
            except Exception as e:
                logger.error(f"Failed to create LLM client: {e}")
                raise
        
        return self._clients_registry['llm']
    
    def get_simple_embeddings_config(self) -> Dict[str, str]:
        """Get embeddings configuration instead of client to avoid HTTP issues"""
        return {
            "openai_api_key": self.azure_config["api_key"],
            "azure_endpoint": self.azure_config["endpoint"],
            "api_version": self.azure_config["api_version"],
            "deployment": self.azure_config["embedding_deployment"]
        }
    
    def _cleanup_all_clients(self):
        """Enhanced cleanup with proper resource management"""
        try:
            logger.info("Starting enhanced client cleanup...")
            
            # Clear client registry first
            if self._clients_registry:
                self._clients_registry.clear()
                logger.info("Client registry cleared")
            
            # Properly close HTTP client if it exists
            if self._http_client is not None:
                try:
                    self._http_client.close()
                    logger.info("HTTP client closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing HTTP client: {e}")
                finally:
                    self._http_client = None
            
            # Force garbage collection to clean up any remaining references
            gc.collect()
            logger.info("Enhanced client cleanup completed successfully")
            
        except Exception as e:
            # Don't raise exceptions during cleanup to avoid exit issues
            logger.warning(f"Warning during enhanced cleanup: {e}")
    
    def reset(self):
        """Reset all clients with enhanced cleanup"""
        self._cleanup_all_clients()

# Global instance
client_manager = AzureOpenAIClientManager()

# Convenience functions for easy access
def get_llm_client() -> AzureChatOpenAI:
    """Get the shared LLM client with enhanced reliability"""
    return client_manager.get_llm_client()

def get_embeddings_config() -> Dict[str, str]:
    """Get embeddings configuration instead of client"""
    return client_manager.get_simple_embeddings_config()

def cleanup_clients():
    """Manually trigger enhanced client cleanup"""
    client_manager._cleanup_all_clients()

def reset_clients():
    """Reset all clients with enhanced cleanup"""
    client_manager.reset() 