from django.contrib.auth import get_user_model
from django.db import models


CHAR_LIMIT = 20

User = get_user_model()


class CreatePublishBaseModel(models.Model):
    is_published = models.BooleanField(
        default=True, verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f' {self.created_at.strftime("%d.%m.%Y %H:%M")}'


class Category(CreatePublishBaseModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True, verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title', )

    def __str__(self):
        category = self.title[:CHAR_LIMIT]
        return f' {category=}'


class Location(CreatePublishBaseModel):
    name = models.CharField(max_length=256, verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name', )

    def __str__(self):
        location = self.name
        return f' {location=}'


class Post(CreatePublishBaseModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='posts', verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        related_name='posts', verbose_name='Категория'
    )
    image = models.ImageField(
        upload_to='post_image',
        blank=True,
        verbose_name='Изображение',
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date', )

    def __str__(self):
        return (
            f'{self.title[:CHAR_LIMIT]=}, '
            f'{self.category.title[:CHAR_LIMIT]=}, '
            f'{self.location.name[:CHAR_LIMIT]=}, '
            f'{self.author.username=}.'
        )


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey( 
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return (
            f'{self.author.username=} '
            f'{self.created_at=}'
            f'{self.text[:CHAR_LIMIT]=}'
        )
