from typing import Any

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, UpdateView, ListView,
)

from .models import Category, Comment, Post
from .forms import CommentForm, PostForm
from .mixins import (
    OnlyUserSelfMixin, PostObjectMixin,
    SetAuthorMixin, FilterAnnotateOrderPostsMixin, ReverseToPostDetailMixin,
)


User = get_user_model()


class UserDetailView(FilterAnnotateOrderPostsMixin, DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        author = self.object
        context['profile'] = author
        paginator = Paginator(
            self.get_filtered_related_posts(
                author.posts,
                author_access_flag=True,
            ),
            10,
        )
        context['page_obj'] = paginator.get_page(
            self.request.GET.get('page', 1),
        )
        return context


class UserUpdateView(LoginRequiredMixin, OnlyUserSelfMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    fields = ('username', 'first_name', 'last_name', 'email')

    def get_object(self, queryset=None) -> Model:
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={
                'username': self.request.user.username,
            }
        )


class PostCreateView(
    LoginRequiredMixin, SetAuthorMixin, PostObjectMixin, CreateView
):
    form_class = PostForm

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={
                'username': self.request.user.username,
            }
        )


class PostListView(FilterAnnotateOrderPostsMixin, ListView):
    model = Post
    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_obj'] = Paginator(
            self.get_filtered_related_posts(author_access_flag=False),
            10,
        ).get_page(
            self.request.GET.get('page', 1),
        )
        return context


class PostDetailView(
    PostObjectMixin,
    FilterAnnotateOrderPostsMixin, DetailView,
):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=Post.objects.all()) -> Model:
        return super().get_object(
            self.get_filtered_related_posts(
                queryset,
                author_access_flag=True,
            )
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('author')
        context['form'] = CommentForm()
        return context


class PostEditView(
    ReverseToPostDetailMixin,
    FilterAnnotateOrderPostsMixin, UpdateView,
):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    form_class = PostForm

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=kwargs.get('post_id'))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        post = form.instance
        if self.request.user != post.author:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().form_valid(form)

    def get_object(self, queryset=Post.objects.all()) -> Model:
        post = super().get_object(
            self.get_filtered_related_posts(
                queryset,
                author_access_flag=True,
            )
        )
        return post


class PostDeleteView(DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_queryset(self):
        user = self.request.user
        if user and not user.is_anonymous:
            return super().get_queryset().filter(author=user)
        return Post.objects.none()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        post = super().get_object(
            queryset=queryset
        )
        return post

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class CommentCreateView(
    LoginRequiredMixin, ReverseToPostDetailMixin, CreateView
):
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.post_object = Post.objects.get(pk=self.kwargs.get('post_id'))
        except Post.DoesNotExist:
            return render(request, 'pages/404.html', status=404)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_object
        return super().form_valid(form)


class CommentUpdateView(
    LoginRequiredMixin, ReverseToPostDetailMixin, UpdateView
):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_object(self, queryset=None) -> Model:
        if queryset is None:
            queryset = self.get_queryset()
        comment = super().get_object(queryset=queryset)
        if self.request.user != comment.author:
            return self.get_success_url()
        return comment


class CommentDeleteView(
    LoginRequiredMixin, ReverseToPostDetailMixin, DeleteView,
):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_object(self, queryset=None) -> Model:
        if queryset is None:
            queryset = self.get_queryset()
        comment = super().get_object(queryset=queryset)
        if self.request.user != comment.author:
            return self.get_success_url()
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('form')
        return context


class CategoryDetailView(FilterAnnotateOrderPostsMixin, DetailView):
    model = Category
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(is_published=True)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['category'] = self.object
        context['page_obj'] = Paginator(
            self.get_filtered_related_posts(
                context['category'].posts,
                author_access_flag=False,
            ),
            10,
        ).get_page(
            self.request.GET.get('page', 1),
        )
        return context
