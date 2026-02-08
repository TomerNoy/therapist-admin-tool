from firebase_loader import FirebaseLoader
import pandas as pd
from datetime import datetime, timezone

# Initialize Firebase
loader = FirebaseLoader()

# Search for the therapist by name
therapist_name = 'תהילה שטראוס'
therapists_ref = loader.db.collection('therapists')
query = therapists_ref.where('name', '==', therapist_name).limit(1)
docs = query.stream()

therapist_id = None
for doc in docs:
    therapist_id = doc.id
    data = doc.to_dict()
    print(f'Found therapist: {therapist_id}')
    print(f'Current otherLanguages: {data.get("otherLanguages")} (type: {type(data.get("otherLanguages"))})')
    break

if not therapist_id:
    print(f'Therapist "{therapist_name}" not found in Firebase!')
else:
    # Get the updated data from results.csv
    df = pd.read_csv('results.csv')
    therapist_row = df[df['name'] == therapist_name]
    
    if not therapist_row.empty:
        therapist_data = therapist_row.iloc[0].to_dict()
        
        # Clean the data (this will convert the string list to actual list)
        cleaned_data = loader._clean_data(therapist_data)
        
        print(f'\nNew otherLanguages: {cleaned_data.get("otherLanguages")} (type: {type(cleaned_data.get("otherLanguages"))})')
        
        # Update timestamp
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        cleaned_data['updatedAt'] = current_time
        
        # Update the document
        therapists_ref.document(therapist_id).update(cleaned_data)
        print(f'\n✓ Updated therapist: {therapist_id} - {therapist_name}')
    else:
        print(f'Therapist "{therapist_name}" not found in results.csv')
