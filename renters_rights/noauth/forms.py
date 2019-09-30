from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email address", max_length=100)


class CodeForm(forms.Form):
    email = forms.EmailField(label="Email address", max_length=100)
    code = forms.CharField(label="Code", max_length=20)
