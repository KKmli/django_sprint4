from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator

from .models import Post, Category, Comment, User
from .forms import PostForm, ProfileEditForm, CommentForm


def get_paginator(request, items, num=10):
    """Создание объекта пагинации."""
    paginator = Paginator(items, num)
    num_pages = request.GET.get('page')
    return paginator.get_page(num_pages)


def get_annotated_posts(post_objects, show_all=False):
    """
    Получение постов с аннотацией количества комментариев.

    Args:
        post_objects: QuerySet постов
        show_all: Если True - показывать все посты (для автора),
                  Если False - только опубликованные
    """
    if not show_all:
        posts = post_objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
    else:
        posts = post_objects

    return posts.annotate(comment_count=Count('comments')).order_by('-pub_date')


def index(request):
    """Главная страница."""
    template = 'blog/index.html'
    post_list = get_annotated_posts(Post.objects, show_all=False)
    page_obj = get_paginator(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    """Полное описание поста."""
    template = 'blog/detail.html'
    
    # Базовый queryset с join'ами для оптимизации
    post_queryset = Post.objects.select_related('author', 'category', 'location')
    
    if request.user.is_authenticated:
        # Для авторизованных: сначала получаем без ограничений
        post = get_object_or_404(post_queryset, id=post_id)
        
        # Проверяем права на просмотр
        if post.author != request.user:
            # Для не-авторов проверяем все условия публикации
            if not (post.is_published and 
                    post.pub_date <= timezone.now() and 
                    post.category.is_published):
                # Если условия не выполнены - возвращаем 404
                # Django использует handler404 из urls.py
                post = get_object_or_404(
                    post_queryset.filter(
                        id=post_id,
                        is_published=True,
                        pub_date__lte=timezone.now(),
                        category__is_published=True
                    )
                )
    else:
        # Для неавторизованных - только опубликованное
        post = get_object_or_404(
            post_queryset.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            ),
            id=post_id
        )
    
    comments = post.comments.order_by('created_at')
    form = CommentForm()
    context = {'post': post, 'form': form, 'comments': comments}
    return render(request, template, context)


def category_posts(request, category_slug):
    """Публикации категории."""
    template = 'blog/category.html'
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    post_list = get_annotated_posts(category.posts.all(), show_all=False)
    page_obj = get_paginator(request, post_list)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    """Профиль пользователя."""
    template = 'blog/profile.html'
    user = get_object_or_404(User, username=username)

    # Определяем, показывать ли все посты
    show_all = request.user.is_authenticated and request.user == user

    posts_list = get_annotated_posts(user.posts.all(), show_all=show_all)
    page_obj = get_paginator(request, posts_list)
    context = {'profile': user, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def create_post(request):
    """Создание новой записи."""
    template = 'blog/create.html'
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', request.user)
    else:
        form = PostForm()
    context = {'form': form}
    return render(request, template, context)


@login_required
def edit_profile(request):
    """Редактирование профиля."""
    template = 'blog/user.html'
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', request.user)
    else:
        form = ProfileEditForm(instance=request.user)
    context = {'form': form}
    return render(request, template, context)


@login_required
def delete_post(request, post_id):
    """Удаление записи."""
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        form = PostForm(request.POST or None, instance=post)
        post.delete()
        return redirect('blog:index')
    else:
        form = PostForm(instance=post)
    context = {'form': form}
    return render(request, template, context)


@login_required
def edit_post(request, post_id):
    """Редактирование записи."""
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        form = PostForm(
            request.POST, files=request.FILES or None, instance=post)
        if form.is_valid():
            post.save()
            return redirect('blog:post_detail', post_id)
    else:
        form = PostForm(instance=post)
    context = {'form': form}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        form = CommentForm(request.POST or None, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id)
    else:
        form = CommentForm(instance=comment)
    context = {'form': form, 'comment': comment}
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id)
    context = {'comment': comment}
    return render(request, template, context)
