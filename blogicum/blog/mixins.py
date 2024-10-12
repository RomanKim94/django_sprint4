from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin

from .models import Post


class ReverseToPostDetailMixin:
    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={
                'post_id': self.kwargs.get('post_id')
            }
        )


class OnlyUserSelfMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object == self.request.user


class PostObjectMixin(SingleObjectMixin):
    model = Post
    template_name = 'blog/create.html'


class SetAuthorMixin:
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class FilterAnnotateOrderPostsMixin:
    def get_filtered_related_posts(
            self, posts=Post.objects.all(), author_access_flag=False
    ):
        """
        Function for filtering received queryset and attaching related tables.
        Additionally annotates with 'comment_count' fields.
        Returns posts queryset.
        """
        user = self.request.user
        user_posts = Post.objects.none()
        if author_access_flag and not user.is_anonymous:
            user_posts = posts.filter(author=user)
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
        posts = (
            (posts | user_posts).distinct()
        ).select_related(
            'author', 'location', 'category',
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
        return posts
