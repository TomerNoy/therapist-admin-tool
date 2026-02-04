# Validation Rules

This document describes all validation rules applied to therapist data processing.

## Overview

The pipeline reads therapist data from CSV, validates and transforms it, and outputs valid/invalid rows separately.

## Field Validations

### 1. Timestamp
- **Rule**: Must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- **Transformation**: Converts valid timestamps to ISO format
- **Example Valid**: `2024-01-15T14:30:00`
- **Example Invalid**: `15/01/2024`, `2024-01-15`
- **Error Message**: `Invalid timestamp`

### 2. Email
- **Rule**: Must match email regex pattern
- **Transformation**: Converts to lowercase
- **Pattern**: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **Example Valid**: `therapist@example.com` → `therapist@example.com`
- **Example Invalid**: `not-an-email`, `@example.com`, `user@`
- **Error Message**: `Invalid email`
- **Duplicate Detection**: Flags duplicate email addresses

### 3. Name
- **Rule**: Must contain at least 2 words
- **Example Valid**: `שרה כהן`, `Dr. John Smith`
- **Example Invalid**: `שרה`, `JohnSmith` (single word)
- **Error Message**: `Invalid name: must contain at least 2 words`

### 4. Read Policy
- **Rule**: Must exactly match `קראתי מאשר.ת`
- **Example Valid**: `קראתי מאשר.ת`
- **Example Invalid**: `קראתי`, `כן`, any other value
- **Error Message**: `Invalid read_policy: must be 'קראתי מאשר.ת'`

### 5. Tel (Phone Number)
- **Rule**: Must contain at least 9 characters
- **Transformation**: 
  - Preserves leading `+` if present
  - Removes all non-digit characters except leading `+`
  - Only one `+` allowed at the beginning
- **Example Valid**: 
  - `+972-54-215-1433` → `+972542151433`
  - `050-777-8886` → `0507778886`
- **Example Invalid**: `12345` (too short), `++972` (multiple +)
- **Error Message**: `Invalid tel: must be at least 9 characters`
- **Duplicate Detection**: Flags duplicate phone numbers

### 6. Address
- **Rule**: Must contain at least 2 characters
- **Example Valid**: `רח' הרצל 10, תל אביב`, `123 Main St`
- **Example Invalid**: `א` (too short), empty string
- **Error Message**: `Invalid address: must be at least 2 characters`

### 7. Bio
- **Rule**: 
  - Must contain at least 10 characters
  - Whitespace is normalized (multiple spaces/newlines collapsed)
  - Must not be a placeholder value
- **Transformation**: Normalizes whitespace
- **Placeholder Detection**: Rejects common placeholders like "test", "אין", "לא רלוונטי"
- **Example Valid**: `בעלת ניסיון רב בטיפול משפחתי`
- **Example Invalid**: `קצר מדי`, `test`, `אין`
- **Error Message**: `Invalid bio: must be at least 10 characters and not a placeholder`

### 8. Specialty
- **Rule**: 
  - Must contain at least 3 characters
  - Whitespace is normalized
  - Must not be a placeholder value
- **Transformation**: Normalizes whitespace
- **Placeholder Detection**: Rejects common placeholders
- **Example Valid**: `טיפול משפחתי`, `CBT`
- **Example Invalid**: `א`, `test`, `אין`
- **Error Message**: `Invalid specialty: must be at least 3 characters and not a placeholder`

### 9. Kupat Holim (Health Fund)
- **Rule**: Must be one of the valid values or empty
- **Valid Values**: `מכבי`, `כללית`, `מאוחדת`, `לאומית`, or empty
- **Example Valid**: `מכבי`, `כללית`, `` (empty)
- **Example Invalid**: `מכב"י`, `קופת חולים כללית`
- **Error Message**: `Invalid kupatHolim: must be one of מכבי, כללית, מאוחדת, לאומית, or empty`

### 10. Website
- **Rule**: Must be a valid URL format or None
- **Transformation**: Removes invalid URLs (sets to None)
- **Pattern**: Must include protocol (http/https) and valid domain
- **Example Valid**: `https://example.com`, `http://therapist.co.il`
- **Example Invalid**: `example.com` (no protocol), `not-a-url`
- **Note**: Invalid websites are silently removed (not flagged as error)

### 11. Boolean Fields (hasWhatsApp, isZoom, misradHaBitachon)
- **Rule**: Converts to boolean
- **Transformation**: 
  - `כן` → `True`
  - All other values → `False`
- **Example Valid**: `כן` → `True`, `לא` → `False`, `` → `False`

## Required Fields

All rows must have the following fields populated:
- `timestamp`
- `email`
- `name`
- `readPolicy`
- `tel`
- `address`
- `bio`
- `specialty`

Missing required fields will cause the row to be marked as invalid.

## Duplicate Detection

The system tracks and flags duplicate values for:
- **Email**: Each email address must be unique across all rows
- **Tel**: Each phone number must be unique across all rows

Duplicate rows are marked as invalid with the specific duplicate field indicated in the `failed_at` column.

## Output Structure

### Valid Rows (results_{timestamp}.csv)
- Contains all rows that passed validation
- All transformations applied (lowercased emails, normalized tel, boolean conversions)

### Invalid Rows (invalid_rows_{timestamp}.csv)
- Contains all rows that failed validation
- Includes all original columns plus `failed_at` column
- `failed_at` column lists comma-separated failed field names

### Summary Report (summary_{timestamp}.json and summary_{timestamp}.txt)
- Total rows processed
- Count of valid/invalid rows
- Breakdown of failures by field
- Paths to output files

### Error Log (error_log_{timestamp}.txt)
- Contains processing errors (exceptions, unexpected issues)
- Includes row numbers and error details

## Examples

### Valid Row Example
```csv
timestamp,email,name,readPolicy,tel,address,bio,specialty,hasWhatsApp,isZoom,misradHaBitachon,kupatHolim,website
2024-01-15T14:30:00,sarah@example.com,שרה כהן,קראתי מאשר.ת,+972542151433,רח' הרצל 10 תל אביב,בעלת ניסיון של 15 שנה בטיפול משפחתי,טיפול משפחתי,כן,כן,לא,מכבי,https://sarah-therapist.com
```

### Invalid Row Example (Multiple Issues)
```csv
failed_at,timestamp,email,name,readPolicy,tel,address,bio,specialty,hasWhatsApp,isZoom,misradHaBitachon,kupatHolim,website
"email, tel, bio",2024-01-15T14:30:00,invalid-email,שרה כהן,קראתי מאשר.ת,123,רח' הרצל 10,קצר,טיפול משפחתי,כן,כן,לא,מכבי,
```

## Configuration

All validation constants are centralized in `src/config.py`:
- Minimum length requirements
- Valid value lists
- Regex patterns
- Column mappings

## Error Handling

- Each row is processed independently with try-catch
- Processing errors are logged to error log file
- Failed rows don't stop processing of remaining rows
- All errors include row numbers for debugging
