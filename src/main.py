"""
Main script for processing therapist data from CSV.
Validates, transforms, and outputs data for Firebase upload.
"""

import pandas as pd
import os
import json
from datetime import datetime
from collections import defaultdict

from config import COLUMN_MAPPING, BOOLEAN_TRUE_VALUE, REQUIRED_FIELDS
from validators import (
    validate_and_transform_timestamp, validate_email, validate_name, 
    validate_read_policy, validate_tel, validate_city, validate_address,
    validate_website, validate_bio, validate_specialty, validate_kupat_holim
)
from model import Therapist
from utils import normalize_tel, normalize_boolean
from geocoder import Geocoder


def read_csv(csv_path):
    """
    Read and preprocess CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        pandas DataFrame with mapped columns
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        abs_path = os.path.join(os.path.dirname(__file__), '../data/raw_spreadsheet.csv')
        print(f"Trying absolute path: {os.path.abspath(abs_path)}")
        df = pd.read_csv(abs_path)

    # Drop columns that start with 'ignored' or are completely empty
    df = df[[col for col in df.columns if not col.startswith('ignored') and not df[col].isnull().all()]]

    # Rename columns according to mapping
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    print("Mapped DataFrame columns:", list(df.columns))
    print(df.head())
    
    return df


def validate_row(row_dict, idx, seen_emails, seen_tels, error_log):
    """
    Validate and transform a single row.
    
    Args:
        row_dict: Dictionary of row data
        idx: Row index (for error reporting)
        seen_emails: Set of seen email addresses (for duplicate detection)
        seen_tels: Set of seen phone numbers (for duplicate detection)
        error_log: List to append errors to
        
    Returns:
        Tuple of (validated_row_dict, issues_list)
    """
    issues = []
    
    try:
        # Website validation (remove if not valid)
        website, _ = validate_website(row_dict.get('website'))
        row_dict['website'] = website

        # Skip row if all fields are empty or NaN
        if all((str(cell).strip() == '' or pd.isna(cell)) for cell in row_dict.values()):
            return None, ['empty_row']

        # Timestamp validation and transformation
        iso_ts, ts_flag = validate_and_transform_timestamp(row_dict.get('createdAt'))
        row_dict['createdAt'] = iso_ts
        if ts_flag:
            issues.append(ts_flag)

        # Email validation and normalization (lowercase)
        email, email_flag = validate_email(row_dict.get('email'))
        if email:
            email = email.lower()
            # Check for duplicate email
            if email in seen_emails:
                issues.append(f"Duplicate email: {email}")
            else:
                seen_emails.add(email)
        row_dict['email'] = email
        if email_flag:
            issues.append(email_flag)

        # Name validation
        name, name_flag = validate_name(row_dict.get('name'))
        row_dict['name'] = name
        if name_flag:
            issues.append(name_flag)

        # Boolean conversions
        row_dict['hasWhatsApp'] = normalize_boolean(row_dict.get('hasWhatsApp'), BOOLEAN_TRUE_VALUE)
        row_dict['isZoom'] = normalize_boolean(row_dict.get('isZoom'), BOOLEAN_TRUE_VALUE)
        row_dict['misradHaBitachon'] = normalize_boolean(row_dict.get('misradHaBitachon'), BOOLEAN_TRUE_VALUE)

        # Convert otherLanguages from comma-separated string to list
        other_languages = row_dict.get('otherLanguages')
        if other_languages and isinstance(other_languages, str):
            # Split by comma, strip whitespace, and filter empty strings
            row_dict['otherLanguages'] = [lang.strip() for lang in other_languages.split(',') if lang.strip()]
        elif not other_languages or (isinstance(other_languages, float) and pd.isna(other_languages)):
            # If None or NaN, set to empty list
            row_dict['otherLanguages'] = []
        
        # City validation (required)
        city, city_flag = validate_city(row_dict.get('city'))
        row_dict['city'] = city
        if city_flag:
            issues.append(city_flag)

        # Address/street validation (optional)
        address, address_flag = validate_address(row_dict.get('address'))
        row_dict['address'] = address
        if address_flag:
            issues.append(address_flag)

        # Bio validation
        bio, bio_flag = validate_bio(row_dict.get('bio'))
        row_dict['bio'] = bio
        if bio_flag:
            issues.append(bio_flag)

        # Specialty validation
        specialty, specialty_flag = validate_specialty(row_dict.get('specialty'))
        row_dict['specialty'] = specialty
        if specialty_flag:
            issues.append(specialty_flag)

        # Kupat Holim validation
        kupat_holim, kupat_holim_flag = validate_kupat_holim(row_dict.get('kupatHolim'))
        row_dict['kupatHolim'] = kupat_holim
        if kupat_holim_flag:
            issues.append(kupat_holim_flag)

        # Tel validation and normalization
        tel, tel_flag = validate_tel(row_dict.get('tel'))
        if tel:
            tel = normalize_tel(tel)
            # Check for duplicate tel
            if tel in seen_tels:
                issues.append(f"Duplicate tel: {tel}")
            else:
                seen_tels.add(tel)
        row_dict['tel'] = tel
        if tel_flag:
            issues.append(tel_flag)

        # Terms of Use validation
        terms_version, terms_flag = validate_read_policy(row_dict.get('termsOfUseVersion'))
        row_dict['termsOfUseVersion'] = terms_version
        if terms_flag:
            issues.append(terms_flag)

        # Check for missing required fields using model (excluding latitude/longitude which are added later)
        # Add placeholder values for lat/lng so they don't show as missing in initial validation
        row_dict_with_placeholders = {**row_dict, 'latitude': 'pending', 'longitude': 'pending'}
        t = Therapist(**row_dict_with_placeholders)
        missing = t.missing_fields()
        issues.extend(missing)

    except Exception as e:
        error_msg = f"Error processing row {idx+1}: {str(e)}"
        error_log.append(error_msg)
        print(f"ERROR: {error_msg}")
        issues.append(f"Processing error: {str(e)}")
    
    return row_dict, issues


def categorize_failure(issues):
    """
    Extract failed field names from issue messages.
    
    Args:
        issues: List of issue messages
        
    Returns:
        Set of failed field names
    """
    failed_columns = set()
    for issue in issues:
        issue_lower = issue.lower()
        if 'createdat' in issue_lower or 'timestamp' in issue_lower:
            failed_columns.add('createdAt')
        if 'email' in issue_lower:
            failed_columns.add('email')
        if 'name' in issue_lower:
            failed_columns.add('name')
        if 'readpolicy' in issue_lower or 'read_policy' in issue_lower or 'terms' in issue_lower:
            failed_columns.add('read_policy')
        if 'city' in issue_lower:
            failed_columns.add('city')
        if 'address' in issue_lower:
            failed_columns.add('address')
        if 'bio' in issue_lower:
            failed_columns.add('bio')
        if 'specialty' in issue_lower:
            failed_columns.add('specialty')
        if 'tel' in issue_lower:
            failed_columns.add('tel')
        if 'kupat' in issue_lower or 'kupatholim' in issue_lower:
            failed_columns.add('kupat_holim')
        if 'latitude' in issue_lower or 'longitude' in issue_lower or 'geocod' in issue_lower:
            failed_columns.add('geolocation')
    return failed_columns


def write_outputs(valid_rows, invalid_rows, df_columns, script_dir):
    """
    Write valid rows, invalid rows, and summary to files.
    
    Args:
        valid_rows: List of valid row dictionaries
        invalid_rows: List of invalid row dictionaries
        df_columns: List of original DataFrame column names
        script_dir: Directory to write files to
    """
    # File paths without timestamps (overwritten each run)
    invalid_rows_path = os.path.join(script_dir, 'invalid_rows.csv')
    results_path = os.path.join(script_dir, 'results.csv')
    summary_path = os.path.join(script_dir, 'summary.json')
    
    # Write invalid rows
    invalid_columns = ['failed_at'] + df_columns
    if invalid_rows:
        pd.DataFrame(invalid_rows).to_csv(invalid_rows_path, index=False)
    else:
        pd.DataFrame(columns=invalid_columns).to_csv(invalid_rows_path, index=False)
    
    # Write valid rows
    if valid_rows:
        pd.DataFrame(valid_rows).to_csv(results_path, index=False)
    else:
        pd.DataFrame(columns=df_columns).to_csv(results_path, index=False)
    
    # Generate summary statistics
    failure_breakdown = defaultdict(int)
    for invalid_row in invalid_rows:
        failed_fields = invalid_row.get('failed_at', '').split(', ')
        for field in failed_fields:
            if field:
                failure_breakdown[field] += 1
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_rows': len(valid_rows) + len(invalid_rows),
        'valid_rows': len(valid_rows),
        'invalid_rows': len(invalid_rows),
        'failure_breakdown': dict(failure_breakdown),
        'output_files': {
            'valid_data': results_path,
            'invalid_data': invalid_rows_path
        }
    }
    
    # Write summary
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Also write a text summary for easy reading
    summary_txt_path = os.path.join(script_dir, 'summary.txt')
    with open(summary_txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Therapist Data Processing Summary\n")
        f.write(f"Generated: {summary['timestamp']}\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Total rows processed: {summary['total_rows']}\n")
        f.write(f"Valid rows: {summary['valid_rows']}\n")
        f.write(f"Invalid rows: {summary['invalid_rows']}\n\n")
        if failure_breakdown:
            f.write("Failure breakdown by field:\n")
            for field, count in sorted(failure_breakdown.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {field}: {count}\n")
        f.write(f"\nOutput files:\n")
        f.write(f"  Valid data: {results_path}\n")
        f.write(f"  Invalid data: {invalid_rows_path}\n")
    
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Total rows: {summary['total_rows']}")
    print(f"  Valid: {summary['valid_rows']}")
    print(f"  Invalid: {summary['invalid_rows']}")
    print(f"  Results saved to: {results_path}")
    print(f"  Invalid rows saved to: {invalid_rows_path}")
    print(f"  Summary saved to: {summary_path}")
    print(f"{'='*50}\n")


def read_and_map_therapists(csv_path):
    """
    Main processing function: read CSV, validate rows, write outputs.
    
    Args:
        csv_path: Path to input CSV file
    """
    # Read CSV
    df = read_csv(csv_path)
    
    # Initialize tracking variables
    invalid_rows = []
    valid_rows = []
    seen_emails = set()
    seen_tels = set()
    error_log = []
    
    # Initialize geocoder
    geocoder = Geocoder(user_agent="therapist-admin-tool")
    
    # Get script directory for output files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\nValidation results:")
    
    # Process each row
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        
        # Validate row
        validated_row, issues = validate_row(row_dict, idx, seen_emails, seen_tels, error_log)
        
        # Skip empty rows
        if validated_row is None:
            continue
        
        # Geocode using structured city + street for all rows that passed initial validation
        if not issues:
            city = validated_row.get('city')
            street = validated_row.get('address')  # optional street component
            
            lat, lng = geocoder.geocode_location(city, street=street)
            # Convert to float explicitly
            validated_row['latitude'] = float(lat) if lat is not None else None
            validated_row['longitude'] = float(lng) if lng is not None else None
            
            # If geocoding failed, mark as invalid
            if lat is None or lng is None:
                location_desc = f"{street}, {city}" if street else city
                print(f"Row {idx+1}: Failed to geocode: {location_desc}")
                issues.append('Failed to geocode address - could not extract latitude/longitude')
        else:
            # If there were validation issues, don't geocode
            validated_row['latitude'] = None
            validated_row['longitude'] = None
        
        # Categorize as valid or invalid
        if issues:
            if 'Row' not in str(issues):  # Only print if not already printed
                print(f"Row {idx+1} issues: {issues}")
            failed_columns = categorize_failure(issues)
            
            # Add to invalid_rows - geocoding failures are critical
            invalid_row = {'failed_at': ', '.join(sorted(failed_columns))}
            invalid_row.update(validated_row)
            invalid_rows.append(invalid_row)
        else:
            # Only add to valid_rows if geocoding succeeded
            valid_rows.append(validated_row)
    
    # Print geocoding statistics for current run
    geocode_stats = geocoder.get_run_stats()
    print(f"\nGeocoding Statistics (current run):")
    print(f"  Total addresses processed: {geocode_stats['total_addresses']}")
    print(f"  Successfully geocoded: {geocode_stats['successful_geocodes']}")
    print(f"  Failed to geocode: {geocode_stats['failed_geocodes']}")
    
    # Write outputs
    write_outputs(valid_rows, invalid_rows, list(df.columns), script_dir)
    
    # Write error log if any errors occurred
    if error_log:
        error_log_path = os.path.join(script_dir, 'error_log.txt')
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write("Processing Errors\n")
            f.write("=" * 50 + "\n\n")
            for error in error_log:
                f.write(f"{error}\n")
        print(f"Error log saved to: {error_log_path}")


if __name__ == "__main__":
    read_and_map_therapists("../data/raw_spreadsheet.csv")
