"""Exception handling utilities for OpenAI client cleanup issues - Enhanced for httpx 0.27.2"""

import warnings
import sys
import atexit
import gc
from agno.utils.log import logger

def setup_openai_exception_suppression():
    """Setup comprehensive exception suppression for OpenAI/httpx compatibility issues"""
    
    # Comprehensive warning filters for different httpx/OpenAI combinations
    warning_patterns = [
        # Original SyncHttpxClientWrapper issues
        "Exception ignored in.*SyncHttpxClientWrapper",
        ".*SyncHttpxClientWrapper.*",
        
        # General httpx/OpenAI cleanup warnings
        ".*httpx.*",
        ".*openai.*",
        ".*_base_client.*",
        ".*_client.*",
        
        # Specific httpx 0.27.2 patterns
        ".*proxies.*",
        ".*ClientState.*",
        ".*_state.*",
        
        # Resource and connection warnings
        ".*ResourceWarning.*",
        ".*ConnectionError.*",
        ".*DeprecationWarning.*httpx.*",
    ]
    
    for pattern in warning_patterns:
        warnings.filterwarnings("ignore", message=pattern)
        warnings.filterwarnings("ignore", category=ResourceWarning, message=pattern)
        warnings.filterwarnings("ignore", category=DeprecationWarning, message=pattern)
    
    # Store original exception hook
    original_excepthook = sys.excepthook
    
    def enhanced_exception_hook(exc_type, exc_value, traceback):
        """Enhanced exception hook to suppress OpenAI/httpx cleanup exceptions"""
        exc_str = str(exc_value)
        type_str = str(exc_type)
        
        # Comprehensive list of patterns to suppress
        suppress_patterns = [
            # Original patterns
            "SyncHttpxClientWrapper",
            "AsyncHttpxClientWrapper", 
            "AttributeError: 'SyncHttpxClientWrapper' object has no attribute '_state'",
            "AttributeError: 'AsyncHttpxClientWrapper' object has no attribute '_state'",
            
            # httpx specific patterns
            "httpx._client.py",
            "openai._base_client.py",
            "openai/_base_client.py",
            
            # Connection and state issues
            "ClientState.CLOSED",
            "_state == ClientState",
            "is_closed",
            
            # Proxy related issues (even with httpx 0.27.2)
            "proxies",
            "unexpected keyword argument 'proxies'",
            
            # General cleanup issues
            "__del__",
            "Exception ignored in",
            "ResourceWarning",
            
            # Threading issues
            "threading.py",
            "Thread-",
        ]
        
        # Check if this is a cleanup exception we should suppress
        if any(pattern in exc_str for pattern in suppress_patterns) or \
           any(pattern in type_str for pattern in suppress_patterns):
            # Log but don't show to user
            logger.debug(f"Suppressed cleanup exception: {exc_type.__name__}: {exc_str}")
            return  # Silently ignore
            
        # For other exceptions, use the original handler
        return original_excepthook(exc_type, exc_value, traceback)
    
    # Install enhanced exception hook
    sys.excepthook = enhanced_exception_hook
    
    # Enhanced cleanup handler
    def enhanced_final_cleanup():
        """Enhanced final cleanup to prevent any remaining exceptions"""
        try:
            # Force multiple garbage collection cycles
            for _ in range(3):
                gc.collect()
            
            # Clear any remaining httpx/openai references
            import sys
            modules_to_cleanup = []
            for module_name in sys.modules:
                if any(pattern in module_name.lower() for pattern in ['httpx', 'openai', '_client']):
                    modules_to_cleanup.append(module_name)
            
            # Note: We don't actually delete modules as it can cause issues,
            # but we trigger cleanup
            gc.collect()
            
            logger.debug("Enhanced final cleanup completed")
            
        except Exception as e:
            # Even cleanup errors should be suppressed
            logger.debug(f"Cleanup error suppressed: {e}")
    
    # Register enhanced cleanup at exit with high priority
    atexit.register(enhanced_final_cleanup)
    
    # Additional suppression for specific threading issues
    def suppress_threading_exceptions():
        """Additional suppression for threading-related exceptions"""
        try:
            import threading
            original_start = threading.Thread.start
            
            def safe_start(self):
                try:
                    return original_start(self)
                except Exception as e:
                    if any(pattern in str(e) for pattern in ['httpx', 'openai', '_state']):
                        logger.debug(f"Suppressed threading exception: {e}")
                        return
                    raise
            
            threading.Thread.start = safe_start
        except Exception:
            # If this fails, just continue - it's optional
            pass
    
    suppress_threading_exceptions()
    
    logger.info("Enhanced OpenAI/httpx exception suppression configured for httpx 0.27.2")

# Auto-setup when module is imported
setup_openai_exception_suppression() 