#!/usr/bin/env python3
"""
One-time script to generate uploaded_therapists.json from existing Firebase data.
"""
import json
import pandas as pd
from firebase_loader import FirebaseLoader
from utils import calculate_therapist_hash
from datetime import datetime

def main():
    # Load results
    df = pd.read_csv('results.csv')
    
    # Initialize Firebase
    loader = FirebaseLoader('../credentials/firebase-service-account.json')
    
    tracking = {}
    print('Fetching therapists from Firebase and calculating hashes...\n')
    
    for idx, row in df.iterrows():
        data = row.to_dict()
        email = data.get('email')
        
        if not email:
            continue
        
        # Query Firebase for this therapist
        is_duplicate, doc_id, field = loader.check_duplicate(email=email)
        if is_duplicate:
            # Get the full document data
            doc_ref = loader.db.collection('therapists').document(doc_id)
            existing_data = doc_ref.get().to_dict()
            
            # Calculate hash from CSV data
            data_hash = calculate_therapist_hash(data)
            
            tracking[email] = {
                'uuid': doc_id,
                'data_hash': data_hash,
                'uploaded_at': existing_data.get('createdAt', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')),
                'updated_at': existing_data.get('updatedAt', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
            }
            print(f'✓ {email[:30]:30s} - hash: {data_hash[:8]}')
    
    # Save tracking file
    with open('uploaded_therapists.json', 'w', encoding='utf-8') as f:
        json.dump(tracking, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ Created uploaded_therapists.json with {len(tracking)} therapists')

if __name__ == '__main__':
    main()
