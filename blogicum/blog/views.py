from typing import Any

from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.base import Model
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import CommentForm, PostForm
from .mixins import (
    AuthorOnlyMixin, PostObjectMixin,
    SetAuthorMixin, ToPostDetailMixin,
)
from .models import Category, Comment, Post, User


POSTS_COUNT_ON_PAGE = 10


def get_filtered_related_posts(
    posts=Post.objects.all(),
    filter_published_flag=True,
    select_related_flag=True,
    annotate_count_flag=True,
):
    """
    Function filters, attaches, annotates with comment count and orders
     if necessary.
    """
    if filter_published_flag:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    if select_related_flag:
        posts = posts.select_related(
            'author', 'location', 'category',
        )
    if annotate_count_flag:
        posts = posts.annotate(
            comment_count=Count('comments')
        )
    return posts.order_by(*Post._meta.ordering)


def get_posts_paginator_page(
    posts, page, posts_on_page=POSTS_COUNT_ON_PAGE
):
    return Paginator(
        posts,
        posts_on_page,
    ).get_page(page)


class UserDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            profile=self.object,
            page_obj=get_posts_paginator_page(
                posts=get_filtered_related_posts(
                    posts=self.object.posts,
                    filter_published_flag=self.object != self.request.user,
                ),
                page=self.request.GET.get('page', 1),
            ),
            **kwargs,
        )


class UserUpdateView(LoginRequiredMixin, UpdateView):
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

    def get_success_url(self):
        return reverse(
            'blog:profile', args=[
                self.request.user.username,
            ]
        )


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_COUNT_ON_PAGE
    queryset = get_filtered_related_posts()


class PostDetailView(LoginRequiredMixin, PostObjectMixin, DetailView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self) -> Model:
        post = super().get_object()
        if post.author == self.request.user:
            return post
        filtered_posts_queryset = get_filtered_related_posts(
            filter_published_flag=True,
            select_related_flag=False,
            annotate_count_flag=False,
        )
        published_post = super().get_object(
            queryset=filtered_posts_queryset,
        )
        return published_post

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
    pattern_name_for_no_access = 'blog:post_detail'


class PostDeleteView(
    LoginRequiredMixin, AuthorOnlyMixin,
    PostObjectMixin, DeleteView,
):
    success_url = reverse_lazy('blog:index')
    pattern_name_for_no_access = 'blog:post_detail'

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
            pk=self.kwargs['post_id'],
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
    pattern_name_for_no_access = 'blog:post_detail'


class CommentDeleteView(
    LoginRequiredMixin, ToPostDetailMixin,
    AuthorOnlyMixin, DeleteView,
):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    pattern_name_for_no_access = 'blog:post_detail'


class CategoryDetailView(DetailView):
    model = Category
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'

    def get_object(self):
        object = super().get_object(
            queryset=Category.objects.filter(is_published=True)
        )
        return object

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            category=self.object,
            page_obj=get_posts_paginator_page(
                posts=get_filtered_related_posts(
                    posts=self.object.posts
                ),
                page=self.request.GET.get('page', 1),
            ),
            **kwargs,
        )
