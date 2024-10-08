from django import forms
from .models import ImagePair

class UploadImageForm(forms.ModelForm):
    class Meta:
        model = ImagePair
        fields = ['original_image', 'copy_image']
