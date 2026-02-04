from firebase_admin import credentials, db
import firebase_admin
import json

# Load service account
with open('../credentials/firebase-service-account.json') as f:
    creds = json.load(f)
    project_id = creds['project_id']

# Try different database URL patterns
urls_to_try = [
    f"https://{project_id}.firebaseio.com/",
    f"https://{project_id}-default-rtdb.firebaseio.com/",
    f"https://{project_id}-default-rtdb.europe-west1.firebasedatabase.app/",
    f"https://{project_id}-default-rtdb.asia-southeast1.firebasedatabase.app/",
]

print("Trying different database URLs...\n")
for url in urls_to_try:
    print(f"Testing: {url}")
    try:
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())
        
        cred = credentials.Certificate('../credentials/firebase-service-account.json')
        firebase_admin.initialize_app(cred, {'databaseURL': url})
        
        ref = db.reference('therapists')
        data = ref.get()
        
        if data is not None:
            count = len(data) if isinstance(data, dict) else 'some'
            print(f"  ✓ SUCCESS! Found {count} therapists at this URL")
            print(f"  \n  **Use this URL in firebase_loader.py**\n")
            
            # Show sample therapist
            if isinstance(data, dict) and len(data) > 0:
                sample_id, sample_data = list(data.items())[0]
                print(f"  Sample therapist:")
                print(f"    ID: {sample_id}")
                print(f"    Name: {sample_data.get('name', 'N/A')}")
            break
        else:
            print(f"  ✗ No data found (empty database)\n")
    except Exception as e:
        error_str = str(e)
        if '404' in error_str:
            print(f"  ✗ Database doesn't exist at this URL (404)\n")
        else:
            print(f"  ✗ Error: {error_str[:80]}\n")

print("\nIf none worked, please check Firebase Console for the actual database URL")
