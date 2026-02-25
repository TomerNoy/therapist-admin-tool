"""
Upload validated therapist data from results.csv to Firebase with hash-based tracking.
"""

import pandas as pd
import os
import json
import sys
from firebase_loader import FirebaseLoader
from utils import calculate_therapist_hash
from datetime import datetime, timezone


def upload_results_to_firebase(dry_run=False):
    """
    Read results.csv and upload new/changed therapists to Firebase.
    Uses hash-based tracking to detect changes and avoid unnecessary uploads.
    
    Args:
        dry_run: If True, only prints what would be done without actually uploading
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(script_dir, 'results.csv')
    tracking_path = os.path.join(script_dir, 'uploaded_therapists.json')
    
    # Check if results.csv exists
    if not os.path.exists(results_path):
        print(f"❌ Error: {results_path} not found. Run main.py first to generate results.csv")
        return
    
    # Read results.csv
    print(f"Reading results from: {results_path}")
    df = pd.read_csv(results_path)
    print(f"Found {len(df)} therapists in results.csv")
    
    # Load tracking file
    if os.path.exists(tracking_path):
        with open(tracking_path, 'r', encoding='utf-8') as f:
            tracking = json.load(f)
        print(f"Loaded tracking file: {len(tracking)} previously uploaded therapists\n")
    else:
        tracking = {}
        print("No tracking file found - all therapists will be treated as new\n")
    
    # Initialize Firebase loader (only if not dry run)
    loader = None if dry_run else FirebaseLoader()
    
    # Counters
    new_count = 0
    updated_count = 0
    coords_updated_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print("="*70)
    if dry_run:
        print("DRY RUN MODE - No actual uploads will be performed")
    print("Analyzing therapists...\n")
    print("="*70)
    
    # Process each therapist
    for idx, row in df.iterrows():
        therapist_data = row.to_dict()
        email = therapist_data.get('email')
        name = therapist_data.get('name', 'Unknown')
        
        if not email:
            print(f"⚠ Row {idx+1}: Missing email, skipping")
            error_count += 1
            continue
        
        # Calculate hash of current data
        current_hash = calculate_therapist_hash(therapist_data)
        
        # Extract current coordinates
        current_lat = therapist_data.get('latitude')
        current_lng = therapist_data.get('longitude')
        try:
            current_lat = float(current_lat) if current_lat is not None and not pd.isna(current_lat) else None
            current_lng = float(current_lng) if current_lng is not None and not pd.isna(current_lng) else None
        except (ValueError, TypeError):
            current_lat, current_lng = None, None
        
        # Check if therapist exists in tracking
        if email in tracking:
            tracked = tracking[email]
            stored_hash = tracked.get('data_hash')
            stored_lat = tracked.get('latitude')
            stored_lng = tracked.get('longitude')
            
            data_changed = current_hash != stored_hash
            coords_changed = (stored_lat != current_lat or stored_lng != current_lng)
            
            if data_changed:
                # Data fields changed - full update
                print(f"📝 UPDATE: {name} ({email})")
                print(f"   Hash changed: {stored_hash[:8]}... → {current_hash[:8]}...")
                
                if not dry_run:
                    success, _, error = loader.update_therapist(tracked['uuid'], therapist_data)
                    if success:
                        tracking[email]['data_hash'] = current_hash
                        tracking[email]['latitude'] = current_lat
                        tracking[email]['longitude'] = current_lng
                        tracking[email]['updated_at'] = current_time
                        updated_count += 1
                    else:
                        errors.append(f"{email}: {error}")
                        error_count += 1
                else:
                    updated_count += 1
            elif coords_changed:
                # Only coordinates changed - targeted update
                print(f"📍 COORDS UPDATE: {name} ({email})")
                print(f"   Lat: {stored_lat} → {current_lat}")
                print(f"   Lng: {stored_lng} → {current_lng}")
                
                if not dry_run:
                    coords_data = {
                        'latitude': current_lat,
                        'longitude': current_lng,
                    }
                    success, _, error = loader.update_therapist(tracked['uuid'], coords_data)
                    if success:
                        tracking[email]['latitude'] = current_lat
                        tracking[email]['longitude'] = current_lng
                        tracking[email]['updated_at'] = current_time
                        coords_updated_count += 1
                    else:
                        errors.append(f"{email}: {error}")
                        error_count += 1
                else:
                    coords_updated_count += 1
            else:
                # No changes - skip
                skipped_count += 1
        else:
            # New therapist - upload
            print(f"✨ NEW: {name} ({email})")
            
            if not dry_run:
                success, therapist_id, error = loader.add_therapist(therapist_data, skip_duplicate_check=True)
                if success:
                    tracking[email] = {
                        'uuid': therapist_id,
                        'data_hash': current_hash,
                        'latitude': current_lat,
                        'longitude': current_lng,
                        'uploaded_at': current_time,
                        'updated_at': current_time
                    }
                    new_count += 1
                else:
                    errors.append(f"{email}: {error}")
                    error_count += 1
            else:
                new_count += 1
    
    # Detect orphaned therapists: in Firebase (tracking) but not in current results.csv
    csv_emails = set(df['email'].dropna().str.strip().str.lower())
    orphaned = []
    for tracked_email, tracked_info in tracking.items():
        if tracked_email.strip().lower() not in csv_emails:
            orphaned.append((tracked_email, tracked_info))
    
    # Save tracking file (only if not dry run)
    if not dry_run:
        with open(tracking_path, 'w', encoding='utf-8') as f:
            json.dump(tracking, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Tracking file saved: {tracking_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("Summary:")
    print("="*70)
    print(f"  Total in CSV: {len(df)}")
    print(f"  New uploads: {new_count}")
    print(f"  Data updates: {updated_count}")
    print(f"  Coords-only updates: {coords_updated_count}")
    print(f"  Skipped (no changes): {skipped_count}")
    print(f"  Errors: {error_count}")
    print("="*70)
    
    # Flag orphaned therapists
    if orphaned:
        print(f"\n⚠️  ORPHANED THERAPISTS ({len(orphaned)}):")
        print(f"   These exist in Firebase but are missing from the current results.csv.")
        print(f"   They may have been removed from the spreadsheet or failed validation.")
        print(f"   Their Firebase documents were NOT updated in this run.\n")
        for email, info in orphaned:
            print(f"   ⚠️  {email}")
            print(f"      UUID: {info.get('uuid', 'unknown')}")
            print(f"      Uploaded: {info.get('uploaded_at', 'unknown')}")
            print(f"      Last updated: {info.get('updated_at', 'unknown')}")
            print()
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made to Firebase")
        print("   Run without --dry-run flag to perform actual uploads")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")


if __name__ == "__main__":
    # Check for --dry-run flag
    dry_run = '--dry-run' in sys.argv
    upload_results_to_firebase(dry_run=dry_run)
