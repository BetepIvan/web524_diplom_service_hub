from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation

from users.models import User
from users.validators import validate_password
from services.models import Category


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField) or isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class UserForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'avatar', 'location')


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        cleaned_data = self.cleaned_data
        validate_password(cleaned_data['password1'])
        if cleaned_data['password1'] != cleaned_data['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data['password2']


class UserLoginForm(StyleFormMixin, AuthenticationForm):
    pass


class UserUpdateForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'telegram', 'max_messenger', 'avatar', 'location')


class UserChangePasswordForm(StyleFormMixin, PasswordChangeForm):
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        validate_password(password1)
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch'
            )
        password_validation.validate_password(password2, self.user)
        return password2


class BecomeMasterForm(StyleFormMixin, forms.ModelForm):
    work_days = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Пн-Сб: 09:00-18:00, Вс: выходной'}),
        label='График работы'
    )

    class Meta:
        model = User
        fields = ('categories', 'experience', 'education', 'about', 'service_description', 'phone', 'telegram', 'location', 'work_days')
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'about': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Расскажите о себе, своих интересах, почему клиенты должны выбрать вас...'}),
            'service_description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опишите ваши услуги, что вы предлагаете, особенности работы...'}),
            'location': forms.TextInput(attrs={'placeholder': 'Например: Москва, ул. Ленина 1'}),
        }

class MasterProfileForm(StyleFormMixin, forms.ModelForm):
    work_days = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Пн-Сб: 09:00-18:00, Вс: выходной'}),
        label='График работы'
    )

    class Meta:
        model = User
        fields = ('categories', 'experience', 'education', 'about', 'service_description', 'portfolio', 'work_days')
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'about': forms.Textarea(attrs={'rows': 5}),
            'service_description': forms.Textarea(attrs={'rows': 5}),
        }
