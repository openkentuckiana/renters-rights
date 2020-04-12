rom django import forms

class NameForm(forms.form):
    your_email = forms.CharField(label = 'Your Email', max_length = 100)
    your_name = forms.CharField(label = 'Your Name', max_length = 100)
    your_comments = forms.CharField(label = 'Your Comments', max_length = 100)


 