"""
Helper utility functions for JEECG A2A Platform.
"""

import re
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def format_timestamp(timestamp: datetime) -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: Datetime object to format
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def sanitize_agent_name(name: str) -> str:
    """
    Sanitize agent name for safe usage.
    
    Args:
        name: Agent name to sanitize
        
    Returns:
        Sanitized agent name
    """
    # Remove special characters and limit length
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', name)
    return sanitized[:100].strip()


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain string or None if invalid
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def calculate_uptime(start_time: datetime) -> dict:
    """
    Calculate uptime from start time.
    
    Args:
        start_time: When the service started
        
    Returns:
        Dictionary with uptime information
    """
    now = datetime.utcnow()
    uptime_delta = now - start_time
    
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "total_seconds": uptime_delta.total_seconds(),
        "formatted": f"{days}d {hours}h {minutes}m {seconds}s"
    }


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_capability_string(capability_str: str) -> list:
    """
    Parse capability string into list of capabilities.
    
    Args:
        capability_str: Comma-separated capability string
        
    Returns:
        List of capability names
    """
    if not capability_str:
        return []
    
    capabilities = [cap.strip() for cap in capability_str.split(',')]
    return [cap for cap in capabilities if cap]


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def is_valid_session_id(session_id: str) -> bool:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not session_id:
        return False
    
    # Check if it's a valid UUID or session format
    try:
        uuid.UUID(session_id)
        return True
    except ValueError:
        # Check if it matches session_* pattern
        return bool(re.match(r'^session_[a-zA-Z0-9]{8,}$', session_id))


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text with potential HTML tags
        
    Returns:
        Clean text without HTML tags
    """
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data like API keys.
    
    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end
        
    Returns:
        Masked string
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]
