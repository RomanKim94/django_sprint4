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
    filter_published=True,
    select_related=True,
    annotate_count=True,
):
    """
    Function filters, attaches, annotates with comment count and orders
     if necessary.
    """
    if filter_published:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    if select_related:
        posts = posts.select_related(
            'author', 'location', 'category',
        )
    if annotate_count:
        posts = posts.annotate(
            comment_count=Count('comments')
        ).order_by(*Post._meta.ordering)
    return posts


def get_paginator_page(
    queryset, request, objects_on_page=POSTS_COUNT_ON_PAGE
):
    return Paginator(
        queryset,
        objects_on_page,
    ).get_page(request.GET.get('page', 1))


class UserDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            profile=self.object,
            page_obj=get_paginator_page(
                queryset=get_filtered_related_posts(
                    posts=self.object.posts,
                    filter_published=self.object != self.request.user,
                ),
                request=self.request,
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
        return super().get_object(
            queryset=get_filtered_related_posts(
                select_related=False,
                annotate_count=False,
            ),
        )

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
    route_for_no_access = 'blog:post_detail'


class PostDeleteView(
    LoginRequiredMixin, AuthorOnlyMixin,
    PostObjectMixin, DeleteView,
):
    success_url = reverse_lazy('blog:index')
    route_for_no_access = 'blog:post_detail'

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
    route_for_no_access = 'blog:post_detail'


class CommentDeleteView(
    LoginRequiredMixin, ToPostDetailMixin,
    AuthorOnlyMixin, DeleteView,
):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    route_for_no_access = 'blog:post_detail'


class CategoryDetailView(DetailView):
    model = Category
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'

    def get_object(self):
        return super().get_object(
            queryset=Category.objects.filter(is_published=True)
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            category=self.object,
            page_obj=get_paginator_page(
                queryset=get_filtered_related_posts(
                    posts=self.object.posts
                ),
                request=self.request,
            ),
            **kwargs,
        )
