from django import forms

class UploadForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=True)
    csv_file = forms.FileField(required=True)