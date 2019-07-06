from django import forms

from items.models import UnitImage


class ItemForm(forms.Form):
    name = forms.CharField(label="Work email", max_length=100)
    description = forms.CharField(label="Work email", max_length=10000)
    images = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)

    def save(self, *args, **kwargs):
        file_list = self.files.getlist('{}-image'.format(self.prefix))

        self.instance.image = file_list[0]
        for file in file_list[1:]:
            UnitImage.objects.create(
                image=file,
                item=self.cleaned_data['position'],
            )

        return super().save(*args, **kwargs)
