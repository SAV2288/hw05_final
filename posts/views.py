from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.db.models import Count
import datetime as dt

from .models import Post, Group, Comment, Follow
from .forms import NewPost, NewComment

User = get_user_model()


# Сравнение автора поста и авторизованного пользователя
def user_validate(func):
    def added_value(request, *args, **kwargs):
        if kwargs["username"] == request.user.username:
            return func(request, *args, **kwargs)
        else:
            return redirect(f'/{kwargs["username"]}/{kwargs["post_id"]}/') 
    return added_value


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.annotate(comment_count=Count("post_comment")).order_by("-pub_date")
    # показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10)
    # переменная в URL с номером запрошенной страницы
    page_number = request.GET.get("page")
    # получить записи с нужным смещением
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {"page": page, "paginator": paginator})


# view-функция для страницы сообщества
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.annotate(comment_count=Count("post_comment")).filter(group=group).order_by("-pub_date")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {"group":group, "page": page, "paginator": paginator})


@login_required
# View-функция для страницы добавления новой записи
def new_post(request):
    form = NewPost(request.POST or None, files=request.FILES or None)
    # Если пришел POST-запрос
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("/")
        # Автоматическое заполнение прошедшими валидацию данными всех полей(после ошибки)
        return render(request, "new_post.html", {"form": form})

    return render(request, "new_post.html", {"form":form})


def profile(request, username):
    author_info_dict = profile_author(request, username)
    # показывать по 10 записей на странице.
    paginator = Paginator(author_info_dict["post_list"], 10)
    # переменная в URL с номером запрошенной страницы
    page_number = request.GET.get("page")
    # получить записи с нужным смещением
    page = paginator.get_page(page_number)
    return render(request, "profile.html",
        {
        "page": page,
        "paginator": paginator,
        "author_info_dict": author_info_dict,
        })


def post_view(request, username, post_id,):
    author_info_dict = profile_author(request, username)
    post = Post.objects.annotate(comment_count=Count("post_comment")).get(pk=post_id)
    form = NewComment(request.POST or None, files=request.FILES or None)
    items = Comment.objects.filter(post=post_id).order_by("-created")
    return render(request, "post.html", {
        "author_info_dict":author_info_dict,
        "post": post,
        "form": form,
        "items": items,
        })


@user_validate
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = NewPost(request.POST or None, files=request.FILES or None, instance=post)
    # Если пришел POST-запрос
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Перенаправляем пользователя на главную страницу
            return redirect(f"/{username}/{post_id}/")
        # Автоматическое заполнение прошедшими валидацию данными всех полей(после ошибки)
        return render(request, "new_post.html", {"form": form, "post": post})
    
    return render(request, "new_post.html", {"form": form, "post": post})


# Посты автора в выбранной группе
def author_current_group_posts(request, username, slug):
    author_info_dict = profile_author(request, username)
    group_current = get_object_or_404(Group, slug=slug)
    # Получаем список постов в выбранной группе
    group_current_post_list = []
    for post in author_info_dict["post_list"]:
        if post.group == group_current:
            group_current_post_list.append(post)
        
    paginator = Paginator(group_current_post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "profile.html",
        {
        "page": page,
        "paginator": paginator,
        "author_info_dict": author_info_dict,
        "group_current": group_current
        })


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    form = NewComment(request.POST or None, files=request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            post = Post.objects.get(pk=post_id)
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect(f"/{username}/{post_id}/")
        # Автоматическое заполнение прошедшими валидацию данными всех полей(после ошибки)
        return render(request, "comments.html", {"form": form})

    return render(request, "comments.html", {"form":form})


# Информация об авторе
def profile_author(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.annotate(comment_count=Count("post_comment")).filter(author=author).order_by("-pub_date")
    # Получаем список групп с постами автора.
    group_list = []
    for post in post_list:
        group = post.group
        if group:
            group_list.append(group)
    group_list = set(group_list)
    number_of_records = len(post_list)
    subscribe = Follow.objects.filter(author=author).count()
    subscribers = Follow.objects.filter(user=author).count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author)
    else:
        following = []
    author_info_dict = {
        "author": author,
        "post_list": post_list,
        "group_list": group_list,
        "number_of_records": number_of_records,
        "subscribe": subscribe,
        "subscribers": subscribers,
        "following": following,
        }
    return author_info_dict


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user)
    post_list = []
    post_list_sort = []
    for follow in following:
        post_list_author = Post.objects.annotate(comment_count=Count("post_comment")).filter(author=follow.author)
        for post in post_list_author:
            post_list.append(post)
    post_list_sort = sorted(post_list, key=lambda x: x.pub_date, reverse=True)
        
    paginator = Paginator(post_list_sort, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page, "paginator": paginator, "following": following})


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    follow = Follow.objects.filter(user = request.user, author = author).count()
    if request.user != author and follow == 0:
        follow = Follow.objects.create(user = request.user, author = author)
    return redirect(f"/{username}/")


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    follow = Follow.objects.get(user = request.user, author = author).delete()
    return redirect(f"/{username}/")
