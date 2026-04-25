from django.http import HttpResponseForbidden
from django.shortcuts import reverse, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


from reviews.models import Review
from reviews.forms import ReviewForm
from reviews.utils import generate_slug
from users.models import UserRoles
from services.models import MasterService

class ReviewListView(ListView):
    model = Review
    extra_context = {
        'title': 'Наши отзывы',
        'description': 'Слова благодарности от тех, кто уже выбрал нас.'
    }
    template_name = 'reviews/reviews.html'
    paginate_by = 3

    def get_queryset(self):
        return super().get_queryset().filter(sign_of_review=True)


class ReviewDeactivatedListView(ListView):
    model = Review
    extra_context = {
        'title': 'Неактивные отзывы'
    }
    template_name = 'reviews/reviews.html'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(sign_of_review=False)
        return queryset


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_updata.html'
    extra_context = {'title': 'Добавить отзыв'}

    def form_valid(self, form):
        if self.request.user.role not in [UserRoles.USER, UserRoles.ADMIN]:
            return HttpResponseForbidden
        self.object = form.save(commit=False)
        if self.object.slug == 'temp_slug':
            self.object.slug = generate_slug()
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)

    # def form_valid(self, form):
    #     if self.request.user.role not in [UserRoles.USER, UserRoles.ADMIN]:
    #         return HttpResponseForbidden
    #     review_object = form.save()
    #     print(review_object.slug)
    #     if review_object.slug == 'temp_slug':
    #         review_object.slug = generate_slug()
    #         print(review_object.slug)
    #     review_object.author = self.request.user
    #     review_object.save()
    #     return super().form_valid(form)


class ReviewDetailView(DetailView):
    model = Review
    template_name = 'reviews/detail.html'
    extra_context = {
        'title': 'Просмотр отзыва'
    }


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_updata.html'

    def get_success_url(self):
        return reverse('reviews:review_detail', args=[self.kwargs.get('slug')])

    def get_object(self, queryset=None):
        review_object = super().get_object(queryset)
        if review_object.author != self.request.user and self.request.user not in [UserRoles.ADMIN, UserRoles.MODERATOR]:
            raise PermissionDenied()
        return review_object

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        review_object = self.get_object()
        context_data['title'] = f'Изменить отзыв {review_object.service}'
        return context_data


class ReviewDeleteView(DeleteView):
    model = Review
    template_name = 'reviews/delete.html'
    extra_context = {
        'title': 'Удалить отзыв'
    }

    def get_object(self, queryset=None):
        review_object = super().get_object(queryset)
        if review_object.author != self.request.user and self.request.user.role != UserRoles.ADMIN:
            raise PermissionDenied()
        return review_object

    def get_success_url(self):
        return reverse('reviews:reviews_list')


def review_toggle_activity(request, slug):
    review_object = get_object_or_404(Review, slug=slug)
    if review_object.sign_of_review:
        review_object.sign_of_review = False
        review_object.save()
        return redirect(reverse('reviews:reviews_deactivated'))
    review_object.sign_of_review = True
    review_object.save()
    return redirect(reverse('reviews:reviews_list'))


class ReviewCreateForMasterView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_updata.html'
    extra_context = {'title': 'Оставить отзыв'}

    def dispatch(self, request, *args, **kwargs):
        # Разрешаем оставлять отзывы и клиентам, и мастерам
        if request.user.role not in [UserRoles.USER, UserRoles.MASTER, UserRoles.ADMIN]:
            raise PermissionDenied

        # Проверяем, оставлял ли пользователь уже отзыв этому мастеру
        master_id = self.kwargs.get('master_id')
        if Review.objects.filter(author=request.user, master_id=master_id).exists():
            from django.contrib import messages
            messages.warning(request, 'Вы уже оставляли отзыв этому мастеру')
            return redirect('users:master_detail', pk=master_id)

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        master_id = self.kwargs.get('master_id')
        if master_id:
            initial['master'] = master_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master_id = self.kwargs.get('master_id')
        if master_id:
            from users.models import User
            master = get_object_or_404(User, pk=master_id)
            context['master'] = master
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.object.slug == 'temp_slug':
            self.object.slug = generate_slug()
        self.object.author = self.request.user
        self.object.master_id = self.kwargs.get('master_id')
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:master_detail', kwargs={'pk': self.kwargs.get('master_id')})
