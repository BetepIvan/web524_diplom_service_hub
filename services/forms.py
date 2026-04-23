from datetime import datetime

from django import forms

from services.models import Service, ServiceImage, Category
from users.forms import StyleFormMixin


class ServiceForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        # fields = '__all__'
        exclude = ('owner', 'is_active', 'views')

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной')
        return price


class ServiceCreateForm(ServiceForm):
    class Meta:
        model = Service
        exclude = ('owner', 'is_active', 'views')


class ServiceAdminForm(ServiceForm):
    class Meta:
        model = Service
        exclude = ('is_active',)


class ServiceImageForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceImage
        fields = '__all__'


class CategoryForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'icon', 'image')
