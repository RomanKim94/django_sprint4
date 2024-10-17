from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import SingleObjectMixin

from .models import Post


class AuthorOnlyMixin:

    def dispatch(self, request, *args, **kwargs):
        self.obj = self.get_object()
        if not self.obj.author == request.user:
            return redirect(
                self.url_for_no_access,
                post_id=self.kwargs.get('post_id'),
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        if not hasattr(self, 'obj'):
            self.obj = super().get_object()
        return self.obj


class ToPostDetailMixin:
    def get_success_url(self):
        return reverse(
            'blog:post_detail', args=[self.kwargs.get('post_id')]
        )


class ProfileOwnerOnlyMixin(UserPassesTestMixin):

    def test_func(self):
        return self.get_object() == self.request.user


class PostObjectMixin(SingleObjectMixin):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class SetAuthorMixin:
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
