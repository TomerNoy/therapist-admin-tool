class Therapist:
    required_fields = [
        "createdAt",
        "name",
        "tel",
        "termsOfUseVersion",
        "email",
        "address",
        "bio",
        "specialty",
        "latitude",
        "longitude",
    ]

    def __init__(self, **kwargs):
        self.data = kwargs
        self.missing = [f for f in self.required_fields if not kwargs.get(f)]

    def is_valid(self):
        return len(self.missing) == 0

    def missing_fields(self):
        return self.missing
