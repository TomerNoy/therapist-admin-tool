from firebase_loader import FirebaseLoader
import pandas as pd
from datetime import datetime, timezone

# Initialize Firebase
loader = FirebaseLoader()

print("Reading all therapists from Firebase...")
therapists_ref = loader.db.collection('therapists')
existing_therapists = {}

# Get all existing therapists
for doc in therapists_ref.stream():
    data = doc.to_dict()
    email = data.get('email')
    if email:
        existing_therapists[email] = doc.id

print(f"Found {len(existing_therapists)} therapists in Firebase")

# Read results.csv
print("\nReading results.csv...")
df = pd.read_csv('results.csv')
print(f"Found {len(df)} therapists in results.csv")

# Update each therapist
updated_count = 0
not_found_count = 0
error_count = 0

current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

print(f"\nUpdating all therapists with updatedAt: {current_time}\n")

for idx, row in df.iterrows():
    therapist_data = row.to_dict()
    email = therapist_data.get('email')
    
    if email and email in existing_therapists:
        therapist_id = existing_therapists[email]
        
        try:
            # Clean the data (converts string lists to actual lists)
            cleaned_data = loader._clean_data(therapist_data)
            
            # Set updatedAt to current time
            cleaned_data['updatedAt'] = current_time
            
            # Update the document
            therapists_ref.document(therapist_id).update(cleaned_data)
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"Progress: {updated_count}/{len(df)}")
        except Exception as e:
            print(f"✗ Error updating {email}: {e}")
            error_count += 1
    else:
        not_found_count += 1

print(f"\n{'='*50}")
print("Update Summary:")
print(f"  Total in CSV: {len(df)}")
print(f"  Successfully updated: {updated_count}")
print(f"  Not found in Firebase: {not_found_count}")
print(f"  Errors: {error_count}")
print(f"{'='*50}")
