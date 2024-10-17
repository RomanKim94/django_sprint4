from django.contrib import admin

from .models import Category, Location, Post, Comment


admin.site.empty_value_display = 'Не задано'


class PostInline(admin.StackedInline):
    model = Post
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (PostInline, )
    list_display = (
        'title', 'description', 'slug', 'is_published', 'created_at'
    )
    list_editable = (
        'description', 'slug', 'is_published'
    )
    search_fields = ('title',)
    list_filter = ('is_published',)
    list_display_links = ('title',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'is_published'
    )
    list_editable = ('is_published', )
    search_fields = ('name',)
    list_filter = ('is_published',)
    list_display_links = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'text', 'pub_date', 'author', 'location',
        'category', 'is_published', 'created_at'
    )
    list_editable = (
        'text', 'pub_date', 'author', 'location',
        'category', 'is_published'
    )
    search_fields = ('title',)
    list_filter = ('category', 'author', 'is_published')
    list_display_links = ('title',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at', 'author', 'post')
    search_fields = ('text', )
    list_filter = ('author', 'post')
    list_display_links = ('text', )
