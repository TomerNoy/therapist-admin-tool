# Therapist Admin Tool

A Python-based data processing pipeline for validating, transforming, and preparing therapist data for Firebase upload.

## Overview

This tool processes therapist data from a CSV spreadsheet, validates each field according to business rules, transforms the data into a standardized format, and prepares it for upload to a Firebase database. It includes comprehensive error handling, duplicate detection, and detailed reporting.

## Features

- **Comprehensive Validation**: Validates 10+ fields with specific rules (email format, phone numbers, required text lengths, etc.)
- **Geocoding Integration**: Automatic address geocoding with ArcGIS and Nominatim fallback, 98.4% success rate
- **Data Transformation**: Normalizes phone numbers, converts booleans, lowercases emails, parses list fields
- **Duplicate Detection**: Identifies duplicate emails and phone numbers across all rows
- **Hash-Based Change Tracking**: Detects changes in therapist data to optimize Firebase operations
- **Firebase Integration**: Direct upload to Firestore with smart update detection
- **Error Handling**: Processes each row independently with try-catch, logs all errors
- **Summary Reports**: Generates JSON and text summaries with statistics and failure breakdowns
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
│   ├── raw_spreadsheet.csv          # Input CSV file
│   └── geocache.json                 # Geocoding cache (auto-generated)
└── src/
    ├── main.py                       # Main validation pipeline
    ├── config.py                     # Configuration and constants
    ├── validators.py                 # Field validation functions
    ├── model.py                      # Therapist data model
    ├── utils.py                      # Helper functions (includes hash calculation)
    ├── geocoder.py                   # Address geocoding (ArcGIS + Nominatim)
    ├── firebase_loader.py            # Firebase/Firestore operations
    ├── upload_results_to_firebase.py # Upload script with change tracking
    ├── upload_fake_therapist.py      # Example script for testing Firebase upload
    ├── generate_tracking.py          # One-time script to backfill tracking file
    ├── results.csv                   # Validated data ready for upload (gitignored)
    ├── invalid_rows.csv              # Invalid rows for review (gitignored)
    ├── summary.json                  # Processing statistics (gitignored)
    └── uploaded_therapists.json      # Tracking file (gitignored)
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Process and Validate Data

Run the validation pipeline with geocoding:
```bash
cd src
python main.py
```

This will:
- Validate all therapist data from `raw_spreadsheet.csv`
- Geocode addresses using ArcGIS (with Nominatim fallback)
- Generate `results.csv` with validated data including latitude/longitude
- Cache geocoded addresses in `geocache.json` for efficiency

### 2. Upload to Firebase

Upload validated therapists to Firestore with smart change detection:
```bash
python upload_results_to_firebase.py
```

This will:
- Check `uploaded_therapists.json` tracking file
- Calculate hash of key fields for each therapist
- Upload NEW therapists
- UPDATE therapists with changed data
- SKIP unchanged therapists (zero Firebase queries)

**Dry-run mode** (preview without uploading):
```bash
python upload_results_to_firebase.py --dry-run
```

### Output Files

The pipeline generates these files:

- **`results.csv`**: Valid therapists ready for Firebase upload (includes lat/long)
- **`invalid_rows.csv`**: Invalid rows with `failed_at` column indicating failed fields
- **`summary.json`**: Processing statistics in JSON format
- **`geocache.json`**: Cached geocoding results (speeds up subsequent runs)
- **`uploaded_therapists.json`**: Tracking file with UUIDs and data hashes (auto-generated on first upload)

### Example Summary Output

```
Validation results:
Row 1 issues: ['Missing specialty', 'Missing tel', "Invalid termsOfUseVersion"]

Geocoding Statistics:
  Total addresses processed: 72
  Successfully geocoded: 71
  Failed to geocode: 1

==================================================
Summary:
  Total rows: 76
  Valid: 75
  Invalid: 1
==================================================
```

## Hash-Based Change Tracking

The upload system uses MD5 hashing to detect changes and optimize Firebase operations:

### Tracked Fields (13 total)

These fields are included in the hash calculation:
- Core identity: `name`, `tel`, `email`, `address`
- Content: `bio`, `specialty`, `otherLanguages`, `website`
- Service options: `hasWhatsApp`, `isZoom`, `misradHaBitachon`, `kupatHolim`
- Terms: `termsOfUseVersion`

### Excluded Fields

Not included in hash (auto-generated or dynamic):
- `latitude`, `longitude` (geocoded coordinates)
- `createdAt`, `updatedAt`, `uploadedAt` (timestamps)
- `uuid` (Firebase document ID)

### Upload Behavior

- **NEW**: Therapist email not in `uploaded_therapists.json` → upload as new document
- **UPDATE**: Email exists but hash changed → update existing document with new `updatedAt`
- **SKIP**: Email exists and hash matches → zero Firebase queries, zero cost

### First-Time Setup

If you already have therapists in Firebase, generate the tracking file:
```bash
python generate_tracking.py
```

This queries all existing therapists once and creates `uploaded_therapists.json` with their current hashes.

## Validation Rules

See [VALIDATION_RULES.md](VALIDATION_RULES.md) for comprehensive documentation of all validation rules.

### Key Validations

