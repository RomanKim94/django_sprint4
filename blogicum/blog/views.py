from typing import Any

from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.base import Model
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import CommentForm, PostForm
from .mixins import (
    AuthorOnlyMixin, PostObjectMixin, ProfileOwnerOnlyMixin,
    SetAuthorMixin, ToPostDetailMixin,
)
from .models import Category, Comment, Post, User


POSTS_COUNT_ON_PAGE = 10


def get_filtered_related_posts(
    posts=Post.objects.all(),
    is_filter_not_published=True,
    is_select_related=True,
    is_annotate_count=True,
    order_by='-pub_date'
):
    """
    Function filters, attaches, annotates with comment count and orders
     if necessary.
    """
    if is_filter_not_published:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    if is_select_related:
        posts = posts.select_related(
            'author', 'location', 'category',
        )
    if is_annotate_count:
        posts = posts.annotate(
            comment_count=Count('comments')
        )
    posts = posts.order_by(order_by)
    return posts


def get_related_posts_paginator_page(view, is_filter_not_published=True):
    return Paginator(
        get_filtered_related_posts(
            view.object.posts,
            is_filter_not_published=is_filter_not_published,
        ),
        POSTS_COUNT_ON_PAGE,
    ).get_page(
        view.request.GET.get('page', 1),
    )


class UserDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            profile=self.object,
            user=self.request.user,
            page_obj=get_related_posts_paginator_page(
                self,
                is_filter_not_published=not (
                    self.request.user
                    and self.object == self.request.user
                ),
            ),
            **kwargs,
        )


class UserUpdateView(LoginRequiredMixin, ProfileOwnerOnlyMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    slug_field = 'username'
    fields = ('username', 'first_name', 'last_name', 'email')

    def get_object(self, queryset=None) -> Model:
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile', args=[self.request.user.username]
        )


class PostCreateView(
    LoginRequiredMixin, SetAuthorMixin,
    PostObjectMixin, CreateView,
):
    form_class = PostForm
    pk_url_kwarg = None

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={
                'username': self.request.user.username,
            }
        )


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_COUNT_ON_PAGE
    queryset = get_filtered_related_posts()


class PostDetailView(LoginRequiredMixin, PostObjectMixin, DetailView):
    template_name = 'blog/detail.html'

    def get_object(self) -> Model:
        post = super().get_object(
            get_filtered_related_posts(
                is_filter_not_published=False,
            )
        )
        if (
            not post.author == self.request.user
            and not (
                post.is_published
                and post.category.is_published
                and post.pub_date <= timezone.now()
            )
        ):
            raise Http404
        return post

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            comments=self.object.comments.select_related('author'),
            form=CommentForm(),
            **kwargs,
        )


class PostEditView(
    LoginRequiredMixin, PostObjectMixin, AuthorOnlyMixin,
    ToPostDetailMixin, UpdateView,
):
    form_class = PostForm
    url_for_no_access = 'blog:post_detail'


class PostDeleteView(
    LoginRequiredMixin, AuthorOnlyMixin,
    PostObjectMixin, DeleteView,
):
    success_url = reverse_lazy('blog:index')
    url_for_no_access = 'blog:post_detail'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            form=PostForm(instance=self.object), **kwargs,
        )


class CommentCreateView(
    LoginRequiredMixin, ToPostDetailMixin, CreateView,
):
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id'),
        )
        return super().form_valid(form)


class CommentUpdateView(
    LoginRequiredMixin, ToPostDetailMixin,
    AuthorOnlyMixin, UpdateView,
):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    url_for_no_access = 'blog:post_detail'


class CommentDeleteView(
    LoginRequiredMixin, ToPostDetailMixin,
    AuthorOnlyMixin, DeleteView,
):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    url_for_no_access = 'blog:post_detail'


class CategoryDetailView(DetailView):
    model = Category
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'

    def get_object(self):
        object = super().get_object()
        if not object.is_published:
            raise Http404
        return object

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            category=self.object,
            page_obj=get_related_posts_paginator_page(self),
            **kwargs,
        )
