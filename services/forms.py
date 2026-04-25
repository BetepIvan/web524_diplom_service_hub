from django import forms
from services.models import Service, Category, Portfolio, MasterService
from users.forms import StyleFormMixin


class ServiceTemplateForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ('category', 'title', 'description')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        master = kwargs.pop('master', None)
        super().__init__(*args, **kwargs)
        if master:
            # Показываем только категории мастера
            self.fields['category'].queryset = master.categories.all()
        self.fields['description'].required = False


class CategoryForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'icon', 'image')


class PortfolioForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ('title', 'description', 'image', 'price')


class MasterServiceForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = MasterService
        fields = ('price',)  # Убираем выбор услуги из формы
        widgets = {
            'price': forms.TextInput(attrs={'placeholder': 'Оставьте пустым - договорная'}),
        }

    def __init__(self, *args, **kwargs):
        master = kwargs.pop('master', None)
        selected_service_id = kwargs.pop('selected_service_id', None)
        super().__init__(*args, **kwargs)

        self.master = master
        self.selected_service_id = selected_service_id

        self.fields['price'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.master = self.master
        instance.service_template_id = self.selected_service_id
        if commit:
            instance.save()
        return instance
