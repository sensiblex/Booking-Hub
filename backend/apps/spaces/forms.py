from django import forms

from .models import Space


class SpaceForm(forms.ModelForm):
    delete_image = forms.BooleanField(required=False, label='Удалить текущее фото')

    class Meta:
        model = Space
        fields = (
            'name',
            'category',
            'address',
            'capacity',
            'price_per_hour',
            'description',
            'amenities',
            'image',
            'has_wifi',
            'has_projector',
            'has_board',
        )
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'adm-input',
                'placeholder': 'Переговорная №1',
            }),
            'address': forms.TextInput(attrs={
                'class': 'adm-input',
                'placeholder': 'ул. Примерная, 10, офис 202',
            }),
            'category': forms.Select(attrs={
                'class': 'adm-input',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'adm-input',
                'min': 1,
            }),
            'price_per_hour': forms.NumberInput(attrs={
                'class': 'adm-input',
                'min': 0,
            }),
            'description': forms.Textarea(attrs={
                'class': 'adm-input',
                'rows': 3,
                'placeholder': 'Краткое описание помещения...',
            }),
            'amenities': forms.CheckboxSelectMultiple(),
            'image': forms.FileInput(attrs={
                'class': 'adm-input',
                'accept': 'image/jpeg,image/png,image/webp',
            }),
        }

    def save(self, commit=True):
        space = super().save(commit=False)
        if self.cleaned_data.get('delete_image') and 'image' not in self.files:
            space.image = None
        if commit:
            space.save()
            self.save_m2m()
        return space
