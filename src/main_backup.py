
import pandas as pd
import os
from validators import validate_and_transform_timestamp, validate_email, validate_name, validate_read_policy, validate_tel, validate_address, validate_website, validate_bio, validate_specialty
from model import Therapist

def read_and_map_therapists(csv_path):
    # Model fields (from Dart/Freezed):

    # Mapping from CSV columns to model fields (add missing params as needed)
    column_mapping = {
        'name': 'name',
        'tel': 'tel',
        'email': 'email',
        'specialty': 'specialty',
        'bio': 'bio',
        'address': 'address',
        'is_whatsapp': 'hasWhatsApp',
        'is_zoom': 'isZoom',  # not in model, but keep naming convention
        'kupat_holim': 'kupatHolim',  # not in model
        'misrad_habithon': 'misradHaBitachon',  # not in model
        'other_languages': 'otherLanguages',  # not in model
        'website': 'website',  # not in model
        'timestamp': 'timestamp',  # for lastUpdated
        'read_policy': 'readPolicy',  # not in model
    }

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        abs_path = os.path.join(os.path.dirname(__file__), '../data/raw_spreadsheet.csv')
        print(f"Trying absolute path: {os.path.abspath(abs_path)}")
        df = pd.read_csv(abs_path)

    # Drop columns that start with 'ignored' or are completely empty
    df = df[[col for col in df.columns if not col.startswith('ignored') and not df[col].isnull().all()]]

    # Rename columns according to mapping (ignore missing)
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    print("Mapped DataFrame columns:", list(df.columns))
    print(df.head())

    # Validate and transform each row
    print("\nValidation results:")
    invalid_rows = []
    valid_rows = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        # website validation (remove if not valid)
        website, _ = validate_website(row_dict.get('website'))
        row_dict['website'] = website

        # Skip row if all fields are empty or NaN (after stripping whitespace)
        if all((str(cell).strip() == '' or pd.isna(cell)) for cell in row_dict.values()):
            continue

        # Timestamp validation and transformation
        iso_ts, ts_flag = validate_and_transform_timestamp(row_dict.get('timestamp'))
        row_dict['timestamp'] = iso_ts
        # Email validation and normalization (lowercase)
        email, email_flag = validate_email(row_dict.get('email'))
        row_dict['email'] = email.lower() if email else email
        # Name validation
        name, name_flag = validate_name(row_dict.get('name'))
        row_dict['name'] = name
        # is_whatsapp, isZoom, misradHaBitachon to boolean
        is_whatsapp_val = row_dict.get('hasWhatsApp')
        row_dict['hasWhatsApp'] = True if str(is_whatsapp_val).strip() == 'כן' else False
        is_zoom_val = row_dict.get('isZoom')
        row_dict['isZoom'] = True if str(is_zoom_val).strip() == 'כן' else False
        misrad_habithon_val = row_dict.get('misradHaBitachon')
        row_dict['misradHaBitachon'] = True if str(misrad_habithon_val).strip() == 'כן' else False
        # address validation
        address, address_flag = validate_address(row_dict.get('address'))
        row_dict['address'] = address
        # bio validation
        bio, bio_flag = validate_bio(row_dict.get('bio'))
        row_dict['bio'] = bio
        # specialty validation
        specialty, specialty_flag = validate_specialty(row_dict.get('specialty'))
        row_dict['specialty'] = specialty
        # tel validation and normalization (preserve + only if present at start, otherwise digits only)
        tel, tel_flag = validate_tel(row_dict.get('tel'))
        if tel:
            import re
            tel = tel.strip()
            if tel.startswith('+'):
                tel = '+' + re.sub(r'\D', '', tel[1:])
            else:
                tel = re.sub(r'\D', '', tel)
        row_dict['tel'] = tel
        # readPolicy validation
        read_policy, read_policy_flag = validate_read_policy(row_dict.get('readPolicy'))
        row_dict['readPolicy'] = read_policy

        t = Therapist(**row_dict)
        issues = t.missing_fields()
        if ts_flag:
            issues.append(ts_flag)
        if email_flag:
            issues.append(email_flag)
        if name_flag:
            issues.append(name_flag)
        if address_flag:
            issues.append(address_flag)
        if bio_flag:
            issues.append(bio_flag)
        if specialty_flag:
            issues.append(specialty_flag)
        if tel_flag:
            issues.append(tel_flag)
        if read_policy_flag:
            issues.append(read_policy_flag)
        if issues:
            print(f"Row {idx+1} issues: {issues}")
            # Only include field names that failed (e.g., 'timestamp', 'email')
            failed_columns = set()
            for issue in issues:
                if 'timestamp' in issue:
                    failed_columns.add('timestamp')
                if 'email' in issue:
                    failed_columns.add('email')
                if 'name' in issue:
                    failed_columns.add('name')
                if 'readPolicy' in issue or 'read_policy' in issue:
                    failed_columns.add('read_policy')
                if 'address' in issue:
                    failed_columns.add('address')
                if 'bio' in issue:
                    failed_columns.add('bio')
                if 'specialty' in issue:
                    failed_columns.add('specialty')
                if 'tel' in issue:
                    failed_columns.add('tel')
            # Only add to invalid_rows if at least one non-empty field (besides failed_at) exists
            non_empty = any(str(v).strip() for k, v in row_dict.items() if k != 'failed_at' and pd.notna(v))
            if non_empty:
                invalid_row = {'failed_at': ', '.join(sorted(failed_columns))}
                invalid_row.update(row_dict)
                invalid_rows.append(invalid_row)
        else:
            # Valid row
            valid_rows.append(row_dict)
        # Always write invalid_rows.csv and results.csv to the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        invalid_rows_path = os.path.join(script_dir, 'invalid_rows.csv')
        results_path = os.path.join(script_dir, 'results.csv')
        columns = ['failed_at'] + list(df.columns)
        # Write invalid rows
        if not os.path.exists(invalid_rows_path):
            pd.DataFrame(columns=columns).to_csv(invalid_rows_path, index=False)
        invalid_df = pd.DataFrame(invalid_rows)
        if not invalid_df.empty:
            invalid_df.to_csv(invalid_rows_path, index=False)
        else:
            pd.DataFrame(columns=columns).to_csv(invalid_rows_path, index=False)
        # Write valid rows
        if valid_rows:
            pd.DataFrame(valid_rows).to_csv(results_path, index=False)
        else:
            # Write only headers if no valid rows
            pd.DataFrame(columns=list(df.columns)).to_csv(results_path, index=False)


if __name__ == "__main__":
    read_and_map_therapists("../data/raw_spreadsheet.csv")
