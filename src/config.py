"""
Configuration file for therapist admin tool.
Contains constants, regex patterns, and validation rules.
"""

# Required fields for Therapist model
REQUIRED_FIELDS = [
    'createdAt', 'name', 'readPolicy', 'email', 'address', 'bio', 'specialty', 'tel'
]

# Valid values for kupat_holim
VALID_KUPAT_HOLIM = ["מכבי", "כללית", "מאוחדת", "לאומית"]

# Boolean field value indicating true
BOOLEAN_TRUE_VALUE = "כן"

# Validation constraints
MIN_BIO_LENGTH = 10
MIN_SPECIALTY_LENGTH = 3
MIN_ADDRESS_LENGTH = 2
MIN_TEL_LENGTH = 9

# Regex patterns
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
WEBSITE_PATTERN = r"^https?://[\w\.-]+(\.[\w\.-]+)+[/\w\-\._~:/?#[\]@!$&'()*+,;=.]*$"
TEL_PATTERN = r"^.{9,}$"

# Placeholder texts to reject
PLACEHOLDER_VALUES = ['n/a', 'na', 'none', 'null', '-']

# CSV column mapping
COLUMN_MAPPING = {
    'name': 'name',
    'tel': 'tel',
    'email': 'email',
    'specialty': 'specialty',
    'bio': 'bio',
    'address': 'address',
    'is_whatsapp': 'hasWhatsApp',
    'is_zoom': 'isZoom',
    'kupat_holim': 'kupatHolim',
    'misrad_habithon': 'misradHaBitachon',
    'other_languages': 'otherLanguages',
    'website': 'website',
    'timestamp': 'createdAt',
    'read_policy': 'readPolicy',
}

# Output file paths (relative to script directory)
INVALID_ROWS_FILENAME = 'invalid_rows'
RESULTS_FILENAME = 'results'
SUMMARY_FILENAME = 'summary'
ERROR_LOG_FILENAME = 'error_log.txt'
