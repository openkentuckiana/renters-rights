from django import forms

from units.models import DOCUMENT, PICTURE, Unit, UnitImage


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = [
            "unit_address_1",
            "unit_address_2",
            "unit_city",
            "unit_state",
            "unit_zip_code",
            "landlord_address_1",
            "landlord_address_2",
            "landlord_city",
            "landlord_state",
            "landlord_zip_code",
            "landlord_phone_number",
            "lease_start_date",
            "lease_end_date",
            "rent_due_date",
        ]

    documents = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False
    )

    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False
    )

    def save(self, commit=True):

        instance = super().save(commit=False)
        old_m2m = self.save_m2m

        def save_m2m():
            old_m2m()

            for file in self.files.getlist("documents"):
                instance.documents.create(image=file, image_type=DOCUMENT)
            for file in self.files.getlist("images"):
                instance.images.create(image=file, image_type=PICTURE)

        self.save_m2m = save_m2m

        if commit:
            instance.save()
            self.save_m2m()

        return instance
