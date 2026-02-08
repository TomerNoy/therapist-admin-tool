"""
Utility functions for data normalization and helper operations.
"""
import re
import hashlib
import json
from datetime import datetime


def calculate_therapist_hash(data):
    """
    Calculate MD5 hash of key therapist fields for change detection.
    
    Args:
        data: Dictionary containing therapist data
        
    Returns:
        String MD5 hash
    """
    key_fields = [
        'name', 'tel', 'email', 'address', 'bio', 'specialty',
        'otherLanguages', 'website', 'hasWhatsApp', 'isZoom', 
        'misradHaBitachon', 'kupatHolim', 'termsOfUseVersion'
    ]
    hash_data = {k: str(data.get(k, '')) for k in key_fields}
    hash_string = json.dumps(hash_data, sort_keys=True)
    return hashlib.md5(hash_string.encode()).hexdigest()


def normalize_tel(tel):
    """
    Normalize phone number: preserve leading + if present, remove all other non-digits.
    
    Args:
        tel: Phone number string
        
    Returns:
        Normalized phone number string or None
    """
    if not tel:
        return None
    tel = tel.strip()
    if tel.startswith('+'):
        return '+' + re.sub(r'\D', '', tel[1:])
    else:
        return re.sub(r'\D', '', tel)


def normalize_boolean(value, true_value="כן"):
    """
    Convert string value to boolean.
    
    Args:
        value: Value to convert
        true_value: String value that represents True
        
    Returns:
        Boolean value
    """
    return True if str(value).strip() == true_value else False


def normalize_whitespace(text):
    """
    Normalize whitespace in text: strip and replace multiple spaces/newlines with single space.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text or None
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text if text else None


def get_timestamp_filename():
    """
    Generate a timestamp string for filename.
    
    Returns:
        Timestamp string in format YYYY-MM-DD_HHMMSS
    """
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def is_placeholder(value, placeholders):
    """
    Check if value is a placeholder.
    
    Args:
        value: Value to check
        placeholders: List of placeholder values
        
    Returns:
        True if value is a placeholder, False otherwise
    """
    if not value or not isinstance(value, str):
        return False
    return value.lower().strip() in placeholders
