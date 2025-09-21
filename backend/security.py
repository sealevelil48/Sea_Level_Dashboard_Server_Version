"""
Security utilities and configurations for Sea Level Monitoring System
"""
import re
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def sanitize_log_input(input_str: str) -> str:
        """Sanitize input for logging to prevent log injection"""
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Remove newlines and control characters
        sanitized = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', '', input_str)
        
        # Limit length to prevent log flooding
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."
        
        return sanitized
    
    @staticmethod
    def validate_station_name(station: str) -> bool:
        """Validate station name to prevent injection attacks"""
        if not isinstance(station, str):
            return False
        
        # Allow only alphanumeric, spaces, hyphens, and underscores
        pattern = r'^[a-zA-Z0-9\s\-_]+$'
        return bool(re.match(pattern, station)) and len(station) <= 50
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        if not isinstance(filename, str):
            return "invalid_filename"
        
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        sanitized = re.sub(r'\.\.', '', sanitized)  # Remove .. sequences
        
        # Ensure it doesn't start with a dot or dash
        sanitized = sanitized.lstrip('.-')
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized or "default_filename"
    
    @staticmethod
    def validate_url(url: str, allowed_schemes: list = None) -> bool:
        """Validate URL to prevent SSRF attacks"""
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in allowed_schemes:
                return False
            
            # Prevent localhost and private IP access
            hostname = parsed.hostname
            if hostname:
                hostname = hostname.lower()
                
                # Block localhost variants
                if hostname in ['localhost', '127.0.0.1', '::1']:
                    return False
                
                # Block private IP ranges (basic check)
                if (hostname.startswith('192.168.') or 
                    hostname.startswith('10.') or 
                    hostname.startswith('172.')):
                    return False
                
                # Block metadata services
                if hostname == '169.254.169.254':
                    return False
            
            return True
            
        except Exception:
            return False

def secure_log(logger_instance, level: str, message: str, **kwargs):
    """Secure logging function that sanitizes inputs"""
    sanitized_message = SecurityUtils.sanitize_log_input(message)
    
    # Sanitize kwargs
    sanitized_kwargs = {}
    for key, value in kwargs.items():
        sanitized_key = SecurityUtils.sanitize_log_input(str(key))
        sanitized_value = SecurityUtils.sanitize_log_input(str(value))
        sanitized_kwargs[sanitized_key] = sanitized_value
    
    # Log with appropriate level
    log_func = getattr(logger_instance, level.lower(), logger_instance.info)
    if sanitized_kwargs:
        log_func(f"{sanitized_message} - {sanitized_kwargs}")
    else:
        log_func(sanitized_message)