from firebase_loader import FirebaseLoader

# Create a complete fake therapist with all values
fake_therapist = {
    'createdAt': '2026-02-04T11:22:00Z',
    'name': 'test user 2',
    'email': 'testuser2@example2.com',
    'tel': '0529876541',
    'address': 'רחוב דיזנגוף 100, תל אביב',
    'latitude': 32.0808,
    'longitude': 34.7730,
    'bio': 'מטפל משפחתי מוסמך עם התמחות בטיפול זוגי וייעוץ הורים. ניסיון של 8 שנים בעבודה עם משפחות בתהליכי משבר ושינוי.',
    'specialty': 'טיפול משפחתי וזוגי',
    'hasWhatsApp': True,
    'isZoom': True,
    'misradHaBitachon': True,
    'kupatHolim': 'מכבי',
    'termsOfUseVersion': '1.1',
    'otherLanguages': ['אנגלית', 'צרפתית'],
    'website': 'https://testuser2-therapy.com'
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
