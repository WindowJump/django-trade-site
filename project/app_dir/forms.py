from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg', 'id': 'typeUsernameX-2'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-lg', 'id': 'typePasswordX-2'}))


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg', 'id': 'typeUsernameX-2'}))
    email = forms.EmailField(label='Email', widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg', 'id': 'typeEmailX-2'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-lg', 'id': 'typePasswordX-2'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-lg', 'id': 'typePasswordX-2'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')