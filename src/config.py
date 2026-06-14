"""
Configuration file for therapist admin tool.
Contains constants, regex patterns, and validation rules.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Required fields for Therapist model
REQUIRED_FIELDS = [
    'createdAt', 'name', 'termsOfUseVersion', 'email', 'city', 'bio', 'specialty', 'tel'
]

# Valid values for kupat_holim
VALID_KUPAT_HOLIM = ["מכבי", "כללית", "מאוחדת", "לאומית"]

# Boolean field value indicating true
BOOLEAN_TRUE_VALUE = "כן"

# Validation constraints
MIN_BIO_LENGTH = 10
MIN_SPECIALTY_LENGTH = 3
MIN_CITY_LENGTH = 2
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
    'city': 'city',
    'address': 'address',
    'is_whatsapp': 'hasWhatsApp',
    'is_zoom': 'isZoom',
    'kupat_holim': 'kupatHolim',
    'misrad_habithon': 'misradHaBitachon',
    'other_languages': 'otherLanguages',
    'website': 'website',
    'timestamp': 'createdAt',
    'read_policy': 'termsOfUseVersion',
}

# Output file paths (relative to script directory)
INVALID_ROWS_FILENAME = 'invalid_rows'
RESULTS_FILENAME = 'results'
SUMMARY_FILENAME = 'summary'
ERROR_LOG_FILENAME = 'error_log.txt'

# Google Sheets integration
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_GID = int(os.environ["SHEET_GID"])
SHEETS_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '../credentials/sheets-service-account.json')
