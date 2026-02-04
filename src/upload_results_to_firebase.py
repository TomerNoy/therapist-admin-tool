"""
Upload validated therapist data from results.csv to Firebase.
"""

import pandas as pd
import os
from firebase_loader import FirebaseLoader


def upload_results_to_firebase():
    """
    Read results.csv and upload all therapists to Firebase.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(script_dir, 'results.csv')
    
    # Check if results.csv exists
    if not os.path.exists(results_path):
        print(f"❌ Error: {results_path} not found. Run main.py first to generate results.csv")
        return
    
    # Read results.csv
    print(f"Reading results from: {results_path}")
    df = pd.read_csv(results_path)
    print(f"Found {len(df)} therapists in results.csv")
    print(f"Uploading all {len(df)} therapists to Firebase\n")
    
    # Convert DataFrame to list of dictionaries
    therapist_list = df.to_dict('records')
    
    # Initialize Firebase loader
    loader = FirebaseLoader()
    
    # Upload therapists in batch
    print("Starting batch upload to Firestore...\n")
    success_count, failure_count, duplicate_count, errors = loader.add_therapists_batch(
        therapist_list, 
        skip_duplicate_check=False  # Check for duplicates
    )
    
    # Print summary
    print("\n" + "="*50)
    print("Upload Summary:")
    print(f"  Total therapists: {len(therapist_list)}")
    print(f"  Successfully uploaded: {success_count}")
    print(f"  Duplicates skipped: {duplicate_count}")
    print(f"  Failed: {failure_count}")
    print("="*50)
    
    if errors:
        print("\nErrors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")


if __name__ == "__main__":
    upload_results_to_firebase()
