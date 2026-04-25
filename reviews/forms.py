from django import forms
from reviews.models import Review
from users.forms import StyleFormMixin


class ReviewForm(StyleFormMixin, forms.ModelForm):
    title = forms.CharField(max_length=150, label='Заголовок')
    content = forms.CharField(widget=forms.Textarea, label='Содержание')
    rating = forms.ChoiceField(
        choices=[(1, '★'), (2, '★★'), (3, '★★★'), (4, '★★★★'), (5, '★★★★★')],
        widget=forms.RadioSelect,
        label='Оценка',
        initial=5
    )
    slug = forms.SlugField(max_length=20, initial='temp_slug', widget=forms.HiddenInput())

    class Meta:
        model = Review
        fields = ('title', 'content', 'rating', 'slug')
