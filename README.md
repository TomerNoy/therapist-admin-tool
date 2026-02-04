# Therapist Admin Tool

A Python-based data processing pipeline for validating, transforming, and preparing therapist data for Firebase upload.

## Overview

This tool processes therapist data from a CSV spreadsheet, validates each field according to business rules, transforms the data into a standardized format, and prepares it for upload to a Firebase database. It includes comprehensive error handling, duplicate detection, and detailed reporting.

## Features

- **Comprehensive Validation**: Validates 10+ fields with specific rules (email format, phone numbers, required text lengths, etc.)
- **Data Transformation**: Normalizes phone numbers, converts booleans, lowercases emails
- **Duplicate Detection**: Identifies duplicate emails and phone numbers across all rows
- **Error Handling**: Processes each row independently with try-catch, logs all errors
- **Summary Reports**: Generates JSON and text summaries with statistics and failure breakdowns
- **Timestamped Outputs**: All output files include timestamps for version tracking
- **Modular Architecture**: Clean separation of concerns across multiple modules

## Project Structure

```
therapist-admin-tool/
├── README.md                          # This file
├── VALIDATION_RULES.md               # Detailed validation documentation
├── requirements.txt                  # Python dependencies
├── credentials/
│   └── firebase-service-account.json # Firebase credentials (gitignored)
├── data/
│   └── raw_spreadsheet.csv          # Input CSV file
└── src/
    ├── main.py                       # Main pipeline orchestration
    ├── config.py                     # Configuration and constants
    ├── validators.py                 # Field validation functions
    ├── model.py                      # Therapist data model
    ├── utils.py                      # Helper functions
    ├── geocoder.py                   # Geolocation extraction (future)
    └── firebase_loader.py            # Firebase upload (future)
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the processing pipeline:
```bash
cd src
python main.py
```

### Output Files

Each run generates timestamped files:

- **`results_{timestamp}.csv`**: Valid rows ready for upload
- **`invalid_rows_{timestamp}.csv`**: Invalid rows with `failed_at` column indicating which fields failed
- **`summary_{timestamp}.json`**: Detailed statistics in JSON format
- **`summary_{timestamp}.txt`**: Human-readable summary report
- **`error_log_{timestamp}.txt`**: Processing errors (if any occurred)

### Example Summary Output

```
Therapist Data Processing Summary
Generated: 2026-02-03T12:52:06
==================================================

Total rows processed: 67
Valid rows: 49
Invalid rows: 18

Failure breakdown by field:
  kupat_holim: 17
  read_policy: 1
  specialty: 1
  tel: 1
```

## Validation Rules

See [VALIDATION_RULES.md](VALIDATION_RULES.md) for comprehensive documentation of all validation rules.

### Key Validations

- **Email**: Must be valid format, converted to lowercase, checked for duplicates
- **Tel**: Minimum 9 characters, normalized (preserves leading +), checked for duplicates
- **Name**: At least 2 words
- **Bio**: Minimum 10 characters, no placeholders
- **Specialty**: Minimum 3 characters, no placeholders
- **Kupat Holim**: Must be one of מכבי, כללית, מאוחדת, לאומית, or empty
- **Read Policy**: Must exactly match "קראתי מאשר.ת"

## Module Documentation

### main.py
Main pipeline orchestration with four key functions:
- `read_csv()`: Reads and maps CSV columns
- `validate_row()`: Validates and transforms a single row
- `write_outputs()`: Writes results, invalid rows, and summaries
- `read_and_map_therapists()`: Coordinates the entire pipeline

### config.py
Central configuration containing:
- Required field names
- Valid value lists (e.g., kupat holim options)
- Minimum length requirements
- Regex patterns for validation
- Column name mappings

### validators.py
Individual validation functions for each field:
- `validate_email()`, `validate_tel()`, `validate_name()`, etc.
- Each returns `(value, error_message)` tuple
- Uses config constants for consistency

### model.py
`Therapist` class representing the data model:
- `required_fields`: List of mandatory fields
- `is_valid()`: Checks if all required fields are present
- `missing_fields()`: Returns list of missing required fields

### utils.py
Helper functions for data transformation:
- `normalize_tel()`: Phone number normalization
- `normalize_boolean()`: Boolean conversion (כן → True)
- `normalize_whitespace()`: Whitespace cleanup
- `get_timestamp_filename()`: Timestamp generation
- `is_placeholder()`: Placeholder text detection

## Data Flow

```
CSV Input
    ↓
Read & Map Columns (config.COLUMN_MAPPING)
    ↓
For Each Row:
    ↓
    Validate & Transform (validators.py)
    ↓
    Check Duplicates (seen_emails, seen_tels)
    ↓
    Error Handling (try-catch)
    ↓
    Categorize (valid vs invalid)
    ↓
Write Outputs:
    ├── results_{timestamp}.csv
    ├── invalid_rows_{timestamp}.csv
    ├── summary_{timestamp}.json
    └── summary_{timestamp}.txt
```

## Future Enhancements

- **Geolocation**: Extract latitude/longitude from addresses using geocoder.py
- **Firebase Upload**: Upload validated data to Firebase database using firebase_loader.py
- **Batch Processing**: Support for processing multiple CSV files
- **API Integration**: REST API for remote processing

## Error Handling

The pipeline includes comprehensive error handling:
- Each row processed independently (one failure doesn't stop others)
- All exceptions caught and logged to error_log_{timestamp}.txt
- Processing continues even if individual rows fail
- Detailed error messages include row numbers for debugging

## Contributing

When adding new validations:
1. Add constants to `config.py`
2. Create validator function in `validators.py`
3. Update `validate_row()` in `main.py`
4. Document in `VALIDATION_RULES.md`

## License

[Add license information]

## Contact

[Add contact information]
