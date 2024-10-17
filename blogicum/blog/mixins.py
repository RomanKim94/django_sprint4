from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import SingleObjectMixin

from .models import Post


class AuthorOnlyMixin:

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.author == request.user:
            return redirect(
                self.pattern_name_for_no_access,
                post_id=self.kwargs.get('post_id'),
            )
        return super().dispatch(request, *args, **kwargs)


class ToPostDetailMixin:
    def get_success_url(self):
        return reverse(
            'blog:post_detail', args=[self.kwargs.get('post_id')]
        )


class PostObjectMixin(SingleObjectMixin):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class SetAuthorMixin:
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
