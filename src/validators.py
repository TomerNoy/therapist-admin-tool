import re
from datetime import datetime
from config import (
    EMAIL_PATTERN, WEBSITE_PATTERN, TEL_PATTERN, MIN_BIO_LENGTH, 
    MIN_SPECIALTY_LENGTH, MIN_ADDRESS_LENGTH, MIN_TEL_LENGTH, PLACEHOLDER_VALUES, VALID_KUPAT_HOLIM
)
from utils import normalize_whitespace, is_placeholder


def validate_website(website):
    """
    Validates that the website is a valid URL (http(s)://...). If not, returns None (removes it).
    Returns (website or None, error_message or None)
    """
    if not website or not isinstance(website, str) or not website.strip():
        return None, None
    website = website.strip()
    if re.match(WEBSITE_PATTERN, website):
        return website, None
    return None, None


def validate_address(address):
    """
    Validates that the address is more than 1 character.
    Returns (address, error_message)
    """
    if not address or not isinstance(address, str) or not address.strip():
        return None, "Missing address"
    address = address.strip()
    if len(address) >= MIN_ADDRESS_LENGTH:
        return address, None
    return address, f"Invalid address: {address} (must be at least {MIN_ADDRESS_LENGTH} characters)"


def validate_tel(tel):
    """
    Validates that the tel is at least 9 characters (regex: ^.{9,}$).
    Returns (tel, error_message)
    """
    if not tel or not isinstance(tel, str) or not tel.strip():
        return None, "Missing tel"
    tel = tel.strip()
    if re.match(TEL_PATTERN, tel):
        return tel, None
    return tel, f"Invalid tel: {tel} (must be at least {MIN_TEL_LENGTH} characters)"


def validate_email(email):
    """
    Validates an email string. Returns (email, error_message)
    """
    if not email or not isinstance(email, str) or not email.strip():
        return None, "Missing email"
    email = email.strip()
    if re.match(EMAIL_PATTERN, email):
        return email, None
    return email, f"Invalid email: {email}"


def validate_read_policy(read_policy):
    """
    Validates that the read_policy is exactly 'קראתי מאשר.ת' and converts to termsOfUseVersion '1.1'.
    Returns (termsOfUseVersion, error_message)
    """
    if not read_policy or not isinstance(read_policy, str) or not read_policy.strip():
        return None, "Missing read_policy"
    read_policy = read_policy.strip()
    if read_policy == "קראתי מאשר.ת":
        return "1.1", None
    return None, f"Invalid read_policy: {read_policy} (must be 'קראתי מאשר.ת')"


def validate_name(name):
    """
    Validates that the name contains at least two words (first and last name).
    Returns (name, error_message)
    """
    if not name or not isinstance(name, str) or not name.strip():
        return None, "Missing name"
    name = name.strip()
    if len(name.split()) >= 2:
        return name, None
    return name, f"Invalid name (must have at least two words): {name}"


def validate_and_transform_timestamp(ts):
    """
    Validates and transforms a timestamp string to ISO 8601 UTC format.
    Returns (iso_timestamp, error_message)
    """
    if ts and isinstance(ts, str) and ts.strip():
        try:
            dt = datetime.strptime(ts.strip(), "%d/%m/%Y %H:%M:%S")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), None
        except Exception:
            return None, f"Invalid createdAt: {ts}"
    return None, "Missing createdAt"


def validate_bio(bio):
    """
    Validates that bio is at least 10 characters, normalizes whitespace, and checks for placeholders.
    Returns (bio, error_message)
    """
    if not bio or not isinstance(bio, str):
        return None, "Missing bio"
    bio = normalize_whitespace(bio)
    if not bio:
        return None, "Missing bio"
    # Check for placeholder text
    if is_placeholder(bio, PLACEHOLDER_VALUES):
        return None, "Bio contains placeholder text"
    if len(bio) < MIN_BIO_LENGTH:
        return bio, f"Invalid bio: too short (minimum {MIN_BIO_LENGTH} characters, got {len(bio)})"
    return bio, None


def validate_specialty(specialty):
    """
    Validates that specialty is at least 3 characters, normalizes whitespace, and checks for placeholders.
    Returns (specialty, error_message)
    """
    if not specialty or not isinstance(specialty, str):
        return None, "Missing specialty"
    specialty = normalize_whitespace(specialty)
    if not specialty:
        return None, "Missing specialty"
    # Check for placeholder text
    if is_placeholder(specialty, PLACEHOLDER_VALUES):
        return None, "Specialty contains placeholder text"
    if len(specialty) < MIN_SPECIALTY_LENGTH:
        return specialty, f"Invalid specialty: too short (minimum {MIN_SPECIALTY_LENGTH} characters, got {len(specialty)})"
    return specialty, None


def validate_kupat_holim(kupat_holim):
    """
    Validates that kupat_holim is one of the valid values or empty.
    Returns (kupat_holim, error_message)
    """
    if not kupat_holim or not isinstance(kupat_holim, str):
        return None, None  # Empty is valid
    kupat_holim = kupat_holim.strip()
    if not kupat_holim:
        return None, None  # Empty is valid
    if kupat_holim in VALID_KUPAT_HOLIM:
        return kupat_holim, None
    return kupat_holim, f"Invalid kupat_holim: {kupat_holim} (must be one of {', '.join(VALID_KUPAT_HOLIM)} or empty)"
