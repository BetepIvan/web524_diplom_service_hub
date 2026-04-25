from django import forms
from services.models import Service, ServiceImage, Category, Portfolio, MasterService
from users.forms import StyleFormMixin


class ServiceForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ('category', 'title', 'description')  # Убрал price и location

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class ServiceCreateForm(StyleFormMixin, forms.ModelForm):
    use_template = forms.BooleanField(required=False, label='Выбрать из готовых услуг')
    template_service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_template=True),
        required=False,
        label='Готовая услуга',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Service
        fields = ('category', 'title', 'description')  # Убрал price, location
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        master = kwargs.pop('master', None)
        super().__init__(*args, **kwargs)
        if master:
            self.fields['category'].queryset = master.categories.all()
            self.fields['template_service'].queryset = Service.objects.filter(
                is_template=True,
                category__in=master.categories.all()
            )
        self.fields['description'].required = False

    def clean(self):
        cleaned_data = super().clean()
        use_template = cleaned_data.get('use_template')
        template_service = cleaned_data.get('template_service')

        if use_template and template_service:
            cleaned_data['title'] = template_service.title
            cleaned_data['description'] = template_service.description
            cleaned_data['category'] = template_service.category

        return cleaned_data


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


class ServiceAdminForm(ServiceForm):
    class Meta:
        model = Service
        fields = ('category', 'title', 'description', 'is_template')


class ServiceImageForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceImage
        fields = '__all__'


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