- **Email**: Must be valid format, converted to lowercase, checked for duplicates
- **Tel**: Minimum 9 characters, normalized (preserves leading +), checked for duplicates
- **Name**: At least 2 words
- **Bio**: Minimum 10 characters, no placeholders
- **Specialty**: Minimum 3 characters, no placeholders
- **Kupat Holim**: Must be one of מכבי, כללית, מאוחדת, לאומית, or empty
- **Terms of Use Version**: Must exactly match "קראתי מאשר.ת" → stored as "1.1"
- **Address**: Automatically geocoded to latitude/longitude
- **Other Languages**: Comma-separated string converted to list

## Module Documentation

### main.py
Main validation pipeline with geocoding integration:
- Reads and validates `raw_spreadsheet.csv`
- Geocodes addresses using ArcGIS geocoder (98.4% success rate)
- Falls back to Nominatim if ArcGIS fails
- Caches geocoding results in `geocache.json`
- Generates `results.csv` with validated data and coordinates

### upload_results_to_firebase.py
Smart upload script with hash-based change tracking:
- Loads `uploaded_therapists.json` tracking file
- Calculates MD5 hash of 13 key fields per therapist
- Categorizes each therapist as NEW/UPDATE/SKIP
- Uploads only new or changed therapists to Firestore
- Updates tracking file with new hashes and timestamps
- Supports `--dry-run` flag for safe testing

### geocoder.py
Address geocoding with multiple providers:
- Primary: ArcGIS geocoder (free tier, no API key required)
- Fallback: Nominatim (OpenStreetMap)
- Persistent cache in `geocache.json`
- Returns latitude/longitude or None if geocoding fails

### firebase_loader.py
Firestore database operations:
- `add_therapist()`: Create new therapist document
- `update_therapist()`: Update existing therapist document
- `check_duplicate()`: Query by email or phone
- Automatic data cleaning (parses string list representations)
- UUID generation for document IDs

### generate_tracking.py
One-time script to backfill tracking data:
- Queries all existing therapists from Firebase
- Calculates hash for each based on `results.csv`
- Creates `uploaded_therapists.json` with UUIDs and hashes
- Run this if you have existing Firebase data before using upload script

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
Helper functions for data transformation and tracking:
- `normalize_tel()`: Phone number normalization
- `normalize_boolean()`: Boolean conversion (כן → True)
- `normalize_whitespace()`: Whitespace cleanup
- `is_placeholder()`: Placeholder text detection
- `calculate_therapist_hash()`: MD5 hash of 13 key fields for change detection

## Data Flow

```
CSV Input (raw_spreadsheet.csv)
    ↓
Read & Map Columns (config.COLUMN_MAPPING)
    ↓
For Each Row:
    ↓
    Validate & Transform (validators.py)
    ↓
    Check Duplicates (seen_emails, seen_tels)
    ↓
    Geocode Address (geocoder.py → geocache.json)
    ↓
    Error Handling (try-catch)
    ↓
    Categorize (valid vs invalid)
    ↓
Write Outputs:
    ├── results.csv (with lat/long)
    ├── invalid_rows.csv
    └── summary.json
    
═══════════════════════════════════════

Firebase Upload (upload_results_to_firebase.py)
    ↓
Load uploaded_therapists.json
    ↓
For Each Therapist in results.csv:
    ↓
    Calculate Hash (13 fields)
    ↓
    Check if Email in Tracking:
        ├─ Not Found → NEW (upload)
        ├─ Hash Differs → UPDATE (update document)
        └─ Hash Matches → SKIP (no Firebase call)
    ↓
Update Tracking File:
    └── uploaded_therapists.json (with new hashes)
```

## Configuration

### Firebase Setup

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Create a Firestore database
3. Generate a service account key:
   - Project Settings → Service Accounts → Generate New Private Key
4. Save as `credentials/firebase-service-account.json`

### Geocoding

The tool uses ArcGIS geocoder in free tier mode (no API key required). Results are cached in `geocache.json` to minimize API calls.

### Tracking File

`uploaded_therapists.json` stores:
```json
{
  "email@example.com": {
    "uuid": "firestore-document-id",
    "data_hash": "md5-hash-of-13-fields",
    "uploaded_at": "2026-02-05T12:30:00Z",
    "updated_at": "2026-02-05T12:30:00Z"
  }
}
```

**Important**: Add to `.gitignore` as it contains Firebase UUIDs.

## Future Enhancements

- **Batch Processing**: Support for processing multiple CSV files
- **API Integration**: REST API for remote processing
- **Admin Dashboard**: Web interface for monitoring uploads
- **Webhook Notifications**: Alerts for failed geocoding or validation errors

## Error Handling

The pipeline includes comprehensive error handling:
- Each row processed independently (one failure doesn't stop others)
- Geocoding failures are logged but don't block processing (lat/long set to None)
- All exceptions caught and logged with row numbers
- Firebase upload failures are reported but don't stop the batch
- Dry-run mode allows safe testing before actual uploads

## Contributing

When adding new validations:
1. Add constants to `config.py`
2. Create validator function in `validators.py`
3. Update `validate_row()` in `main.py`
4. Update hash calculation in `utils.py` if field should trigger updates
5. Document in `VALIDATION_RULES.md`

## License

MIT License — see [LICENSE](LICENSE) for details.
