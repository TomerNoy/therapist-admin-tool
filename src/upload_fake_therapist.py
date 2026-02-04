from firebase_loader import FirebaseLoader

# Create a complete fake therapist with all values
fake_therapist = {
    'createdAt': '2026-02-03T15:25:00Z',
    'name': 'דר׳ מיכל לוי',
    'email': 'michal.levy@example.com',
    'tel': '0541234567',
    'address': 'רחוב הרצל 25, תל אביב',
    'latitude': 32.0853,
    'longitude': 34.7818,
    'bio': 'פסיכולוגית קלינית בעלת ניסיון של 12 שנה בטיפול במבוגרים ובני נוער. מתמחה בטיפול קוגניטיבי התנהגותי (CBT) וטיפול משפחתי.',
    'specialty': 'טיפול קוגניטיבי התנהגותי (CBT)',
    'hasWhatsApp': True,
    'isZoom': True,
    'misradHaBitachon': False,
    'kupatHolim': 'כללית',
    'readPolicy': 'קראתי מאשר.ת',
    'otherLanguages': 'אנגלית, רוסית',
    'website': 'https://michal-levy-therapy.com'
}

# Initialize Firebase and upload
print("Creating fake therapist and uploading to Firestore...\n")
loader = FirebaseLoader()

success, therapist_id, error = loader.add_therapist(fake_therapist)

if success:
    print(f"\n✓ Fake therapist uploaded successfully!")
    print(f"  ID: {therapist_id}")
    print(f"  Name: {fake_therapist['name']}")
    print(f"  Email: {fake_therapist['email']}")
    print(f"  Tel: {fake_therapist['tel']}")
    print(f"\nYou can view it in Firebase Console")
else:
    print(f"\n✗ Failed: {error}")
