"""
Firebase loader module for uploading therapist data to Firestore Database.
"""

import os
import json
import uuid
import time
import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseLoader:
    """
    Firebase loader for uploading therapist data to Firestore Database.
    """
    
    def __init__(self, service_account_path=None):
        """
        Initialize Firestore connection.
        
        Args:
            service_account_path: Path to Firebase service account JSON file
        """
        # Set default service account path
        if service_account_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            service_account_path = os.path.join(script_dir, '../credentials/firebase-service-account.json')
        
        # Load service account
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Firebase service account file not found: {service_account_path}")
        
        self.service_account_path = service_account_path
        self.initialized = False
        
        # Initialize Firebase (only once)
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            self.initialized = True
            print(f"Firebase/Firestore initialized")
        else:
            print("Firebase already initialized")
        
        # Get Firestore client
        self.db = firestore.client()
    
    def generate_therapist_id(self):
        """
        Generate a unique UUID for a therapist.
        
        Returns:
            String UUID
        """
        return str(uuid.uuid4())
    
    def check_duplicate(self, email=None, tel=None):
        """
        Check if a therapist with the same email or tel already exists.
        
        Args:
            email: Email to check
            tel: Phone number to check
            
        Returns:
            Tuple of (is_duplicate: bool, existing_id: str or None, field: str or None)
        """
        try:
            therapists_ref = self.db.collection('therapists')
            
            # Check email
            if email:
                docs = therapists_ref.where('email', '==', email).limit(1).stream()
                for doc in docs:
                    return True, doc.id, 'email'
            
            # Check tel
            if tel:
                docs = therapists_ref.where('tel', '==', tel).limit(1).stream()
                for doc in docs:
                    return True, doc.id, 'tel'
            
            return False, None, None
            
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            return False, None, None
    
    def add_therapist(self, therapist_data, therapist_id=None, skip_duplicate_check=False):
        """
        Add a single therapist to Firestore.
        
        Args:
            therapist_data: Dictionary containing therapist data
            therapist_id: Optional UUID (will be generated if not provided)
            skip_duplicate_check: If True, skip duplicate checking
            
        Returns:
            Tuple of (success: bool, therapist_id: str, error_message: str or None)
        """
        try:
            # Check for duplicates unless explicitly skipped
            if not skip_duplicate_check:
                email = therapist_data.get('email')
                tel = therapist_data.get('tel')
                is_dup, existing_id, field = self.check_duplicate(email=email, tel=tel)
                
                if is_dup:
                    error_msg = f"Duplicate {field} found (existing ID: {existing_id})"
                    print(f"⚠ Skipping duplicate: {therapist_data.get('name')} - {error_msg}")
                    return False, existing_id, error_msg
            
            # Generate ID if not provided
            if therapist_id is None:
                therapist_id = self.generate_therapist_id()
            
            # Get reference to therapists collection
            therapists_ref = self.db.collection('therapists')
            
            # Clean data - remove NaN values and convert to JSON-compatible types
            cleaned_data = self._clean_data(therapist_data)
            
            # Add timestamps as ISO 8601 strings
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            cleaned_data['uploadedAt'] = current_time
            cleaned_data['updatedAt'] = current_time
            
            # Set data at the specific therapist ID
            therapists_ref.document(therapist_id).set(cleaned_data)
            
            print(f"✓ Added therapist: {therapist_id} - {cleaned_data.get('name', 'Unknown')}")
            return True, therapist_id, None
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Failed to add therapist: {error_msg}")
            return False, therapist_id, error_msg
    
    def add_therapists_batch(self, therapist_list, skip_duplicate_check=False):
        """
        Add multiple therapists to Firestore.
        
        Args:
            therapist_list: List of therapist data dictionaries
            skip_duplicate_check: If True, skip duplicate checking
            
        Returns:
            Tuple of (success_count, failure_count, duplicate_count, errors_list)
        """
        success_count = 0
        failure_count = 0
        duplicate_count = 0
        errors = []
        
        print(f"\nUploading {len(therapist_list)} therapists to Firestore...")
        
        for idx, therapist_data in enumerate(therapist_list, 1):
            success, therapist_id, error = self.add_therapist(
                therapist_data, 
                skip_duplicate_check=skip_duplicate_check
            )
            
            if success:
                success_count += 1
            elif error and 'Duplicate' in error:
                duplicate_count += 1
            else:
                failure_count += 1
                errors.append({
                    'index': idx,
                    'therapist_id': therapist_id,
                    'name': therapist_data.get('name', 'Unknown'),
                    'error': error
                })
            
            # Progress indicator
            if idx % 10 == 0:
                print(f"Progress: {idx}/{len(therapist_list)}")
        
        print(f"\nUpload complete:")
        print(f"  Success: {success_count}")
        print(f"  Duplicates skipped: {duplicate_count}")
        print(f"  Failed: {failure_count}")
        
        return success_count, failure_count, duplicate_count, errors
    
    def get_therapist(self, therapist_id):
        """
        Retrieve a therapist from Firestore by ID.
        
        Args:
            therapist_id: UUID of the therapist
            
        Returns:
            Dictionary of therapist data or None if not found
        """
        try:
            doc_ref = self.db.collection('therapists').document(therapist_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as e:
            print(f"Error retrieving therapist {therapist_id}: {e}")
            return None
    
    def list_all_therapists(self):
        """
        List all therapists from Firestore.
        
        Returns:
            Dictionary of therapist_id: therapist_data
        """
        try:
            therapists_ref = self.db.collection('therapists')
            docs = therapists_ref.stream()
            
            therapists = {}
            for doc in docs:
                therapists[doc.id] = doc.to_dict()
            
            return therapists
        except Exception as e:
            print(f"Error listing therapists: {e}")
            return {}
    
    def delete_therapist(self, therapist_id):
        """
        Delete a therapist from Firestore.
        
        Args:
            therapist_id: UUID of the therapist
            
        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        try:
            self.db.collection('therapists').document(therapist_id).delete()
            print(f"✓ Deleted therapist: {therapist_id}")
            return True, None
        except Exception as e:
            error_msg = f"Failed to delete therapist: {str(e)}"
            print(f"✗ {error_msg}")
            return False, error_msg
    
    def _clean_data(self, data):
        """
        Clean data for Firebase upload (remove NaN, convert types).
        
        Args:
            data: Dictionary to clean
            
        Returns:
            Cleaned dictionary
        """
        import pandas as pd
        import numpy as np
        
        cleaned = {}
        for key, value in data.items():
            # Skip NaN values (but not empty lists)
            if value is None:
                continue
            if not isinstance(value, (list, bool)) and pd.isna(value):
                continue
            
            # Explicitly convert latitude and longitude to float
            if key in ['latitude', 'longitude']:
                try:
                    cleaned[key] = float(value)
                    continue
                except (ValueError, TypeError):
                    continue
            
            # Convert numpy types to Python types
            if isinstance(value, (np.integer, np.int64)):
                cleaned[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                cleaned[key] = float(value)
            elif isinstance(value, (np.bool_, bool)):
                cleaned[key] = bool(value)
            elif isinstance(value, list):
                # Handle lists (e.g., otherLanguages)
                cleaned[key] = [str(item) for item in value if item]
            elif isinstance(value, str):
                cleaned[key] = str(value)
            else:
                # Try to convert to string as fallback
                try:
                    cleaned[key] = str(value)
                except:
                    continue
        
        return cleaned


def test_firebase_connection():
    """
    Test Firebase connection and basic operations.
    """
    print("=" * 60)
    print("Firebase Connection Test")
    print("=" * 60)
    
    try:
        # Initialize Firebase
        loader = FirebaseLoader()
        print("✓ Firebase initialized successfully")
        
        # First, try to list existing therapists
        print("\nChecking existing therapists...")
        existing_therapists = loader.list_all_therapists()
        
        if existing_therapists:
            print(f"✓ Found {len(existing_therapists)} existing therapists in database")
            print("\nSample existing therapists:")
            for idx, (therapist_id, data) in enumerate(list(existing_therapists.items())[:3]):
                print(f"  {idx+1}. ID: {therapist_id}")
                print(f"     Name: {data.get('name', 'N/A')}")
                print(f"     Email: {data.get('email', 'N/A')}")
        else:
            print("✓ Database is empty (no existing therapists)")
        
        # Create a test therapist
        test_therapist = {
            'createdAt': '2026-02-03T15:30:00Z',
            'name': 'Test Therapist',
            'email': 'test@example.com',
            'tel': '0501234567',
            'address': 'Test Address, Tel Aviv',
            'latitude': 32.0853,
            'longitude': 34.7818,
            'specialty': 'Test Specialty',
            'bio': 'This is a test therapist entry',
            'hasWhatsApp': True,
            'isZoom': False,
            'kupatHolim': 'מכבי',
            'readPolicy': 'קראתי מאשר.ת'
        }
        
        # Add test therapist
        print("\nAdding test therapist...")
        success, therapist_id, error = loader.add_therapist(test_therapist)
        
        if success:
            print(f"✓ Test therapist added with ID: {therapist_id}")
            
            # Retrieve test therapist
            print("\nRetrieving test therapist...")
            retrieved = loader.get_therapist(therapist_id)
            if retrieved:
                print(f"✓ Test therapist retrieved successfully")
                print(f"  Name: {retrieved.get('name')}")
                print(f"  Email: {retrieved.get('email')}")
            
            # Delete test therapist
            print("\nDeleting test therapist...")
            success, error = loader.delete_therapist(therapist_id)
            if success:
                print("✓ Test therapist deleted successfully")
            
            print("\n" + "=" * 60)
            print("Firebase test completed successfully!")
            print("=" * 60)
        else:
            print(f"✗ Failed to add test therapist: {error}")
            
    except Exception as e:
        print(f"✗ Firebase test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_firebase_connection()
